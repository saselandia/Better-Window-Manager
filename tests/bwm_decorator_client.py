"""Cliente del protocolo de bwm-decorator (src/bwm-decorator/PROTOCOL.md) para las pruebas.

Habla el protocolo binario por el socket SOCK_SEQPACKET, recibe los memfd de los marcos y de la
sombra y compone la decoración en una imagen de Pillow. Es la referencia en Python de lo que hará
el plugin breezebars (F6b).
"""
from __future__ import annotations

import array
import mmap
import os
import socket
import struct
import time
from dataclasses import dataclass, field

MAGIC = 0x444D5742
VERSION = 1
HEADER = struct.Struct("<IHHII")

HELLO, CREATE, UPDATE, DESTROY, POINTER, PING = 1, 2, 3, 4, 5, 6
HELLO_ACK, GEOMETRY, FRAME, SHADOW, REQUEST, ERROR, RECONFIGURED, PONG, SECTION = range(101, 110)

ACTIVE, MAX_H, MAX_V, ALL_DESKTOPS, KEEP_ABOVE, KEEP_BELOW, SHADED = (1 << i for i in range(7))
CLOSEABLE, MAXIMIZEABLE, MINIMIZEABLE, MOVEABLE, RESIZEABLE, SHADEABLE = (1 << i for i in range(7, 13))
DEFAULT_FLAGS = CLOSEABLE | MAXIMIZEABLE | MINIMIZEABLE | MOVEABLE | RESIZEABLE | SHADEABLE

MOTION, LEAVE, PRESS, RELEASE, WHEEL = 1, 2, 3, 4, 5
LEFT_BUTTON = 1

REQUESTS = {1: "close", 2: "toggleMaximization", 3: "minimize", 4: "windowMenu", 5: "showToolTip",
            6: "hideToolTip", 7: "keepAbove", 8: "keepBelow", 9: "onAllDesktops", 10: "shade",
            11: "contextHelp", 12: "applicationMenu", 13: "excludeFromCapture"}


def _string(text: str) -> bytes:
    data = text.encode()
    return struct.pack("<I", len(data)) + data


class _Reader:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def take(self, fmt: str):
        s = struct.Struct("<" + fmt)
        values = s.unpack_from(self.data, self.pos)
        self.pos += s.size
        return values if len(values) > 1 else values[0]

    def string(self) -> str:
        n = self.take("I")
        text = self.data[self.pos:self.pos + n].decode()
        self.pos += n
        return text


@dataclass
class Frame:
    serial: int
    buffer: int
    scale: float
    width: int
    height: int
    stride: int
    capacity: int
    parts: list  # [(dest(x, y, w, h) en píxeles, rect lógico (x, y, w, h))] arriba, abajo, izq., der.
    damage: list
    pixels: bytes = b""


@dataclass
class Window:
    id: int
    geometry: dict | None = None
    frames: list = field(default_factory=list)
    shadow: dict | None = None
    requests: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    buffers: dict = field(default_factory=dict)  # índice → mmap


class Client:
    def __init__(self, path: str, timeout: float = 5.0):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock.connect(path)
        self.sock.settimeout(timeout)
        self.windows: dict[int, Window] = {}
        self.errors: list[str] = []
        self.reconfigured: list[tuple] = []
        self.ack = None
        self.send(HELLO, 0, struct.pack("<I", VERSION))
        self.wait(lambda: self.ack is not None)

    def close(self):
        for w in self.windows.values():
            for m in w.buffers.values():
                m.close()
        self.sock.close()

    def send(self, kind: int, window: int, payload: bytes = b""):
        self.sock.send(HEADER.pack(MAGIC, VERSION, kind, window, len(payload)) + payload)

    def state(self, width=800, height=500, scale=1.0, flags=DEFAULT_FLAGS | ACTIVE, edges=0,
              caption="kitty — ~", app_class="kitty", icon=""):
        return (struct.pack("<dddII", width, height, scale, flags, edges)
                + _string(caption) + _string(app_class) + _string(icon))

    def create(self, wid: int, **state) -> Window:
        self.windows[wid] = Window(wid)
        self.send(CREATE, wid, self.state(**state))
        return self.windows[wid]

    def update(self, wid: int, **state):
        self.send(UPDATE, wid, self.state(**state))

    def destroy(self, wid: int):
        self.send(DESTROY, wid)
        w = self.windows.pop(wid, None)
        if w:
            for m in w.buffers.values():
                m.close()

    def pointer(self, wid: int, kind: int, x: float, y: float, button=0, buttons=0, delta=0.0):
        self.send(POINTER, wid, struct.pack("<IddIId", kind, x, y, button, buttons, delta))

    def click(self, wid: int, x: float, y: float):
        self.pointer(wid, MOTION, x, y)
        self.pointer(wid, PRESS, x, y, LEFT_BUTTON, LEFT_BUTTON)
        self.pointer(wid, RELEASE, x, y, LEFT_BUTTON, 0)

    # ───────────────────────────────────────────── recepción
    def pump(self, timeout: float = 0.05) -> bool:
        self.sock.settimeout(timeout)
        try:
            data, ancdata, _, _ = self.sock.recvmsg(65536, socket.CMSG_LEN(4 * 4))
        except (socket.timeout, BlockingIOError):
            return False
        fds = []
        for level, kind, cdata in ancdata:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                arr = array.array("i")
                arr.frombytes(cdata[:len(cdata) - len(cdata) % arr.itemsize])
                fds.extend(arr)
        self._handle(data, fds)
        return True

    def wait(self, predicate, timeout: float = 5.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if predicate():
                return True
            self.pump(0.05)
        return predicate()

    def wait_frame(self, wid: int, after: int = 0, timeout: float = 5.0) -> Frame | None:
        w = self.windows[wid]
        self.wait(lambda: any(f.serial > after for f in w.frames), timeout)
        newer = [f for f in w.frames if f.serial > after]
        return newer[-1] if newer else None

    def settle(self, quiet: float = 0.3):
        end = time.monotonic() + quiet
        while time.monotonic() < end:
            if self.pump(0.05):
                end = time.monotonic() + quiet

    def _handle(self, data: bytes, fds: list[int]):
        magic, version, kind, wid, size = HEADER.unpack_from(data)
        r = _Reader(data[HEADER.size:HEADER.size + size])
        w = self.windows.get(wid)
        if kind == HELLO_ACK:
            self.ack = (r.take("I"), r.string(), r.string())
        elif kind == ERROR:
            self.errors.append(r.string())
        elif kind == RECONFIGURED:
            self.reconfigured.append((r.string(), r.string()))
        elif kind == GEOMETRY and w:
            v = r.take("d" * 16)
            w.geometry = {"borders": v[0:4], "resizeOnly": v[4:8], "radius": v[8:12], "titleBar": v[12:16],
                          "opaque": bool(r.take("I")), "outline": (r.take("d"), r.take("I"))}
        elif kind == SECTION and w:
            w.sections.append(r.take("I"))
        elif kind == REQUEST and w:
            k, arg = r.take("II")
            rect = r.take("dddd")
            w.requests.append({"kind": REQUESTS.get(k, k), "arg": arg, "rect": rect, "text": r.string()})
        elif kind == SHADOW and w:
            serial, has_fd, width, height, stride = r.take("IIIII")
            dpr = r.take("d")
            padding = r.take("dddd")
            inner = r.take("dddd")
            pixels = b""
            if has_fd and fds and width and height:
                with mmap.mmap(fds[0], stride * height, prot=mmap.PROT_READ) as m:
                    pixels = bytes(m)
            w.shadow = {"serial": serial, "size": (width, height), "stride": stride, "dpr": dpr,
                        "padding": padding, "inner": inner, "pixels": pixels}
        elif kind == FRAME and w:
            serial, buffer, has_fd = r.take("III")
            scale = r.take("d")
            width, height, stride, capacity = r.take("IIII")
            parts = [(r.take("IIII"), r.take("dddd")) for _ in range(4)]
            damage = [r.take("dddd") for _ in range(r.take("I"))]
            if has_fd and fds:
                old = w.buffers.pop(buffer, None)
                if old:
                    old.close()
                w.buffers[buffer] = mmap.mmap(fds[0], capacity, prot=mmap.PROT_READ)
            frame = Frame(serial, buffer, scale, width, height, stride, capacity, parts, damage)
            m = w.buffers.get(buffer)
            if m is not None:
                frame.pixels = m[:stride * height]  # copia inmediata, como el plugin
            w.frames.append(frame)
        for fd in fds:
            os.close(fd)


def frame_image(frame: Frame):
    """La decoración completa (piezas en su sitio, interior transparente) como imagen RGBA de Pillow."""
    from PIL import Image
    buf = Image.frombuffer("RGBA", (frame.width, frame.height), frame.pixels, "raw", "BGRA", frame.stride, 1)
    top_rect = frame.parts[0][1]
    side_rect = frame.parts[2][1]
    total_w = round(top_rect[2] * frame.scale)
    total_h = round((side_rect[3] + frame.parts[0][1][3] + frame.parts[1][1][3]) * frame.scale)
    canvas = Image.new("RGBA", (max(total_w, 1), max(total_h, 1)), (0, 0, 0, 0))
    for (dx, dy, dw, dh), (lx, ly, lw, lh) in frame.parts:
        if dw and dh:
            piece = buf.crop((dx, dy, dx + dw, dy + dh))
            canvas.paste(piece, (round(lx * frame.scale), round(ly * frame.scale)))
    return canvas


def luminance(rgb) -> float:
    r, g, b = (c / 255 for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

#!/usr/bin/env python3
"""
Marca en XWayland como monitor «principal» (RandR primary) el que tiene el workspace 1.

Hyprland no fija ningún primary en XWayland, así que Wine/Proton y muchos juegos X11 toman
el primer output (aquí el LG 4K): se abrían a 3840x2160 o con la posición del otro monitor
y, al llevarlos la regla al monitor principal, quedaban diminutos o por debajo de las pantallas.

Uso:
  xwayland-primary.py          aplica una vez
  xwayland-primary.py status   muestra outputs de XWayland y el primary actual

Lo mantiene aplicado window-guard.py watch (autostart.sh) al cambiar los monitores.
"""
import ctypes as C
import json
import os
import subprocess
import sys
import time


class _Res(C.Structure):
    _fields_ = [("timestamp", C.c_ulong), ("configTimestamp", C.c_ulong),
                ("ncrtc", C.c_int), ("crtcs", C.c_void_p),
                ("noutput", C.c_int), ("outputs", C.POINTER(C.c_ulong)),
                ("nmode", C.c_int), ("modes", C.c_void_p)]


class _Out(C.Structure):
    # Sólo los campos iniciales de XRROutputInfo que se leen
    _fields_ = [("timestamp", C.c_ulong), ("crtc", C.c_ulong),
                ("name", C.c_char_p), ("nameLen", C.c_int)]


def _libs():
    x11 = C.CDLL("libX11.so.6")
    xrr = C.CDLL("libXrandr.so.2")
    x11.XOpenDisplay.restype = C.c_void_p
    x11.XOpenDisplay.argtypes = [C.c_char_p]
    x11.XDefaultRootWindow.restype = C.c_ulong
    x11.XDefaultRootWindow.argtypes = [C.c_void_p]
    x11.XSync.argtypes = [C.c_void_p, C.c_int]
    x11.XCloseDisplay.argtypes = [C.c_void_p]
    xrr.XRRGetScreenResourcesCurrent.restype = C.POINTER(_Res)
    xrr.XRRGetScreenResourcesCurrent.argtypes = [C.c_void_p, C.c_ulong]
    xrr.XRRFreeScreenResources.argtypes = [C.POINTER(_Res)]
    xrr.XRRGetOutputInfo.restype = C.POINTER(_Out)
    xrr.XRRGetOutputInfo.argtypes = [C.c_void_p, C.POINTER(_Res), C.c_ulong]
    xrr.XRRFreeOutputInfo.argtypes = [C.POINTER(_Out)]
    xrr.XRRGetOutputPrimary.restype = C.c_ulong
    xrr.XRRGetOutputPrimary.argtypes = [C.c_void_p, C.c_ulong]
    xrr.XRRSetOutputPrimary.argtypes = [C.c_void_p, C.c_ulong, C.c_ulong]
    return x11, xrr


def _hyprctl(*args):
    out = subprocess.run(["hyprctl", *args, "-j"], capture_output=True, text=True, timeout=5)
    return json.loads(out.stdout or "null")


def wanted_output():
    """Nombre (DP-N) del monitor con el workspace 1; si no, el enfocado."""
    try:
        for ws in _hyprctl("workspaces") or []:
            if ws.get("id") == 1 and ws.get("monitor"):
                return ws["monitor"]
        for mon in _hyprctl("monitors") or []:
            if mon.get("focused"):
                return mon["name"]
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None


def xoutputs(x11, xrr, dpy, root):
    res = xrr.XRRGetScreenResourcesCurrent(dpy, root)
    outs = {}
    try:
        for i in range(res.contents.noutput):
            oid = res.contents.outputs[i]
            info = xrr.XRRGetOutputInfo(dpy, res, oid)
            if info:
                outs[info.contents.name.decode()] = (oid, bool(info.contents.crtc))
                xrr.XRRFreeOutputInfo(info)
    finally:
        xrr.XRRFreeScreenResources(res)
    return outs


def apply(verbose=False):
    target = wanted_output()
    if not target:
        return False
    x11, xrr = _libs()
    dpy = x11.XOpenDisplay(os.environ.get("DISPLAY", ":0").encode())
    if not dpy:
        return False  # XWayland aún no está
    try:
        root = x11.XDefaultRootWindow(dpy)
        outs = xoutputs(x11, xrr, dpy, root)
        if target not in outs:
            return False
        oid = outs[target][0]
        if xrr.XRRGetOutputPrimary(dpy, root) != oid:
            xrr.XRRSetOutputPrimary(dpy, root, oid)
            x11.XSync(dpy, 0)
            if verbose:
                print(f"primary de XWayland -> {target}")
        elif verbose:
            print(f"primary de XWayland ya es {target}")
        return True
    finally:
        x11.XCloseDisplay(dpy)


def status():
    x11, xrr = _libs()
    dpy = x11.XOpenDisplay(os.environ.get("DISPLAY", ":0").encode())
    if not dpy:
        print("XWayland no disponible")
        return 1
    root = x11.XDefaultRootWindow(dpy)
    prim = xrr.XRRGetOutputPrimary(dpy, root)
    for name, (oid, active) in xoutputs(x11, xrr, dpy, root).items():
        print(f"{name}{' (activo)' if active else ''}{'  <- primary' if oid == prim else ''}")
    if not prim:
        print("sin primary")
    print(f"deseado: {wanted_output()}")
    x11.XCloseDisplay(dpy)
    return 0


def apply_retrying(tries=30, delay=1.0):
    for _ in range(tries):
        if apply():
            return True
        time.sleep(delay)
    return False


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if cmd == "status":
        sys.exit(status())
    sys.exit(0 if apply(verbose=True) else 1)

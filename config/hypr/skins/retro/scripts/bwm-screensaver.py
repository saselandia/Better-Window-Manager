#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWM terminal screensaver, modelled on Omarchy's (omarchy-screensaver runs random
TerminalTextEffects over the Omarchy logo). ttfx/tte is not packaged for Gentoo, so
the effects are drawn here with plain truecolor ANSI: the BWM logo appears through a
random effect, stays a moment with a moving gradient, and the next effect starts.

Colours come from the Retro (Omarchy) palette when there is one
(~/.local/state/bwm/omarchy/colors.toml), otherwise from a default set.
Any key quits; Quickshell (modules/ii/screensaver) closes it on any input, mouse included.
"""

import math
import os
import random
import select
import shutil
import signal
import sys
import termios
import time
import tomllib
import tty
from pathlib import Path

LOGO = r"""
▄███████▄   ███       ███   ▄██▄     ▄██▄
███   ███   ███       ███   ████▄   ▄████
███   ███   ███       ███   ███ ██▄██ ███
███▄▄▄██▀   ███  ▄█▄  ███   ███  ▀█▀  ███
███▀▀▀██▄   ███ ██▀██ ███   ███       ███
███   ███   ████▀   ▀████   ███       ███
███   ███   ███▀     ▀███   ███       ███
▀███████▀   ▀█▀       ▀█▀   ▀█▀       ▀█▀
""".strip("\n").splitlines()

GLYPHS = "ｱｲｳｴｵｶｷｸｹｺ0123456789ABCDEF#$%&*+=<>/\\|~░▒▓"
FPS = 40
STATE = Path.home() / ".local" / "state" / "bwm" / "omarchy" / "colors.toml"


def load_palette():
    try:
        with open(STATE, "rb") as f:
            c = tomllib.load(f)
        keys = ["accent", "magenta", "cyan", "blue", "green", "yellow", "red"]
        cols = [c[k] for k in keys if k in c]
        return [hex_rgb(x) for x in cols], hex_rgb(c.get("muted", "#3b4252"))
    except Exception:
        return [hex_rgb(x) for x in ("#7aa2f7", "#bb9af7", "#7dcfff", "#9ece6a", "#e0af68", "#f7768e")], hex_rgb("#414868")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(palette, t):
    """Colour at position t (0..1, wraps) along the palette."""
    t %= 1.0
    n = len(palette)
    x = t * n
    i = int(x)
    return mix(palette[i % n], palette[(i + 1) % n], x - i)


class Screen:
    def __init__(self):
        self.cols, self.rows = shutil.get_terminal_size((120, 40))
        h, w = len(LOGO), max(len(l) for l in LOGO)
        self.ox = max(0, (self.cols - w) // 2)
        self.oy = max(0, (self.rows - h) // 2)
        # Every visible logo cell: (x, y, char)
        self.cells = [(self.ox + x, self.oy + y, ch)
                      for y, line in enumerate(LOGO) for x, ch in enumerate(line) if ch != " "]
        self.w, self.h = w, h

    def frame(self, items):
        """items: iterable of (x, y, ch, rgb). Draws a full frame on black."""
        out = ["\x1b[H\x1b[48;2;0;0;0m\x1b[2J"]
        for x, y, ch, (r, g, b) in items:
            if 0 <= x < self.cols and 0 <= y < self.rows:
                out.append(f"\x1b[{int(y) + 1};{int(x) + 1}H\x1b[38;2;{r};{g};{b}m{ch}")
        sys.stdout.write("".join(out))
        sys.stdout.flush()


# ------------------------------------------------------------------------------
# Effects: generators of frames, each frame a list of (x, y, ch, rgb)
# ------------------------------------------------------------------------------
def shine(s, palette, t):
    return [(x, y, ch, gradient(palette, (x - s.ox) / max(1, s.w) * 0.8 + (y - s.oy) * 0.03 - t * 0.35))
            for x, y, ch in s.cells]


def effect_decrypt(s, palette, muted):
    """Random glyphs that resolve into the logo (like TTE's decrypt)."""
    order = {c[:2]: random.uniform(0.2, 2.2) for c in s.cells}
    start = time.time()
    while (t := time.time() - start) < 2.6:
        items = []
        for x, y, ch in s.cells:
            if t >= order[(x, y)]:
                items.append((x, y, ch, gradient(palette, (x - s.ox) / s.w)))
            else:
                items.append((x, y, random.choice(GLYPHS), mix(muted, palette[0], random.random() * 0.6)))
        yield items


def effect_rain(s, palette, muted):
    """Every cell falls from the top to its place, column by column."""
    delay = {c[:2]: (c[0] - s.ox) * 0.018 + random.uniform(0, 0.4) for c in s.cells}
    start = time.time()
    while (t := time.time() - start) < 3.2:
        items = []
        for x, y, ch in s.cells:
            p = max(0.0, min(1.0, (t - delay[(x, y)]) / 0.9))
            ease = 1 - (1 - p) ** 3
            items.append((x, -1 + (y + 1) * ease, ch if p > 0 else " ", gradient(palette, (y - s.oy) / s.h + t * 0.2)))
        yield items


def effect_beams(s, palette, muted):
    """A bright beam sweeps every row and leaves the logo behind it."""
    start = time.time()
    while (t := time.time() - start) < 2.8:
        items = []
        for x, y, ch in s.cells:
            row_t = t * 1.4 - (y - s.oy) * 0.08
            head = s.ox + row_t * s.w
            if x <= head:
                glow = max(0.0, 1 - (head - x) / 6)
                items.append((x, y, ch, mix(gradient(palette, (x - s.ox) / s.w), (255, 255, 255), glow * 0.8)))
        yield items


def effect_expand(s, palette, muted):
    """Cells fly out from the centre to their places."""
    cx, cy = s.ox + s.w / 2, s.oy + s.h / 2
    start = time.time()
    while (t := time.time() - start) < 2.4:
        p = min(1.0, t / 1.8)
        ease = 1 - (1 - p) ** 4
        yield [(cx + (x - cx) * ease, cy + (y - cy) * ease, ch, gradient(palette, ease * 0.6 + (x - s.ox) / s.w * 0.4))
               for x, y, ch in s.cells]


def effect_matrix(s, palette, muted):
    """Falling glyph columns; the logo lights up where they pass."""
    drops = [[random.randrange(-s.rows, 0), random.uniform(8, 22)] for _ in range(s.cols)]
    logo = {(x, y): ch for x, y, ch in s.cells}
    lit = {}
    start = time.time()
    last = start
    while (t := time.time() - start) < 4.0:
        now = time.time()
        dt, last = now - last, now
        items = []
        for col, d in enumerate(drops):
            d[0] += d[1] * dt
            if d[0] - 12 > s.rows:
                d[0] = random.randrange(-12, 0)
            head = int(d[0])
            for k in range(12):
                y = head - k
                if 0 <= y < s.rows and (col, y) not in logo:
                    items.append((col, y, random.choice(GLYPHS), mix(palette[0], (0, 0, 0), k / 12)))
            if (col, head) in logo:
                lit[(col, head)] = True
        for (x, y), ch in logo.items():
            if lit.get((x, y)) or t > 3.0:
                items.append((x, y, ch, gradient(palette, (x - s.ox) / s.w + t * 0.1)))
        yield items


def effect_hold(s, palette, muted, seconds=5.0):
    """The finished logo with a gradient flowing through it."""
    start = time.time()
    while (t := time.time() - start) < seconds:
        yield shine(s, palette, t)


EFFECTS = [effect_decrypt, effect_rain, effect_beams, effect_expand, effect_matrix]


def key_pressed(fd, started):
    """A real key, not a terminal reply/report (escape sequences) nor the start-up noise."""
    data = os.read(fd, 1024)
    if time.time() - started < 1.0:
        return False
    return not (data.startswith(b"\x1b") and len(data) > 1)


def main():
    palette, muted = load_palette()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    def quit_(*_):
        try:  # the terminal may already be gone (window closed)
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            sys.stdout.write("\x1b[0m\x1b[2J\x1b[H\x1b[?25h")
            sys.stdout.flush()
        except (OSError, termios.error):
            pass
        os._exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, quit_)
    tty.setcbreak(fd)
    sys.stdout.write("\x1b[?25l\x1b]11;rgb:00/00/00\x07")  # hide cursor, black background

    # The terminal starts at 80x24 until the compositor resizes it (see omarchy-screensaver)
    deadline = time.time() + 2
    while shutil.get_terminal_size() == os.terminal_size((80, 24)) and time.time() < deadline:
        time.sleep(0.02)

    started = time.time()
    bag = []  # every effect once, in random order, before repeating
    while True:
        if not bag:
            bag = random.sample(EFFECTS, len(EFFECTS))
        effect = bag.pop()
        s = Screen()  # re-measured each round, in case the terminal was resized
        for frames in (effect(s, palette, muted), effect_hold(s, palette, muted)):
            for items in frames:
                s.frame(items)
                if select.select([fd], [], [], 1 / FPS)[0] and key_pressed(fd, started):
                    quit_()


if __name__ == "__main__":
    main()

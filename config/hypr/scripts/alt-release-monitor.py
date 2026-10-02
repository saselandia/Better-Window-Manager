#!/usr/bin/env python3
import glob
import fcntl
import time
import sys
import os

KEY_LEFTALT = 56
KEY_RIGHTALT = 100
BUF_LEN = 96
# EVIOCGKEY(len) ioctl: _IOC(_IOC_READ, "E", 0x18, len)
# (2 << 30) | (ord("E") << 8) | 0x18 | (BUF_LEN << 16)
EVIOCGKEY = (2 << 30) | (ord("E") << 8) | 0x18 | (BUF_LEN << 16)

def get_keyboard_fds():
    fds = []
    # Search /dev/input/by-id for keyboard devices first
    paths = glob.glob("/dev/input/by-id/*-event-kbd")
    if not paths:
        paths = glob.glob("/dev/input/event*")
    
    for p in paths:
        try:
            fd = os.open(p, os.O_RDONLY | os.O_NONBLOCK)
            fds.append(fd)
        except Exception:
            pass
    return fds

def is_alt_down(fds):
    for fd in fds:
        try:
            buf = bytearray(BUF_LEN)
            fcntl.ioctl(fd, EVIOCGKEY, buf)
            b56 = (buf[KEY_LEFTALT // 8] >> (KEY_LEFTALT % 8)) & 1
            b100 = (buf[KEY_RIGHTALT // 8] >> (KEY_RIGHTALT % 8)) & 1
            if b56 or b100:
                return True
        except Exception:
            pass
    return False

def main():
    fds = get_keyboard_fds()
    if not fds:
        # Fallback if no device accessible
        sys.exit(0)

    try:
        # Maximum wait: 15 seconds to prevent orphaned process
        start_time = time.monotonic()
        while time.monotonic() - start_time < 15.0:
            if not is_alt_down(fds):
                # Alt is not pressed (or was just released)
                sys.exit(0)
            time.sleep(0.015) # Check every 15ms
    finally:
        for fd in fds:
            try:
                os.close(fd)
            except Exception:
                pass

if __name__ == "__main__":
    main()

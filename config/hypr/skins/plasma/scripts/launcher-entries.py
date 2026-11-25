#!/usr/bin/env python3
"""Unity LauncherEntry listener for the Breeze task manager.

Port of the protocol handling of plasma-desktop 6.7.5
applets/taskmanager/smartlauncherbackend.cpp (Kai Uwe Broulik, GPL-2.0-or-later):
listens on the session bus for com.canonical.Unity.LauncherEntry.Update,
keeps count / count-visible / progress / progress-visible / urgent per
desktop storage id and forgets an entry when its sender leaves the bus.

Output: one JSON object per line on stdout.
  {"reset": true}                         at start
  {"id": "<storage id>", "count": …, "countVisible": …,
   "progress": 0-100, "progressVisible": …, "urgent": …}
  {"id": "<storage id>", "removed": true} when the sender disappears
The id is the .desktop storage id lowercased, without "application://" or ".desktop".
"""
import ctypes
import json
import math
import os
import signal
import sys

from gi.repository import Gio, GLib

INT_MAX = 2**31 - 1
APP_PREFIX = "application://"


def normalize(uri):
    if not isinstance(uri, str):
        return ""
    if uri.startswith(APP_PREFIX):
        uri = uri[len(APP_PREFIX):]
    uri = uri.strip().rsplit("/", 1)[-1]
    if uri.endswith(".desktop"):
        uri = uri[:-len(".desktop")]
    return uri.lower()


def apply(entry, props):
    """Update entry from an a{sv} dict like Backend::update(); returns True if it changed."""
    before = dict(entry)
    if "count" in props:
        try:
            count = int(props["count"])
            if 0 <= count < INT_MAX:
                entry["count"] = count
        except (TypeError, ValueError, OverflowError):
            pass
    if "count-visible" in props:
        entry["countVisible"] = bool(props["count-visible"])
    if "progress" in props:
        try:
            value = float(props["progress"])
        except (TypeError, ValueError):
            value = 0.0
        if not math.isfinite(value):
            value = 0.0  # upstream treats NaN/Inf as zero
        entry["progress"] = max(0, min(100, round(value * 100)))
    if "progress-visible" in props:
        entry["progressVisible"] = bool(props["progress-visible"])
    if "urgent" in props:
        entry["urgent"] = bool(props["urgent"])
    return entry != before


def emit(obj):
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
    sys.stdout.flush()


class Listener:
    def __init__(self, bus):
        self.bus = bus
        self.entries = {}   # id -> state
        self.senders = {}   # unique bus name -> set(ids)

    def on_update(self, _conn, sender, _path, _iface, _signal, params):
        if params.get_type_string() != "(sa{sv})":
            return
        uri, props = params.unpack()
        key = normalize(uri)
        if not key:
            return
        entry = self.entries.setdefault(key, {
            "count": 0, "countVisible": False,
            "progress": 0, "progressVisible": False, "urgent": False,
        })
        if sender:
            self.senders.setdefault(sender, set()).add(key)
        if apply(entry, props):
            emit({"id": key, **entry})

    def on_owner_changed(self, _conn, _sender, _path, _iface, _signal, params):
        name, _old, new = params.unpack()
        if new or name not in self.senders:
            return
        for key in self.senders.pop(name):
            if self.entries.pop(key, None) is not None:
                emit({"id": key, "removed": True})


def follow_parent(loop):
    """Exit with the shell that started us: an orphan would keep com.canonical.Unity."""
    parent = os.getppid()
    try:
        ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG
    except (OSError, AttributeError):
        pass
    if os.getppid() != parent:  # died between fork and prctl
        sys.exit(0)

    def check():
        if os.getppid() != parent:
            loop.quit()
            return False
        return True
    GLib.timeout_add_seconds(5, check)
    signal.signal(signal.SIGTERM, lambda *_: loop.quit())

    # A hot reload of the shell destroys its Process without ending the shell process,
    # so PDEATHSIG never fires: the old listener kept the name with nobody reading it.
    # The write end of a pipe reports POLLERR once its last reader is gone.
    def reader_gone(*_):
        loop.quit()
        return False
    try:
        GLib.io_add_watch(sys.stdout.fileno(), GLib.PRIORITY_DEFAULT,
                          GLib.IOCondition.ERR | GLib.IOCondition.HUP, reader_gone)
    except (OSError, ValueError):
        pass


def main():
    loop = GLib.MainLoop()
    follow_parent(loop)
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    listener = Listener(bus)
    bus.signal_subscribe(None, "com.canonical.Unity.LauncherEntry", "Update", None, None,
                         Gio.DBusSignalFlags.NONE, listener.on_update)
    bus.signal_subscribe("org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
                         "/org/freedesktop/DBus", None, Gio.DBusSignalFlags.NONE,
                         listener.on_owner_changed)
    # Like Plasma, announce com.canonical.Unity so apps that look for a dock emit updates;
    # never replace another owner (another dock keeps it, we just listen), but wait in the
    # queue so the name is not left without owner when that dock or an old listener exits.
    Gio.bus_own_name_on_connection(bus, "com.canonical.Unity",
                                   Gio.BusNameOwnerFlags.NONE, None, None)
    emit({"reset": True})
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

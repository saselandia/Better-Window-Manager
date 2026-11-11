#!/usr/bin/env python3
"""
Native-like Window Minimize & Restore Controller for Hyprland (KDE Plasma Style).
Supports:
  toggle-minimize.py min [address]
  toggle-minimize.py restore [address]
  toggle-minimize.py toggle [address]
  toggle-minimize.py toggle-app <appId>
  toggle-minimize.py show-desktop        (KDE "Show Desktop": minimize every window on the
                                          visible workspaces, or restore them if already shown)
  toggle-minimize.py show-desktop leave  (a window appeared while showing the desktop: bring the
                                          hidden windows back but keep the new one in front, like KWin)

Minimized windows wait on special:minimized with Omarchy's tag omarchy-minimized-from-<n> (Omarchy
quattro b99593e), so Retro's dock and this script share them: no conversion when changing skin.
Unlike Omarchy it works on tiled workspaces and without a dock, puts a window back on the
workspace it came from and keeps the exact geometry of floating ones. Windows left by older
versions on workspace 99 with from_ws_<n> are still recognised and restored.
"""

import os
import sys
import json
import subprocess

MINIMIZED_WS = "special:minimized"
TAG_PREFIX = "omarchy-minimized-from-"
LEGACY_WS_ID = 99            # older versions: workspace 99 + from_ws_<n>
LEGACY_TAG_PREFIX = "from_ws_"
# Windows hidden by Show Desktop, read by the Breeze panel DesktopState.
# Quickshell empties it as soon as a window shows up again, which ends the mode like KWin.
SHOW_DESKTOP_STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "bwm-show-desktop.json")
# Exact geometry of minimized floating windows: moving between workspaces (and monitors, on
# restore) lets Hyprland move/clamp a floating window, so it is put back as it was.
GEOMETRY_STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "bwm-minimized-geometry.json")

def load_geometries() -> dict:
    try:
        with open(GEOMETRY_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_geometries(data: dict):
    tmp = GEOMETRY_STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, GEOMETRY_STATE)

def get_clients() -> list:
    try:
        out = subprocess.check_output(["hyprctl", "clients", "-j"]).decode("utf-8")
        return json.loads(out)
    except Exception:
        return []

def get_active_window() -> dict:
    try:
        out = subprocess.check_output(["hyprctl", "activewindow", "-j"]).decode("utf-8")
        data = json.loads(out)
        if isinstance(data, dict) and data.get("address"):
            return data
    except Exception:
        pass
    return {}

def run_lua(code: str):
    subprocess.run(["hyprctl", "dispatch", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_minimized(client: dict) -> bool:
    ws = client.get("workspace", {})
    ws_name = str(ws.get("name", ""))
    ws_id = ws.get("id", 0)
    return ws_name == MINIMIZED_WS or ws_id == LEGACY_WS_ID

def minimize_tags(client: dict) -> list:
    """Tags this script or Omarchy's minimize left (dynamic tags may end in "*")."""
    return [t.rstrip("*") for t in client.get("tags", []) or []
            if t.rstrip("*").startswith((TAG_PREFIX, LEGACY_TAG_PREFIX))]

def origin_workspace(client: dict):
    for tag in minimize_tags(client):
        number = tag[len(TAG_PREFIX):] if tag.startswith(TAG_PREFIX) else tag[len(LEGACY_TAG_PREFIX):]
        if number.isdigit() and int(number) >= 1 and int(number) != LEGACY_WS_ID:
            return int(number)
    return None

def untag_lua(tags: list) -> str:
    return " ".join(
        f'pcall(function() hl.dispatch(hl.dsp.window.tag({{ tag = "-{t}", window = w }})) end)' for t in tags)

def minimize_win(client: dict):
    addr = client.get("address")
    if not addr or is_minimized(client):
        return

    ws = client.get("workspace", {})
    ws_id = ws.get("id", 1)

    if client.get("floating"):
        geometries = load_geometries()
        geometries[addr] = {"at": client.get("at"), "size": client.get("size")}
        save_geometries(geometries)

    # Like Omarchy: one origin tag, the window to the hidden special workspace without following it,
    # and focus back on the workspace it left (else the next window opened would join it there).
    # Only when that workspace is the one in front: minimizing from a dock or a list never switches.
    lua_code = f"""(function()
        local cur = hl.get_cursor_pos()
        local w = hl.get_window("address:{addr}")
        if w then
            {untag_lua(minimize_tags(client))}
            -- "+" sets the tag (a bare tag name toggles it in Hyprland)
            pcall(function() hl.dispatch(hl.dsp.window.tag({{ tag = "+{TAG_PREFIX}{ws_id}", window = w }})) end)
            hl.dispatch(hl.dsp.window.move({{ workspace = "{MINIMIZED_WS}", follow = false, window = w }}))
            local active = hl.get_active_workspace()
            if active and active.id == {ws_id} then
                pcall(function() hl.dispatch(hl.dsp.focus({{ workspace = "{ws_id}" }})) end)
            end
            if cur and cur.x and cur.y then
                pcall(function() hl.dispatch(hl.dsp.cursor.move({{ x = cur.x, y = cur.y }})) end)
            end
        end
        return hl.dsp.no_op()
    end)()"""
    run_lua(lua_code)

def restore_win(client: dict):
    addr = client.get("address")
    if not addr:
        return

    # Only the minimize tags are removed: quick-tile's snapped_* tags must survive
    # (they let Alt+Enter un-maximize a window that was minimized while maximized)
    untag = untag_lua(minimize_tags(client))
    target_ws_id = origin_workspace(client)

    if target_ws_id is not None:
        target_clause = f"local target = {target_ws_id}"
    else:
        target_clause = "local target = (hl.get_active_workspace() and hl.get_active_workspace().id) or 1"

    geometries = load_geometries()
    geo = geometries.pop(addr, None)
    geometry_clause = ""
    if geo and client.get("floating") and geo.get("at") and geo.get("size"):
        (gx, gy), (gw, gh) = geo["at"], geo["size"]
        geometry_clause = (
            f"hl.dispatch(hl.dsp.window.resize({{ x = {int(gw)}, y = {int(gh)}, relative = false, window = w }})) "
            f"hl.dispatch(hl.dsp.window.move({{ x = {int(gx)}, y = {int(gy)}, relative = false, window = w }}))"
        )
    if geo is not None:
        save_geometries(geometries)

    # Restore window to workspace, bring to top (primer plano), focus, and keep cursor in place!
    lua_code = f"""(function()
        local cur = hl.get_cursor_pos()
        local w = hl.get_window("address:{addr}")
        if w then
            {target_clause}
            hl.dispatch(hl.dsp.window.move({{ workspace = target, follow = false, window = w }}))
            {geometry_clause}
            pcall(function() hl.dispatch(hl.dsp.window.bring_to_top({{ window = w }})) end)
            pcall(function() hl.dispatch(hl.dsp.window.alter_zorder({{ mode = "top", window = w }})) end)
            hl.dispatch(hl.dsp.focus({{ window = w }}))
            {untag}
            if cur and cur.x and cur.y then
                pcall(function() hl.dispatch(hl.dsp.cursor.move({{ x = cur.x, y = cur.y }})) end)
            end
        end
        return hl.dsp.no_op()
    end)()"""
    run_lua(lua_code)

def toggle_win(client: dict, active_addr: str):
    addr = client.get("address")
    if is_minimized(client):
        restore_win(client)
    elif addr == active_addr:
        minimize_win(client)
    else:
        # Focus and bring to top without warping mouse away from where clicked!
        lua_code = f"""(function()
            local cur = hl.get_cursor_pos()
            local w = hl.get_window("address:{addr}")
            if w then
                pcall(function() hl.dispatch(hl.dsp.window.bring_to_top({{ window = w }})) end)
                pcall(function() hl.dispatch(hl.dsp.window.alter_zorder({{ mode = "top", window = w }})) end)
                hl.dispatch(hl.dsp.focus({{ window = w }}))
                if cur and cur.x and cur.y then
                    pcall(function() hl.dispatch(hl.dsp.cursor.move({{ x = cur.x, y = cur.y }})) end)
                end
            end
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua_code)

def find_matching_clients(clients: list, app_id: str) -> list:
    if not app_id:
        return []
    
    if app_id.startswith("0x"):
        c = next((x for x in clients if x.get("address") == app_id), None)
        return [c] if c else []

    app_str = app_id.lower().strip()
    if app_str.endswith(".desktop"):
        app_str = app_str[:-8]

    # Check exact matches first
    exact = [c for c in clients if str(c.get("class", "")).lower() == app_str or str(c.get("initialClass", "")).lower() == app_str]
    if exact:
        return exact

    # Token-based matching
    parts = [app_str]
    if "." in app_str:
        parts.append(app_str.split(".")[-1])
    if "-" in app_str:
        parts.append(app_str.split("-")[0])

    fuzzy = []
    for c in clients:
        cls = str(c.get("class", "")).lower()
        init_cls = str(c.get("initialClass", "")).lower()
        targets = [cls, init_cls]
        if "." in cls:
            targets.append(cls.split(".")[-1])
        if "-" in cls:
            targets.append(cls.split("-")[0])

        for p in parts:
            if not p:
                continue
            if p in targets or any(p in t or t in p for t in targets if t):
                fuzzy.append(c)
                break
    return fuzzy

def read_show_desktop_state() -> list:
    try:
        with open(SHOW_DESKTOP_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("windows", []) if isinstance(data, dict) else []
    except Exception:
        return []

def write_show_desktop_state(addresses: list):
    tmp = SHOW_DESKTOP_STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"windows": addresses}, f)
    os.replace(tmp, SHOW_DESKTOP_STATE)

def show_desktop(clients: list, leave: bool = False, keep_focus: str = ""):
    """Toggle KDE-style Show Desktop over the active workspace of every monitor."""
    hidden = read_show_desktop_state()
    by_addr = {c.get("address"): c for c in clients}
    still_hidden = [by_addr[a] for a in hidden if a in by_addr and is_minimized(by_addr[a])]

    if still_hidden:
        # Restore least recently focused first so the previously active window ends on top
        still_hidden.sort(key=lambda c: c.get("focusHistoryID", 0), reverse=True)
        write_show_desktop_state([])
        for c in still_hidden:
            restore_win(c)
        if leave and keep_focus:
            run_lua(f"""(function()
                local w = hl.get_window("address:{keep_focus}")
                if w then
                    pcall(function() hl.dispatch(hl.dsp.window.alter_zorder({{ mode = "top", window = w }})) end)
                    hl.dispatch(hl.dsp.focus({{ window = w }}))
                end
                return hl.dsp.no_op()
            end)()""")
        return
    if leave:
        write_show_desktop_state([])
        return

    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]).decode("utf-8"))
    except Exception:
        monitors = []
    visible_ws = {m.get("activeWorkspace", {}).get("id") for m in monitors}
    targets = [
        c for c in clients
        if c.get("mapped", True) and not c.get("hidden", False) and not is_minimized(c)
        and c.get("workspace", {}).get("id") in visible_ws
    ]
    for c in targets:
        minimize_win(c)
    # Written last: Quickshell ends the mode when it sees a visible window
    write_show_desktop_state([c.get("address") for c in targets])

def main():
    if len(sys.argv) < 2:
        print("Usage: toggle-minimize.py <toggle|toggle-app|min|restore> [arg]")
        sys.exit(1)

    cmd = sys.argv[1].lower().strip()
    arg = sys.argv[2].strip() if len(sys.argv) > 2 else ""

    clients = get_clients()
    active = get_active_window()
    active_addr = active.get("address", "")

    if cmd == "min":
        target = None
        if arg:
            target = next((c for c in clients if c.get("address") == arg), None)
        if not target and active_addr:
            target = active
        if target:
            minimize_win(target)

    elif cmd == "restore":
        target = None
        if arg:
            target = next((c for c in clients if c.get("address") == arg), None)
        if target:
            restore_win(target)

    elif cmd == "toggle":
        target = None
        if arg:
            target = next((c for c in clients if c.get("address") == arg), None)
        if not target and active_addr:
            target = active
        if target:
            toggle_win(target, active_addr)

    elif cmd == "show-desktop":
        show_desktop(clients, leave=(arg == "leave"), keep_focus=active_addr)

    elif cmd == "toggle-app":
        matching = find_matching_clients(clients, arg)
        if not matching:
            sys.exit(0)

        # 1. If any window of this app is minimized -> RESTORE IT!
        minimized_match = next((c for c in matching if is_minimized(c)), None)
        if minimized_match:
            restore_win(minimized_match)
            return

        # 2. If currently focused window belongs to this app -> MINIMIZE IT!
        active_match = next((c for c in matching if c.get("address") == active_addr), None)
        if active_match:
            minimize_win(active_match)
            return

        # 3. Otherwise, focus the first window of this app, bring to top (primer plano), and preserve cursor!
        target_addr = matching[0]["address"]
        lua_code = f"""(function()
            local cur = hl.get_cursor_pos()
            local w = hl.get_window("address:{target_addr}")
            if w then
                pcall(function() hl.dispatch(hl.dsp.window.bring_to_top({{ window = w }})) end)
                pcall(function() hl.dispatch(hl.dsp.window.alter_zorder({{ mode = "top", window = w }})) end)
                hl.dispatch(hl.dsp.focus({{ window = w }}))
                if cur and cur.x and cur.y then
                    pcall(function() hl.dispatch(hl.dsp.cursor.move({{ x = cur.x, y = cur.y }})) end)
                end
            end
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua_code)

if __name__ == "__main__":
    main()

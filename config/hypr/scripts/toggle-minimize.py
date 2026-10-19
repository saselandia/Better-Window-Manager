#!/usr/bin/env python3
"""
Window minimize & restore manager for Hyprland and Quickshell (KDE Plasma style).
Usage:
  toggle-minimize.py min [address]
  toggle-minimize.py restore [address]
  toggle-minimize.py toggle [address]
  toggle-minimize.py toggle-app <appId>
"""

import sys
import json
import subprocess

def get_clients():
    try:
        out = subprocess.check_output(["hyprctl", "clients", "-j"]).decode("utf-8")
        return json.loads(out)
    except Exception:
        return []

def get_active_window():
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

def minimize_win(client: dict):
    addr = client.get("address")
    if not addr:
        return
    ws = client.get("workspace", {})
    ws_name = str(ws.get("name", ""))
    ws_id = ws.get("id", 1)

    if ws_name.startswith("special:minimized"):
        return

    # Move to special:minimized and immediately close the special workspace
    # so the screen NEVER dims and NO special workspace or minimized windows are displayed!
    lua_code = f"""(function()
        local w = hl.get_window("address:{addr}")
        if w then
            pcall(function() hl.dispatch(hl.dsp.window.tag({{ tag = "from_ws_{ws_id}", window = w }})) end)
            hl.dispatch(hl.dsp.window.move({{ workspace = "special:minimized", window = w }}))
            if hl.get_active_special_workspace() then
                hl.dispatch(hl.dsp.workspace.toggle_special("minimized"))
            end
        end
        return hl.dsp.no_op()
    end)()"""
    run_lua(lua_code)

def restore_win(client: dict):
    addr = client.get("address")
    if not addr:
        return

    target_ws_id = None
    tags = client.get("tags", [])
    for t in tags:
        if t.startswith("from_ws_"):
            orig_id = t.replace("from_ws_", "")
            if orig_id.isdigit():
                target_ws_id = int(orig_id)
                break

    if target_ws_id is not None:
        target_clause = f"local target = {target_ws_id}"
    else:
        target_clause = "local target = (hl.get_active_workspace() and hl.get_active_workspace().id) or 1"

    lua_code = f"""(function()
        local w = hl.get_window("address:{addr}")
        if w then
            {target_clause}
            hl.dispatch(hl.dsp.window.move({{ workspace = target, window = w }}))
            hl.dispatch(hl.dsp.focus({{ window = w }}))
            pcall(function() hl.dispatch(hl.dsp.window.clear_tags(w)) end)
            if hl.get_active_special_workspace() then
                hl.dispatch(hl.dsp.workspace.toggle_special("minimized"))
            end
        end
        return hl.dsp.no_op()
    end)()"""
    run_lua(lua_code)

def toggle_win(client: dict, active_addr: str):
    addr = client.get("address")
    ws_name = str(client.get("workspace", {}).get("name", ""))

    if ws_name.startswith("special:minimized"):
        restore_win(client)
    elif addr == active_addr:
        minimize_win(client)
    else:
        lua_code = f"""(function()
            local w = hl.get_window("address:{addr}")
            if w then
                hl.dispatch(hl.dsp.focus({{ window = w }}))
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

    elif cmd == "toggle-app":
        matching = find_matching_clients(clients, arg)
        if not matching:
            sys.exit(0)

        # 1. If any window of this app is minimized in special:minimized -> RESTORE IT!
        minimized_match = next((c for c in matching if str(c.get("workspace", {}).get("name", "")).startswith("special:minimized")), None)
        if minimized_match:
            restore_win(minimized_match)
            return

        # 2. If currently focused window belongs to this app -> MINIMIZE IT!
        active_match = next((c for c in matching if c.get("address") == active_addr), None)
        if active_match:
            minimize_win(active_match)
            return

        # 3. Otherwise, focus the first window of this app
        target_addr = matching[0]["address"]
        lua_code = f"""(function()
            local w = hl.get_window("address:{target_addr}")
            if w then
                hl.dispatch(hl.dsp.focus({{ window = w }}))
            end
            return hl.dsp.no_op()
        end)()"""
        run_lua(lua_code)

if __name__ == "__main__":
    main()

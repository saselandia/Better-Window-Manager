#!/usr/bin/env bash
""":":
exec python3 "$0" "$@"
"""
import os
import sys
import json
import argparse
import subprocess

CONFIG_PATH = os.path.expanduser("~/.config/hypr/modules/monitors.lua")
WORKSPACE_RULES_PATH = os.path.expanduser("~/.config/hypr/workspace_rules.json")
LAYOUT_PATH = os.path.expanduser("~/.config/hypr/monitors_layout.json")

def load_workspace_config():
    if os.path.exists(WORKSPACE_RULES_PATH):
        try:
            with open(WORKSPACE_RULES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"primary_monitor": "DP-2", "monitor_workspaces": {"DP-1": "10", "DP-2": "1-9"}}

def save_workspace_config(cfg):
    try:
        os.makedirs(os.path.dirname(WORKSPACE_RULES_PATH), exist_ok=True)
        with open(WORKSPACE_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving workspace config: {e}", file=sys.stderr)

def load_layout_config():
    if os.path.exists(LAYOUT_PATH):
        try:
            with open(LAYOUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Initial fallback values based on system configuration
    return {
        "desc:LG Electronics LG ULTRAFINE 405NTVS2J655": {
            "name": "DP-1",
            "x": 1920,
            "y": 0,
            "width": 3840,
            "height": 2160,
            "refreshRate": 60.0,
            "scale": 1.0,
            "transform": 0,
            "disabled": False
        },
        "desc:HP Inc. HP X24ih 1CR1420TD4": {
            "name": "DP-2",
            "x": 0,
            "y": 1080,
            "width": 1920,
            "height": 1080,
            "refreshRate": 144.0,
            "scale": 1.0,
            "transform": 0,
            "disabled": False
        }
    }

def save_layout_config(layout):
    try:
        os.makedirs(os.path.dirname(LAYOUT_PATH), exist_ok=True)
        with open(LAYOUT_PATH, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2)
    except Exception as e:
        print(f"Error saving layout config: {e}", file=sys.stderr)

def monitor_selector(m):
    desc = (m.get("description") or "").strip()
    return f"desc:{desc}" if desc else m.get("name", "")

def get_monitor_brightness(m_name):
    try:
        cmd = ["omarchy-brightness-display", "--monitor", m_name]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=1.5).decode("utf-8").strip()
        val = int(out)
        return max(0, min(100, val))
    except Exception:
        return 100

def set_monitor_brightness(m_name, percent):
    percent = max(1, min(100, int(percent)))
    try:
        cmd = ["omarchy-brightness-display", "--no-osd", "--monitor", m_name, f"{percent}%"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return True
    except Exception:
        return False

def get_nightlight_state():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        nl_py = os.path.join(script_dir, "nightlight.py")
        if os.path.exists(nl_py):
            out = subprocess.check_output(["python3", nl_py, "--status"], stderr=subprocess.DEVNULL, timeout=1).decode("utf-8")
            return json.loads(out)
    except Exception:
        pass
    return {"enabled": False, "temperature": 4000}

def get_monitors(with_brightness=False):
    try:
        out = subprocess.check_output(["hyprctl", "monitors", "all", "-j"], stderr=subprocess.DEVNULL).decode("utf-8")
        data = json.loads(out)
    except Exception as e:
        return []

    ws_cfg = load_workspace_config()
    layout_cfg = load_layout_config()
    primary_name = ws_cfg.get("primary_monitor", "DP-2")
    monitor_workspaces = ws_cfg.get("monitor_workspaces", {})

    connected_names = [m.get("name") for m in data]
    if primary_name not in connected_names and connected_names:
        primary_name = "DP-2" if "DP-2" in connected_names else connected_names[0]

    result = []
    for m in data:
        m_name = m.get("name", "")
        m_desc = m.get("description", "")
        sel = monitor_selector(m)
        saved = layout_cfg.get(sel) or layout_cfg.get(m_name) or {}

        modes = m.get("availableModes", [])
        res_map = {}
        for mode in modes:
            if "@" in mode:
                res, hz_str = mode.split("@", 1)
                hz_val = hz_str.replace("Hz", "").strip()
                try:
                    hz_float = round(float(hz_val), 1)
                    if res not in res_map:
                        res_map[res] = []
                    if hz_float not in res_map[res]:
                        res_map[res].append(hz_float)
                except Exception:
                    pass

        for r in res_map:
            res_map[r].sort(reverse=True)

        res_list = sorted(list(res_map.keys()), key=lambda r: int(r.split("x")[0]) * int(r.split("x")[1]), reverse=True)

        cur_w = m.get("width") or saved.get("width", 1920)
        cur_h = m.get("height") or saved.get("height", 1080)
        cur_res = f"{cur_w}x{cur_h}"
        if cur_res not in res_list and cur_res:
            res_list.insert(0, cur_res)
            res_map[cur_res] = [round(float(m.get("refreshRate") or saved.get("refreshRate", 60.0)), 1)]

        is_prim = (m_name == primary_name)
        assigned_ws = monitor_workspaces.get(m_name, "1-9" if is_prim else "10")

        # Position preservation
        cur_x = m.get("x", 0)
        cur_y = m.get("y", 0)
        if cur_x == 0 and cur_y == 0 and saved:
            cur_x = saved.get("x", 0)
            cur_y = saved.get("y", 0)

        cur_scale = m.get("scale", 1.0)
        if cur_scale == 1.0 and saved.get("scale"):
            cur_scale = saved.get("scale")

        cur_transform = m.get("transform", 0)
        if cur_transform == 0 and saved.get("transform"):
            cur_transform = saved.get("transform")

        b_val = 100
        if with_brightness and not m.get("disabled", False):
            b_val = get_monitor_brightness(m_name)

        result.append({
            "id": m.get("id", 0),
            "name": m_name,
            "description": m_desc,
            "model": m.get("model", "") or m_name,
            "make": m.get("make", ""),
            "width": cur_w,
            "height": cur_h,
            "refreshRate": round(float(m.get("refreshRate") or saved.get("refreshRate", 60.0)), 1),
            "x": cur_x,
            "y": cur_y,
            "scale": cur_scale,
            "transform": cur_transform,
            "focused": m.get("focused", False),
            "disabled": m.get("disabled", False),
            "is_primary": is_prim,
            "workspaces": assigned_ws,
            "resolutions": res_list,
            "modesMap": res_map,
            "availableModes": modes,
            "brightness": b_val
        })
    return result

def parse_workspace_range(ws_str):
    parts = []
    for item in ws_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            try:
                start, end = item.split("-", 1)
                for x in range(int(start), int(end) + 1):
                    parts.append(x)
            except Exception:
                pass
        else:
            try:
                parts.append(int(item))
            except Exception:
                pass
    return parts

def write_monitors_lua(monitors):
    ws_cfg = load_workspace_config()
    layout_cfg = load_layout_config()
    active_monitors = [m for m in monitors if not m.get("disabled")]
    
    primary_candidate = next((m["name"] for m in active_monitors if m.get("is_primary")), None)
    if primary_candidate:
        ws_cfg["primary_monitor"] = primary_candidate
    elif ws_cfg.get("primary_monitor") not in [m["name"] for m in active_monitors]:
        ws_cfg["primary_monitor"] = "DP-2" if any(m["name"] == "DP-2" for m in active_monitors) else (active_monitors[0]["name"] if active_monitors else "DP-2")

    if "monitor_workspaces" not in ws_cfg:
        ws_cfg["monitor_workspaces"] = {}

    for m in active_monitors:
        name = m["name"]
        if "workspaces" in m and m["workspaces"]:
            ws_cfg["monitor_workspaces"][name] = str(m["workspaces"]).strip()
        elif name == ws_cfg["primary_monitor"]:
            ws_cfg["monitor_workspaces"][name] = "1-9"
        else:
            ws_cfg["monitor_workspaces"][name] = "10"

    save_workspace_config(ws_cfg)

    # Update layout config
    for m in monitors:
        sel = monitor_selector(m)
        layout_cfg[sel] = {
            "name": m.get("name"),
            "x": m.get("x", 0),
            "y": m.get("y", 0),
            "width": m.get("width", 1920),
            "height": m.get("height", 1080),
            "refreshRate": m.get("refreshRate", 60.0),
            "scale": m.get("scale", 1.0),
            "transform": m.get("transform", 0),
            "disabled": m.get("disabled", False)
        }
    save_layout_config(layout_cfg)

    lines = [
        "------------------",
        "---- MONITORS ----",
        "------------------",
        "",
        "-- Archivo gestionado automáticamente por Quickshell Display Settings",
        "-- See https://wiki.hypr.land/Configuring/Basics/Monitors/",
        "-- Por descripción (desc:), no por conector: los nombres DP-N cambian si cambia el orden",
        "-- en que arrancan las GPU (iGPU AMD / NVIDIA) y entonces las reglas caen en el monitor equivocado.",
        "",
    ]

    for m in monitors:
        sel = monitor_selector(m)
        if m.get("disabled"):
            lines.append(f'hl.monitor({{ output = "{sel}", mode = "disable" }})')
            continue

        name = m.get("name")
        w = m.get("width", 1920)
        h = m.get("height", 1080)
        hz = m.get("refreshRate", 60.0)
        x = m.get("x", 0)
        y = m.get("y", 0)
        scale = m.get("scale", 1.0)
        transform = m.get("transform", 0)

        mode_str = f"{w}x{h}@{hz}" if hz else f"{w}x{h}"
        pos_str = f"{x}x{y}"
        scale_str = f"{scale}"

        lines.append(f"-- {name}")
        lines.append("hl.monitor({")
        lines.append(f'    output   = "{sel}",')
        lines.append(f'    mode     = "{mode_str}",')
        lines.append(f'    position = "{pos_str}",')
        lines.append(f'    scale    = "{scale_str}",')
        if transform:
            lines.append(f'    transform = {transform},')
        lines.append("})")
        lines.append("")

    lines.extend([
        "-------------------------",
        "---- WORKSPACE RULES ----",
        "-------------------------",
        "",
    ])

    primary_name = ws_cfg.get("primary_monitor", "DP-2")
    for m in active_monitors:
        m_name = m["name"]
        sel = monitor_selector(m)
        is_prim = (m_name == primary_name)
        ws_str = ws_cfg["monitor_workspaces"].get(m_name, "1-9" if is_prim else "10")
        
        if ws_str == "1-9":
            lines.append(f"-- Monitor Principal (Workspaces 1 al 9)")
            lines.append("for i = 1, 9 do")
            lines.append("    hl.workspace_rule({")
            lines.append("        workspace = tostring(i),")
            lines.append(f'        monitor   = "{sel}",')
            lines.append("        default   = (i == 1),")
            lines.append("        persistent = (i == 1),")
            lines.append("    })")
            lines.append("end")
            lines.append("")
        elif ws_str == "10":
            lines.append(f"-- Monitor Secundario: Workspace 10 persistente")
            lines.append("hl.workspace_rule({")
            lines.append('    workspace = "10",')
            lines.append(f'    monitor   = "{sel}",')
            lines.append("    default   = true,")
            lines.append("    persistent = true,")
            lines.append("})")
            lines.append("")
        else:
            parsed = parse_workspace_range(ws_str)
            if parsed:
                lines.append(f"-- Workspaces personalizados ({ws_str}) vinculados al monitor ({m_name})")
                for idx, ws_num in enumerate(parsed):
                    lines.append("hl.workspace_rule({")
                    lines.append(f'    workspace = "{ws_num}",')
                    lines.append(f'    monitor   = "{sel}",')
                    lines.append(f'    default   = {str(idx == 0).lower()},')
                    lines.append("})")
                lines.append("")

    content = "\n".join(lines)

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # Recargar Hyprland
    subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_target_monitor(monitors, name_or_desc):
    target = None
    for m in monitors:
        if m["name"] == name_or_desc or monitor_selector(m) == name_or_desc or m.get("description") == name_or_desc:
            return m
    return None

def main():
    parser = argparse.ArgumentParser(description="Gestor de Monitores para Hyprland (BWM)")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="Lista los monitores conectados en JSON")
    subparsers.add_parser("get-state", help="Devuelve el estado completo (monitores, brillo, luz nocturna) en JSON")

    mode_parser = subparsers.add_parser("set-mode", help="Establece resolución y tasa de refresco")
    mode_parser.add_argument("monitor", help="Nombre o descripción del monitor")
    mode_parser.add_argument("resolution", help="Resolución (ej. 1920x1080)")
    mode_parser.add_argument("refresh_rate", nargs="?", type=float, help="Tasa de refresco en Hz (ej. 144.0)")

    scale_parser = subparsers.add_parser("set-scale", help="Establece el escalado de un monitor")
    scale_parser.add_argument("monitor", help="Nombre o descripción del monitor")
    scale_parser.add_argument("scale", type=float, help="Escalado (ej. 1.25)")

    transform_parser = subparsers.add_parser("set-transform", help="Establece la rotación del monitor (0, 1, 2, 3)")
    transform_parser.add_argument("monitor", help="Nombre o descripción del monitor")
    transform_parser.add_argument("transform", type=int, choices=[0, 1, 2, 3], help="Rotación: 0=normal, 1=90, 2=180, 3=270")

    bright_parser = subparsers.add_parser("set-brightness", help="Establece el brillo de un monitor")
    bright_parser.add_argument("monitor", help="Nombre o descripción del monitor")
    bright_parser.add_argument("percent", type=int, help="Brillo en %% (1-100)")

    bright_get_parser = subparsers.add_parser("get-brightness", help="Obtiene el brillo de un monitor")
    bright_get_parser.add_argument("monitor", help="Nombre o descripción del monitor")

    toggle_parser = subparsers.add_parser("toggle-enable", help="Activa o desactiva un monitor")
    toggle_parser.add_argument("monitor", help="Nombre o descripción del monitor")
    toggle_parser.add_argument("state", nargs="?", choices=["enable", "disable", "toggle"], default="toggle")

    set_prim_parser = subparsers.add_parser("set-primary", help="Establece el monitor principal (workspaces 1-9)")
    set_prim_parser.add_argument("monitor", help="Nombre del monitor principal")

    apply_parser = subparsers.add_parser("apply", help="Aplica la configuración de monitores desde JSON")
    apply_parser.add_argument("json_data", help="JSON con la lista de monitores configurados")

    align_parser = subparsers.add_parser("align", help="Alinea un monitor relativo a otro")
    align_parser.add_argument("--target", required=True, help="Nombre del monitor a mover")
    align_parser.add_argument("--relative-to", required=True, help="Nombre del monitor de referencia")
    align_parser.add_argument("--direction", required=True, choices=["left", "right", "top", "bottom"], help="Dirección")

    args = parser.parse_args()

    if args.command == "list" or not args.command:
        mons = get_monitors(with_brightness=False)
        print(json.dumps(mons, indent=2))

    elif args.command == "get-state":
        mons = get_monitors(with_brightness=True)
        focused = next((m["name"] for m in mons if m.get("focused")), "")
        primary = next((m["name"] for m in mons if m.get("is_primary")), "")
        nl = get_nightlight_state()
        state = {
            "monitors": mons,
            "focused": focused,
            "primary": primary,
            "nightlight": nl
        }
        print(json.dumps(state, indent=2))

    elif args.command == "set-brightness":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        name = target["name"] if target else args.monitor
        ok = set_monitor_brightness(name, args.percent)
        print(json.dumps({"status": "success" if ok else "error", "brightness": args.percent, "monitor": name}))

    elif args.command == "get-brightness":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        name = target["name"] if target else args.monitor
        b = get_monitor_brightness(name)
        print(json.dumps({"status": "success", "brightness": b, "monitor": name}))

    elif args.command == "set-scale":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor {args.monitor} no encontrado"}), file=sys.stderr)
            sys.exit(1)
        target["scale"] = float(args.scale)
        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "monitor": target["name"], "scale": target["scale"]}))

    elif args.command == "set-mode":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor {args.monitor} no encontrado"}), file=sys.stderr)
            sys.exit(1)
        try:
            w_str, h_str = args.resolution.split("x", 1)
            target["width"] = int(w_str)
            target["height"] = int(h_str)
        except Exception:
            print(json.dumps({"status": "error", "message": f"Formato de resolución inválido: {args.resolution}"}), file=sys.stderr)
            sys.exit(1)

        if args.refresh_rate:
            target["refreshRate"] = float(args.refresh_rate)
        else:
            rates = target.get("modesMap", {}).get(args.resolution, [])
            if rates:
                target["refreshRate"] = float(rates[0])

        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "monitor": target["name"], "resolution": args.resolution, "refreshRate": target["refreshRate"]}))

    elif args.command == "set-transform":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor {args.monitor} no encontrado"}), file=sys.stderr)
            sys.exit(1)
        target["transform"] = int(args.transform)
        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "monitor": target["name"], "transform": target["transform"]}))

    elif args.command == "toggle-enable":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor {args.monitor} no encontrado"}), file=sys.stderr)
            sys.exit(1)

        active_count = len([m for m in mons if not m.get("disabled")])
        cur_disabled = target.get("disabled", False)

        if args.state == "enable":
            new_disabled = False
        elif args.state == "disable":
            new_disabled = True
        else:
            new_disabled = not cur_disabled

        if new_disabled and active_count <= 1 and not cur_disabled:
            print(json.dumps({"status": "error", "message": "No se puede apagar la única pantalla activa"}), file=sys.stderr)
            sys.exit(1)

        target["disabled"] = new_disabled
        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "monitor": target["name"], "disabled": new_disabled}))

    elif args.command == "set-primary":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.monitor)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor '{args.monitor}' no encontrado"}), file=sys.stderr)
            sys.exit(1)
        for m in mons:
            if m["name"] == target["name"]:
                m["is_primary"] = True
                m["workspaces"] = "1-9"
            else:
                m["is_primary"] = False
                m["workspaces"] = "10"
        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "message": f"Monitor '{target['name']}' establecido como principal (workspaces 1-9)"}))

    elif args.command == "apply":
        try:
            mons = json.loads(args.json_data)
            write_monitors_lua(mons)
            print(json.dumps({"status": "success", "message": "Configuración aplicada y guardada en monitors.lua"}))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
            sys.exit(1)

    elif args.command == "align":
        mons = get_monitors(with_brightness=False)
        target = find_target_monitor(mons, args.target)
        ref = find_target_monitor(mons, args.relative_to)
        if not target or not ref:
            print(json.dumps({"status": "error", "message": "Monitor no encontrado"}), file=sys.stderr)
            sys.exit(1)

        if args.direction == "right":
            target["x"] = ref["x"] + ref["width"]
            target["y"] = ref["y"]
        elif args.direction == "left":
            target["x"] = max(0, ref["x"] - target["width"])
            target["y"] = ref["y"]
        elif args.direction == "bottom":
            target["x"] = ref["x"]
            target["y"] = ref["y"] + ref["height"]
        elif args.direction == "top":
            target["x"] = ref["x"]
            target["y"] = max(0, ref["y"] - target["height"])

        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "monitors": mons}))

if __name__ == "__main__":
    main()

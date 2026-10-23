#!/usr/bin/env bash
""":":
exec python3 "bash" ""
"""
import os
import sys
import json
import argparse
import subprocess

CONFIG_PATH = os.path.expanduser("~/.config/hypr/modules/monitors.lua")
WORKSPACE_RULES_PATH = os.path.expanduser("~/.config/hypr/workspace_rules.json")

def load_workspace_config():
    if os.path.exists(WORKSPACE_RULES_PATH):
        try:
            with open(WORKSPACE_RULES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"primary_monitor": "DP-1", "monitor_workspaces": {"DP-1": "1-9", "DP-2": "10"}}

def save_workspace_config(cfg):
    try:
        os.makedirs(os.path.dirname(WORKSPACE_RULES_PATH), exist_ok=True)
        with open(WORKSPACE_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving workspace config: {e}", file=sys.stderr)

def get_monitors():
    try:
        out = subprocess.check_output(["hyprctl", "monitors", "all", "-j"], stderr=subprocess.DEVNULL).decode("utf-8")
        data = json.loads(out)
    except Exception as e:
        return []

    ws_cfg = load_workspace_config()
    primary_name = ws_cfg.get("primary_monitor", "DP-1")
    monitor_workspaces = ws_cfg.get("monitor_workspaces", {})
    
    connected_names = [m.get("name") for m in data]
    if primary_name not in connected_names and connected_names:
        primary_name = "DP-1" if "DP-1" in connected_names else connected_names[0]

    result = []
    for m in data:
        m_name = m.get("name", "")
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

        cur_w = m.get("width", 1920)
        cur_h = m.get("height", 1080)
        cur_res = f"{cur_w}x{cur_h}"
        if cur_res not in res_list and cur_res:
            res_list.insert(0, cur_res)
            res_map[cur_res] = [round(float(m.get("refreshRate", 60.0)), 1)]

        is_prim = (m_name == primary_name)
        assigned_ws = monitor_workspaces.get(m_name, "1-9" if is_prim else "10")

        result.append({
            "id": m.get("id", 0),
            "name": m_name,
            "description": m.get("description", ""),
            "model": m.get("model", "") or m_name,
            "make": m.get("make", ""),
            "width": cur_w,
            "height": cur_h,
            "refreshRate": round(float(m.get("refreshRate", 60.0)), 1),
            "x": m.get("x", 0),
            "y": m.get("y", 0),
            "scale": m.get("scale", 1.0),
            "focused": m.get("focused", False),
            "disabled": m.get("disabled", False),
            "is_primary": is_prim,
            "workspaces": assigned_ws,
            "resolutions": res_list,
            "modesMap": res_map,
            "availableModes": modes
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

def monitor_selector(m):
    """desc:<descripción> en vez del conector: los nombres DP-N cambian si cambia el orden en
    que arrancan las GPU (p. ej. la iGPU AMD antes que la NVIDIA) y las reglas por nombre
    acaban en el monitor equivocado (resolución mala, monitores superpuestos)."""
    desc = (m.get("description") or "").strip()
    return f"desc:{desc}" if desc else m.get("name", "")

def write_monitors_lua(monitors):
    ws_cfg = load_workspace_config()
    active_monitors = [m for m in monitors if not m.get("disabled")]
    
    primary_candidate = next((m["name"] for m in active_monitors if m.get("is_primary")), None)
    if primary_candidate:
        ws_cfg["primary_monitor"] = primary_candidate
    elif ws_cfg.get("primary_monitor") not in [m["name"] for m in active_monitors]:
        ws_cfg["primary_monitor"] = "DP-1" if any(m["name"] == "DP-1" for m in active_monitors) else (active_monitors[0]["name"] if active_monitors else "DP-1")

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

    lines = [
        "------------------",
        "---- MONITORS ----",
        "------------------",
        "",
        "-- Archivo gestionado automáticamente por Quickshell Display Settings",
        "-- See https://wiki.hypr.land/Configuring/Basics/Monitors/",
    ]

    for m in monitors:
        if m.get("disabled"):
            lines.append(f'hl.monitor({{ output = "{monitor_selector(m)}", mode = "disable" }})')
            continue

        name = m.get("name")
        w = m.get("width", 1920)
        h = m.get("height", 1080)
        hz = m.get("refreshRate", 60.0)
        x = m.get("x", 0)
        y = m.get("y", 0)
        scale = m.get("scale", 1.0)

        mode_str = f"{w}x{h}@{hz}" if hz else f"{w}x{h}"
        pos_str = f"{x}x{y}"
        scale_str = f"{scale}"

        lines.append(f"-- {name}")
        lines.append("hl.monitor({")
        lines.append(f'    output   = "{monitor_selector(m)}",')
        lines.append(f'    mode     = "{mode_str}",')
        lines.append(f'    position = "{pos_str}",')
        lines.append(f'    scale    = "{scale_str}",')
        lines.append("})")

    lines.extend([
        "",
        "-------------------------",
        "---- WORKSPACE RULES ----",
        "-------------------------",
        "",
    ])

    primary_name = ws_cfg.get("primary_monitor", "DP-1")
    for m in active_monitors:
        m_name = m["name"]
        sel = monitor_selector(m)
        is_prim = (m_name == primary_name)
        ws_str = ws_cfg["monitor_workspaces"].get(m_name, "1-9" if is_prim else "10")
        
        if ws_str == "1-9":
            lines.append(f"-- Workspaces 1 al 9 vinculados al monitor ({m_name}){' [Principal]' if is_prim else ''}")
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
            lines.append(f"-- Workspace 10 vinculado al monitor ({m_name}){' [Secundario]' if not is_prim else ''}")
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

    # Migrar workspaces activos a sus monitores asignados inmediatamente
    try:
        ws_out = subprocess.check_output(["hyprctl", "workspaces", "-j"], stderr=subprocess.DEVNULL).decode("utf-8")
        current_workspaces = json.loads(ws_out)
        target_map = {}
        for m_name, ws_str in ws_cfg.get("monitor_workspaces", {}).items():
            for w in parse_workspace_range(ws_str):
                target_map[w] = m_name
        for cw in current_workspaces:
            wid = cw.get("id")
            cur_mon = cw.get("monitor")
            if wid in target_map and target_map[wid] != cur_mon:
                target_mon = target_map[wid]
                subprocess.run([
                    "hyprctl", "dispatch",
                    f"hl.dsp.workspace.move({{ workspace = {wid}, monitor = '{target_mon}' }})"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Gestor de Monitores para Hyprland")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="Lista los monitores conectados en JSON")

    apply_parser = subparsers.add_parser("apply", help="Aplica la configuración de monitores desde JSON")
    apply_parser.add_argument("json_data", help="JSON con la lista de monitores configurados")

    set_prim_parser = subparsers.add_parser("set-primary", help="Establece el monitor principal (workspaces 1-9)")
    set_prim_parser.add_argument("monitor_name", help="Nombre del monitor principal (ej. DP-3)")

    align_parser = subparsers.add_parser("align", help="Alinea un monitor relativo a otro")
    align_parser.add_argument("--target", required=True, help="Nombre del monitor a mover")
    align_parser.add_argument("--relative-to", required=True, help="Nombre del monitor de referencia")
    align_parser.add_argument("--direction", required=True, choices=["left", "right", "top", "bottom"], help="Dirección")

    args = parser.parse_args()

    if args.command == "list" or not args.command:
        mons = get_monitors()
        print(json.dumps(mons, indent=2))
    elif args.command == "apply":
        try:
            mons = json.loads(args.json_data)
            write_monitors_lua(mons)
            print(json.dumps({"status": "success", "message": "Configuración aplicada y guardada en monitors.lua"}))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
            sys.exit(1)
    elif args.command == "set-primary":
        mons = get_monitors()
        target = next((m for m in mons if m["name"] == args.monitor_name), None)
        if not target:
            print(json.dumps({"status": "error", "message": f"Monitor '{args.monitor_name}' no encontrado"}), file=sys.stderr)
            sys.exit(1)
        for m in mons:
            if m["name"] == args.monitor_name:
                m["is_primary"] = True
                m["workspaces"] = "1-9"
            else:
                m["is_primary"] = False
                m["workspaces"] = "10"
        write_monitors_lua(mons)
        print(json.dumps({"status": "success", "message": f"Monitor '{args.monitor_name}' establecido como principal (workspaces 1-9)"}))
    elif args.command == "align":
        mons = get_monitors()
        target = next((m for m in mons if m["name"] == args.target), None)
        ref = next((m for m in mons if m["name"] == args.relative_to), None)
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

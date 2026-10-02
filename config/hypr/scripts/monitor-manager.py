#!/usr/bin/env bash
""":"
exec python3 "$0" "$@"
"""
import os
import sys
import json
import argparse
import subprocess

CONFIG_PATH = os.path.expanduser("~/.config/hypr/modules/monitors.lua")

def get_monitors():
    try:
        out = subprocess.check_output(["hyprctl", "monitors", "all", "-j"], stderr=subprocess.DEVNULL).decode("utf-8")
        data = json.loads(out)
    except Exception as e:
        return []

    result = []
    for m in data:
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

        result.append({
            "id": m.get("id", 0),
            "name": m.get("name", ""),
            "description": m.get("description", ""),
            "model": m.get("model", "") or m.get("name", ""),
            "make": m.get("make", ""),
            "width": cur_w,
            "height": cur_h,
            "refreshRate": round(float(m.get("refreshRate", 60.0)), 1),
            "x": m.get("x", 0),
            "y": m.get("y", 0),
            "scale": m.get("scale", 1.0),
            "focused": m.get("focused", False),
            "disabled": m.get("disabled", False),
            "resolutions": res_list,
            "modesMap": res_map,
            "availableModes": modes
        })
    return result

def write_monitors_lua(monitors):
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
            lines.append(f'hl.monitor({{ output = "{m["name"]}", mode = "disable" }})')
            continue

        name = m.get("name")
        w = m.get("width", 1920)
        h = m.get("height", 1080)
        hz = m.get("refreshRate", 60.0)
        x = m.get("x", 0)
        y = m.get("y", 0)
        scale = m.get("scale", 1.0)

        # Formato de modo
        mode_str = f"{w}x{h}@{hz}" if hz else f"{w}x{h}"
        pos_str = f"{x}x{y}"
        scale_str = f"{scale}"

        lines.append("hl.monitor({")
        lines.append(f'    output   = "{name}",')
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

    # Enlazar workspaces al monitor primario/secundario si hay múltiples
    active_monitors = [m for m in monitors if not m.get("disabled")]
    if active_monitors:
        primary = active_monitors[0]["name"]
        lines.append(f"-- Workspaces 1 al 9 vinculados al monitor principal ({primary})")
        lines.append("for i = 1, 9 do")
        lines.append("    hl.workspace_rule({")
        lines.append("        workspace = tostring(i),")
        lines.append(f'        monitor   = "{primary}",')
        lines.append("        default   = (i == 1),")
        lines.append("    })")
        lines.append("end")

        if len(active_monitors) > 1:
            sec = active_monitors[1]["name"]
            lines.append("")
            lines.append(f"-- Workspace 10 vinculado al monitor secundario ({sec})")
            lines.append("hl.workspace_rule({")
            lines.append('    workspace = "10",')
            lines.append(f'    monitor   = "{sec}",')
            lines.append("    default   = true,")
            lines.append("})")

    lines.append("")
    content = "\n".join(lines)

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # Recargar Hyprland
    subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser(description="Gestor de Monitores para Hyprland")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="Lista los monitores conectados en JSON")

    apply_parser = subparsers.add_parser("apply", help="Aplica la configuración de monitores desde JSON")
    apply_parser.add_argument("json_data", help="JSON con la lista de monitores configurados")

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

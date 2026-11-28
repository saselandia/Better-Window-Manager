#!/usr/bin/env python3
"""Matriz de ciclo de vida del anfitrión nativo de Plasma entre skins (R9).

Recorre una secuencia de skins con el gestor común (`bwm-theme-manager.py set`) y, tras
cada cambio, comprueba en la sesión real:

* en Breeze: `plasma-host.py status` ready con PID vivo, un panel nativo
  (`bwm-r4-native-policy`) y un escritorio (`bwm-r5-desktop`) por monitor, y ninguna capa
  del respaldo Quickshell (`quickshell:plasmaPanel`, `quickshell:plasmaDesktop`);
* fuera de Breeze: host detenido y ninguna capa `bwm-r4-*`/`bwm-r5-*`;
* siempre: una sola instancia `qs -c ii`, `hyprctl configerrors` vacío, las mismas
  ventanas (dirección+PID) en el mismo workspace, workspaces visibles iguales y las
  reservas de monitores iguales a las de la misma skin en la pasada anterior.

No crea ventanas, no mueve el puntero, no carga plugins ni escribe configuración del
usuario: sólo cambia de skin con el gestor y vuelve a la skin inicial al terminar.
Los monitores se identifican por descripción. Uso:

    python3 check-skin-lifecycle.py --run [--sequence plasma,retro,plasma,default,plasma]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
MANAGER = HOME / ".config/hypr/scripts/bwm-theme-manager.py"
PLASMA_HOST = HOME / ".config/hypr/skins/plasma/scripts/plasma-host.py"
NATIVE_PANEL = "bwm-r4-native-policy"
NATIVE_DESKTOP = "bwm-r5-desktop"
FALLBACK = ("quickshell:plasmaPanel", "quickshell:plasmaDesktop")


def hypr(*args: str):
    out = subprocess.run(["hyprctl", "-j", *args], capture_output=True, text=True, timeout=5)
    if out.returncode:
        raise RuntimeError(f"hyprctl {' '.join(args)}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def shell_count() -> int:
    """Instancias vivas del shell `ii` según Quickshell (no cuenta llamadas `ipc`/`log`)."""
    sys.path.insert(0, str(HOME / ".config/hypr/scripts"))
    import bwm_session
    return len(bwm_session.shell_instances())


def snapshot() -> dict:
    monitors = hypr("monitors")
    names = {m["name"]: m["description"] for m in monitors}
    layers = {}
    for name, data in hypr("layers").items():
        ns = [l["namespace"] for lv in data["levels"].values() for l in lv]
        layers[names.get(name, name)] = sorted(ns)
    clients = {f'{c["address"]}:{c["pid"]}': c["workspace"]["name"]
               for c in hypr("clients") if c.get("mapped", True)}
    host = json.loads(subprocess.run([sys.executable, str(PLASMA_HOST), "status"],
                                     capture_output=True, text=True, timeout=10).stdout or "{}")
    errors = subprocess.run(["hyprctl", "configerrors"], capture_output=True, text=True).stdout.strip()
    return {
        "skin": subprocess.run([sys.executable, str(MANAGER), "get"], capture_output=True,
                               text=True).stdout.strip(),
        "monitors": {m["description"]: {"workspace": m["activeWorkspace"]["name"],
                                        "reserved": m["reserved"]} for m in monitors},
        "layers": layers,
        "clients": clients,
        "host": {k: host.get(k) for k in ("running", "ready", "pid")},
        "shells": shell_count(),
        "configErrors": errors,
    }


def wait_settled(skin: str, timeout: float = 12.0) -> dict:
    """Espera a que el estado converja para la skin; devuelve la última instantánea."""
    deadline = time.monotonic() + timeout
    snap = snapshot()
    while time.monotonic() < deadline:
        if not problems(snap, skin):
            time.sleep(1.0)  # margen para reservas/capas tardías
            return snapshot()
        time.sleep(0.5)
        snap = snapshot()
    return snap


def problems(snap: dict, skin: str) -> list[str]:
    out = []
    if snap["skin"] != skin:
        out.append(f"skin activa {snap['skin']!r}, esperada {skin!r}")
    if snap["shells"] != 1:
        out.append(f"{snap['shells']} instancias de qs -c ii")
    if snap["configErrors"] and snap["configErrors"] != "no errors":
        out.append("hyprctl configerrors no vacío")
    for desc, ns in snap["layers"].items():
        if skin == "plasma":
            if ns.count(NATIVE_PANEL) < 1 or ns.count(NATIVE_DESKTOP) != 1:
                out.append(f"{desc}: capas nativas {ns.count(NATIVE_PANEL)}/{ns.count(NATIVE_DESKTOP)}")
            dup = [n for n in ns if n in FALLBACK]
            if dup:
                out.append(f"{desc}: respaldo Quickshell duplicado {dup}")
        else:
            nat = [n for n in ns if n.startswith(("bwm-r4-", "bwm-r5-"))]
            if nat:
                out.append(f"{desc}: capas nativas fuera de Breeze {nat}")
    if skin == "plasma" and not (snap["host"]["running"] and snap["host"]["ready"]):
        out.append(f"host no listo: {snap['host']}")
    if skin != "plasma" and snap["host"]["running"]:
        out.append(f"host sigue activo fuera de Breeze: {snap['host']}")
    return out


def run(sequence: list[str]) -> dict:
    initial = snapshot()
    report = {"initial": initial, "steps": [], "passed": True}
    by_skin: dict[str, dict] = {initial["skin"]: initial}
    try:
        for skin in sequence:
            started = time.monotonic()
            import tempfile
            with tempfile.TemporaryFile(mode="w+") as out_f, tempfile.TemporaryFile(mode="w+") as err_f:
                res = subprocess.run([sys.executable, str(MANAGER), "set", skin],
                                     stdout=out_f, stderr=err_f, timeout=120)
                err_f.seek(0)
                err_text = err_f.read()
            switch_s = round(time.monotonic() - started, 2)
            snap = wait_settled(skin)
            issues = problems(snap, skin)
            if res.returncode:
                issues.append(f"gestor salió con {res.returncode}: {err_text.strip()[-400:]}")
            lost = sorted(set(initial["clients"]) - set(snap["clients"]))
            moved = sorted(k for k, ws in initial["clients"].items()
                           if k in snap["clients"] and snap["clients"][k] != ws)
            if moved:
                issues.append(f"ventanas cambiaron de workspace: {len(moved)}")
            visible = {d: m["workspace"] for d, m in snap["monitors"].items()}
            if visible != {d: m["workspace"] for d, m in initial["monitors"].items()}:
                issues.append(f"workspaces visibles cambiaron: {visible}")
            prev = by_skin.get(skin)
            if prev:
                res_now = {d: m["reserved"] for d, m in snap["monitors"].items()}
                res_prev = {d: m["reserved"] for d, m in prev["monitors"].items()}
                if res_now != res_prev:
                    issues.append(f"reservas distintas a la pasada anterior: {res_prev} → {res_now}")
            by_skin[skin] = snap
            step = {"skin": skin, "switchSeconds": switch_s, "issues": issues,
                    "lostWindows": len(lost), "host": snap["host"],
                    "reserved": {d: m["reserved"] for d, m in snap["monitors"].items()},
                    "layers": snap["layers"]}
            report["steps"].append(step)
            print(f"{skin:8} {switch_s:5}s  {'OK' if not issues else '; '.join(issues)}"
                  + (f"  (ventanas cerradas durante el ensayo: {len(lost)})" if lost else ""),
                  flush=True)
            if issues:
                report["passed"] = False
    finally:
        if snapshot()["skin"] != initial["skin"]:
            subprocess.run([sys.executable, str(MANAGER), "set", initial["skin"]],
                           capture_output=True, text=True, timeout=120)
        report["final"] = snapshot()
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", action="store_true", help="ejecutar la matriz en la sesión real")
    ap.add_argument("--sequence", default="retro,plasma,default,plasma")
    ap.add_argument("--report", default=str(Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
                                            / "bwm-skin-lifecycle.json"))
    args = ap.parse_args()
    if not args.run:
        ap.print_help()
        return 2
    sequence = [s.strip() for s in args.sequence.split(",") if s.strip()]
    report = run(sequence)
    Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(("PASS" if report["passed"] else "FAIL") + f"  informe: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

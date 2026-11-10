#!/usr/bin/env python3
"""BWMenu: galería de skins y diagnóstico, con consola de rescate independiente.

--open abre una ventana autónoma; --open --tui abre una terminal limpia.
--tui funciona también sin Quickshell/Qt y desde una TTY.
--report [--json] permite consultar el mismo diagnóstico sin interfaz.
"""
import argparse
import fcntl
import importlib.util
import json
import os
import re
import select
import shutil
import subprocess
import sys
import termios
import textwrap
import tty
from pathlib import Path

from bwm_versions import bwm_version, output

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parents[2]
APP_ID = "org.bwm.menu"
CONSOLE_APP_ID = "org.bwm.menu.console"
GUI_QML = REPO / "config/quickshell/bwmenu/shell.qml"
STATUS = {"ok": "OK", "missing": "FALTA", "outdated": "ANTIGUA",
          "pending": "PENDIENTE", "build": "RECOMPILAR"}


def requirements_module():
    spec = importlib.util.spec_from_file_location("bwm_requirements", SCRIPTS / "bwm-requirements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot():
    data = {"version": bwm_version(REPO), "repo": str(REPO)}
    try:
        data.update(requirements_module().report(None, False, None, versions=True))
    except Exception as exc:
        data.update(error=str(exc), current="", skins=[], core={"ok": False})
    try:
        data["hyprland"] = json.loads(output(["hyprctl", "version", "-j"]))
    except ValueError:
        data["hyprland"] = {}
    installed = re.search(r"Hyprland ([0-9][0-9.]*)", output(["Hyprland", "--version"]))
    data["installedHyprland"] = installed[1] if installed else "sin dato"
    # list sólo consulta la instancia; nunca qs -c ii sin subcomando.
    try:
        from bwm_session import shell_instances
        data["shellPids"] = [item["pid"] for item in shell_instances()]
    except Exception:
        data["shellPids"] = []
    data["configErrors"] = output(["hyprctl", "configerrors"]) if data["hyprland"] else ""
    return data


def diagnostic_lines(data):
    running = data["hyprland"]
    lines = [f"BWM: {data['version']}", f"Carpeta: {data['repo']}",
             f"Skin activa: {data.get('current') or 'sin dato'}",
             f"Hyprland en ejecución: {running.get('version', 'sin conexión')}",
             f"Hyprland instalado (próxima sesión): {data['installedHyprland']}",
             f"Commit en ejecución: {running.get('commit', 'sin dato')}",
             "Quickshell ii: " + ("en marcha · PID " + ", ".join(map(str, data["shellPids"]))
                                    if data["shellPids"] else "sin instancia detectada"),
             "Errores de configuración: " + (data["configErrors"] or
                                            ("ninguno" if running else "sin conexión"))]
    if data.get("error"):
        lines.append("Error leyendo requisitos: " + data["error"])
    if running:
        for name in ("Aquamarine", "Hyprlang", "Hyprutils", "Hyprcursor", "Hyprgraphics"):
            built, system = running.get("build" + name), running.get("system" + name)
            if built or system:
                lines.append(f"{name}: compilación {built or '?'} · sistema {system or '?'}")
    return lines


def plain_report(data):
    lines = diagnostic_lines(data)
    for group in [dict(data["core"], name="Núcleo"), *data["skins"]]:
        lines.extend(["", group["name"]])
        for optional, key in ((False, "requires"), (True, "recommends")):
            for row in group.get(key, []):
                lines.append(f"  [{STATUS[row['status']]}{' · opcional' if optional else ''}] {row['label']}: "
                             f"{row['version'] or 'versión sin dato'} · {row['versionPolicy']}")
                if row["detail"]:
                    lines.append("    " + row["detail"])
    return "\n".join(lines)


def open_window(terminal=False):
    # Reutiliza la ventana antes de lanzar otra; el candado de la TUI resuelve carreras.
    try:
        clients = json.loads(output(["hyprctl", "clients", "-j"]))
    except ValueError:
        clients = []
    for client in clients:
        if client.get("class") in ((CONSOLE_APP_ID,) if terminal else (APP_ID, CONSOLE_APP_ID)):
            pid = int(client["pid"])
            output(["hyprctl", "dispatch", f'hl.dsp.focus({{ window = "pid:{pid}" }})'])
            return 0
    if not os.environ.get("WAYLAND_DISPLAY"):
        return main(["--tui"])
    from bwm_session import spawn
    if not terminal and shutil.which("qs") and GUI_QML.is_file():
        return 0 if spawn([sys.executable, str(Path(__file__).resolve()), "--gui"]) else 1
    kitty = shutil.which("kitty")
    if not kitty:
        print("BWMenu necesita kitty para abrir una ventana. Desde una consola: bwm menu --tui", file=sys.stderr)
        return 1
    # Ignora la configuración de Kitty por si el fallo viene del tema o de sus includes.
    argv = [kitty, "--config", "NONE", "--class", CONSOLE_APP_ID, "--title", "BWMenu · Consola",
            "-o", "remember_window_size=no", "-o", "initial_window_width=112c",
            "-o", "initial_window_height=36c", "-o", "font_size=12",
            "-o", "background=#111827", "-o", "foreground=#e5e7eb",
            "-o", "background_opacity=1", "-o", "shell_integration=disabled",
            sys.executable, str(Path(__file__).resolve()), "--tui"]
    return 0 if spawn(argv) else 1


def graphical():
    """Instancia aparte del shell ii; caída o error de carga → consola de rescate."""
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "bwm-menu-gui.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        with (runtime / "bwm-menu.log").open("w") as log:
            try:
                process = subprocess.Popen(["qs", "-n", "-p", str(GUI_QML)], stdout=log, stderr=log)
                code = process.wait()
                if code == 0:
                    return 0
            except OSError:
                pass
        return open_window(terminal=True)


def clean(text):
    # Los logs y nombres de terceros son datos, no secuencias de control de terminal.
    return "".join(c for c in str(text).expandtabs(4) if c == "\n" or (ord(c) >= 32 and not 127 <= ord(c) < 160))


def shell_log_text():
    from bwm_session import SHELL_LOG
    try:
        with open(SHELL_LOG, "rb") as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 32000))
            return "\n".join(stream.read().decode("utf-8", errors="replace").splitlines()[-100:]) or "El registro está vacío."
    except OSError:
        return "No se encuentra " + SHELL_LOG


class Menu:
    def __init__(self):
        self.data = {}
        self.pages = []
        self.message = ""
        self.frame = None
        self.appearance = {}
        self.appearance_stamp = None

    def push(self, title, rows, intro=""):
        self.pages.append({"title": title, "rows": rows, "intro": intro, "selected": 0})

    def view(self, title, text):
        # Filas por párrafo: las flechas permiten recorrer logs o comandos largos.
        rows = [{"label": line or " ", "detail": line} for line in str(text).splitlines()]
        self.push(title, rows or [{"label": "Sin datos"}], "Esc: volver · flechas: recorrer")

    def refresh(self):
        self.message = "Leyendo versiones y comprobando requisitos…"
        self.draw()
        self.data = snapshot()
        self.pages = []
        self.message = ""
        self.push("Inicio", [
            {"label": "Estado de BWM y versiones", "action": self.overview,
             "detail": "Revisión de BWM, Hyprland en ejecución y estado de la barra."},
            {"label": "Dependencias: versiones y compatibilidad", "action": self.dependencies,
             "detail": "Requisitos del núcleo y de cada skin, mínimos y comandos para resolver lo que falta."},
            {"label": "Skins instaladas / aplicar una skin", "action": self.skins,
             "detail": "Consulta sus requisitos y activa una skin con el gestor habitual de BWM."},
            {"label": "Recuperar barra y paneles", "action": self.recovery,
             "detail": "Reiniciar Quickshell, recargar Hyprland o consultar errores sin usar la barra."},
            {"label": "Ayuda y recuperación desde consola", "action": self.help},
            {"label": "Actualizar diagnóstico", "action": self.refresh},
            {"label": "Salir", "action": lambda: self.pages.clear()},
        ], "Mantén + y pulsa - (o al revés). También las teclas + y - del teclado numérico.")

    def overview(self):
        self.view("Estado y versiones", "\n".join(diagnostic_lines(self.data)))

    def dependencies(self):
        rows = [{"label": "Núcleo de BWM", "action": lambda: self.group(self.data["core"], "Núcleo")}]
        for skin in self.data["skins"]:
            rows.append({"label": skin["name"], "action": lambda s=skin: self.group(s, s["name"])})
        self.push("Dependencias", rows,
                  self.data.get("error") or "OK significa que pasa la comprobación declarada; no garantiza toda versión futura.")

    def group(self, group, title):
        rows = []
        for key, optional in (("requires", False), ("recommends", True)):
            for row in group.get(key, []):
                detail = [row["why"], f"Versión: {row['version'] or 'sin dato'}",
                          f"Exigida: {row['versionPolicy']}", f"Estado: {STATUS[row['status']]}"]
                if row.get("testedVersion"):
                    detail.append("Referencia probada: " + row["testedVersion"])
                if row["versionSource"]:
                    detail.append("Origen del dato: " + row["versionSource"])
                if row["detail"]:
                    detail.append(row["detail"])
                rows.append({"label": f"[{STATUS[row['status']]}]{' [opcional]' if optional else ''} {row['label']}"
                                      f" · {row['version'] or 'versión sin dato'}", "detail": "\n".join(detail)})
        rows.append({"label": "Cómo instalar o reparar lo que falta", "action": lambda: self.plan(group, title)})
        self.push(title, rows, "Selecciona una dependencia para ver su versión exigida y el resultado de la comprobación.")

    def plan(self, group, title):
        lines = ["Comandos para ejecutar tú en una terminal (BWMenu no instala paquetes)."]
        for key, label in (("plan", "Necesario"), ("recommendPlan", "Opcional")):
            lines.extend(["", label])
            plan = group.get(key, {})
            items = [x for field in ("commands", "manual", "notes") for x in plan.get(field, [])]
            lines.extend(items or ["Nada pendiente."])
        self.view("Reparar · " + title, "\n".join(lines))

    def skins(self):
        rows = []
        for skin in self.data["skins"]:
            active = " · activa" if skin["id"] == self.data.get("current") else ""
            state = "lista" if skin["ready"] else "faltan requisitos"
            rows.append({"label": f"{skin['name']} · {state}{active}",
                         "detail": skin["description"], "action": lambda s=skin: self.skin(s)})
        self.push("Skins instaladas", rows, self.data.get("error") or
                  "Instalada = tiene manifiesto. Lista = cumple el núcleo y sus requisitos obligatorios.")

    def skin(self, skin):
        rows = [{"label": "Ver requisitos y versiones", "action": lambda: self.group(skin, skin["name"])},
                {"label": "Cómo instalar los requisitos", "action": lambda: self.plan(skin, skin["name"])},
                {"label": "Aplicar esta skin" if skin["ready"] else "Aplicar: faltan requisitos",
                 "detail": "Orden: bwm skin " + skin["id"],
                 "action": lambda: self.apply_skin(skin["id"])}]
        theme = skin.get("defaultTheme") or {}
        intro = f"{skin['description']}\nTema por defecto: {theme.get('name', '?')}. Orden: bwm skin {skin['id']}"
        self.push(skin["name"], rows, intro)

    def apply_skin(self, sid):
        # Se comprueba de nuevo en bwm skin; el diagnóstico mostrado puede haberse quedado antiguo.
        self.execute([str(SCRIPTS / "bwm"), "skin", sid], "Aplicar skin " + sid, skin=sid)

    def execute(self, argv, title, skin=None, restart=False):
        if not self.data["hyprland"]:
            self.view(title, "No hay conexión con Hyprland. Abre una sesión gráfica para realizar esta acción.\n"
                      "Puedes consultar versiones, requisitos y ayuda desde esta consola.")
            return
        self.message = title + "… Espera a que termine."
        self.draw()
        # No se mata una transición a mitad por un timeout del visor.
        try:
            result = subprocess.run(argv, capture_output=True, text=True)
            log = (result.stdout or "") + (result.stderr or "")
            ok = result.returncode == 0
        except OSError as exc:
            log, ok = str(exc), False
        fresh = snapshot()
        if skin:
            ok = ok and fresh.get("current") == skin and not fresh["configErrors"] and bool(fresh["shellPids"])
        if restart:
            ok = ok and bool(fresh["shellPids"]) and not fresh["configErrors"]
        if argv[:2] == ["hyprctl", "reload"]:
            ok = ok and not fresh["configErrors"]
        self.data = fresh
        self.message = ""
        self.pages = self.pages[:1]
        self.view(title, ("Acción terminada y comprobada." if ok else "La acción necesita revisión.")
                  + "\n\n" + log + "\n\n" + "\n".join(diagnostic_lines(fresh)))

    def restart(self):
        sid = self.data.get("current")
        if sid not in {s["id"] for s in self.data["skins"]}:
            self.view("Recuperar", "No se pudo determinar la skin activa. Revisa el diagnóstico.")
            return
        self.execute([sys.executable, str(SCRIPTS / "bwm-theme-manager.py"), "set", sid, "--restart-shell"],
                     "Reiniciar barra y paneles", restart=True)

    def recovery(self):
        self.push("Recuperación", [
            {"label": "Reiniciar barra y paneles de la skin actual", "action": self.restart,
             "detail": "Usa el reinicio de mantenimiento de BWM (~10 s). BWMenu permanece abierto."},
            {"label": "Recargar configuración de Hyprland", "action": lambda: self.execute(["hyprctl", "reload"], "Recargar Hyprland")},
            {"label": "Errores de configuración", "action": lambda: self.view("Errores de Hyprland", self.data["configErrors"] or
                         ("Ninguno." if self.data["hyprland"] else "Sin conexión con Hyprland."))},
            {"label": "Últimas líneas del registro de Quickshell", "action": self.shell_log},
            {"label": "Elegir otra skin", "action": self.skins},
        ], "Recuperación manual; no cierra la sesión ni las aplicaciones.")

    def shell_log(self):
        self.view("Registro de Quickshell", shell_log_text())

    def help(self):
        self.view("Ayuda", "BWMenu funciona sin la barra ni Quickshell.\n"
                  "Abrir: mantén + y pulsa -, o al revés; también sirve el teclado numérico.\n"
                  "Desde una terminal: bwm menu (o bwmenu).\n"
                  "Si cae Hyprland, el atajo no puede funcionar: entra con Ctrl+Alt+F3 e inicia sesión.\n"
                  "En esa consola: bwm menu --tui\n"
                  "Si bwm no está en PATH: ~/.config/hypr/scripts/bwm menu --tui\n"
                  "Versión de BWM: bwm version\nRequisitos con versiones: bwm check --versions\n"
                  "Skins instaladas: bwm skins\nSkin activa: bwm skin\nAplicar una skin: bwm skin retro\n"
                  "Un cambio de skin comprueba sus requisitos antes de aplicarla.\n"
                  "Reiniciar barra desde la sesión gráfica:\n"
                  'python3 ~/.config/hypr/scripts/bwm-theme-manager.py set "$(bwm skin)" --restart-shell\n'
                  "Si un plugin no coincide con Hyprland, consulta sus instrucciones en Dependencias.\n"
                  "Los mínimos declarados no son una garantía de compatibilidad con cualquier versión futura.\n"
                  "Referencia de BWMenu: docs/BWMENU.md")

    def draw(self):
        from bwm_menu_appearance import appearance, stamp
        signature = stamp()
        if signature != self.appearance_stamp:
            self.appearance = appearance()
            self.appearance_stamp = signature
        width, height = shutil.get_terminal_size((100, 32))
        width = max(12, width - 2)
        lines = ["BWMenu  ·  diagnóstico y recuperación",
                 self.appearance.get("skinName", "BWM") + " · " + self.appearance.get("themeName", ""),
                 "BWM " + self.data.get("version", "…")]
        if self.pages:
            page = self.pages[-1]
            lines.extend([" / ".join(p["title"] for p in self.pages), "─" * width])
            intro = clean(page["intro"])
            lines.extend(textwrap.wrap(intro.replace("\n", " · "), width)[:2])
            lines.append("")
            rows = page["rows"]
            selected = page["selected"]
            count = max(1, height - len(lines) - 10)
            start = max(0, min(selected - count // 2, len(rows) - count))
            for i in range(start, min(len(rows), start + count)):
                label = clean(rows[i]["label"]).replace("\n", " ")
                value = (" › " if i == selected else "   ") + label
                lines.append(("\033[7m" if i == selected else "") + value[:width] + "\033[0m")
            lines.extend(["", "─" * width])
            detail = clean(rows[selected].get("detail", "Intro: abrir")) if rows else "Sin datos disponibles."
            wrapped = [part for line in detail.splitlines() for part in (textwrap.wrap(line, width) or [""])]
            lines.extend(wrapped[:5])
            lines.append(f"{selected + 1 if rows else 0}/{len(rows)}  ↑↓: elegir · Intro: abrir · Esc: volver · R: actualizar · Q: salir")
        if self.message:
            lines.append(self.message)
        def ansi(value, background=False):
            rgb = ";".join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
            return f"\033[{48 if background else 38};2;{rgb}m"
        colored = os.environ.get("TERM") not in ("linux", "dumb", None) and not os.environ.get("NO_COLOR")
        base = (ansi(self.appearance["background"], True) + ansi(self.appearance["foreground"])) if colored else ""
        body = "\n".join(lines[:max(1, height - 1)])
        if colored:
            selection = ansi(self.appearance["accent"], True) + ansi(self.appearance["onAccent"])
            body = body.replace("\033[7m", selection).replace("\033[0m", "\033[0m" + base)
        frame = "\033[H" + base + "\033[2J" + body
        if frame != self.frame:
            sys.stdout.write(frame)
            sys.stdout.flush()
            self.frame = frame

    def run(self):
        fd = sys.stdin.fileno()
        previous = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            sys.stdout.write("\033[?1049h\033[?25l")
            self.refresh()
            while self.pages:
                self.draw()
                if not select.select([fd], [], [], 0.4)[0]:
                    continue
                key = os.read(fd, 1)
                if key == b"\x1b":
                    while select.select([fd], [], [], 0.04)[0]:
                        key += os.read(fd, 1)
                page = self.pages[-1]
                total = len(page["rows"])
                if key in (b"q", b"Q"):
                    break
                if key in (b"r", b"R"):
                    self.refresh()
                elif key in (b"\x1b", b"\x7f", b"\x1b[D"):
                    self.pages.pop()
                elif total and key in (b"\x1b[A", b"k", b"\x1b[B", b"j", b"\t"):
                    step = -1 if key in (b"\x1b[A", b"k") else 1
                    page["selected"] = (page["selected"] + step) % total
                elif total and key in (b"\n", b"\r", b"\x1b[C"):
                    action = page["rows"][page["selected"]].get("action")
                    if action:
                        action()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, previous)
            sys.stdout.write("\033[0m\033[?25h\033[?1049l")
            sys.stdout.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="abre BWMenu en una terminal limpia")
    parser.add_argument("--tui", action="store_true", help="usa esta terminal (también TTY)")
    parser.add_argument("--report", action="store_true", help="diagnóstico sin interfaz")
    parser.add_argument("--json", action="store_true", help="diagnóstico JSON sin interfaz")
    parser.add_argument("--appearance", action="store_true", help="aspecto actual en JSON")
    parser.add_argument("--watch-appearance", action="store_true", help="sigue en vivo los temas originales")
    parser.add_argument("--gui", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--shell-log", action="store_true", help="últimas líneas del registro de la barra")
    args = parser.parse_args(argv)
    if args.shell_log:
        print(clean(shell_log_text()))
        return 0
    if args.appearance or args.watch_appearance:
        from bwm_menu_appearance import appearance, watch
        if args.watch_appearance:
            try:
                watch()
            except (BrokenPipeError, KeyboardInterrupt):
                pass
        else:
            print(json.dumps(appearance(), ensure_ascii=False))
        return 0
    if args.gui:
        return graphical()
    if args.report or args.json:
        data = snapshot()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else plain_report(data))
        return 0 if not data.get("error") else 1
    if args.open:
        return open_window(terminal=args.tui)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Necesita una terminal: bwm menu --open. Diagnóstico de texto: bwm menu --report", file=sys.stderr)
        return 2
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    lock_path = (runtime if runtime.is_dir() else Path.home() / ".cache") / "bwm-menu.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("BWMenu ya está abierto.")
            return 0
        try:
            Menu().run()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

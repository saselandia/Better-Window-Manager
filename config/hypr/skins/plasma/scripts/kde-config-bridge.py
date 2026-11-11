#!/usr/bin/env python3
"""Puente de configuración de Breeze: enter/export/import/watch/leave/guards.

KDE manda en aspecto y ventanas; BWM, en ajustes compartidos. Sólo se escribe una lista
explícita de claves. Las opciones del usuario se leen, nunca se modifican. Ver BREEZE_ARCH §9.
Linux inotify se usa a través de libc (sin dependencia Python adicional).
"""
import argparse
import contextlib
import errno
import ctypes
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import tempfile
import time
import types
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kwin_rules
import kwin_tiles

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "bwm/plasma"
DATA = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))
OPTIONS = CONFIG / "illogical-impulse/config.json"
META = STATE / "bridge-state.json"
KWIN_STATE = STATE / "kwin.lua"
DISABLED_KDED = (
    "statusnotifierwatcher", "networkmanagement", "bluedevil", "kscreen",
    "audioshortcutsservice", "mprisservice", "appmenu", "lookandfeelautoswitcher",
    "plasma_accentcolor_service", "plasma_session_shortcuts", "donationmessage",
    "devicenotifications", "freespacenotifier", "oom_notifier", "remotenotifier", "wpad-detector",
)


class Conflict(RuntimeError):
    """El archivo cambió mientras se preparaba una escritura: reintentar, nunca pisarlo."""


def run(argv):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return subprocess.CompletedProcess(argv, 1, "", "")


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def atomic(path, content, expected=None):
    # Conserva los enlaces al repo; no escribe a través de un enlace a configuración del usuario.
    path = path.resolve()
    protected = (CONFIG / "bwm/user").resolve()
    if path == protected or protected in path.parents:
        raise ValueError("El puente no puede escribir la configuración en texto del usuario")
    old = read(path)
    if expected is not None and old != expected:
        raise Conflict(str(path))
    if old == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".bwm-kde-", delete=False) as f:
        tmp = Path(f.name)
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    try:
        tmp.chmod(mode)
        if read(path) != old:
            raise Conflict(str(path))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def load_json(path, default=None):
    text = read(path)
    return json.loads(text) if text.strip() else ({} if default is None else default)


def save_json(path, data, expected=None):
    return atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", expected)


def ini(text):
    result, group = {}, ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            group = stripped[1:-1]
        elif "=" in line and not stripped.startswith(("#", ";")):
            key, value = line.split("=", 1)
            result.setdefault(group, {})[key.strip()] = value.strip()
    return result


def patch_ini(text, changes):
    """Conserva comentarios, grupos anidados, claves localizadas y desconocidas byte a byte.

    changes: {(grupo, clave): valor o None para quitar sólo esa clave}.
    """
    remaining = dict(changes)
    lines, group = [], ""
    def flush():
        for (g, key), value in list(remaining.items()):
            if g == group:
                if value is not None:
                    if lines and not lines[-1].endswith("\n"):
                        lines[-1] += "\n"
                    lines.append(f"{key}={value}\n")
                del remaining[g, key]
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            flush()
            group = stripped[1:-1]
        elif "=" in line and not stripped.startswith(("#", ";")):
            key = line.split("=", 1)[0].strip()
            if (group, key) in changes:
                value = remaining.pop((group, key), None)
                if value is not None:
                    lines.append(f"{key}={value}\n")
                continue
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(line)
    flush()
    for g in dict.fromkeys(g for g, _ in remaining):
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(f"\n[{g}]\n")
        for (gg, key), value in remaining.items():
            if gg == g and value is not None:
                lines.append(f"{key}={value}\n")
    return "".join(lines)


def merged(file):
    result = {}
    bases = [Path(p) for p in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":") if p]
    for base in reversed([CONFIG, CONFIG / "kdedefaults", *bases]):
        for group, values in ini(read(base / file)).items():
            result.setdefault(group, {}).update(values)
    return result


def notify(file, changes):
    # Formato de KConfig 6.29: /<archivo>, ConfigChanged(a{saay}). Sin reescribir tras el rename.
    groups = {}
    for group, key in changes:
        groups.setdefault(group.replace("][", "\x1d"), []).append(key)
    payload = "{" + ", ".join(repr(g) + ": [" + ", ".join(
        "[" + ", ".join(f"byte {b}" for b in key.encode()) + "]" for key in keys) + "]"
        for g, keys in groups.items()) + "}"
    run(["gdbus", "emit", "--session", "--object-path", "/" + file,
         "--signal", "org.kde.kconfig.notify.ConfigChanged", payload])
    if file == "kdeglobals" and any(key in ("font", "fixed", "menuFont", "activeFont") for _, key in changes):
        # La misma señal que KFonts::save() de Plasma 6.7.5 para apps con plasma-integration.
        run(["gdbus", "emit", "--session", "--object-path", "/KDEPlatformTheme",
             "--signal", "org.kde.KDEPlatformTheme.refreshFonts"])


def active():
    return load_json(OPTIONS).get("appearance", {}).get("bwmTheme") == "plasma"


def effective_options():
    options = load_json(OPTIONS)
    loader = importlib.machinery.SourceFileLoader("bwm_bridge_user", str(SCRIPTS / "bwm-user-config"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.apply_shell(options, "plasma")
    return options


def option(name, fallback):
    result = run(["hyprctl", "getoption", name, "-j"])
    try:
        data = json.loads(result.stdout)
        return next(data[k] for k in ("str", "int", "float") if k in data)
    except (ValueError, StopIteration, TypeError):
        return fallback


def cursor():
    # La fuente común es el gestor de BWM; gsettings refleja su aplicación en vivo.
    text = read(CONFIG / "hypr/modules/cursor.lua")
    theme = re.findall(r'hl\.env\("(?:HYPRCURSOR|XCURSOR)_THEME",\s*"([^"]*)"\)', text)
    size = re.findall(r'hl\.env\("(?:HYPRCURSOR|XCURSOR)_SIZE",\s*"(\d+)"\)', text)
    return (theme[-1] if theme else "default", size[-1] if size else "24")


def shared_values():
    options = effective_options()
    theme, size = cursor()
    night = load_json(STATE.parent / "nightlight.json", {"enabled": False, "temperature": 4000})
    temperature = options.get("light", {}).get("night", {}).get("colorTemperature", night.get("temperature", 4000))
    count = max(1, min(100, int(options.get("bar", {}).get("workspaces", {}).get("shown", 10))))
    values = {
        "kcminputrc": {("Mouse", "cursorTheme"): theme, ("Mouse", "cursorSize"): size,
            ("Keyboard", "RepeatDelay"): str(option("input:repeat_delay", 250)),
            ("Keyboard", "RepeatRate"): str(option("input:repeat_rate", 40)),
            ("Keyboard", "KeyRepeat"): "repeat" if option("input:repeat_rate", 40) else "none",
            ("Keyboard", "NumLock"): "0" if option("input:numlock_by_default", 1) else "1"},
        "kxkbrc": {("Layout", "Use"): "true", ("Layout", "LayoutList"): str(option("input:kb_layout", "us")),
            ("Layout", "VariantList"): str(option("input:kb_variant", "")),
            ("Layout", "Model"): str(option("input:kb_model", "")),
            ("Layout", "Options"): str(option("input:kb_options", "")), ("Layout", "SwitchMode"): "Global"},
        "kwinrc": {("NightColor", "Active"): str(bool(night.get("enabled"))).lower(),
            ("NightColor", "Mode"): "0", ("NightColor", "NightTemperature"): str(temperature),
            ("NightColor", "DayTemperature"): "6500", ("Desktops", "Number"): str(count),
            ("Desktops", "Rows"): "1"},
    }
    # mimeapps.list ya es la fuente XDG común: no duplicarla ni pasar por xdg-settings en import.
    apps = options.get("apps", {})
    terminal = apps.get("terminal", "kitty -1")
    values["kdeglobals"] = {("General", "TerminalApplication"): terminal,
                            ("General", "TerminalService"): "org.kde.konsole.desktop" if terminal == "konsole" else ""}
    locale = options.get("language", {}).get("ui", "auto")
    if locale != "auto":
        values["plasma-localerc"] = {("Translations", "LANGUAGE"): str(locale).replace("-", "_")}
    else:
        values["plasma-localerc"] = {("Translations", "LANGUAGE"): None}
    return values


@contextlib.contextmanager
def lock():
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "bridge.lock", "a") as fd:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield


def export_shared(meta):
    changed = []
    for file, updates in shared_values().items():
        path = CONFIG / file
        text = read(path)
        original = ini(text)
        entries = meta.setdefault("exports", {}).setdefault(file, {})
        for (group, key), value in updates.items():
            ident = group + "\x1f" + key
            entry = entries.setdefault(ident, {"before": original.get(group, {}).get(key)})
            entry["written"] = value
        # Guardar propiedad antes de escribir, para recuperarse de un cierre interrumpido.
        save_json(META, meta)
        actual = {k: v for k, v in updates.items() if original.get(k[0], {}).get(k[1]) != v}
        if actual and atomic(path, patch_ini(text, actual), text):
            notify(file, actual)
            changed.append(file)
    return changed


def guards():
    """Protecciones de sesión: también fuera de Breeze si plasma-workspace está instalado."""
    if not Path("/usr/bin/plasma_waitforname").exists():
        return
    updates = {("Module-" + mod, "autoload"): "false" for mod in DISABLED_KDED}
    path = CONFIG / "kded5rc"
    text = read(path)
    atomic(path, patch_ini(text, updates), text)
    service = DATA / "dbus-1/services/org.freedesktop.Notifications.service"
    text = read(service)
    # Un servicio propio del usuario tiene prioridad. Sólo mantener el que BWM creó en F0/F2.
    if not text or "plasma_waitforname" in text:
        atomic(service, "# Generado por BWM: esperar al dueño de avisos de la skin activa.\n"
               "[D-BUS Service]\nName=org.freedesktop.Notifications\n"
               "Exec=/usr/bin/plasma_waitforname --timeout 25 org.freedesktop.Notifications\n", text)


def kwin_settings():
    w, k = merged("kwinrc"), merged("kdeglobals")
    win = w.get("Windows", {})
    decor = w.get("org.kde.kdecoration2", {})
    kde = k.get("KDE", {})
    def number(value, default, lower, upper):
        try:
            return max(lower, min(upper, float(value)))
        except (TypeError, ValueError):
            return default
    return {
        "focus": win.get("FocusPolicy", "ClickToFocus"),
        "placement": win.get("Placement", "Smart"),
        "doubleClick": win.get("TitlebarDoubleClickCommand", "Maximize"),
        "wheel": w.get("MouseBindings", {}).get("CommandTitlebarWheel", "Nothing"),
        "borderSnap": int(number(win.get("BorderSnapZone"), 10, 0, 1000)),
        "windowSnap": int(number(win.get("WindowSnapZone"), 10, 0, 1000)),
        "centerSnap": int(number(win.get("CenterSnapZone"), 0, 0, 1000)),
        "snapOnlyOverlapping": win.get("SnapOnlyWhenOverlapping", "false").lower() == "true",
        "quickTile": win.get("ElectricBorderTiling", "true").lower() == "true",
        "edgeMaximize": win.get("ElectricBorderMaximize", "true").lower() == "true",
        "cornerRatio": number(win.get("ElectricBorderCornerRatio"), 0.25, 0, 0.5),
        "buttonsLeft": decor.get("ButtonsOnLeft", "M"),
        "buttonsRight": decor.get("ButtonsOnRight", "IAX"),
        "animationFactor": number(kde.get("AnimationDurationFactor"), 1, 0, 20),
        "singleClick": kde.get("SingleClick", "false").lower() == "true",
    }


def lua(value):
    # Escapes explícitos: no usar JSON \uXXXX como escape Lua ni interpolar código de KDE.
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


def generate_kwin():
    settings = kwin_settings()
    changed = atomic(KWIN_STATE, "-- Generado por kde-config-bridge.py; KDE es la fuente.\nreturn {\n" +
                  "".join(f"    {key} = {lua(value)},\n" for key, value in settings.items()) + "}\n")
    # Both files share the bridge debounce and at most one compositor reload.
    bridge = types.SimpleNamespace(**globals())
    changed_rules = kwin_rules.generate(bridge)
    changed_tiles = kwin_tiles.generate(bridge)
    return changed or changed_rules or changed_tiles


def import_breeze(meta):
    """Importa sólo fuentes a appearance; iconos/colores/ventanas se leen de KDE directamente."""
    text = read(OPTIONS)
    options = json.loads(text)
    old_options = json.loads(text)
    kde = merged("kdeglobals")
    fonts = options.setdefault("appearance", {}).setdefault("fonts", {})
    pairs = (("General", "font", "main"), ("General", "fixed", "monospace"),
             ("General", "menuFont", "reading"), ("WM", "activeFont", "title"))
    previous = meta.setdefault("fonts", {})
    updates = {}
    for group, key, bwm in pairs:
        kde_value = kde.get(group, {}).get(key, "")
        kde_family = kde_value.split(",", 1)[0]
        prior = previous.get(bwm, {})
        # BWM → KDE si sólo cambió BWM. En una edición simultánea, KDE gana en aspecto;
        # shell.jsonc del usuario se aplica después y siempre tiene prioridad.
        bwm_changed = prior and fonts.get(bwm) != prior.get("bwm")
        kde_changed = prior and kde_value != prior.get("kde")
        if kde_family and not (bwm_changed and not kde_changed):
            fonts[bwm] = kde_family
    loader = importlib.machinery.SourceFileLoader("bwm_bridge_user", str(SCRIPTS / "bwm-user-config"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.apply_shell(options, "plasma")
    fonts = options.get("appearance", {}).get("fonts", {})
    if options != old_options:
        save_json(OPTIONS, options, text)
    for group, key, bwm in pairs:
        kde_value = kde.get(group, {}).get(key, "")
        family = fonts.get(bwm)
        if family and kde_value.split(",", 1)[0] != family:
            suffix = kde_value.partition(",")[2] or "10,-1,5,50,0,0,0,0,0"
            kde_value = family + "," + suffix
            updates[group, key] = kde_value
        previous[bwm] = {"kde": kde_value, "bwm": family}
    if updates:
        path = CONFIG / "kdeglobals"
        text = read(path)
        if atomic(path, patch_ini(text, updates), text):
            notify("kdeglobals", updates)
    return generate_kwin()


def new_session():
    return {"session": True, "exports": {}, "palette": palette_signature(),
            "legacy": {name: read(CONFIG / name) for name in ("gtkrc", "gtkrc-2.0", "Trolltech.conf")}}


def repair_legacy(meta):
    """krdb de Plasma escribe GTK1/2 y Qt4. Conservar los ajustes previos de BWM y lo ajeno."""
    baseline = meta.get("legacy", {})
    for name in ("gtkrc", "gtkrc-2.0"):
        if name not in baseline:
            continue
        path = CONFIG / name
        text = read(path)
        if text == baseline[name] or "KDE Plasma" not in text:
            continue
        # Sólo retirar el bloque generado por krdb; conservar líneas que no son de ese bloque.
        extras = []
        for line in text.splitlines(keepends=True):
            item = line.strip()
            generated = (not item or item == "#" or (item.startswith("#") and "KDE Plasma" in item)
                         or item.startswith(("gtk-alternative-button-order", "gtk-theme-name", "include ")))
            if not generated and line not in baseline[name].splitlines(keepends=True):
                extras.append(line)
        content = baseline[name]
        if extras and content and not content.endswith("\n"):
            content += "\n"
        atomic(path, content + "".join(extras), text)
    if "Trolltech.conf" in baseline:
        path = CONFIG / "Trolltech.conf"
        text = read(path)
        current, before = ini(text).get("qt", {}), ini(baseline["Trolltech.conf"]).get("qt", {})
        keys = {"font", "GUIEffects", r"KDE\contrast"}
        keys.update(k for k in current if k.startswith(("Palette\\", "KWinPalette\\")))
        updates = {("qt", k): before.get(k) for k in keys if current.get(k) != before.get(k)}
        if updates:
            atomic(path, patch_ini(text, updates), text)


def palette_signature():
    # Sólo colores/iconos/estilo: cambiar cursor o terminal no vuelve a generar todas las apps.
    groups = merged("kdeglobals")
    own = {g: v for g, v in groups.items() if g.startswith(("Colors:", "ColorEffects:", "WM"))}
    for g, keys in (("Icons", ("Theme",)), ("General", ("ColorScheme", "AccentColor")),
                    ("KDE", ("widgetStyle", "LookAndFeelPackage"))):
        own[g] = {key: groups.get(g, {}).get(key) for key in keys}
    return hashlib.sha256(json.dumps(own, sort_keys=True).encode()).hexdigest()


def reconcile(do_import=True, reload=True):
    if not active():
        return False
    with lock():
        if not active():
            return False
        meta = load_json(META)
        if not meta.get("session"):
            meta = new_session()
        # Import antes de export: sólo importa la lista explícita de opciones propias.
        changed_kwin = import_breeze(meta) if do_import else False
        export_shared(meta)
        repair_legacy(meta)
        guards()
        sig = palette_signature()
        if do_import and sig != meta.get("palette"):
            # subprocess no hereda la excepción de una transición: no cerrar/reiniciar apps.
            env_prev = os.environ.get("BWM_SKIN_SWITCH")
            os.environ["BWM_SKIN_SWITCH"] = "1"
            try:
                run([sys.executable, str(Path(__file__).with_name("plasma-theme.py")), "sync"])
                run([sys.executable, str(SCRIPTS / "bwm_icons.py"), "apply", "plasma"])
            finally:
                if env_prev is None:
                    os.environ.pop("BWM_SKIN_SWITCH", None)
                else:
                    os.environ["BWM_SKIN_SWITCH"] = env_prev
        meta["palette"] = sig
        save_json(META, meta)
        if changed_kwin and reload and os.environ.get("BWM_SKIN_SWITCH") != "1":
            run(["hyprctl", "reload"])
        return True


def enter():
    if not active():
        return
    with lock():
        meta = load_json(META)
        # Enter es idempotente: un reinicio no pierde los valores previos a la skin.
        if not meta.get("session"):
            save_json(META, new_session())
    reconcile(reload=False)


def leave():
    stop()
    with lock():
        meta = load_json(META)
        repair_legacy(meta)
        for file, entries in meta.get("exports", {}).items():
            path = CONFIG / file
            text = read(path)
            current = ini(text)
            updates = {}
            for ident, entry in entries.items():
                group, key = ident.split("\x1f", 1)
                # No deshacer una edición ajena posterior a nuestra última escritura.
                if current.get(group, {}).get(key) == entry["written"]:
                    updates[group, key] = entry["before"]
            if updates and atomic(path, patch_ini(text, updates), text):
                notify(file, updates)
        save_json(META, {})


def start():
    if not active():
        return
    import bwm_session
    bwm_session.spawn([sys.executable, str(Path(__file__).resolve()), "watch"],
                      str(STATE / "bridge.log"))


def stop():
    try:
        fd = os.open(STATE / "watch.lock", os.O_RDWR)
    except FileNotFoundError:
        return
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pid = int(os.read(fd, 32))
            # Verificar el ejecutable y argv antes de señalar un PID que pudiera reutilizarse.
            args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            if str(Path(__file__).resolve()).encode() in args and b"watch" in args:
                os.kill(pid, signal.SIGTERM)
                for _ in range(200):
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        time.sleep(0.05)
                else:
                    raise RuntimeError("El vigilante sigue escribiendo; no se cambia de skin")
    except (OSError, ValueError):
        pass
    finally:
        os.close(fd)


def watched_files():
    return [OPTIONS, CONFIG / "hypr/modules/cursor.lua", CONFIG / "hypr/modules/binds.lua",
            CONFIG / "hypr/modules/monitors.lua", CONFIG / "hypr/monitors_layout.json",
            CONFIG / "bwm/user/shell.jsonc", CONFIG / "bwm/user/hyprland.lua",
            CONFIG / "bwm/default-apps.json", CONFIG / "mimeapps.list",
            STATE.parent / "nightlight.json", STATE / "tiling-outputs.json", *[CONFIG / f for f in
                ("kdeglobals", "kcminputrc", "kxkbrc", "kwinrc", "kwinrulesrc", "plasmarc", "breezerc", "plasma-localerc",
                 "gtkrc", "gtkrc-2.0", "Trolltech.conf")],
            *[CONFIG / "kdedefaults" / f for f in ("kdeglobals", "kcminputrc", "kwinrc", "plasmarc")]]


def signatures():
    return {str(p): hashlib.sha256(read(p).encode()).hexdigest() for p in watched_files()}


class Inotify:
    def __init__(self):
        self.lib = ctypes.CDLL(None, use_errno=True)
        self.fd = self.lib.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0 and ctypes.get_errno() not in (errno.EMFILE, errno.ENOSPC):
            raise OSError(ctypes.get_errno(), "inotify_init1")
        # A busy session can exhaust the user's inotify quota. Keep the bridge alive by polling.
        self.previous = signatures()
        self.dirs = set()
        self.refresh()

    def refresh(self):
        # Vigilar directorios reales, también padres de los que aún no existen. Así los rename
        # atómicos de Qt/KCM y las carpetas creadas después no nos dejan vigilando un inodo viejo.
        for path in watched_files():
            folder = path.parent.resolve()
            while not folder.exists():
                folder = folder.parent
            if folder not in self.dirs:
                if self.fd < 0:
                    self.dirs.add(folder)
                    continue
                wd = self.lib.inotify_add_watch(self.fd, os.fsencode(folder), 0xFCe)  # write/move/create/delete
                if wd < 0:
                    raise OSError(ctypes.get_errno(), str(folder))
                self.dirs.add(folder)

    def wait(self, timeout):
        if self.fd < 0:
            time.sleep(timeout)
            current = signatures()
            events = current != self.previous
            self.previous = current
            self.refresh()
            return events
        events = bool(select.select([self.fd], [], [], timeout)[0])
        if events:
            while True:
                try:
                    os.read(self.fd, 65536)
                except BlockingIOError:
                    break
            self.refresh()
        return events

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)


def watch():
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "watch.lock", "a+") as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        guard.seek(0)
        guard.truncate()
        guard.write(str(os.getpid()))
        guard.flush()
        stopping = False
        def shutdown(signum, frame):
            nonlocal stopping
            stopping = True
        signal.signal(signal.SIGTERM, shutdown)
        watcher = Inotify()
        previous, deadline = signatures(), None
        rules = kwin_rules.Runtime(types.SimpleNamespace(**globals()))
        try:
            while not stopping:
                try:
                    if not active():
                        break
                except ValueError:
                    # Un editor puede dejar config.json incompleto durante su escritura.
                    watcher.wait(0.25)
                    continue
                if watcher.wait(0.25):
                    if signatures() != previous:
                        deadline = time.monotonic() + 0.3
                if deadline is not None and time.monotonic() >= deadline:
                    try:
                        reconcile()
                        previous, deadline = signatures(), None
                    except (Conflict, ValueError, OSError) as exc:
                        print(f"kde-config-bridge: reintentar: {exc}", file=sys.stderr, flush=True)
                        deadline = time.monotonic() + 1
                if deadline is None:
                    try:
                        rules.tick()
                    except (Conflict, ValueError, OSError) as exc:
                        print(f"kde-config-bridge: reglas: {exc}", file=sys.stderr, flush=True)
        finally:
            try:
                rules.close()
            finally:
                watcher.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("enter", "export", "import", "watch", "start", "stop", "leave", "guards"))
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args()
    try:
        if args.action in ("export", "import"):
            reconcile(do_import=args.action == "import", reload=not args.no_reload)
        else:
            globals()[args.action]()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"kde-config-bridge: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

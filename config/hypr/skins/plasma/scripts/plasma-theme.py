#!/usr/bin/env python3
"""Temas de Plasma para la skin Breeze, con los formatos y herramientas del original.

  plasma-theme.py list [colors|desktoptheme|icons|lookandfeel|aurorae]
  plasma-theme.py current                    lo activo, en JSON
  plasma-theme.py colors <esquema|archivo.colors>
  plasma-theme.py desktoptheme <tema>        estilo de Plasma (plasmarc [Theme] name)
  plasma-theme.py icons <tema>
  plasma-theme.py lookandfeel <id>           tema global: aplica sus partes como lookandfeeltool
  plasma-theme.py cursor <tema>              no: el cursor es común a todas las skins (regla 14)
  plasma-theme.py save | restore             guarda/devuelve el kdeglobals de Breeze al salir/entrar
  plasma-theme.py sync                       regenera la paleta de las apps desde el esquema activo
  plasma-theme.py translations               compila los catálogos de lo portado (Kickoff…) en locale/

Escribe los mismos archivos que Plasma (kdeglobals, plasmarc, kwinrc, ksplashrc) con notificación
de KConfig, así el shell (libplasma, Kirigami) y las apps KDE cambian en vivo. Usa plasma-apply-*
si están instalados (plasma-workspace) y, si no, hace lo mismo por su cuenta. Nunca cambia el
cursor (lo manda BWM) ni la disposición del escritorio ni el fondo de un tema global.
"""
from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plasma_palette  # noqa: E402

HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
DATA = Path(os.environ.get("XDG_DATA_HOME") or HOME / ".local/share")
STATE = Path(os.environ.get("XDG_STATE_HOME") or HOME / ".local/state") / "bwm" / "plasma"
DATA_DIRS = [DATA] + [Path(p) for p in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if p]
KDEGLOBALS = CONFIG / "kdeglobals"
SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"  # config/hypr/scripts
COLOR_GROUPS = ("Colors:", "ColorEffects:", "WM")
DEFAULT_LOOKANDFEEL = "org.kde.breezedark.desktop"
# Partes de un tema global que BWM no aplica: el cursor es común (regla 14); el fondo y la
# disposición del escritorio son de BWM; la pantalla de carga (splash) no existe en BWM.
SKIPPED_DEFAULTS = {("kcminputrc", "Mouse"), ("Wallpaper",), ("plasmashellrc",)}


# ───────────────────────────────────────────────────────────── utilidades
def _ini() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    parser.optionxform = str
    return parser


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def kwrite(file: str, groups: list[str], key: str, value: str):
    """Como kwriteconfig6 --notify (que se usa si está): las apps KDE lo ven en vivo."""
    if _which("kwriteconfig6"):
        cmd = ["kwriteconfig6", "--file", str(CONFIG / file)]
        for g in groups:
            cmd += ["--group", g]
        subprocess.run(cmd + ["--key", key, "--notify", value], check=False)
        return
    path = CONFIG / file
    parser = _ini()
    parser.read(path, encoding="utf-8")
    section = "][".join(groups)
    if not parser.has_section(section):
        parser.add_section(section)
    parser[section][key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        parser.write(f, space_around_delimiters=False)


def kread(file: str, group: str, key: str, default: str = "") -> str:
    parser = _ini()
    parser.read(CONFIG / file, encoding="utf-8")
    return parser.get(group, key, fallback=default)


def notify_palette():
    """KGlobalSettings.notifyChange(PaletteChanged): repintan las apps con el plugin de KDE."""
    subprocess.run(["dbus-send", "--session", "--type=signal", "/KGlobalSettings", "org.kde.KGlobalSettings.notifyChange",
                    "int32:0", "int32:0"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def active_skin() -> str:
    try:
        data = json.loads((CONFIG / "illogical-impulse" / "config.json").read_text(encoding="utf-8"))
        return data.get("appearance", {}).get("bwmTheme", "default")
    except Exception:
        return "default"


def _metadata_name(folder: Path) -> str:
    meta = folder / "metadata.json"
    if meta.is_file():
        try:
            return json.loads(meta.read_text(encoding="utf-8")).get("KPlugin", {}).get("Name") or folder.name
        except Exception:
            pass
    desktop = folder / "metadata.desktop"
    if desktop.is_file():
        for line in desktop.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Name="):
                return line.split("=", 1)[1]
    return folder.name


# ───────────────────────────────────────────────────────────── catálogos
def list_colors() -> list[dict]:
    seen, out = set(), []
    for base in DATA_DIRS:
        for f in sorted((base / "color-schemes").glob("*.colors")):
            if f.stem in seen:
                continue
            seen.add(f.stem)
            name = _ini()
            name.read(f, encoding="utf-8")
            out.append({"id": f.stem, "name": name.get("General", "Name", fallback=f.stem), "path": str(f)})
    return out


def _list_packages(sub: str, marker: tuple[str, ...]) -> list[dict]:
    seen, out = set(), []
    for base in DATA_DIRS:
        root = base / sub
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if d.name in seen or not d.is_dir() or not any((d / m).exists() for m in marker):
                continue
            seen.add(d.name)
            out.append({"id": d.name, "name": _metadata_name(d), "path": str(d)})
    return out


def list_desktopthemes():
    return _list_packages("plasma/desktoptheme", ("metadata.json", "metadata.desktop"))


def list_lookandfeel():
    return _list_packages("plasma/look-and-feel", ("contents/defaults",))


def list_aurorae():
    return _list_packages("aurorae/themes", ("metadata.desktop", "metadata.json", "decoration.svg", "decoration.svgz"))


def list_icons() -> list[dict]:
    out = []
    for item in _list_packages("icons", ("index.theme",)):
        index = _ini()
        index.read(Path(item["path"]) / "index.theme", encoding="utf-8")
        if index.get("Icon Theme", "Directories", fallback=""):  # no los temas que sólo son cursores
            item["name"] = index.get("Icon Theme", "Name", fallback=item["name"])
            out.append(item)
    return out


def _find(items: list[dict], wanted: str) -> dict | None:
    for item in items:
        if wanted in (item["id"], item["name"]):
            return item
    return None


# ───────────────────────────────────────────────────────────── aplicar
def apply_colors(arg: str, sync_after: bool = True) -> int:
    path = Path(arg).expanduser()
    if not (path.suffix == ".colors" and path.is_file()):
        item = _find(list_colors(), arg)
        if not item:
            print(f"No existe el esquema de color «{arg}»", file=sys.stderr)
            return 1
        path = Path(item["path"])
    tool = _which("plasma-apply-colorscheme") or str(Path(__file__).resolve().parents[2] / "default/scripts/kde-shims/plasma-apply-colorscheme")
    # El de Plasma se niega si ya es el actual: así se repite también tras editar el archivo
    result = subprocess.run([tool, str(path)], capture_output=True, text=True)
    if result.returncode != 0 or "already set" in result.stdout:
        _merge_colors(path)
        notify_palette()
    if sync_after:
        sync()
    return 0


def _merge_colors(scheme_path: Path):
    """Lo mismo que plasma-apply-colorscheme: los grupos de color del esquema sustituyen a los de
    kdeglobals y [General] ColorScheme lo nombra; el resto de kdeglobals se conserva."""
    scheme, globals_ = _ini(), _ini()
    scheme.read(scheme_path, encoding="utf-8")
    globals_.read(KDEGLOBALS, encoding="utf-8")
    for section in list(globals_.sections()):
        if section.startswith(COLOR_GROUPS):
            globals_.remove_section(section)
    for section in scheme.sections():
        if section.startswith(COLOR_GROUPS):
            globals_[section] = dict(scheme[section])
    if not globals_.has_section("General"):
        globals_.add_section("General")
    globals_["General"]["ColorScheme"] = scheme.get("General", "ColorScheme", fallback=scheme_path.stem) or scheme_path.stem
    KDEGLOBALS.parent.mkdir(parents=True, exist_ok=True)
    tmp = KDEGLOBALS.with_suffix(".bwm-tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        globals_.write(f, space_around_delimiters=False)
    os.replace(tmp, KDEGLOBALS)


def apply_desktoptheme(name: str) -> int:
    item = _find(list_desktopthemes(), name)
    if not item:
        print(f"No existe el estilo de Plasma «{name}»", file=sys.stderr)
        return 1
    if _which("plasma-apply-desktoptheme"):
        subprocess.run(["plasma-apply-desktoptheme", item["id"]], check=False, stdout=subprocess.DEVNULL)
    else:
        kwrite("plasmarc", ["Theme"], "name", item["id"])
    return 0


def apply_icons(name: str, sync_after: bool = True) -> int:
    item = _find(list_icons(), name)
    if not item:
        print(f"No existe el tema de iconos «{name}»", file=sys.stderr)
        return 1
    kwrite("kdeglobals", ["Icons"], "Theme", item["id"])
    subprocess.run(["dbus-send", "--session", "--type=signal", "/KIconLoader", "org.kde.KIconLoader.iconChanged", "int32:0"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if sync_after:
        sync()
    return 0


def apply_lookandfeel(pkg_id: str, sync_after: bool = True) -> int:
    """Como lookandfeeltool -a, sin la disposición del escritorio, el fondo ni el cursor, y sin
    escribir gtkrc/Trolltech.conf (GTK lo lleva BWM)."""
    item = _find(list_lookandfeel(), pkg_id)
    if not item:
        print(f"No existe el tema global «{pkg_id}»", file=sys.stderr)
        return 1
    defaults = _ini()
    defaults.read(Path(item["path"]) / "contents" / "defaults", encoding="utf-8")
    colors = None
    for section in defaults.sections():
        parts = section.split("][")
        if tuple(parts[:2]) in SKIPPED_DEFAULTS or (parts[0],) in SKIPPED_DEFAULTS or len(parts) < 2:
            continue
        file, groups = parts[0], parts[1:]
        for key, value in defaults[section].items():
            if (file, groups, key) == ("kdeglobals", ["General"], "ColorScheme"):
                colors = value
                continue
            kwrite(file, groups, key, value)
    kwrite("kdeglobals", ["KDE"], "LookAndFeelPackage", item["id"])
    if colors:
        apply_colors(colors, sync_after=False)
    if sync_after:
        sync()
    return 0


def current() -> dict:
    scheme = plasma_palette.load(KDEGLOBALS)
    return {
        "colorScheme": scheme.name,
        "dark": scheme.dark,
        "desktopTheme": kread("plasmarc", "Theme", "name", "default"),
        "icons": kread("kdeglobals", "Icons", "Theme", "breeze"),
        "lookAndFeel": kread("kdeglobals", "KDE", "LookAndFeelPackage", ""),
        "widgetStyle": kread("kdeglobals", "KDE", "widgetStyle", "Breeze"),
        "decoration": {"library": kread("kwinrc", "org.kde.kdecoration2", "library", "org.kde.breeze"),
                       "theme": kread("kwinrc", "org.kde.kdecoration2", "theme", "Breeze")},
    }


# ───────────────────────────────────────────────────────────── traducciones de lo portado
# Catálogos originales de plasma-desktop 6.7.5 incluidos con el QML portado (plasma-desktop no se
# instala: sólo sus .po). KLocalizedString los busca en <datos>/locale/<idioma>/LC_MESSAGES.
PORTED_CATALOGS = {
    "plasma_applet_org.kde.plasma.kickoff": Path(__file__).resolve().parents[4] / "quickshell/ii/modules/plasma/kickoff/po",
    # F9: menús de ventana, tareas, escritorio y panel (cadenas de kwin, plasma-desktop, plasma-workspace
    # y libplasma en un catálogo propio, modules/plasma/menus/po/extract.py)
    "bwm_plasma_menus": Path(__file__).resolve().parents[4] / "quickshell/ii/modules/plasma/menus/po",
}


def install_translations() -> int:
    if not _which("msgfmt"):
        return 0
    for domain, po_dir in PORTED_CATALOGS.items():
        for po in sorted(po_dir.glob("*.po")):
            target = DATA / "locale" / po.stem / "LC_MESSAGES" / f"{domain}.mo"
            if target.is_file() and target.stat().st_mtime >= po.stat().st_mtime:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".tmp")
            if subprocess.run(["msgfmt", "-o", str(tmp), str(po)], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                os.replace(tmp, target)
            else:
                tmp.unlink(missing_ok=True)
    return 0


# ───────────────────────────────────────────────────────────── kdeglobals de Breeze
def _is_bwm_kdeglobals() -> bool:
    try:
        return "[BWM]" in KDEGLOBALS.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def save() -> int:
    """Al salir de Breeze: las otras skins reescriben kdeglobals con su paleta (bwm_icons)."""
    if KDEGLOBALS.is_file() and not _is_bwm_kdeglobals():
        STATE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(KDEGLOBALS, STATE / "kdeglobals")
    return 0


def restore() -> int:
    """Al entrar en Breeze: el kdeglobals que tenía, o el tema global Breeze Oscuro la primera vez."""
    install_translations()
    saved = STATE / "kdeglobals"
    if saved.is_file():
        tmp = KDEGLOBALS.with_suffix(".bwm-tmp")
        shutil.copy2(saved, tmp)
        os.replace(tmp, KDEGLOBALS)
        notify_palette()
        write_palette_state(plasma_palette.load(KDEGLOBALS))
        return 0
    if _is_bwm_kdeglobals():
        # Conserva fuentes y demás claves que no son de BWM; quita la marca y la paleta de BWM
        parser = _ini()
        parser.read(KDEGLOBALS, encoding="utf-8")
        for section in list(parser.sections()):
            if section == "BWM" or section.startswith(COLOR_GROUPS):
                parser.remove_section(section)
        if parser.has_section("KDE"):
            parser.remove_option("KDE", "widgetStyle")
        with open(KDEGLOBALS, "w", encoding="utf-8") as f:
            parser.write(f, space_around_delimiters=False)
    if _find(list_lookandfeel(), DEFAULT_LOOKANDFEEL):
        apply_lookandfeel(DEFAULT_LOOKANDFEEL, sync_after=False)
    else:
        apply_colors("BreezeDark", sync_after=False)
    write_palette_state(plasma_palette.load(KDEGLOBALS))
    return 0


# ───────────────────────────────────────────────────────────── paleta del resto del escritorio
def write_palette_state(scheme) -> Path:
    STATE.mkdir(parents=True, exist_ok=True)
    data = plasma_palette.m3(scheme)
    data["darkmode"] = scheme.dark
    data["scheme"] = scheme.name
    out = STATE / "colors.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, out)
    return out


def sync() -> int:
    """Paleta de las apps desde el esquema activo. Fuera de Breeze sólo guarda el estado."""
    in_breeze = active_skin() == "plasma"
    source = KDEGLOBALS if in_breeze else STATE / "kdeglobals"
    if not source.is_file():
        return 0
    write_palette_state(plasma_palette.load(source))
    if in_breeze:
        subprocess.run([sys.executable, str(SCRIPTS / "bwm-theme-manager.py"), "apply-plasma-colors"], check=False)
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, args = argv[0], argv[1:]
    if cmd == "list":
        kind = args[0] if args else "colors"
        listers = {"colors": list_colors, "desktoptheme": list_desktopthemes, "icons": list_icons,
                   "lookandfeel": list_lookandfeel, "aurorae": list_aurorae}
        if kind not in listers:
            print(__doc__)
            return 1
        for item in listers[kind]():
            print(f"{item['id']}\t{item['name']}")
        return 0
    if cmd == "current":
        print(json.dumps(current(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "cursor":
        print("El cursor es común a todas las skins de BWM: cámbialo en Ajustes → Cursor.", file=sys.stderr)
        return 2
    handlers = {"colors": apply_colors, "desktoptheme": apply_desktoptheme, "icons": apply_icons,
                "lookandfeel": apply_lookandfeel}
    if cmd in handlers:
        if not args:
            print(__doc__)
            return 1
        return handlers[cmd](args[0])
    if cmd in ("save", "restore", "sync", "translations"):
        return {"save": save, "restore": restore, "sync": sync, "translations": install_translations}[cmd]()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

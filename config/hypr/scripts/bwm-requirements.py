#!/usr/bin/env python3
"""Comprueba los requisitos de BWM y de cada skin, y dice cómo instalar lo que falta.

Los requisitos viven en config/hypr/skins/: requirements.json (núcleo + catálogo) y un
<id>.json por skin. Lo usan install.sh (sale si falta algo), el comando `bwm` y la
bienvenida (bwmWelcome.qml, con --json).

  bwm-requirements.py check [--skin ID]... [--json] [--pre-install] [--distro FAMILIA]
  bwm-requirements.py skins [--json]

--pre-install: lo que instala o compila el propio instalador (fuentes, plugin hyprbars)
no cuenta como fallo. --distro fuerza la familia para los comandos (gentoo, arch, fedora,
debian, opensuse). Código de salida: 0 si el núcleo y las skins pedidas están listos.
Sólo lee el sistema: no instala nada.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKINS_DIR = REPO / "config" / "hypr" / "skins"
USER_SKINS_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "bwm" / "skins"
THEME_MANAGER = REPO / "config" / "hypr" / "scripts" / "bwm-theme-manager.py"
SKIN_ORDER = ["default", "retro", "plasma"]
EXTRA_PATH = [str(Path.home() / ".local" / "bin"), "/usr/local/bin", "/usr/libexec"]

FAMILIES = {
    "gentoo": "gentoo", "funtoo": "gentoo",
    "arch": "arch", "cachyos": "arch", "endeavouros": "arch", "manjaro": "arch", "garuda": "arch", "artix": "arch",
    "fedora": "fedora", "nobara": "fedora", "ultramarine": "fedora",
    "debian": "debian", "ubuntu": "debian", "linuxmint": "debian", "pop": "debian",
    "opensuse": "opensuse", "opensuse-tumbleweed": "opensuse", "suse": "opensuse",
    "nixos": "nixos",
}
FAMILY_NAMES = {"gentoo": "Gentoo", "arch": "Arch Linux", "fedora": "Fedora", "debian": "Debian/Ubuntu",
                "opensuse": "openSUSE", "nixos": "NixOS", "unknown": "tu distribución"}

OK, MISSING, OUTDATED, PENDING, BUILD = "ok", "missing", "outdated", "pending", "build"
PRE_INSTALL_OK = {OK, PENDING, BUILD}


# ── Sistema ──────────────────────────────────────────────────────────────────

def read_os_release() -> dict:
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError:
            continue
        data = {}
        for line in text.splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            data[key.strip()] = value
        return data
    return {}


def detect_distro(forced: str | None = None) -> dict:
    info = read_os_release()
    family = forced or "unknown"
    if not forced:
        for candidate in [info.get("ID", "")] + info.get("ID_LIKE", "").split():
            if candidate.lower() in FAMILIES:
                family = FAMILIES[candidate.lower()]
                break
    return {"id": info.get("ID", ""), "name": info.get("PRETTY_NAME") or info.get("NAME") or "Linux",
            "family": family, "familyName": FAMILY_NAMES.get(family, family)}


def which(name: str) -> str | None:
    if "/" in name:
        path = Path(name).expanduser()
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(name, path=os.pathsep.join([os.environ.get("PATH", "")] + EXTRA_PATH))


def run(cmd: list[str], timeout: float = 5) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or "") + (out.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return ""


def version_tuple(text: str) -> tuple:
    return tuple(int(p) for p in re.findall(r"\d+", text)[:3])


def qt_dirs(kind: str) -> list[Path]:
    """Carpetas de módulos QML (kind='qml') o de plugins de Qt 6 (kind='plugins')."""
    dirs = []
    if kind == "qml":
        for var in ("QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
            dirs += [Path(p) for p in os.environ.get(var, "").split(":") if p]
    query = "QT_INSTALL_QML" if kind == "qml" else "QT_INSTALL_PLUGINS"
    for tool in ("qtpaths6", "qtpaths-qt6", "qmake6"):
        if which(tool):
            value = run([tool, "-query", query]).strip().splitlines()
            if value and value[0].startswith("/"):
                dirs.append(Path(value[0]))
    for base in ("/usr/lib64/qt6", "/usr/lib/qt6", "/usr/lib/x86_64-linux-gnu/qt6",
                 "/usr/lib/aarch64-linux-gnu/qt6", "/run/current-system/sw/lib/qt-6"):
        dirs.append(Path(base) / kind)
    return [d for d in dict.fromkeys(dirs) if d.is_dir()]


def running_hyprland_commit() -> str:
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") and which("hyprctl"):
        try:
            return json.loads(run(["hyprctl", "version", "-j"])).get("commit", "")
        except ValueError:
            pass
    match = re.search(r"at commit ([0-9a-f]{40})", run(["Hyprland", "--version"]))
    return match.group(1) if match else ""


# ── Comprobaciones ───────────────────────────────────────────────────────────

def check_requirement(spec: dict, catalog: dict) -> tuple[str, str]:
    """(estado, detalle) de un requisito."""
    check = spec.get("check", {})
    kind = check.get("type")
    if kind == "cmd":
        names = check.get("all") or check.get("any") or []
        found = [n for n in names if which(n)]
        if check.get("all"):
            missing = [n for n in names if n not in found]
            return (OK, "") if not missing else (MISSING, "falta " + ", ".join(missing))
        return (OK, "") if found else (MISSING, "no está " + " / ".join(names))
    if kind == "version":
        if not which(check["cmd"][0]):
            return MISSING, f"no está {check['cmd'][0]}"
        match = re.search(check["regex"], run(check["cmd"]))
        if not match:
            return MISSING, "no se pudo leer la versión"
        found = match.group(1)
        if version_tuple(found) < version_tuple(check["min"]):
            return OUTDATED, f"{found}; hace falta {check['min']} o superior"
        tested = check.get("tested")
        if tested and version_tuple(found) < version_tuple(tested):
            return OK, f"{found} (BWM se prueba con {tested})"
        return OK, found
    if kind == "python":
        found = ".".join(map(str, sys.version_info[:3]))
        return (OK, found) if sys.version_info[:2] >= version_tuple(check["min"])[:2] \
            else (OUTDATED, f"{found}; hace falta {check['min']}")
    if kind == "pymodule":
        return (OK, "") if importlib.util.find_spec(check["module"]) else (MISSING, f"python3 no encuentra {check['module']}")
    if kind == "qml":
        for base in qt_dirs("qml"):
            if (base / check["module"] / "qmldir").is_file():
                return OK, str(base / check["module"])
        return MISSING, f"no está el módulo QML {check['module'].replace('/', '.')}"
    if kind == "qtplugin":
        for base in qt_dirs("plugins"):
            if (base / check["path"]).is_file():
                return OK, ""
        return MISSING, f"no está el plugin de Qt {check['path']}"
    if kind == "path":
        for p in check["any"]:
            if Path(p).expanduser().exists():
                return OK, ""
        return MISSING, "no está instalado"
    if kind == "font":
        if not which("fc-list"):
            return MISSING, "sin fontconfig no se puede comprobar"
        families = run(["fc-list", ":", "family"], timeout=15)
        return (OK, "") if check["family"].lower() in families.lower() else (MISSING, f"no está la fuente {check['family']}")
    if kind == "pkgconfig":
        missing = [c for c in check.get("cmds", []) if not which(c)]
        if which("pkg-config"):
            missing += [m for m in check.get("modules", [])
                        if subprocess.run(["pkg-config", "--exists", m], capture_output=True).returncode != 0]
        return (OK, "") if not missing else (MISSING, "falta " + ", ".join(dict.fromkeys(missing)))
    if kind == "hyprland-plugin":
        plugin = REPO / check["path"]
        if not plugin.is_file():
            state, detail = MISSING, "no está compilado"
        else:
            built = set(re.findall(rb"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", plugin.read_bytes()))
            commit = running_hyprland_commit()
            if commit and commit.encode() in built:
                return OK, f"compilado para Hyprland {commit[:8]}"
            built_for = next(iter(built), b"").decode()[:8] or "?"
            state = MISSING
            detail = f"compilado para Hyprland {built_for}, usas {commit[:8] or '?'}: hay que recompilarlo"
        tools = catalog.get("plugin-build")
        if tools and check_requirement(tools, catalog)[0] == OK:
            return BUILD, detail
        return state, detail + " (faltan herramientas para compilarlo)"
    return MISSING, f"comprobación desconocida: {kind}"


def evaluate(ids: list[str], catalog: dict) -> list[dict]:
    results = []
    for rid in ids:
        spec = catalog.get(rid)
        if not spec:
            results.append({"id": rid, "label": rid, "why": "", "status": MISSING, "detail": "no está en el catálogo"})
            continue
        status, detail = check_requirement(spec, catalog)
        if status == MISSING and spec.get("provider") == "bwm":
            status = PENDING
            detail = "la instala install.sh"
        results.append({"id": rid, "label": spec.get("label", rid), "why": spec.get("why", ""),
                        "status": status, "detail": detail})
    return results


def group_ok(results: list[dict], pre_install: bool) -> bool:
    allowed = PRE_INSTALL_OK if pre_install else {OK}
    return all(r["status"] in allowed for r in results)


# ── Comandos de instalación ──────────────────────────────────────────────────

def install_plan(results: list[dict], catalog: dict, family: str, links: dict) -> dict:
    """Comandos para instalar los requisitos que fallan en la familia de distros dada."""
    gentoo_repos, packages, aur, coprs = [], [], [], []
    manual, notes, builds = [], [], []
    failing = [r for r in results if r["status"] not in (OK,)]
    for r in failing:
        spec = catalog.get(r["id"], {})
        if r["status"] == PENDING:
            manual.append(f"{spec.get('label', r['id'])}: ejecuta ./install.sh (la trae BWM)")
            continue
        if spec.get("check", {}).get("type") == "hyprland-plugin":
            if r["status"] != BUILD:
                failing_tools = catalog.get("plugin-build")
                if failing_tools:
                    failing.append({"id": "plugin-build", "status": MISSING})
            builds.append(spec.get("build", "").replace("{repo}", str(REPO)))
            note = spec.get("notes", {}).get("all")
            if note:
                notes.append(note)
            continue
        pkg = spec.get("packages", {}).get(family)
        if not pkg:
            hint = spec.get("manual") or links.get(spec.get("guide", ""), "") or links.get("requirements", "")
            manual.append(f"{spec.get('label', r['id'])}: {hint}")
            continue
        for token in pkg.split():
            prefix, _, rest = token.partition(":")
            if family == "gentoo" and rest and "/" not in prefix:
                gentoo_repos.append(prefix)
                packages.append(rest)
            elif family == "arch" and prefix == "aur" and rest:
                aur.append(rest)
            elif family == "fedora" and prefix == "copr" and rest:
                repo, _, name = rest.rpartition(":")
                coprs.append(repo)
                packages.append(name)
            else:
                packages.append(token)
        for key in (family, "all"):
            if spec.get("notes", {}).get(key):
                notes.append(spec["notes"][key])
    packages, aur = list(dict.fromkeys(packages)), list(dict.fromkeys(aur))
    commands = []
    if family == "gentoo":
        repos = [r for r in dict.fromkeys(gentoo_repos) if not Path(f"/var/db/repos/{r}").is_dir()]
        if repos:
            commands.append("sudo emerge --ask --noreplace app-eselect/eselect-repository")
            commands.append("sudo eselect repository enable " + " ".join(repos))
            commands.append("sudo emaint sync " + " ".join(f"-r {r}" for r in repos))
        if packages:
            commands.append("sudo emerge --ask --noreplace " + " ".join(packages))
            notes.append("Si Portage pide palabras clave (~amd64) o USE, acéptalas con --autounmask-write y revisa con dispatch-conf.")
    elif family == "arch":
        if packages:
            commands.append("sudo pacman -S --needed " + " ".join(packages))
        if aur:
            commands.append("paru -S --needed " + " ".join(aur) + "   # o yay")
    elif family == "fedora":
        commands += [f"sudo dnf copr enable {c}" for c in dict.fromkeys(coprs)]
        if packages:
            commands.append("sudo dnf install " + " ".join(packages))
    elif family == "opensuse" and packages:
        commands.append("sudo zypper install " + " ".join(packages))
    elif family == "debian" and packages:
        commands.append("sudo apt install " + " ".join(packages))
    commands += [b for b in dict.fromkeys(builds) if b]
    return {"commands": commands, "manual": list(dict.fromkeys(manual)), "notes": list(dict.fromkeys(notes))}


# ── Skins ────────────────────────────────────────────────────────────────────

def load_data() -> tuple[dict, list[dict]]:
    base = json.loads((SKINS_DIR / "requirements.json").read_text(encoding="utf-8"))
    skins = {}
    for folder in (SKINS_DIR, USER_SKINS_DIR):
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            if path.name == "requirements.json":
                continue
            try:
                skin = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(skin, dict) or not skin.get("id"):
                continue
            base["catalog"] = {**skin.get("catalog", {}), **base["catalog"]}
            skin["builtin"] = folder == SKINS_DIR
            skins.setdefault(skin["id"], skin)
    ordered = sorted(skins.values(), key=lambda s: (SKIN_ORDER.index(s["id"]) if s["id"] in SKIN_ORDER else 99, s["id"]))
    return base, ordered


def current_skin() -> str:
    out = run([sys.executable, str(THEME_MANAGER), "get"]).strip().splitlines()
    return out[-1] if out else ""


def report(selected: list[str] | None, pre_install: bool, family: str | None) -> dict:
    base, skins = load_data()
    catalog, links = base["catalog"], base.get("links", {})
    distro = detect_distro(family)
    core_req = evaluate(base["core"]["requires"], catalog)
    core_rec = evaluate(base["core"].get("recommends", []), catalog)
    data = {
        "distro": distro, "repo": str(REPO), "links": links, "current": current_skin(),
        "core": {"ok": group_ok(core_req, pre_install), "requires": core_req, "recommends": core_rec,
                 "plan": install_plan(core_req, catalog, distro["family"], links),
                 "recommendPlan": install_plan(core_rec, catalog, distro["family"], links)},
        "skins": [],
    }
    for skin in skins:
        if selected and skin["id"] not in selected:
            continue
        req = evaluate(skin.get("requires", []), catalog)
        rec = evaluate(skin.get("recommends", []), catalog)
        ready = data["core"]["ok"] and group_ok(req, pre_install)
        preview = skin.get("preview", "")
        data["skins"].append({
            **{k: skin.get(k) for k in ("id", "name", "imitates", "upstream", "description", "defaultTheme", "themes", "builtin")},
            "preview": str(REPO / preview) if preview and not preview.startswith("/") else preview,
            "ready": ready, "requires": req, "recommends": rec,
            "plan": install_plan(req, catalog, distro["family"], links),
            "recommendPlan": install_plan(rec, catalog, distro["family"], links),
        })
    data["ok"] = data["core"]["ok"] and all(s["ready"] for s in data["skins"])
    return data


# ── Salida de texto ──────────────────────────────────────────────────────────

def colours() -> dict:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return {k: "" for k in ("g", "r", "y", "c", "b", "d", "n")}
    return {"g": "\033[32m", "r": "\033[31m", "y": "\033[33m", "c": "\033[36m", "b": "\033[1m", "d": "\033[2m", "n": "\033[0m"}


def print_group(title: str, required: list[dict], recommended: list[dict], c: dict):
    print(f"\n{c['b']}{title}{c['n']}")
    marks = {OK: f"{c['g']}✓", PENDING: f"{c['c']}•", BUILD: f"{c['y']}⚙", OUTDATED: f"{c['r']}✗", MISSING: f"{c['r']}✗"}
    for r in required:
        detail = f" {c['d']}({r['detail']}){c['n']}" if r["detail"] and r["status"] != OK else ""
        print(f"  {marks[r['status']]}{c['n']} {r['label']}{detail}")
        if r["status"] != OK:
            print(f"      {c['d']}{r['why']}{c['n']}")
    missing_rec = [r for r in recommended if r["status"] != OK]
    if missing_rec:
        print(f"  {c['d']}Recomendado (opcional): " + ", ".join(r["label"] for r in missing_rec) + c["n"])


def print_plan(title: str, plan: dict, c: dict):
    if not any(plan.values()):
        return
    print(f"\n{c['b']}{title}{c['n']}")
    for cmd in plan["commands"]:
        print(f"  {c['c']}{cmd}{c['n']}")
    for item in plan["manual"]:
        print(f"  • {item}")
    for note in plan["notes"]:
        print(f"  {c['d']}ℹ {note}{c['n']}")


def print_report(data: dict, pre_install: bool):
    c = colours()
    distro = data["distro"]
    print(f"{c['b']}BWM · requisitos{c['n']} — {distro['name']} (familia: {distro['familyName']})")
    print_group("Núcleo: lo que necesita cualquier skin para pintar la pantalla",
                data["core"]["requires"], data["core"]["recommends"], c)
    for skin in data["skins"]:
        mode = "dinámico" if skin["defaultTheme"]["mode"] == "dynamic" else "estático"
        state = f"{c['g']}lista{c['n']}" if skin["ready"] else f"{c['r']}faltan requisitos{c['n']}"
        print_group(f"Skin {skin['name']} — imita {skin['imitates']} · tema por defecto: "
                    f"{skin['defaultTheme']['name']} ({mode}) · {state}",
                    skin["requires"], skin["recommends"], c)
    plan_title = f"Para instalar lo que falta en {distro['familyName']}:"
    merged = {"commands": [], "manual": [], "notes": []}
    for plan in [data["core"]["plan"]] + [s["plan"] for s in data["skins"]]:
        for key in merged:
            merged[key] += [x for x in plan[key] if x not in merged[key]]
    if pre_install:  # lo que hace el instalador no es tarea del usuario
        merged["manual"] = [m for m in merged["manual"] if "install.sh" not in m]
        merged["commands"] = [x for x in merged["commands"] if "make install" not in x]
    print_plan(plan_title, merged, c)
    optional = {"commands": [], "manual": [], "notes": []}
    for plan in [data["core"]["recommendPlan"]] + [s["recommendPlan"] for s in data["skins"]]:
        for key in optional:
            optional[key] += [x for x in plan[key] if x not in optional[key]]
    print_plan("Opcional (recomendado):", optional, c)
    if distro["family"] in ("unknown", "nixos") or (not merged["commands"] and merged["manual"]):
        print(f"  Guía de requisitos: {data['links'].get('requirements', '')}")
    if data["ok"]:
        print(f"\n{c['g']}{c['b']}Todo listo.{c['n']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Requisitos de BWM y sus skins")
    parser.add_argument("action", nargs="?", default="check", choices=["check", "skins"])
    parser.add_argument("--skin", action="append", help="sólo esta skin (repetible)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pre-install", action="store_true", help="no cuenta lo que hace el instalador")
    parser.add_argument("--distro", choices=sorted(set(FAMILIES.values()) | {"unknown"}))
    args = parser.parse_args()

    data = report(args.skin, args.pre_install, args.distro)
    if args.skin:
        unknown = set(args.skin) - {s["id"] for s in data["skins"]}
        if unknown:
            print("Skin desconocida: " + ", ".join(sorted(unknown)), file=sys.stderr)
            return 2
    if args.json:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=1)
        print()
    elif args.action == "skins":
        c = colours()
        for skin in data["skins"]:
            mark = f"{c['g']}●" if skin["ready"] else f"{c['r']}●"
            active = " (activa)" if skin["id"] == data["current"] else ""
            print(f"{mark}{c['n']} {skin['id']:<8} {skin['name']} — imita {skin['imitates']}{active}")
    else:
        print_report(data, args.pre_install)
    return 0 if data["ok"] or args.action == "skins" else 1


if __name__ == "__main__":
    sys.exit(main())

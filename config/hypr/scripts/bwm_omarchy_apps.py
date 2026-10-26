#!/usr/bin/env python3
"""
Estilo Retro: los temas de apps de Omarchy (default/themed/*.tpl, MIT), como omarchy-theme-set.

render_theme_dir() rellena todas las plantillas de hypr/omarchy/themed con la paleta del tema Retro
en ~/.local/state/bwm/omarchy/theme (un tema estático de Omarchy aporta antes sus propios archivos:
neovim.lua, vscode.json, btop.theme... y la plantilla sólo cubre lo que falta), y
~/.local/state/omarchy/current/theme apunta ahí, la ruta que leen las configuraciones de Omarchy.

apply_apps() hace lo de cada omarchy-theme-set-<app>, aunque la app no esté instalada:
  alacritty / ghostty / foot   incluyen el tema desde su config (se crea si no existe)
  helix                        themes/omarchy.toml + theme = "omarchy"
  neovim                       lua/plugins/theme.lua -> neovim.lua (si hay una config LazyVim)
  VS Code / VSCodium / Cursor  extensión generada «Omarchy» o la del tema estático (vscode.json)
  Obsidian                     tema «Omarchy» en cada bóveda
  Claude Code, pi, Hermes, T3  sus temas/skins «omarchy»
  fcitx5                       tema «omarchy»
  tmux                         colores de la barra y los bordes en las sesiones abiertas
Chromium (política de navegador, necesita root), gum, el teclado RGB y hyprland.lua (Hyprland ya
lo pinta retro_colors.lua) se dejan generados en el directorio del tema.

restore_apps() devuelve, al salir de Retro, lo que se activó al entrar (tema de Helix, de Claude
Code, de pi y de los editores VS Code), guardado en app-restore.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
DATA = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share"))
STATE_DIR = HOME / ".local" / "state" / "bwm" / "omarchy"
THEME_DIR = STATE_DIR / "theme"
OMARCHY_THEME_LINK = HOME / ".local" / "state" / "omarchy" / "current" / "theme"
OMARCHY_THEME_PATH = "~/.local/state/omarchy/current/theme"  # as Omarchy's configs write it
TEMPLATES = Path(__file__).resolve().parent.parent / "omarchy" / "themed"
RESTORE = STATE_DIR / "app-restore.json"

# Files of a static theme that are not app configs
NOT_CONFIG = {"preview.png", "preview-unlock.png", "unlock.png", "light.mode"}


def _write(path: Path, content: str) -> bool:
    try:
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == content:
            return False
    except Exception:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".bwm-tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    return True


def _restore_state() -> dict:
    try:
        return json.loads(RESTORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_restore(key: str, value):
    """Remember what an app had before Retro, only the first time (not our own value)."""
    state = _restore_state()
    if key not in state:
        state[key] = value
        _write(RESTORE, json.dumps(state, indent=2))


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


# ------------------------------------------------------------------------------ theme directory
def render_theme_dir(colors: dict, render, static_dir: Path | None = None) -> Path:
    """`render` is bwm_omarchy.render_omarchy (template text, colors) -> text."""
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    produced = set()

    if static_dir and static_dir.is_dir():
        for f in static_dir.iterdir():
            if f.name in NOT_CONFIG or f.name == "colors.toml":
                continue
            dest = THEME_DIR / f.name
            if f.is_dir():  # backgrounds/
                if dest.is_symlink() or dest.is_file():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(dest)
                dest.symlink_to(f)
            else:
                _write(dest, f.read_text(encoding="utf-8", errors="replace"))
            produced.add(f.name)

    _write(THEME_DIR / "colors.toml", "\n".join(f'{k} = "{v}"' for k, v in colors.items()) + "\n")
    produced.add("colors.toml")
    for tpl in sorted(TEMPLATES.glob("*.tpl")):
        name = tpl.name[:-4]
        if name in produced:
            continue
        _write(THEME_DIR / name, render(tpl.read_text(encoding="utf-8"), colors))
        produced.add(name)

    # A file the previous theme shipped (its neovim.lua, vscode.json...) must not outlive it
    # (shell.toml and tmux.conf are written right after, by apply_shell/apply_tmux)
    for f in THEME_DIR.iterdir():
        if f.name not in produced | {"shell.toml", "tmux.conf"} and not f.name.endswith(".bwm-tmp"):
            if f.is_dir() and not f.is_symlink():
                shutil.rmtree(f)
            else:
                f.unlink()

    try:
        OMARCHY_THEME_LINK.parent.mkdir(parents=True, exist_ok=True)
        if OMARCHY_THEME_LINK.is_symlink() or OMARCHY_THEME_LINK.is_file():
            OMARCHY_THEME_LINK.unlink()
        elif OMARCHY_THEME_LINK.is_dir():
            shutil.rmtree(OMARCHY_THEME_LINK)
        OMARCHY_THEME_LINK.symlink_to(THEME_DIR)
    except Exception as e:
        print(f"[Warning] {OMARCHY_THEME_LINK}: {e}", file=sys.stderr)
    return THEME_DIR


# ------------------------------------------------------------------------------ terminals
def apply_terminals():
    # Alacritty reloads its config (and imports) live
    ala = CONFIG / "alacritty" / "alacritty.toml"
    line = f'general.import = [ "{OMARCHY_THEME_PATH}/alacritty.toml" ]'
    if not ala.exists():
        _write(ala, line + "\n")
    elif "current/theme/alacritty.toml" not in ala.read_text(encoding="utf-8"):
        print(f"[Info] {ala}: añade «{line}» para usar el tema de Omarchy", file=sys.stderr)

    # Ghostty: config-file can go anywhere; reloads with its reload_config action
    gh = CONFIG / "ghostty" / "config"
    line = f'config-file = ?"{OMARCHY_THEME_PATH}/ghostty.conf"'
    if not gh.exists():
        _write(gh, line + "\n")
    elif "current/theme/ghostty.conf" not in gh.read_text(encoding="utf-8"):
        _write(gh, gh.read_text(encoding="utf-8").rstrip("\n") + "\n" + line + "\n")
    if subprocess.run(["pgrep", "-x", "ghostty"], stdout=subprocess.DEVNULL).returncode == 0:
        subprocess.run(["pkill", "-USR2", "-x", "ghostty"], check=False)

    # foot: include= at the top of the main section
    foot = CONFIG / "foot" / "foot.ini"
    line = f"include={OMARCHY_THEME_PATH}/foot.ini"
    if not foot.exists():
        _write(foot, line + "\n")
    elif "current/theme/foot.ini" not in foot.read_text(encoding="utf-8"):
        _write(foot, line + "\n" + foot.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------ editors
def _toml_set_top(text: str, key: str, value: str) -> tuple[str, str | None]:
    """Set a top-level `key = "value"` (before the first [table]); returns (text, old value)."""
    head, sep, rest = text.partition("\n[")
    m = re.search(rf'^\s*{key}\s*=\s*"([^"]*)"\s*$', head, flags=re.M)
    if m:
        old = m.group(1)
        head = head[:m.start()] + f'{key} = "{value}"' + head[m.end():]
    else:
        old = None
        head = f'{key} = "{value}"\n' + head
    return head + sep + rest, old


def apply_helix():
    src = THEME_DIR / "helix.toml"
    if not src.is_file():
        return
    _write(CONFIG / "helix" / "themes" / "omarchy.toml", src.read_text(encoding="utf-8"))
    cfg = CONFIG / "helix" / "config.toml"
    text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
    new, old = _toml_set_top(text, "theme", "omarchy")
    if old != "omarchy":
        _save_restore("helix", old)
    _write(cfg, new)
    subprocess.run(["pkill", "-USR1", "-x", "hx"], check=False)  # helix reloads its config on USR1


NVIM_CONFIG = Path(__file__).resolve().parent.parent.parent / "nvim"  # config/nvim del repo


def apply_neovim():
    """Omarchy's neovim.lua is a LazyVim plugin spec. Without a Neovim config, ~/.config/nvim becomes
    BWM's (config/nvim: LazyVim, every theme plugin installed, live reload like Omarchy's
    omarchy-theme-hotreload.lua); with one of the user's that has lua/plugins, only theme.lua is
    linked there. Plugins are installed ahead (headless Lazy sync), so Neovim opens themed."""
    nvim = CONFIG / "nvim"
    if not nvim.exists() and not nvim.is_symlink():
        nvim.symlink_to(NVIM_CONFIG)
    plugins = nvim / "lua" / "plugins"
    if not plugins.is_dir():
        return
    link = plugins / "theme.lua"
    if link.exists() and not link.is_symlink():
        return  # the user's own theme.lua
    if not link.is_symlink() or os.readlink(link) != str(OMARCHY_THEME_LINK / "neovim.lua"):
        link.unlink(missing_ok=True)
        link.symlink_to(OMARCHY_THEME_LINK / "neovim.lua")
    if (_have("nvim") and nvim.resolve() == NVIM_CONFIG
            and not (DATA / "nvim" / "lazy" / "LazyVim").is_dir()):
        subprocess.Popen(["nvim", "--headless", "+Lazy! sync", "+qa"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)


VSCODE_EDITORS = (
    ("code", CONFIG / "Code" / "User" / "settings.json", HOME / ".vscode" / "extensions"),
    ("codium", CONFIG / "VSCodium" / "User" / "settings.json", HOME / ".vscode-oss" / "extensions"),
    ("cursor", CONFIG / "Cursor" / "User" / "settings.json", HOME / ".cursor" / "extensions"),
)
VSCODE_EXT_ID = "local.omarchy-theme"
VSCODE_EXT_VERSION = "1.0.0"


def _vscode_register(ext_base: Path, ext_dir: Path):
    reg = ext_base / "extensions.json"
    try:
        entries = json.loads(reg.read_text(encoding="utf-8")) if reg.is_file() else []
    except Exception:
        return
    entries = [e for e in entries if e.get("identifier", {}).get("id") != VSCODE_EXT_ID]
    entries.append({
        "identifier": {"id": VSCODE_EXT_ID}, "version": VSCODE_EXT_VERSION,
        "location": {"$mid": 1, "fsPath": str(ext_dir), "external": f"file://{ext_dir}",
                     "path": str(ext_dir), "scheme": "file"},
        "relativeLocation": ext_dir.name,
    })
    _write(reg, json.dumps(entries))


def _vscode_generated_extension(ext_base: Path, mode: str):
    ext_dir = ext_base / "omarchy-theme"
    _write(ext_dir / "themes" / "omarchy-color-theme.json",
           (THEME_DIR / "vscode-theme.json").read_text(encoding="utf-8"))
    _write(ext_dir / "package.json", json.dumps({
        "name": "omarchy-theme", "displayName": "Omarchy Theme", "publisher": "local",
        "version": VSCODE_EXT_VERSION, "engines": {"vscode": "^1.70.0"}, "categories": ["Themes"],
        "contributes": {"themes": [{"label": "Omarchy", "uiTheme": "vs" if mode == "light" else "vs-dark",
                                    "path": "./themes/omarchy-color-theme.json", "_watch": True}]},
    }, indent=2))
    _vscode_register(ext_base, ext_dir)


def _jsonc_set_color_theme(path: Path, name: str) -> str | None:
    """Edit "workbench.colorTheme" in place (settings.json is JSONC: no round-trip). Returns the old one."""
    text = path.read_text(encoding="utf-8") if path.is_file() else "{\n}\n"
    m = re.search(r'("workbench\.colorTheme"\s*:\s*")([^"]*)(")', text)
    if m:
        old = m.group(2)
        text = text[:m.start(2)] + name.replace("\\", "") + text[m.end(2):]
    else:
        old = None
        text = re.sub(r"\{", '{\n    "workbench.colorTheme": "' + name + '",', text, count=1)
    _write(path, text)
    return old


def _vscode_has(ext_base: Path, ext: str) -> bool:
    return ext_base.is_dir() and any(p.name.lower().startswith(ext.lower() + "-") for p in ext_base.iterdir())


def _vscode_select(cmd: str, settings: Path, name: str):
    settings.parent.mkdir(parents=True, exist_ok=True)
    old = _jsonc_set_color_theme(settings, name)
    if old != name and (old is None or not _is_ours(old)):
        _save_restore(f"vscode:{cmd}", old)


def _is_ours(theme: str) -> bool:
    """A colorTheme BWM itself set (Omarchy's generated one or a static theme's)."""
    if theme == "Omarchy":
        return True
    for d in (Path(__file__).resolve().parent.parent / "omarchy" / "themes").glob("*/vscode.json"):
        try:
            if json.loads(d.read_text(encoding="utf-8")).get("name") == theme:
                return True
        except Exception:
            pass
    return False


def apply_vscode(mode: str):
    """The static theme's own extension (vscode.json) when it is installed; otherwise the generated
    «Omarchy» extension, while the theme's one installs in the background (vscode-install) and is
    selected only if that works (Open VSX, VSCodium's store, lacks some of them)."""
    descriptor = THEME_DIR / "vscode.json"
    name = ext = ""
    if descriptor.is_file():
        try:
            d = json.loads(descriptor.read_text(encoding="utf-8"))
            name, ext = str(d.get("name") or ""), str(d.get("extension") or "")
        except Exception:
            pass
        if not re.fullmatch(r'[^\x00-\x1f"\\]+', name or "x"):
            name = ""
        if not re.fullmatch(r"[A-Za-z0-9._-]+", ext):
            ext = ""
    # Also for editors that are not installed: they open with the theme already selected
    for cmd, settings, ext_base in VSCODE_EDITORS:
        if (THEME_DIR / "vscode-theme.json").is_file():
            ext_base.mkdir(parents=True, exist_ok=True)
            _vscode_generated_extension(ext_base, mode)
        if name and ext and _vscode_has(ext_base, ext):
            _vscode_select(cmd, settings, name)
            continue
        _vscode_select(cmd, settings, "Omarchy")
        if name and ext and _have(cmd):
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "vscode-install", cmd, ext, name],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def vscode_install(cmd: str, ext: str, name: str):
    settings, ext_base = next((s, e) for c, s, e in VSCODE_EDITORS if c == cmd)
    try:
        subprocess.run([cmd, "--install-extension", ext], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=180)
    except Exception:
        return
    # Still the theme in use (no other switch meanwhile) and really installed
    try:
        current = json.loads((THEME_DIR / "vscode.json").read_text(encoding="utf-8")).get("name")
    except Exception:
        current = None
    if current == name and _vscode_has(ext_base, ext):
        _vscode_select(cmd, settings, name)


# ------------------------------------------------------------------------------ other apps
def apply_obsidian():
    css = THEME_DIR / "obsidian.css"
    try:
        vaults = json.loads((CONFIG / "obsidian" / "obsidian.json").read_text(encoding="utf-8")).get("vaults", {})
    except Exception:
        return
    for v in vaults.values():
        path = Path(v.get("path", ""))
        if not (path / ".obsidian").is_dir():
            continue
        d = path / ".obsidian" / "themes" / "Omarchy"
        if not (d / "manifest.json").is_file():
            _write(d / "manifest.json", json.dumps({
                "name": "Omarchy", "version": "1.0.0", "minAppVersion": "0.16.0",
                "description": "Automatically syncs with your current Omarchy system theme colors and fonts",
                "author": "Omarchy", "authorUrl": "https://omarchy.org"}, indent=2))
        _write(d / "theme.css", css.read_text(encoding="utf-8"))


def _json_setting(path: Path, key: str, value: str, restore_key: str):
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except Exception:
        return  # not plain JSON: leave it
    if data.get(key) != value:
        _save_restore(restore_key, data.get(key))
        data[key] = value
        _write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def apply_agents():
    """Written even when the agent is not installed, so it starts with the theme."""
    # Claude Code: custom theme ~/.claude/themes/omarchy.json, selected as "custom:omarchy"
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
    _write(claude / "themes" / "omarchy.json", (THEME_DIR / "claude.json").read_text(encoding="utf-8"))
    _json_setting(claude / "settings.json", "theme", "custom:omarchy", "claude")
    # pi
    pi = HOME / ".pi" / "agent"
    _write(pi / "themes" / "omarchy-system.json", (THEME_DIR / "pi.json").read_text(encoding="utf-8"))
    _json_setting(pi / "settings.json", "theme", "omarchy-system", "pi")
    # Hermes: its gateway watches the skin file and repaints
    hermes = Path(os.environ.get("HERMES_HOME", HOME / ".hermes"))
    _write(hermes / "skins" / "omarchy.yaml", (THEME_DIR / "hermes.yaml").read_text(encoding="utf-8"))
    # T3 Code
    t3 = Path(os.environ.get("T3CODE_HOME", HOME / ".t3")) / "userdata"
    _write(t3 / "themes" / "omarchy.json", (THEME_DIR / "t3code.json").read_text(encoding="utf-8"))


def apply_fcitx5():
    d = DATA / "fcitx5" / "themes" / "omarchy"
    _write(d / "theme.conf", (THEME_DIR / "fcitx5-theme.conf").read_text(encoding="utf-8"))
    for glyph in Path("/usr/share/fcitx5/themes/default").glob("*.svg"):
        link = d / glyph.name
        if not link.exists():
            link.symlink_to(glyph)
    conf = CONFIG / "fcitx5" / "conf" / "classicui.conf"
    if True:  # also before fcitx5 is installed
        text = conf.read_text(encoding="utf-8") if conf.is_file() else ""
        for key in ("Theme", "DarkTheme"):
            m = re.search(rf"^{key}=(.*)$", text, flags=re.M)
            if not m:
                text += ("" if not text or text.endswith("\n") else "\n") + f"{key}=omarchy\n"
            elif m.group(1) in ("default", "default-dark"):
                text = text[:m.start(1)] + "omarchy" + text[m.end(1):]
        _write(conf, text)
    subprocess.run(["busctl", "--user", "--auto-start=no", "call", "org.fcitx.Fcitx5", "/controller",
                    "org.fcitx.Fcitx.Controller1", "ReloadAddonConfig", "s", "classicui"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def apply_share_picker():
    cfg = CONFIG / "hyprland-preview-share-picker" / "config.yaml"
    if cfg.parent.is_dir() and not cfg.exists():
        _write(cfg, f'stylesheets: ["../../.local/state/omarchy/current/theme/hyprland-preview-share-picker.css"]\n')


def _tmux_commands(c: dict) -> list:
    return [
        f"set -g status-style 'bg={c['background']},fg={c['foreground']}'",
        f"set -g window-status-current-style 'bg={c['accent']},fg={c['background']},bold'",
        f"set -g pane-border-style 'fg={c['muted']}'",
        f"set -g pane-active-border-style 'fg={c['accent']}'",
        f"set -g message-style 'bg={c['background']},fg={c['accent']}'",
        f"set -g mode-style 'bg={c['selection']},fg={c['bright_foreground']}'",
    ]


def apply_tmux(colors: dict):
    """tmux.conf in the theme directory, sourced from ~/.config/tmux/tmux.conf (created if missing),
    and applied live to the running sessions."""
    cmds = _tmux_commands(colors)
    _write(THEME_DIR / "tmux.conf", "\n".join(cmds) + "\n")
    conf = CONFIG / "tmux" / "tmux.conf"
    line = f"source-file -q {OMARCHY_THEME_PATH}/tmux.conf"
    if not conf.exists() and not (HOME / ".tmux.conf").exists():
        _write(conf, line + "\n")
    if not _have("tmux") or subprocess.run(["tmux", "list-sessions"], stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL).returncode != 0:
        return
    subprocess.run(["tmux", "source-file", "-"], input="\n".join(cmds) + "\n", text=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _osc(c: dict) -> str:
    """omarchy-theme-osc: foreground, background, cursor, selection and the 16 ANSI colours."""
    ansi = ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground", "muted",
            "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta", "bright_cyan",
            "bright_foreground"]
    out = "".join(f"\033]{code};{c[key]}\007" for code, key in
                  ((10, "foreground"), (11, "background"), (12, "cursor"), (17, "selection_background"),
                   (19, "selection_foreground")) if c.get(key))
    return out + "".join(f"\033]4;{i};{c[k]}\007" for i, k in enumerate(ansi) if c.get(k))


def recolor_foot(colors: dict):
    """omarchy-theme-set-foot: the OSC sequences written to the terminal of every shell foot runs."""
    pids = subprocess.run(["pgrep", "-x", "foot"], capture_output=True, text=True).stdout.split()
    seq = _osc(colors)
    for pid in pids:
        try:
            children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
        except Exception:
            continue
        for child in children:
            try:
                tty = os.readlink(f"/proc/{child}/fd/1")
                if tty.startswith("/dev/pts/"):
                    with open(tty, "w") as f:
                        f.write(seq)
            except Exception:
                pass


def apply_apps(colors: dict):
    mode = colors.get("mode", "dark")
    for step in (apply_terminals, apply_helix, apply_neovim, lambda: apply_vscode(mode), apply_obsidian,
                 apply_agents, apply_fcitx5, apply_share_picker, lambda: apply_tmux(colors),
                 lambda: recolor_foot(colors)):
        try:
            step()
        except Exception as e:
            print(f"[Warning] {getattr(step, '__name__', 'app')}: {e}", file=sys.stderr)


# ------------------------------------------------------------------------------ leaving Retro
def restore_apps():
    state = _restore_state()
    if not state:
        return
    try:
        if "helix" in state:
            cfg = CONFIG / "helix" / "config.toml"
            if cfg.is_file():
                text = cfg.read_text(encoding="utf-8")
                if state["helix"]:
                    text, _ = _toml_set_top(text, "theme", state["helix"])
                else:
                    text = re.sub(r'^\s*theme\s*=\s*"omarchy"\s*\n', "", text, count=1, flags=re.M)
                _write(cfg, text)
        for key, path in (("claude", Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude")) / "settings.json"),
                          ("pi", HOME / ".pi" / "agent" / "settings.json")):
            if key in state and path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                if state[key] is None:
                    data.pop("theme", None)
                else:
                    data["theme"] = state[key]
                _write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        for cmd, settings, _ext in VSCODE_EDITORS:
            key = f"vscode:{cmd}"
            if key in state and settings.is_file():
                text = settings.read_text(encoding="utf-8")
                if state[key]:
                    text = re.sub(r'("workbench\.colorTheme"\s*:\s*")[^"]*(")', rf'\g<1>{state[key]}\g<2>', text, count=1)
                else:
                    text = re.sub(r'\s*"workbench\.colorTheme"\s*:\s*"[^"]*",?', "", text, count=1)
                _write(settings, text)
    finally:
        RESTORE.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "vscode-install":
        vscode_install(*sys.argv[2:5])

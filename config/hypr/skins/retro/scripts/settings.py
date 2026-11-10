#!/usr/bin/env python3
"""Retro menu rows over BWM's existing managers; no additional settings store."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
ROOTS = {
    "cursor": "setup.cursor", "defaultapps": "setup.default",
    "autostart": "setup.autostart", "keybinds": "setup.keybindings",
    "plugins": "setup.plugin.manage", "plugin-catalog": "setup.plugin.catalog",
    "themes": "appearance.retro-palette.catalog",
}


def command(argv, timeout=30):
    result = subprocess.run(list(map(str, argv)), capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        try:
            message = json.loads(result.stdout).get("message", "")
        except (ValueError, AttributeError):
            message = ""
        raise ValueError(message or result.stderr.strip() or result.stdout.strip() or "No se pudo guardar")
    return result.stdout


def run(script, *args):
    output = command([sys.executable, SCRIPTS / script, *args])
    # Some existing managers report a failed write as JSON with exit status zero.
    for line in reversed(output.splitlines()):
        try:
            result = json.loads(line)
        except ValueError:
            continue
        if isinstance(result, dict) and result.get("success") is False:
            raise ValueError("No se pudo guardar")
    return output


def token(value):
    # Omarchy resolves IPC routes case-insensitively; ids must survive lowercasing.
    return value.encode().hex()


class Rows:
    def __init__(self, category):
        self.category = category
        self.root = ROOTS[category]
        self.entries = []
        self.fields = []

    def menu(self, key, label, parent=None):
        item_id = (parent or self.root) + "." + key
        self.entries.append(dict(id=item_id, parent=parent or self.root, label=label, icon=""))
        return item_id

    def field(self, parent, key, label, value, kind="text", choices=None, **extra):
        f = dict(id=parent + "." + key, parent=parent, label=label, type=kind,
                 backend="manager", value=value, category=self.category, key=key, **extra)
        if choices is not None:
            f["choices"] = [dict(label=str(label), value=value) for label, value in choices]
        self.fields.append(f)

    def result(self):
        return dict(entries=self.entries, fields=self.fields)


def cursor_rows(current, themes):
    rows = Rows("cursor")
    choices = [(t["name"], t["id"]) for t in themes]
    if current["theme"] not in [v for _, v in choices]:
        choices.insert(0, (current["theme"], current["theme"]))
    rows.field(rows.root, "theme", "Tema", current["theme"], "choice", choices)
    rows.field(rows.root, "size", "Tamaño", current["size"], "number", min=16, max=96, step=4, unit="px")
    return rows.result()


def default_rows(data):
    rows = Rows("defaultapps")
    for kind, label in [("terminal", "Terminal"), ("browser", "Navegador"), ("files", "Archivos"),
                        ("editor", "Editor"), ("taskmanager", "Monitor del sistema")]:
        info = data[kind]
        choices = [(o["name"], o["id"]) for o in info["options"]]
        if info["current"] and info["current"] not in [v for _, v in choices]:
            choices.insert(0, (info["current"], info["current"]))
        rows.field(rows.root, kind, label, info["current"], "choice", choices)
    return rows.result()


def autostart_rows(entries, apps):
    rows = Rows("autostart")
    choices = [(a["name"], a["id"]) for a in apps if a["id"] not in {e["file"] for e in entries}]
    if choices:
        rows.menu("add", "Añadir aplicación")
        rows.field(rows.root, "add", "Añadir aplicación", "", "choice", choices, operation="add-app")
    new = rows.menu("new", "Añadir comando")
    for key, label in [("name", "Nombre"), ("exec", "Comando")]:
        rows.field(new, key, label, "", draft=True)
    rows.field(new, "workspace", "Workspace", "default", "choice",
               [("Actual", "default")] + [(str(n), str(n)) for n in range(1, 11)], draft=True)
    rows.field(new, "save", "Añadir", None, "action", operation="create")
    for entry in entries:
        parent = rows.menu(token(entry["file"]), entry["name"])
        extra = dict(item=entry["file"])
        rows.field(parent, "enabled", "Activado", entry["enabled"], "bool", **extra)
        rows.field(parent, "workspace", "Workspace", entry["workspace"], "choice",
                   [("Actual", "default")] + [(str(n), str(n)) for n in range(1, 11)], **extra)
        remove = rows.menu("remove", "Quitar", parent)
        rows.field(remove, "confirm", "Quitar del inicio", None, "action", operation="remove", **extra)
    return rows.result()


def keybind_rows(entries):
    rows = Rows("keybinds")
    new = rows.menu("new", "Añadir atajo")
    for key, label, value in [("description", "Nombre", ""), ("combo", "Atajo", "Super + ")]:
        rows.field(new, key, label, value, draft=True)
    rows.field(new, "action_type", "Acción", "exec", "choice", [("Comando", "exec"), ("Hyprland", "dispatcher")], draft=True)
    rows.field(new, "exec", "Comando", "", draft=True, showIf="exec")
    rows.field(new, "dispatcher", "Acción de Hyprland", "window.close", draft=True, showIf="dispatcher")
    rows.field(new, "dispatcher_arg", "Argumento", "", draft=True, showIf="dispatcher")
    rows.field(new, "save", "Añadir", None, "action", operation="create")
    for entry in entries:
        if entry.get("skins") and "retro" not in entry["skins"]:
            continue
        combo = " + ".join(entry.get("mods", []) + [entry["key"]])
        parent = rows.menu(token(entry["id"]), entry["description"])
        # The combination is the value, rather than an extra explanatory paragraph.
        rows.entries[-1]["description"] = combo
        extra = dict(item=entry["id"])
        rows.field(parent, "enabled", "Activado", entry.get("enabled", True), "bool", **extra)
        rows.field(parent, "combo", "Atajo", combo, **extra)
        rows.field(parent, "description", "Nombre", entry["description"], **extra)
        if entry.get("action_type", "exec") == "exec":
            rows.field(parent, "exec", "Comando", entry.get("exec", ""), **extra)
        else:
            rows.field(parent, "dispatcher", "Acción de Hyprland", entry.get("dispatcher", ""), **extra)
            rows.field(parent, "dispatcher_arg", "Argumento", entry.get("dispatcher_arg", ""), **extra)
        if entry.get("is_default"):
            if entry.get("is_modified") or not entry.get("enabled", True):
                rows.field(parent, "reset", "Restablecer", None, "action", operation="reset", **extra)
        else:
            remove = rows.menu("remove", "Eliminar", parent)
            rows.field(remove, "confirm", "Eliminar atajo", None, "action", operation="purge", **extra)
    return rows.result()


def plugin_rows(plugins, layout):
    rows = Rows("plugins")
    placed = {p["id"]: section for section, items in layout.items() for p in items}
    positions = [("Izquierda", "left"), ("Antes del reloj", "centerBegin"), ("Centro", "center"),
                 ("Después del reloj", "centerEnd"), ("Bandeja", "tray"), ("Derecha", "right")]
    for plugin in plugins:
        if not plugin.get("canDisable") and "bar-widget" not in plugin["kinds"]:
            continue
        parent = rows.menu(token(plugin["id"]), plugin["name"])
        if plugin.get("canDisable"):
            rows.field(parent, "enabled", "Activado", plugin["enabled"], "bool", item=plugin["id"])
        if plugin["enabled"] and "bar-widget" in plugin["kinds"]:
            rows.field(parent, "section", "Posición", placed.get(plugin["id"], "right"), "choice", positions, item=plugin["id"])
    return rows.result()


def addon_module():
    # Reuse its cached catalogs, validation and installer; these are not another format.
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("bwm_addons", SCRIPTS / "bwm-addons.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def addon_rows(category, catalog, installed, installed_ids=(), query="", limit=60):
    rows = Rows(category)
    from_url = rows.menu("url", "Desde URL")
    rows.field(from_url, "url", "URL de Git", "", draft=True)
    rows.field(from_url, "install", "Instalar", None, "action", operation="install-url")
    words = query.casefold().split()
    matches = [a for a in catalog if all(w in " ".join(str(v) for v in a.values()).casefold() for w in words)]
    for addon in matches[:limit]:
        parent = rows.menu(token(addon["url"]), addon["name"])
        rows.entries[-1]["searchTerms"] = [addon.get("author", ""), addon.get("description", "")]
        rows.field(parent, "open", "Ver repositorio", None, "action", operation="open", item=addon["url"])
        addon_id = addon.get("id", "")
        if category == "themes":
            addon_id = re.sub(r"-(?:omarchy-)?theme$", "", re.sub(r"^omarchy-", "", urlsplit(addon["url"]).path.rstrip("/").split("/")[-1].lower()))
        present = addon["url"].removesuffix(".git").rstrip("/") in installed or addon_id in installed_ids
        if present:
            rows.entries[-1]["label"] += " ✓"
        else:
            rows.field(parent, "install", "Instalar", None, "action", operation="install", item=addon["url"])
    if len(matches) > limit:
        rows.field(rows.root, "more", "Mostrar más", None, "action", operation="more", searchTerms=[query])
    return rows.result()


def load(category, query="", limit=60):
    if category == "cursor":
        return cursor_rows(json.loads(run("cursor-manager.py", "get")), json.loads(run("cursor-manager.py", "list")))
    if category == "defaultapps":
        return default_rows(json.loads(run("default-apps.py", "list")))
    if category == "autostart":
        return autostart_rows(json.loads(run("autostart-manager.py", "list")), json.loads(run("autostart-manager.py", "list-apps")))
    if category == "keybinds":
        return keybind_rows(json.loads(run("keybinds-manager.py", "list")))
    if category == "plugins":
        plugins = json.loads(command([SCRIPTS / "omarchy-shims/omarchy-plugin-list", "--json"]))
        layout = json.loads(command(["qs", "-c", "ii", "ipc", "call", "shell", "listShellConfig"]))["bar"]["layout"]
        return plugin_rows(plugins, layout)
    if category in ("themes", "plugin-catalog"):
        module = addon_module()
        kind = "themes" if category == "themes" else "plugins"
        catalog, warning = module.remote_catalog(kind)
        data = module.installed()
        installed = {str(p.get("url", "")).removesuffix(".git").rstrip("/") for p in data[kind]}
        result = addon_rows(category, catalog, installed, {p["id"] for p in data[kind]}, query, limit)
        result["message"] = warning
        return result
    raise ValueError("Sección desconocida")


def combination(value):
    parts = [p.strip() for p in value.split("+")]
    aliases = {"SUPER": "SUPER", "CTRL": "CTRL", "CONTROL": "CTRL", "ALT": "ALT", "SHIFT": "SHIFT", "MAYÚS": "SHIFT"}
    if not parts[-1] or any(p.upper() not in aliases for p in parts[:-1]):
        raise ValueError("Atajo no válido")
    return ",".join(dict.fromkeys(aliases[p.upper()] for p in parts[:-1])), parts[-1]


def save(f, value, draft):
    category, key, item = f["category"], f["key"], f.get("item", "")
    operation = f.get("operation", "")
    if category == "cursor":
        current = json.loads(run("cursor-manager.py", "get"))
        current[key] = value
        run("cursor-manager.py", "apply", current["theme"], current["size"])
    elif category == "defaultapps":
        run("default-apps.py", "set", key, value)
    elif category == "autostart":
        if operation == "add-app":
            run("autostart-manager.py", "add-app", value)
        elif operation == "create":
            if not draft.get("name", "").strip() or not draft.get("exec", "").strip():
                raise ValueError("Faltan nombre y comando")
            run("autostart-manager.py", "add-custom", "--name", draft["name"], "--exec", draft["exec"], "--workspace", draft.get("workspace", "default"))
        elif operation == "remove":
            run("autostart-manager.py", "remove", item)
        elif key == "enabled":
            run("autostart-manager.py", "toggle", item, str(value).lower())
        elif key == "workspace":
            run("autostart-manager.py", "set-workspace", item, value)
    elif category == "keybinds":
        if operation == "create":
            action_type = draft.get("action_type", "exec")
            action = draft.get("exec", "") if action_type == "exec" else draft.get("dispatcher", "window.close")
            if not draft.get("description", "").strip() or not action.strip():
                raise ValueError("Faltan nombre y acción")
            mods, key = combination(draft.get("combo", ""))
            args = ["add", "--desc", draft["description"], "--mods", mods, "--key", key, "--type", action_type]
            args += ["--exec", action] if action_type == "exec" else ["--dispatcher", action, "--dispatcher-arg", draft.get("dispatcher_arg", "")]
            run("keybinds-manager.py", *args)
        elif operation in ("reset", "purge"):
            run("keybinds-manager.py", operation, "--id", item)
        else:
            args = ["update", "--id", item]
            if key == "combo":
                mods, bind_key = combination(value)
                args += ["--mods", mods, "--key", bind_key]
            else:
                flag = {"description": "desc", "dispatcher_arg": "dispatcher-arg"}.get(key, key)
                args += ["--" + flag, str(value).lower() if isinstance(value, bool) else value]
            run("keybinds-manager.py", *args)
    elif category == "plugins":
        if key == "enabled":
            command([SCRIPTS / "omarchy-shims" / ("omarchy-plugin-enable" if value else "omarchy-plugin-disable"), item])
        elif key == "section":
            command([SCRIPTS / "omarchy-shims/omarchy-plugin-enable", item, "--section", value])
    elif category in ("themes", "plugin-catalog"):
        if operation == "open":
            command(["xdg-open", item])
        else:
            url = draft.get("url", "") if operation == "install-url" else item
            action = "install-theme" if category == "themes" else "install-plugin"
            result = json.loads(command([sys.executable, SCRIPTS / "bwm-addons.py", action, url], timeout=180))
            if not result.get("ok", False):
                raise ValueError(result.get("message", "No se pudo instalar"))
    else:
        raise ValueError("Sección desconocida")


def main():
    try:
        if sys.argv[1] == "list":
            result = load(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "", int(sys.argv[4]) if len(sys.argv) > 4 else 60)
        elif sys.argv[1] == "save":
            save(*[json.loads(arg) for arg in sys.argv[2:5]])
            result = {"ok": True}
        else:
            raise ValueError("Acción desconocida")
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"ok": False, "message": str(error)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

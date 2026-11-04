#!/usr/bin/env python3
"""Apply end-4 colors before running app hooks; newer requests supersede old hooks."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import uuid

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
STATE = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "bwm/default-colors"


def toml_dump(data):
    """Preserve arbitrary Matugen options/templates, including third-party templates."""
    lines = []

    def value(item):
        if isinstance(item, bool):
            return str(item).lower()
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, list):
            return "[" + ", ".join(value(v) for v in item) + "]"
        if isinstance(item, dict):
            return "{ " + ", ".join(json.dumps(k) + " = " + value(v) for k, v in item.items()) + " }"
        if hasattr(item, "isoformat"):
            return item.isoformat()
        return repr(item)

    def table(items, path=()):
        if path:
            lines.append("[" + ".".join(json.dumps(k) for k in path) + "]")
        for key, item in items.items():
            if not isinstance(item, dict):
                lines.append(json.dumps(key) + " = " + value(item))
        for key, item in items.items():
            if isinstance(item, dict):
                table(item, (*path, key))
    table(data)
    return "\n".join(lines) + "\n"


def current(token):
    try:
        return (STATE / "request").read_text() == token and json.loads(
            (CONFIG / "illogical-impulse/config.json").read_text()
        ).get("appearance", {}).get("bwmTheme", "default") == "default"
    except (OSError, ValueError):
        return False


def run_hooks(payload):
    # Hooks see the newest files. Suppress app restarts and repeated compositor reloads.
    env = {**os.environ, "BWM_SKIN_SWITCH": "1"}
    with (STATE / "hooks.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for hook in payload["hooks"]:
            if not current(payload["token"]):
                break
            try:
                subprocess.run(hook, shell=True, env=env, timeout=30, check=False)
            except subprocess.TimeoutExpired:
                print("BWM: hook de colores agotó 30 s:", hook, flush=True)


def apply(args):
    STATE.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("BWM_COLORS_REQUEST") or uuid.uuid4().hex
    # Atomic replacement so hook workers never observe a partially written generation.
    if not os.environ.get("BWM_COLORS_REQUEST"):
        publish_request(token)
    if not current(token):
        return
    cfg_path = CONFIG / "matugen/config.toml"
    data = tomllib.loads(cfg_path.read_text())
    hooks = []
    for name, template in list(data.get("templates", {}).items()):
        # The original terminal generator owns Kitty; avoid an intermediate Matugen palette.
        if name == "kitty":
            del data["templates"][name]
            continue
        hook = template.pop("post_hook", None)
        if hook and name not in ("quickshell_colors", "hyprland_colors"):
            hooks.append(hook)
    # Rendering writes every palette first, without waiting for Steam, Spotify, GTK, etc.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", dir=cfg_path.parent) as temp:
        temp.write(toml_dump(data))
        temp.flush()
        subprocess.run(["matugen", *args, "--config", temp.name], check=True)
    if not current(token):
        return
    subprocess.run(["quickshell", "-c", "ii", "ipc", "call", "theme", "reload"], check=False)
    if os.environ.get("BWM_SKIN_SWITCH") != "1":
        subprocess.run(["hyprctl", "reload"], check=False)
    if hooks:
        with (STATE / "hooks.log").open("a") as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--hooks",
                              json.dumps({"token": token, "hooks": hooks})],
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             start_new_session=True)


def publish_request(token):
    STATE.mkdir(parents=True, exist_ok=True)
    request = STATE / (token + ".request")
    request.write_text(token)
    request.replace(STATE / "request")


def run_request(command):
    token = uuid.uuid4().hex
    publish_request(token)
    with (STATE / "apply.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not current(token):
            return 0
        return subprocess.run(["bash", *command], env={**os.environ, "BWM_COLORS_REQUEST": token}).returncode


if __name__ == "__main__":
    if sys.argv[1:2] == ["--request"]:
        sys.exit(run_request(sys.argv[2:]))
    elif sys.argv[1:2] == ["--hooks"]:
        run_hooks(json.loads(sys.argv[2]))
    else:
        apply(sys.argv[1:])

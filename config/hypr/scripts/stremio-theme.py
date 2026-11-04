#!/usr/bin/env python3
"""Enable BWM's CSS bridge only when Stremio Linux Flatpak is installed."""
import argparse
import configparser
import fcntl
from pathlib import Path
import subprocess
import shutil
import sys

APP = 'com.stremio.Stremio'
SCRIPTS = Path(__file__).resolve().parent
STATE = Path.home() / '.local/state/bwm/stremio'
PRELOAD = SCRIPTS / 'stremio-theme.cjs'


def installed():
    return bool(shutil.which('flatpak')) and subprocess.run(
        ['flatpak', 'info', APP], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=10).returncode == 0


def configure():
    override = subprocess.run(['flatpak', 'override', '--user', '--show', APP],
                              capture_output=True, text=True, check=True).stdout
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    cfg.read_string(override)
    options = cfg.get('Environment', 'NODE_OPTIONS', fallback='')
    require = f'--require="{PRELOAD}"'
    if str(PRELOAD) not in options:
        options = (options + ' ' + require).strip()
    subprocess.run(['flatpak', 'override', '--user',
                    f'--filesystem={SCRIPTS}:ro', f'--filesystem={STATE}:ro',
                    f'--env=NODE_OPTIONS={options}', f'--env=BWM_STREMIO_CSS={STATE / "theme.css"}',
                    APP], check=True)


LAUNCHER = Path.home() / '.local/share/applications' / f'{APP}.desktop'
EXPORTS = (Path.home() / '.local/share/flatpak/exports/share/applications', Path('/var/lib/flatpak/exports/share/applications'))
NO_DECORATIONS = '--no-window-decorations'
MARK = 'X-BWM-Generated=stremio-theme.py'


def launcher():
    """BWM's copy of Stremio's launcher, without its GTK title bar (Stremio's own
    --no-window-decorations): the bar is GTK and only takes the theme when Stremio starts, while
    the web UI under it changes live. Tiling skins have no title bars anyway (as Omarchy).
    Written only if there is no launcher of the user's own; updated when Flatpak changes it."""
    source = next((d / f'{APP}.desktop' for d in EXPORTS if (d / f'{APP}.desktop').is_file()), None)
    if source is None:
        return
    try:
        if LAUNCHER.exists() and MARK not in LAUNCHER.read_text(encoding='utf-8'):
            return  # the user's own
    except OSError:
        return
    lines = []
    for line in source.read_text(encoding='utf-8').splitlines():
        if line.startswith('Exec=') and NO_DECORATIONS not in line:
            line = line.replace(f' {APP}', f' {APP} {NO_DECORATIONS}', 1)
        lines.append(line)
        if line == '[Desktop Entry]':
            lines.append(MARK)
    text = '\n'.join(lines) + '\n'
    if not LAUNCHER.exists() or LAUNCHER.read_text(encoding='utf-8') != text:
        LAUNCHER.parent.mkdir(parents=True, exist_ok=True)
        LAUNCHER.write_text(text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup-only', action='store_true', help='Configure without restarting windows')
    args = parser.parse_args()
    if not installed():
        return
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'setup.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        configure()
        launcher()
        sys.path.insert(0, str(SCRIPTS))  # also when loaded by path (tests)
        import bwm_transition
        if args.setup_only or bwm_transition.switching():
            return
        # One initial restart attaches the bridge. Subsequent changes are read live.
        from bwm_omarchy import _hypr_clients, restart_app
        windows = [c for c in _hypr_clients() if c.get('class') == APP]
        if not windows:
            return
        try:
            if all(str(PRELOAD).encode() in Path(f'/proc/{c["pid"]}/environ').read_bytes() for c in windows):
                return
        except (FileNotFoundError, PermissionError):
            return  # A window closed during setup; the next launch already has the bridge.
        # Never interrupt playback just to attach the bridge; it loads on the next launch.
        if any(c.get('fullscreen') for c in windows):
            return
        playback = subprocess.run(
            ['busctl', '--user', 'get-property', 'org.mpris.MediaPlayer2.Stremio',
             '/org/mpris/MediaPlayer2', 'org.mpris.MediaPlayer2.Player', 'PlaybackStatus'],
            capture_output=True, text=True)
        if 'Playing' in playback.stdout:
            return
        restart_app(lambda c: c.get('class') == APP, ['flatpak', 'run', APP, NO_DECORATIONS])


if __name__ == '__main__':
    main()

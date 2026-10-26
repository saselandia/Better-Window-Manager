#!/usr/bin/env python3
"""Enable BWM's CSS bridge only when Stremio Linux Flatpak is installed."""
import argparse
import configparser
import fcntl
from pathlib import Path
import subprocess
import shutil

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
        if args.setup_only:
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
        restart_app(lambda c: c.get('class') == APP, ['flatpak', 'run', APP])


if __name__ == '__main__':
    main()

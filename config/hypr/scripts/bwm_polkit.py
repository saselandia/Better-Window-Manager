#!/usr/bin/env python3
"""Start exactly the external polkit agent selected by the skin manifest."""
import json
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import signal
import sys
import subprocess
import time
import bwm_session

AGENTS = {'hyprpolkitagent','polkit-kde-authentication-agent-1'}
ROOT = Path(__file__).resolve().parents[1]

def session_token():
    identity=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or os.environ.get('XDG_SESSION_ID') or 'unknown'
    return hashlib.sha256(identity.encode()).hexdigest()[:16]


def executable(skin):
    manifest=json.loads((ROOT/'skins'/skin/'skin.json').read_text())
    candidates=manifest.get('polkitAgent',[])
    if manifest.get('polkitEmbedded',False):return None
    if not candidates:candidates=['hyprpolkitagent','/usr/libexec/hyprpolkitagent','/usr/lib/hyprpolkitagent/hyprpolkitagent']
    return next((shutil.which(p) for p in candidates if shutil.which(p)),None)

def active_skin():
    result=subprocess.run([sys.executable,str(ROOT/'scripts/bwm-theme-manager.py'),'get'],capture_output=True,text=True,timeout=5)
    return result.stdout.strip() if result.returncode==0 else None


def session_matches(process):
    """An agent in another TTY/compositor session belongs to that session."""
    try:
        entries=(process/'environ').read_bytes().split(b'\0')
        environment={key.decode():value.decode() for entry in entries if b'=' in entry
                     for key,value in [entry.split(b'=',1)] if key in (b'HYPRLAND_INSTANCE_SIGNATURE',b'XDG_SESSION_ID')}
    except (OSError,UnicodeError):return False
    signature=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if signature and environment.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return environment['HYPRLAND_INSTANCE_SIGNATURE']==signature
    session=os.environ.get('XDG_SESSION_ID')
    return bool(session and environment.get('XDG_SESSION_ID')==session)


def configure(skin):
    if active_skin()!=skin:return False  # A delayed hook may belong to the skin we just left.
    command=executable(skin)
    selected=Path(command).name if command else None
    running=False
    stopped=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:
            if process.stat().st_uid!=os.getuid() or not session_matches(process):continue
            exe=(process/'exe').resolve(strict=True)
            if exe.name not in AGENTS:continue
            if exe.name==selected:running=True
            else:
                # Recheck executable and UID immediately before terminating only the known agent.
                if (process/'exe').resolve(strict=True)==exe and process.stat().st_uid==os.getuid() and session_matches(process):os.kill(int(process.name),signal.SIGTERM);stopped.append(process)
        except (OSError,ProcessLookupError):continue
    deadline=time.monotonic()+2
    while stopped and time.monotonic()<deadline:
        stopped=[p for p in stopped if (p/'exe').exists()]
        if stopped:time.sleep(0.05)
    if stopped:return False
    if command and not running:
        # A shell-owned agent is disabled by its skin condition before the replacement registers.
        return bwm_session.spawn([sys.executable,str(Path(__file__).resolve()),"run",skin], str(Path(os.environ.get("XDG_RUNTIME_DIR",f"/run/user/{os.getuid()}"))/f"bwm-polkit-agent-{session_token()}.log"))
    return True

def run_agent(skin):
    signal.pthread_sigmask(signal.SIG_SETMASK, [])
    runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
    with (runtime/f'bwm-polkit-agent-{session_token()}.lock').open('w') as lock:
        deadline=time.monotonic()+2
        while True:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()>deadline:return False
                time.sleep(0.1)
        for attempt in range(8):
            if active_skin()!=skin:return False
            command=executable(skin)
            if not command:return False
            started=time.monotonic()
            result=subprocess.run([command],check=False)
            # Only retry an early registration failure while the previous shell tears down.
            if result.returncode==0 or time.monotonic()-started>2:return result.returncode==0
            time.sleep(0.25)
    return False


if __name__=='__main__':
    args=sys.argv[1:]
    run=len(args)==2 and args[0]=='run'
    skin=args[-1] if args else ''
    if skin not in ('default','plasma','retro') or len(args)!=(2 if run else 1):
        raise SystemExit('usage: bwm_polkit.py [run] default|plasma|retro')
    raise SystemExit(0 if (run_agent(skin) if run else configure(skin)) else 1)

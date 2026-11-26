#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T4: original KSplash, theme logout host and transactional layout restart."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/"scripts"))
from bwm_wallpaper import atomic_write
import bwm_session

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded);return loaded
host=module("t4_host","plasma-host.py")
interface=module("t4_interface","interface-theme.py")
CONFIG=Path(os.environ.get("XDG_CONFIG_HOME",Path.home()/".config"))
STATE=Path(os.environ.get("XDG_STATE_HOME",Path.home()/".local/state"))
RUNTIME=host.RUNTIME_DIR
LEGACY=CONFIG/"bwm-plasma-host"

def bus(*args):
    result=subprocess.run(["busctl","--user","--auto-start=no","--timeout=1s",*args],capture_output=True,text=True,timeout=2)
    return result.stdout.strip() if result.returncode==0 else None

def splash_settings():
    cfg=interface.config("ksplashrc")
    engine=cfg.get("KSplash","Engine",fallback="KSplashQML")
    theme=cfg.get("KSplash","Theme",fallback="org.kde.breeze.desktop")
    if engine.lower() in ("none","") or theme.lower() in ("none",""):return None
    return theme

def finish_splash(pid):
    owner=bus("call","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixProcessID","s","org.kde.KSplash")
    if owner!=f"u {pid}":return
    # initial/wm are supplied by ksplashqml itself; duplicate stages are idempotent.
    for stage in ("startPlasma","kcminit","ksmserver","desktop"):
        bus("call","org.kde.KSplash","/KSplash","org.kde.KSplash","setStage","s",stage)

def splash_start():
    if host.current_skin()!="plasma":return 0
    theme=splash_settings()
    if not theme:return 0
    sig=os.environ.get("HYPRLAND_INSTANCE_SIGNATURE","")
    if not sig:return 1
    marker=RUNTIME/("bwm-plasma-splash-"+hashlib.sha256(sig.encode()).hexdigest()[:16])
    try:
        fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    except FileExistsError:return 0
    if bus("call","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetNameOwner","s","org.kde.KSplash"):return 0
    token=secrets.token_hex(16)
    if not bwm_session.spawn(["env","BWM_KSPLASH_TOKEN="+token,"ksplashqml","--nofork",theme],allow_fallback=False):return 1
    pid=None
    for _ in range(40):
        owner=bus("call","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixProcessID","s","org.kde.KSplash")
        if owner and owner.startswith("u "):
            observed=int(owner[2:])
            try:environment=Path(f"/proc/{observed}/environ").read_bytes().split(b"\0")
            except OSError:environment=[]
            if ("BWM_KSPLASH_TOKEN="+token).encode() in environment:pid=observed;break
        time.sleep(.05)
    if not pid:return 1
    for _ in range(200):
        if host.ready_pid() is not None or host.current_skin()!="plasma":break
        time.sleep(.1)
    finish_splash(pid)
    return 0

def validate_generation(directory):
    root=Path(directory)
    authority=(STATE/"bwm/plasma/session-profiles").resolve()
    if root.is_symlink() or root.parent.resolve()!=authority or not root.is_dir() or root.stat().st_uid!=os.getuid():
        raise ValueError("Invalid session generation")
    manifest=json.loads((root/"session.json").read_text())
    if manifest.get("version")!=1 or manifest.get("directory")!=str(root):raise ValueError("Invalid generation metadata")
    expected={"appletsrc","plasmashellrc","assignments.json","desktop-assignments.json"}
    if set(manifest.get("files",{}))!=expected:raise ValueError("Incomplete session generation")
    for name,digest in manifest["files"].items():
        if name not in ("appletsrc","plasmashellrc","assignments.json","desktop-assignments.json"):raise ValueError("Invalid native filename")
        path=root/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError("Native session generation changed")
    return root

def replace_layout(pid,candidate,previous):
    candidate=validate_generation(candidate);previous=validate_generation(previous)
    for _ in range(150):
        if not host.is_host_pid(pid):break
        time.sleep(.1)
    else:raise RuntimeError("Previous Corona did not close; original layout retained")
    # No native owner retains the destination: select another generation, never
    # overwrite the appletsrc of the Corona that just closed.
    if host.current_skin()!="plasma":return 1
    def select(path):atomic_write(LEGACY/"active-session.json",json.dumps({"version":1,"directory":str(path)}))
    select(candidate)
    try:
        if host.start_host()!=0 or host.ready_pid() is None:raise RuntimeError("New layout host did not become ready")
        ready=False
        for _ in range(50):
            info=json.loads(host.host_ctl("layout-status") or "{}")
            if info.get("registered") and info.get("root")==str(candidate) and info.get("desktops",0)>0 and info.get("panels") and not info.get("runtimeError") and all(p.get("status")=="visible" for p in info["panels"]):
                ready=True;break
            time.sleep(.1)
        if not ready:raise RuntimeError("New native panel/desktop did not render on its assigned outputs")
        result={"phase":"active","candidate":str(candidate),"previous":str(previous)}
    except Exception as error:
        host.stop_host();select(previous)
        restored=host.start_host()==0 and host.ready_pid() is not None
        result={"phase":"rolled-back","error":str(error),"restored":restored,"previous":str(previous)}
    atomic_write(LEGACY/"last-layout.json",json.dumps(result,indent=2))
    return 0 if result["phase"]=="active" else 1

def aux_ctl(command):
    import socket
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(1);connection.connect(str(RUNTIME/"bwm-plasma-logout.sock"))
            connection.sendall((command+"\n").encode());return connection.recv(32).decode().strip()
    except OSError:return None

def main(args):
    if args[0]=="splash-start":return splash_start()
    if args[0]=="splash-finish":finish_splash(int(args[1]));return 0
    if args[0] in ("cancel","toggle"):
        status=host.host_ctl("session-status")
        if args[0]=="cancel" or (status and json.loads(status).get("windows")) or aux_ctl("status")=="ok":
            return 0 if host.host_ctl("session-cancel")=="ok" or aux_ctl("cancel")=="ok" else 1
        return main(["prompt","all"])
    if args[0]=="prompt" and args[1] in ("all","shutdown","reboot","logout"):
        if host.current_skin()!="plasma":return 1
        if host.host_ctl("session-prompt "+args[1])=="ok":return 0
        return 0 if bwm_session.spawn(["env","QT_QPA_PLATFORM=wayland","QT_QPA_PLATFORMTHEME=kde",str(host.BINARY),"--logout-dialog",args[1]],allow_fallback=False) else 1
    if args[0]=="replace-layout":return replace_layout(int(args[1]),args[2],args[3])
    return 2

if __name__=="__main__":
    try:raise SystemExit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(f"Plasma session: {error}",file=sys.stderr);raise SystemExit(1)

#!/usr/bin/env python3
"""Interactive opt-in preview: disposable config/data, no connection to the session D-Bus."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import importlib.util
import secrets
import time

p=argparse.ArgumentParser()
p.add_argument('--binary',type=Path,required=True)
source=p.add_mutually_exclusive_group(required=True)
source.add_argument('--package',type=Path)
source.add_argument('--profile',type=Path,help='Existing private native test profile; keeps native files when this wrapper closes')
p.add_argument('--layer-panel',action='store_true',help='Explicit layer-shell preview; does not reserve screen space')
p.add_argument('--native-panel',action='store_true',help='Original org.kde.panel with two independent widget instances')
p.add_argument('--output',help='Output description (Hyprland desc:, e.g. "MAG 274Q X24"); connector names are not accepted')
p.add_argument('--native-policy',action='store_true',help='Explicit surface-policy test: native NormalPanel/WindowsGoBelow; may reserve workspace area on the selected output')
operation=p.add_mutually_exclusive_group()
operation.add_argument('--follow-skin',action='store_true',help='Explicitly register this isolated preview with the BWM skin-change hook')
operation.add_argument('--export-as',help='Copy --profile and its snapshot history to a named persistent XDG state profile; do not start a panel')
a=p.parse_args()
if a.export_as and not a.profile:p.error('--export-as requires --profile')
if a.profile and (not (a.follow_skin or a.export_as) or a.output):
    p.error('--profile requires --follow-skin or --export-as and uses its persisted output bindings instead of --output')
if a.follow_skin and not a.profile and not (a.native_panel and a.layer_panel and a.output):
    p.error('--follow-skin requires --native-panel --layer-panel --output DESCRIPTION')
if a.native_policy and not a.follow_skin:p.error('--native-policy requires --follow-skin (with a package or persisted profile)')
initial_skin='default'
if a.follow_skin:
    try:
        actual_config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'illogical-impulse/config.json'
        initial_skin=json.loads(actual_config.read_text()).get('appearance',{}).get('bwmTheme','default')
    except (OSError,ValueError): pass
    if initial_skin not in ('default','retro','plasma'):initial_skin='default'
    spec=importlib.util.spec_from_file_location('bwm_panel_session',Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/panel-session.py')
    session=importlib.util.module_from_spec(spec);spec.loader.exec_module(session)
plugin=json.loads((a.package/'metadata.json').read_text())['KPlugin']['Id'] if a.package else None
with tempfile.TemporaryDirectory(prefix='bwm-r4-preview-') as tmp:
    root=Path(tmp)
    env=dict(os.environ,XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),
             XDG_CACHE_HOME=str(root/'cache'),XDG_RUNTIME_DIR=str(root/'runtime'),
             XDG_CONFIG_DIRS=str(root/'defaults'),XDG_DATA_DIRS='/usr/local/share:/usr/share',
             DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
    env.pop('BWM_R4_NATIVE_PANEL_POLICY',None)
    if a.native_policy:env['BWM_R4_NATIVE_PANEL_POLICY']='1'
    if a.output: env['BWM_R4_OUTPUT']=a.output
    for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(mode=0o700)
    # This explicit interactive command preserves access to the selected Wayland display,
    # while config/data/cache/runtime and session D-Bus stay disposable. It is not used by
    # the automated offscreen tests or invoked automatically in the user's session.
    if env.get('WAYLAND_DISPLAY') and not env['WAYLAND_DISPLAY'].startswith('/'):
        actualRuntime=os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
        env['WAYLAND_DISPLAY']=str(Path(actualRuntime)/env['WAYLAND_DISPLAY'])
    packageRoot=root/'data/plasma/plasmoids';packageRoot.mkdir(parents=True)
    if a.package:
        subprocess.run(['kpackagetool6','--type','Plasma/Applet','--packageroot',str(packageRoot),'--install',str(a.package)],env=env,check=True)
    else:
        # Lookup installed packages in the caller's XDG data home; all new writes,
        # caches, runtime and D-Bus remain in this wrapper's disposable roots.
        original_data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
        env['XDG_DATA_DIRS']=str(original_data)+os.pathsep+os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
        checked=subprocess.run([str(a.binary),'--profile-info',str(a.profile.resolve())],env=env,capture_output=True,text=True)
        if checked.returncode:p.error(checked.stderr.strip())
        if a.export_as:
            exported=subprocess.run([str(a.binary),'--export-profile',str(a.profile.resolve()),a.export_as],env=env,capture_output=True,text=True)
            if exported.returncode:p.error(exported.stderr.strip())
            print(exported.stdout,end='');raise SystemExit(0)
    mode=('--layer-panel-preview' if a.layer_panel else '--panel-preview') if a.native_panel else ('--layer-preview' if a.layer_panel else '--preview')
    if a.follow_skin:
        token=secrets.token_hex(32);control=root/'runtime/control';control.mkdir(mode=0o700)
        session.atomic_json(control/'control.json',{'version':1,'token':token,'revision':0,'command':'skin','skin':'default'})
        env.update(BWM_R4_CONTROL_DIR=str(control),BWM_R4_SESSION_TOKEN=token)
        mode='--follow-panel-preview'
    if a.profile:mode='--serve-profile'
    child=subprocess.Popen([str(a.binary),mode,str(a.profile.resolve()) if a.profile else plugin],env=env)
    try:
        if a.follow_skin:
            deadline=time.monotonic()+5
            while not (control/'ack.json').exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
            session.register(control,child.pid,token)
            session.command({'controlDirectory':str(control),'token':token},'skin',initial_skin)
            print('Prueba R4 registrada: sigue Breeze/Retro/default. Ctrl+C detiene sólo el auxiliar.',flush=True)
        status=child.wait()
    except KeyboardInterrupt:
        if a.follow_skin:
            try:session.command({'controlDirectory':str(control),'token':token},'stop')
            except (OSError,ValueError,TimeoutError):child.terminate()
        else:child.terminate()
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired: child.kill();child.wait()
        status=130
    except (OSError,ValueError,TimeoutError) as error:
        print(f'No se pudo registrar la prueba R4: {error}',flush=True);child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        status=1
    finally:
        if a.follow_skin:
            session.unregister(token)
            session.drain(control)
    raise SystemExit(status)

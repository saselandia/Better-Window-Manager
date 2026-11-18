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
import re
from previewchecks import wait_task_source,wait_initial_ack

p=argparse.ArgumentParser()
p.add_argument('--binary',type=Path,required=True)
source=p.add_mutually_exclusive_group(required=True)
source.add_argument('--package',type=Path)
source.add_argument('--profile',type=Path,help='Existing private native test profile; keeps native files when this wrapper closes')
source.add_argument('--selected-profile',action='store_true',help='Explicit preview of the selected persistent native profile; native host resolves and leases it atomically')
source.add_argument('--builtin',help='Installed native widget ID, including compiled/resource applets')
p.add_argument('--desktop-actions',action='store_true',help='Explicitly connect native KWindowSystem desktop requests to the live common BWM manager; may minimize/restore your windows')
p.add_argument('--task-actions',action='store_true',help='Experimental native window task source and PID-guarded actions; desktop activation requires --native-desktops and a separately loaded provider')
p.add_argument('--all-desktops',action='store_true',help='Explicit disposable task preview using the native show-all-desktops option; cannot modify a saved profile')
p.add_argument('--session-appearance',action='store_true',help='Snapshot native KDE icons, palette, fonts and Plasma SVG theme into the disposable preview at startup; never executes layouts or follows later theme changes')
p.add_argument('--task-thumbnails',action='store_true',help='Capture hovered task windows in memory through Hyprland native toplevel protocols; disposable task preview only')
p.add_argument('--native-desktops',action='store_true',help='Require the already loaded/enabled experimental desktop provider and its per-connection activation barrier; never loads a plugin')
p.add_argument('--layer-panel',action='store_true',help='Explicit layer-shell preview; does not reserve screen space')
p.add_argument('--native-panel',action='store_true',help='Original org.kde.panel; task-action previews use one instance by default')
p.add_argument('--edit-mode',action='store_true',help='R5: open the original Panel Settings (Enter Edit Mode) once the disposable panel is shown')
p.add_argument('--instances',type=int,choices=(1,2),help='Disposable following native panel: one widget, or two for comparison')
p.add_argument('--output',help='Output description (Hyprland desc:, e.g. "MAG 274Q X24"); connector names are not accepted')
p.add_argument('--native-policy',action='store_true',help='Explicit surface-policy test: native NormalPanel/WindowsGoBelow; may reserve workspace area on the selected output')
operation=p.add_mutually_exclusive_group()
operation.add_argument('--follow-skin',action='store_true',help='Explicitly register this isolated preview with the BWM skin-change hook')
operation.add_argument('--export-as',help='Copy --profile and its snapshot history to a named persistent XDG state profile; do not start a panel')
operation.add_argument('--recover-snapshot',help='Recover --profile from this explicit snapshot ID, even with a broken head/generation; archive the old head and exit offscreen')
a=p.parse_args()
saved_profile=bool(a.profile or a.selected_profile)
a.binary=a.binary.expanduser().resolve()
if not a.binary.is_file() or not os.access(a.binary,os.X_OK):
    source_root=Path(__file__).resolve().parent
    build_root=source_root.parents[1]/'build/bwm-plasma-host'
    p.error(f'No existe un auxiliar ejecutable en {a.binary}. Compílalo con: '
            f'cmake -S {source_root} -B {build_root} && cmake --build {build_root} -j4. '
            f'Después usa --binary {build_root}/bwm-plasma-host')
if a.builtin and not re.fullmatch(r'[A-Za-z0-9_.-]+',a.builtin):p.error('Invalid native widget ID')
if a.desktop_actions and (not a.follow_skin or a.export_as):p.error('--desktop-actions requires --follow-skin preview, not profile export')
if a.task_actions and (not a.follow_skin or a.export_as):p.error('--task-actions requires --follow-skin preview, not profile export')
if a.all_desktops and (not a.task_actions or saved_profile):p.error('--all-desktops requires --task-actions in a disposable preview, not --profile/--selected-profile')
if a.session_appearance and (not a.follow_skin or saved_profile):p.error('--session-appearance requires a disposable --follow-skin preview, not --profile/--selected-profile')
if a.task_thumbnails and (not a.task_actions or saved_profile):p.error('--task-thumbnails requires --task-actions in a disposable preview, not --profile/--selected-profile')
if a.task_actions and not (a.all_desktops or a.native_desktops):p.error('--task-actions requires --all-desktops for this isolated test, or --native-desktops with its already loaded provider; current-desktop filtering otherwise hides windows')
if a.native_desktops and (not a.follow_skin or a.export_as):p.error('--native-desktops requires --follow-skin preview, not profile export')
if a.export_as and not a.profile:p.error('--export-as requires --profile')
if a.recover_snapshot and (not a.profile or not re.fullmatch(r'[a-f0-9]{32}',a.recover_snapshot)):
    p.error('--recover-snapshot requires --profile and its explicit 32-character lowercase snapshot ID')
if a.recover_snapshot and (a.native_panel or a.layer_panel):p.error('--recover-snapshot does not accept panel display options')
if a.edit_mode and (saved_profile or not a.native_panel or not a.follow_skin):p.error('--edit-mode requires a disposable --native-panel --follow-skin preview')
if a.instances is not None and (saved_profile or not a.native_panel or not a.follow_skin):p.error('--instances requires a disposable --native-panel --follow-skin preview')
if a.profile and (not (a.follow_skin or a.export_as or a.recover_snapshot) or a.output):
    p.error('--profile requires --follow-skin, --export-as or --recover-snapshot and uses its persisted output bindings instead of --output')
if a.selected_profile and (not a.follow_skin or a.output):p.error('--selected-profile requires --follow-skin and uses the saved output bindings')
if a.follow_skin and not saved_profile and not (a.native_panel and a.layer_panel and a.output):
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
if a.builtin:plugin=a.builtin
with tempfile.TemporaryDirectory(prefix='bwm-r4-preview-') as tmp:
    root=Path(tmp)
    env=dict(os.environ,XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),
             XDG_CACHE_HOME=str(root/'cache'),XDG_RUNTIME_DIR=str(root/'runtime'),
             XDG_CONFIG_DIRS=str(root/'defaults'),XDG_DATA_DIRS='/usr/local/share:/usr/share',
             DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
    env.pop('BWM_R4_NATIVE_PANEL_POLICY',None);env.pop('BWM_R5_EDIT_MODE',None)
    if a.edit_mode:env['BWM_R5_EDIT_MODE']='1'
    env.pop('BWM_R4_DESKTOP_ACTIONS',None);env.pop('BWM_R4_DESKTOP_RUNTIME',None);env.pop('BWM_R4_DESKTOP_CONFIG',None)
    for key in ('BWM_R4_TASK_ACTIONS','BWM_R4_TASK_RUNTIME','BWM_R4_TASK_CONFIG','BWM_R4_PREVIEW_INSTANCES','BWM_R4_LAUNCH_CONTEXT','BWM_R4_GUARD_RUNTIME','BWM_R4_NATIVE_DESKTOPS','BWM_R4_TASK_ALL_DESKTOPS','BWM_R4_TASK_THUMBNAILS'):env.pop(key,None)
    if a.instances is not None or (a.task_actions and a.native_panel):
        env['BWM_R4_PREVIEW_INSTANCES']=str(a.instances if a.instances is not None else 1)
    if a.task_thumbnails:env['BWM_R4_TASK_THUMBNAILS']='1'
    if a.all_desktops:env['BWM_R4_TASK_ALL_DESKTOPS']='1'
    if a.desktop_actions or a.task_actions or a.native_desktops:
        if initial_skin!='plasma':p.error('Native actions require Breeze active')
        actual_runtime=session.private_directory(Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')))
        probe=subprocess.run(['hyprctl','-j','monitors'],capture_output=True,text=True,timeout=2)
        if probe.returncode:p.error('Native actions require accessible compositor IPC')
        if a.desktop_actions:
            env['BWM_R4_DESKTOP_ACTIONS']='1'
            env['BWM_R4_DESKTOP_RUNTIME']=str(actual_runtime)
            env['BWM_R4_DESKTOP_CONFIG']=str(Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')).resolve())
        if a.task_actions:
            launch_spec=importlib.util.spec_from_file_location('bwm_native_launch',Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native_launch.py')
            launch=importlib.util.module_from_spec(launch_spec);launch_spec.loader.exec_module(launch)
            env[launch.VARIABLE]=launch.capture(os.environ)
            env['BWM_R4_TASK_ACTIONS']='1';env['BWM_R4_TASK_RUNTIME']=str(actual_runtime)
            env['BWM_R4_TASK_CONFIG']=str(Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')).resolve())
        if a.native_desktops:
            try:
                reply=subprocess.run(['hyprctl','-j','bwm-plasma-desktops'],capture_output=True,text=True,timeout=2,check=True)
                provider=json.loads(reply.stdout)
                compatible=isinstance(provider,dict) and all(type(provider.get(k)) is int and provider[k]==v for k,v in
                    (('version',1),('protocolVersion',4),('barrierProtocolVersion',2),('serverArbitrationVersion',1),('providerLifecycleVersion',1),('countMirrorVersion',1),('activationReadbackVersion',1))) and all(provider.get(k) is True for k in
                    ('enabled','providerAvailable','perClientBarrierSupported','configuredCountAvailable')) and provider.get('arbitrationState')=='active' and provider.get('providerRestartRequired') is False and provider.get('observerStartup')=='deferred-event-loop'
            except (OSError,ValueError,subprocess.SubprocessError):compatible=False
            if not compatible:p.error('El proveedor de escritorios debe estar cargado, habilitado y ofrecer la barrera por conexión v2 con asociación de global, arbitraje de servidor v1 activo y ciclo de vida v1 con inicio diferido y contador común sincronizado y activación absoluta con lectura posterior v1. Revisa src/bwm-plasma-desktops/README.md; no cargar/descargar plugins en caliente.')
            env['BWM_R4_NATIVE_DESKTOPS']='1'
        env['QT_QPA_PLATFORM']='wayland'
    if a.native_policy:env['BWM_R4_NATIVE_PANEL_POLICY']='1'
    if a.output: env['BWM_R4_OUTPUT']=a.output
    for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(mode=0o700)
    # A disposable host must never spawn applications itself: they would inherit
    # its temporary XDG roots and private D-Bus. KDE's own KIOSK denies its
    # in-process launches; --task-actions routes them through the helper.
    host_policy_spec=importlib.util.spec_from_file_location('bwm_host_launch_policy',Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native_launch.py')
    host_policy=importlib.util.module_from_spec(host_policy_spec);host_policy_spec.loader.exec_module(host_policy)
    host_policy.write_host_policy(root/'defaults')
    if a.task_actions:
        # Places shown by KDE's task menu for file managers come from the caller's
        # own user-places.xbel (read-only snapshot); launches leave via the helper.
        host_policy.snapshot_places(Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share')),root/'data')
    if a.session_appearance:
        appearance_env=dict(env,BWM_R4_APPEARANCE_CONFIG_DIRS=os.environ.get('XDG_CONFIG_DIRS','/etc/xdg'))
        try:
            appearance=subprocess.run([str(a.binary),'--stage-preview-appearance',str(actual_config.parent.parent.resolve())],
                env=appearance_env,capture_output=True,text=True,timeout=5)
        except (OSError,subprocess.SubprocessError) as error:p.error(f'No se pudo preparar el aspecto del preview: {error}')
        if appearance.returncode:p.error(appearance.stderr.strip())
        # Let the native KDE platform theme create its icon engine and palette.
        # QIcon::setThemeName would bypass that engine. D-Bus remains isolated.
        env['QT_QPA_PLATFORMTHEME']='kde'
    # This explicit interactive command preserves access to the selected Wayland display,
    # while config/data/cache/runtime and session D-Bus stay disposable. It is not used by
    # the automated offscreen tests or invoked automatically in the user's session.
    if env.get('WAYLAND_DISPLAY') and not env['WAYLAND_DISPLAY'].startswith('/'):
        actualRuntime=os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
        env['WAYLAND_DISPLAY']=str(Path(actualRuntime)/env['WAYLAND_DISPLAY'])
    packageRoot=root/'data/plasma/plasmoids';packageRoot.mkdir(parents=True)
    if a.package:
        subprocess.run(['kpackagetool6','--type','Plasma/Applet','--packageroot',str(packageRoot),'--install',str(a.package)],env=env,check=True)
    if not a.package or a.session_appearance:
        # Lookup installed packages in the caller's XDG data home; all new writes,
        # caches, runtime and D-Bus remain in this wrapper's disposable roots.
        original_data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
        env['XDG_DATA_DIRS']=str(original_data)+os.pathsep+os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
    if a.profile:
        if a.recover_snapshot:
            # This operation never connects to the compositor or registers a
            # preview. Do not preflight --profile-info: the current head may be bad.
            for key in ('DISPLAY','WAYLAND_DISPLAY','HYPRLAND_INSTANCE_SIGNATURE'):env.pop(key,None)
            env.update(QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software')
            try:
                recovered=subprocess.run([str(a.binary),'--recover-profile',str(a.profile.expanduser().absolute()/'snapshots'/a.recover_snapshot)],
                    env=env,capture_output=True,text=True,timeout=25)
            except (OSError,subprocess.SubprocessError) as error:p.error(f'No se pudo recuperar el perfil: {error}')
            if recovered.returncode:p.error(recovered.stderr.strip())
            print(recovered.stdout,end='');raise SystemExit(0)
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
    if a.selected_profile:mode='--serve-selected-profile'
    try:
        arguments=[str(a.binary),mode] if a.selected_profile else [str(a.binary),mode,str(a.profile.resolve()) if a.profile else plugin]
        child=subprocess.Popen(arguments,env=env)
    except OSError as error:
        p.error(f'No se pudo ejecutar el auxiliar {a.binary}: {error}')
    try:
        if a.follow_skin:
            wait_initial_ack(control,child)
            session.register(control,child.pid,token,reports_exit=True)
            session.command({'controlDirectory':str(control),'token':token},'skin',initial_skin)
            if a.task_actions:
                tasks=wait_task_source(session,{'controlDirectory':str(control),'token':token},child,require_thumbnails=a.task_thumbnails)
                print(f"Tareas R4 conectadas: {tasks['windowCount']} ventanas; filas visibles: {tasks['visibleWindowRows']}; lanzadores: {tasks['launcherRows']}.",flush=True)
                if a.task_thumbnails:print('Miniaturas R4: protocolos de captura por ventana conectados; primeros fotogramas pendientes del hover.',flush=True)
            print('Prueba R4 registrada: sigue Breeze/Retro/default. Ctrl+C detiene sólo el auxiliar.',flush=True)
        status=child.wait()
    except KeyboardInterrupt:
        stop_timeout=5
        if a.follow_skin:
            try:session.command({'controlDirectory':str(control),'token':token},'stop')
            except BlockingIOError:
                # A session exit can already be waiting for the host to save.
                # Let it finish instead of terminating the host on Ctrl+C.
                stop_timeout=8
            except (OSError,ValueError,TimeoutError):child.terminate()
        else:child.terminate()
        try: child.wait(timeout=stop_timeout)
        except subprocess.TimeoutExpired: child.kill();child.wait()
        status=130
    except (OSError,ValueError,TimeoutError) as error:
        print(f'No se pudo registrar la prueba R4: {error}',flush=True);child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        status=1
    finally:
        if a.follow_skin:
            try:
                if child.returncode is not None and (control/'ack.json').exists():
                    session.record_exit(control,token,child.returncode)
            finally:
                session.unregister(token)
                session.drain(control)
    raise SystemExit(status)

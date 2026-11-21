#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BWM contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare native KWindowShadow tiles in fresh Hyprland and KWin compositors.

Only the child Hyprland loads the candidate, before clients. Both compositors get
private XDG roots/buses and the same native KDE client. No daily module or shell is
replaced. Captures contain only a controlled gray background and the test rectangle.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import tempfile
import time
import shutil

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r6_nested',Path(__file__).with_name('check-r6-nested.py'))
nested=importlib.util.module_from_spec(spec);spec.loader.exec_module(nested)
hypr=nested.hypr

def stop(p):
    if p is None or p.poll() is not None:return
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:p.wait(5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(5)

class _Done(Exception):
    pass

def wait(predicate,message,timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.1)
    raise TimeoutError(message)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--binary',type=Path,default=ROOT/'build/bwm-plasma-host/test-r6-native')
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--scales',default='1,1.25,1.5,2')
    p.add_argument('--themes',default='breeze-dark,breeze-light,Sweet')
    p.add_argument('--capture-dir',type=Path)
    p.add_argument('--effects',action='store_true',help='Measure native half-window blur on a private checkerboard')
    p.add_argument('--kind',choices=('tiles','dialog','decorated'),default='tiles',help='Native tiles, the complete original PlasmaQuick::Dialog, or a server-side decorated window (KDecoration shadow)')
    p.add_argument('--helper',type=Path,default=ROOT/'src/bwm-decorator/bwm-decorator',help='bwm-decorator for the decorated kind (Hyprland side)')
    p.add_argument('--trace',action='store_true',help='Retain only this fixture client protocol log beside its captures')
    p.add_argument('--hypr-blur',default='',help='Extra Lua fields for the nested Hyprland decoration.blur table (e.g. "size=8,passes=4")')
    p.add_argument('--blur-pattern',choices=('checker','edge'),default='checker',help='Background behind the blur fixture; edge quadrants measure the blur radius')
    p.add_argument('--user-no-blur',action='store_true',help='Add a user no_blur rule for the decorated window: Hyprland must not blur it even when asked')
    p.add_argument('--backends',default='hyprland,kwin',help='Compositors to run; comparisons need both')
    a=p.parse_args();scales=[float(v) for v in a.scales.split(',')];themes=a.themes.split(',')
    if a.effects and a.kind=='dialog':p.error('The blur fixture uses the tiles or decorated client')
    if a.user_no_blur and (not a.effects or a.kind!='decorated' or a.backends!='hyprland'):p.error('--user-no-blur needs --effects --kind decorated --backends hyprland')
    module=a.module.resolve();binary=a.binary.resolve()
    if not module.is_file() or not binary.is_file():p.error('Build and atomically install the candidate in build/ first')
    if module.parent==ROOT/'config/hypr/plugins':p.error('Use a separate candidate in build/, never the daily module')
    from PIL import Image,ImageChops,ImageStat,ImageFilter
    before=nested.snapshot();instances={v['instance'] for v in json.loads(hypr('instances','-j'))}
    clients=json.loads(hypr('-j','clients'))
    if any(c.get('class')=='aquamarine' for c in clients):p.error('Another nested compositor is open')
    dialogs={c['pid'] for c in clients if c.get('class')=='hyprland-dialog'}
    host=f'BWM-R6-SURFACES-{os.getpid()}';rule=f'bwm-r6-surfaces-{os.getpid()}';created=False;ruled=False
    report={'version':2,'passed':False,'scope':'Native KDE shadows and effects in isolated compositors',
        'clientKind':a.kind,'effectsFixture':a.effects,'opacityProtocol':'wp_alpha_modifier_v1','cases':[]}
    captures=a.capture_dir.resolve() if a.capture_dir else None
    if captures:captures.mkdir(parents=True,exist_ok=True,mode=0o700)
    processes=[]
    try:
      with tempfile.TemporaryDirectory(prefix='bwm-r6-surface-build-') as b:
        build=Path(b);xml='/usr/share/plasma-wayland-protocols/fake-input.xml'
        subprocess.run(['wayland-scanner','client-header',xml,str(build/'fake-input-client.h')],check=True)
        subprocess.run(['wayland-scanner','private-code',xml,str(build/'fake-input-protocol.c')],check=True)
        subprocess.run(['cc','-fPIC','-c',str(build/'fake-input-protocol.c'),'-o',str(build/'protocol.o')],check=True)
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Gui','Qt6DBus','wayland-client'],text=True))
        capture_client=build/'capture'
        subprocess.run(['g++','-std=c++20','-fPIC','-O1','-I'+str(build),str(ROOT/'tests/r5_reference_client.cpp'),str(build/'protocol.o'),'-o',str(capture_client),*flags],check=True)
        hypr('output','create','headless',host);created=True
        hypr('eval','hl.monitor({output='+json.dumps(host)+',mode="2560x1600@60",position="20000x20000",scale=1})')
        monitor=wait(lambda:next((m for m in json.loads(hypr('-j','monitors')) if m['name']==host),None),'Host output missing')
        workspace=monitor['activeWorkspace']['id']
        hypr('eval',f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},workspace="{workspace} silent",no_initial_focus=true}})');ruled=True
        runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
        for theme in themes:
          for scale in scales:
            images={};states={}
            for backend in [v for v in ('hyprland','kwin') if v in a.backends.split(',')]:
              with tempfile.TemporaryDirectory(prefix='bwm-r6-surface-') as d:
                root=Path(d)
                for name in ('config','data','cache','state','runtime','defaults'):(root/name).mkdir(mode=0o700)
                color='BreezeLight' if theme=='breeze-light' else 'BreezeDark'
                (root/'config/kdeglobals').write_text(Path(f'/usr/share/color-schemes/{color}.colors').read_text()+'\n[KDE]\nwidgetStyle=Breeze\n')
                (root/'config/plasmarc').write_text('[Theme]\nname='+theme+'\n')
                if a.kind=='decorated':
                    # Same decoration for both compositors, read from the private kwinrc.
                    # Sweet uses its Aurorae SVG theme (third-party decoration path).
                    aurorae=next((base/'aurorae/themes/Sweet-Dark' for base in [Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share'))),*[Path(v) for v in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')]] if (base/'aurorae/themes/Sweet-Dark').is_dir()),None) if theme=='Sweet' else None
                    if theme=='Sweet' and aurorae is None:raise FileNotFoundError('Aurorae Sweet-Dark is not installed')
                    if aurorae:shutil.copytree(aurorae,root/'data/aurorae/themes/Sweet-Dark')
                    deco='library=org.kde.kwin.aurorae\ntheme=__aurorae__svg__Sweet-Dark\n' if aurorae else 'library=org.kde.breeze\ntheme=Breeze\n'
                    # Two desktops: KDecoration hides «on all desktops» with only one, BWM has several.
                    (root/'config/kwinrc').write_text('[Desktops]\nNumber=2\nRows=1\n\n[Windows]\nPlacement=Centered\n\n[org.kde.kdecoration2]\n'+deco)
                theme_roots=[Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share'))),*[Path(v) for v in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')]]
                source=next((base/'plasma/desktoptheme'/theme for base in theme_roots if (base/'plasma/desktoptheme'/theme).is_dir()),None)
                if source is None:raise FileNotFoundError('Installed Plasma style is missing: '+theme)
                shutil.copytree(source,root/'data/plasma/desktoptheme'/theme)
                env={k:v for k,v in os.environ.items() if not k.startswith(('DBUS_','QT_','QSG_','BWM_')) and k not in ('DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE')}
                env.update(XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),XDG_STATE_HOME=str(root/'state'),XDG_CONFIG_DIRS=str(root/'defaults'),
                    XDG_RUNTIME_DIR=str(root/'runtime'),DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'no-system-bus'),BWM_R6_TEST_ROOT=str(root),
                    QSG_RHI_BACKEND='opengl',LANG='en_US.UTF-8',LANGUAGE='en')
                if a.effects:env['BWM_R6_EFFECTS']='1'
                if a.effects:env['BWM_R6_EFFECTS_PATTERN']=a.blur_pattern
                env['BWM_R6_CLIENT_KIND']=a.kind
                vendor=Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json')
                if vendor.is_file():env.update(GBM_BACKEND='nvidia-drm',__EGL_VENDOR_LIBRARY_FILENAMES=str(vendor))
                config=root/'bus.conf';config.write_text('<busconfig><type>session</type><listen>unix:path='+str(root/'runtime/bus')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
                bus=subprocess.Popen(['dbus-daemon','--config-file='+str(config),'--nofork','--print-address=1'],env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,start_new_session=True)
                processes.append(bus);env['DBUS_SESSION_BUS_ADDRESS']=bus.stdout.readline().strip()
                def launch(argv,name,child_env=None):
                    with (root/(name+'.log')).open('w') as log:child=subprocess.Popen([str(v) for v in argv],env=child_env or env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                    processes.append(child);return child
                def run(argv,timeout=10):
                    r=subprocess.run([str(v) for v in argv],env=env,capture_output=True,text=True,timeout=timeout)
                    if r.returncode:raise RuntimeError(' '.join(str(v) for v in argv[:2])+': '+r.stdout[-1000:]+r.stderr[-1000:])
                    return r.stdout
                try:
                  width,height=round(1280*scale),round(800*scale)
                  if backend=='hyprland':
                    env.update(XDG_RUNTIME_DIR=str(runtime))
                    if a.kind=='decorated':
                        helper_env=dict(env,QT_QPA_PLATFORM='offscreen');env['BWM_DECORATOR_SOCKET']=str(root/'deco.sock')
                        launch([a.helper.resolve(),'--socket',root/'deco.sock'],'helper',helper_env)
                        wait(lambda:(root/'deco.sock').exists(),'Disposable decorator socket missing')
                    config=root/'hyprland.lua';config.write_text(f'hl.monitor({{output="",mode="{width}x{height}",position="0x0",scale={scale}}})\n'+
                      ('hl.window_rule({name="fixture",match={class="^bwm-r6-decorated$"},float=true,center=true,no_shadow=false})\n' if a.kind=='decorated' else '')+
                      ('hl.window_rule({name="user-no-blur",match={class="^bwm-r6-decorated$"},no_blur=true})\n' if a.user_no_blur else '')+
                      'hl.config({general={border_size=0},misc={disable_hyprland_logo=true,disable_splash_rendering=true},animations={enabled=false},xwayland={enabled=false},input={follow_mouse=0},decoration={shadow={enabled=false},blur={enabled='+('true' if a.effects else 'false')+(','+a.hypr_blur if a.hypr_blur else '')+'}}})\n')
                    compositor=launch(['Hyprland','--config',config],'compositor')
                    instance=wait(lambda:next((i for i in json.loads(hypr('instances','-j')) if i['pid']==compositor.pid),None),'Nested compositor did not start')
                    signature=instance['instance'];env['WAYLAND_DISPLAY']=str(runtime/instance['wl_socket'])
                    outputs=wait(lambda:json.loads(hypr('-j','monitors',instance=signature)),'Nested output missing')
                    if abs(outputs[0]['scale']-scale)>.02:raise AssertionError('Wrong Hyprland scale')
                    if hypr('plugin','load',str(module),instance=signature,timeout=45).strip()!='ok':raise RuntimeError('Candidate load failed')
                    hypr('eval','hl.config({plugin={breezebars={enabled=true}}})',instance=signature)
                    output=outputs[0]['name']
                    hypr('dispatch','hl.dsp.cursor.move({x=2,y=2})',instance=signature)
                  else:
                    env.pop('WAYLAND_DISPLAY',None)
                    # Plasma runs KWin with the KDE platform theme: title font from kdeglobals
                    # (Noto Sans 10), not the generic Qt fallback.
                    env.update(QT_QPA_PLATFORMTHEME='kde',KWIN_COMPOSE='O2',KWIN_SCREENSHOT_NO_PERMISSION_CHECKS='1',XDG_CURRENT_DESKTOP='KDE',XDG_SESSION_TYPE='wayland')
                    compositor=launch(['kwin_wayland','--virtual','--no-kactivities','--no-global-shortcuts','--width','1280','--height','800','--scale',str(scale),'--socket','r6-reference'],'compositor')
                    wait(lambda:(root/'runtime/r6-reference').exists(),'KWin did not start')
                    env['WAYLAND_DISPLAY']=str(root/'runtime/r6-reference')
                    run(['kscreen-doctor',f'output.Virtual-0.scale.{scale}'])
                    env['BWM_R5_REFERENCE_MARKER']=str(root/'reference.json')
                    (root/'reference.json').write_text(json.dumps({'pid':compositor.pid,'runtime':env['XDG_RUNTIME_DIR'],'display':env['WAYLAND_DISPLAY']}))
                  env.update(QT_QPA_PLATFORM='wayland',QT_QPA_PLATFORMTHEME='kde',BWM_R6_WAYLAND_DISPLAY=env['WAYLAND_DISPLAY'],BWM_R6_COMPOSITOR_PID=str(compositor.pid))
                  fixture_env=dict(env,WAYLAND_DEBUG='client') if a.trace else env
                  fixture=launch([binary],'client',fixture_env)
                  sequence=0;result={};backend_states={}
                  commands=[('plain',{'shadow':False}),('shadow',{'shadow':True}),('recreated',{'recreate':True}),
                    ('small',{'size':[17,11]}),('tiny',{'size':[4,20]}),('docked',{'size':[180,120],'borders':11}),
                    ('unset',{'shadow':False,'borders':15}),('hidden',{'visible':False}),('restored',{'visible':True,'shadow':True}),
                    ('opacity',{'opacity':.5}),('opacity-restored',{'opacity':1.0})]
                  if a.effects:commands=[('plain',{'shadow':False,'blur':False}),('blur',{'blur':True}),('blur-removed',{'blur':False})]
                  elif a.kind=='decorated':commands=[('active',{}),('inactive',{'second':True}),('reactivated',{'second':False})]
                  elif a.kind=='dialog':commands=[('normal',{}),('recreated',{'recreate':True}),('small',{'size':[17,11]}),('hidden',{'visible':False}),('restored',{'size':[180,120],'visible':True}),('opacity',{'opacity':.5}),('opacity-restored',{'opacity':1.0})]
                  for name,command in commands:
                    sequence+=1
                    target=root/'command.json';tmp=root/'next.json';tmp.write_text(json.dumps(dict(command,sequence=sequence)));tmp.replace(target)
                    def ready():
                        if fixture.poll() is not None:raise RuntimeError('Native fixture exited: '+(root/'client.log').read_text()[-2000:])
                        try:
                            state=json.loads((root/'state.json').read_text())
                            return state if state.get('sequence')==sequence else None
                        except (OSError,ValueError):return None
                    state=wait(ready,'Native fixture did not acknowledge command');backend_states[name]=state
                    if not state['created']:raise AssertionError('Native KWindowShadow creation failed')
                    if state['theme']!=theme:raise AssertionError('Native Plasma style fell back: '+str(state))
                    if abs(state['dpr']-scale)>.02:raise AssertionError('Wrong client DPR: '+str(state))
                    if backend=='hyprland':
                        state['protocol']=json.loads(hypr('-j','breezebars-shadows',instance=signature))
                        if a.kind=='decorated':
                            def decorated():
                                csd=json.loads(hypr('-j','breezebars-csd',instance=signature))
                                own=[w for w in csd['windows'] if w['class']=='bwm-r6-decorated']
                                expected=2 if command.get('second') else 1
                                return own if len(own)==expected and all(w['kind']=='kde' for w in own) else None
                            state['decoration']=wait(decorated,'Native KDecoration never arrived')
                    # The first decorated frame can be followed by a settled one.
                    time.sleep(1.0 if a.kind=='decorated' and sequence==1 else .25);path=root/(name+'.png')
                    if backend=='hyprland':run(['grim','-o',output,path])
                    else:run([capture_client,'capture',path,'workspace'])
                    if captures:shutil.copy2(path,captures/f'{theme}-{scale}-{backend}-{name}.png')
                    with Image.open(path) as im:
                        # Exclude compositor notifications/cursor, not any shadow:
                        # a 128-logical-pixel margin encloses the complete native tiles.
                        region=tuple(round(v*scale) for v in (192,92,628,468))
                        rgb=im.convert('RGB')
                        if a.kind=='decorated' and a.effects:
                            # Translucent #80707070 over the checkerboard. Qt clears with the
                            # straight colour and compositors read it premultiplied: 0x70 + bg/2,
                            # 0x90/0xd0 inside the window, 0x40/0xc0 outside. Found once without
                            # blur; the window does not move.
                            if name=='plain':
                                grey=rgb.convert('L')
                                mask=grey.point(lambda v:1 if abs(v-0x90)<=3 or abs(v-0xd0)<=3 else 0)
                                # Rows and columns crossing the window (360x240 logical); stray
                                # pixels with those values elsewhere never add up to that.
                                data=mask.get_flattened_data();w,h=mask.size;need=round(200*scale)
                                rows=[y for y in range(h) if sum(data[y*w:(y+1)*w])>=need]
                                cols=[x for x in range(w) if sum(data[x::w])>=round(150*scale)]
                                if not rows or not cols:raise AssertionError('Translucent decorated fixture not found')
                                effect_box=(cols[0]-2,rows[0]-2,cols[-1]+3,rows[-1]+3)
                            m=round(128*scale);box=effect_box
                            region=(box[0]-m,box[1]-m,box[2]+m,box[3]+m);state.setdefault('contentBox',list(box))
                        elif a.kind=='decorated':
                            # Placement may differ between compositors: align on the
                            # fixture content colour, then keep 128 logical px around it.
                            mask=ImageChops.difference(rgb,Image.new('RGB',rgb.size,(0x2a,0x6f,0x97))).convert('L').point(lambda v:255 if v<=3 else 0)
                            # Erode first: a few cursor pixels can share the fixture colour.
                            box=mask.filter(ImageFilter.MinFilter(5)).getbbox()
                            box=box and (box[0]-2,box[1]-2,box[2]+2,box[3]+2)
                            if not box:raise AssertionError('Decorated fixture content not found in '+name)
                            m=round(128*scale)
                            region=(0,0,rgb.width,rgb.height) if command.get('maximized') else (box[0]-m,box[1]-m,box[2]+m,box[3]+m)
                            state.setdefault('contentBox',list(box))
                        result[name]=rgb.crop(region)
                  images[backend]=result;states[backend]=backend_states
                  sequence+=1;(root/'command.json').write_text(json.dumps({'sequence':sequence,'quit':True}));fixture.wait(5)
                  if fixture.returncode:raise AssertionError('Fixture failed on shutdown')
                  if backend=='hyprland':
                    def released():
                        state=json.loads(hypr('-j','breezebars-shadows',instance=signature))
                        return state if not any(state[key] for key in ('surfaces','objects','applied','queued')) else None
                    empty=wait(released,'Shadow resources survived the native client')
                    report.setdefault('resourceCleanup',[]).append(dict(theme=theme,scale=scale,**empty))
                    if a.kind=='decorated':
                        stop(compositor)
                        if compositor.returncode not in (0,-signal.SIGTERM):raise AssertionError('Compositor failed at shutdown: '+str(compositor.returncode))
                        raise _Done()
                    # A second client remains mapped with a live shadow while the
                    # compositor exits. Plugin teardown must retire every resource
                    # before its callbacks/code are unloaded.
                    (root/'command.json').write_text(json.dumps({'sequence':1,'shadow':True}))
                    (root/'state.json').unlink(missing_ok=True)
                    live=launch([binary],'live-shutdown-client')
                    wait(lambda:(root/'state.json').exists() or live.poll() is not None,'Live shutdown client did not start')
                    if live.poll() is not None:raise AssertionError('Live shutdown client failed')
                    before_exit=json.loads(hypr('-j','breezebars-shadows',instance=signature))
                    if before_exit['applied']<1:raise AssertionError('No live shadow at compositor teardown')
                    stop(compositor)
                    if compositor.returncode not in (0,-signal.SIGTERM):raise AssertionError('Compositor failed at live-shadow shutdown: '+str(compositor.returncode))
                    report.setdefault('liveResourceShutdown',[]).append({'theme':theme,'scale':scale,'passed':True,'resourcesBeforeExit':before_exit})
                except _Done:
                  pass
                except Exception:
                  report['failureLogs']={name:(root/(name+'.log')).read_text(errors='replace')[-1800:] for name in ('compositor','client') if (root/(name+'.log')).exists()}
                  for crash in (root/'cache/hyprland').glob('hyprlandCrashReport*'):
                    trace=crash.read_text(errors='replace');start=trace.find('Backtrace');report['failureTrace']=trace[start:start+2500] if start>=0 else 'No backtrace'
                  raise
                finally:
                  for child in reversed(processes):stop(child)
                  if a.trace and captures and (root/'client.log').exists():shutil.copy2(root/'client.log',captures/f'{theme}-{scale}-{backend}-client.log')
            # Decorated windows sit at different places in each compositor over a fixed pattern:
            # their blur semantics are checked per backend below, not pixel by pixel.
            for name in (name for name,_ in commands if name!='plain' and len(images)==2 and not (a.kind=='decorated' and a.effects)):
              ref,own=images['kwin'],images['hyprland']
              original,current=ref[name],own[name]
              if original.size!=current.size:raise AssertionError(f'Output sizes differ: {original.size} / {current.size}')
              delta=ImageChops.difference(current,original)
              entry={'theme':theme,'scale':scale,'case':name,'sameSize':True,'maxChannelError':max(v[1] for v in delta.getextrema()),
                'meanChannelError':ImageStat.Stat(delta).mean,'differentPixels':sum(any(v) for v in delta.get_flattened_data()),
                'differenceBounds':delta.getbbox(),'kwin':states['kwin'][name],'hyprland':states['hyprland'][name]}
              report['cases'].append(entry);print(json.dumps({k:v for k,v in entry.items() if k not in ('kwin','hyprland')}),flush=True)
            if a.kind=='decorated' and not a.effects and len(images)==2:
              # Shadow presence must match KWin: some Aurorae themes ship none.
              counts={}
              for backend in images:
                ring=images[backend]['active'].copy();w,h=ring.size;m=round(128*scale)
                ring.paste(Image.new('RGB',(w-2*m+2*round(40*scale),h-2*m+2*round(40*scale)),(0x80,0x80,0x80)),(m-round(40*scale),m-round(40*scale)))
                counts[backend]=sum(any(abs(c-0x80)>2 for c in px) for px in ring.get_flattened_data())
              if (counts['hyprland']>=100)!=(counts['kwin']>=100):raise AssertionError(f'Decoration shadow presence differs from KWin: {counts}')
            for backend in images:
              if a.kind=='decorated' and not a.effects:
                own=images[backend];ring=own['active'].copy();w,h=ring.size;m=round(128*scale)
                inner=Image.new('RGB',(w-2*m+2*round(40*scale),h-2*m+2*round(40*scale)),(0x80,0x80,0x80))
                ring.paste(inner,(m-round(40*scale),m-round(40*scale)))
                shadow=sum(any(abs(c-0x80)>2 for c in px) for px in ring.get_flattened_data())
                # The first frame must already be the settled one, as in KWin: a decoration
                # created active once kept an Aurorae shadow sized without its borders.
                moved=sum(max(px)>2 for px in ImageChops.difference(own['reactivated'],own['active']).get_flattened_data())
                if moved:raise AssertionError(f'{backend}: reactivation changed the decorated window ({moved} pixels)')
                if ImageChops.difference(own['inactive'],own['active']).getbbox() is None:raise AssertionError(backend+': focus change did not repaint the decoration')
                report.setdefault('decorationShadows',[]).append({'backend':backend,'theme':theme,'scale':scale,'shadowPixelsOutsideFrame':shadow,'reactivationPixelsAboveTwo':moved})
                continue
              if a.kind=='dialog':
                own=images[backend]
                if ImageChops.difference(own['opacity'],own['normal']).getbbox() is None:raise AssertionError(backend+': native opacity was not applied')
                for name in ('recreated','restored','opacity-restored'):
                  if ImageChops.difference(own[name],own['normal']).getbbox():raise AssertionError(backend+': native dialog lifecycle changed its image: '+name)
                report.setdefault('nativeDialogs',[]).append({'backend':backend,'theme':theme,'scale':scale,'lifecycleExact':True})
                continue
              if a.effects:
                own=images[backend];change=ImageChops.difference(own['blur'],own['plain'])
                # Fixture starts at (320,220); crop starts at (192,92). Only
                # its left half requested blur. Exclude the shared boundary.
                inside=tuple(round(v*scale) for v in (132,132,212,244))
                outside=tuple(round(v*scale) for v in (222,132,304,244))
                if a.kind=='decorated':
                  # Content box in the crop: 128 logical px margin plus the 2 px detection margin
                  m=round(128*scale);w,h=own['plain'].size;half=m+2+(w-2*m-4)//2;e=round(6*scale)
                  inside=(m+2+e,m+2+e,half-e,h-m-2-e);outside=(half+e,m+2+e,w-m-2-e,h-m-2-e)
                affected=sum(any(v) for v in change.crop(inside).get_flattened_data())
                leaked=sum(any(v) for v in change.crop(outside).get_flattened_data())
                if a.user_no_blur:
                  if affected or leaked:raise AssertionError(f'{backend}: a user no_blur rule must win ({affected} inside, {leaked} outside)')
                elif affected<100 or leaked:raise AssertionError(f'{backend}: native blur region failed ({affected} inside, {leaked} outside)')
                if ImageChops.difference(own['blur-removed'],own['plain']).getbbox():raise AssertionError(backend+': blur remnants after disabling')
                report.setdefault('blurRegions',[]).append({'backend':backend,'theme':theme,'scale':scale,'changedPixelsInside':affected,'changedPixelsOutside':leaked,'removalExact':True})
                continue
              own=images[backend];changes=ImageChops.difference(own['shadow'],own['plain']);affected=sum(any(v) for v in changes.get_flattened_data())
              if ImageChops.difference(own['opacity'],own['shadow']).getbbox() is None:raise AssertionError(backend+': native opacity was not applied')
              if ImageChops.difference(own['opacity-restored'],own['shadow']).getbbox():raise AssertionError(backend+': opacity restore changed the shadow')
              if affected<100:raise AssertionError(f'{backend}: no measurable shadow ({affected})')
              if ImageChops.difference(own['unset'],own['plain']).getbbox():raise AssertionError(backend+': shadow remnants after unset')
              if ImageChops.difference(own['recreated'],own['shadow']).getbbox():raise AssertionError(backend+': surface recreation changed the shadow')
              if ImageChops.difference(own['restored'],own['shadow']).getbbox():raise AssertionError(backend+': reopening changed the shadow')
              report.setdefault('profiles',[]).append({'backend':backend,'theme':theme,'scale':scale,'changedPixels':affected,'bounds':changes.getbbox(),
                  'horizontalAlphaProfile':[round(max(changes.getpixel((x,round((280-92)*scale))))/128,6) for x in range(round((270-192)*scale),round((550-192)*scale))]})
        report['passed']=True
        report['gpuParityWithinOneChannelUnit']=all(case['maxChannelError']<=1 for case in report['cases'])
    except Exception as error:report.update(passed=False,error=str(error))
    finally:
        for child in reversed(processes):stop(child)
        if created:hypr('output','remove',host)
        if ruled:hypr('reload');time.sleep(.4)
        for client in json.loads(hypr('-j','clients')):
            if client.get('class')!='hyprland-dialog' or client['pid'] in dialogs:continue
            try:
                args=Path(f'/proc/{client["pid"]}/cmdline').read_bytes().split(b'\0')
                if any(b'An application aquamarine - WAYLAND-1 - aquamarine is not responding.' in arg for arg in args):os.kill(client['pid'],signal.SIGTERM)
            except (FileNotFoundError,ProcessLookupError):pass
        nested.restore_session(before)
        after=nested.snapshot();report['sessionUnchanged']=after==before
        report['sessionDifferences']=[key for key in before if before[key]!=after[key]]
        report['cleanupVerified']=all(child.poll() is not None for child in processes) and {i['instance'] for i in json.loads(hypr('instances','-j'))}<=instances
        report['configErrors']=hypr('configerrors').strip()
        report['passed']=report['passed'] and report['sessionUnchanged'] and report['cleanupVerified'] and not report['configErrors']
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:report.get(k) for k in ('passed','error','sessionUnchanged','cleanupVerified')}),flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())

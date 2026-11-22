#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BWM contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Sample actual output frames from private KWin 6.7.5 and Hyprland using Breeze's animations.

Only a controlled solid rectangle and background are captured. An optional candidate
module is loaded before clients in the child only. Daily modules are never replaced.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
ANIMATIONS = ROOT / 'config/hypr/skins/plasma/hypr/animations.lua'
spec = importlib.util.spec_from_file_location('r7_nested', Path(__file__).with_name('check-r6-nested.py'))
nested = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nested)
hypr = nested.hypr


def stop(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(4)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(4)


def wait(predicate, description, timeout=20):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        value = predicate()
        if value:
            return value
        time.sleep(.025)
    raise TimeoutError(description)


def build_client(destination):
    xml = ROOT / 'build/r6-upstream/hyprland-source/protocols/wlr-screencopy-unstable-v1.xml'
    if not xml.is_file():
        raise FileNotFoundError('Provide the reviewed Hyprland 0.56.2 source in build/r6-upstream/hyprland-source')
    subprocess.run(['wayland-scanner', 'client-header', xml, destination / 'r7-screencopy-client.h'], check=True)
    subprocess.run(['wayland-scanner', 'private-code', xml, destination / 'screencopy.c'], check=True)
    subprocess.run(['cc', '-c', '-fPIC', destination / 'screencopy.c', '-o', destination / 'screencopy.o'], check=True)
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Gui', 'Qt6Quick', 'Qt6DBus', 'wayland-client'], text=True))
    binary = destination / 'r7-client'
    subprocess.run(['g++', '-std=c++20', '-O2', '-fPIC', '-I'+str(destination), ROOT / 'tests/r7_animation_client.cpp',
                    destination / 'screencopy.o', '-o', binary, '-lLayerShellQtInterface', *flags], check=True)
    return binary


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fit_cubic(samples, duration, incoming=True):
    """Fit duration and phase separately; never disguise latency as a new easing.

    This is a diagnostic estimate, not proof of exact parity. Full samples and
    capture brackets remain in the report for assessing frame uncertainty.
    """
    if len(samples)<4:
        return None
    def value(t, offset, length):
        progress=max(0,min(1,(t-offset)/length))
        return 1-(1-progress)**3 if incoming else 1-progress**3
    def loss(offset, length):
        return sum((v-value(t,offset,length))**2 for t,v in samples)/len(samples)
    best=(float('inf'),0,duration)
    for offset in range(-40,81,2):
        for length in range(max(1,round(duration*.7)),round(duration*1.3)+1,2):
            candidate=(loss(offset,length),offset,length)
            if candidate<best:
                best=candidate
    _,base_offset,base_length=best
    # Phase and duration covary, particularly for InCubic's nearly flat start.
    # Refine a wide enough diagonal neighbourhood to avoid a coarse-grid minimum.
    for i in range(-16,17):
        for j in range(-48,49):
            offset,length=base_offset+i/4,base_length+j/4
            candidate=(loss(offset,length),offset,length)
            if candidate<best:
                best=candidate
    mse,offset,length=best
    return dict(fittedDurationMs=length,fittedStartAfterEventMs=offset,rmsProgressError=mse**.5,
                maxProgressError=max(abs(v-value(t,offset,length)) for t,v in samples),sampleCount=len(samples))


def summarize(frames, events, factor):
    """Raw samples remain authoritative. Use verified presentation time when available.

    KWin's screenshot API has no presentation timestamp. Bounds describe sampling
    uncertainty; exact source-event latency cannot be inferred from a single sample.
    """
    presentation_clock = all(f['presentationMs']>0 and f['requestedMs']<=f['presentationMs']<=f['receivedMs'] for f in frames)
    times = [f['presentationMs'] if presentation_clock else (f['requestedMs'] + f['receivedMs']) / 2 for f in frames]
    gaps = sorted(b-a for a, b in zip(times, times[1:]))
    result = {'frameCount': len(frames), 'timestampSource': 'screencopy-ready-monotonic' if presentation_clock else 'request-receive-midpoint',
              'medianIntervalMs': gaps[len(gaps)//2],
              'maxIntervalMs': max(gaps), 'maxCaptureBracketMs': max(f['receivedMs']-f['requestedMs'] for f in frames), 'events': []}
    for index, event in enumerate(events):
        end = events[index+1]['monotonicMs'] if index+1 < len(events) else float('inf')
        samples = [dict(f, sinceEventMs=t-event['monotonicMs']) for f, t in zip(frames, times) if event['monotonicMs'] <= t < end]
        entry=dict(event,samples=samples)
        if factor>0 and index in (0,1,2,3,6,7):
            nominal=(250 if event['action'] in ('maximize','restore') else 200)*factor
            selected=[s for s in samples if s['sinceEventMs']<nominal*1.3+80]
            if event['action'] in ('open','close'):
                entry['opacityFit']=fit_cubic([(s['sinceEventMs'],s['opacity']) for s in selected],nominal,event['action']=='open')
                geometry=[(s['sinceEventMs'],max(0,min(1,(s['box'][2]-240)/60))) for s in selected if s['box'] and s['opacity']>.05]
                entry['geometryFit']=fit_cubic(geometry,nominal,event['action']=='open')
                entry['maxScaleOpacityWidthDifferencePx']=max((abs(s['box'][2]-(240+60*s['opacity'])) for s in selected if s['box'] and s['opacity']>.05),default=0)
            else:
                geometry=[(s['sinceEventMs'],((s['box'][2]-300)/500 if event['action']=='maximize' else (800-s['box'][2])/500)) for s in selected if s['box']]
                entry['geometryFit']=fit_cubic(geometry,nominal)
        result['events'].append(entry)
    return result


def compare(cases):
    comparisons=[]
    for factor in sorted({c['factor'] for c in cases}):
        pair={c['backend']:c for c in cases if c['factor']==factor}
        if set(pair)!= {'kwin','hyprland'}:
            continue
        reference, own=pair['kwin'],pair['hyprland']
        # One compositor frame plus one screenshot scheduling frame. This is a
        # declared acceptance tolerance, never an assertion of exact equality.
        tolerance=2*max(reference['medianIntervalMs'],own['medianIntervalMs'])
        rows=[]
        if factor>0:
            for index in (0,1,2,3,6,7):
                a,b=reference['events'][index],own['events'][index]
                for channel in ('opacityFit','geometryFit'):
                    if not a.get(channel) or not b.get(channel):
                        continue
                    difference=b[channel]['fittedDurationMs']-a[channel]['fittedDurationMs']
                    rows.append(dict(eventIndex=index,event=a['action'],channel=channel,
                        kwinDurationMs=a[channel]['fittedDurationMs'],bwmDurationMs=b[channel]['fittedDurationMs'],
                        durationDifferenceMs=difference,withinTwoSamplingIntervals=abs(difference)<=tolerance))
        coupling={backend:max((e.get('maxScaleOpacityWidthDifferencePx',0) for e in case['events']),default=0) for backend,case in pair.items()}
        cancellation={backend:max((s['opacity'] for s in case['events'][5]['samples'] if s['sinceEventMs']<30),default=0) for backend,case in pair.items()}
        zero_intermediate={backend:sum(0<s['opacity']<1 for e in case['events'] for s in e['samples']) for backend,case in pair.items()} if factor==0 else None
        comparisons.append(dict(factor=factor,temporalToleranceMs=tolerance,durationRows=rows,
            scaleOpacityCouplingTolerancePx=3,maxScaleOpacityWidthDifferencePx=coupling,
            withinScaleOpacityCouplingTolerance={backend:value<=3 for backend,value in coupling.items()},
            earlyCloseFirst30msMaxOpacity=cancellation,zeroFactorIntermediateOpacitySamples=zero_intermediate,
            exactParityCertified=False))
    return comparisons


def contact_sheet(cases, destination):
    """Contact sheet of actual frames; timestamps are sampled, never interpolated images."""
    from PIL import Image, ImageDraw, ImageFont
    pair={c['backend']:c for c in cases if c['factor']==1}
    if set(pair)!={'kwin','hyprland'}:
        raise ValueError('Contact sheet requires factor 1 and both compositors')
    try:
        font=ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Regular.ttf',14)
    except (ImportError,OSError):
        font=ImageFont.load_default()
    times=(0,50,100,150,200,250)
    sheet=Image.new('RGB',(1150,660),'#f2f2f2')
    draw=ImageDraw.Draw(sheet)
    draw.text((12,8),'R7 · fotogramas reales · factor 1 · tiempos desde la orden del cliente',fill='#202020',font=font)
    row=0
    for event_index,label in ((0,'Abrir'),(5,'Cierre precoz')):
        for backend in ('kwin','hyprland'):
            case=pair[backend]
            top=40+row*150
            draw.text((8,top+40),label,fill='#202020',font=font)
            draw.text((8,top+61),'KWin' if backend=='kwin' else 'BWM',fill='#202020',font=font)
            event=case['events'][event_index]
            for column,target in enumerate(times):
                sample=min(event['samples'],key=lambda s:abs(s['sinceEventMs']-target))
                source=Path(case['artifacts'])/'frames'/f'{sample["index"]:05d}.png'
                if not source.is_absolute():
                    source=ROOT/source
                with Image.open(source) as frame:
                    sheet.paste(frame.resize((160,120),Image.Resampling.LANCZOS),(140+column*168,top))
                draw.text((142+column*168,top+123),f'{sample["sinceEventMs"]:.0f} ms',fill='#202020',font=font)
            row+=1
    draw.text((12,644),'El muestreo KWin usa el intervalo petición/respuesta; BWM usa la marca de screencopy.',fill='#404040',font=font)
    destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination)


def run_case(backend, factor, binary, host_runtime, artifact_dir, save_frames, module=None, trace_scale=False, disable_cm=False, guard='none',decorated=False,helper=None,early_close_ms=50):
    children = []
    with tempfile.TemporaryDirectory(prefix='bwm-r7-scene-') as folder:
        root = Path(folder)
        for name in ('config', 'data', 'state', 'cache', 'runtime', 'defaults'):
            (root / name).mkdir(mode=0o700)
        env = {k:v for k,v in os.environ.items() if not k.startswith(('DBUS_', 'QT_', 'QSG_', 'BWM_'))
               and k not in ('DISPLAY', 'WAYLAND_SOCKET', 'HYPRLAND_INSTANCE_SIGNATURE')}
        env.update(XDG_CONFIG_HOME=str(root/'config'), XDG_DATA_HOME=str(root/'data'), XDG_STATE_HOME=str(root/'state'),
                   XDG_CACHE_HOME=str(root/'cache'), XDG_RUNTIME_DIR=str(root/'runtime'), XDG_CONFIG_DIRS=str(root/'defaults'),
                   DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'no-system-bus'), BWM_R7_ROOT=str(root),
                   QSG_RHI_BACKEND='opengl', LANG='en_US.UTF-8', LANGUAGE='en')
        vendor = Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json')
        if vendor.is_file():
            env.update(GBM_BACKEND='nvidia-drm', __EGL_VENDOR_LIBRARY_FILENAMES=str(vendor))
        bus_config = root / 'bus.conf'
        bus_config.write_text('<busconfig><type>session</type><listen>unix:path='+str(root/'runtime/bus')+'</listen><auth>EXTERNAL</auth>'
                              '<policy context="default"><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
        bus = subprocess.Popen(['dbus-daemon', '--config-file='+str(bus_config), '--nofork', '--print-address=1'], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
        children.append(bus)
        env['DBUS_SESSION_BUS_ADDRESS'] = bus.stdout.readline().strip()
        (root/'config/kdeglobals').write_text(f'[KDE]\nAnimationDurationFactor={factor}\n')
        (root/'config/kwinrc').write_text('[Windows]\nPlacement=Centered\n[Plugins]\nscaleEnabled=true\nmaximizeEnabled=true\n'
                                         'fadeEnabled=false\nfadingpopupsEnabled=true\nslidingpopupsEnabled=true\nslideEnabled=true\n'
                                         'blurEnabled=false\n[Desktops]\nNumber=2\nRows=1\n'+
                                         ('[org.kde.kdecoration2]\nlibrary=org.kde.breeze\ntheme=Breeze\n' if decorated else ''))
        def launch(argv, name, extra=None):
            with (root/(name+'.log')).open('w') as log:
                child = subprocess.Popen([str(a) for a in argv], env=dict(env, **(extra or {})), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            return child
        try:
            if backend == 'hyprland':
                env['XDG_RUNTIME_DIR'] = str(host_runtime)
                if module:
                    env['BWM_DECORATOR_SOCKET']=str(root/'no-daily-decorator.sock')
                    if decorated:
                        launch([helper,'--socket',env['BWM_DECORATOR_SOCKET']],'decorator',{'QT_QPA_PLATFORM':'offscreen'})
                        wait(lambda:Path(env['BWM_DECORATOR_SOCKET']).exists(),'No private decorator')
                state = root / 'state/bwm/plasma'
                state.mkdir(parents=True)
                (state/'kwin.lua').write_text(f'return {{animationFactor={factor},scaleEnabled='+('false' if guard=='scale-off' else 'true')+'}\n')
                config = root / 'hyprland.lua'
                config.write_text('hl.monitor({output="",mode="800x600@60",position="0x0",scale=1})\n'
                    'hl.window_rule({name="r7-scene",match={class="^bwm-r7-scene$"},float=true,center=true})\n'
                    'hl.config({general={border_size=0},misc={disable_hyprland_logo=true,disable_splash_rendering=true,disable_watchdog_warning=true},'
                    'cursor={invisible=true},xwayland={enabled=false},input={follow_mouse=0},decoration={rounding=0,dim_strength=0.05,shadow={enabled=false},blur={enabled=false}}})\n'
                    +('hl.config({render={cm_enabled=false}})\n' if disable_cm else '')+
                    'dofile('+json.dumps(str(ANIMATIONS))+')\n'+
                    ('hl.window_rule({name="r7-user",match={class="^bwm-r7-scene$"},no_anim=true})\n' if guard=='no-anim' else '')+
                    ('hl.window_rule({name="r7-user",match={class="^bwm-r7-scene$"},animation="popin 50%"})\n' if guard=='custom-style' else ''))
                compositor = launch(['Hyprland', '--config', config], 'compositor')
                instance = wait(lambda: next((i for i in json.loads(hypr('instances','-j')) if i['pid']==compositor.pid),None), 'Hyprland did not start')
                signature = instance['instance']
                wait(lambda: json.loads(hypr('-j','monitors', instance=signature)), 'No nested output')
                errors = hypr('configerrors', instance=signature).strip()
                if errors:
                    raise RuntimeError(errors)
                env['WAYLAND_DISPLAY'] = str(host_runtime / instance['wl_socket'])
                if module:
                    if hypr('plugin','load',str(module),instance=signature,timeout=45).strip()!='ok':
                        raise RuntimeError('Private candidate failed to load')
                    hypr('eval','hl.config({plugin={breezebars={enabled=true}}})',instance=signature)
                    if trace_scale and guard!='scale-off':
                        hypr('eval','hl.plugin.breezebars.scale_config({enabled='+str(factor>0).lower()+',in_scale=.8,trace=true})',instance=signature)
                    if guard=='skin-inactive':
                        hypr('eval','hl.config({plugin={breezebars={enabled=false}}})',instance=signature)
                    errors=hypr('configerrors',instance=signature).strip()
                    if errors:
                        raise RuntimeError(errors)
                hypr('dispatch', 'hl.dsp.cursor.move({x=2,y=2})', instance=signature)
            else:
                env.pop('WAYLAND_DISPLAY', None)
                env.update(QT_QPA_PLATFORMTHEME='kde', KWIN_COMPOSE='O2', KWIN_SCREENSHOT_NO_PERMISSION_CHECKS='1', XDG_CURRENT_DESKTOP='KDE', XDG_SESSION_TYPE='wayland')
                compositor = launch(['kwin_wayland', '--virtual', '--no-kactivities', '--no-global-shortcuts', '--width', '800', '--height', '600', '--socket', 'r7-reference'], 'compositor')
                wait(lambda: (root/'runtime/r7-reference').exists(), 'KWin did not start')
                env['WAYLAND_DISPLAY'] = str(root/'runtime/r7-reference')
            env.update(QT_QPA_PLATFORM='wayland', BWM_R7_DISPLAY=env['WAYLAND_DISPLAY'], BWM_R7_COMPOSITOR_PID=str(compositor.pid), BWM_R7_BACKEND=backend)
            if decorated:
                env['BWM_R7_DECORATED']='1'
            scene = launch([binary, 'scene'], 'scene')
            time.sleep(.35)
            if scene.poll() is not None:
                raise RuntimeError('Scene failed')
            capture = launch([binary, 'capture', backend, '6.7'], 'capture', {'BWM_R7_SAVE_FRAMES':'1'} if save_frames else {})
            wait(lambda: (root/'capture-ready').exists() or capture.poll() is not None, 'No first frame')
            if capture.poll() is not None:
                raise RuntimeError('Capture failed')
            start = time.monotonic()
            schedule = [(.25,'open'),(1.25,'maximize'),(2.25,'restore'),(3.25,'close'),(4.25,'open'),(4.25+early_close_ms/1000,'close'),(4.80,'open'),(5.80,'close')]
            for sequence, (delay, action) in enumerate(schedule):
                if sequence==5 and early_close_ms<16:
                    wait(lambda:any(e['sequence']==sequence for e in read_lines(root/'events.jsonl')),'No client-timed close')
                    continue
                time.sleep(max(0, start+delay-time.monotonic()))
                tmp = root / 'next.json'
                payload=dict(sequence=sequence,action=action)
                if sequence==4 and early_close_ms<16:
                    payload['closeAfterMs']=early_close_ms
                tmp.write_text(json.dumps(payload))
                tmp.replace(root/'command.json')
                if backend=='hyprland' and sequence==4 and guard in ('resize-entry','reload-entry','fullscreen-entry','workspace-entry'):
                    wait(lambda: any(e['sequence']==sequence for e in read_lines(root/'events.jsonl')), 'No guarded entry')
                    time.sleep(.015)
                    if guard=='reload-entry':
                        hypr('reload',instance=signature)
                    else:
                        client=next(c for c in json.loads(hypr('-j','clients',instance=signature)) if c['pid']==scene.pid)
                        operation={'resize-entry':'hl.dsp.window.resize({x=320,y=220,relative=false,window=w})',
                                   'fullscreen-entry':'hl.dsp.window.fullscreen({mode=0,action="set",window=w})',
                                   'workspace-entry':'hl.dsp.window.move({workspace=2,follow=false,window=w})'}[guard]
                        hypr('eval',f'local w=hl.get_window("address:{client["address"]}"); if w and w.pid=={scene.pid} then hl.dispatch({operation}) end',instance=signature)
                if backend=='hyprland' and action in ('maximize','restore'):
                    wait(lambda: (root/'events.jsonl').exists() and any(e['sequence']==sequence for e in read_lines(root/'events.jsonl')), 'No scene action')
                    client = next(c for c in json.loads(hypr('-j','clients',instance=signature)) if c['pid']==scene.pid)
                    x,y,w,h = (0,0,800,600) if action=='maximize' else (250,200,300,200)
                    hypr('eval',f'''local w = hl.get_window("address:{client['address']}")
                        if w and w.pid == {scene.pid} then
                            hl.dispatch(hl.dsp.window.resize({{x={w},y={h},relative=false,window=w}}))
                            hl.dispatch(hl.dsp.window.move({{x={x},y={y},relative=false,window=w}}))
                        end''',instance=signature)
            capture.wait(15)
            if capture.returncode:
                raise RuntimeError('Frame sampler failed')
            frames, events = read_lines(root/'frames.jsonl'), read_lines(root/'events.jsonl')
            if len(events) != len(schedule) or len(frames)<60:
                raise AssertionError('Incomplete event/frame stream')
            result = dict(backend=backend, factor=factor,colorManagement=not disable_cm,guard=guard,decorated=decorated,earlyCloseMs=early_close_ms, **summarize(frames, events, factor))
            result['outputSizes'] = sorted({tuple(f['output']) for f in frames})
            if result['outputSizes'] != [(800,600)]:
                raise AssertionError('Wrong output size')
            if backend=='hyprland':
                result['activeAnimations'] = hypr('animations',instance=signature)
                if module:
                    result['scaleAdapter']=json.loads(hypr('-j','breezebars-scale',instance=signature))
                    if result['scaleAdapter']['tracked']:
                        raise AssertionError('Scale adapter retained a closed window')
                    stats=result['scaleAdapter']
                    if guard in ('no-anim','custom-style','skin-inactive','scale-off') or factor==0:
                        if stats['starts'] or stats['resetOnClose']:
                            raise AssertionError('Scale adapter overrode a disabled/custom animation')
                    elif guard in ('resize-entry','reload-entry','fullscreen-entry','workspace-entry'):
                        if stats['resetOnClose']:
                            raise AssertionError('Scale adapter reset a cancelled or resized entry')
                    elif stats['resetOnClose']!=(0 if early_close_ms<16 and stats['starts']==2 else 1):
                        raise AssertionError('Interrupted-entry close was not handled exactly once')
                    result['candidateSha256']=hashlib.sha256(module.read_bytes()).hexdigest()
            if artifact_dir:
                destination = artifact_dir / f'{backend}-factor-{factor:g}'
                destination.mkdir(parents=True, exist_ok=True)
                for name in ('frames.jsonl','events.jsonl','compositor.log','scene.log','capture.log'):
                    shutil.copy2(root/name,destination/name)
                if save_frames:
                    shutil.copytree(root/'frames',destination/'frames',dirs_exist_ok=True)
                result['artifacts'] = str(destination.relative_to(ROOT)) if destination.is_relative_to(ROOT) else str(destination)
            print(json.dumps({k:result[k] for k in ('backend','factor','frameCount','medianIntervalMs','maxIntervalMs','maxCaptureBracketMs')}),flush=True)
            return result
        except Exception as error:
            logs = {p.name:p.read_text(errors='replace')[-2500:] for p in root.glob('*.log')}
            raise RuntimeError(str(error)+'\n'+json.dumps(logs)) from error
        finally:
            for child in reversed(children):
                stop(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path)
    parser.add_argument('--save-frames',action='store_true')
    parser.add_argument('--contact-sheet',type=Path)
    parser.add_argument('--factors',default='1,2,0')
    parser.add_argument('--backends',default='kwin,hyprland')
    parser.add_argument('--module',type=Path,help='Separate candidate, loaded only in a fresh child before any clients')
    parser.add_argument('--trace-scale',action='store_true',help='Bounded in-memory raw animation diagnostics in the private candidate')
    parser.add_argument('--disable-cm',action='store_true',help='Diagnostic only: disable color management in the fresh child Hyprland')
    parser.add_argument('--guard',choices=('none','no-anim','custom-style','skin-inactive','scale-off','resize-entry','reload-entry','fullscreen-entry','workspace-entry'),default='none')
    parser.add_argument('--decorated',action='store_true',help='Original KDecoration in KWin and the private BWM decorator in Hyprland')
    parser.add_argument('--helper',type=Path,default=ROOT/'src/bwm-decorator/bwm-decorator')
    parser.add_argument('--early-close-ms',type=int,default=50)
    args = parser.parse_args()
    if not 1<=args.early_close_ms<=300:
        parser.error('--early-close-ms must be in 1..300')
    if args.early_close_ms<16 and args.guard!='none':
        parser.error('Client-timed early close is a separate scenario from the guard cases')
    if args.contact_sheet and not (args.artifacts and args.save_frames):
        parser.error('--contact-sheet needs --artifacts and --save-frames')
    module=args.module.resolve() if args.module else None
    if module and (not module.is_file() or module.parent==(ROOT/'config/hypr/plugins').resolve()):
        parser.error('Build/install a separate candidate in build/, never use the daily module path')
    if args.decorated and (not module or not args.helper.is_file()):
        parser.error('--decorated needs a separate candidate and built decorator')
    before = nested.snapshot()
    if any(c.get('class')=='aquamarine' for c in json.loads(hypr('-j','clients'))):
        parser.error('Another nested compositor is already open')
    host = f'BWM-R7-{os.getpid()}'
    rule = f'bwm-r7-{os.getpid()}'
    created = ruled = False
    report = dict(schema=1,completed=False,scope='Controlled '+('KDecoration' if args.decorated else 'frameless')+' window; real output frames in isolated compositors',
                  animationsSha256=hashlib.sha256(ANIMATIONS.read_bytes()).hexdigest(),cases=[])
    try:
        version_env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='')
        report['versions']={'kwin':subprocess.check_output(['kwin_wayland','--version'],env=version_env,stderr=subprocess.DEVNULL,text=True,timeout=10).strip(),
                            'hyprland':subprocess.check_output(['Hyprland','--version'],text=True,timeout=10).strip()}
        with tempfile.TemporaryDirectory(prefix='bwm-r7-build-') as folder:
            binary = build_client(Path(folder))
            hypr('output','create','headless',host)
            created = True
            hypr('eval','hl.monitor({output='+json.dumps(host)+',mode="1000x800@60",position="20000x20000",scale=1})')
            monitor = wait(lambda: next((m for m in json.loads(hypr('-j','monitors')) if m['name']==host),None),'No host output')
            workspace = monitor['activeWorkspace']['id']
            hypr('eval',f'hl.window_rule({{name="{rule}",match={{class="^aquamarine$"}},workspace="{workspace} silent",no_initial_focus=true}})')
            ruled = True
            runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
            artifacts = args.artifacts.resolve() if args.artifacts else None
            for factor in map(float,args.factors.split(',')):
                for backend in args.backends.split(','):
                    if backend not in ('hyprland','kwin'):
                        raise ValueError('Unknown backend')
                    report['cases'].append(run_case(backend,factor,binary,runtime,artifacts,args.save_frames,module,args.trace_scale,args.disable_cm,args.guard,args.decorated,args.helper.resolve(),args.early_close_ms))
            report['completed'] = True
            report['comparisons'] = compare(report['cases'])
            if args.contact_sheet:
                contact_sheet(report['cases'],args.contact_sheet.resolve())
    except Exception as error:
        report['error'] = str(error)
    finally:
        if created:
            hypr('output','remove',host)
        if ruled:
            hypr('reload')
            time.sleep(.3)
        nested.restore_session(before)
        # Focusing the original window can itself warp the pointer. Restore it once
        # more after focus; do not infer an intact session until measuring again.
        current_cursor=json.loads(hypr('-j','cursorpos'))
        if current_cursor!=before['cursor']:
            cursor=before['cursor']
            hypr('dispatch',f'hl.dsp.cursor.move({{x={cursor["x"]},y={cursor["y"]}}})')
        after=nested.snapshot()
        report['sessionUnchanged'] = after==before
        report['sessionChangedAreas'] = [key for key in before if before[key]!=after[key]]
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report.get(k) for k in ('completed','sessionUnchanged','error')}),flush=True)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

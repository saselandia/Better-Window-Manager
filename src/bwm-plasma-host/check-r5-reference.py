#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BWM contributors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare R5 with installed Plasma in a new virtual KWin and private D-Bus.

No session display, user clipboard, compositor module, or user configuration is used.
The native shell and BWM are shown sequentially on the same private display. Input
uses KWin's testing protocol on that display only. Optional captures contain fixtures.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import tempfile
import time
import shutil

ROOT = Path(__file__).resolve().parents[2]


def stop(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(5)


def wait(predicate, description, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(.1)
    raise TimeoutError(description)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=ROOT/'build/bwm-plasma-host/test-plasma-ui')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--scales', default='1,1.25,1.5,1.6')
    parser.add_argument('--capture-dir', type=Path, help='Keep only fixture images for visual inspection')
    parser.add_argument('--egl-vendor-json', type=Path, help='EGL vendor for the private compositor (auto: NVIDIA when installed)')
    parser.add_argument('--gbm-backend', help='GBM backend for the private compositor')
    parser.add_argument('--scenes', default='applet,wallpaper,wallpaper-image,edit,paste')
    args = parser.parse_args()
    vendor = args.egl_vendor_json
    if vendor is None and Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json').is_file():
        vendor = Path('/usr/share/glvnd/egl_vendor.d/10_nvidia.json')
    backend = args.gbm_backend or ('nvidia-drm' if vendor and vendor.name=='10_nvidia.json' else None)
    scales = [float(value) for value in args.scales.split(',')]
    scenes = args.scenes.split(',')
    if any(scene not in ('applet', 'wallpaper', 'wallpaper-image', 'edit', 'paste', 'panel') for scene in scenes):
        parser.error('Unknown scene')
    captures = args.capture_dir.resolve() if args.capture_dir else None
    if captures:
        captures.mkdir(parents=True, exist_ok=True, mode=0o700)
    report = {'version': 1, 'reference': 'plasmashell and kwin_wayland 6.7.5',
        'sessionModified': False, 'userClipboardUsed': False, 'cases': [], 'passed': False}
    from PIL import Image, ImageChops, ImageStat
    with tempfile.TemporaryDirectory(prefix='bwm-r5-reference-build-') as build_dir:
        build = Path(build_dir)
        xml = Path('/usr/share/plasma-wayland-protocols/fake-input.xml')
        subprocess.run(['wayland-scanner', 'client-header', str(xml), str(build/'fake-input-client.h')], check=True)
        subprocess.run(['wayland-scanner', 'private-code', str(xml), str(build/'fake-input-protocol.c')], check=True)
        subprocess.run(['cc', '-fPIC', '-c', str(build/'fake-input-protocol.c'), '-o', str(build/'fake-input-protocol.o')], check=True)
        flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Gui', 'Qt6DBus', 'wayland-client'], text=True))
        subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-fPIC', '-O1', '-I'+str(build),
            str(ROOT/'tests/r5_reference_client.cpp'), str(build/'fake-input-protocol.o'), '-o', str(build/'client'), *flags], check=True)
        client = build/'client'
        for scale in scales:
            with tempfile.TemporaryDirectory(prefix='bwm-r5-reference-') as directory:
                root = Path(directory)
                for name in ('config', 'data', 'cache', 'state', 'runtime', 'defaults', 'Desktop'):
                    (root/name).mkdir(mode=0o700)
                env = {k: v for k, v in os.environ.items() if k not in ('DISPLAY', 'WAYLAND_DISPLAY', 'WAYLAND_SOCKET', 'HYPRLAND_INSTANCE_SIGNATURE')
                    and not k.startswith(('DBUS_', 'BWM_R4_', 'BWM_R5_', 'QT_'))}
                env.update(XDG_CONFIG_HOME=str(root/'config'), XDG_DATA_HOME=str(root/'data'),
                    XDG_CACHE_HOME=str(root/'cache'), XDG_STATE_HOME=str(root/'state'), XDG_RUNTIME_DIR=str(root/'runtime'),
                    XDG_CONFIG_DIRS=str(root/'defaults'), DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'no-system-bus'),
                    KWIN_COMPOSE='O2',
                    QSG_RHI_BACKEND='opengl', XDG_SESSION_TYPE='wayland', XDG_CURRENT_DESKTOP='KDE',
                    KWIN_SCREENSHOT_NO_PERMISSION_CHECKS='1', KWIN_WAYLAND_NO_PERMISSION_CHECKS='1', LANG='en_US.UTF-8', LANGUAGE='en')
                if vendor:
                    env['__EGL_VENDOR_LIBRARY_FILENAMES'] = str(vendor.resolve())
                if backend:
                    env['GBM_BACKEND'] = backend
                (root/'config/user-dirs.dirs').write_text(f'XDG_DESKTOP_DIR="{root}/Desktop"\n')
                (root/'config/kdeglobals').write_text(Path('/usr/share/color-schemes/BreezeDark.colors').read_text()+'\n[KDE]\nwidgetStyle=Breeze\n')
                (root/'config/plasmarc').write_text('[Theme]\nname=breeze-dark\n')
                packages = root/'data/plasma/plasmoids'
                packages.mkdir(parents=True)
                shutil.copytree(ROOT/'src/bwm-plasma-host/tests/shared-config', packages/'org.bwm.r4.shared-config')
                fixture = packages/'org.bwm.r4.shared-config/contents/ui/main.qml'
                original_fixture = '''import QtQuick
import org.kde.plasma.plasmoid
PlasmoidItem {
    preferredRepresentation: fullRepresentation
    fullRepresentation: Rectangle {
        implicitWidth: 72; implicitHeight: 36; color: "#355060"
        Text { anchors.centerIn: parent; text: "R5"; color: "white" }
    }
}
'''
                fixture.write_text(original_fixture.replace('PlasmoidItem {', 'PlasmoidItem { Timer { interval: 1500; running: true; onTriggered: Plasmoid.internalAction("configure").trigger() }') if 'applet' in scenes else original_fixture)
                processes = []
                def launch(argv, name, child_env=None):
                    with (root/f'{name}.log').open('w') as log:
                        process = subprocess.Popen([str(v) for v in argv], env=child_env or env,
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    processes.append(process)
                    return process
                def run(argv, timeout=10):
                    reply = subprocess.run([str(v) for v in argv], env=env, capture_output=True, text=True, timeout=timeout)
                    if reply.returncode:
                        raise RuntimeError(' '.join(str(v) for v in argv[:3])+': '+reply.stdout[-1500:]+reply.stderr[-1500:])
                    return reply.stdout
                def script(code):
                    return run(['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', code]).strip()
                def key(code):
                    run([client, 'input', 'key', str(code)])
                    time.sleep(.12)
                def capture(source, scene):
                    run([client, 'input', 'move', '2', '2', '0'])
                    time.sleep(.35)
                    image = root/f'{source}-{scene}.png'
                    meta = json.loads(run([client, 'capture', image, *(['workspace'] if scene in ('edit','panel') else [])]))
                    if abs(meta['scale']-scale)>.02:
                        raise AssertionError('Capture scale differs from requested scale: '+str(meta))
                    if captures:
                        destination = captures/f'{source}-{scene}-{scale}.png'
                        if destination.exists():
                            raise FileExistsError(destination)
                        shutil.copy2(image, destination)
                    return image, meta
                def paste(native_shell=False):
                    sample = root/'bwm-paste-fixture.txt'
                    sample.write_text('BWM disposable clipboard\n')
                    # wl-copy's data-control source belongs only to this private seat.
                    with (root/'clipboard.log').open('w') as log:
                        provider = subprocess.Popen(['wl-copy', '--primary', '--foreground', '--type', 'text/uri-list'], env=env,
                            stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    processes.append(provider)
                    provider.stdin.write((sample.as_uri()+'\r\n').encode());provider.stdin.close()
                    wait(lambda: subprocess.run(['wl-paste', '--primary', '--no-newline', '--type', 'text/uri-list'], env=env,
                        capture_output=True, timeout=3).stdout.decode().strip()==sample.as_uri(), 'Private clipboard did not become ready')
                    time.sleep(.2)
                    run([client, 'input', 'click', '500', '300', '274'])  # BTN_MIDDLE, private seat
                    if native_shell:
                        wait(lambda: script('print(desktops()[0].widgets().filter(w=>w.type=="org.kde.plasma.icon").length)')=='1',
                            'Middle-button paste did not create an Icon widget')
                        url = script('var w=desktops()[0].widgets().filter(w=>w.type=="org.kde.plasma.icon")[0]; w.currentConfigGroup=[]; print(w.readConfig("url"));')
                        if url!=sample.as_uri():
                            raise AssertionError('Native pasted URL differs: '+url)
                        script('desktops()[0].widgets().filter(w=>w.type=="org.kde.plasma.icon").forEach(w=>w.remove())')
                    else:
                        time.sleep(.8)  # The QtTest fixture checks the resulting widget and URL.
                    stop(provider)
                    return True
                try:
                    bus = subprocess.Popen(['dbus-daemon', '--session', '--nofork', '--print-address=1',
                        '--address=unix:path='+str(root/'runtime/bus')], env=env, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, start_new_session=True)
                    processes.append(bus)
                    env['DBUS_SESSION_BUS_ADDRESS'] = bus.stdout.readline().strip()
                    kwin = launch(['kwin_wayland', '--virtual', '--no-kactivities', '--no-global-shortcuts',
                        '--width', '1600', '--height', '1000', '--scale', str(scale), '--socket', 'bwm-reference'], 'kwin')
                    wait(lambda: (root/'runtime/bwm-reference').exists(), 'Private KWin did not start')
                    env.update(WAYLAND_DISPLAY=str(root/'runtime/bwm-reference'), QT_QPA_PLATFORM='wayland', QT_QPA_PLATFORMTHEME='kde',
                        BWM_R5_REFERENCE_MARKER=str(root/'reference.json'))
                    (root/'reference.json').write_text(json.dumps({'pid': kwin.pid, 'runtime': env['XDG_RUNTIME_DIR'], 'display': env['WAYLAND_DISPLAY']}))
                    # KWin's output store may replace the CLI scale with its DPI choice.
                    # Apply it through the native private output-management protocol and verify.
                    run(['kscreen-doctor', f'output.Virtual-0.scale.{scale}'])
                    outputs = json.loads(run([client, 'outputs']))
                    native_outputs = json.loads(run(['kscreen-doctor', '--json']))['outputs']
                    if len(native_outputs)!=1 or abs(native_outputs[0]['scale']-scale)>.02:
                        raise AssertionError('Private output scale differs: '+str(native_outputs))
                    report.setdefault('outputs', []).append(dict(requestedScale=scale, nativeScale=native_outputs[0]['scale'], **outputs[0]))
                    input_ready = root/'input.ready'
                    launch([client, 'input-keepalive', input_ready], 'input')
                    wait(input_ready.exists, 'Private input device did not start')
                    activities = launch(['/usr/libexec/kactivitymanagerd'], 'activities', dict(env, QT_QPA_PLATFORM='offscreen'))
                    wait(lambda: subprocess.run(['qdbus6', 'org.kde.ActivityManager'], env=env,
                        capture_output=True, timeout=3).returncode==0, 'Private activity manager did not start')
                    activity = run(['qdbus6', 'org.kde.ActivityManager', '/ActivityManager/Activities', 'org.kde.ActivityManager.Activities.CurrentActivity']).strip()
                    (root/'config/plasma-org.kde.plasma.desktop-appletsrc').write_text(
                        '[Containments][1]\nactivityId='+activity+'\nplugin=org.kde.plasma.folder\nlastScreen=0\nwallpaperplugin=org.kde.color\nlocation=0\nformfactor=0\n')
                    shell = launch(['plasmashell', '--no-respawn'], 'plasma')
                    def shell_ready():
                        try:
                            return int(script('print(desktops().length)')) > 0
                        except (ValueError, RuntimeError):
                            return False
                    wait(shell_ready, 'Native Plasma did not load its desktop', 20)
                    script('panels().forEach(p=>p.remove()); var d=desktops()[0]; '
                        'd.wallpaperPlugin="org.kde.color"; d.currentConfigGroup=["Wallpaper","org.kde.color","General"]; d.writeConfig("Color","#202428"); '
                        'd.currentConfigGroup=["ContainmentActions","RightButton;NoModifier"]; d.writeConfig("_display_settings",false); '
                        'var p=new Panel; p.location="bottom"; p.height=36; p.floating=false; p.opacity="translucent"; '
                        'p.addWidget("org.bwm.r4.shared-config");')
                    time.sleep(1)
                    native = {}
                    for scene in scenes:
                        if scene=='paste':
                            if scale!=scales[0]:
                                continue
                            paste(native_shell=True)
                            native[scene] = True
                        elif scene=='applet':
                            time.sleep(.7)  # Disposable fixture triggers its actual configure QAction.
                            native[scene] = capture('plasma', scene);key(1)
                        elif scene.startswith('wallpaper'):
                            if scene=='wallpaper-image':
                                script('var d=desktops()[0]; d.wallpaperPlugin="org.kde.image"; d.currentConfigGroup=["Wallpaper","org.kde.image","General"]; d.writeConfig("Image","file:///usr/share/wallpapers/Next/");');time.sleep(.4)
                            script('desktops()[0].showConfigurationInterface()');time.sleep(.7)
                            native[scene] = capture('plasma', scene);key(1)
                        elif scene=='panel':
                            native[scene] = capture('plasma', scene)
                        elif scene=='edit':
                            script('var d=desktops()[0]; d.wallpaperPlugin="org.kde.color"; d.currentConfigGroup=["Wallpaper","org.kde.color","General"]; d.writeConfig("Color","#202428");');time.sleep(.4)
                            run([client, 'input', 'click', '500', '300', '273'])
                            time.sleep(.2)
                            key(107);key(103);key(28)  # End, Up, Enter: native menu's Edit Mode above Configure
                            time.sleep(.7)
                            native[scene] = capture('plasma', scene);key(1)
                    stop(shell)
                    fixture.write_text(original_fixture)
                    time.sleep(.4)
                    for scene in scenes:
                        if scene not in native:
                            continue
                        ready = root/f'host-{scene}.ready'
                        own = launch([args.binary.resolve(), 'captureR5NativeScene'], 'host-'+scene,
                            dict(env, BWM_R5_VISUAL_SCENE=scene, BWM_R5_VISUAL_READY=str(ready)))
                        wait(lambda: ready.exists() or own.poll() is not None, 'BWM native scene did not become ready', 15)
                        if not ready.exists():
                            raise RuntimeError((root/f'host-{scene}.log').read_text()[-2500:])
                        host_state=json.loads(ready.read_text())
                        if scene=='paste':
                            paste()
                            result = {'scale': scale, 'scene': scene, 'nativePaste': True, 'bwmPaste': True, 'userClipboardUsed': False, 'result': 'org.kde.plasma.icon with the disposable local URL'}
                        else:
                            image, meta = capture('bwm', scene)
                            reference, ref_meta = native[scene]
                            with Image.open(image) as source, Image.open(reference) as original:
                                source, original = source.convert('RGB'), original.convert('RGB')
                                result = {'scale': scale, 'scene': scene, 'bwm': meta, 'plasma': ref_meta, 'sameSize': source.size==original.size}
                                if source.size==original.size:
                                    difference = ImageChops.difference(source, original)
                                    result.update(differenceBounds=difference.getbbox(), meanChannelError=ImageStat.Stat(difference).mean,
                                        differentPixels=sum(any(pixel) for pixel in difference.get_flattened_data()),
                                        maxChannelDelta=max(hi for lo, hi in difference.getextrema()),
                                        pixelsAboveOneChannelUnit=sum(max(pixel)>1 for pixel in difference.get_flattened_data()))
                                result['bwmSha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
                                result['plasmaSha256'] = hashlib.sha256(reference.read_bytes()).hexdigest()
                        result['hostState']=host_state
                        ready.with_name(ready.name+'.stop').write_text('stop')
                        own.wait(8)
                        if own.returncode:
                            raise RuntimeError((root/f'host-{scene}.log').read_text()[-2500:])
                        report['cases'].append(result)
                        print(json.dumps(result), flush=True)
                except Exception as error:
                    report['error'] = str(error)
                    report['logs'] = {name: (root/f'{name}.log').read_text(errors='replace')[-2000:]
                        for name in ('kwin', 'plasma', 'activities', 'clipboard', 'input') if (root/f'{name}.log').exists()}
                    break
                finally:
                    for process in reversed(processes):
                        stop(process)
                    report['cleanupVerified'] = all(process.poll() is not None for process in processes)
    report['passed'] = 'error' not in report and bool(report['cases']) and report.get('cleanupVerified', False)
    report['pixelParityVerified'] = report['passed'] and all(case.get('differentPixels', 0)==0 and case.get('sameSize', True) for case in report['cases'])
    configuration_cases = [case for case in report['cases'] if case['scene'] in ('applet', 'wallpaper', 'wallpaper-image')]
    report['configurationParityWithinOneChannelUnit'] = report['passed'] and bool(configuration_cases) and all(
        case.get('sameSize') and case.get('maxChannelDelta', 256)<=1 for case in configuration_cases)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({key: report.get(key) for key in ('passed', 'pixelParityVerified', 'error', 'cleanupVerified')}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())

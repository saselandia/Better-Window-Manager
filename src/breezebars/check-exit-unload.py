#!/usr/bin/env python3
"""§376: salir de Hyprland con una ventana X11 desmapeada no debe caer tras descargar el plugin.

Hyprland desechable como ventana del workspace 9 de la sesión (sin tocar el compositor diario):
carga el plugin, abre kitty y una ventana X11 que se mapea, se desmapea y sigue viva, y sale
con hl.dsp.exit(). Con el fallo, el compositor termina con SIGSEGV en el liberador de la
decoración (código ya desmapeado).
"""
import json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('cdh', '/mnt/HDD1TB/Projects/hyprland-de/src/bwm-plasma-host/check-desktops-hyprland.py')
cdh = importlib.util.module_from_spec(spec); spec.loader.exec_module(cdh)
CFG = '''hl.monitor({ output = "", mode = "1280x800", position = "0x0", scale = 1 })
hl.config({ misc = { disable_hyprland_logo = true, disable_splash_rendering = true }, animations = { enabled = true } })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 40, bezier = "default", style = "popin 80%" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 40, bezier = "default" })
hl.window_rule({ name = "bwm-exit-float", match = { class = "bwm-exit-k.*" }, float = true })
'''
def run(plugin, label, close_first, hide=False):
    before = {i['instance'] for i in json.loads(cdh.hyprctl('instances', '-j'))}
    res = {'case': label}
    with tempfile.TemporaryDirectory(prefix='bwm-exit-') as t:
        root = Path(t); (root/'hyprland.lua').write_text(CFG)
        cdh.parent_rule(9)
        env = {k: v for k, v in os.environ.items() if k != 'HYPRLAND_INSTANCE_SIGNATURE'}
        nested = subprocess.Popen(['Hyprland', '--config', str(root/'hyprland.lua')], env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            inst = cdh.wait(lambda: next((i for i in json.loads(cdh.hyprctl('instances', '-j'))
                    if i['instance'] not in before and i['pid'] == nested.pid), None), 20, 'no start')
            sig = inst['instance']
            res['load'] = cdh.hyprctl('plugin', 'load', plugin, instance=sig, check=False).strip()
            cdh.hyprctl('eval', 'hl.config({ plugin = { ' + CFG_KEY + ' = { enabled = true } } })', instance=sig, check=False)
            cdh.hyprctl('dispatch', 'hl.dsp.exec_cmd("kitty --config NONE --class bwm-exit-ka")', instance=sig)
            cdh.hyprctl('dispatch', 'hl.dsp.exec_cmd("python3 ' + str(Path(__file__).resolve().parent/'tests/x11_unmapped_client.py') + '")', instance=sig)
            time.sleep(6)
            csd = cdh.hyprctl('-j', 'breezebars-csd', instance=sig, check=False)
            try:
                wins = json.loads(csd)['windows']; res['windows'] = [(w['class'] or w['title'], w['visible']) for w in wins]
            except Exception: res['windows'] = csd[:200]
            if hide:
                cdh.hyprctl('dispatch', 'hl.dsp.window.move({ workspace = "special:hidden" })', instance=sig, check=False)
                time.sleep(0.3)
            batch = []
            if close_first:
                clients = json.loads(cdh.hyprctl('-j', 'clients', instance=sig))
                for c in clients:
                    batch.append(f'dispatch hl.dsp.window.close({{ window = "address:{c["address"]}" }})')
            batch.append('dispatch hl.dsp.exit()')
            cdh.hyprctl('--batch', ' ; '.join(batch), instance=sig, check=False)
            rc = nested.wait(20)
            res['rc'] = rc
        except Exception as e:
            res['error'] = str(e)
        finally:
            if nested.poll() is None:
                os.killpg(nested.pid, signal.SIGKILL); nested.wait(5); res['killed'] = True
            try: os.killpg(nested.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            cdh.parent_rule(None)
    print(json.dumps(res), flush=True)
    return res
import argparse
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--plugin', default=str(Path(__file__).resolve().parent/'breezebars.so'))
ap.add_argument('--config-key', default='breezebars', help='hyprbars para el plugin de Omarchy')
ap.add_argument('--runs', type=int, default=3)
a = ap.parse_args()
CFG_KEY = a.config_key
results = [run(a.plugin, 'x11-unmapped+exit', False) for _ in range(a.runs)]
sys.exit(0 if all(r.get('rc') == 0 for r in results) else 1)

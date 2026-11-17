"""Avisos de los gestores comunes a la skin activa (sin datos de ninguna skin aquí)."""
import json
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys


def effective_options():
    """Read current common options and user overrides without writing/applying a skin."""
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    options=json.loads((config/'illogical-impulse/config.json').read_text())
    active=options.get('appearance',{}).get('bwmTheme','default')
    if not isinstance(active,str):raise ValueError('Invalid active skin')
    loader=importlib.machinery.SourceFileLoader('bwm_shared_user_options',str(Path(__file__).with_name('bwm-user-config')))
    spec=importlib.util.spec_from_loader(loader.name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module)
    module.apply_shell(options,active)
    return options


def shared():
    """Notify reviewed bundled adapters independently of the active skin.

    A prerequisite only arms delivery, never loads/enables a provider. Downloaded
    skins/packages do not acquire automatic background execution by declaring it.
    """
    import bwm_skins
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    report={'version':1,'retryMs':0,'adapters':[]}
    for skin in bwm_skins.all_skins():
        if skin.get('builtin') is not True:continue
        entry=skin.get('hooks',{}).get('sharedSettings')
        if not entry:continue
        status={'skin':skin['id'],'active':False,'applied':False}
        try:
            if not isinstance(entry,dict):raise ValueError('Invalid shared settings hook')
            interval=entry.get('intervalMs')
            if type(interval) is not int or not 1000<=interval<=30000:raise ValueError('Invalid shared settings interval')
            relative=Path(entry['requiresConfigFile'])
            if relative.is_absolute() or '..' in relative.parts or str(relative)=='.':raise ValueError('Invalid shared settings prerequisite')
            directory=Path(skin['dir']).resolve();script=(directory/entry['script']).resolve()
            if directory not in script.parents:raise ValueError('Shared settings hook escapes skin')
            if not (config/relative).is_file():
                report['adapters'].append(status);continue
            status['active']=True
            # Retry only while delivery is pending: an applied value is kept by the
            # provider and later changes come from the shell's own change signals.
            # An adapter reporting "inactive" (provider not loaded in this session)
            # has nothing to deliver and is not polled.
            retry=True
            try:
                result=subprocess.run([sys.executable,str(script),'shared'],capture_output=True,text=True,timeout=3,check=True)
                if len(result.stdout)>65536:raise ValueError('Oversized shared settings receipt')
                receipt=json.loads(result.stdout)
                if not isinstance(receipt,dict) or type(receipt.get('version')) is not int or receipt['version']!=1 or type(receipt.get('applied')) is not bool:
                    raise ValueError('Invalid shared settings receipt')
                status['applied']=receipt['applied']
                if receipt.get('inactive') is True and not receipt['applied']:status['inactive']=True;retry=False
                elif receipt['applied']:retry=False
            finally:
                if retry:report['retryMs']=interval if not report['retryMs'] else min(report['retryMs'],interval)
            if not status['applied'] and isinstance(receipt.get('error'),str):status['error']=receipt['error'][:256]
        except (OSError,KeyError,TypeError,ValueError,subprocess.SubprocessError) as error:
            status['error']=str(error)
        report['adapters'].append(status)
    return report


def changed():
    """Exportar después de guardar un ajuste; el gestor conserva la única recarga necesaria."""
    try:
        config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        active = json.loads((config / "illogical-impulse/config.json").read_text()).get("appearance", {}).get("bwmTheme", "default")
        import bwm_skins
        skin = bwm_skins.skin(active)
        hook = skin.get("hooks", {}).get("settingsChanged")
        if not hook:
            return
        script = (Path(skin["dir"]) / hook).resolve()
        if Path(skin["dir"]).resolve() not in script.parents:
            raise ValueError("El hook de ajustes debe estar dentro de su skin")
        subprocess.run([sys.executable, str(script), "export", "--no-reload"],
                       stdout=subprocess.DEVNULL, timeout=20, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"BWM: no se pudo sincronizar el ajuste con la skin: {exc}", file=sys.stderr)


def skin_changed(phase, previous, current):
    """Notify hooks of both involved skins; no skin-specific policy in this module.

    Before is called before changing profiles; after is called after shell reload.
    A hook may only act on an explicitly registered/opted-in helper of its own.
    """
    if phase not in ('before', 'after'): raise ValueError('Fase de cambio de skin inválida')
    import bwm_skins
    ok = True
    for sid in dict.fromkeys((previous, current)):
        skin = bwm_skins.skin(sid)
        hook = skin.get('hooks', {}).get('skinChanged')
        if not hook: continue
        try:
            directory = Path(skin['dir']).resolve()
            script = (directory / hook).resolve()
            if directory not in script.parents: raise ValueError('El hook debe estar dentro de su skin')
            result = subprocess.run([sys.executable, str(script), 'event', phase, previous, current],
                                    capture_output=True, text=True, timeout=3, check=False)
            if result.returncode: raise RuntimeError(result.stderr.strip() or 'El hook no confirmó el cambio')
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f'BWM: hook de cambio de {sid}: {exc}', file=sys.stderr);ok = False
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ['shared']:
        print(json.dumps(shared(),ensure_ascii=False));raise SystemExit(0)
    if sys.argv[1:2] == ['skin']:
        if len(sys.argv) != 5: raise SystemExit('Uso: bwm_settings_hooks.py skin before|after ANTERIOR ACTUAL')
        raise SystemExit(0 if skin_changed(*sys.argv[2:]) else 1)
    changed()

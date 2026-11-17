#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Forward the existing shared count outside the compositor, via the existing bridge."""
import json
import contextlib
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time


@contextlib.contextmanager
def bridge_lock(state,blocking=True):
    state.mkdir(parents=True,exist_ok=True)
    with open(state/'bridge.lock','a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield


def configured_count(options):
    value=options.get('bar',{}).get('workspaces',{}).get('shown',10)
    if type(value) is not int or not 1<=value<=100:
        raise ValueError('Invalid shared workspace count')
    return value


def publish(bridge):
    # Installation alone never enables/loads the plugin. An absent optional
    # module costs no IPC; a loaded old module cannot forge a valid receipt.
    if not (bridge.CONFIG/'hypr/plugins/bwm-plasma-desktops.so').is_file():return False
    count=configured_count(bridge.effective_options())
    reply=bridge.run(['hyprctl','bwm-plasma-desktops-count',str(count)],timeout=2)
    if reply.returncode:raise RuntimeError('Workspace count IPC failed')
    try:data=json.loads(reply.stdout)
    except ValueError as error:raise RuntimeError('Workspace count IPC returned no receipt') from error
    if (not isinstance(data,dict) or type(data.get('version')) is not int or data['version']!=1 or
        data.get('accepted') is not True or type(data.get('configuredCount')) is not int or data['configuredCount']!=count or
        type(data.get('revision')) is not int or data['revision']<1):
        raise RuntimeError('Workspace count receipt rejected or mismatched')
    return True


class Runtime:
    """One coordinator in the existing bridge, with no watcher, daemon or preferences."""
    def __init__(self,bridge,clock=time.monotonic):
        self.bridge=bridge;self.clock=clock;self.next=0;self.last_error=''

    def tick(self,force=False,locked=False):
        now=self.clock()
        if not force and now<self.next:return False
        self.next=now+2
        try:
            if not (self.bridge.CONFIG/'hypr/plugins/bwm-plasma-desktops.so').is_file():return False
            # Serialize with reconcile using its existing lock, outside the
            # compositor. Never block the watch loop or acquire it recursively.
            guard=self.bridge.lock(blocking=False) if not locked and hasattr(self.bridge,'lock') else contextlib.nullcontext()
            with guard:applied=publish(self.bridge)
            self.last_error='';return applied
        except BlockingIOError:
            self.next=now+0.25;return False
        except (OSError,ValueError,TypeError,AttributeError,RuntimeError,subprocess.SubprocessError) as error:
            message=str(error)
            if message!=self.last_error:print('kde-config-bridge: native workspaces: '+message,file=sys.stderr,flush=True)
            self.last_error=message;return False


def shared_main():
    """One bounded invocation by the common shell; no KDE bridge/import/watch."""
    from types import SimpleNamespace
    scripts=Path(__file__).resolve().parents[3]/'scripts'
    sys.path.insert(0,str(scripts))
    import bwm_settings_hooks
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    state=Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'bwm/plasma'
    def run(argv,timeout):return subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    bridge=SimpleNamespace(CONFIG=config,effective_options=bwm_settings_hooks.effective_options,
        run=run,lock=lambda blocking=True:bridge_lock(state,blocking))
    runtime=Runtime(bridge)
    applied=runtime.tick(force=True)
    result={'version':1,'applied':applied}
    if runtime.last_error:result['error']=runtime.last_error[:256]
    return result


if __name__=='__main__':
    if sys.argv[1:]!=['shared']:raise SystemExit('Usage: native_workspaces.py shared')
    print(json.dumps(shared_main()))

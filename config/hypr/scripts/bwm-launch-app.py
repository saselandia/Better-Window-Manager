#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Launch a parsed DesktopEntry using the current compositor environment, not the shell's boot environment."""
import json
from pathlib import Path
import sys
import bwm_session


def command_for(payload):
    if not isinstance(payload, dict):raise ValueError('Invalid desktop launch payload')
    args=payload.get('command')
    if not isinstance(args,list) or not args or not all(isinstance(arg,str) and '\0' not in arg for arg in args) or not args[0]:
        raise ValueError('Desktop entry has no valid parsed command')
    cwd=payload.get('workingDirectory','')
    if not isinstance(cwd,str) or '\0' in cwd:raise ValueError('Invalid working directory')
    if payload.get('terminal',False):
        args=[str(Path(__file__).with_name('bwm-terminal')),'--',*args]
    return ['env','--chdir',cwd,*args] if cwd else args


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    try:
        if len(argv)!=1:raise ValueError('Expected one JSON desktop launch payload')
        args=command_for(json.loads(argv[0]))
        if not bwm_session.spawn(args,allow_fallback=False):
            raise RuntimeError('Hyprland did not accept the application launch')
    except (ValueError,RuntimeError) as error:
        print(f'BWM: {error}',file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())

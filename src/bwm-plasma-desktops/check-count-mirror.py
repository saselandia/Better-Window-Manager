#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Test real Python forwarding against real C++ receipts, with private transport only."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
source=Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native_workspaces.py'
spec=importlib.util.spec_from_file_location('count_forwarding',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
report={'version':1,'sessionModified':False,'realHyprctlUsed':False,'passed':False}
try:
    result=subprocess.run([str(a.binary)],capture_output=True,text=True,timeout=5,check=True)
    report['projectionChecks']=result.stdout
    with tempfile.TemporaryDirectory(prefix='bwm-count-contract-') as tmp:
        config=Path(tmp);plugin=config/'hypr/plugins/bwm-plasma-desktops.so';plugin.parent.mkdir(parents=True);plugin.touch()
        settings=config/'config.json';original=b'{"bar":{"workspaces":{"shown":3}},"foreign":"keep"}';settings.write_bytes(original)
        options={'bar':{'workspaces':{'shown':7}}};calls=[]
        def runner(argv,timeout):
            assert argv[:2]==['hyprctl','bwm-plasma-desktops-count'] and len(argv)==3
            # The production helper constructs the request; the SAME native
            # CountMirror command/parser/receipt implementation executes it.
            result=subprocess.run([str(a.binary),'--receipt',' '.join(argv[1:])],capture_output=True,text=True,timeout=timeout,check=True)
            calls.append({'request':argv[1:],'receipt':json.loads(result.stdout)});return result
        bridge=SimpleNamespace(CONFIG=config,effective_options=lambda:options,run=runner)
        for count in [1,7,100]:
            options['bar']['workspaces']['shown']=count
            assert module.publish(bridge)
        assert settings.read_bytes()==original
        report.update(passed=True,forwarded=calls,settingsUnchanged=True,helperAndNativeReceiptCombined=True)
except (AssertionError,OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
    report['error']=str(error)
a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)

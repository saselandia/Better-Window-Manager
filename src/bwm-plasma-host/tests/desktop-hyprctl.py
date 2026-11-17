#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Test-only IPC substitute. Lua runs only against fake hl; never contacts a compositor."""
import json
import os
from pathlib import Path
import sys
import subprocess
args=sys.argv[1:]
state=Path(os.environ['BWM_R4_FAKE_CLIENTS'])
client=json.loads(state.read_text())
if 'repl' in args:
    # Execute the real generated guards/dispatcher receipt against a data-only
    # Lua stand-in. Do not pretend returncode=0 means that a dispatch succeeded.
    def literal(value):
        if value is None:return 'nil'
        if type(value) is bool:return 'true' if value else 'false'
        if type(value) is int:return str(value)
        if isinstance(value,str):return json.dumps(value,ensure_ascii=False)
        if isinstance(value,dict):return '{'+','.join('['+literal(k)+']='+literal(v) for k,v in value.items())+'}'
        raise ValueError('Unexpected Lua fixture value')
    config=Path(os.environ['XDG_CONFIG_HOME'])/'illogical-impulse/config.json'
    theme=json.loads(config.read_text())['appearance']['bwmTheme']
    fields={key:client.get(key) for key in ('pid','mapped','hidden','pinned','workspace','fullscreen')}
    prefix='local w='+literal(fields)+'\npackage.loaded["modules.theme"]={name='+literal(theme)+'}\n'
    prefix+='''hl={dsp={window={fullscreen=function(o) return o end}}}
hl.get_window=function() return w end
hl.dispatch=function(o)
 if o.mode~=0 or o.window~=w or (o.action~="set" and o.action~="unset") then return {ok=false} end
 w.fullscreen=o.action=="set" and 2 or 0
 return {ok=true}
end
'''
    reply=subprocess.run([os.environ['BWM_R4_TEST_LUA'],'-'],input=prefix+'\nlocal receipt='+args[-1]+'\nprint(receipt)\nprint(w.fullscreen or 0)\n',
                         capture_output=True,text=True,timeout=2)
    if reply.returncode:
        print(reply.stderr,file=sys.stderr);raise SystemExit(2)
    receipt,fullscreen=reply.stdout.strip().splitlines()
    if receipt=='bwm-r4-fullscreen-ok':
        client['fullscreen']=int(fullscreen)
        temporary=state.with_suffix('.tmp');temporary.write_text(json.dumps(client));os.replace(temporary,state)
    with Path(os.environ['BWM_R4_FAKE_ACTIONS']).open('a') as log:log.write(args[-1]+'\n')
    print(receipt)
elif 'dispatch' in args:
    code=args[-1]
    with Path(os.environ['BWM_R4_FAKE_ACTIONS']).open('a') as log:log.write(code+'\n')
    if 'workspace = "special:minimized"' in code:
        client['workspace']={'id':-98,'name':'special:minimized'}
        client['tags']=['omarchy-minimized-from-1']
    elif 'window.move' in code and 'workspace = target' in code:
        client['workspace']={'id':1,'name':'1'};client['tags']=[]
    elif 'window.close' in code:client['mapped']=False
    temporary=state.with_suffix('.tmp');temporary.write_text(json.dumps(client));os.replace(temporary,state)
    print('ok')
elif 'clients' in args:print(json.dumps([client]))
elif 'activewindow' in args:print('{}')
elif 'monitors' in args:
    x,y,width,height=client.get('fixtureScreen',[0,0,1920,1080])
    print(json.dumps([{'id':0,'activeWorkspace':{'id':1},'x':x,'y':y,'width':width,'height':height,'scale':1,'transform':0,'specialWorkspace':{'id':0}}]))
else:
    print('Unexpected mock request',file=sys.stderr);raise SystemExit(2)

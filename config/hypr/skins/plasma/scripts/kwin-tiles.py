#!/usr/bin/env python3
"""Breeze: edit the KWin tile tree or apply an exact drag-preview frame."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import kwin_tiles


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def apply_frame(kw,client,monitor,frame,direction):
    from bwm_windows import monitor_box
    if len(frame)!=4 or not all(kwin_tiles.finite(v) for v in frame) or min(frame[2:])<=0:return False
    x,y,w,h=frame;mx,my,mw,mh=monitor_box(monitor)
    reserved=(list(monitor.get('reserved',[]))+[0,0,0,0])[:4];l,t,r,b=reserved
    # Reject stale/out-of-workarea frames instead of applying a different preview.
    if x<mx+l-1 or y<my+t-1 or x+w>mx+mw-r+1 or y+h>my+mh-b+1:return False
    workspace=client.get('workspace',{}).get('id') if client.get('monitor')==monitor['id'] else monitor['activeWorkspace']['id']
    kw.run_lua(kw.window_lua(client,f'hl.dispatch(hl.dsp.window.move({{workspace={int(workspace)},follow=false,window=w}}))'))
    fresh=kw.find_client(client['address'])
    if not fresh or fresh.get('pid')!=client.get('pid'):return False
    if direction=='maximize':kw.maximize(fresh,'full');return True
    borders=kw.window_borders(fresh)
    cx,cy,cw,ch=kw.content_from_frame(frame,borders)
    qt=kw.load_script('bwm_quick_tile','quick-tile.py')
    if not kw.has_tag(fresh,'snapped') and not kw.mode_from_tags(fresh.get('tags')):qt.save_presnap(fresh['address'],fresh['size'])
    # Remove only BWM window-state tags, preserving rules and user tags.
    remove=' '.join('hl.dispatch(hl.dsp.window.tag({tag='+json.dumps('-'+str(tag).rstrip('*'))+',window=w}))'
                    for tag in fresh.get('tags',[]) if not str(tag).endswith('*') and (str(tag).startswith('snapped') or str(tag).startswith('bwm-max')))
    body=f'''hl.dispatch(hl.dsp.window.fullscreen({{mode=0,action='unset',window=w}}))
        hl.dispatch(hl.dsp.window.fullscreen({{mode=1,action='unset',window=w}}))
        hl.dispatch(hl.dsp.window.float({{action='enable',window=w}}))
        {remove}
        hl.dispatch(hl.dsp.window.tag({{tag='+snapped',window=w}}))
        hl.dispatch(hl.dsp.window.tag({{tag={json.dumps('+snapped_'+direction)},window=w}}))
        hl.dispatch(hl.dsp.window.resize({{x={round(cw)},y={round(ch)},relative=false,window=w}}))
        hl.dispatch(hl.dsp.window.move({{x={round(cx)},y={round(cy)},relative=false,window=w}}))'''
    kw.run_lua(kw.window_lua(fresh,body));return True


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('apply');a.add_argument('address');a.add_argument('--pid',type=int,required=True);a.add_argument('--monitor',required=True);a.add_argument('--direction',choices=['left','right','top-left','top-right','bottom-left','bottom-right','bottom','maximize','custom'],required=True);a.add_argument('--frame',required=True)
    a=sub.add_parser('inspect');a.add_argument('--monitor');a.add_argument('--output')
    a=sub.add_parser('edit');a.add_argument('operation',choices=['split-horizontal','split-vertical','join','ratio','save']);a.add_argument('payload')
    sub.add_parser('open')
    args=p.parse_args(argv)
    if args.action=='open':
        subprocess.run(['qs','-c','ii','ipc','call','plasmaTiles','open']);return 0
    kw=module('bwm_tiles_window','kwin-window.py')
    if args.action=='apply':
        c=kw.find_client(args.address);monitor=next((m for m in kw.hypr_json('monitors') or [] if 'desc:'+m.get('description','')==args.monitor),None)
        if not c or c.get('pid')!=args.pid or not monitor:return 1
        # Plugin may outlive a skin switch; never snap other skins from an old queued command.
        theme=kw.hypr_json('getoption','plugin:breezebars:enabled')
        if not isinstance(theme,dict) or not theme.get('int'):return 1
        return 0 if apply_frame(kw,c,monitor,[float(v) for v in args.frame.split(',')],args.direction) else 1
    bridge=module('bwm_tiles_bridge','kde-config-bridge.py')
    if args.action=='inspect':
        monitors=kw.hypr_json('monitors') or [];active=kw.hypr_json('activeworkspace') or {}
        mon=next((m for m in monitors if 'desc:'+m.get('description','')==args.monitor),None) if args.monitor else next((m for m in monitors if m['id']==active.get('monitorID')),None)
        if not mon:mon=next(iter(monitors),None)
        if not mon:return 1
        ws=mon.get('activeWorkspace',{}).get('id',1)
        data=kwin_tiles.inspect(bridge,mon,ws,args.output);data['monitors']=[m['description'] for m in monitors];print(json.dumps(data));return 0
    data=json.loads(args.payload)
    if args.operation=='save':
        if not bridge.active():raise ValueError('El editor sólo guarda en Breeze')
        with bridge.lock():kwin_tiles.save(bridge,data)
    else:
        path=data.get('selected',[])
        if args.operation.startswith('split-'):data['tree']=kwin_tiles.split(data['tree'],path,args.operation.split('-')[1])
        elif args.operation=='join':data['tree']=kwin_tiles.join(data['tree'],path)
        else:data['tree']=kwin_tiles.resize_split(data['tree'],path,data['ratio'])
        data['leaves']=kwin_tiles.leaves(data['tree']);print(json.dumps(data))
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,KeyError,OSError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)

# SPDX-License-Identifier: GPL-2.0-or-later
"""Track BWM maximized frames in the existing Breeze bridge; no restore-state writes."""
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import stat
import tempfile
import time


def process_start(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        return fields[19] if fields[0] not in ('Z','X') else None
    except (OSError,IndexError):return None


def transition_busy(path='/tmp/bwm-theme-manager.lock'):
    fd=None
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid():return True
        try:fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
        except BlockingIOError:return True
        return False
    except FileNotFoundError:return False
    except OSError:return True
    finally:
        if fd is not None:os.close(fd)


def eligible(client, kw):
    space=client.get('workspace') or {}
    if not isinstance(space,dict) or not isinstance(client.get('tags'),list):return False
    if not isinstance(client.get('address'),str):return False
    for key in ('at','size'):
        values=client.get(key)
        if not isinstance(values,list) or len(values)!=2 or any(type(n) not in (int,float) or not math.isfinite(n) for n in values):return False
    if min(client['size'])<=0:return False
    tags={str(t).rstrip('*') for t in client['tags']}
    return (type(client.get('pid')) is int and client['pid']>0 and
            type(client.get('monitor')) is int and client['monitor']>=0 and
            re.fullmatch(r'0x[0-9a-fA-F]+',client.get('address','')) is not None and
            client.get('mapped') is True and client.get('floating') is True and not client.get('hidden',False) and
            client.get('fullscreen',0)==0 and client.get('fullscreenClient',0)==0 and
            type(space.get('id')) is int and space['id']>0 and space['id']!=99 and
            not str(space.get('name','')).startswith('special:') and
            not tags.intersection({'bwm-ignore-kwin-rules','bwm-ignore-maximized-area','snapped'}) and
            not any(t.startswith('snapped_') for t in tags) and
            kw.mode_from_tags(tags)>0)


def area(monitor,kw):
    for key in ('x','y','width','height','scale'):
        value=monitor.get(key)
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Invalid monitor geometry')
    if monitor['scale']<=0 or monitor['width']<=0 or monitor['height']<=0:raise ValueError('Invalid monitor size')
    if type(monitor.get('transform',0)) is not int or not 0<=monitor.get('transform',0)<=7:raise ValueError('Invalid output transform')
    reserved=monitor.get('reserved')
    if not isinstance(reserved,list) or len(reserved)!=4 or any(type(n) not in (int,float) or not math.isfinite(n) or n<0 for n in reserved):raise ValueError('Invalid reserved area')
    x,y,w,h=kw.bwm_windows.monitor_box(monitor,round_to_nearest=True)
    left,top,right,bottom=reserved
    result=tuple(int(n) for n in (x+left,y+top,w-left-right,h-top-bottom))
    if min(result[2:])<=0:raise ValueError('Empty work area')
    return result


def target_frame(frame,work,mode):
    x,y,w,h=frame;ax,ay,aw,ah=work
    if mode&2:x,w=ax,aw
    if mode&1:y,h=ay,ah
    return (x,y,w,h)


def command(client,work,borders,kw):
    mode=kw.mode_from_tags(client.get('tags',[]))
    frame=kw.frame_from_client(client,borders);target=target_frame(frame,work,mode)
    if tuple(frame)==target:return None
    x,y,w,h=(int(round(n)) for n in kw.content_from_frame(target,borders))
    addr=json.dumps('address:'+client['address']);pid=client['pid'];monitor=int(client['monitor'])
    return f'''(function()
      local theme=package.loaded["modules.theme"]
      if not theme or theme.name~="plasma" then return hl.dsp.no_op() end
      local w=hl.get_window({addr})
      if not w or w.pid~={pid} or not w.mapped or w.hidden or not w.floating or w.fullscreen~=0 or w.fullscreen_client~=0 then return hl.dsp.no_op() end
      local ws=w.workspace; local mon=w.monitor
      if not ws or ws.id<1 or ws.id==99 or not mon or mon.id~={monitor} then return hl.dsp.no_op() end
      local tags={{}};for _,tag in ipairs(w.tags or {{}}) do local clean=tag:gsub("%*$","");if clean:sub(1,8)=="snapped_" then return hl.dsp.no_op() end tags[clean]=true end
      if tags["bwm-ignore-kwin-rules"] or tags["bwm-ignore-maximized-area"] or tags["snapped"] then return hl.dsp.no_op() end
      if ((tags["bwm-max-v"] and 1 or 0)+(tags["bwm-max-h"] and 2 or 0))~={mode} then return hl.dsp.no_op() end
      hl.dispatch(hl.dsp.window.resize({{x={w},y={h},relative=false,window=w}}))
      hl.dispatch(hl.dsp.window.move({{x={x},y={y},relative=false,window=w}}))
      return hl.dsp.no_op()
    end)()'''


class Runtime:
    def __init__(self,bridge,clock=time.monotonic,rules=None):
        self.b=bridge;self.clock=clock;self.next_poll=0;self.done={};self.attempts={}
        self.rules=rules
        spec=importlib.util.spec_from_file_location('bwm_area_window',Path(__file__).with_name('kwin-window.py'))
        self.kw=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.kw)
        self.ready=bridge.STATE/'area-observer.json';self.started=time.time();self.marked=False
        self.start_id=process_start(os.getpid())
        self.last_error=None;self.error_time=0

    def log_error(self,error):
        text=str(error);now=self.clock()
        if text!=self.last_error or now-self.error_time>=30:
            print('kde-config-bridge: maximized area: '+text,file=sys.stderr,flush=True)
            self.last_error=text;self.error_time=now

    def query(self,name):
        reply=self.b.run(['hyprctl','-j',name],timeout=2)
        if reply.returncode:raise ValueError('Area observer IPC unavailable')
        return json.loads(reply.stdout)

    def mark_ready(self):
        self.ready.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.area-ready-',dir=self.ready.parent)
        try:
            with os.fdopen(fd,'w') as file:json.dump({'version':1,'pid':os.getpid(),'processStart':self.start_id,'startedAt':self.started,'ready':True},file)
            os.replace(name,self.ready);self.marked=True
        finally:Path(name).unlink(missing_ok=True)

    def tick(self):
        now=self.clock()
        if now<self.next_poll:return
        self.next_poll=now+.5
        if transition_busy():return
        monitors=self.query('monitors');clients=self.query('clients')
        if not isinstance(monitors,list) or not monitors or not isinstance(clients,list):raise ValueError('Invalid area observer snapshot')
        if any(not isinstance(m,dict) or type(m.get('id')) is not int or not isinstance(m.get('description',''),str) or not (m.get('description') or (isinstance(m.get('name'),str) and m['name'])) for m in monitors) or any(not isinstance(c,dict) for c in clients):raise ValueError('Invalid monitor/client identity')
        # The identity only lives in this in-memory signature, to notice an id
        # reused by another output. Outputs without EDID (headless, virtual or
        # a monitor that sends none) have an empty description: use their
        # connector for this purpose instead of rejecting every monitor.
        areas={m['id']:(m.get('description') or 'connector:'+m['name'],area(m,self.kw)) for m in monitors}
        if len(areas)!=len(monitors):raise ValueError('Duplicate monitor identity')
        if not self.marked:self.mark_ready()
        live={(c.get('address'),c.get('pid')) for c in clients if isinstance(c.get('address'),str) and type(c.get('pid')) is int}
        self.done={k:v for k,v in self.done.items() if k in live};self.attempts={k:v for k,v in self.attempts.items() if k in live}
        pending=[]
        for c in clients:
            if not isinstance(c.get('address'),str) or type(c.get('pid')) is not int:continue
            ident=(c.get('address'),c.get('pid'))
            if not eligible(c,self.kw) or c.get('monitor') not in areas:
                self.done.pop(ident,None);self.attempts.pop(ident,None);continue
            signature=(areas[c['monitor']],self.kw.mode_from_tags(c.get('tags',[])),c['workspace']['id'],getattr(self.rules,'last_text',None))
            if self.done.get(ident)==signature:continue
            # The old frame is no longer confirmed once we observe a transition.
            # Its signature can return before the new frame is confirmed.
            self.done.pop(ident,None)
            attempt=self.attempts.get(ident)
            if attempt is not None and attempt[0]!=signature:
                self.attempts.pop(ident)
            pending.append((c,ident,signature))
        if not pending:return
        data=self.query('breezebars-csd')
        if not isinstance(data,dict) or data.get('version')!=1 or data.get('api')!='breezebars-csd':raise ValueError('Area observer needs decoration authority')
        if not isinstance(data.get('windows'),list):raise ValueError('Invalid decoration snapshot')
        records={(w.get('address'),w.get('pid')):w for w in data.get('windows',[]) if isinstance(w,dict) and isinstance(w.get('address'),str) and type(w.get('pid')) is int}
        batch=[]
        for c,ident,signature in pending:
            record=records.get(ident)
            if not record or type(record.get('visible')) is not bool:continue
            if self.rules is not None:
                properties=self.b.kwin_rules.resolve(self.rules.rules,dict(c,kdeMetadata=record.get('kdeMetadata',{})))
                if any(properties.get(key,{}).get('mode')==2 for key in ('position','size','screen','desktops')):
                    self.done[ident]=signature;continue # Explicit KDE geometry policy wins.
            raw=record.get('borders',{}) if record['visible'] else dict.fromkeys(('left','top','right','bottom'),0)
            if not isinstance(raw,dict) or any(type(raw.get(k)) not in (int,float) or not math.isfinite(raw[k]) or raw[k]<0 for k in ('left','top','right','bottom')):continue
            borders=self.kw.bwm_windows.normalized_extents(raw)
            lua=command(c,signature[0][1],borders,self.kw)
            if lua is None:self.done[ident]=signature;self.attempts.pop(ident,None);continue
            _,count=self.attempts.get(ident,(signature,0))
            if count>=3:
                self.done[ident]=signature # Retry only after area/eligibility changes.
                self.log_error('Resize not confirmed after 3 attempts; respecting possible forced geometry policy')
                continue
            batch.append(lua);self.attempts[ident]=(signature,count+1)
            if len(batch)>=16:break
        if batch:
            body='\n'.join('local _area'+str(i)+'='+lua for i,lua in enumerate(batch))
            reply=self.b.run(['hyprctl','dispatch','(function() '+body+' return hl.dsp.no_op() end)()'],timeout=2)
            if reply.returncode:raise ValueError('Area observer resize failed; retry bounded')

    def close(self):
        if self.ready.is_symlink():return
        try:
            data=json.loads(self.ready.read_text())
            if isinstance(data,dict) and data.get('pid')==os.getpid() and data.get('processStart')==self.start_id:self.ready.unlink()
        except (OSError,ValueError):pass

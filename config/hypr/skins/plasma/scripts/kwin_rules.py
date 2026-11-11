"""BWM F10: independent adapter for KWin 6.7.5 rulesettings.kcfg/rules.cpp.

Reads the original format; never evaluates KDE values as Lua/shell code. The bridge owns
watch/lifecycle. Only mode Remember writes back, through its preserving atomic INI writer.
"""
from __future__ import annotations
import hashlib
import itertools
import importlib.util
from pathlib import Path
import json
import re
import time

PREFIX = 'bwm-kwin-rule-'
PROPERTIES = {'position','size','desktops','screen','maximizevert','maximizehoriz','minimize',
              'fullscreen','noborder','opacityactive','opacityinactive','acceptfocus','minsize','maxsize',
              'excludefromcapture'}
UNSUPPORTED = {'above','below','activity','skiptaskbar','skippager','skipswitcher','placement',
               'decocolor','blockcompositing','fsplevel','fpplevel','closeable','autogroup',
               'autogroupfg','autogroupid','strictgeometry','shortcut','disableglobalshortcuts',
               'desktopfile','ignoregeometry','layer','adaptivesync','tearing'}
FORCE_ONLY = {'opacityactive','opacityinactive','acceptfocus','minsize','maxsize'}
BOOL = {'maximizevert','maximizehoriz','minimize','fullscreen','noborder','acceptfocus','excludefromcapture'}


def decode(value):
    # KConfig string escaping (the regex backslash must itself be escaped in KConfig).
    return re.sub(r'\\(s|n|r|t|\\|,)', lambda m: {'s':' ','n':'\n','r':'\r','t':'\t','\\':'\\',',':','}[m[1]], value)


def klist(value):
    return [decode(x) for x in re.split(r'(?<!\\),', value) if x]


def integer(value, default=0):
    try: return int(value)
    except (TypeError,ValueError): return default


def value_for(key, raw):
    if key in BOOL:
        if raw.lower() not in ('true','false','1','0'): raise ValueError('boolean inválido')
        return raw.lower() in ('true','1')
    if key in ('position','size','minsize','maxsize'):
        pair = [int(x) for x in raw.split(',')]
        if len(pair)!=2 or any(abs(x)>100000 for x in pair): raise ValueError('geometría inválida')
        if key!='position' and min(pair)<=0: raise ValueError('tamaño inválido')
        return pair
    if key in ('opacityactive','opacityinactive'):
        n=int(raw)
        if not 0<=n<=100: raise ValueError('opacidad inválida')
        return n
    if key=='screen': return int(raw)
    return klist(raw)


def parse(text, ini):
    groups=ini(text);general=groups.get('General',{})
    order=klist(general.get('rules','')) or [str(i) for i in range(1,min(4096,integer(general.get('count')))+1)]
    rules=[];issues=[]
    for ident in order[:4096]:
        g=groups.get(ident,{})
        if not g or g.get('Enabled','true').lower() in ('false','0','no','off'): continue
        match={};blocked=False
        for field in ('wmclass','title','windowrole','clientmachine','tag'):
            mode=integer(g.get(field+'match'))
            if not mode: continue
            pattern=decode(g.get(field,''))
            if mode not in (1,2,3):
                issues.append(f'{ident}: {field}: coincidencia desconocida');blocked=True;continue
            try:
                if mode==3: re.compile(pattern)
            except re.error:
                issues.append(f'{ident}: {field}: expresión no válida');blocked=True;continue
            if field=='clientmachine' or (field=='wmclass' and g.get('wmclasscomplete','false').lower()=='true'):
                issues.append(f'{ident}: {field}: dato no expuesto por Hyprland; regla omitida');blocked=True
            match[field]={'mode':mode,'value':pattern}
        if blocked: continue  # Never broaden a rule whose selector cannot be represented.
        match['types']=integer(g.get('types'),0xffffffff)&0xffffffff
        if integer(g.get('hastransientparentmatch')):
            match['parent']=g.get('hastransientparent','false').lower()=='true'
        props={}
        for key in sorted(PROPERTIES|UNSUPPORTED):
            mode=integer(g.get(key+'rule'))
            if not mode: continue
            if key not in PROPERTIES or mode not in (1,2,3,4):
                issues.append(f'{ident}: {key}: modo {mode} no soportado')
                if key in PROPERTIES:props[key]={'mode':1,'value':None,'group':ident}
                continue
            if key in FORCE_ONLY and mode not in (1,2):
                issues.append(f'{ident}: {key}: KWin sólo admite Forzar');continue
            try: value=value_for(key,g.get(key,'false' if key in BOOL else '0' if key=='screen' else '')) if mode!=1 else None
            except (ValueError,TypeError):
                if mode==4 and key in ('position','size'):value=None
                else:
                    issues.append(f'{ident}: {key}: valor inválido')
                    props[key]={'mode':1,'value':None,'group':ident}
                    continue
            props[key]={'mode':mode,'value':value,'group':ident}
        rules.append({'id':ident,'match':match,'props':props})
    return rules,issues


def matches(rule, client):
    m=rule['match'];meta=client.get('kdeMetadata',{})
    for field in ('wmclass','title','windowrole','tag'):
        check=m.get(field)
        if not check: continue
        if field=='windowrole' and not meta.get('known'): return False
        values={'wmclass':client.get('class',''),'title':client.get('title',''),
                'windowrole':meta.get('role',''),'tag':','.join(str(t).rstrip('*') for t in client.get('tags',[]))}
        text=values[field];p=check['value'];mode=check['mode']
        if not (text==p if mode==1 else p in text if mode==2 else re.search(p,text) is not None): return False
    if m['types']!=0xffffffff:
        if not meta.get('known') or not (m['types']&int(meta.get('typeMask',0))): return False
    if 'parent' in m and (not meta.get('known') or bool(meta.get('parent'))!=m['parent']): return False
    return True


def resolve(rules, client):
    result={}
    for rule in rules:
        if matches(rule,client):
            for key,prop in rule['props'].items(): result.setdefault(key,prop)
    return result


def tag(key,value):
    return PREFIX+key+'-'+hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()[:12]


def effects(key,value):
    if key=='noborder': return {'decorate':not value, 'border_size':0} if value else {'decorate':True}
    if key=='acceptfocus': return {'no_focus':not value}
    if key=='excludefromcapture': return {'no_screen_share':value}
    if key in ('minsize','maxsize'): return {key.replace('size','_size'):f'{value[0]} {value[1]}'}
    if key=='opacity': return {'opacity':f'{value[0]/100:g} override {value[1]/100:g} override'}
    return {}


def native_cases(rules):
    cases={}
    active={100};inactive={100}
    for rule in rules:
        for key,p in rule['props'].items():
            if p['mode']==2 and key.startswith('opacity'):
                (active if key=='opacityactive' else inactive).add(p['value'])
            if p['mode']==2 and effects(key,p['value']): cases[tag(key,p['value'])]=effects(key,p['value'])
    # Native opacity takes both values; independent KWin properties must compose, not overwrite.
    for pair in itertools.product(active,inactive): cases[tag('opacity',pair)]=effects('opacity',pair)
    return cases


def generate(bridge):
    rules,issues=parse(bridge.read(bridge.CONFIG/'kwinrulesrc'),bridge.ini)
    lines=['-- BWM F10: generated from kwinrulesrc; loaded before user configuration.']
    for name,e in sorted(native_cases(rules).items()):
        fields=', '.join(f'{k} = {bridge.lua(v)}' for k,v in e.items())
        lines.append('hl.window_rule({ name = '+bridge.lua(name)+', match = { tag = '+bridge.lua(name)+' }, '+fields+' })')
    lines.append('return '+str(bool(rules)).lower())
    changed=bridge.atomic(bridge.STATE/'kwinrules.lua','\n'.join(lines)+'\n')
    bridge.atomic(bridge.STATE/'kwinrules-report.json',json.dumps({'issues':issues,'rules':len(rules)},ensure_ascii=False,indent=2)+'\n')
    return changed


def desired_tags(props):
    tags=set()
    for key,p in props.items():
        if p['mode']==2 and effects(key,p['value']): tags.add(tag(key,p['value']))
    a=props.get('opacityactive',{});i=props.get('opacityinactive',{})
    if a.get('mode',1)==2 or i.get('mode',1)==2:
        tags.add(tag('opacity',(a.get('value') if a.get('mode',1)==2 else 100,
                                i.get('value') if i.get('mode',1)==2 else 100)))
    return tags


class Runtime:
    """Lives in the single Breeze configuration bridge. Identity is always (address, PID)."""
    def __init__(self,bridge):
        self.b=bridge;self.seen={};self.last_text=None;self.rules=[];self.kw=None;self.monitors=[]

    def command(self,client,body):
        addr=json.dumps('address:'+client['address']);pid=int(client.get('pid') or 0)
        self.b.run(['hyprctl','dispatch',f'(function() local theme=package.loaded["modules.theme"]; if not theme or theme.name~="plasma" then return hl.dsp.no_op() end local w=hl.get_window({addr}); if not w or w.pid~={pid} then return hl.dsp.no_op() end for _,tag in ipairs(w.tags or {{}}) do if tag=="bwm-ignore-kwin-rules" or tag=="bwm-ignore-kwin-rules*" then return hl.dsp.no_op() end end {body} return hl.dsp.no_op() end)()'])

    def remember(self,entry):
        text=self.b.read(self.b.CONFIG/'kwinrulesrc');groups=self.b.ini(text);changes={}
        # Never save over a KCM edit made after this observation.
        for key,p in entry['props'].items():
            if p['mode']!=4: continue
            group=groups.get(p['group'],{})
            if group.get(key+'rule')!='4' or group.get(key,'')!=p['raw']: continue
            value=entry['values'].get(key)
            if value is not None: changes[p['group'],key]=value
        if changes: self.b.atomic(self.b.CONFIG/'kwinrulesrc',self.b.patch_ini(text,changes),text)

    def close(self):
        # Leaving the skin is like shutting down KWin: persist the last normal observation.
        for entry in self.seen.values():
            self.remember(entry)

    def tick(self):
        text=self.b.read(self.b.CONFIG/'kwinrulesrc')
        if text!=self.last_text:
            self.rules,_=parse(text,self.b.ini);self.last_text=text
        # No IPC on an empty ruleset unless we still have old tags to remove.
        if not self.rules and not self.seen: return
        result=self.b.run(['hyprctl','-j','clients'])
        if result.returncode: return
        try: clients=json.loads(result.stdout)
        except ValueError: return
        if not isinstance(clients,list): return
        identities={(c.get('address'),c.get('pid')) for c in clients}
        for ident in set(self.seen)-identities:
            self.remember(self.seen.pop(ident))
        # Remember the withdrawn instance before applying initial rules to a reused address.
        text=self.b.read(self.b.CONFIG/'kwinrulesrc')
        if text!=self.last_text:
            self.rules,_=parse(text,self.b.ini);self.last_text=text
        if any('screen' in r['props'] for r in self.rules):
            result=self.b.run(['hyprctl','-j','monitors'])
            try:self.monitors=json.loads(result.stdout)
            except ValueError:self.monitors=[]
            if not isinstance(self.monitors,list):self.monitors=[]
        metadata={}
        data=self.b.run(['hyprctl','-j','breezebars-csd'])
        try:
            metadata={(w['address'],w['pid']):w for w in json.loads(data.stdout).get('windows',[])}
        except (ValueError,TypeError,KeyError,AttributeError): pass
        for c in clients:
            ident=(c.get('address'),c.get('pid'))
            if not c.get('mapped',True) or not c.get('address'): continue
            c['kdeMetadata']=metadata.get(ident,{}).get('kdeMetadata',{})
            current={str(t).rstrip('*') for t in c.get('tags',[])}
            if 'bwm-ignore-kwin-rules' in current: continue  # User's last-loaded Lua can opt out.
            props=resolve(self.rules,c);desired=desired_tags(props)
            changes=['-'+t for t in current if (t.startswith(PREFIX) and t not in desired) or t=='bwm-kwin-new']
            changes+=['+'+t for t in desired-current]
            if changes:
                self.command(c,' '.join('hl.dispatch(hl.dsp.window.tag({tag='+json.dumps(t)+',window=w}))' for t in changes))
            old=self.seen.get(ident)
            initial=old is None and 'bwm-kwin-new' in current
            apply={k:p for k,p in props.items() if p['value'] is not None and (p['mode']==2 or (initial and p['mode'] in (3,4)))}
            space=c.get('workspace',{}).get('name','')
            if space=='special:minimized':
                self.apply(c,{k:p for k,p in apply.items() if k=='minimize'})
            elif not space.startswith('special:'):
                self.apply(c,apply)
            # Remember only supported mutable state; tiled/maximized geometry is not restore geometry.
            values={**(old.get('values',{}) if old else {}),**self.snapshot(c,metadata.get(ident,{}))}
            for k,p in props.items(): p=dict(p);p['raw']=self.b.ini(text).get(p['group'],{}).get(k,'');props[k]=p
            self.seen[ident]={'props':props,'values':values}

    def snapshot(self,c,frame):
        tags={str(t).rstrip('*') for t in c.get('tags',[])}
        border=frame.get('borders',{}) if frame.get('visible') else {}
        x,y=c.get('at',[0,0]);w,h=c.get('size',[1,1])
        b=[border.get(k,0) for k in ('left','top','right','bottom')]
        out={'noborder':str('bwm-no-border' in tags or not frame.get('observed',{}).get('decorate',True)).lower(),
             'fullscreen':str(c.get('fullscreen')==2).lower(),
             'maximizevert':str('bwm-max-v' in tags).lower(),'maximizehoriz':str('bwm-max-h' in tags).lower(),
             'minimize':str(c.get('workspace',{}).get('name')=='special:minimized').lower()}
        ws=c.get('workspace',{}).get('id',0)
        if ws>=1:out['desktops']=self.b.merged('kwinrc').get('Desktops',{}).get(f'Id_{ws}',str(ws))
        saved=self.b.load_json(self.b.STATE/'kwin-screens.json',[])
        monitor=next((m for m in self.monitors if m.get('id')==c.get('monitor')),None)
        if monitor and monitor.get('description') in saved:out['screen']=str(saved.index(monitor['description']))
        if not c.get('fullscreen') and not (tags&{'snapped','bwm-max-v','bwm-max-h'}):
            out.update(position=f'{round(x-b[0])},{round(y-b[1])}',size=f'{round(w+b[0]+b[2])},{round(h+b[1]+b[3])}')
        return out

    def apply(self,c,props):
        if not props:return
        if self.kw is None:
            spec=importlib.util.spec_from_file_location('bwm_kwin_rules_window',Path(__file__).with_name('kwin-window.py'))
            self.kw=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.kw)
        self.kw.run_lua=lambda code:self.command(c,'hl.dispatch('+code+')')
        body=[];tags={str(t).rstrip('*') for t in c.get('tags',[])}
        def val(key):return props.get(key,{}).get('value')
        # Desktop first, geometry second. UUIDs come from BWM's exported Desktops/Id_N.
        if 'desktops' in props:
            ids=val('desktops');desktops=self.b.merged('kwinrc').get('Desktops',{})
            ws=next((i for i in range(1,257) if desktops.get(f'Id_{i}') in ids),None)
            if ws is None: ws=next((integer(s) for s in ids if str(s).isdigit() and integer(s)>0),None)
            if ws and c.get('workspace',{}).get('id')!=ws:
                body.append(f'hl.dispatch(hl.dsp.window.move({{workspace={ws},follow=false,window=w}}))')
        if 'screen' in props and 'desktops' not in props:
            result=self.b.run(['hyprctl','-j','monitors'])
            try: monitors=json.loads(result.stdout)
            except ValueError: monitors=[]
            idx=val('screen')
            saved=self.b.load_json(self.b.STATE/'kwin-screens.json',[])
            target=next((m for m in monitors if 0<=idx<len(saved) and m.get('description')==saved[idx]),None)
            if target and c.get('monitor')!=target['id']:
                ws=target.get('activeWorkspace',{}).get('id')
                if ws: body.append(f'hl.dispatch(hl.dsp.window.move({{workspace={int(ws)},follow=false,window=w}}))')
        if 'size' in props and c.get('fullscreen')!=2:
            size=val('size');b=self.kw.window_borders(c)
            width=max(1,size[0]-b['left']-b['right']);height=max(1,size[1]-b['top']-b['bottom'])
            if c.get('size')!=[width,height]:body.append(f'hl.dispatch(hl.dsp.window.resize({{x={width},y={height},relative=false,window=w}}))')
        if 'position' in props and c.get('fullscreen')!=2:
            x,y=val('position');b=self.kw.window_borders(c);x+=b['left'];y+=b['top']
            if c.get('at')!=[x,y]:body.append(f'hl.dispatch(hl.dsp.window.move({{x={x},y={y},relative=false,window=w}}))')
        for key,state_tag in (('noborder','bwm-no-border'),('excludefromcapture','bwm-no-capture')):
            if key in props and props[key]['mode'] in (3,4) and (state_tag in tags)!=bool(val(key)):
                sign='+' if val(key) else '-'
                body.append('hl.dispatch(hl.dsp.window.tag({tag='+json.dumps(sign+state_tag)+',window=w}))')
        if body:
            self.command(c,' '.join(body))
            fresh=self.kw.find_client(c['address'])
            if not fresh or fresh.get('pid')!=c.get('pid'):return
            c=fresh
        if 'fullscreen' in props and bool(c.get('fullscreen')==2)!=val('fullscreen'):
            self.command(c,"hl.dispatch(hl.dsp.window.fullscreen({mode=0,action='"+('set' if val('fullscreen') else 'unset')+"',window=w}))")
        old=self.kw.mode_from_tags(c.get('tags'));mode=old
        if 'maximizevert' in props:mode=(mode|1) if val('maximizevert') else (mode&~1)
        if 'maximizehoriz' in props:mode=(mode|2) if val('maximizehoriz') else (mode&~2)
        if mode!=old:
            request={0:'restore',3:'full'}.get(mode)
            if request:self.kw.maximize(c,request)
            else:
                if (mode^old)==3:
                    self.kw.maximize(c,'restore');c=self.kw.find_client(c['address'])
                    if not c:return
                self.kw.maximize(c,'vertical' if mode==1 else 'horizontal')
        elif mode and any(props.get(key,{}).get('mode')==2 for key in ('maximizevert','maximizehoriz')) and c.get('fullscreen')!=2:
            # A forced maximized axis must resist manual resizing and monitor/workarea changes.
            # Keep F8's restore geometry; do not re-save an already-maximized frame.
            area=self.kw.work_area(c)
            if area:
                borders=self.kw.window_borders(c);frame=list(self.kw.frame_from_client(c,borders))
                if mode&1:frame[1],frame[3]=area[1],area[3]
                if mode&2:frame[0],frame[2]=area[0],area[2]
                x,y,w,h=self.kw.content_from_frame(frame,borders)
                if c.get('at')!=[x,y] or c.get('size')!=[w,h]:
                    self.command(c,f'hl.dispatch(hl.dsp.window.resize({{x={int(w)},y={int(h)},relative=false,window=w}})) hl.dispatch(hl.dsp.window.move({{x={int(x)},y={int(y)},relative=false,window=w}}))')
        if 'minimize' in props:
            tm=self.kw.minimizer();is_min=tm.is_minimized(c)
            tm.run_lua=lambda code:self.command(c,'hl.dispatch('+code+')')
            if bool(is_min)!=val('minimize'):
                tm.minimize_win(c) if val('minimize') else tm.restore_win(c)

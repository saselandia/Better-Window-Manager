"""BWM F10: original KWin Tiling tree in kwinrc, adapted to Hyprland monitors.

Tile JSON is exactly KWin 6.7.5 TileManager::tileToJSon. Output UUID associations (because
KWin assigns random UUIDs not available in Hyprland) are separate machine state keyed by desc.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import uuid

DEFAULT={'layoutDirection':'horizontal','tiles':[{'width':.25},{'width':.5},{'width':.25}]}


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def leaves(tree,area=(0.,0.,1.,1.),path=(),depth=0):
    if depth>16 or not isinstance(tree,dict):raise ValueError('Árbol de mosaico inválido')
    children=tree.get('tiles',[])
    if not children:return [{'path':list(path),'x':area[0],'y':area[1],'width':area[2],'height':area[3]}]
    if not isinstance(children,list) or len(children)>128:raise ValueError('Demasiadas zonas')
    direction=tree.get('layoutDirection','floating')
    if direction not in ('horizontal','vertical','floating'):raise ValueError('Dirección de mosaico inválida')
    result=[];x,y,w,h=area;offset=0.
    for i,child in enumerate(children):
        if not isinstance(child,dict):raise ValueError('Zona inválida')
        if direction in ('horizontal','vertical'):
            length=w if direction=='horizontal' else h
            value=child.get('width' if direction=='horizontal' else 'height',length-offset)
            if not finite(value) or value<=0 or offset>=length:raise ValueError('Proporción inválida')
            value=min(value,length-offset)
            if i==len(children)-1:value=length-offset # KWin fills the remaining parent area.
            rect=(x+offset,y,value,h) if direction=='horizontal' else (x,y+offset,w,value)
            offset+=value
        else:
            rect=tuple(child.get(k,0 if k in ('x','y') else 1) for k in ('x','y','width','height'))
            if not all(finite(v) for v in rect) or min(rect[:2])<0 or min(rect[2:])<=0 or rect[0]+rect[2]>1.000001 or rect[1]+rect[3]>1.000001:
                raise ValueError('Zona flotante fuera de la pantalla')
        result+=leaves(child,rect,path+(i,),depth+1)
        if len(result)>256:raise ValueError('Demasiadas zonas')
    return result


def split(tree,path,direction):
    tree=copy.deepcopy(tree);node=tree
    for i in path:node=node['tiles'][i]
    if node.get('tiles'):raise ValueError('Selecciona una zona hoja')
    rect=next(r for r in leaves(tree) if r['path']==path)
    key='width' if direction=='horizontal' else 'height'
    node['layoutDirection']=direction;node['tiles']=[{key:rect[key]/2},{key:rect[key]/2}]
    return tree


def join(tree,path):
    tree=copy.deepcopy(tree);node=tree
    for i in path[:-1]:node=node['tiles'][i]
    node.pop('tiles',None);node.pop('layoutDirection',None)
    return tree


def resize_split(tree,path,ratio):
    if not finite(ratio) or not .1<=ratio<=.9:raise ValueError('Proporción fuera de 10–90 %')
    if not path:raise ValueError('Selecciona una zona')
    tree=copy.deepcopy(tree);node=tree
    for i in path[:-1]:node=node['tiles'][i]
    children=node.get('tiles',[]);direction=node.get('layoutDirection')
    if len(children)<2 or direction not in ('horizontal','vertical'):
        raise ValueError('La proporción requiere una división horizontal o vertical')
    key='width' if direction=='horizontal' else 'height';axis='x' if direction=='horizontal' else 'y'
    rects=leaves(tree);parent=path[:-1]
    lengths=[]
    for i in range(len(children)):
        prefix=parent+[i];parts=[r for r in rects if r['path'][:len(prefix)]==prefix]
        lengths.append(max(r[axis]+r[key] for r in parts)-min(r[axis] for r in parts))
    total=sum(lengths);selected=path[-1];others=total-lengths[selected]
    for i,child in enumerate(children):
        child[key]=total*ratio if i==selected else lengths[i]/others*total*(1-ratio)
    return tree


def output_key(bridge,monitor):
    mapping=bridge.load_json(bridge.STATE/'tiling-outputs.json')
    value=mapping.get(monitor['description'])
    return value or str(uuid.uuid5(uuid.NAMESPACE_URL,'https://bwm.local/output/'+monitor['description']))


def desktop_key(groups,workspace):
    return groups.get('Desktops',{}).get(f'Id_{workspace}') or str(uuid.uuid5(uuid.NAMESPACE_URL,f'https://bwm.local/desktop/{workspace}'))


def inspect(bridge,monitor,workspace,output=None):
    text=bridge.read(bridge.CONFIG/'kwinrc');groups=bridge.ini(text)
    desktop=desktop_key(groups,workspace);output=output or output_key(bridge,monitor)
    group=f'Tiling][{desktop}][{output}'
    # Plasma <6.7 used Tiling/output without the per-desktop subgroup.
    g=groups.get(group,groups.get('Tiling]['+output,{}))
    raw=g.get('tiles');tree=json.loads(raw) if raw else copy.deepcopy(DEFAULT)
    padding=int(g.get('padding',groups.get('Tiling',{}).get('padding',4)))
    rects=leaves(tree)
    choices=[]
    for name,values in groups.items():
        if name.startswith('Tiling][') and 'tiles' in values:
            choices.append(name.split('][')[-1])
    return {'description':monitor['description'],'workspace':workspace,'output':output,'desktop':desktop,
            'tree':tree,'leaves':rects,'padding':max(0,min(100,padding)),
            'outputs':sorted(set(choices+[output])),
            'revision':hashlib.sha256(text.encode()).hexdigest()}


def save(bridge,data):
    leaves(data['tree']);padding=data['padding']
    if not finite(padding) or not 0<=padding<=100:raise ValueError('Separación inválida')
    # UUID only: no INI section/key injection from the editor or command line.
    output=str(uuid.UUID(data['output']));desktop=str(uuid.UUID(data['desktop']));workspace=int(data['workspace'])
    if not 1<=workspace<=256:raise ValueError('Escritorio inválido')
    text=bridge.read(bridge.CONFIG/'kwinrc')
    if hashlib.sha256(text.encode()).hexdigest()!=data['revision']:raise ValueError('KDE cambió durante la edición; vuelve a abrir el editor')
    group=f'Tiling][{desktop}][{output}'
    updates={(group,'tiles'):json.dumps(data['tree'],separators=(',',':')),(group,'padding'):str(round(padding)),
             ('Desktops',f'Id_{workspace}'):desktop}
    bridge.atomic(bridge.CONFIG/'kwinrc',bridge.patch_ini(text,updates),text)
    mapping=bridge.load_json(bridge.STATE/'tiling-outputs.json');mapping[data['description']]=output
    bridge.save_json(bridge.STATE/'tiling-outputs.json',mapping)


def generate(bridge):
    result=bridge.run(['hyprctl','-j','monitors'])
    try:monitors=json.loads(result.stdout)
    except ValueError:monitors=[]
    if not isinstance(monitors,list):monitors=[]
    saved=bridge.load_json(bridge.STATE/'kwin-screens.json',[])
    if not isinstance(saved,list):saved=[]
    for m in monitors:
        if m.get('description') and m['description'] not in saved:saved.append(m['description'])
    bridge.save_json(bridge.STATE/'kwin-screens.json',saved)
    groups=bridge.merged('kwinrc');count=int(groups.get('Desktops',{}).get('Number',1));rows=[]
    for monitor in monitors:
        if not monitor.get('description'):continue
        for workspace in range(1,min(256,count)+1):
            try:data=inspect(bridge,monitor,workspace)
            except (ValueError,TypeError,KeyError):continue
            for rect in data['leaves']:
                fields={k:v for k,v in rect.items() if k!='path'}
                fields.update(description=monitor['description'],workspace=workspace,padding=data['padding'])
                rows.append('{'+', '.join(f'{key}={bridge.lua(value)}' for key,value in fields.items())+'}')
    content='-- BWM F10: KWin tiles; output association uses desc, never DP-N.\nif hl.plugin and hl.plugin.breezebars and hl.plugin.breezebars.snap_tiles then\n hl.plugin.breezebars.snap_tiles({'+',\n'.join(rows)+'})\nend\n'
    return bridge.atomic(bridge.STATE/'kwintiles.lua',content)


def padded_frame(leaf,area,padding):
    x,y,w,h=area
    l=padding/2 if leaf['x']>0 else padding;t=padding/2 if leaf['y']>0 else padding
    r=padding/2 if leaf['x']+leaf['width']<1 else padding;b=padding/2 if leaf['y']+leaf['height']<1 else padding
    # C++ std::round matches floor(n+.5), not Python's ties-to-even.
    rnd=lambda n:math.floor(n+.5) if n>=0 else math.ceil(n-.5)
    left=rnd(x+leaf['x']*w);top=rnd(y+leaf['y']*h)
    right=rnd(x+(leaf['x']+leaf['width'])*w);bottom=rnd(y+(leaf['y']+leaf['height'])*h)
    return [left+l,top+t,max(1,right-left-l-r),max(1,bottom-top-t-b)]

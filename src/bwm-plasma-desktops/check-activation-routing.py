#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run original Hyprland 0.56.2 action bodies with data-only focus/pointer scaffolding.

Compiles the actual BWM applyExact body and WorkspaceActivator. No compositor,
Wayland client, plugin loading, windows or real pointer movement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT/'tests/upstream/Hyprland-0.56.2-WorkspaceActions.cpp'
UPSTREAM_SHA256 = 'b168802c7436b44b0d8f48b208b9c928cb585790c674bea7f6f88426ce18bc49'


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    end, depth = opening+1, 1
    while depth:
        depth += (source[end] == '{')-(source[end] == '}')
        end += 1
    return source[opening+1:end-1]


SCAFFOLD = r'''
#include "activation.h"
#include <cassert>
#include <expected>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
struct Monitor;struct Workspace;struct Window;
using PHLMONITOR=std::shared_ptr<Monitor>;
using PHLWORKSPACE=std::shared_ptr<Workspace>;
using PHLWINDOW=std::shared_ptr<Window>;
template<class T>struct Ref {
 std::shared_ptr<T> value;Ref()=default;Ref(std::shared_ptr<T> p):value(p){}
 auto lock()const{return value;}T*operator->()const{return value.get();}
 friend bool operator==(const Ref&a,const std::shared_ptr<T>&b){return a.value==b;}
 friend bool operator==(const std::shared_ptr<T>&a,const Ref&b){return a==b.value;}
};
struct Vector2D {int output=0;};
int noWarps=0,followMouse=2,hideSpecial=0,centerOn=0,warpOnWorkspace=0;
int focusCalls=0,workspaceCalls=0,simulated=0;
template<class T>struct CConfigValue {
 std::string key;CConfigValue(const char*k):key(k){}
 int operator*()const{
  if(key=="cursor:no_warps")return noWarps;
  if(key=="input:follow_mouse")return followMouse;
  if(key=="binds:hide_special_on_workspace_change")return hideSpecial;
  if(key=="binds:workspace_center_on")return centerOn;
  if(key=="cursor:warp_on_change_workspace")return warpOnWorkspace;
  assert(false);return 0;
 }
};
namespace Config {
 using INTEGER=int;
 namespace Actions {
 enum class eActionErrorLevel {WARNING};enum class eActionErrorCode {NO_TARGET,INVALID_STATE};
 using ActionResult=std::expected<int,int>;
 inline auto actionError(const char*,eActionErrorLevel,eActionErrorCode){return std::unexpected(1);}
 ActionResult focusMonitor(PHLMONITOR);
 ActionResult changeWorkspace(PHLWORKSPACE);
 }
}
using Config::Actions::ActionResult;
using Config::Actions::actionError;
using Config::Actions::eActionErrorLevel;
using Config::Actions::eActionErrorCode;
namespace Actions=Config::Actions;
struct Focus {
 PHLMONITOR mon;bool hasSurface=false;
 PHLMONITOR monitor(){return mon;}
 void rawMonitorFocus(PHLMONITOR p){mon=p;}
 void rawWindowFocus(PHLWINDOW,int);
 void fullWindowFocus(PHLWINDOW,int);
 bool surface(){return hasSurface;}
} focus;
namespace Desktop {
 constexpr int FOCUS_REASON_KEYBIND=0;
 Focus*focusState(){return &focus;}
 namespace View {
 constexpr int VIEW_TYPE_WINDOW=1;
 struct View {int type(){return VIEW_TYPE_WINDOW;}};
 struct CWLSurface {
  template<class T>static CWLSurface*fromResource(T){return nullptr;}
  View*view(){static View v;return &v;}
 };
 }
}
struct Monitor {
 int number,m_id=0;std::string m_name;PHLWORKSPACE m_activeWorkspace,m_activeSpecialWorkspace;
 Vector2D middle(){return {number};}
 void setSpecialWorkspace(PHLWORKSPACE w){m_activeSpecialWorkspace=w;}
 void changeWorkspace(PHLWORKSPACE w,bool=false,bool=false){
  // CMonitor::changeWorkspace returns before focus work when already active.
  if(w==m_activeWorkspace)return;
  ++workspaceCalls;m_activeWorkspace=w;
 }
};
struct Workspace {
 int m_id;bool m_isSpecialWorkspace=false;Ref<Monitor>m_monitor;PHLWINDOW candidate;
 bool inert(){return false;}
 PHLWINDOW getFocusCandidate(){return candidate;}
 PHLWINDOW getLastFocusedWindow(){return candidate;}
};
struct PointerController {
 PHLMONITOR pointed;
 void warpTo(Vector2D pos);
} pointer;
struct Window {
 Ref<Monitor>owner;
 Vector2D middle(){return owner.lock()->middle();}
 void warpCursor(int=0){pointer.warpTo(middle());}
};
void Focus::rawWindowFocus(PHLWINDOW w,int){hasSurface=bool(w);if(w)mon=w->owner.lock();}
void Focus::fullWindowFocus(PHLWINDOW w,int reason){rawWindowFocus(w,reason);}
struct Input {
 bool m_lastFocusOnLS=false;PHLWINDOW m_forcedFocus;
 void unconstrainMouse(){}
 void sendMotionEventsToFocused(){}
 void simulateMouseMovement(){
  ++simulated;
  if(m_forcedFocus)focus.fullWindowFocus(m_forcedFocus,0);
  else focus.rawMonitorFocus(pointer.pointed);
 }
} input;
Input*g_pInputManager=&input;
struct Seat {struct {std::weak_ptr<int>pointerFocus;}m_state;}seat;
Seat*g_pSeatManager=&seat;
namespace Pointer {PointerController*pointerController(){return &pointer;}}
struct Workspaces {
 std::vector<Ref<Workspace>> items;
 const auto&workspaces(){return items;}
 PHLWORKSPACE create(int, int,const std::string&){return {};}
} workspaces;
struct Monitors {
 std::vector<PHLMONITOR>items;const auto&monitors(){return items;}
} monitors;
namespace State {
 Workspaces*workspaceState(){return &workspaces;}
 Monitors*monitorState(){return &monitors;}
}
void PointerController::warpTo(Vector2D pos){
 if(noWarps)return;
 for(const auto&m:monitors.items)if(m->number==pos.output)pointed=m;
}
void updateRelativeCursorCoords(){}
struct Extension {
 std::string lastActivationError;
 static int number(const std::string&s){return std::stoi(s);}
 bool applyExact(const std::string&,const std::string&);
};
'''

MAIN = r'''
int main(){
 using namespace BwmPlasma;
 int cases=0,reproduced=0;
 for(int warps:{0,1})for(int follows:{0,1,2})for(bool empty:{false,true})for(bool visible:{false,true})for(bool cross:{false,true}){
  auto a=std::make_shared<Monitor>();a->number=0;a->m_name="A";
  auto b=std::make_shared<Monitor>();b->number=1;b->m_name="B";
  auto one=std::make_shared<::Workspace>();one->m_id=1;one->m_monitor=a;a->m_activeWorkspace=one;
  auto two=std::make_shared<::Workspace>();two->m_id=2;two->m_monitor=b;b->m_activeWorkspace=two;
  auto owner=cross?b:a;
  auto target=visible?owner->m_activeWorkspace:std::make_shared<::Workspace>();
  if(!visible){target->m_id=3;target->m_monitor=owner;}
  if(!empty){auto w=std::make_shared<Window>();w->owner=owner;target->candidate=w;}
  workspaces.items={one,two};if(!visible)workspaces.items.push_back(target);
  monitors.items={a,b};
  const auto reset=[&]{
   a->m_activeWorkspace=one;b->m_activeWorkspace=two;focus.mon=a;focus.hasSurface=false;pointer.pointed=a;
   noWarps=warps;followMouse=follows;simulated=focusCalls=workspaceCalls=0;
  };
  reset();
  if(cross && visible && empty && noWarps){
   // Original BWM integration: native focus followed by native workspace action.
   assert(Actions::focusMonitor(owner));assert(Actions::changeWorkspace(target));
   assert(focus.mon==a);++reproduced;
  }
  reset();Extension extension;
  WorkspaceActivator activation([&]{
   return std::optional(ActivationState{focus.mon->m_name,{{"A",a->m_activeWorkspace->m_id},{"B",b->m_activeWorkspace->m_id}}});
  },[&](const auto&id,const auto&output){return extension.applyExact(id,output);});
  const bool result=activation.activate(std::to_string(target->m_id),owner->m_name);
  if(visible){
   assert(result && focus.mon==owner);
   assert(a->m_activeWorkspace==one && b->m_activeWorkspace==two);
   assert(workspaceCalls==0); // No second workspace action on an active desktop.
  }else{
   assert(owner->m_activeWorkspace==target && workspaceCalls==1);
   // Preserve upstream behavior and strict readback for inactive/empty targets;
   // do not silently force a different cursor/focus policy to make the test pass.
   const bool nativeMismatch=cross && empty && noWarps;
   assert(result!=nativeMismatch);
   assert((activation.outcome()=="activation-readback-mismatch")==nativeMismatch);
  }
  if(noWarps)assert(pointer.pointed==a); // Never override the user's no-warps setting.
  ++cases;
 }
 assert(cases==48 && reproduced==3);
 std::cout<<"{\"cases\":"<<cases<<",\"legacyEmptyTargetNoWarpFailuresReproduced\":"<<reproduced
          <<",\"activeWorkspaceRoutingPassed\":true,\"readbackGuardPreserved\":true}\n";
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--asan', action='store_true')
    args = parser.parse_args()
    report = {'version': 1, 'passed': False, 'sessionModified': False,
              'hyprlandPluginLoaded': False, 'realCompositorVerified': False, 'asan': args.asan}
    try:
        original = UPSTREAM.read_text()
        if hashlib.sha256(original.encode()).hexdigest() != UPSTREAM_SHA256:
            raise ValueError('Unreviewed Hyprland action source fixture')
        body = function((ROOT/'plugin.cpp').read_text(), 'bool applyExact(')
        with tempfile.TemporaryDirectory(prefix='bwm-activation-routing-') as tmp:
            root = Path(tmp);source = root/'routing.cpp';binary = root/'routing'
            source.write_text(SCAFFOLD+original+'\nbool Extension::applyExact(const std::string&id,const std::string&output){'+body+'}\n'+MAIN)
            command = [args.compiler, '-std=c++23', '-O1', '-g', '-fno-omit-frame-pointer']
            if args.asan:command += ['-fsanitize=address']
            compiled = subprocess.run(command+['-I', str(ROOT), str(source), str(ROOT/'activation.cpp'), '-o', str(binary)],
                                      capture_output=True, text=True, timeout=30)
            if compiled.returncode:raise RuntimeError(compiled.stderr[:5000])
            checked = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
            if checked.returncode:raise RuntimeError(checked.stderr[-3000:])
            report.update(passed=True, result=json.loads(checked.stdout), originalSha256=UPSTREAM_SHA256)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

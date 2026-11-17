#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile the actual upstream init/monitor-change bodies before and after the patch.

The monitor/event-loop scaffolding is data-only. No Hyprland process, session or
capture is started. The fixture retains Hyprland's original BSD license in notices.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).parent/'tests/upstream/Hyprland-0.56.2-ScreenshareSession.cpp'
SYSTEM_SOURCE=Path(__file__).parent/'tests/upstream/Hyprland-0.56.2-SystemInfo.cpp'
PATCH=ROOT/'patches/hyprland/0.56.2-screenshare-monitor-guard.patch'
SESSION_PATH='src/managers/screenshare/ScreenshareSession.cpp'
SYSTEM_PATH='src/helpers/SystemInfo.cpp'
HEADER_PATH='src/managers/screenshare/BwmCaptureGuard.hpp'

def patched_tree(originals,patch):
    results=dict(originals);lines=patch.splitlines(True);i=0
    while i<len(lines):
        if not lines[i].startswith('--- '):raise ValueError('Missing old patch path')
        old=lines[i][4:].strip();i+=1
        if not lines[i].startswith('+++ b/'):raise ValueError('Unexpected patch target')
        path=lines[i][6:].strip();i+=1
        if path not in (SESSION_PATH,SYSTEM_PATH,HEADER_PATH):raise ValueError('Unreviewed patch target')
        if old!='a/'+path and old!='/dev/null':raise ValueError('Unexpected old patch path')
        original=('' if old=='/dev/null' else originals[path]).splitlines(True);output=[];cursor=0
        while i<len(lines) and not lines[i].startswith('--- '):
            match=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);i+=1
            if not match:raise ValueError('Unexpected patch line')
            start=max(0,int(match[1])-1)
            if start<cursor:raise ValueError('Overlapping patch hunks')
            output.extend(original[cursor:start]);cursor=start;oldCount=newCount=0
            while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
                item=lines[i];i+=1
                if item.startswith((' ','-')):
                    if cursor>=len(original) or original[cursor]!=item[1:]:raise ValueError('Patch context differs from reviewed original')
                    cursor+=1;oldCount+=1
                if item.startswith((' ','+')):output.append(item[1:]);newCount+=1
            if oldCount!=int(match[2] or 1) or newCount!=int(match[4] or 1):raise ValueError('Patch hunk count mismatch')
        output.extend(original[cursor:]);results[path]=''.join(output)
    return results

def patched_source(source,patch):
    return patched_tree({SESSION_PATH:source,SYSTEM_PATH:SYSTEM_SOURCE.read_text()},patch)[SESSION_PATH]

def body(source,needle):
    start=source.index(needle)+len(needle);depth=1;i=start
    while depth:
        if source[i]=='{':depth+=1
        elif source[i]=='}':depth-=1
        i+=1
    return source[start:i-1]

SCAFFOLD=r'''
#include <cassert>
#include <chrono>
#include <memory>
#include <cstdint>
#include <string>
#include <iostream>
#include <unistd.h>
#define LOGM(...) (void)0
namespace Log {enum {TRACE};}
template<class T>using SP=std::shared_ptr<T>;
template<class T,class... A>auto makeShared(A&&... a){return std::make_shared<T>(std::forward<A>(a)...);}
struct CEventLoopTimer {template<class F>CEventLoopTimer(std::chrono::milliseconds,F,void*){}};
struct Signal {volatile int attached=0;template<class F>int listen(F){attached=attached+1;return attached;}void emit(){}};
struct Monitor {double m_scale=1;struct {Signal disconnect,modeChanged;}m_events;};
struct Weak {bool expired()const{return true;}void *get()const{return nullptr;}};
struct Box {volatile double scaleValue=0;Box& scale(double value){scaleValue=value;return *this;}Box& round(){return *this;}};
struct Loop {int added=0;void addTimer(SP<CEventLoopTimer>){++added;}} loop;
Loop *g_pEventLoopManager=&loop;
constexpr int SHARE_WINDOW=1;
class CScreenshareSession {
public:
 int m_type=SHARE_WINDOW;Weak m_window,m_monitor;std::string m_name;
 bool m_stopped=false,drop=false;int calls=0,constraints=0;
 SP<Monitor> available;SP<CEventLoopTimer>m_shareStopTimer;Box m_captureBox;
 struct {int monitorDestroyed=0,monitorModeChanged=0;}m_listeners;
 struct {Signal constraintsChanged;}m_events;
 SP<Monitor>monitor(){++calls;auto copy=available;if(drop)available.reset();return copy;}
 void stop(){m_stopped=true;}void screenshareEvents(bool){}void calculateConstraints(){++constraints;}
 void init();void changed();
};
'''
VERSION_SCAFFOLD=r'''
#include <format>
#include <algorithm>
#include <string_view>
enum class eHyprCtlOutputFormat {FORMAT_NORMAL,FORMAT_JSON};
namespace Helpers::SystemInfo {std::string getVersion(eHyprCtlOutputFormat);}
#define ISDEBUG 0
#define GIT_COMMIT_MESSAGE "Own fixture"
#define HYPRLAND_VERSION "0.56.2"
#define GIT_BRANCH "fixture"
#define GIT_COMMIT_HASH "own-fixture-commit"
#define GIT_DIRTY "clean"
#define GIT_COMMIT_DATE "fixture"
#define GIT_TAG "v0.56.2"
#define GIT_COMMITS "0"
#define AQUAMARINE_VERSION "fixture"
#define HYPRLANG_VERSION "fixture"
#define HYPRUTILS_VERSION "fixture"
#define HYPRCURSOR_VERSION "fixture"
#define HYPRGRAPHICS_VERSION "fixture"
std::string trim(const std::string& s){return s;}
std::string escapeJSONStrings(const std::string& s){return s;}
std::string getBuiltSystemLibraryNames(){return "own-fixture-libraries";}
std::string getSystemLibraryVersion(const std::string&){return "fixture";}
std::string __hyprland_api_get_hash(){return "own-fixture-ABI";}
void trimTrailingComma(std::string& s){if(!s.empty() && s.back()==',')s.pop_back();}
'''
MAIN=r'''
int main(int argc,char **argv){
 assert(argc==2);const std::string test=argv[1];CScreenshareSession s;
 if(test=="report"){std::cout<<Helpers::SystemInfo::getVersion(eHyprCtlOutputFormat::FORMAT_JSON);return 0;}
 if(test=="valid-init" || test=="drop-init" || test=="valid-change" || test=="drop-change" || test=="stopped-change")s.available=std::make_shared<Monitor>();
 s.drop=test.starts_with("drop");s.m_stopped=test=="stopped-change";
 if(test.ends_with("init"))s.init();else s.changed();
 if(test.starts_with("null")){assert(s.m_stopped);assert(s.m_listeners.monitorDestroyed==0);assert(s.m_listeners.monitorModeChanged==0);}
 else if(test=="stopped-change"){assert(s.calls==0);assert(s.m_listeners.monitorDestroyed==0);}
 else {assert(!s.m_stopped);assert(s.calls==1);assert(s.m_listeners.monitorDestroyed==1);assert(s.m_listeners.monitorModeChanged==1);assert(s.constraints==1);}
 return 0;
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--asan',action='store_true');a=p.parse_args()
    report={'version':1,'sessionModified':False,'fullHyprlandBuildVerified':False,'installed':False,'runtimeVerified':False}
    source=SOURCE.read_text()
    if hashlib.sha256(source.encode()).hexdigest()!='b6b2ce5d682080131f374510e7cecae54925356bea541ef99feeff3aba394c99':raise ValueError('Unreviewed Hyprland source fixture')
    system=SYSTEM_SOURCE.read_text()
    if hashlib.sha256(system.encode()).hexdigest()!='d8bc38f86d8cb89b10616a4ac42fe4feb32e257e7fb03167277b7a69f867dc12':raise ValueError('Unreviewed SystemInfo source fixture')
    report['systemInfoOriginalSha256']=hashlib.sha256(system.encode()).hexdigest()
    tree=patched_tree({SESSION_PATH:source,SYSTEM_PATH:system},PATCH.read_text());patched=tree[SESSION_PATH]
    report['originalSha256']=hashlib.sha256(source.encode()).hexdigest();report['patchedSha256']=hashlib.sha256(patched.encode()).hexdigest()
    def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    try:
        with tempfile.TemporaryDirectory(prefix='bwm-screenshare-guard-') as tmp:
            root=Path(tmp)
            for label,text in [('before',source),('after',patched)]:
                init=body(text,'void CScreenshareSession::init() {')
                change=body(text,'m_listeners.windowMonitorChanged = m_window->m_events.monitorChanged.listen([this]() {')
                marker=re.search(r'\[\[gnu::used, gnu::retain\]\] const char BWM_SCREENSHARE_GUARD\[\] = "BWM_SCREENSHARE_MONITOR_GUARD_V1";',text).group(0) if label=='after' else ''
                guard=tree[HEADER_PATH]+'\nint Screenshare::bwmMonitorGuardVersion(){'+body(patched,'int Screenshare::bwmMonitorGuardVersion() {')+'}\n' if label=='after' else ''
                versionSource=tree[SYSTEM_PATH] if label=='after' else system
                version=versionSource[versionSource.index('std::string SystemInfo::getVersion('):versionSource.index('std::string SystemInfo::getSystemInfo()')].replace('SystemInfo::getVersion(', 'Helpers::SystemInfo::getVersion(', 1)
                cpp=root/(label+'.cpp');binary=root/label
                cpp.write_text(SCAFFOLD+VERSION_SCAFFOLD+marker+guard+version+'\nvoid CScreenshareSession::init(){'+init+'}\nvoid CScreenshareSession::changed(){'+change+'}\n'+MAIN)
                flags=['-std=c++20','-O1','-g','-fno-omit-frame-pointer']+(['-fsanitize=address'] if a.asan else [])
                compiled=subprocess.run([a.compiler,*flags,str(cpp),'-o',str(binary)],capture_output=True,text=True,timeout=30)
                if compiled.returncode:raise RuntimeError(compiled.stderr[-4000:])
                cases=['null-init','drop-init','null-change','drop-change','valid-init','valid-change','stopped-change'] if label=='after' else ['null-init','null-change']
                outputs={}
                for case in cases:
                    reply=subprocess.run([str(binary),case],capture_output=True,text=True,timeout=5,preexec_fn=no_core)
                    outputs[case]={'exit':reply.returncode,'diagnostics':reply.stderr[-1500:]}
                    if label=='before' and reply.returncode==0:raise AssertionError('Original null-monitor case unexpectedly succeeded')
                    if label=='after' and reply.returncode:raise AssertionError('Patched case failed: '+case+'\n'+reply.stderr[-2000:])
                report[label]=outputs
                if label=='after':assert b'BWM_SCREENSHARE_MONITOR_GUARD_V1' in binary.read_bytes()
                with subprocess.Popen([str(binary),'report'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,preexec_fn=no_core) as child:
                    stdout,stderr=child.communicate(timeout=5);assert child.returncode==0,stderr
                    packet=json.loads(stdout);assert packet['version']=='0.56.2' and isinstance(packet['flags'],list)
                    if label=='after':assert packet['bwmScreenshareMonitorGuard']=={'version':1,'pid':child.pid}
                    else:assert 'bwmScreenshareMonitorGuard' not in packet
                    report[label+'VersionReply']=packet
            report.update(passed=True,patchAppliedToReviewedSource=True,actualBodiesCompiled=True,guardMarkerRetainedInTestElf=True)
    except (AssertionError,OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        report.update(passed=False,error=str(error))
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

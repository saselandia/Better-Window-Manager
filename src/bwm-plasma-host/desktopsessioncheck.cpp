// SPDX-License-Identifier: GPL-2.0-or-later
#include "desktopsessioncheck.h"
#include "nativedesktopcontrol.h"
#include "outputidentity.h"
#include <virtualdesktopinfo.h>
#include <QGuiApplication>
#include <QScreen>
#include <QJsonArray>
#include <QEventLoop>
#include <QElapsedTimer>
#include <QSet>
#include <QTimer>
#include <functional>

QJsonObject nativeDesktopSessionSnapshot(const QStringList &descriptions, int timeoutMs){
    QJsonObject report{{"version",1},{"readOnly",true},{"ready",false}};
    if(!QGuiApplication::platformName().startsWith("wayland") || descriptions.isEmpty() || descriptions.size()>32){
        report["error"]="Wayland and 1–32 output descriptions are required";return report;
    }
    // The connection starts read-only. Observing binding/availability does not
    // call ensurePaused(false), send an activation or register a panel runtime.
    NativeDesktopControl control;
    TaskManager::VirtualDesktopInfo info;
    const auto snapshot=[&]{
        QJsonArray outputs;
        QSet<QScreen*> selected;
        bool valid=true;
        for(const auto &description:descriptions){
            QString status;auto *screen=BwmOutput::resolveScreen(description,&status);
            QJsonObject output{{"description",description},{"match",status}};
            if(!screen || selected.contains(screen)){
                valid=false;if(screen)output["match"]="duplicate-output-selection";
            }else{
                selected.insert(screen);const auto box=screen->geometry();
                output["geometry"]=QJsonArray{box.x(),box.y(),box.width(),box.height()};
                output["currentByName"]=info.currentDesktopByScreenName(screen->name()).toString();
                output["currentByGeometry"]=info.currentDesktopByScreenGeometry(box).toString();
                if(output["currentByName"].toString().isEmpty() || output["currentByGeometry"].toString().isEmpty())valid=false;
            }
            outputs.append(output);
        }
        const auto binding=control.state();
        const auto ids=info.desktopIds();
        valid=valid && binding.value("bindingVerified").toBool() && binding.value("providerAvailable").toBool()
            && !control.resumed() && binding.value("serial").toUInt()==0
            && info.numberOfDesktops()>0 && info.numberOfDesktops()==ids.size() && !info.currentDesktop().toString().isEmpty()
            && QGuiApplication::allWindows().isEmpty();
        return QJsonObject{{"version",1},{"readOnly",true},{"ready",valid},
            {"desktopIds",QJsonArray::fromVariantList(ids)},{"current",info.currentDesktop().toString()},
            {"desktops",info.numberOfDesktops()},{"outputs",outputs},{"control",QJsonObject::fromVariantMap(binding)},
            {"qtScreenCount",QGuiApplication::screens().size()},{"windowCount",QGuiApplication::allWindows().size()}};
    };
    QEventLoop loop;QTimer sample,deadline;QElapsedTimer stable;
    QJsonObject previous;
    sample.setInterval(20);deadline.setSingleShot(true);
    QObject::connect(&sample,&QTimer::timeout,&loop,[&]{
        report=snapshot();
        if(!report.value("ready").toBool() || report!=previous){previous=report;stable.restart();}
        else if(stable.isValid() && stable.elapsed()>=120)loop.quit();
    });
    bool timedOut=false;
    QObject::connect(&deadline,&QTimer::timeout,&loop,[&]{timedOut=true;loop.quit();});
    sample.start();deadline.start(qBound(1,timeoutMs,5000));loop.exec();
    report=snapshot();
    if(timedOut){report["ready"]=false;report["error"]="Native desktop snapshot did not settle before the deadline";}
    return report;
}

namespace {
bool awaitDesktopState(const std::function<bool()> &ready,int timeoutMs){
    QEventLoop loop;QTimer tick,deadline;bool accepted=false;
    tick.setInterval(20);deadline.setSingleShot(true);
    QObject::connect(&tick,&QTimer::timeout,&loop,[&]{if(ready()){accepted=true;loop.quit();}});
    QObject::connect(&deadline,&QTimer::timeout,&loop,&QEventLoop::quit);
    tick.start();deadline.start(timeoutMs);loop.exec();return accepted;
}
}

static QJsonObject nativeDesktopCycle(const QString &originalOutput,const QStringList &descriptions,const QString &navigationTarget={}){
    const bool navigation=!navigationTarget.isEmpty();
    QJsonObject report{{"version",1},{"readOnly",false},{"passed",false},{"restoredInitialOutput",false},
        {"activationRequestsSent",0},{"windowCount",QGuiApplication::allWindows().size()},
        {"activationMethod",navigation?"requestActivate":"requestActivateOnScreen"}};
    if(descriptions.size()<(navigation?1:2) || descriptions.size()>8 || descriptions.count(originalOutput)!=1){
        report["error"]="Cycle requires distinct output descriptions and the original output";return report;
    }
    const auto initial=nativeDesktopSessionSnapshot(descriptions);
    if(!initial.value("ready").toBool()){
        report["error"]="Initial native desktop snapshot unavailable";return report;
    }
    const auto outputs=initial.value("outputs").toArray();
    const auto ids=initial.value("desktopIds").toArray();
    QJsonObject original;QJsonArray route;QSet<QString> active;
    for(const auto &value:outputs){
        const auto output=value.toObject();const auto current=output.value("currentByName").toString();
        if(active.contains(current) || current!=output.value("currentByGeometry").toString()){
            report["error"]="Output desktop assignments are ambiguous";return report;
        }
        active.insert(current);
        if(output.value("description").toString()==originalOutput)original=output;
        else route.append(output);
    }
    if(original.isEmpty() || initial.value("current")!=original.value("currentByName")){
        report["error"]="The focused desktop changed before the cycle";return report;
    }
    if(navigation){
        bool numeric=false;const int number=navigationTarget.toInt(&numeric);
        if(!numeric || number<1 || number==99 || QString::number(number)!=navigationTarget
            || !ids.contains(navigationTarget) || active.contains(navigationTarget)){
            report["error"]="Navigation target must be an ordinary projected desktop not visible on any output";return report;
        }
        route={};auto destination=original;
        destination["currentByName"]=navigationTarget;destination["currentByGeometry"]=navigationTarget;
        route.append(destination);report["navigationTarget"]=navigationTarget;
    }
    route.append(original);
    QJsonArray expectedOutputs=outputs;
    NativeDesktopControl control;TaskManager::VirtualDesktopInfo info;
    const auto matches=[&](const QJsonArray &expected){
        if(QGuiApplication::screens().size()!=outputs.size() || !QGuiApplication::allWindows().isEmpty()
            || QJsonArray::fromVariantList(info.desktopIds())!=ids)return false;
        for(const auto &value:expected){
            const auto output=value.toObject();auto *screen=BwmOutput::resolveScreen(output.value("description").toString());
            if(!screen)return false;const auto box=screen->geometry();
            if(QJsonArray{box.x(),box.y(),box.width(),box.height()}!=output.value("geometry").toArray()
                || info.currentDesktopByScreenName(screen->name()).toString()!=output.value("currentByName").toString()
                || info.currentDesktopByScreenGeometry(box).toString()!=output.value("currentByGeometry").toString())return false;
        }
        return true;
    };
    const auto assignmentsMatch=[&]{return matches(expectedOutputs);};
    const auto pause=[&]{
        return awaitDesktopState([&]{return control.ensurePaused(true)==NativeDesktopControl::Status::Ready;},1300);
    };
    const auto observation=[&]{
        QJsonArray observed;
        for(const auto &value:outputs){
            const auto description=value.toObject().value("description").toString();
            QString match;auto *screen=BwmOutput::resolveScreen(description,&match);
            QJsonObject output{{"description",description},{"match",match}};
            if(screen){
                const auto box=screen->geometry();
                output["geometry"]=QJsonArray{box.x(),box.y(),box.width(),box.height()};
                output["currentByName"]=info.currentDesktopByScreenName(screen->name()).toString();
                output["currentByGeometry"]=info.currentDesktopByScreenGeometry(box).toString();
            }
            observed.append(output);
        }
        return QJsonObject{{"current",info.currentDesktop().toString()},{"outputs",observed},
            {"assignmentsMatch",assignmentsMatch()},{"control",QJsonObject::fromVariantMap(control.state())}};
    };
    report["initialCurrent"]=initial.value("current");report["initialOutputs"]=outputs;
    if(!awaitDesktopState([&]{return control.ensurePaused(false)==NativeDesktopControl::Status::Ready
            && assignmentsMatch() && info.currentDesktop().toString()==initial.value("current").toString();},1500)){
        report["error"]="Native activation barrier or initial assignments unavailable";
        report["failedObservation"]=observation();
        report["paused"]=pause();return report;
    }
    QJsonArray steps;QString expectedCurrent=initial.value("current").toString();
    QString error;
    for(const auto &value:route){
        const auto output=value.toObject();const auto description=output.value("description").toString();
        auto *screen=BwmOutput::resolveScreen(description);
        if(!screen || !control.resumed() || !assignmentsMatch() || info.currentDesktop().toString()!=expectedCurrent){
            error="Outputs, assignments or focus changed before the next activation";break;
        }
        const auto target=output.value("currentByName").toString();
        report["requestedOutput"]=description;report["requestedDesktop"]=target;
        if(navigation){
            // The wrapper audits the unused ID's effective Hyprland binding.
            // Only this output may change; every other assignment remains fixed.
            for(qsizetype i=0;i<expectedOutputs.size();++i){
                auto expected=expectedOutputs[i].toObject();
                if(expected.value("description").toString()==originalOutput){
                    expected["currentByName"]=target;expected["currentByGeometry"]=target;
                    expectedOutputs[i]=expected;
                }
            }
            info.requestActivate(target);
        }else info.requestActivateOnScreen(target,screen->name());
        report["activationRequestsSent"]=report.value("activationRequestsSent").toInt()+1;
        if(!awaitDesktopState([&]{return control.resumed() && assignmentsMatch() && info.currentDesktop().toString()==target;},1200)){
            report["failedObservation"]=observation();
            error="Native activation was not observed with unchanged output assignments";break;
        }
        steps.append(QJsonObject{{"description",description},{"current",target},{"verified",true}});
        expectedCurrent=target;
    }
    report["steps"]=steps;
    // Cancel/drain this connection even on failure. Do not restore stale focus
    // after changed assignments or a failed action; there are no later actions.
    const bool paused=pause();report["paused"]=paused;
    report["finalObservation"]=observation();
    const bool restored=matches(outputs) && info.currentDesktop().toString()==initial.value("current").toString();
    report["restoredInitialOutput"]=restored;
    report["windowCount"]=QGuiApplication::allWindows().size();
    if(error.isEmpty() && !paused)error="Native activation pause barrier did not complete";
    if(error.isEmpty() && !restored)error="Initial output was not restored";
    if(error.isEmpty())report["passed"]=true;else report["error"]=error;
    return report;
}

QJsonObject nativeDesktopFocusCycle(const QString &originalOutput,const QStringList &descriptions){
    return nativeDesktopCycle(originalOutput,descriptions);
}
QJsonObject nativeDesktopWorkspaceCycle(const QString &originalOutput,const QString &target,const QStringList &descriptions){
    return nativeDesktopCycle(originalOutput,descriptions,target);
}

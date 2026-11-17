// SPDX-License-Identifier: GPL-2.0-or-later
#include "tasksource.h"
#include "taskbridge.h"
#include "desktopbridge.h"
#include "panelruntime.h"
#include "runtimecontrol.h"
#include <tasksmodel.h>
#include <startuptasksmodel.h>
#include <windowtasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QStandardItemModel>
#include <QAbstractItemModelTester>
#include <QPersistentModelIndex>
#include <QJsonArray>
#include <QFile>
#include <QStandardPaths>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QQmlEngine>
#include <QQmlComponent>
#include <Plasma/PluginLoader>
#include <Plasma/Applet>
#include <QCryptographicHash>
#include <QtTest>
class TaskTest:public QObject {
    Q_OBJECT
    QJsonObject window(int pid=123,const QString &generation="1")const {
        return {{"address","0xabc"},{"pid",pid},{"generation",generation},{"title","Fixture"},{"appId","fixture"},
            {"workspace","2"},{"geometry",QJsonArray{0,0,800,600}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",false},{"minimized",false},{"maximized",false},{"fullscreen",false},{"urgent",false},{"onAllDesktops",false}};
    }
    QJsonObject snapshot(const QJsonObject &w)const{return {{"version",1},{"windows",QJsonArray{w}}};}
private Q_SLOTS:
    void coldGroupUsesOriginalKdeStackingFallback(){
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        BwmTaskSource source;
        auto first=window(2147483647),second=first;
        first["address"]="0xabc";first["stackingOrder"]=9;
        second["address"]="0xdef";second["stackingOrder"]=3;
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{first,second}}}));
        TaskManager::TasksModel tasks;tasks.componentComplete();
        QStandardItemModel startup(0,1);
        for(auto *concat:tasks.findChildren<QConcatenateTablesProxyModel*>())for(auto *model:concat->sourceModels()){
            if(auto *s=qobject_cast<TaskManager::StartupTasksModel*>(model);s && s->columnCount()==0)s->setSourceModel(&startup);
            if(auto *w=qobject_cast<TaskManager::WindowTasksModel*>(model))w->setSourceModel(&source);
        }
        tasks.setFilterByCurrentVirtualDesktop(false);tasks.setFilterByActivity(false);tasks.setFilterByScreen(false);
        tasks.setGroupMode(TaskManager::TasksModel::GroupApplications);tasks.setGroupInline(false);tasks.setGroupingWindowTasksThreshold(-1);
        QTRY_COMPARE(tasks.rowCount(),1);
        const auto group=tasks.index(0,0);
        QVERIFY(group.data(TaskManager::AbstractTasksModel::IsGroupParent).toBool());QCOMPARE(tasks.rowCount(group),2);
        // Load KDE's installed module/resources before importing its unmodified
        // TaskTools.js. No copied activation function or fake group model.
        QScopedPointer<Plasma::Applet> installed(Plasma::PluginLoader::self()->loadApplet("org.kde.plasma.taskmanager"));
        QVERIFY(installed);
        QQmlEngine engine;QQmlComponent bootstrap(&engine);
        bootstrap.setData("import QtQml\nimport plasma.applet.org.kde.plasma.taskmanager\nQtObject {}",QUrl());
        QScopedPointer<QObject> loaded(bootstrap.create());QVERIFY2(loaded,qPrintable(bootstrap.errorString()));
        QFile original(":/qt/qml/plasma/applet/org/kde/plasma/taskmanager/TaskTools.js");
        QVERIFY(original.open(QIODevice::ReadOnly));
        const auto scriptHash=QCryptographicHash::hash(original.readAll(),QCryptographicHash::Sha256).toHex();
        QCOMPARE(scriptHash,QByteArray("74e0b23971ef8f4c53d5693bf4a03f985500ae21ce4e84975244f718bfc57a77"));
        QQmlComponent component(&engine);
        component.setData(R"(
import QtQml
import plasma.applet.org.kde.plasma.taskmanager as Native
QtObject {
    required property var nativeModel
    property QtObject task: QtObject {
        property int index: 0
        function modelIndex() { return nativeModel.makeModelIndex(0); }
    }
    property QtObject tasks: QtObject { property var tasksModel: nativeModel }
    property QtObject plasmoid: QtObject {
        property QtObject configuration: QtObject { property int groupedTaskVisualization: 0 }
    }
    function activate() {
        Native.TaskTools.activateTask(nativeModel.makeModelIndex(0), {IsGroupParent:true}, 0, task, plasmoid, tasks, false);
    }
}
)",QUrl());
        QScopedPointer<QObject> root(component.createWithInitialProperties({{"nativeModel",QVariant::fromValue(&tasks)}}));
        QVERIFY2(root,qPrintable(component.errorString()));
        QSignalSpy actions(&source,&BwmTaskSource::actionRequested);
        QVERIFY(QMetaObject::invokeMethod(root.get(),"activate"));QCOMPARE(actions.count(),1);
        QCOMPARE(actions.first().first().toJsonObject().value("address").toString(),"0xabc");
        QCOMPARE(actions.first().first().toJsonObject().value("action").toString(),"focus");
        // The source retains its own row order; only the stacking role changes.
        QPersistentModelIndex held=source.index(0);
        second["stackingOrder"]=12;QSignalSpy changed(&source,&BwmTaskSource::dataChanged);
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{first,second}}}));
        QVERIFY(held.isValid());QVERIFY(!changed.isEmpty());
        QVERIFY(changed.last().at(2).value<QList<int>>().contains(TaskManager::AbstractTasksModel::StackingOrder));
        actions.clear();QVERIFY(QMetaObject::invokeMethod(root.get(),"activate"));QCOMPARE(actions.count(),1);
        QCOMPARE(actions.first().first().toJsonObject().value("address").toString(),"0xdef");
        // MRU remains KDE's first choice once an activation has been observed.
        first["active"]=true;QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{first,second}}}));
        first["active"]=false;QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{first,second}}}));
        actions.clear();QVERIFY(QMetaObject::invokeMethod(root.get(),"activate"));QCOMPARE(actions.count(),1);
        QCOMPARE(actions.first().first().toJsonObject().value("address").toString(),"0xabc");
    }
    void stackingSnapshotValidationAndLegacyOrder(){
        BwmTaskSource source;auto first=window(),second=first;second["address"]="0xdef";
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{first,second}}}));
        using Roles=TaskManager::AbstractTasksModel;
        QCOMPARE(source.index(0).data(Roles::StackingOrder).toInt(),0);
        QCOMPARE(source.index(1).data(Roles::StackingOrder).toInt(),1);
        QPersistentModelIndex held=source.index(0);
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{second,first}}}));
        QVERIFY(held.isValid());QCOMPARE(held.data(Roles::StackingOrder).toInt(),1);
        const auto data=held.data();
        for(const auto &bad:QList<QJsonValue>{true,-1,1.5,2147483648.0,QString("2"),QJsonValue(QJsonValue::Null)}){
            auto invalid=first;invalid["stackingOrder"]=bad;
            QVERIFY(!source.apply(snapshot(invalid)));QVERIFY(held.isValid());QCOMPARE(held.data(),data);
            QCOMPARE(held.data(Roles::StackingOrder).toInt(),1);
        }
    }
    void persistentIndicesSurviveDataAndRejectReusedIdentity() {
        BwmTaskSource source;QAbstractItemModelTester tester(&source,QAbstractItemModelTester::FailureReportingMode::QtTest);
        QVERIFY(source.apply(snapshot(window())));QCOMPARE(source.rowCount(),1);
        QPersistentModelIndex held(source.index(0));const auto raw=source.index(0);
        const auto uuid=source.data(held,TaskManager::AbstractTasksModel::WinIdList);
        auto changed=window();changed["title"]="Changed";changed["minimized"]=true;
        QVERIFY(source.apply(snapshot(changed)));QVERIFY(held.isValid());QCOMPARE(source.data(held).toString(),"Changed");
        QCOMPARE(source.data(held,TaskManager::AbstractTasksModel::WinIdList),uuid);
        QSignalSpy requests(&source,&BwmTaskSource::actionRequested);source.requestActivate(held);
        QCOMPARE(requests.count(),1);QCOMPARE(requests.first().first().toJsonObject().value("action").toString(),"focus");
        QVERIFY(source.apply(snapshot(window(456,"2"))));QVERIFY(!held.isValid());
        requests.clear();source.requestClose(raw);QCOMPARE(requests.count(),0);
        QVERIFY(source.data(source.index(0),TaskManager::AbstractTasksModel::WinIdList)!=uuid);
        auto pinned=window(456,"2");pinned["onAllDesktops"]=true;
        QVERIFY(source.apply(snapshot(pinned)));
        QVERIFY(source.data(source.index(0),TaskManager::AbstractTasksModel::VirtualDesktops).toList().isEmpty());
        QVERIFY(!source.data(source.index(0),TaskManager::AbstractTasksModel::IsVirtualDesktopsChangeable).toBool());
        QVERIFY(!source.data(source.index(0),TaskManager::AbstractTasksModel::CanLaunchNewInstance).toBool());
    }
    void malformedSnapshotIsAtomic() {
        BwmTaskSource source;QVERIFY(source.apply(snapshot(window())));
        const auto idx=QPersistentModelIndex(source.index(0));
        QVERIFY(!source.apply(QJsonObject{{"version",1},{"windows",QJsonArray{window(),window()}}}));
        QVERIFY(idx.isValid());QCOMPARE(source.rowCount(),1);
        auto bad=window();bad["pid"]=true;QVERIFY(!source.apply(snapshot(bad)));QVERIFY(idx.isValid());
        source.clear();QVERIFY(!idx.isValid());
    }
    void fullscreenCapabilityAndDesiredStateFollowSnapshots(){
        BwmTaskSource source;QVERIFY(source.apply(snapshot(window())));
        QSignalSpy requests(&source,&BwmTaskSource::actionRequested);
        QVERIFY(!source.data(source.index(0),TaskManager::AbstractTasksModel::IsFullScreenable).toBool());
        source.requestToggleFullScreen(source.index(0));QCOMPARE(requests.count(),0);
        auto capable=window();capable["fullscreenable"]=true;QVERIFY(source.apply(snapshot(capable)));
        QVERIFY(source.data(source.index(0),TaskManager::AbstractTasksModel::IsFullScreenable).toBool());
        source.requestToggleFullScreen(source.index(0));source.requestToggleFullScreen(source.index(0));
        QCOMPARE(requests.count(),2);
        for(const auto &r:requests){const auto data=r.first().toJsonObject();QCOMPARE(data.value("action").toString(),"fullscreen");QCOMPARE(data.value("state"),QJsonValue(true));}
        capable["fullscreen"]=true;QVERIFY(source.apply(snapshot(capable)));requests.clear();
        source.requestToggleFullScreen(source.index(0));QCOMPARE(requests.count(),1);
        QCOMPARE(requests.first().first().toJsonObject().value("state"),QJsonValue(false));
        QSignalSpy changes(&source,&BwmTaskSource::dataChanged);
        capable["fullscreenable"]=false;QVERIFY(source.apply(snapshot(capable)));requests.clear();
        QVERIFY(!changes.isEmpty());QVERIFY(changes.last().at(2).value<QList<int>>().contains(TaskManager::AbstractTasksModel::IsFullScreenable));
        source.requestToggleFullScreen(source.index(0));QCOMPARE(requests.count(),0);
        capable["fullscreenable"]="true";QVERIFY(!source.apply(snapshot(capable)));
        QVERIFY(!source.data(source.index(0),TaskManager::AbstractTasksModel::IsFullScreenable).toBool());
    }
    void moveResizeBorderAndCaptureUseCommonManagerStates(){
        using M=TaskManager::AbstractTasksModel;
        BwmTaskSource source;QVERIFY(source.apply(snapshot(window())));
        QSignalSpy requests(&source,&BwmTaskSource::actionRequested);
        // Optional v1 fields absent: KDE capabilities false, no requests.
        for(int role:{int(M::IsMovable),int(M::IsResizable),int(M::CanSetNoBorder),int(M::HasNoBorder),int(M::IsExcludedFromCapture)})
            QVERIFY(!source.data(source.index(0),role).toBool());
        QVERIFY(!source.data(source.index(0),BwmTaskSource::ActionCapabilitiesRole).toMap().value("excludeFromCapture").toBool());
        source.requestMove(source.index(0));source.requestResize(source.index(0));
        source.requestToggleNoBorder(source.index(0));source.requestToggleExcludeFromCapture(source.index(0));
        QCOMPARE(requests.count(),0);
        auto capable=window();capable["movable"]=true;capable["windowTagsSettable"]=true;capable["noBorder"]=false;capable["excludedFromCapture"]=true;
        QSignalSpy changes(&source,&BwmTaskSource::dataChanged);
        QVERIFY(source.apply(snapshot(capable)));
        QVERIFY(!changes.isEmpty());const auto roles=changes.last().at(2).value<QList<int>>();
        for(int role:{int(M::IsMovable),int(M::IsResizable),int(M::CanSetNoBorder),int(M::IsExcludedFromCapture)})QVERIFY(roles.contains(role));
        QVERIFY(source.data(source.index(0),M::IsMovable).toBool() && source.data(source.index(0),M::IsResizable).toBool());
        QVERIFY(source.data(source.index(0),M::CanSetNoBorder).toBool() && source.data(source.index(0),M::IsExcludedFromCapture).toBool());
        QVERIFY(source.data(source.index(0),BwmTaskSource::ActionCapabilitiesRole).toMap().value("excludeFromCapture").toBool());
        source.requestMove(source.index(0));source.requestResize(source.index(0));
        // Desired state from the snapshot: duplicates never invert it.
        source.requestToggleNoBorder(source.index(0));source.requestToggleNoBorder(source.index(0));
        source.requestToggleExcludeFromCapture(source.index(0));
        QCOMPARE(requests.count(),5);
        QCOMPARE(requests.at(0).first().toJsonObject().value("action").toString(),"move");
        QCOMPARE(requests.at(1).first().toJsonObject().value("action").toString(),"resize");
        for(int i:{2,3}){const auto d=requests.at(i).first().toJsonObject();QCOMPARE(d.value("action").toString(),"no-border");QCOMPARE(d.value("state"),QJsonValue(true));}
        QCOMPARE(requests.at(4).first().toJsonObject().value("action").toString(),"no-capture");
        QCOMPARE(requests.at(4).first().toJsonObject().value("state"),QJsonValue(false));
        for(const auto &r:requests)QCOMPARE(r.first().toJsonObject().value("address").toString(),capable.value("address").toString());
        for(const char *field:{"movable","windowTagsSettable","noBorder","excludedFromCapture"}){
            auto bad=capable;bad[field]="true";QVERIFY(!source.apply(snapshot(bad)));
        }
        QVERIFY(source.data(source.index(0),M::IsMovable).toBool()); // Rejected snapshots are atomic.
    }
    void nativeTaskModelsShareCommonSourceAndApplyGuardedActions() {
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        QStandardItemModel emptyStartup(0,1);
        const auto offscreenStartup=[&](TaskManager::TasksModel *tasks){
            // KDE has no StartupTasksModel backend on offscreen: it exposes zero
            // columns, making QConcatenateTablesProxyModel hide every other source.
            // Supply an empty one-column startup fixture; do not alter production.
            for(auto *concat:tasks->findChildren<QConcatenateTablesProxyModel*>())
                for(auto *source:concat->sourceModels())if(auto *startup=qobject_cast<TaskManager::StartupTasksModel*>(source))
                    if(startup->columnCount()==0)startup->setSourceModel(&emptyStartup);
        };
        auto first=std::make_unique<TaskManager::TasksModel>();auto second=std::make_unique<TaskManager::TasksModel>();
        first->componentComplete();second->componentComplete();
        offscreenStartup(first.get());offscreenStartup(second.get());
        first->setGroupMode(TaskManager::TasksModel::GroupDisabled);second->setGroupMode(TaskManager::TasksModel::GroupDisabled);
        BwmTaskBridge bridge(qEnvironmentVariable("XDG_RUNTIME_DIR"),qEnvironmentVariable("XDG_CONFIG_HOME"),
            QStandardPaths::findExecutable("python3"),QStringLiteral(BWM_TASK_HELPER_SOURCE));
        bridge.attach(first.get());bridge.attach(second.get());bridge.tick();
        QTRY_COMPARE(bridge.source()->rowCount(),1);QCOMPARE(bridge.boundCount(),1);
        QTRY_COMPARE(first->rowCount(),1);QTRY_COMPARE(second->rowCount(),1);
        auto idx=first->index(0,0);QCOMPARE(first->data(idx,Qt::DisplayRole).toString(),"Native task fixture");
        QPersistentModelIndex nativeHeld(idx);
        QPersistentModelIndex held(bridge.source()->index(0));
        first->requestToggleMinimized(idx);
        QTRY_VERIFY(bridge.source()->data(held,TaskManager::AbstractTasksModel::IsMinimized).toBool());
        QTRY_VERIFY(second->data(second->index(0,0),TaskManager::AbstractTasksModel::IsMinimized).toBool());
        second->requestActivate(second->index(0,0));
        QTRY_VERIFY(!bridge.source()->data(held,TaskManager::AbstractTasksModel::IsMinimized).toBool());
        QVERIFY(held.isValid());QVERIFY2(bridge.error().isEmpty(),qPrintable(bridge.error()));
        QVERIFY(nativeHeld.isValid());
        first->requestToggleFullScreen(first->index(0,0));
        first->requestToggleFullScreen(first->index(0,0)); // Same snapshot: duplicate desired state must not toggle back.
        QTRY_VERIFY(bridge.source()->data(held,TaskManager::AbstractTasksModel::IsFullScreen).toBool());
        QTRY_VERIFY(!bridge.state().value("actionInFlight").toBool() && bridge.state().value("pendingActions").toInt()==0);
        QVERIFY(bridge.source()->data(held,TaskManager::AbstractTasksModel::IsFullScreen).toBool());
        second->requestToggleFullScreen(second->index(0,0));
        QTRY_VERIFY(!bridge.source()->data(held,TaskManager::AbstractTasksModel::IsFullScreen).toBool());
        QVERIFY2(bridge.error().isEmpty(),qPrintable(bridge.error()));
        first->requestClose(first->index(0,0));QTRY_COMPARE(bridge.source()->rowCount(),0);
        QVERIFY(!held.isValid());QVERIFY(!nativeHeld.isValid());
        QFile fixture(qEnvironmentVariable("BWM_R4_FAKE_CLIENTS"));QVERIFY(fixture.open(QIODevice::ReadOnly));
        auto reopened=QJsonDocument::fromJson(fixture.readAll()).object();fixture.close();reopened["mapped"]=true;
        QSaveFile replacementFile(fixture.fileName());QVERIFY(replacementFile.open(QIODevice::WriteOnly));
        replacementFile.write(QJsonDocument(reopened).toJson());QVERIFY(replacementFile.commit());
        QTRY_COMPARE(bridge.source()->rowCount(),1);
        first.reset();bridge.tick();QCOMPARE(bridge.boundCount(),1);
        second.reset();bridge.tick();QCOMPARE(bridge.boundCount(),0);QCOMPARE(bridge.source()->rowCount(),0);
        TaskManager::TasksModel surviving;surviving.componentComplete();
        offscreenStartup(&surviving);
        {
            BwmTaskBridge replacement(qEnvironmentVariable("XDG_RUNTIME_DIR"),qEnvironmentVariable("XDG_CONFIG_HOME"),
                QStandardPaths::findExecutable("python3"),QStringLiteral(BWM_TASK_HELPER_SOURCE));
            replacement.attach(&surviving);replacement.tick();QTRY_COMPARE(surviving.rowCount(),1);
            QVERIFY(replacement.state().value("snapshotAvailable").toBool());
            QVERIFY(!replacement.state().value("operationalVerified").toBool());
        }
        QCOMPARE(surviving.rowCount(),0); // Restores the native source before deleting the injected model.
        QStandardItemModel custom(1,1);TaskManager::WindowTasksModel *windowProxy=nullptr;
        for(auto *concat:surviving.findChildren<QConcatenateTablesProxyModel*>())
            for(auto *source:concat->sourceModels())if(auto *windows=qobject_cast<TaskManager::WindowTasksModel*>(source))windowProxy=windows;
        QVERIFY(windowProxy);windowProxy->setSourceModel(&custom);
        BwmTaskBridge respectCustom(qEnvironmentVariable("XDG_RUNTIME_DIR"),qEnvironmentVariable("XDG_CONFIG_HOME"),
            "/usr/bin/false","unused");respectCustom.attach(&surviving);respectCustom.tick();
        QCOMPARE(windowProxy->sourceModel(),&custom);QCOMPARE(respectCustom.boundCount(),0);
    }
    void suspensionDrainsCurrentTaskAndDiscardsQueuedActions() {
        QTemporaryDir root;QVERIFY(root.isValid());
        const auto helper=root.path()+"/task-helper.py",started=root.path()+"/started",release=root.path()+"/release",log=root.path()+"/actions";
        QFile file(helper);QVERIFY(file.open(QIODevice::WriteOnly));
        const auto data=QJsonDocument(snapshot(window())).toJson(QJsonDocument::Compact);
        file.write("import json,sys,time\nfrom pathlib import Path\nroot=Path(__file__).parent\n"
            "if sys.argv[1]=='snapshot':\n print("+QByteArray("'")+data+"')\n"
            "else:\n request=json.load(sys.stdin)\n with (root/'actions').open('a') as f:f.write(request['action']+'\\n')\n"
            " (root/'started').touch()\n while not (root/'release').exists():time.sleep(.01)\n"
            " print('{\"version\":1,\"accepted\":true}')\n");file.close();
        const QString token(64,'b');
        const auto request=[&](int revision,const QString &skin){
            QSaveFile out(root.path()+"/control.json");if(!out.open(QIODevice::WriteOnly))return false;
            out.write(QJsonDocument(QJsonObject{{"version",1},{"token",token},{"revision",revision},{"command","skin"},{"skin",skin}}).toJson());return out.commit();
        };
        PanelRuntime runtime(nullptr,root.path()+"/views",false);
        QVERIFY(request(0,"plasma"));RuntimeControl control(&runtime,root.path(),token);QVERIFY(control.start());
        TaskManager::WindowTasksModel native;
        BwmTaskBridge bridge(root.path(),root.path(),QStandardPaths::findExecutable("python3"),helper);
        bridge.attach(&native);bridge.tick();QTRY_COMPARE(bridge.source()->rowCount(),1);
        bridge.source()->requestToggleMinimized(bridge.source()->index(0));QTRY_VERIFY(QFile::exists(started));
        bridge.source()->requestClose(bridge.source()->index(0));QCOMPARE(bridge.state().value("pendingActions").toInt(),1);
        QVERIFY(request(1,"retro"));QTRY_VERIFY(runtime.quiescing());QVERIFY(bridge.state().value("suspended").toBool());
        QCOMPARE(control.revision(),0);QCOMPARE(runtime.skin(),"plasma");
        QCOMPARE(bridge.state().value("pendingActions").toInt(),0);QVERIFY(bridge.state().value("actionInFlight").toBool());
        QCOMPARE(bridge.source()->rowCount(),0);
        QFile gate(release);QVERIFY(gate.open(QIODevice::WriteOnly));gate.close();
        QTRY_VERIFY(bridge.state().value("quiescent").toBool());
        QTRY_COMPARE(control.revision(),1);QCOMPARE(runtime.skin(),"retro");
        file.setFileName(log);
        QVERIFY(file.open(QIODevice::ReadOnly));QCOMPARE(file.readAll(),"toggle-minimize\n");file.close();
        QVERIFY(request(2,"plasma"));QTRY_COMPARE(control.revision(),2);bridge.tick();QTRY_COMPARE(bridge.source()->rowCount(),1);
    }
    void controlAcknowledgesWithdrawalOnlyAfterNativeMutationFinishes() {
        QTemporaryDir root;QVERIFY(root.isValid());
        const auto helper=root.path()+"/desktop-helper.py",started=root.path()+"/started",release=root.path()+"/release",completed=root.path()+"/completed";
        QFile file(helper);QVERIFY(file.open(QIODevice::WriteOnly));
        file.write("import time\nfrom pathlib import Path\nroot=Path(__file__).parent\n"
                   "with (root/'actions').open('a') as f:f.write('entered\\n')\n(root/'started').touch()\n"
                   "while not (root/'release').exists():time.sleep(.01)\n(root/'completed').touch()\n");file.close();
        const QString token(64,'a');
        const auto request=[&](int revision,const QString &skin){
            QSaveFile out(root.path()+"/control.json");if(!out.open(QIODevice::WriteOnly))return false;
            out.write(QJsonDocument(QJsonObject{{"version",1},{"token",token},{"revision",revision},{"command","skin"},{"skin",skin}}).toJson());return out.commit();
        };
        PanelRuntime runtime(nullptr,root.path()+"/views",false);
        QVERIFY(request(0,"plasma"));RuntimeControl control(&runtime,root.path(),token);QVERIFY(control.start());
        DesktopBridge desktop(root.path(),QStandardPaths::findExecutable("python3"),{helper});
        desktop.setShowingDesktop(true);QTRY_VERIFY(QFile::exists(started));
        desktop.setShowingDesktop(true); // This deferred mutation must be discarded on suspension.
        QVERIFY(request(1,"retro"));QTRY_VERIFY(runtime.quiescing());
        QCOMPARE(control.revision(),0);QCOMPARE(runtime.skin(),"plasma");QVERIFY(!QFile::exists(completed));
        QFile gate(release);QVERIFY(gate.open(QIODevice::WriteOnly));gate.close();
        QTRY_COMPARE(control.revision(),1);QVERIFY(QFile::exists(completed));QCOMPARE(runtime.skin(),"retro");
        file.setFileName(root.path()+"/ack.json");QVERIFY(file.open(QIODevice::ReadOnly));
        const auto ack=QJsonDocument::fromJson(file.readAll()).object();QVERIFY(ack.value("ok").toBool());QCOMPARE(ack.value("skin").toString(),"retro");file.close();
        file.setFileName(root.path()+"/actions");QVERIFY(file.open(QIODevice::ReadOnly));QCOMPARE(file.readAll(),"entered\n");file.close();
        QVERIFY(request(2,"plasma"));QTRY_COMPARE(control.revision(),2); // A failed/cancelled change can resume the old skin too.
    }
};
QTEST_MAIN(TaskTest)
#include "test-tasks.moc"

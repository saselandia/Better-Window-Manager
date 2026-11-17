// SPDX-License-Identifier: GPL-2.0-or-later
#include "tasksource.h"
#include "nativedesktopcontrol.h"
#include "panelruntime.h"
#include "runtimecontrol.h"
#include <virtualdesktopinfo.h>
#include <tasksmodel.h>
#include <taskfilterproxymodel.h>
#include <windowtasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QGuiApplication>
#include <QScreen>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QProcess>
#include <QProcessEnvironment>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QtTest>
#include <unistd.h>
#include <poll.h>
#include <fcntl.h>
#include <cstdio>
class DesktopTest:public QObject {
    Q_OBJECT
    void command(const QByteArray &value){
        bool ok=false;const auto fd=qEnvironmentVariableIntValue("BWM_R4_DESKTOP_TEST_FD",&ok);QVERIFY(ok);
        const auto bytes=value+'\n';QCOMPARE(::write(fd,bytes.constData(),bytes.size()),bytes.size());
    }
    QJsonObject window(int number)const {
        return {{"address",QString("0x%1").arg(number)},{"pid",int(::getpid())},{"generation","1"},
            {"title",QString("Window %1").arg(number)},{"appId",QString("app%1").arg(number)},
            {"workspace",QString::number(number)},{"geometry",QJsonArray{10,20,800,600}},
            {"screen",QJsonArray{0,0,1920,1080}},{"active",false},{"minimized",false},
            {"maximized",false},{"fullscreen",false},{"urgent",false},{"onAllDesktops",false}};
    }
private Q_SLOTS:
    void nativeActivationRequiresObservedAbsoluteState(){
        NativeDesktopControl gate;TaskManager::VirtualDesktopInfo info;
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QTRY_COMPARE(info.currentDesktop().toString(),"1");
        const auto status=[&]()->QJsonObject{
            command("activation-status");
            pollfd fd{qEnvironmentVariableIntValue("BWM_R4_FIXTURE_NOTIFY_FD"),POLLIN,0};
            if(::poll(&fd,1,1000)!=1)return {};
            char buffer[1024];const auto n=::read(fd.fd,buffer,sizeof(buffer));
            return n>0?QJsonDocument::fromJson(QByteArray(buffer,n)).object():QJsonObject{};
        };
        const auto initial=status();QVERIFY(initial.contains("actions"));
        info.requestActivate(QString("1"));QTest::qWait(30);
        QCOMPARE(status().value("actions"),initial.value("actions")); // Cannot toggle back-and-forth.
        command("activation-pretend-on");QVERIFY(status().value("pretend").toBool());
        info.requestActivate(QString("3"));
        QTRY_COMPARE(status().value("outcome").toString(),"activation-readback-mismatch");
        QCOMPARE(info.currentDesktop().toString(),"1");
        QVERIFY(status().value("rejected").toInt()>initial.value("rejected").toInt());
        command("activation-pretend-off");QVERIFY(!status().value("pretend").toBool());
        info.requestActivate(QString("3"));QTRY_COMPARE(info.currentDesktop().toString(),"3");
        const auto verified=status();QCOMPARE(verified.value("outcome").toString(),"applied-verified");
        info.requestActivate(QString("3"));QTest::qWait(30);QCOMPARE(status().value("actions"),verified.value("actions"));
        info.requestActivate(QString("1"));QTRY_COMPARE(info.currentDesktop().toString(),"1");
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
    }
    void sharedCountMirrorUpdatesOriginalKde(){
        NativeDesktopControl gate;TaskManager::VirtualDesktopInfo info;
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QTRY_COMPARE(info.numberOfDesktops(),3);
        command("bwm-plasma-desktops-count 7");QTRY_COMPARE(info.numberOfDesktops(),7);
        info.requestActivate(QString("7"));QTRY_COMPARE(info.currentDesktop().toString(),"7");
        command("bwm-plasma-desktops-count 2");QTRY_COMPARE(info.desktopIds(),QVariantList({QString("1"),QString("2"),QString("3"),QString("7")}));
        QCOMPARE(info.currentDesktop().toString(),"7"); // Shrink never deletes a live/active workspace.
        command("bwm-plasma-desktops-count true");QTest::qWait(25);QCOMPARE(info.numberOfDesktops(),4);
        info.requestActivate(QString("1"));QTRY_COMPARE(info.currentDesktop().toString(),"1");
        command("bwm-plasma-desktops-count 3");QTRY_COMPARE(info.numberOfDesktops(),3);
        QCOMPARE(info.desktopNames(),QStringList({"One","Two","Three"}));
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
    }
    void arbitratedProviderFeedsOriginalKdeAndWithdraws(){
        if(qEnvironmentVariable("BWM_R4_ARBITRATED_FIXTURE")!="1")QSKIP("Run separately with the arbitrated provider fixture");
        NativeDesktopControl gate;TaskManager::VirtualDesktopInfo info;
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QTRY_COMPARE(info.desktopNames(),QStringList({"One","Two","Three"}));
        QVERIFY(gate.resumed());QVERIFY(gate.state().value("bindingVerified").toBool());
        QQmlEngine engine;QQmlComponent component(&engine);
        component.setData("import QtQml\nimport org.kde.taskmanager as Tasks\nQtObject { property var info: Tasks.VirtualDesktopInfo {} }",QUrl());
        QScopedPointer<QObject> root(component.create());QVERIFY2(root,qPrintable(component.errorString()));
        auto *qmlInfo=root->property("info").value<QObject*>();QVERIFY(qmlInfo);
        QTRY_COMPARE(qmlInfo->property("numberOfDesktops").toInt(),3);
        info.requestActivate(QString("3"));
        QTRY_COMPARE(info.currentDesktop().toString(),"3");
        QTRY_COMPARE(qmlInfo->property("currentDesktop").toString(),"3");
        command("shrink");QTRY_COMPARE(info.numberOfDesktops(),2);
        QTRY_COMPARE(info.desktopNames(),QStringList({"Renamed One","Two"}));
        QTRY_COMPARE(qmlInfo->property("numberOfDesktops").toInt(),2);
        // Invalid backend state revokes this generation. A compatible global
        // name/version alone cannot keep the controller resumed.
        command("invalid");QTRY_VERIFY(!gate.resumed());
        QTRY_VERIFY(!gate.state().value("connected").toBool());
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        QVERIFY(gate.state().value("registry").toMap().value("managementGlobals").toInt()==0);
    }
    void registryRequiresUniqueAndAssociatedControl(){
        NativeDesktopControl gate;
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QVERIFY(gate.resumed());QVERIFY(gate.state().value("bindingVerified").toBool());
        auto inventory=[&]{return gate.state().value("registry").toMap();};
        QVERIFY(inventory().value("complete").toBool());
        QCOMPARE(inventory().value("managementGlobals").toInt(),1);QCOMPARE(inventory().value("controlGlobals").toInt(),1);
        const auto firstSerial=gate.state().value("serial").toUInt();
        command("extra-control");QTRY_COMPARE(inventory().value("controlGlobals").toInt(),2);
        QVERIFY(!gate.resumed());QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        command("drop-extras");QTRY_COMPARE(inventory().value("controlGlobals").toInt(),1);
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QVERIFY(gate.state().value("serial").toUInt()!=firstSerial);
        command("foreign");
        QTRY_VERIFY(gate.state().value("connected").toBool() && gate.state().value("providerAvailable").toBool() &&
            inventory().value("topologyCompatible").toBool() && gate.state().value("bindingKnown").toBool() && gate.state().value("managementGlobal").toUInt()==0);
        QVERIFY(!gate.state().value("bindingVerified").toBool());
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        command("drop-extras");command("restore");
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QVERIFY(gate.state().value("bindingVerified").toBool());
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
    }
    void registryTimeoutRequiresFreshRevisionAfterLateInventory(){
        const int input=qEnvironmentVariableIntValue("BWM_R4_DESKTOP_TEST_FD");
        struct Resume {int fd;bool active=true;~Resume(){if(active)::write(fd,"unstall\n",8);}} resume{input};
        command("stall");
        pollfd ready{qEnvironmentVariableIntValue("BWM_R4_FIXTURE_NOTIFY_FD"),POLLIN,0};QCOMPARE(::poll(&ready,1,1000),1);
        char message[8];QCOMPARE(::read(ready.fd,message,8),8);QCOMPARE(QByteArray(message,8),"stalled\n");
        NativeDesktopControl gate;
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Pending);
        QTRY_VERIFY(gate.state().value("registryTimedOut").toBool());
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QCOMPARE(::write(input,"unstall\n",8),8);resume.active=false;
        QTRY_VERIFY(gate.state().value("bindingVerified").toBool());
        QVERIFY(!gate.resumed());QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        gate.beginRevision(42);
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
    }
    void originalKdeProviderFeedsCppQmlFiltersAndSorting() {
        QCOMPARE(QGuiApplication::platformName(),"wayland");QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        NativeDesktopControl activation;
        QTRY_VERIFY(activation.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        TaskManager::VirtualDesktopInfo first,second;
        QTRY_COMPARE(first.numberOfDesktops(),3);QTRY_COMPARE(first.desktopNames(),QStringList({"One","Two","Three"}));
        QCOMPARE(first.desktopIds(),QVariantList({QString("1"),QString("2"),QString("3")}));
        QTRY_COMPARE(first.currentDesktop().toString(),"1");QCOMPARE(second.currentDesktop(),first.currentDesktop());
        QTRY_COMPARE(QGuiApplication::screens().size(),2);
        auto *a=QGuiApplication::screens().at(0);auto *b=QGuiApplication::screens().at(1);
        if(a->name()!="r4-output-A")std::swap(a,b);
        QCOMPARE(a->name(),"r4-output-A");QCOMPARE(b->name(),"r4-output-B");
        QTRY_COMPARE(first.currentDesktopByScreenName(a->name()).toString(),"1");
        QTRY_COMPARE(first.currentDesktopByScreenGeometry(b->geometry()).toString(),"2");
        QQmlEngine engine;QQmlComponent component(&engine);
        component.setData("import QtQml\nimport QtQml.Models\nimport org.kde.taskmanager as Tasks\n"
            "QtObject { property var info: Tasks.VirtualDesktopInfo {}\n"
            " property var tasks: Tasks.TasksModel { groupMode: Tasks.TasksModel.GroupDisabled; sortMode: Tasks.TasksModel.SortVirtualDesktop }\n"
            " property var rows: Instantiator { model: tasks; delegate: QtObject { required property string display } }\n"
            " property int rowCount: rows.count\n"
            " function titleAt(i) { return rows.objectAt(i) ? rows.objectAt(i).display : '' } }",QUrl());
        QScopedPointer<QObject> root(component.create());QVERIFY2(root,qPrintable(component.errorString()));
        auto *qmlInfo=root->property("info").value<QObject*>();QVERIFY(qmlInfo);
        QTRY_COMPARE(qmlInfo->property("numberOfDesktops").toInt(),3);

        BwmTaskSource source;QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{window(3),window(1),window(2)}}}));
        TaskManager::TaskFilterProxyModel filter;filter.setSourceModel(&source);filter.setScreenGeometry(a->geometry());
        filter.setFilterByCurrentVirtualDesktop(true);
        QTRY_COMPARE(filter.rowCount(),1);QCOMPARE(filter.index(0,0).data().toString(),"Window 1");
        TaskManager::TasksModel tasks;tasks.componentComplete();tasks.setGroupMode(TaskManager::TasksModel::GroupDisabled);
        TaskManager::WindowTasksModel *windows=nullptr;
        for(auto *concat:tasks.findChildren<QConcatenateTablesProxyModel*>())
            for(auto *model:concat->sourceModels())if(auto *w=qobject_cast<TaskManager::WindowTasksModel*>(model))windows=w;
        QVERIFY(windows);QPointer<QAbstractItemModel> previous=windows->sourceModel();windows->setSourceModel(&source);
        tasks.setSortMode(TaskManager::TasksModel::SortVirtualDesktop);
        QTRY_COMPARE(tasks.rowCount(),3);
        QCOMPARE(tasks.index(0,0).data().toString(),"Window 1");QCOMPARE(tasks.index(1,0).data().toString(),"Window 2");
        QTRY_COMPARE(root->property("rowCount").toInt(),3);
        QVariant title;QVERIFY(QMetaObject::invokeMethod(root.data(),"titleAt",Q_RETURN_ARG(QVariant,title),Q_ARG(QVariant,0)));
        QCOMPARE(title.toString(),"Window 1"); // Real QML role names/delegates, without creating a surface.

        first.requestActivate(QString("3"));
        QTRY_COMPARE(second.currentDesktop().toString(),"3");QTRY_COMPARE(qmlInfo->property("currentDesktop").toString(),"3");
        QTRY_COMPARE(filter.index(0,0).data().toString(),"Window 3");
        second.requestActivateOnScreen(QString("1"),b->name());
        QTRY_COMPARE(first.currentDesktopByScreenName(b->name()).toString(),"1");
        first.requestActivateOnScreen(QString("2"),"unknown-output");QTest::qWait(30);
        QCOMPARE(first.currentDesktopByScreenName(b->name()).toString(),"1");
        first.requestCreateDesktop(0);first.requestRemoveDesktop(0);QTest::qWait(30);
        QCOMPARE(first.numberOfDesktops(),3); // Explicitly unsupported capability, not advertised as operational.
        command("invalid");QTest::qWait(30);QCOMPARE(first.numberOfDesktops(),3);
        command("shrink");QTRY_COMPARE(first.numberOfDesktops(),2);QTRY_COMPARE(first.desktopNames(),QStringList({"Renamed One","Two"}));
        QTRY_COMPARE(qmlInfo->property("numberOfDesktops").toInt(),2);QTRY_COMPARE(filter.index(0,0).data().toString(),"Window 1");
        command("reorder");QTRY_COMPARE(first.desktopIds(),QVariantList({QString("2"),QString("1")}));
        QTRY_COMPARE(first.desktopLayoutRows(),2);QTRY_COMPARE(first.position(QString("2")),0u);
        command("recreate");QTRY_COMPARE(first.numberOfDesktops(),3);
        QTRY_COMPARE(first.desktopNames(),QStringList({"Two","Renamed One","New Three"}));
        first.requestActivate(QString("3"));QTRY_COMPARE(second.currentDesktop().toString(),"3");
        windows->setSourceModel(previous); // Source lifetime remains explicit; no dangling native proxy.
    }
    void nativeConnectionBarrierControlsRuntimeAndHandlesProviderLoss(){
        qputenv("BWM_R4_NATIVE_DESKTOPS","1");
        {
            QTemporaryDir directory;QVERIFY(directory.isValid());const QString token(64,'c');
            const auto request=[&](int revision,const QString &skin){
                QSaveFile file(directory.path()+"/control.json");if(!file.open(QIODevice::WriteOnly))return false;
                file.write(QJsonDocument(QJsonObject{{"version",1},{"token",token},{"revision",revision},{"command","skin"},{"skin",skin}}).toJson());return file.commit();
            };
            PanelRuntime runtime(nullptr,directory.path()+"/settings",false);
            QVERIFY(request(0,"default"));RuntimeControl control(&runtime,directory.path(),token);QVERIFY(control.start());
            QTRY_COMPARE(control.revision(),0);
            auto *peer=NativeDesktopControl::requiredControl();QVERIFY(peer);
            QVERIFY(peer->state().value("confirmedPaused").toBool());
            TaskManager::VirtualDesktopInfo info;QTRY_COMPARE(info.numberOfDesktops(),3);
            const auto previous=info.currentDesktop();info.requestActivate(QString("1"));QTest::qWait(40);QCOMPARE(info.currentDesktop(),previous);
            QVERIFY(request(1,"plasma"));QTRY_COMPARE(control.revision(),1);QVERIFY(peer->resumed());
            info.requestActivate(QString("1"));QTRY_COMPARE(info.currentDesktop().toString(),"1");
            info.requestActivate(QString("3"));peer->beginRevision(2);
            QVERIFY(!runtime.setSkin("retro"));QVERIFY(runtime.quiescing());
            {
                QTemporaryDir invalid;QVERIFY(invalid.isValid());QSaveFile bad(invalid.path()+"/control.json");QVERIFY(bad.open(QIODevice::WriteOnly));
                bad.write(QJsonDocument(QJsonObject{{"version",1},{"token",QString(64,'d')},{"revision",0},{"command","skin"},{"skin","retro"}}).toJson());QVERIFY(bad.commit());
                RuntimeControl rejected(&runtime,invalid.path(),token);QVERIFY(!rejected.start());
            } // A previously busy runtime cannot make an invalid control channel acceptable.
            QTRY_VERIFY(peer->state().value("confirmed").toBool());QVERIFY(peer->state().value("confirmedPaused").toBool());
            QCOMPARE(info.currentDesktop().toString(),"1"); // Same flush: pending request cancelled before the barrier ack.
            QVERIFY(request(2,"retro"));QTRY_COMPARE(control.revision(),2);QCOMPARE(runtime.skin(),"retro");
            info.requestActivate(QString("3"));QTest::qWait(40);QCOMPARE(info.currentDesktop().toString(),"1");
            QVERIFY(request(3,"plasma"));QTRY_COMPARE(control.revision(),3);QVERIFY(peer->resumed());
            command("unavailable");QTRY_VERIFY(!peer->state().value("providerAvailable").toBool());
            QVERIFY(!runtime.setSkin("plasma"));QVERIFY(!runtime.quiescing());QVERIFY(runtime.error().contains("unavailable"));
            command("available");QTRY_VERIFY(peer->resumed());
            command("withdraw");QTRY_VERIFY(!peer->state().value("connected").toBool());
            QVERIFY(runtime.setSkin("retro")); // A lost provider must not trap logout/withdrawal.
            QVERIFY(!runtime.setSkin("plasma"));QVERIFY(runtime.error().contains("unavailable"));
            command("restore");QTRY_VERIFY(peer->state().value("connected").toBool());QTRY_VERIFY(peer->resumed());
            QVERIFY(request(4,"plasma"));QTRY_COMPARE(control.revision(),4);QCOMPARE(runtime.skin(),"plasma");
            QTRY_COMPARE(info.numberOfDesktops(),3);info.requestActivate(QString("2"));QTRY_COMPARE(info.currentDesktop().toString(),"2");
            {
                const int input=qEnvironmentVariableIntValue("BWM_R4_DESKTOP_TEST_FD");
                struct Resume {int fd;bool active=true;~Resume(){if(active)::write(fd,"unstall\n",8);}} resume{input};
                command("stall");
                pollfd ready{qEnvironmentVariableIntValue("BWM_R4_FIXTURE_NOTIFY_FD"),POLLIN,0};QCOMPARE(::poll(&ready,1,1000),1);
                char notification[8];QCOMPARE(::read(ready.fd,notification,8),8);QCOMPARE(QByteArray(notification,8),"stalled\n");
                peer->beginRevision(5);QVERIFY(!runtime.setSkin("retro"));QVERIFY(runtime.quiescing());
                QTRY_VERIFY(peer->state().value("lastError").toString().contains("timed out"));
                QCOMPARE(control.revision(),4);QCOMPARE(runtime.skin(),"plasma");QVERIFY(!peer->state().value("confirmed").toBool());
                QCOMPARE(::write(input,"unstall\n",8),8);resume.active=false;
                QTest::qWait(50);QVERIFY(!peer->state().value("confirmed").toBool()); // Late ack cannot convert timeout into success.
            }
            QVERIFY(request(6,"retro"));QTRY_COMPARE(control.revision(),6);QCOMPARE(runtime.skin(),"retro");
            QVERIFY(request(7,"plasma"));QTRY_COMPARE(control.revision(),7);QVERIFY(peer->resumed());
            QVERIFY(request(8,"retro"));QTRY_COMPARE(control.revision(),8);
            const auto oldSerial=peer->state().value("serial").toUInt();
            command("withdraw");QTRY_VERIFY(!peer->state().value("connected").toBool());QVERIFY(runtime.setSkin("retro"));
            command("restore");QTRY_VERIFY(peer->state().value("connected").toBool());
            QTRY_VERIFY(peer->state().value("confirmed").toBool() && peer->state().value("serial").toUInt()!=oldSerial);
            QVERIFY(peer->state().value("confirmedPaused").toBool());QVERIFY(!peer->resumed());
            QVERIFY(request(9,"plasma"));QTRY_COMPARE(control.revision(),9);QVERIFY(peer->resumed());
        }
        qunsetenv("BWM_R4_NATIVE_DESKTOPS");
    }
    void desktopAmbiguityRequiresFreshAuxiliaryProcess(){
        NativeDesktopControl gate;
        QTRY_VERIFY(gate.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        TaskManager::VirtualDesktopInfo info;QTRY_COMPARE(info.numberOfDesktops(),3);
        command("extra-desktop");
        auto inventory=[&]{return gate.state().value("registry").toMap();};
        QTRY_COMPARE(inventory().value("managementGlobals").toInt(),2);
        QVERIFY(inventory().value("restartRequired").toBool());QVERIFY(!gate.resumed());
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        command("drop-extras");QTRY_COMPARE(inventory().value("managementGlobals").toInt(),1);
        QVERIFY(!inventory().value("topologyCompatible").toBool());
        QCOMPARE(gate.ensurePaused(false),NativeDesktopControl::Status::Unavailable);
        QVERIFY(gate.state().value("lastError").toString().contains("restart this auxiliary"));
        QTRY_VERIFY(gate.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        NativeDesktopControl another;
        QCOMPARE(another.ensurePaused(false),NativeDesktopControl::Status::Unavailable); // Same process cannot reset KDE's private static backend.
        QCOMPARE(another.ensurePaused(true),NativeDesktopControl::Status::Ready);
        command("registry-append");
        pollfd appended{qEnvironmentVariableIntValue("BWM_R4_FIXTURE_NOTIFY_FD"),POLLIN,0};QCOMPARE(::poll(&appended,1,1000),1);
        char receipt[9];QCOMPARE(::read(appended.fd,receipt,9),9);QCOMPARE(QByteArray(receipt,9),"appended\n");
        QProcess fresh;auto env=QProcessEnvironment::systemEnvironment();
        const int second=qEnvironmentVariableIntValue("BWM_R4_SECOND_CLIENT_FD");
        env.insert("WAYLAND_SOCKET",QString::number(second));fresh.setProcessEnvironment(env);
        fresh.setChildProcessModifier([second]{if(::fcntl(second,F_SETFD,0)<0)::_exit(74);});
        fresh.start(QCoreApplication::applicationFilePath(),{"--fresh-registry-check"});
        QVERIFY(fresh.waitForFinished(5000));
        QVERIFY2(fresh.exitStatus()==QProcess::NormalExit && fresh.exitCode()==0,fresh.readAllStandardError().constData());
        QTest::qWait(50);QCOMPARE(info.numberOfDesktops(),0); // KDE lost the old binding; the fresh child sees four.
    }
};
int main(int argc,char **argv){
    if(!qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE") || qEnvironmentVariable("QT_QPA_PLATFORM")!="wayland" ||
        qEnvironmentVariableIsEmpty("WAYLAND_SOCKET") || qEnvironmentVariableIsEmpty("BWM_R4_DESKTOP_TEST_FD")){
        std::fputs("This test requires check-desktops.py and its private Wayland fixture.\n",stderr);return 70;
    }
    QGuiApplication app(argc,argv);
    if(app.arguments().contains("--fresh-registry-check")){
        NativeDesktopControl gate;TaskManager::VirtualDesktopInfo info;QTimer poll;bool pausing=false;
        QObject::connect(&poll,&QTimer::timeout,&app,[&]{
            if(gate.ensurePaused(pausing)==NativeDesktopControl::Status::Ready){if(pausing && info.numberOfDesktops()==4)app.exit(0);else if(!pausing)pausing=true;}
        });
        poll.start(10);QTimer::singleShot(3000,&app,[&]{app.exit(73);});return app.exec();
    }
    DesktopTest test;return QTest::qExec(&test,argc,argv);
}
#include "test-desktops.moc"

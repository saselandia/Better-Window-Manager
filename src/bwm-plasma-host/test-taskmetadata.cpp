// SPDX-License-Identifier: GPL-2.0-or-later
#include "tasksource.h"
#include "tests/task-app-fixture.h"
#include <tasksmodel.h>
#include <startuptasksmodel.h>
#include <windowtasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QStandardItemModel>
#include <KSycoca>
#include <KService>
#include <QDir>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QPersistentModelIndex>
#include <QProcess>
#include <QSaveFile>
#include <QScopeGuard>
#include <QtTest>
#include <memory>

class MetadataTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void delegateApplicationFixtureResolvesBeforePidFallback(){
        TaskApplicationFixture application;
        QVERIFY2(application.prepare(qEnvironmentVariable("BWM_R4_LOCAL_TEST_ROOT"),QStringLiteral(BWM_TEST_SYCOCA_PROGRAM)),qPrintable(application.error));
        const QJsonObject row{{"address","0xabc"},{"pid",int(QCoreApplication::applicationPid())},{"generation","1"},
            {"title","BWM native delegate"},{"appId",application.id},{"workspace","1"},
            {"geometry",QJsonArray{10,20,800,600}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",true},{"minimized",false},{"maximized",false},{"fullscreen",false},
            {"fullscreenable",true},{"urgent",false},{"onAllDesktops",false}};
        BwmTaskSource source;QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{row}}}));
        using Roles=TaskManager::AbstractTasksModel;
        QCOMPARE(source.index(0).data(Roles::AppId).toString(),application.id+".desktop");
        QCOMPARE(source.index(0).data(Roles::AppName).toString(),application.name);
        QCOMPARE(source.index(0).data(Qt::DecorationRole).value<QIcon>().pixmap(16,16).toImage().pixelColor(8,8),QColor(Qt::red));
    }
    void nativeTaskProxyRoutesApplicationRequestsAndRefreshesCapability(){
        const auto root=qEnvironmentVariable("BWM_R4_LOCAL_TEST_ROOT");QVERIFY(!root.isEmpty());
        const auto id="org.bwm.r4.launch.capability."+QString::number(QCoreApplication::applicationPid());
        const auto desktop=root+"/data/applications/"+id+".desktop";QVERIFY(QDir().mkpath(root+"/data/applications"));
        const auto cleanup=qScopeGuard([&]{QFile::remove(desktop);});
        const auto write=[&](bool single){
            QFile file(desktop);if(!file.open(QIODevice::WriteOnly|QIODevice::Truncate))return false;
            file.write(QString("[Desktop Entry]\nType=Application\nName=Launch capability fixture\nExec=/usr/bin/false\nSingleMainWindow=%1\n").arg(single?"true":"false").toUtf8());file.close();
            QProcess build;build.start(QStringLiteral(BWM_TEST_SYCOCA_PROGRAM),{"--noincremental"});
            return build.waitForFinished(10000) && build.exitCode()==0;
        };
        QVERIFY(write(false));
        QTRY_VERIFY(KService::serviceByStorageId(id+".desktop"));
        const QJsonObject row{{"address","0x987"},{"pid",2147483647},{"generation","1"},{"title","Launch fixture"},{"appId",id},
            {"workspace","1"},{"geometry",QJsonArray{0,0,400,300}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",false},{"minimized",false},{"maximized",false},{"fullscreen",false},{"urgent",false},{"onAllDesktops",false}};
        BwmTaskSource source;QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{row}}}));
        TaskManager::TasksModel tasks;tasks.componentComplete();QStandardItemModel startup(0,1);
        for(auto *concat:tasks.findChildren<QConcatenateTablesProxyModel*>())for(auto *proxy:concat->sourceModels()){
            if(auto *s=qobject_cast<TaskManager::StartupTasksModel*>(proxy);s && s->columnCount()==0)s->setSourceModel(&startup);
            if(auto *w=qobject_cast<TaskManager::WindowTasksModel*>(proxy))w->setSourceModel(&source);
        }
        tasks.setLauncherList({});tasks.setFilterByCurrentVirtualDesktop(false);tasks.setFilterByActivity(false);tasks.setFilterByScreen(false);
        tasks.setGroupMode(TaskManager::TasksModel::GroupDisabled);QTRY_COMPARE(tasks.rowCount(),1);
        using Roles=TaskManager::AbstractTasksModel;
        QPersistentModelIndex held=source.index(0);QVERIFY(tasks.index(0,0).data(Roles::CanLaunchNewInstance).toBool());
        QSignalSpy requests(&source,&BwmTaskSource::actionRequested),changes(&source,&BwmTaskSource::dataChanged);
        tasks.requestNewInstance(tasks.index(0,0));QCOMPARE(requests.count(),1);
        QCOMPARE(requests.first().first().toJsonObject().value("action").toString(),"new-instance");
        const QList<QUrl> urls{QUrl::fromLocalFile(root+"/own file.txt"),QUrl("https://example.invalid/file?q=a%20b")};
        tasks.requestOpenUrls(tasks.index(0,0),urls);QCOMPARE(requests.count(),2);
        const auto payload=requests.last().first().toJsonObject();QCOMPARE(payload.value("action").toString(),"open-urls");
        QCOMPARE(payload.value("urls").toArray()[0].toString(),urls[0].toString(QUrl::FullyEncoded));
        tasks.requestOpenUrls(tasks.index(0,0),{});source.requestOpenUrls(held,{QUrl("relative-file")});QCOMPARE(requests.count(),2);
        QVERIFY(write(true));QTRY_VERIFY(!held.data(Roles::CanLaunchNewInstance).toBool());
        QTRY_VERIFY(([&]{for(const auto &change:changes)if(change.at(2).value<QList<int>>().contains(Roles::CanLaunchNewInstance))return true;return false;})());
        tasks.requestNewInstance(tasks.index(0,0));QCOMPARE(requests.count(),3); // Menu visibility does not block explicit native requests.
        tasks.requestOpenUrls(tasks.index(0,0),urls);QCOMPARE(requests.count(),4); // Single-window apps can still open documents.
        source.clear();source.requestNewInstance(held);source.requestOpenUrls(held,urls);QCOMPARE(requests.count(),4);
    }
    void nativeDatabaseRefreshesBothSourcesWithoutReplacingWindows(){
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        QVERIFY(qEnvironmentVariableIsEmpty("KDESYCOCA"));
        const QString root=qEnvironmentVariable("BWM_R4_LOCAL_TEST_ROOT");
        QVERIFY(!root.isEmpty());
        QCOMPARE(qEnvironmentVariable("XDG_DATA_HOME"),root+"/data");
        QCOMPARE(qEnvironmentVariable("XDG_CACHE_HOME"),root+"/cache");
        const QString id="org.bwm.r4.metadata."+QString::number(QCoreApplication::applicationPid());
        const QString directory=root+"/data/applications";
        QVERIFY(QDir().mkpath(directory));
        const QString desktop=directory+'/'+id+".desktop",red=root+"/red.png",blue=root+"/blue.png";
        auto cleanup=qScopeGuard([&]{QFile::remove(desktop);QFile::remove(red);QFile::remove(blue);});
        QImage image(16,16,QImage::Format_ARGB32);image.fill(Qt::red);QVERIFY(image.save(red));
        image.fill(Qt::blue);QVERIFY(image.save(blue));
        const auto write=[&](const QString &name,const QString &icon){
            QSaveFile file(desktop);if(!file.open(QIODevice::WriteOnly))return false;
            file.write(QString("[Desktop Entry]\nType=Application\nName=%1\nGenericName=Native metadata fixture\nExec=/usr/bin/false\nIcon=%2\nNoDisplay=true\n").arg(name,icon).toUtf8());
            return file.commit();
        };
        const auto rebuild=[](){
            QProcess build;build.start(QStringLiteral(BWM_TEST_SYCOCA_PROGRAM),{"--noincremental"});
            return build.waitForFinished(10000) && build.exitStatus()==QProcess::NormalExit && build.exitCode()==0;
        };
        QVERIFY(write("First metadata",red));QVERIFY(rebuild());
        // Another test can already hold KSycoca open. Wait for native cache
        // delivery during setup, just as the later update checks do.
        QTRY_VERIFY(([&]{const auto service=KService::serviceByStorageId(id+".desktop");return service && service->name()=="First metadata";})());
        QVERIFY(KSycoca::absoluteFilePath().startsWith(root+"/cache/"));
        const QJsonObject row{{"address","0xabc"},{"pid",2147483647},{"generation","1"},{"title","Stable window title"},
            {"appId",id},{"workspace","2"},{"geometry",QJsonArray{0,0,800,600}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",false},{"minimized",false},{"maximized",false},{"fullscreen",false},{"urgent",false},{"onAllDesktops",false}};
        const QJsonObject snapshot{{"version",1},{"windows",QJsonArray{row}}};
        BwmTaskSource first,second;QVERIFY(first.apply(snapshot));QVERIFY(second.apply(snapshot));
        using Roles=TaskManager::AbstractTasksModel;
        QPersistentModelIndex held=first.index(0),other=second.index(0);
        const auto uuid=held.data(Roles::WinIdList),secondUuid=other.data(Roles::WinIdList);
        QCOMPARE(held.data(Roles::AppName).toString(),"First metadata");
        QCOMPARE(held.data(Qt::DecorationRole).value<QIcon>().pixmap(16,16).toImage().pixelColor(8,8),QColor(Qt::red));
        QSignalSpy changes(&first,&BwmTaskSource::dataChanged),resets(&first,&BwmTaskSource::modelReset);
        QSignalSpy database(KSycoca::self(),&KSycoca::databaseChanged);
        QVERIFY(write("Updated metadata",blue));QVERIFY(rebuild());
        QTRY_VERIFY_WITH_TIMEOUT(!database.isEmpty(),10000); // Real KDirWatch/cache notification, no signal injection.
        QTRY_COMPARE(held.data(Roles::AppName).toString(),"Updated metadata");
        QTRY_COMPARE(other.data(Roles::AppName).toString(),"Updated metadata");
        QCOMPARE(held.data(Qt::DecorationRole).value<QIcon>().pixmap(16,16).toImage().pixelColor(8,8),QColor(Qt::blue));
        QVERIFY(!changes.isEmpty());const auto roles=changes.last().at(2).value<QList<int>>();
        for(int role:QList<int>{Qt::DecorationRole,Roles::AppId,Roles::AppName,Roles::GenericName,Roles::LauncherUrl,Roles::LauncherUrlWithoutIcon})QVERIFY(roles.contains(role));
        QCOMPARE(held.data().toString(),"Stable window title");QCOMPARE(held.data(Roles::WinIdList),uuid);
        QCOMPARE(other.data(Roles::WinIdList),secondUuid);QCOMPARE(resets.count(),0);
        // Removing the package clears stale app metadata without another IPC snapshot.
        database.clear();QVERIFY(QFile::remove(desktop));QVERIFY(rebuild());
        QTRY_VERIFY_WITH_TIMEOUT(!database.isEmpty(),10000);
        QTRY_VERIFY(held.data(Roles::AppName).toString()!="Updated metadata");
        QTRY_VERIFY(other.data(Roles::AppName).toString()!="Updated metadata");
        QCOMPARE(held.data(Roles::GenericName).toString(),QString());
        const auto fallback=TaskManager::appDataFromUrl(TaskManager::windowUrlFromMetadata(id,2147483647),QIcon::fromTheme("application-x-executable"));
        QCOMPARE(held.data(Roles::LauncherUrl).toUrl(),fallback.url);
        QVERIFY(held.isValid());QCOMPARE(held.data(Roles::WinIdList),uuid);
        database.clear();QVERIFY(write("Reinstalled metadata",red));QVERIFY(rebuild());
        QTRY_VERIFY_WITH_TIMEOUT(!database.isEmpty(),10000);
        QTRY_COMPARE(held.data(Roles::AppName).toString(),"Reinstalled metadata");
        QTRY_COMPARE(other.data(Roles::AppName).toString(),"Reinstalled metadata");
        QCOMPARE(held.data(Roles::WinIdList),uuid);QCOMPARE(resets.count(),0);
        // A pending database notification must not outlive its source, and an
        // empty source must remain safe while another source reads the update.
        auto transient=std::make_unique<BwmTaskSource>();QVERIFY(transient->apply(snapshot));
        database.clear();QVERIFY(write("Lifecycle metadata",blue));QVERIFY(rebuild());
        QTRY_VERIFY_WITH_TIMEOUT(!database.isEmpty(),10000);
        transient.reset();second.clear();QVERIFY(!other.isValid());
        QTRY_COMPARE(held.data(Roles::AppName).toString(),"Lifecycle metadata");
        QVERIFY(second.apply(snapshot));QCOMPARE(second.index(0).data(Roles::AppName).toString(),"Lifecycle metadata");
        QCOMPARE(held.data(Roles::WinIdList),uuid);QCOMPARE(resets.count(),0);
    }
};
QTEST_MAIN(MetadataTest)
#include "test-taskmetadata.moc"

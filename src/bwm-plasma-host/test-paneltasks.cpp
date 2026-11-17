// SPDX-License-Identifier: GPL-2.0-or-later
// Real PanelSession registration and original KDE launcher/window merging.
#include "panelsession.h"
#include "taskbridge.h"
#include "taskpreview.h"
#include "tasklauncher.h"
#include "launchrouter.h"
#include "tests/task-app-fixture.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <KConfigGroup>
#include <KConfigLoader>
#include <tasksmodel.h>
#include <startuptasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QStandardItemModel>
#include <QQuickWindow>
#include <QQuickItem>
#include <QJsonDocument>
#include <QSaveFile>
#include <QScreen>
#include <QMenu>
#include <QAction>
#include <QApplication>
#include <QProcess>
#include <KService>
#include <QtTest>
class PanelTaskCorona:public Plasma::Corona {
public:QRect screenGeometry(int)const override{return {0,0,1920,1080};}
};
QQuickItem *taskDelegate(QQuickItem *root){
    if(root->metaObject()->indexOfMethod("showContextMenu(QVariant)")>=0)return root;
    for(auto *child:root->childItems())if(auto *found=taskDelegate(child))return found;return nullptr;
}
// KDE's KAcceleratorManager adds mnemonics when a menu is shown.
QString plainText(const QAction *action){QString text=action->text();text.replace("&&","\x01");text.remove('&');text.replace("\x01","&");return text;}
QMenu *visibleMenuWith(const QString &text){
    for(auto *widget:QApplication::topLevelWidgets())if(auto *menu=qobject_cast<QMenu*>(widget);menu && menu->isVisible())
        for(auto *action:menu->actions())if(plainText(action)==text)return menu;
    return nullptr;
}
class PanelTaskTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void panelRegistrationFindsVisualAppletAndMergesItsLauncher(){
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        const auto root=qEnvironmentVariable("BWM_R4_LOCAL_TEST_ROOT");
        const auto clients=qEnvironmentVariable("BWM_R4_FAKE_CLIENTS");
        QVERIFY(!root.isEmpty() && clients.startsWith(root+'/'));
        TaskApplicationFixture application;
        QVERIFY2(application.prepare(root,QStringLiteral(BWM_TEST_SYCOCA_PROGRAM)),qPrintable(application.error));
        QFile input(clients);QVERIFY(input.open(QIODevice::ReadOnly));
        auto client=QJsonDocument::fromJson(input.readAll()).object();input.close();
        client["class"]=application.id;client["mapped"]=true;client["title"]="Panel registration fixture";
        const auto screen=qGuiApp->primaryScreen()->geometry();
        client["fixtureScreen"]=QJsonArray{screen.x(),screen.y(),screen.width(),screen.height()};
        QSaveFile replacement(clients);QVERIFY(replacement.open(QIODevice::WriteOnly));
        replacement.write(QJsonDocument(client).toJson());QVERIFY(replacement.commit());
        qputenv("BWM_R4_TASK_ACTIONS","1");
        qputenv("BWM_R4_TASK_RUNTIME",qgetenv("XDG_RUNTIME_DIR"));
        qputenv("BWM_R4_TASK_CONFIG",qgetenv("XDG_CONFIG_HOME"));
        PanelTaskCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c && !c->failedToLaunch());
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *applet=c->createApplet("org.kde.plasma.taskmanager");QVERIFY(applet && !applet->failedToLaunch());
        auto *other=c->createApplet("org.kde.plasma.taskmanager");QVERIFY(other && !other->failedToLaunch());
        for(auto *a:{applet,other}){
            auto *scheme=a->configScheme();QVERIFY(scheme);
            auto *launchers=scheme->KCoreConfigSkeleton::findItem("launchers");QVERIFY(launchers);
            auto *desktopFilter=scheme->KCoreConfigSkeleton::findItem("showOnlyCurrentDesktop");QVERIFY(desktopFilter);
            QVERIFY(desktopFilter->property().toBool()); // Unmodified KDE default requires a desktop backend.
            launchers->setProperty(QStringList{"applications:"+application.id+".desktop"});QVERIFY(scheme->save());
        }
        QString error;QVERIFY2(prepareAllDesktopTaskPreview({applet,other},&error),qPrintable(error));
        PanelSession session(c,false);
        QQuickWindow window;window.resize(640,48);
        auto *panel=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(panel);
        panel->setParentItem(window.contentItem());panel->setSize({640,48});
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);QVERIFY(item);
        auto *otherItem=PlasmaQuick::AppletQuickItem::itemForApplet(other);QVERIFY(otherItem);
        session.bindPanelItem(panel); // The production path: do NOT attach the applet to the bridge by hand.
        window.show();
        QList<TaskManager::TasksModel*> models;
        QStandardItemModel startup(0,1);
        for(auto *i:{item,otherItem}){
            QTRY_VERIFY(!i->findChildren<TaskManager::TasksModel*>().isEmpty());
            auto *tasks=i->findChildren<TaskManager::TasksModel*>().first();models.append(tasks);
            QVERIFY(!tasks->filterByCurrentVirtualDesktop()); // Native option; no filter setter in the test.
            for(auto *concat:tasks->findChildren<QConcatenateTablesProxyModel*>())for(auto *source:concat->sourceModels())
                if(auto *s=qobject_cast<TaskManager::StartupTasksModel*>(source);s && s->columnCount()==0)s->setSourceModel(&startup);
        }
        QTRY_COMPARE_WITH_TIMEOUT(BwmTaskBridge::diagnostics().value("boundModels").toInt(),1,2000);
        QTRY_VERIFY_WITH_TIMEOUT(BwmTaskBridge::diagnostics().value("snapshotAvailable").toBool(),3000);
        QTRY_COMPARE(BwmTaskBridge::diagnostics().value("windowCount").toInt(),1);
        for(auto *tasks:models)QTRY_COMPARE(tasks->rowCount(),1);
        QCOMPARE(BwmTaskBridge::diagnostics().value("currentDesktopFilteringViews").toInt(),0);
        QCOMPARE(BwmTaskBridge::diagnostics().value("visibleWindowRows").toInt(),2);
        auto *bridge=qApp->findChild<BwmTaskBridge*>();QVERIFY(bridge);
        QSignalSpy actions(bridge->source(),&BwmTaskSource::actionRequested);
        for(auto *tasks:models){
            const auto index=tasks->index(0,0);
            QVERIFY(index.data(TaskManager::AbstractTasksModel::IsWindow).toBool());
            QVERIFY(!index.data(TaskManager::AbstractTasksModel::IsLauncher).toBool());
            QVERIFY(index.data(TaskManager::AbstractTasksModel::HasLauncher).toBool());
            QCOMPARE(index.data(TaskManager::AbstractTasksModel::AppName).toString(),application.name);
            tasks->requestActivate(index);
        }
        QCOMPARE(actions.count(),2);
        for(const auto &action:actions)QCOMPARE(action.first().toJsonObject().value("action").toString(),"focus");
        QTRY_VERIFY(!bridge->state().value("actionInFlight").toBool() && bridge->state().value("pendingActions").toInt()==0);
        QVERIFY2(bridge->error().isEmpty(),qPrintable(bridge->error()));
        // Hidden storage may belong to another monitor. With the explicit
        // all-desktops option the minimized window must remain actionable.
        QFile current(clients);QVERIFY(current.open(QIODevice::ReadOnly));
        auto hidden=QJsonDocument::fromJson(current.readAll()).object();current.close();
        hidden["workspace"]=QJsonObject{{"id",-98},{"name","special:minimized"}};
        hidden["tags"]=QJsonArray{"omarchy-minimized-from-1"};
        hidden["fixtureScreen"]=QJsonArray{screen.x()+screen.width(),screen.y(),screen.width(),screen.height()};
        QSaveFile minimize(clients);QVERIFY(minimize.open(QIODevice::WriteOnly));
        minimize.write(QJsonDocument(hidden).toJson());QVERIFY(minimize.commit());
        for(auto *tasks:models){
            QTRY_COMPARE(tasks->rowCount(),1);
            QTRY_VERIFY(tasks->index(0,0).data(TaskManager::AbstractTasksModel::IsMinimized).toBool());
        }
        auto *secondModel=models.last();
        secondModel->requestToggleMinimized(secondModel->index(0,0));
        secondModel->requestActivate(secondModel->index(0,0)); // Original KDE minimized activation sequence.
        QCOMPARE(actions.count(),4);
        QCOMPARE(actions.at(2).first().toJsonObject().value("action").toString(),"toggle-minimize");
        QCOMPARE(actions.at(3).first().toJsonObject().value("action").toString(),"focus");
        for(auto *tasks:models)QTRY_VERIFY(!tasks->index(0,0).data(TaskManager::AbstractTasksModel::IsMinimized).toBool());
        QTRY_VERIFY(!bridge->state().value("actionInFlight").toBool() && bridge->state().value("pendingActions").toInt()==0);
        QVERIFY2(bridge->error().isEmpty(),qPrintable(bridge->error()));
        QTRY_VERIFY(BwmTaskBridge::suspendAll(true));
    }
    void pinnedLauncherAndDesktopActionsLeaveTheHost(){
        // No window: KDE's LauncherTasksModel row and the original task menu.
        // The disposable host itself must never start them (KIOSK policy written
        // by the runner like preview-isolated.py); the router/menu policy queue
        // them for the launch helper instead.
        QVERIFY(nativeInProcessLaunchDenied());
        const auto root=qEnvironmentVariable("BWM_R4_LOCAL_TEST_ROOT");const auto clients=qEnvironmentVariable("BWM_R4_FAKE_CLIENTS");
        QVERIFY(!root.isEmpty() && clients.startsWith(root+'/'));
        QFile input(clients);QVERIFY(input.open(QIODevice::ReadOnly));
        auto client=QJsonDocument::fromJson(input.readAll()).object();input.close();
        client["mapped"]=false; // Valid snapshot with zero windows.
        QSaveFile replacement(clients);QVERIFY(replacement.open(QIODevice::WriteOnly));
        replacement.write(QJsonDocument(client).toJson());QVERIFY(replacement.commit());
        const auto id=QStringLiteral("org.bwm.r4.pinned.%1").arg(QCoreApplication::applicationPid());
        const auto marker=root+"/in-process-launch-marker";QFile::remove(marker);
        QSaveFile desktop(root+"/data/applications/"+id+".desktop");QVERIFY(desktop.open(QIODevice::WriteOnly));
        const auto entry=QStringLiteral("[Desktop Entry]\nType=Application\nName=BWM pinned launcher fixture\nExec=/usr/bin/touch %1\n"
            "Categories=FileManager;\nActions=compose;hidden;after;\n"
            "[Desktop Action compose]\nName=Compose & send\nExec=/usr/bin/touch %1\n"
            "[Desktop Action hidden]\nName=Hidden fixture action\nNoDisplay=true\nExec=/usr/bin/touch %1\n"
            "[Desktop Action after]\nName=After fixture\nExec=/usr/bin/touch %1\n").arg(marker).toUtf8();
        QVERIFY(desktop.write(entry)==entry.size() && desktop.commit());
        QProcess build;build.start(QStringLiteral(BWM_TEST_SYCOCA_PROGRAM),{"--noincremental"});
        QVERIFY(build.waitForFinished(10000) && build.exitCode()==0);
        QTRY_VERIFY_WITH_TIMEOUT(KService::serviceByStorageId(id+".desktop") && KService::serviceByStorageId(id+".desktop")->actions().size()==3,3000);
        QCOMPARE(nativeJumpListActions(QUrl("applications:"+id+".desktop")).size(),2); // NoDisplay filtered like Backend.
        BwmTaskBridge::suspendAll(false);
        PanelTaskCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c && !c->failedToLaunch());
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *applet=c->createApplet("org.kde.plasma.taskmanager");QVERIFY(applet && !applet->failedToLaunch());
        auto *scheme=applet->configScheme();QVERIFY(scheme);
        scheme->KCoreConfigSkeleton::findItem("launchers")->setProperty(QStringList{"applications:"+id+".desktop"});QVERIFY(scheme->save());
        QString error;QVERIFY2(prepareAllDesktopTaskPreview({applet},&error),qPrintable(error));
        PanelSession session(c,false);
        QQuickWindow window;window.resize(640,48);
        auto *panel=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(panel);
        panel->setParentItem(window.contentItem());panel->setSize({640,48});
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);QVERIFY(item);
        session.bindPanelItem(panel);window.show();
        QStandardItemModel startup(0,1);
        QTRY_VERIFY(!item->findChildren<TaskManager::TasksModel*>().isEmpty());
        auto *tasks=item->findChildren<TaskManager::TasksModel*>().first();
        for(auto *concat:tasks->findChildren<QConcatenateTablesProxyModel*>())for(auto *source:concat->sourceModels())
            if(auto *s=qobject_cast<TaskManager::StartupTasksModel*>(source);s && s->columnCount()==0)s->setSourceModel(&startup);
        QTRY_VERIFY_WITH_TIMEOUT(BwmTaskBridge::diagnostics().value("snapshotAvailable").toBool(),3000);
        QTRY_COMPARE_WITH_TIMEOUT(BwmTaskBridge::diagnostics().value("applicationLauncher").toMap().value("pinnedLauncherRoutes").toInt(),1,3000);
        QVERIFY(BwmTaskBridge::diagnostics().value("applicationLauncher").toMap().value("inProcessLaunchDenied").toBool());
        QTRY_COMPARE(tasks->rowCount(),1);
        const auto index=tasks->index(0,0);
        QVERIFY(index.data(TaskManager::AbstractTasksModel::IsLauncher).toBool());
        QVERIFY(!index.data(TaskManager::AbstractTasksModel::IsWindow).toBool());
        QVERIFY(tasks->findChildren<BwmLaunchRouter*>().isEmpty()); // Owned by the bridge; KDE's concatenation stays untouched.
        auto *bridge=qApp->findChild<BwmTaskBridge*>();QVERIFY(bridge);
        QSignalSpy launches(bridge,&BwmTaskBridge::launchQueued);
        QSignalSpy windowActions(bridge->source(),&BwmTaskSource::actionRequested);
        const auto expected="applications:"+id+".desktop";
        tasks->requestActivate(index);tasks->requestNewInstance(index);
        tasks->requestOpenUrls(index,{QUrl::fromLocalFile(root+"/dropped file.txt")});
        tasks->requestOpenUrls(index,{}); // KDE ignores an empty drop.
        QCOMPARE(launches.count(),3);QCOMPARE(windowActions.count(),0);
        for(int i=0;i<3;++i){
            const auto request=launches.at(i).first().toJsonObject();
            QCOMPARE(request.value("action").toString(),"launcher");QCOMPARE(request.value("launcherUrl").toString(),expected);
            QCOMPARE(request.value("urls").toArray().size(),i==2?1:0);
        }
        QCOMPARE(launches.at(2).first().toJsonObject().value("urls").toArray().first().toString(),QUrl::fromLocalFile(root+"/dropped file.txt").toString(QUrl::FullyEncoded));
        // Original ContextMenu.qml: Backend jump list + Places (FileManager).
        launches.clear();
        QQuickItem *delegate=nullptr;QTRY_VERIFY(delegate=taskDelegate(item));
        QVERIFY(QMetaObject::invokeMethod(delegate,"showContextMenu",Q_ARG(QVariant,QVariantMap{})));
        QMenu *menu=nullptr;QTRY_VERIFY(menu=visibleMenuWith("Compose & send"));
        QAction *compose=nullptr,*after=nullptr,*newWindow=nullptr;QObject *context=nullptr;
        for(auto *action:menu->actions()){
            if(plainText(action)=="Compose & send"){compose=action;context=action->parent();}
            if(plainText(action)=="After fixture")after=action;
            if(action->parent() && action->parent()->property("icon").toString()=="window-new")newWindow=action;
            QVERIFY(plainText(action)!="Hidden fixture action");
        }
        QVERIFY(compose && after && context);
        // KDE's LauncherTasksModel reports CanLaunchNewInstance=false: no generic entry.
        QVERIFY(!newWindow || !newWindow->isVisible());
        QVERIFY(compose->isEnabled() && after->isEnabled());
        // Places (FileManager): every entry that KDE's KFilePlacesModel shows is
        // routed to the launcher helper with its URL; "N more Places…" and group
        // submenus only reopen/expand KDE's menu and stay enabled.
        QList<QAction*> places;
        for(auto *action:menu->actions())if(action->parent()==context && action!=compose && action!=after && !action->isSeparator() && !action->menu()
            && action->icon().name()!="view-more-symbolic"){QVERIFY2(action->isEnabled(),qPrintable(action->text()));places.append(action);}
        QVERIFY(!places.isEmpty());
        const auto policy=BwmTaskBridge::diagnostics().value("menuPolicy").toMap();
        QVERIFY2(policy.value("lastError").toString().isEmpty(),qPrintable(policy.value("lastError").toString()));
        QCOMPARE(policy.value("maskedLaunchActions").toInt(),0);
        QVERIFY(policy.value("routedLaunchActions").toInt()>=2+places.size());
        const auto entryUrl=QUrl::fromLocalFile(KService::serviceByStorageId(id+".desktop")->entryPath()).toString(QUrl::FullyEncoded);
        places.first()->trigger();QTRY_COMPARE(launches.count(),1);
        const auto place=launches.first().first().toJsonObject();
        QCOMPARE(place.value("action").toString(),"launcher");QCOMPARE(place.value("launcherUrl").toString(),entryUrl);
        QCOMPARE(place.value("urls").toArray().size(),1);
        QVERIFY(QUrl(place.value("urls").toArray().first().toString()).isLocalFile()); // First KDE place: Home.
        launches.clear();
        compose->trigger();after->trigger();
        QTRY_COMPARE(launches.count(),2);
        QCOMPARE(launches.at(0).first().toJsonObject(),(QJsonObject{{"version",1},{"action","service-action"},{"launcherUrl",expected},{"serviceAction","compose"}}));
        QCOMPARE(launches.at(1).first().toJsonObject().value("serviceAction").toString(),"after");
        QCOMPARE(windowActions.count(),0);
        // KDE's own handlers stayed connected and were denied by KIOSK: nothing
        // started from inside the host (the queued helper has no launch context here).
        QTest::qWait(800);QVERIFY(!QFile::exists(marker));
        menu->close();
        // KDE's manual launcher sorting still maps through its own concatenation:
        // the router sits above it, never replaces LauncherTasksModel.
        QSaveFile second(root+"/data/applications/"+id+"-second.desktop");QVERIFY(second.open(QIODevice::WriteOnly));
        const auto secondEntry=QStringLiteral("[Desktop Entry]\nType=Application\nName=BWM second pinned fixture\nExec=/usr/bin/touch %1\n").arg(marker).toUtf8();
        QVERIFY(second.write(secondEntry)==secondEntry.size() && second.commit());
        build.start(QStringLiteral(BWM_TEST_SYCOCA_PROGRAM),{"--noincremental"});QVERIFY(build.waitForFinished(10000) && build.exitCode()==0);
        QTRY_VERIFY_WITH_TIMEOUT(KService::serviceByStorageId(id+"-second.desktop"),3000);
        const QStringList order{"applications:"+id+".desktop","applications:"+id+"-second.desktop"};
        tasks->setLauncherList(order);QTRY_COMPARE(tasks->rowCount(),2);
        QCOMPARE(tasks->sortMode(),TaskManager::TasksModel::SortManual);
        QCOMPARE(tasks->index(0,0).data(TaskManager::AbstractTasksModel::LauncherUrlWithoutIcon).toUrl().toString(),order.first());
        QVERIFY(tasks->move(0,1));tasks->syncLaunchers();
        QCOMPARE(tasks->launcherList(),(QStringList{order.last(),order.first()}));
        QCOMPARE(tasks->index(0,0).data(TaskManager::AbstractTasksModel::LauncherUrlWithoutIcon).toUrl().toString(),order.last());
        launches.clear();tasks->requestActivate(tasks->index(0,0));QCOMPARE(launches.count(),1);
        QCOMPARE(launches.first().first().toJsonObject().value("launcherUrl").toString(),order.last());
        QFile::remove(root+"/data/applications/"+id+"-second.desktop");
        QTRY_VERIFY(!bridge->state().value("actionInFlight").toBool());
        QTRY_VERIFY(BwmTaskBridge::suspendAll(true));
        QFile::remove(root+"/data/applications/"+id+".desktop");
    }
};
QTEST_MAIN(PanelTaskTest)
#include "test-paneltasks.moc"

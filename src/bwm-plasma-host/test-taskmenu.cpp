// SPDX-License-Identifier: GPL-2.0-or-later
#include "tasksource.h"
#include "taskmenupolicy.h"
#include "tests/task-qml-source.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <KConfigGroup>
#include <tasksmodel.h>
#include <startuptasksmodel.h>
#include <windowtasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QStandardItemModel>
#include <QQuickWindow>
#include <QQuickItem>
#include <QApplication>
#include <QMenu>
#include <QAction>
#include <QJsonArray>
#include <QQmlContext>
#include <QQmlEngine>
#include <QScopeGuard>
#include <QtTest>
class MenuCorona:public Plasma::Corona{public:QRect screenGeometry(int)const override{return {0,0,1024,768};}};
QQuickItem *task(QQuickItem *root){
    if(root->metaObject()->indexOfMethod("showContextMenu(QVariant)")>=0)return root;
    for(auto *child:root->childItems())if(auto *found=task(child))return found;return nullptr;
}
QAction *action(QMenu *menu,const QString &icon){
    for(auto *a:menu->actions()){
        if(a->parent() && a->parent()->property("icon").toString()==icon)return a;
        if(a->menu())if(auto *found=action(a->menu(),icon))return found;
    }return nullptr;
}
QJsonObject fixtureWindow(const QString &address,const QString &title){
    return {{"address",address},{"pid",int(QCoreApplication::applicationPid())},
        {"generation","1"},{"title",title},{"appId","bwm-menu-fixture"},{"workspace","1"},
        {"geometry",QJsonArray{10,20,800,600}},{"screen",QJsonArray{0,0,1024,768}},
        {"active",false},{"minimized",false},{"maximized",false},{"fullscreen",false},{"fullscreenable",true},{"urgent",false},{"onAllDesktops",false}};
}
class MenuTest:public QObject{
    Q_OBJECT
private Q_SLOTS:
    void originalTaskManagerMenuUsesCapabilityMaskAndRoutesSupportedAction(){
        QCOMPARE(QGuiApplication::platformName(),"offscreen");QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        BwmTaskSource source;
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{fixtureWindow("0xabc","Menu fixture")}}}));
        MenuCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c && !c->failedToLaunch());
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *applet=c->createApplet("org.kde.plasma.icontasks");QVERIFY(applet && !applet->failedToLaunch());
        auto config=applet->config();config.writeEntry("launchers",QStringList{});config.writeEntry("showOnlyCurrentDesktop",false);config.writeEntry("showOnlyCurrentActivity",false);config.writeEntry("groupingStrategy",0);
        QQuickWindow window;window.resize(640,48);
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(root);root->setParentItem(window.contentItem());root->setSize({640,48});
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);QVERIFY(item);window.show();
        QStandardItemModel startup(0,1);QList<QPair<QPointer<TaskManager::WindowTasksModel>,QPointer<QAbstractItemModel>>> previous;
        auto restore=qScopeGuard([&]{for(const auto &binding:previous)if(binding.first)binding.first->setSourceModel(binding.second);});
        TaskManager::TasksModel *model=nullptr;
        QTRY_VERIFY(!item->findChildren<TaskManager::TasksModel*>().isEmpty());
        for(auto *tasks:item->findChildren<TaskManager::TasksModel*>()){
            tasks->setLauncherList({});tasks->setFilterByCurrentVirtualDesktop(false);tasks->setFilterByActivity(false);tasks->setFilterByScreen(false);
            tasks->setGroupMode(TaskManager::TasksModel::GroupDisabled);model=tasks;
            for(auto *concat:tasks->findChildren<QConcatenateTablesProxyModel*>())for(auto *proxy:concat->sourceModels()){
                if(auto *s=qobject_cast<TaskManager::StartupTasksModel*>(proxy);s && s->columnCount()==0)s->setSourceModel(&startup); // Offscreen-only fixture.
                if(auto *w=qobject_cast<TaskManager::WindowTasksModel*>(proxy);w && w->sourceModel()!=&source){previous.append({w,w->sourceModel()});w->setSourceModel(&source);}
            }
        }
        QVERIFY(model);QTRY_COMPARE(model->rowCount(),1);
        TaskMenuPolicy policy;policy.attach(item);
        QQuickItem *delegate=nullptr;QTRY_VERIFY(delegate=task(item));
        const auto provenance=taskQmlSource(delegate);
        QVERIFY2(provenance.value("reviewed").toBool(),qPrintable(QJsonDocument::fromVariant(provenance).toJson()));
        QSignalSpy requests(&source,&BwmTaskSource::actionRequested);
        QVERIFY(QMetaObject::invokeMethod(delegate,"showContextMenu",Q_ARG(QVariant,QVariantMap{})));
        QMenu *menu=nullptr;
        QTRY_VERIFY(([&]{for(auto *widget:QApplication::topLevelWidgets())if(auto *m=qobject_cast<QMenu*>(widget);m && m->isVisible() && action(m,"window-close")){menu=m;return true;}return false;})());
        QVERIFY2(policy.state().value("lastError").toString().isEmpty(),qPrintable(policy.state().value("lastError").toString()));
        auto *above=action(menu,"window-keep-above"),*below=action(menu,"window-keep-below"),*capture=action(menu,"view-private"),*minimize=action(menu,"window-minimize");
        QVERIFY(above && below && capture && minimize);
        QVERIFY(!above->isEnabled());QVERIFY(!below->isEnabled());QVERIFY(!capture->isEnabled());QVERIFY(minimize->isEnabled());
        QVERIFY(above->actionGroup() && !above->actionGroup()->isExclusive());
        above->setChecked(true);below->setChecked(true);QVERIFY(above->isChecked() && below->isChecked());
        auto *applicationAction=new QAction(QIcon::fromTheme("window-keep-above"),"Application action",menu);menu->addAction(applicationAction);
        QVERIFY(policy.apply(menu));QVERIFY(applicationAction->isEnabled() && !applicationAction->actionGroup());
        QSignalSpy disabledTrigger(above,&QAction::triggered);above->trigger();QCOMPARE(disabledTrigger.count(),0);QCOMPARE(requests.count(),0);
        minimize->trigger();QTRY_COMPARE(requests.count(),1);QCOMPARE(requests.first().first().toJsonObject().value("action").toString(),"toggle-minimize");
        auto *fullscreen=action(menu,"view-fullscreen");QVERIFY(fullscreen && fullscreen->isEnabled());
        requests.clear();fullscreen->trigger();QTRY_COMPARE(requests.count(),1);
        QCOMPARE(requests.first().first().toJsonObject().value("action").toString(),"fullscreen");
        QCOMPARE(requests.first().first().toJsonObject().value("state"),QJsonValue(true));
        // Disabled group is a mask, not a replacement of the native enabled
        // property. Restore the latest explicit state, never a cached boolean.
        QPointer<QAction> keptAbove=above,keptBelow=below;QPointer<QMenu> originalMenu=menu;above->setEnabled(false);below->setEnabled(true);
        policy.setSuspended(true);
        if(keptAbove)QVERIFY(!keptAbove->isEnabled());if(keptBelow)QVERIFY(keptBelow->isEnabled());
        QTRY_VERIFY(!originalMenu || !originalMenu->isVisible());policy.setSuspended(false);
        auto full=fixtureWindow("0xabc","Fullscreen fixture");full["fullscreen"]=true;
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{full}}}));
        QVERIFY(QMetaObject::invokeMethod(delegate,"showContextMenu",Q_ARG(QVariant,QVariantMap{})));
        QPointer<QMenu> reopened;
        QTRY_VERIFY(([&]{for(auto *widget:QApplication::topLevelWidgets())if(auto *m=qobject_cast<QMenu*>(widget);m && m->isVisible() && action(m,"window-close")){reopened=m;return true;}return false;})());
        fullscreen=action(reopened,"view-fullscreen");QVERIFY(fullscreen && fullscreen->isEnabled() && fullscreen->isChecked());
        requests.clear();fullscreen->trigger();QTRY_COMPARE(requests.count(),1);
        QCOMPARE(requests.first().first().toJsonObject().value("state"),QJsonValue(false));
        reopened->close();QTRY_VERIFY(!reopened || !reopened->isVisible());
        // Common manager capabilities: move/resize and hide-from-capture unmasked
        // only when the snapshot grants them; keep above/below stay masked.
        auto capable=fixtureWindow("0xabc","Capable fixture");capable["movable"]=true;capable["windowTagsSettable"]=true;
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{capable}}}));
        QVERIFY(QMetaObject::invokeMethod(delegate,"showContextMenu",Q_ARG(QVariant,QVariantMap{})));
        QPointer<QMenu> capableMenu;
        QTRY_VERIFY(([&]{for(auto *widget:QApplication::topLevelWidgets())if(auto *m=qobject_cast<QMenu*>(widget);m && m->isVisible() && action(m,"window-close")){capableMenu=m;return true;}return false;})());
        // KDE shows "Hide from Screencast" only on the wayland platform (hidden ⇒
        // disabled offscreen): verify our capability mask is lifted instead.
        QVERIFY(!action(capableMenu,"view-private")->actionGroup() && !action(capableMenu,"window-keep-above")->isEnabled());
        QVERIFY(action(capableMenu,"transform-move")->isEnabled() && action(capableMenu,"transform-scale")->isEnabled());
        requests.clear();action(capableMenu,"transform-move")->trigger();action(capableMenu,"transform-scale")->trigger();
        QTRY_COMPARE(requests.count(),2);
        QCOMPARE(requests.at(0).first().toJsonObject().value("action").toString(),"move");
        QCOMPARE(requests.at(1).first().toJsonObject().value("action").toString(),"resize");
        reopened=capableMenu;
        source.clear();QTRY_VERIFY(!reopened || !reopened->isVisible()); // Never keep a stale task index actionable.
        // Native grouped menu must apply the same restrictions to all members.
        config.writeEntry("groupingStrategy",1);model->setGroupMode(TaskManager::TasksModel::GroupApplications);
        model->setGroupInline(false);model->setGroupingWindowTasksThreshold(-1);
        QVERIFY(source.apply({{"version",1},{"windows",QJsonArray{fixtureWindow("0xabc","First"),fixtureWindow("0xdef","Second")}}}));
        QTRY_COMPARE(model->rowCount(),1);
        QTRY_VERIFY(model->index(0,0).data(TaskManager::AbstractTasksModel::IsGroupParent).toBool());
        QCOMPARE(model->rowCount(model->index(0,0)),2);
        QTRY_VERIFY(delegate=task(item));
        QVERIFY(QMetaObject::invokeMethod(delegate,"showContextMenu",Q_ARG(QVariant,QVariantMap{})));
        QPointer<QMenu> grouped;
        QTRY_VERIFY(([&]{for(auto *widget:QApplication::topLevelWidgets())if(auto *m=qobject_cast<QMenu*>(widget);m && m->isVisible() && action(m,"window-close")){grouped=m;return true;}return false;})());
        QVERIFY(!action(grouped,"window-keep-above")->isEnabled());QVERIFY(!action(grouped,"window-keep-below")->isEnabled());
        QVERIFY(!action(grouped,"view-private")->isEnabled());QVERIFY(action(grouped,"window-minimize")->isEnabled());
        requests.clear();action(grouped,"window-minimize")->trigger();QTRY_COMPARE(requests.count(),2);
        QSet<QString> addresses;
        for(const auto &request:requests){const auto data=request.first().toJsonObject();QCOMPARE(data.value("action").toString(),"toggle-minimize");addresses.insert(data.value("address").toString());}
        QCOMPARE(addresses,(QSet<QString>{"0xabc","0xdef"}));
        requests.clear();fullscreen=action(grouped,"view-fullscreen");QVERIFY(fullscreen && fullscreen->isEnabled());
        fullscreen->trigger();QTRY_COMPARE(requests.count(),2);
        for(const auto &request:requests){const auto data=request.first().toJsonObject();QCOMPARE(data.value("action").toString(),"fullscreen");QCOMPARE(data.value("state"),QJsonValue(true));}
        source.clear();QTRY_VERIFY(!grouped || !grouped->isVisible());
        QMenu foreign;foreign.addAction(QIcon::fromTheme("window-keep-above"),"Foreign action");foreign.show();QVERIFY(foreign.actions().first()->isEnabled());QVERIFY(!policy.apply(&foreign));foreign.close();
    }
};
QTEST_MAIN(MenuTest)
#include "test-taskmenu.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY: native Wayland models, original KDE QML, software rendering to memory.
// The data-only fixture rejects surfaces; this window is never shown or created.
#include "taskbridge.h"
#include "tests/task-qml-source.h"
#include "tests/task-app-fixture.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <KConfigGroup>
#include <tasksmodel.h>
#include <QApplication>
#include <QtGui/qguiapplication_platform.h>
#include <wayland-client.h>
#include <sys/stat.h>
#include <QQuickRenderControl>
#include <QQuickRenderTarget>
#include <QQuickWindow>
#include <QQuickItem>
#include <QQmlContext>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QStandardPaths>
#include <QtTest>

namespace {
struct stat inheritedSocket{};
bool inheritedSocketValid=false;
}
class DelegateCorona:public Plasma::Corona {
public: QRect screenGeometry(int)const override{return {0,0,1920,1080};}
};
QQuickItem *nativeTask(QQuickItem *root){
    if(root->metaObject()->indexOfMethod("showContextMenu(QVariant)")>=0)return root;
    for(auto *child:root->childItems())if(auto *found=nativeTask(child))return found;
    return nullptr;
}
class TaskDelegateTest:public QObject {
    Q_OBJECT
    TaskApplicationFixture m_application;
public:
    static void initMain(){
        // QTest calls this before constructing QApplication. libwayland's
        // wl_display_connect consumes/unsets WAYLAND_SOCKET during Qt startup.
        bool ok=false;
        const int fd=qEnvironmentVariableIntValue("WAYLAND_SOCKET",&ok);
        inheritedSocketValid=ok && fd>=0 && ::fstat(fd,&inheritedSocket)==0 && S_ISSOCK(inheritedSocket.st_mode);
    }
private Q_SLOTS:
    void initTestCase(){
        QCOMPARE(QGuiApplication::platformName(),"wayland");
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        QVERIFY(qEnvironmentVariableIsEmpty("WAYLAND_DISPLAY"));
        QVERIFY2(inheritedSocketValid,"Runner must supply a valid private socket before QApplication starts");
        auto *native=qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>();
        QVERIFY(native && native->display());
        struct stat activeSocket{};
        QCOMPARE(::fstat(wl_display_get_fd(native->display()),&activeSocket),0);
        QVERIFY(S_ISSOCK(activeSocket.st_mode));
        // Check the live connection, including a dup of the inherited fd,
        // without retaining/resetting the consumed environment variable.
        QCOMPARE(activeSocket.st_dev,inheritedSocket.st_dev);
        QCOMPARE(activeSocket.st_ino,inheritedSocket.st_ino);
        QVERIFY2(m_application.prepare(qEnvironmentVariable("BWM_R4_DESKTOP_TEST_ROOT"),QStringLiteral(BWM_TEST_SYCOCA_PROGRAM)),
            qPrintable(m_application.error));
    }
    void originalDelegateRendersWithNativeWaylandRoles_data(){
        QTest::addColumn<QString>("plugin");
        QTest::newRow("icons-only")<<QString("org.kde.plasma.icontasks");
        QTest::newRow("text-and-icons")<<QString("org.kde.plasma.taskmanager");
    }
    void originalDelegateRendersWithNativeWaylandRoles(){
        QFETCH(QString,plugin);
        const QRegularExpression bindingError(".*(Task.qml|main.qml).*(undefined|TypeError|ReferenceError|Unable to assign).*");
        QTest::failOnWarning(bindingError);
        QTemporaryDir fixtures(QStandardPaths::writableLocation(QStandardPaths::CacheLocation)+"-delegate-XXXXXX");
        QVERIFY(fixtures.isValid());
        const auto write=[&](const QString &name,const QByteArray &bytes){
            QSaveFile file(fixtures.filePath(name));
            return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size() && file.commit();
        };
        const auto snapshot=[&](const QJsonArray &rows){
            return write("snapshot.json",QJsonDocument(QJsonObject{{"version",1},{"windows",rows}}).toJson());
        };
        QVERIFY(snapshot({}));
        QVERIFY(write("helper.py","import pathlib,sys\nprint((pathlib.Path(__file__).parent/'snapshot.json').read_text())\n"));
        QQuickRenderControl render;
        QQuickWindow window(&render);window.resize(640,48);window.setColor(Qt::transparent);
        QImage image(window.size(),QImage::Format_ARGB32_Premultiplied);image.fill(Qt::transparent);
        window.setRenderTarget(QQuickRenderTarget::fromPaintDevice(&image));
        // Software render control has no QRhi to initialize. It creates its
        // scene graph during sync and never asks the fixture for a wl_surface.
        const auto paint=[&]{render.polishItems();render.sync();render.render();};
        DelegateCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *containment=corona.createContainment("org.kde.panel");QVERIFY(containment && !containment->failedToLaunch());
        containment->setFormFactor(Plasma::Types::Horizontal);containment->setLocation(Plasma::Types::BottomEdge);
        auto *applet=containment->createApplet(plugin);QVERIFY(applet && !applet->failedToLaunch());
        auto config=applet->config();
        config.writeEntry("launchers",QStringList{});config.writeEntry("showOnlyCurrentDesktop",false);
        config.writeEntry("showOnlyCurrentActivity",false);config.writeEntry("groupingStrategy",0);
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(containment);QVERIFY(root);
        root->setParentItem(window.contentItem());root->setSize({640,48});
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);QVERIFY(item);
        QTRY_VERIFY(!item->findChildren<TaskManager::TasksModel*>().isEmpty());
        BwmTaskBridge bridge(qEnvironmentVariable("XDG_RUNTIME_DIR"),qEnvironmentVariable("XDG_CONFIG_HOME"),
            QStandardPaths::findExecutable("python3"),fixtures.filePath("helper.py"));
        bridge.attach(item);bridge.tick();
        QTRY_COMPARE(bridge.boundCount(),1);
        TaskManager::TasksModel *model=nullptr;
        QTRY_VERIFY(!item->findChildren<TaskManager::TasksModel*>().isEmpty());
        model=item->findChildren<TaskManager::TasksModel*>().first();
        model->setFilterByCurrentVirtualDesktop(false);model->setFilterByActivity(false);model->setFilterByScreen(false);
        model->setGroupMode(TaskManager::TasksModel::GroupDisabled);model->setLauncherList({});
        // No role-name or StartupTasksModel substitutes: native Wayland only.
        QTRY_VERIFY(bridge.state().value("snapshotAvailable").toBool());
        QTRY_COMPARE(model->rowCount(),0);
        const auto roles=model->roleNames();
        QCOMPARE(roles.value(TaskManager::AbstractTasksModel::AppName),QByteArray("AppName"));
        QCOMPARE(roles.value(TaskManager::AbstractTasksModel::IsActive),QByteArray("IsActive"));
        QJsonObject row{{"address","0xabc"},{"pid",int(QCoreApplication::applicationPid())},{"generation","1"},
            {"title","BWM native delegate"},{"appId",m_application.id},{"workspace","1"},
            {"geometry",QJsonArray{10,20,800,600}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",true},{"minimized",false},{"maximized",false},{"fullscreen",false},
            {"fullscreenable",true},{"urgent",false},{"onAllDesktops",false}};
        QVERIFY(snapshot({row}));bridge.tick();QTRY_COMPARE(model->rowCount(),1);
        // Prove deterministic service resolution before checking the QML view.
        QCOMPARE(model->index(0,0).data(TaskManager::AbstractTasksModel::AppId).toString(),m_application.id+".desktop");
        QCOMPARE(model->index(0,0).data(TaskManager::AbstractTasksModel::AppName).toString(),m_application.name);
        QQuickItem *delegate=nullptr;QTRY_VERIFY(delegate=nativeTask(item));
        const auto provenance=taskQmlSource(delegate);
        QVERIFY2(provenance.value("reviewed").toBool(),qPrintable(QJsonDocument::fromVariant(provenance).toJson()));
        QTRY_COMPARE(delegate->property("pid").toInt(),int(QCoreApplication::applicationPid()));
        QCOMPARE(delegate->property("appId").toString(),m_application.id);
        QCOMPARE(delegate->property("appName").toString(),m_application.name);
        QVERIFY(delegate->property("isWindow").toBool());
        QTRY_COMPARE(delegate->property("state").toString(),"active");
        QTRY_VERIFY((paint(),delegate->width()>0 && delegate->height()>0));
        const QRect box=delegate->mapRectToScene(delegate->boundingRect()).toAlignedRect().intersected(image.rect());
        QVERIFY(!box.isEmpty());
        paint();const auto active=image.copy(box);
        bool opaque=false;for(int y=0;y<active.height();++y)for(int x=0;x<active.width();++x)opaque|=qAlpha(active.pixel(x,y))>0;
        QVERIFY2(opaque,"Original task delegate painted no pixels");
        const auto held=QPersistentModelIndex(model->index(0,0));
        row["active"]=false;row["minimized"]=true;
        QVERIFY(snapshot({row}));bridge.tick();QTRY_COMPARE(delegate->property("state").toString(),"minimized");
        QVERIFY(held.isValid());QCOMPARE(nativeTask(item),delegate);
        QTRY_VERIFY((paint(),image.copy(box)!=active));
        row["minimized"]=false;row["title"]="Updated native title";
        QVERIFY(snapshot({row}));bridge.tick();
        QTRY_COMPARE(model->index(0,0).data().toString(),"Updated native title");
        QTRY_COMPARE(delegate->property("state").toString(),"");
        if(plugin=="org.kde.plasma.taskmanager")QTRY_COMPARE(delegate->property("labelText").toString(),"Updated native title");
        QPointer<QQuickItem> old=delegate;
        QVERIFY(snapshot({}));bridge.tick();QTRY_COMPARE(model->rowCount(),0);QVERIFY(!held.isValid());
        QTRY_VERIFY(!old);paint();
        QVERIFY2(bridge.error().isEmpty(),qPrintable(bridge.error()));
        QVERIFY(!window.isVisible());QVERIFY(!window.handle());
        render.invalidate();
    }
};
QTEST_MAIN(TaskDelegateTest)
#include "test-taskdelegate.moc"

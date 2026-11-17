// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskthumbnail.h"
#include "tasksource.h"
#include "packagewindows.h"
#include "surfaces.h"
#include <LayerShellQt/Window>
#include <PlasmaQuick/PopupPlasmaWindow>
#include <PlasmaQuick/Dialog>
#include <QPlatformSurfaceEvent>
#include <QJsonArray>
#include <QTemporaryDir>
#include <QFile>
#include <QScopeGuard>
#include <unistd.h>
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/SharedQmlEngine>
#include <PlasmaQuick/AppletQuickItem>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickWindow>
#include <QtTest>
#include <wayland-client-protocol.h>
class ThumbnailCorona:public Plasma::Corona {public:QRect screenGeometry(int)const override{return {0,0,1920,1080};}};
class ThumbnailTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void initTestCase(){QVERIFY(!qEnvironmentVariableIsEmpty("BWM_R4_THUMBNAIL_LOCAL_ROOT"));}
    void missingNativeDisplayIsNotReportedAsMissingMarker(){
        const auto result=thumbnailCompositorGuardStatus();
        QVERIFY(!result.value("verified").toBool());
        QCOMPARE(result.value("reason").toString(),QString("no-native-wayland-display"));
        QVERIFY(!result.value("capturesStarted").toBool());
    }
    void guardReportMustMatchKernelPeer(){
        const QJsonObject valid{{"version",1},{"pid",5178}};
        QVERIFY(thumbnailGuardReportMatches(valid,5178));
        QVERIFY(!thumbnailGuardReportMatches(valid,5179));
        QVERIFY(!thumbnailGuardReportMatches(valid,0));
        for(const auto &bad:QList<QJsonObject>{ {},{{"version",true},{"pid",5178}},{{"version","1"},{"pid",5178}},
            {{"version",2},{"pid",5178}},{{"version",1},{"pid","5178"}},{{"version",1},{"pid",true}},
            {{"version",1},{"pid",5178.5}},{{"version",1}} })QVERIFY(!thumbnailGuardReportMatches(bad,5178));
    }
    void ipcGuardUsesFreshBoundedReplyAndActualRuntime(){
        QTemporaryDir root;QVERIFY(root.isValid());
        const auto previous=qgetenv("PATH");const bool hadPath=qEnvironmentVariableIsSet("PATH");
        const auto restore=qScopeGuard([&]{if(hadPath)qputenv("PATH",previous);else qunsetenv("PATH");});
        qputenv("PATH",root.path().toUtf8());
        const auto script=[&](const QByteArray &body){
            QFile file(root.filePath("hyprctl"));if(!file.open(QIODevice::WriteOnly|QIODevice::Truncate))return false;
            file.write("#!/bin/sh\n[ \"$1\" = -j ] && [ \"$2\" = version ] || exit 7\n[ \"$XDG_RUNTIME_DIR\" = '"+root.path().toUtf8()+"' ] || exit 8\n"+body+"\n");
            file.close();return file.setPermissions(QFile::ReadOwner|QFile::WriteOwner|QFile::ExeOwner);
        };
        const int peer=getpid();
        const auto packet=[&](int pid){return QByteArray("printf '%s' '{\"bwmScreenshareMonitorGuard\":{\"version\":1,\"pid\":")+QByteArray::number(pid)+"}}'";};
        QVERIFY(script(packet(peer)));
        auto result=thumbnailGuardIpcStatus(peer,root.path());QVERIFY(result.value("verified").toBool());
        QCOMPARE(result.value("verificationMethod").toString(),QString("compositor-ipc"));
        QVERIFY(script(packet(peer+1)));result=thumbnailGuardIpcStatus(peer,root.path());
        QVERIFY(!result.value("verified").toBool());QCOMPARE(result.value("reason").toString(),QString("ipc-report-does-not-match-wayland-peer"));
        QVERIFY(script("printf '{}'") );result=thumbnailGuardIpcStatus(peer,root.path());
        QCOMPARE(result.value("reason").toString(),QString("ipc-report-missing-install-reporting-patch"));
        QVERIFY(script("printf 'invalid'") );result=thumbnailGuardIpcStatus(peer,root.path());
        QCOMPARE(result.value("reason").toString(),QString("ipc-invalid-json"));
        QVERIFY(script("exit 3"));result=thumbnailGuardIpcStatus(peer,root.path());
        QCOMPARE(result.value("reason").toString(),QString("ipc-query-failed"));
        QVERIFY(script("exec /usr/bin/head -c 70000 /dev/zero"));result=thumbnailGuardIpcStatus(peer,root.path());
        QCOMPARE(result.value("reason").toString(),QString("ipc-response-exceeds-limit"));
        QVERIFY(script("exec /bin/sleep 5"));result=thumbnailGuardIpcStatus(peer,root.path());
        QCOMPARE(result.value("reason").toString(),QString("ipc-response-timed-out"));
    }
    void windowAssociatedItemCanBeDestroyed(){
        QQuickWindow window,other;
        auto item=std::make_unique<TaskThumbnail>(window.contentItem());
        QCOMPARE(item->window(),&window);
        item->setParentItem(other.contentItem());QCOMPARE(item->window(),&other);
        item->setParentItem(nullptr);QVERIFY(!item->window());
        item->setParentItem(window.contentItem());
        QSignalSpy destroyed(item.get(),&QObject::destroyed);
        QPointer<TaskThumbnail> held=item.get();
        item.reset();
        QVERIFY(!held);QCOMPARE(destroyed.count(),1);
    }
    void parentWindowCanDestroyItsThumbnail(){
        auto window=std::make_unique<QQuickWindow>();
        auto *item=new TaskThumbnail(window->contentItem());
        QPointer<TaskThumbnail> held=item;
        QSignalSpy destroyed(item,&QObject::destroyed);
        window.reset();QVERIFY(!held);QCOMPARE(destroyed.count(),1);
    }
    void bufferBounds(){
        QVERIFY(TaskThumbnail::validBufferSize(3840,2160));
        QVERIFY(TaskThumbnail::validBufferSize(8192,2048));
        QVERIFY(!TaskThumbnail::validBufferSize(8192,2049));
        QVERIFY(!TaskThumbnail::validBufferSize(0,50));
        QVERIFY(!TaskThumbnail::validBufferSize(UINT32_MAX,UINT32_MAX));
    }
    void nativePixelFormats(){
        const uint32_t argb=0xff112233,abgr=0xff332211;
        QCOMPARE(QImage(reinterpret_cast<const uchar*>(&argb),1,1,4,TaskThumbnail::pixelFormat(WL_SHM_FORMAT_ARGB8888)).pixelColor(0,0),QColor("#112233"));
        QCOMPARE(QImage(reinterpret_cast<const uchar*>(&abgr),1,1,4,TaskThumbnail::pixelFormat(WL_SHM_FORMAT_ABGR8888)).pixelColor(0,0),QColor("#112233"));
        const uint32_t bgr30=0xc0000000u|(1023u<<10)|1023u;
        QCOMPARE(QImage(reinterpret_cast<const uchar*>(&bgr30),1,1,4,TaskThumbnail::pixelFormat(WL_SHM_FORMAT_XBGR2101010)).pixelColor(0,0).name(),QString("#ffff00"));
        QCOMPARE(TaskThumbnail::pixelFormat(WL_SHM_FORMAT_RGB565),QImage::Format_Invalid);
    }
    void transformsAndDetachedPixels(){
        QImage pixels(2,3,QImage::Format_RGB32);
        for(int y=0;y<3;++y)for(int x=0;x<2;++x)pixels.setPixelColor(x,y,QColor(30+x*50,20+y*70,5));
        const auto normal=TaskThumbnail::transformed(pixels,0).copy();
        for(uint t=0;t<8;++t){
            const auto image=TaskThumbnail::transformed(pixels,t);
            QCOMPARE(image.size(),t%2?QSize(3,2):QSize(2,3));
            QSet<QRgb> colors;
            for(int y=0;y<image.height();++y)for(int x=0;x<image.width();++x)colors.insert(image.pixel(x,y));
            QCOMPARE(colors.size(),6);
        }
        QCOMPARE(TaskThumbnail::transformed(pixels,1).pixelColor(2,0),pixels.pixelColor(0,0));
        QVERIFY(TaskThumbnail::transformed(pixels,8).isNull());
        pixels.fill(Qt::red);QVERIFY(normal.pixelColor(0,0)!=Qt::red);
    }
    void taskUuidRejectsReusedIdentityAndMinimizedWindow(){
        BwmTaskSource source;
        QJsonObject row{{"address","0xabc"},{"pid",123},{"generation","1"},{"title","Own fixture"},{"appId","fixture"},
            {"workspace","1"},{"geometry",QJsonArray{0,0,64,48}},{"screen",QJsonArray{0,0,1920,1080}},
            {"active",false},{"minimized",false},{"maximized",false},{"fullscreen",false},{"urgent",false},{"onAllDesktops",false}};
        const auto apply=[&]{return source.apply({{"version",1},{"windows",QJsonArray{row}}});};
        const auto uuid=[&]{return source.index(0).data(TaskManager::AbstractTasksModel::WinIdList).toList().first().toUuid();};
        QVERIFY(apply());const auto original=uuid();QVERIFY(!source.thumbnailTarget(original).isEmpty());
        row["pid"]=124;row["generation"]="2";QVERIFY(apply());QVERIFY(source.thumbnailTarget(original).isEmpty());
        const auto current=uuid();QVERIFY(current!=original);QVERIFY(!source.thumbnailTarget(current).isEmpty());
        row["minimized"]=true;QVERIFY(apply());QVERIFY(source.thumbnailTarget(current).isEmpty());
        row["minimized"]=false;row["workspace"]="special:magic";QVERIFY(apply());QVERIFY(source.thumbnailTarget(current).isEmpty());
        row["workspace"]="1";row["screen"]=QJsonArray{};QVERIFY(apply());QVERIFY(source.thumbnailTarget(current).isEmpty());
        source.clear();QVERIFY(source.thumbnailTarget(current).isEmpty());
    }
    void originalCppTooltipGetsLayerRoleBeforeShowAndFollowsCurrentOwner(){
        ThumbnailCorona corona;
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        auto *other=corona.createContainment("org.kde.panel");QVERIFY(other);
        auto *a=c->createApplet("org.kde.plasma.taskmanager");QVERIFY(a);
        auto *b=other->createApplet("org.kde.plasma.taskmanager");QVERIFY(b);
        QQuickWindow panel,second;panel.resize(500,48);second.resize(500,48);
        BwmSurface::configurePanel(&panel,Qt::BottomEdge);
        BwmSurface::configurePanel(&second,Qt::TopEdge);
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);
        auto *otherItem=PlasmaQuick::AppletQuickItem::itemForApplet(b);QVERIFY(item && otherItem);
        item->setParentItem(panel.contentItem());item->setSize({500,48});
        otherItem->setParentItem(second.contentItem());otherItem->setSize({500,48});
        PackageWindows windows(c),otherWindows(other);
        QQmlComponent component(qmlEngine(item));
        component.setData(R"(import QtQuick
            import org.kde.plasma.core as Core
            Core.ToolTipArea {
                width: 40; height: 32; interactive: true
                mainText: "Own tooltip fixture"
                mainItem: Rectangle { implicitWidth: 120; implicitHeight: 80; color: "blue" }
            })",QUrl("qrc:/bwm-original-tooltip-test.qml"));
        std::unique_ptr<QObject> first(component.create(qmlContext(item))),last(component.create(qmlContext(otherItem)));
        auto *area=qobject_cast<QQuickItem*>(first.get()),*next=qobject_cast<QQuickItem*>(last.get());
        QVERIFY2(area && next,qPrintable(component.errorString()));
        area->setParentItem(item);area->setPosition({120,0});next->setParentItem(otherItem);next->setPosition({280,0});
        QVERIFY(QMetaObject::invokeMethod(area,"showToolTip",Qt::DirectConnection));
        PlasmaQuick::PopupPlasmaWindow *popup=nullptr;
        for(auto *w:qGuiApp->allWindows())if(auto *candidate=qobject_cast<PlasmaQuick::PopupPlasmaWindow*>(w);candidate && candidate->visualParent()==area)popup=candidate;
        QVERIFY(popup);QVERIFY(popup->isVisible());
        QVERIFY(!qobject_cast<PlasmaQuick::Dialog*>(popup));QVERIFY(!qmlContext(popup));
        QVERIFY(popup->property("bwmPackageWindowAdapted").toBool());
        QVERIFY(popup->property("bwmPackageRoleAtSurfaceCreation").toBool());
        auto *role=LayerShellQt::Window::get(popup);
        QCOMPARE(role->layer(),LayerShellQt::Window::LayerOverlay);
        QCOMPARE(role->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityNone);
        QVERIFY(!role->activateOnShow());QCOMPARE(role->exclusionZone(),-1);
        QVERIFY(popup->flags().testFlag(Qt::WindowDoesNotAcceptFocus));
        QVERIFY(!popup->flags().testFlag(Qt::WindowTransparentForInput));
        const auto expected=[&](QQuickWindow &view,QQuickItem *anchor,Qt::Edge edge){
            return BwmSurface::placePopup(view.screen()->availableGeometry(),anchor->mapRectToScene(QRectF(0,0,anchor->width(),anchor->height())).toAlignedRect().translated(view.property("bwmPanelRect").toRect().topLeft()),popup->size(),edge);
        };
        QCOMPARE(popup->property("bwmPopupRect").toRect(),expected(panel,area,Qt::BottomEdge));
        area->setX(220);QCOMPARE(popup->property("bwmPopupRect").toRect(),expected(panel,area,Qt::BottomEdge));
        QVERIFY(QMetaObject::invokeMethod(next,"showToolTip",Qt::DirectConnection));
        QCOMPARE(popup->visualParent(),next);QVERIFY(popup->isVisible());
        QCOMPARE(popup->property("bwmPopupRect").toRect(),expected(second,next,Qt::TopEdge));
        QCOMPARE(popup->findChildren<PopupAnchor*>("bwmPackagePopupAnchor",Qt::FindDirectChildrenOnly).size(),1);
        windows.suspend();QVERIFY(popup->isVisible()); // Shared tooltip now belongs to the other containment.
        otherWindows.suspend();QVERIFY(!popup->isVisible());
        QVERIFY(QMetaObject::invokeMethod(area,"showToolTip",Qt::DirectConnection));
        QVERIFY(popup->isVisible());QCOMPARE(popup->visualParent(),area);
        QCOMPARE(popup->property("bwmPopupRect").toRect(),expected(panel,area,Qt::BottomEdge));
        windows.suspend();QVERIFY(!popup->isVisible());
        QQuickWindow ordinary;ordinary.resize(400,300);
        std::unique_ptr<QObject> foreign(component.create(qmlContext(item)));
        auto *foreignArea=qobject_cast<QQuickItem*>(foreign.get());QVERIFY(foreignArea);
        foreignArea->setParentItem(ordinary.contentItem());
        QVERIFY(QMetaObject::invokeMethod(foreignArea,"showToolTip",Qt::DirectConnection));
        QCOMPARE(popup->visualParent(),foreignArea);QVERIFY(popup->isVisible());
        QVERIFY(!popup->property("bwmPackageWindowAdapted").toBool());
        QVERIFY(!popup->findChild<PopupAnchor*>("bwmPackagePopupAnchor",Qt::FindDirectChildrenOnly));
        QVERIFY(QMetaObject::invokeMethod(area,"showToolTip",Qt::DirectConnection));
        QVERIFY(popup->property("bwmPackageWindowAdapted").toBool());
        QCOMPARE(popup->property("bwmPopupRect").toRect(),expected(panel,area,Qt::BottomEdge));
        windows.suspend();QVERIFY(!popup->isVisible());
        PlasmaQuick::PopupPlasmaWindow unrelated;unrelated.resize(50,50);unrelated.create();
        QVERIFY(!unrelated.property("bwmPackageWindowAdapted").toBool());
    }
    void originalQmlEndpointLoadsWithoutPipeWire(){
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        ThumbnailCorona corona;
        auto *containment=corona.createContainment("org.kde.panel");QVERIFY(containment);
        auto *applet=containment->createApplet("org.kde.plasma.taskmanager");QVERIFY(applet && !applet->failedToLaunch());
        PlasmaQuick::SharedQmlEngine shared;
        auto *engine=shared.engine().get();QString error;QVERIFY2(installTaskThumbnails(engine,&error),qPrintable(error));
        auto *appletItem=PlasmaQuick::AppletQuickItem::itemForApplet(applet);QVERIFY(appletItem);
        auto *appletContext=QQmlEngine::contextForObject(appletItem);QVERIFY(appletContext);
        QCOMPARE(appletContext->engine(),engine);
        QQmlComponent component(engine);
        component.setData(R"(
            import QtQuick
            import "qrc:/qt/qml/plasma/applet/org/kde/plasma/taskmanager" as Upstream
            Item {
                id: thumbnailSourceItem
                property string winId: "00000000-0000-0000-0000-000000000000"
                property bool castWorks: false
                Upstream.PipeWireThumbnail {
                    Component.onCompleted: parent.castWorks = (this as Upstream.PipeWireThumbnail) !== null
                }
            }
        )",QUrl("qrc:/bwm-thumbnail-test.qml"));
        QTRY_VERIFY_WITH_TIMEOUT(component.status()!=QQmlComponent::Loading,2000);
        std::unique_ptr<QObject> object(component.create());
        QVERIFY2(object,qPrintable(component.errorString()));
        QVERIFY(object->property("castWorks").toBool());
        auto *thumbnail=object->findChild<TaskThumbnail*>();QVERIFY(thumbnail);
        QVERIFY(!thumbnail->property("hasThumbnail").toBool());
        QVERIFY(!thumbnail->ready());
        thumbnail->acceptFrame(QImage(16,16,QImage::Format_RGB32));QVERIFY(thumbnail->ready());
        thumbnail->setUuid("different");QVERIFY(!thumbnail->ready());
    }
};
QTEST_MAIN(ThumbnailTest)
#include "test-taskthumbnail.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
#include "wallpaperbridge.h"
#include "containmentconfigview.h"
#include "desktopviewhost.h"
#include "viewcorona.h"
#include "surfaces.h"
#include <KPackage/PackageLoader>
#include <Plasma/Containment>
#include <KConfigGroup>
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QQmlPropertyMap>
#include <QQuickItem>
#include <QQuickItemGrabResult>
#include <QProcess>
#include <QScreen>
#include <QTemporaryDir>
#include <QtTest>

class WallpaperTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void nativeConfigurationAndBwmShareOneAuthority() {
        QVERIFY(qEnvironmentVariable("XDG_CONFIG_HOME").startsWith("/tmp/bwm-wallpaper-"));
        QTemporaryDir files;
        QImage red(128,128,QImage::Format_RGB32); red.fill(Qt::red);
        const QString first=files.filePath("fondo con ñ y espacio.png"), second=files.filePath("second.png");
        QVERIFY(red.save(first)); red.fill(Qt::blue); QVERIFY(red.save(second));
        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell", BWM_SHELL_SOURCE_DIR));
        BwmSurface::registerTypes();
        auto *desktop=corona.createContainment("org.kde.plasma.folder"); QVERIFY(desktop);
        DesktopViewHost view(&corona, true, QGuiApplication::primaryScreen());
        corona.bind(desktop,&view); QVERIFY2(view.load(desktop),qPrintable(view.error())); view.show();
        WallpaperBridge bridge(&corona); bridge.observe(desktop,"output-a");
        QTRY_VERIFY_WITH_TIMEOUT(desktop->property("wallpaperGraphicsObject").value<QObject*>(),5000);
        QJsonObject req{{"source", first}, {"still", first}};
        QTRY_VERIFY_WITH_TIMEOUT(bridge.setWallpaper(req),5000);
        auto selected=[&] { const auto rows=bridge.status().value("screens").toArray(); return rows.isEmpty()?QJsonObject():rows.first().toObject(); };
        QTRY_COMPARE_WITH_TIMEOUT(selected().value("source").toString(),first,8000);
        QCOMPARE(desktop->wallpaperPlugin(),"org.kde.image");
        QCOMPARE(desktop->config().group("Wallpaper").group("org.kde.image").group("General").readEntry("Image",QString()),QUrl::fromLocalFile(first).toString());

        // Exercise the actual ContainmentConfigView Apply path, including plugin
        // changes, not an equivalent writer in a test-only implementation.
        ContainmentConfigView config(desktop,&view);
        config.setCurrentWallpaper("org.kde.image");
        QVERIFY(config.wallpaperConfiguration());
        config.wallpaperConfiguration()->insert("Image",QUrl::fromLocalFile(second).toString());
        config.applyWallpaper();
        QTRY_COMPARE_WITH_TIMEOUT(selected().value("source").toString(),second,8000);

        // A per-output edit must not flatten another containment. Both are genuine
        // native views; the isolated compositor runner provides the screen(s).
        auto *other=corona.createContainment("org.kde.plasma.folder"); QVERIFY(other);
        DesktopViewHost otherView(&corona,true,QGuiApplication::screens().last());
        corona.bind(other,&otherView); QVERIFY(otherView.load(other)); otherView.show();
        bridge.observe(other,"output-b");
        req["source"]=first; req["still"]=first; req["screen"]="output-b";
        QTRY_VERIFY(bridge.setWallpaper(req));
        QTRY_COMPARE(bridge.status().value("screens").toArray().size(),2);
        QCOMPARE(QUrl(desktop->config().group("Wallpaper").group("org.kde.image").group("General").readEntry("Image",QString())).toLocalFile(),second);
        req.remove("screen"); QVERIFY(bridge.setWallpaper(req));
        QTRY_COMPARE(selected().value("source").toString(),first);

        // Native color plugin exports only its own background subtree.
        config.setCurrentWallpaper("org.kde.color");
        config.wallpaperConfiguration()->insert("Color",QColor("#25ab71"));
        config.applyWallpaper();
        QTRY_COMPARE(desktop->wallpaperPlugin(),"org.kde.color");
        QTRY_VERIFY_WITH_TIMEOUT(selected().value("plugin").toString()=="org.kde.color" && QFile::exists(selected().value("still").toString()),8000);
        QImage color(selected().value("still").toString()); QVERIFY(!color.isNull());
        QCOMPARE(color.pixelColor(color.width()/2,color.height()/2),QColor("#25ab71"));
        QVERIFY(bridge.setWallpaper(req));
        QTRY_COMPARE(selected().value("plugin").toString(),"org.kde.image");
        // Slideshow advances through the native ImageBackend and exports the
        // current slide, rather than a directory or its configuration preview.
        config.setCurrentWallpaper("org.kde.slideshow");
        config.wallpaperConfiguration()->insert("SlidePaths",QStringList{files.path()});
        config.wallpaperConfiguration()->insert("SlideInterval",1);
        config.applyWallpaper();
        QTRY_VERIFY_WITH_TIMEOUT(selected().value("plugin").toString()=="org.kde.slideshow" &&
            (selected().value("source").toString()==first || selected().value("source").toString()==second),10000);
        const QString slide=selected().value("source").toString();
        QTRY_VERIFY_WITH_TIMEOUT(selected().value("source").toString()!=slide,8000);

        const QString video=files.filePath("video.mp4");
        QProcess encode;
        encode.start("ffmpeg", {"-nostdin","-loglevel","error","-y","-f","lavfi","-i",
            "testsrc=size=128x128:rate=10:duration=2","-c:v","libx264","-pix_fmt","yuv420p",video});
        QVERIFY(encode.waitForFinished(10000)); QCOMPARE(encode.exitCode(),0);
        req["source"]=video;req["still"]=first;req["video"]=true;
        QVERIFY(bridge.setWallpaper(req));
        QTRY_COMPARE_WITH_TIMEOUT(selected().value("source").toString(),video,8000);
        QCOMPARE(selected().value("still").toString(),first);
        auto *videoItem=qobject_cast<QQuickItem*>(desktop->property("wallpaperGraphicsObject").value<QObject*>());
        QVERIFY(videoItem);
        auto frame=videoItem->grabToImage(); QVERIFY(frame);
        QSignalSpy captured(frame.get(),&QQuickItemGrabResult::ready);
        QTRY_COMPARE(captured.count(),1);
        const QImage image=frame->image();
        QTest::qWait(450);
        auto next=videoItem->grabToImage(); QVERIFY(next);
        QSignalSpy capturedNext(next.get(),&QQuickItemGrabResult::ready);
        QTRY_COMPARE(capturedNext.count(),1);
        QVERIFY2(image!=next->image(),"Native video wallpaper did not produce changing frames");
        req["source"]=first;req["still"]=first;req["video"]=false;
        QVERIFY(bridge.setWallpaper(req));
        QTRY_COMPARE(selected().value("source").toString(),first);
        QVERIFY(!bridge.setWallpaper(QJsonObject{{"source","/does-not-exist"}}));
        corona.saveLayout(files.filePath("appletsrc"));
        QVERIFY(QFileInfo(files.filePath("appletsrc")).size()>0);
        view.hide(); otherView.hide(); corona.unbind(desktop); corona.unbind(other);
    }
};
QTEST_MAIN(WallpaperTest)
#include "test-wallpapers-session.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskthumbnail.h"
#include "taskbridge.h"
#include <windowtasksmodel.h>
#include <QQuickRenderControl>
#include <QQuickRenderTarget>
#include <QQuickWindow>
#include <QSaveFile>
#include <QJsonDocument>
#include <QPainter>
#include <QQmlEngine>
#include <QtTest>
#include <unistd.h>
class NativeThumbnailTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void nativeWindowPixelsAndLifecycle(){
        QCOMPARE(QGuiApplication::platformName(),"wayland");
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        const auto root=qEnvironmentVariable("BWM_R4_DESKTOP_TEST_ROOT");
        const auto clients=qEnvironmentVariable("BWM_R4_FAKE_CLIENTS");QVERIFY(!root.isEmpty() && clients.startsWith(root+'/'));
        QQmlEngine engine;QString error;
        QVERIFY(!installTaskThumbnails(&engine,&error));QVERIFY(error.contains("GUARD_V1"));
        allowSyntheticThumbnailFixtureForTest();
        qputenv("BWM_R4_TASK_ACTIONS","1");qputenv("BWM_R4_TASK_THUMBNAILS","1");
        qputenv("BWM_R4_TASK_RUNTIME",qgetenv("XDG_RUNTIME_DIR"));qputenv("BWM_R4_TASK_CONFIG",qgetenv("XDG_CONFIG_HOME"));
        QObject owner;TaskManager::WindowTasksModel model(&owner);
        BwmTaskBridge::attachEnabled(&owner);
        BwmTaskBridge *bridge=nullptr;QTRY_VERIFY(bridge=BwmTaskBridge::thumbnailBridge());
        QTRY_COMPARE(bridge->source()->rowCount(),1);
        const auto uuid=[&]{return bridge->source()->index(0).data(TaskManager::AbstractTasksModel::WinIdList).toList().first().toUuid().toString();};
        const auto oldUuid=uuid();QVERIFY(!QUuid(oldUuid).isNull());
        QQuickRenderControl render;QQuickWindow window(&render);window.resize(64,48);
        QImage image(64,48,QImage::Format_ARGB32_Premultiplied);image.fill(Qt::transparent);
        window.setRenderTarget(QQuickRenderTarget::fromPaintDevice(&image));
        auto item=std::make_unique<TaskThumbnail>(window.contentItem());item->setSize({64,48});item->setUuid(oldUuid);
        QTRY_VERIFY_WITH_TIMEOUT(taskThumbnailDiagnostics().value("protocolsReady").toBool(),3000);
        QTRY_VERIFY_WITH_TIMEOUT(item->ready(),5000);
        render.polishItems();render.sync();render.render();
        QCOMPARE(image.pixelColor(32,24),QColor("#3684c9"));
        qInfo("thumbnail-check: synthetic pixels verified");
        QVERIFY(!window.isVisible());QVERIFY(!window.handle());
        QTRY_VERIFY(taskThumbnailDiagnostics().value("frames").toULongLong()>=2);
        const auto command=[](const char *text){const auto bytes=QByteArray(text)+'\n';return write(qEnvironmentVariableIntValue("BWM_R4_DESKTOP_TEST_FD"),bytes.constData(),bytes.size())==bytes.size();};
        QVERIFY(command("thumbnail-static"));QTest::qWait(2300);QVERIFY(item->ready());
        item->setVisible(false);QTRY_COMPARE(taskThumbnailDiagnostics().value("bufferBytes").toLongLong(),0);
        const auto paused=taskThumbnailDiagnostics().value("frames").toULongLong();QTest::qWait(350);
        QCOMPARE(taskThumbnailDiagnostics().value("frames").toULongLong(),paused);QVERIFY(!item->ready());
        QVERIFY(command("thumbnail-live"));item->setVisible(true);QTRY_VERIFY_WITH_TIMEOUT(item->ready(),3000);
        QVERIFY(command("thumbnail-resize"));QTRY_COMPARE(taskThumbnailDiagnostics().value("bufferBytes").toLongLong(),96*64*4);
        qInfo("thumbnail-check: static image, visibility and resize verified");
        item.reset();
        QTRY_COMPARE(taskThumbnailDiagnostics().value("activeCaptures").toInt(),0);
        QCOMPARE(taskThumbnailDiagnostics().value("bufferBytes").toLongLong(),0);
        item=std::make_unique<TaskThumbnail>(window.contentItem());item->setSize({64,48});item->setUuid(oldUuid);
        QTRY_VERIFY_WITH_TIMEOUT(item->ready(),3000);
        qInfo("thumbnail-check: active-capture destruction and recreation verified");
        // Same address, different process generation: the old task UUID must lose
        // capture authority before the row belonging to the new task can be used.
        QFile file(clients);QVERIFY(file.open(QIODevice::ReadOnly));auto client=QJsonDocument::fromJson(file.readAll()).object();file.close();
        client["pid"]=int(QCoreApplication::applicationPid());
        QSaveFile replacement(clients);QVERIFY(replacement.open(QIODevice::WriteOnly));replacement.write(QJsonDocument(client).toJson());QVERIFY(replacement.commit());
        QTRY_VERIFY(uuid()!=oldUuid);QTRY_VERIFY(!item->ready());
        QVERIFY(bridge->source()->thumbnailTarget(QUuid(oldUuid)).isEmpty());
        item->setUuid(uuid());QTRY_VERIFY_WITH_TIMEOUT(item->ready(),3000);
        QVERIFY(command("thumbnail-close"));QTRY_VERIFY(!item->ready());
        QTRY_COMPARE(taskThumbnailDiagnostics().value("activeCaptures").toInt(),0);
        QVERIFY(command("thumbnail-withdraw"));QTRY_VERIFY(!taskThumbnailDiagnostics().value("protocolsReady").toBool());
        qInfo("thumbnail-check: identity, close and withdrawal verified");
        QTRY_VERIFY(BwmTaskBridge::suspendAll(true));item.reset();render.invalidate();
        QCOMPARE(taskThumbnailDiagnostics().value("bufferBytes").toLongLong(),0);
        qInfo("thumbnail-check: teardown complete");
    }
};
QTEST_MAIN(NativeThumbnailTest)
#include "test-taskthumbnail-native.moc"

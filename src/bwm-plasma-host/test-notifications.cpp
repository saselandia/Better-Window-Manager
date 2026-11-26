// SPDX-License-Identifier: GPL-2.0-or-later
#include "notificationhost.h"

#include <notificationmanager/notification.h>
#include <notificationmanager/server.h>
#include <notificationmanager/settings.h>

#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusInterface>
#include <QDBusReply>
#include <QFile>
#include <QProcess>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTest>

class TestNotifications final : public QObject
{
    Q_OBJECT

private Q_SLOTS:
    void popupMarginsClampAcrossOutputs()
    {
        // Primary 1440p monitor at (0, 720)
        const QRect msi(0, 720, 2560, 1440);
        const QSize popup(360, 110);
        QCOMPARE(NotificationHost::popupMarginsForScreen(msi, QPoint(2160, 1980), popup),
                 QMargins(2160, 1260, 0, 0));
        // Out of bounds clamps safely inside the monitor
        QCOMPARE(NotificationHost::popupMarginsForScreen(msi, QPoint(-20, 700), popup),
                 QMargins(0, 0, 0, 0));
        QCOMPARE(NotificationHost::popupMarginsForScreen(msi, QPoint(2500, 2150), popup),
                 QMargins(2560 - 360, 1440 - 110, 0, 0));
        // Secondary 4K monitor at (2560, 0)
        const QRect lg(2560, 0, 3840, 2160);
        QCOMPARE(NotificationHost::popupMarginsForScreen(lg, QPoint(2600, 40), popup),
                 QMargins(40, 40, 0, 0));
    }

    void handoffReceiveAndDndOnPrivateBus()
    {
        // Must run on a private D-Bus session (never the user's daily bus).
        QVERIFY2(QDBusConnection::sessionBus().isConnected(), "Private D-Bus session is required");

        QTemporaryDir tmp;
        QVERIFY(tmp.isValid());
        qputenv("XDG_CONFIG_HOME", tmp.path().toUtf8());
        const QString dndFile = tmp.filePath(QStringLiteral("bwm-plasma-dnd"));

        // 1. Simulate a competing owner (e.g. Quickshell or swaync) holding org.freedesktop.Notifications
        //    on a separate D-Bus connection.
        auto foreignBus = QDBusConnection::connectToBus(QDBusConnection::SessionBus, QStringLiteral("foreign-owner"));
        QVERIFY(foreignBus.isConnected());
        auto foreignReg = foreignBus.interface()->registerService(
            QStringLiteral("org.freedesktop.Notifications"),
            QDBusConnectionInterface::DontQueueService,
            QDBusConnectionInterface::AllowReplacement);
        QCOMPARE(foreignReg.value(), QDBusConnectionInterface::ServiceRegistered);

        NotificationHost host(dndFile);
        // Must NOT queue or steal when another owner holds it; must return false cleanly.
        QVERIFY(!host.start());
        QVERIFY(!host.isValid());

        // 2. Foreign owner releases the name: NotificationHost's QDBusServiceWatcher claims it automatically.
        QSignalSpy validSpy(&NotificationManager::Server::self(), &NotificationManager::Server::validChanged);
        QVERIFY(foreignBus.interface()->unregisterService(QStringLiteral("org.freedesktop.Notifications")).value());
        QTRY_VERIFY_WITH_TIMEOUT(host.isValid(), 3000);
        QVERIFY(validSpy.count() >= 1);
        QDBusConnection::disconnectFromBus(QStringLiteral("foreign-owner"));

        // 3. Real client call via D-Bus (and notify-send if installed) reaches NotificationManager::Server.
        QSignalSpy addedSpy(&NotificationManager::Server::self(), &NotificationManager::Server::notificationAdded);
        QDBusInterface client(QStringLiteral("org.freedesktop.Notifications"),
                              QStringLiteral("/org/freedesktop/Notifications"),
                              QStringLiteral("org.freedesktop.Notifications"),
                              QDBusConnection::sessionBus());
        QVERIFY(client.isValid());
        QDBusReply<uint> reply = client.call(
            QStringLiteral("Notify"),
            QStringLiteral("BWM Test App"),
            uint(0),
            QStringLiteral("dialog-information"),
            QStringLiteral("Hello Plasma"),
            QStringLiteral("Body from private D-Bus"),
            QStringList{QStringLiteral("default"), QStringLiteral("Open")},
            QVariantMap{{QStringLiteral("urgency"), uchar(1)}},
            int(5000));
        QVERIFY2(reply.isValid(), qPrintable(reply.error().message()));
        QVERIFY(reply.value() > 0);
        QTRY_COMPARE_WITH_TIMEOUT(addedSpy.count(), 1, 2000);

        if (!QStandardPaths::findExecutable(QStringLiteral("notify-send")).isEmpty()) {
            const int before = addedSpy.count();
            QProcess proc;
            proc.start(QStringLiteral("notify-send"),
                       {QStringLiteral("-a"), QStringLiteral("NotifySendTest"),
                        QStringLiteral("CLI Summary"), QStringLiteral("CLI Body")});
            QTRY_COMPARE_WITH_TIMEOUT(proc.state(), QProcess::NotRunning, 3000);
            QCOMPARE(proc.exitCode(), 0);
            QTRY_COMPARE_WITH_TIMEOUT(addedSpy.count(), before + 1, 2000);
        }

        // 4. Do Not Disturb roundtrip: host API -> Server::inhibited + D-Bus property + dnd state file + plasmanotifyrc.
        QVERIFY(!host.isInhibited());
        host.setDoNotDisturb(true);
        QVERIFY(host.isInhibited());
        QVERIFY(NotificationManager::Server::self().inhibited());
        {
            QFile f(dndFile);
            QVERIFY(f.open(QIODevice::ReadOnly));
            QCOMPARE(f.readAll().trimmed(), QByteArrayLiteral("true"));
        }
        QDBusInterface props(QStringLiteral("org.freedesktop.Notifications"),
                             QStringLiteral("/org/freedesktop/Notifications"),
                             QStringLiteral("org.freedesktop.DBus.Properties"),
                             QDBusConnection::sessionBus());
        QDBusReply<QDBusVariant> inhibitedProp = props.call(
            QStringLiteral("Get"), QStringLiteral("org.freedesktop.Notifications"), QStringLiteral("Inhibited"));
        QVERIFY(inhibitedProp.isValid());
        QCOMPARE(inhibitedProp.value().variant().toBool(), true);

        host.toggleDoNotDisturb();
        QVERIFY(!host.isInhibited());
        {
            QFile f(dndFile);
            QVERIFY(f.open(QIODevice::ReadOnly));
            QCOMPARE(f.readAll().trimmed(), QByteArrayLiteral("false"));
        }

        // 5. plasmanotifyrc settings (kcm_notifications contract) read live.
        NotificationManager::Settings settings;
        settings.setPopupPosition(NotificationManager::Settings::TopLeft);
        settings.setPopupTimeout(9000);
        settings.setLowPriorityPopups(false);
        settings.save();

        NotificationManager::Settings reloaded;
        QCOMPARE(reloaded.popupPosition(), NotificationManager::Settings::TopLeft);
        QCOMPARE(reloaded.popupTimeout(), 9000);
        QCOMPARE(reloaded.lowPriorityPopups(), false);

        host.stop();
        QVERIFY(!QFile::exists(dndFile));
    }
};

QTEST_MAIN(TestNotifications)
#include "test-notifications.moc"

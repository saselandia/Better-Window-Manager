// SPDX-License-Identifier: GPL-2.0-or-later
#include "desktopbridge.h"
#include <KWindowSystem>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QFile>
#include <QTemporaryDir>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QStandardPaths>
#include <QtTest>
#include <QtPlugin>
#include <Plasma/PluginLoader>
#include <Plasma/Applet>
Q_IMPORT_PLUGIN(BwmWindowSystemPlugin)
class DesktopTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void originalNativeControllerUsesCommonManager() {
        QVERIFY(qEnvironmentVariable("BWM_R4_DESKTOP_ACTIONS")=="1");
        QVERIFY(qEnvironmentVariable("PATH").startsWith(qEnvironmentVariable("BWM_R4_FAKE_BIN")+':'));
        QVERIFY(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE"));
        // Compiled applet modules register their embedded QML types when the
        // native plugin is loaded, not via a directory in the QML import path.
        QScopedPointer<Plasma::Applet> applet(Plasma::PluginLoader::self()->loadApplet("org.kde.plasma.showdesktop",0));
        QVERIFY(applet);
        QQmlEngine engine;QQmlComponent component(&engine);
        component.setData("import plasma.applet.org.kde.plasma.showdesktop\nShowDesktop {}",QUrl());
        QScopedPointer<QObject> first(component.create()),second(component.create());
        QVERIFY2(first,qPrintable(component.errorString()));QVERIFY(second);
        QVERIFY(!first->property("showingDesktop").toBool());
        QVERIFY(QMetaObject::invokeMethod(first.data(),"toggleDesktop"));
        QTRY_VERIFY(KWindowSystem::showingDesktop());
        QTRY_VERIFY(second->property("showingDesktop").toBool());
        QFile file(qEnvironmentVariable("BWM_R4_DESKTOP_RUNTIME")+"/bwm-show-desktop.json");
        QVERIFY(file.open(QIODevice::ReadOnly));
        QVERIFY(!QJsonDocument::fromJson(file.readAll()).object().value("windows").toArray().isEmpty());file.close();
        // Explicit setter must not toggle a mode already active in another instance.
        KWindowSystem::setShowingDesktop(true);QTest::qWait(350);QVERIFY(KWindowSystem::showingDesktop());
        QVERIFY(QMetaObject::invokeMethod(second.data(),"toggleDesktop"));
        QTRY_VERIFY(!KWindowSystem::showingDesktop());
        QTRY_VERIFY(!first->property("showingDesktop").toBool());
        QVERIFY(file.open(QIODevice::ReadOnly));
        QVERIFY(QJsonDocument::fromJson(file.readAll()).object().value("windows").toArray().isEmpty());
        QFile actions(qEnvironmentVariable("BWM_R4_FAKE_ACTIONS"));QVERIFY(actions.open(QIODevice::ReadOnly));
        const auto log=actions.readAll();QVERIFY(log.contains("special:minimized"));QVERIFY(log.contains("workspace = target"));
    }
    void malformedStateCannotLaunchActions() {
        QTemporaryDir root;QVERIFY(root.isValid());
        QFile state(root.path()+"/bwm-show-desktop.json");QVERIFY(state.open(QIODevice::WriteOnly));state.write("not-json");state.close();
        DesktopBridge bridge(root.path(),"/usr/bin/false",{});QVERIFY(bridge.available());
        bridge.setShowingDesktop(true);QTest::qWait(100);
        QCOMPARE(bridge.error(),"Invalid desktop state");QVERIFY(!bridge.showingDesktop());
        QVERIFY(state.open(QIODevice::WriteOnly));state.write("{\"windows\":[3]}");state.close();
        bridge.setShowingDesktop(true);QTest::qWait(50);QCOMPARE(bridge.error(),"Invalid desktop state");
        QVERIFY(state.remove());QVERIFY(QFile::link(root.path()+"/missing",state.fileName()));
        bridge.setShowingDesktop(true);QTest::qWait(50);QCOMPARE(bridge.error(),"Invalid desktop state");
    }
    void timedOutActionDoesNotLeaveRunningChild() {
        QTemporaryDir root;QVERIFY(root.isValid());
        const auto script=root.path()+"/slow.py",pidFile=root.path()+"/child.pid";
        QFile file(script);QVERIFY(file.open(QIODevice::WriteOnly));
        file.write("import subprocess,sys,time\nfrom pathlib import Path\n"
                   "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])\n"
                   "Path(sys.argv[1]).write_text(str(p.pid))\ntime.sleep(20)\n");file.close();
        DesktopBridge bridge(root.path(),QStandardPaths::findExecutable("python3"),{script,pidFile});
        bridge.setShowingDesktop(true);QTRY_VERIFY(QFile::exists(pidFile));
        QTRY_COMPARE_WITH_TIMEOUT(bridge.error(),"Desktop action timed out",6500);
        QFile pid(pidFile);QVERIFY(pid.open(QIODevice::ReadOnly));const auto child=pid.readAll().trimmed();
        const auto stopped=[&]{QFile state("/proc/"+QString::fromLatin1(child)+"/stat");
            if(!state.open(QIODevice::ReadOnly))return true;
            const auto data=state.readAll();return data.mid(data.lastIndexOf(')')+2,1)=="Z";
        };
        QTRY_VERIFY(stopped());QVERIFY(!bridge.showingDesktop());
    }
};
QTEST_MAIN(DesktopTest)
#include "test-desktop.moc"

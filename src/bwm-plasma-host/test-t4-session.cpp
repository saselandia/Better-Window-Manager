// SPDX-License-Identifier: GPL-2.0-or-later
#include "lookandfeellayout.h"
#include "profilestore.h"
#include "sessionui.h"
#include "viewcorona.h"
#include <Plasma/Containment>
#include <KConfig>
#include <KConfigGroup>
#include <KSharedConfig>
#include <QCryptographicHash>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusPendingCall>
#include <QDBusMessage>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QProcess>
#include <QQuickView>
#include <QQuickItem>
#include <QElapsedTimer>
#include <QTemporaryDir>
#include <QtTest>

class T4Test : public QObject {
    Q_OBJECT
    QString legacy;
    QByteArray read(const QString &path){QFile f(path);if(!f.open(QIODevice::ReadOnly))return {};return f.readAll();}
private Q_SLOTS:
    void initTestCase(){
        QVERIFY(qEnvironmentVariable("XDG_CONFIG_HOME").startsWith("/tmp/bwm-t4-"));
        legacy=qEnvironmentVariable("XDG_CONFIG_HOME")+"/bwm-plasma-host";QDir().mkpath(legacy);
        QFile f(legacy+"/appletsrc");QVERIFY(f.open(QIODevice::WriteOnly));f.write("[General]\nunknown-preserved=yes\n");
    }
    void nativeLayoutsAndRollbackBeforeActivation(){
        const auto original=read(legacy+"/appletsrc");
        for(const QString &theme:{QString("org.kde.breeze.desktop"),QString("Sweet"),QString("com.github.vinceliuice.Layan")}){
            const auto generation=LookAndFeelLayout::prepare(theme,legacy,BWM_SHELL_SOURCE_DIR);
            QVERIFY(QFile::exists(generation+"/session.json"));
            KConfig layout(generation+"/appletsrc",KConfig::SimpleConfig);
            const auto groups=layout.group("Containments").groupList();int panels=0,desktops=0;
            for(const auto &id:groups){auto group=layout.group("Containments").group(id);if(group.readEntry("plugin",QString())=="org.kde.panel")panels++;else desktops++;}
            QVERIFY(panels>=1);QVERIFY(desktops>=1);
            QCOMPARE(read(legacy+"/appletsrc"),original);
            QCOMPARE(ProfileStore::sessionRoot(legacy),legacy);
        }
        bool rejected=false;try{LookAndFeelLayout::prepare("org.bwm.t4.broken",legacy,BWM_SHELL_SOURCE_DIR);}catch(const std::exception&){rejected=true;}
        QVERIFY(rejected);QCOMPARE(read(legacy+"/appletsrc"),original);
        QElapsedTimer deadline;deadline.start();rejected=false;
        try{LookAndFeelLayout::prepare("org.bwm.t4.loop",legacy,BWM_SHELL_SOURCE_DIR);}catch(const std::exception&){rejected=true;}
        QVERIFY(rejected);QVERIFY(deadline.elapsed()<5500);QCOMPARE(read(legacy+"/appletsrc"),original);
    }
    void doesNotReplaceARealPlasmashell(){
        auto foreign=QDBusConnection::connectToBus(QDBusConnection::SessionBus,"t4-existing-plasmashell");
        QVERIFY(foreign.registerService("org.kde.plasmashell"));
        ViewCorona corona;LookAndFeelLayout service(&corona,legacy,legacy,[]{});
        QVERIFY(!service.start());
        foreign.unregisterService("org.kde.plasmashell");
    }
    void originalDbusMethodPreparesAndRequestsRestart(){
        ViewCorona corona;int saves=0,restarts=0;
        LookAndFeelLayout service(&corona,legacy,legacy,[&]{saves++;},nullptr,[&](const QString &next,const QString &previous){
            if(!QFile::exists(next+"/session.json")||!QFile::exists(previous+"/session.json"))return false;
            restarts++;return true;
        });
        QVERIFY(service.start());QSignalSpy restarted(&service,&LookAndFeelLayout::restartRequested);
        auto client=QDBusConnection::connectToBus(QDBusConnection::SessionBus,"t4-kcm-client");
        auto message=QDBusMessage::createMethodCall("org.kde.plasmashell","/PlasmaShell","org.kde.PlasmaShell","loadLookAndFeelDefaultLayout");message<<QString("org.kde.breeze.desktop");
        auto reply=client.asyncCall(message);QTRY_VERIFY_WITH_TIMEOUT(reply.isFinished(),10000);QVERIFY(!reply.isError());
        QTRY_COMPARE(restarted.count(),1);QCOMPARE(saves,1);QCOMPARE(restarts,1);
        QVERIFY(!QFile::exists(legacy+"/active-session.json")); // supervisor selects after old owner exits
    }
    void doesNotCheckpointAnOpenEditSession(){
        ViewCorona corona;corona.setEditMode(true);int saves=0;
        LookAndFeelLayout service(&corona,legacy,legacy,[&]{saves++;});
        service.loadLookAndFeelDefaultLayout("org.kde.breeze.desktop");QCOMPARE(saves,0);
    }
    void originalLogoutThemeCancelAndCountdownUseOnlyFakePower(){
        const QString record=qEnvironmentVariable("XDG_RUNTIME_DIR")+"/power.log";
        const QString fake=qEnvironmentVariable("XDG_RUNTIME_DIR")+"/fake-power";
        QFile script(fake);QVERIFY(script.open(QIODevice::WriteOnly));script.write(("#!/bin/sh\nprintf '%s\\n' \"$*\" >> '"+record+"'\n").toUtf8());script.close();QVERIFY(script.setPermissions(QFile::ReadOwner|QFile::WriteOwner|QFile::ExeOwner));
        SessionUi ui(fake);QVERIFY(ui.start());
        for(const auto &theme:{"org.kde.breeze.desktop","Sweet","com.github.vinceliuice.Layan"}){
            KSharedConfig::openConfig("kdeglobals")->group("KDE").writeEntry("LookAndFeelPackage",theme);
            KSharedConfig::openConfig("kdeglobals")->sync();
            QVERIFY2(ui.prompt("all"),qPrintable(ui.status().value("error").toString()));
            QVERIFY(ui.status().value("windows").toInt()>0);
            auto layerCount=[](){
                QProcess query;auto env=QProcessEnvironment::systemEnvironment();env.insert("XDG_RUNTIME_DIR",qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));query.setProcessEnvironment(env);
                query.start("hyprctl",{"-j","layers"});if(!query.waitForFinished(2000))return -1;
                int count=0;const auto outputs=QJsonDocument::fromJson(query.readAllStandardOutput()).object();
                for(const auto &output:outputs){const auto levels=output.toObject().value("levels").toObject();for(const auto &level:levels)for(const auto &layer:level.toArray())
                    if(layer.toObject().value("namespace").toString()=="bwm-plasma-logout")count++;}
                return count;
            };
            QTRY_COMPARE_WITH_TIMEOUT(layerCount(),QGuiApplication::screens().size(),4000);
            ui.cancel();QCoreApplication::sendPostedEvents(nullptr,QEvent::DeferredDelete);QVERIFY(!QFile::exists(record));
        }
        auto firstRoot=[]()->QQuickItem*{for(auto *w:QGuiApplication::topLevelWindows())if(w->isVisible()){
            auto *theme=qobject_cast<QQuickItem*>(w->property("bwmLogoutTheme").value<QObject*>());
            if(theme&&!theme->childItems().isEmpty())return theme->childItems().first();
        }return nullptr;};
        QVERIFY(ui.prompt("shutdown"));auto *root=firstRoot();QVERIFY(root);
        QVERIFY(QMetaObject::invokeMethod(root,"cancelRequested"));QTRY_COMPARE(ui.status().value("windows").toInt(),0);QVERIFY(!QFile::exists(record));
        for(const auto &action:{"logout","reboot","shutdown"}){
            QVERIFY(ui.prompt(action));root=firstRoot();QVERIFY(root);
            QVERIFY(root->setProperty("remainingTime",0));
            QTRY_VERIFY(read(record).contains((QString(action)+" --confirmed").toUtf8()));
            QCoreApplication::sendPostedEvents(nullptr,QEvent::DeferredDelete);
        }
        QVERIFY(ui.prompt("all"));ui.suspend(1); // legacy StandbyState, original KDE contract
        QTRY_VERIFY(read(record).contains("suspend --confirmed"));
        QCOMPARE(read(record).count("--confirmed"),4); // once across both monitor timers
    }
    void customLogoutReloadsSettingsAndQtQuitClosesOnlyTheTheme(){
        KConfig config(qEnvironmentVariable("XDG_CONFIG_HOME")+"/kdeglobals",KConfig::SimpleConfig);
        config.group("KDE").writeEntry("LookAndFeelPackage","org.bwm.t4.customlogout");config.sync();
        const auto record=qEnvironmentVariable("XDG_RUNTIME_DIR")+"/power.log";
        const auto before=read(record);
        SessionUi ui(qEnvironmentVariable("XDG_RUNTIME_DIR")+"/fake-power");
        QVERIFY(ui.prompt("all"));
        QVERIFY(ui.status().value("source").toString().contains("org.bwm.t4.customlogout/"));
        QQuickItem *root=nullptr;
        for(auto *w:QGuiApplication::topLevelWindows())if(w->isVisible()){
            auto *theme=qobject_cast<QQuickItem*>(w->property("bwmLogoutTheme").value<QObject*>());
            if(theme&&!theme->childItems().isEmpty()){root=theme->childItems().first();break;}
        }
        QVERIFY(root);QVERIFY(QMetaObject::invokeMethod(root,"finish"));
        QTRY_COMPARE(ui.status().value("windows").toInt(),0);
        QCOMPARE(read(record),before);
    }

};
QTEST_MAIN(T4Test)
#include "test-t4-session.moc"

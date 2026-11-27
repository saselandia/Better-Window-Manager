// SPDX-License-Identifier: GPL-2.0-or-later
#include "traydefaults.h"
#include <KConfig>
#include <QFile>
#include <QTemporaryDir>
#include <QtTest>

class TrayDefaultsTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void newTrayPersistsNativeOptOutButAllowsExplicitEnable() {
        QTemporaryDir tmp;const auto path=tmp.filePath("appletsrc");
        {
            KConfig config(path,KConfig::SimpleConfig);auto group=config.group("General");
            QVERIFY(BwmTrayDefaults::apply(group,true));
            QVERIFY(group.readEntry("extraItems",QStringList()).isEmpty());config.sync();
        }
        KConfig config(path,KConfig::SimpleConfig);auto group=config.group("General");
        const auto known=group.readEntry("knownItems",QStringList());
        QVERIFY(known.contains("org.kde.plasma.clipboard"));
        QVERIFY(known.contains("org.kde.plasma.keyboardlayout"));
        group.writeEntry("extraItems",QStringList{"org.kde.plasma.clipboard"});
        QVERIFY(!BwmTrayDefaults::apply(group));
        QCOMPARE(group.readEntry("extraItems",QStringList()),QStringList{"org.kde.plasma.clipboard"});
    }
    void existingChoicesAreNeverRewritten_data() {
        QTest::addColumn<QString>("key");
        for(const auto *key:{"knownItems","extraItems","hiddenItems","shownItems"})QTest::newRow(key)<<QString(key);
    }
    void existingChoicesAreNeverRewritten() {
        QFETCH(QString,key);QTemporaryDir tmp;KConfig config(tmp.filePath("appletsrc"),KConfig::SimpleConfig);
        auto group=config.group("General");group.writeEntry(key,QStringList{"org.kde.plasma.clipboard"});
        config.sync();QFile file(config.name());QVERIFY(file.open(QIODevice::ReadOnly));const auto before=file.readAll();file.close();
        QVERIFY(!BwmTrayDefaults::apply(group));config.sync();QVERIFY(file.open(QIODevice::ReadOnly));QCOMPARE(file.readAll(),before);
    }
    void immutableConfigurationIsRespected() {
        QTemporaryDir tmp;const auto path=tmp.filePath("appletsrc");QFile file(path);QVERIFY(file.open(QIODevice::WriteOnly));
        file.write("[General][$i]\n");file.close();KConfig config(path,KConfig::SimpleConfig);
        QVERIFY(!BwmTrayDefaults::apply(config.group("General"),true));
    }
};
QTEST_GUILESS_MAIN(TrayDefaultsTest)
#include "test-traydefaults.moc"

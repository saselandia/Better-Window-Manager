// SPDX-License-Identifier: GPL-2.0-or-later
#include "managermodule.h"
#include <KPluginFactory>
#include <QFile>
#include <QLabel>
#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QCheckBox>
#include <QTemporaryDir>
#include <QtTest>
class ManagerTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void discoveryAndFactory() {
        QCoreApplication::addLibraryPath(QString::fromLocal8Bit(BWM_TEST_PLUGIN_ROOT));
        for (auto category : {"cursor", "screens", "workspaces", "apps", "startup", "shortcuts", "energy", "windows", "effects"}) {
            const auto metadata = KPluginMetaData::findPluginById("plasma/kcms/systemsettings", QStringLiteral("kcm_bwm_") + category);
            QVERIFY(metadata.isValid());
            const auto result = KPluginFactory::instantiatePlugin<KCModule>(metadata, nullptr);
            QVERIFY2(result.plugin, qPrintable(result.errorString));
            delete result.plugin; // Discovery must never invoke the real controller.
        }
    }
    void effectDefaultsAreStagedAndPrecise() {
        QTemporaryDir tmp;
        QFile f(tmp.filePath("backend.py"));
        QVERIFY(f.open(QIODevice::WriteOnly));
        f.write(R"PY(import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
values = json.loads(p.read_text()) if p.exists() else {'scale':False,'factor':0.0625}
if sys.argv[2] == 'save':
 values.update(json.load(sys.stdin)['changes'])
 p.write_text(json.dumps(values))
print(json.dumps({'revision':'r', 'fields':[
 {'key':'scale','label':'Scale','type':'bool','value':values['scale'],'default':True},
 {'key':'factor','label':'Factor','type':'real','value':values['factor'],'default':1,'min':0,'max':20,'decimals':4,'step':0.25}]}))
)PY");
        f.close();
        const QStringList backend{"python3", f.fileName(), tmp.filePath("state")};
        ManagerModule kcm(nullptr, {}, backend);
        kcm.load();
        QCOMPARE(kcm.widget()->findChild<QDoubleSpinBox *>("factor")->value(), 0.0625);
        QVERIFY(kcm.buttons() & KCModule::Default);
        QVERIFY(!kcm.representsDefaults());
        kcm.defaults();
        QVERIFY(kcm.needsSave());
        QVERIFY(kcm.representsDefaults());
        QVERIFY(!QFile::exists(tmp.filePath("state")));
        kcm.load();
        QVERIFY(!kcm.needsSave());
        QVERIFY(!kcm.widget()->findChild<QCheckBox *>("scale")->isChecked());
        kcm.defaults();
        kcm.save();
        QVERIFY(!kcm.needsSave());
        ManagerModule reopened(nullptr, {}, backend);
        reopened.load();
        QVERIFY(reopened.representsDefaults());
        QVERIFY(reopened.widget()->findChild<QCheckBox *>("scale")->isChecked());
    }
    void transactionAndReopen() {
        QTemporaryDir tmp;
        QFile f(tmp.filePath("backend.py"));
        QVERIFY(f.open(QIODevice::WriteOnly));
        f.write(R"PY(import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
s = int(p.read_text()) if p.exists() else 300
if sys.argv[2] == 'save':
 r = json.load(sys.stdin)
 if r['revision'] != str(s):
  print(json.dumps({'error':'Concurrent edit'})); sys.exit(1)
 s = r['changes'].get('screen', s)
 p.write_text(str(s))
print(json.dumps({'revision':str(s),'fields':[{'key':'screen','label':'Screen','type':'int','min':0,'max':7200,'value':s}]}))
)PY");
        f.close();
        const QStringList backend{"python3", f.fileName(), tmp.filePath("state")};
        ManagerModule kcm(nullptr, {}, backend);
        kcm.load();
        auto *spin = kcm.widget()->findChild<QSpinBox *>("screen");
        QVERIFY(spin);
        spin->setValue(600);
        QVERIFY(kcm.needsSave());
        QVERIFY(!QFile::exists(tmp.filePath("state"))); // Editing never calls save.
        kcm.save();
        QVERIFY(!kcm.needsSave());
        ManagerModule reopened(nullptr, {}, backend);
        reopened.load();
        QCOMPARE(reopened.widget()->findChild<QSpinBox *>("screen")->value(), 600);
        QFile state(tmp.filePath("state")); QVERIFY(state.open(QIODevice::WriteOnly)); state.write("900"); state.close();
        spin = kcm.widget()->findChild<QSpinBox *>("screen"); spin->setValue(700);
        kcm.save();
        QVERIFY(kcm.needsSave());
        QVERIFY(!kcm.widget()->findChild<QLabel *>("error")->text().isEmpty());
        kcm.load();
        QCOMPARE(kcm.widget()->findChild<QSpinBox *>("screen")->value(), 900);
        QVERIFY(!kcm.needsSave());
    }
};
QTEST_MAIN(ManagerTest)
#include "test-manager.moc"

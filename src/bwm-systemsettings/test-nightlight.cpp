// SPDX-License-Identifier: GPL-2.0-or-later
#include "nightlightmodule.h"
#include <KPluginFactory>
#include <QCheckBox>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QSpinBox>
#include <QTemporaryDir>
#include <QtTest>

class NativeKcmTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void defaultsApplyResetAndFailure() {
        QTemporaryDir temp;
        QVERIFY(temp.isValid());
        const auto script = temp.filePath(QStringLiteral("fake.py"));
        const auto state = temp.filePath(QStringLiteral("state.json"));
        QFile backend(script);
        QVERIFY(backend.open(QIODevice::WriteOnly));
        backend.write(R"PY(import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
if p.exists() and p.read_text() == 'broken':
    print('not json')
    sys.exit(1)
s = json.loads(p.read_text()) if p.exists() else {'enabled': True, 'temperature': 5000}
args = sys.argv[2:]
if '--temperature' in args:
    s['temperature'] = int(args[args.index('--temperature') + 1])
    s['enabled'] = '--on' in args
    p.write_text(json.dumps(s))
print(json.dumps(s))
)PY");
        backend.close();
        NightlightModule kcm(nullptr, KPluginMetaData(), {QStringLiteral("python3"), script, state});
        auto *enabled = kcm.widget()->findChild<QCheckBox *>(QStringLiteral("enabled"));
        auto *temperature = kcm.widget()->findChild<QSpinBox *>(QStringLiteral("temperature"));
        auto *error = kcm.widget()->findChild<QLabel *>(QStringLiteral("error"));
        QVERIFY(enabled && temperature && error);
        kcm.load();
        QTRY_VERIFY(kcm.widget()->isEnabled());
        QCOMPARE(temperature->value(), 5000);
        QVERIFY(enabled->isChecked());
        QVERIFY(!kcm.needsSave());
        QVERIFY(!kcm.representsDefaults());
        kcm.defaults();
        QVERIFY(kcm.needsSave());
        QVERIFY(kcm.representsDefaults());
        QVERIFY(!QFile::exists(state)); // Defaults must not apply anything.
        kcm.load();
        QTRY_VERIFY(kcm.widget()->isEnabled());
        QCOMPARE(temperature->value(), 5000);
        QVERIFY(!kcm.needsSave());
        temperature->setValue(3500);
        enabled->setChecked(false);
        QVERIFY(kcm.needsSave());
        kcm.save();
        QVERIFY(kcm.widget()->isEnabled());
        QVERIFY(!kcm.needsSave());
        QFile stored(state);
        QVERIFY(stored.open(QIODevice::ReadOnly));
        const auto data = QJsonDocument::fromJson(stored.readAll()).object();
        stored.close();
        QCOMPARE(data.value(QStringLiteral("temperature")).toInt(), 3500);
        QCOMPARE(data.value(QStringLiteral("enabled")).toBool(), false);
        QVERIFY(stored.open(QIODevice::WriteOnly | QIODevice::Truncate));
        stored.write("broken");
        stored.close();
        temperature->setValue(4500);
        kcm.save();
        QTRY_VERIFY(kcm.widget()->isEnabled());
        QVERIFY(kcm.needsSave()); // Failed saves must not lose the dirty state.
        QVERIFY(!error->text().isEmpty());
    }
    void pluginDiscoveryAndFactory() {
        QCoreApplication::addLibraryPath(QString::fromLocal8Bit(BWM_TEST_PLUGIN_ROOT));
        const auto plugins = KPluginMetaData::findPlugins(QStringLiteral("plasma/kcms/systemsettings"));
        auto it = std::find_if(plugins.begin(), plugins.end(), [](const auto &p) { return p.pluginId() == QStringLiteral("kcm_bwm_nightlight"); });
        QVERIFY(it != plugins.end());
        const auto result = KPluginFactory::instantiatePlugin<KCModule>(*it, nullptr);
        QVERIFY2(result.plugin, qPrintable(result.errorString));
        delete result.plugin; // Never load/save the real user's settings in this test.
    }
};
QTEST_MAIN(NativeKcmTest)
#include "test-nightlight.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KCModule>
#include <QApplication>
#include <QCheckBox>
#include <QImage>
#include <QProcess>
#include <QTemporaryDir>
#include <QtTest>
#include <QStandardPaths>
static QTemporaryDir *s_tmp = nullptr;
class DecorationOptionTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void nativeOptionPersistsAndChangesRendering() {
        // The config roots are redirected in main(), before QApplication: a platform theme or
        // widget style created with the application may open breezerc first, and KSharedConfig
        // would then keep writing the user's real file (§374).
        QTemporaryDir &tmp = *s_tmp;
        QVERIFY(tmp.isValid());
        QCOMPARE(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation), tmp.path());
        const auto decoration = KPluginMetaData::findPluginById("org.kde.kdecoration3", "org.kde.breeze");
        QVERIFY(decoration.isValid());
        // No fixed BWM option catalog: follow the installed decoration's configuration metadata.
        const auto config = KPluginMetaData::findPluginById("org.kde.kdecoration3.kcm", decoration.value("X-KDE-ConfigModule"));
        QVERIFY(config.isValid());
        for (bool enabled : {false, true}) {
            const auto result = KPluginFactory::instantiatePlugin<KCModule>(config, nullptr);
            QVERIFY2(result.plugin, qPrintable(result.errorString));
            auto *kcm = result.plugin;
            kcm->load();
            auto *gradient = kcm->widget()->findChild<QCheckBox *>("drawBackgroundGradient");
            QVERIFY(gradient); // This option belongs to the installed module, absent from BWM's fixed pages.
            gradient->setChecked(enabled);
            kcm->save();
            delete kcm;
            const auto reopened = KPluginFactory::instantiatePlugin<KCModule>(config, nullptr);
            QVERIFY(reopened.plugin);
            reopened.plugin->load();
            QCOMPARE(reopened.plugin->widget()->findChild<QCheckBox *>("drawBackgroundGradient")->isChecked(), enabled);
            delete reopened.plugin;
            QProcess render;
            render.start(QCoreApplication::applicationDirPath() + "/test-decoration-render", {"org.kde.breeze", "", tmp.filePath(enabled ? "on.png" : "off.png")});
            QVERIFY(render.waitForFinished(15000));
            QCOMPARE(render.exitCode(), 0);
        }
        const QImage on(tmp.filePath("on.png")), off(tmp.filePath("off.png"));
        QVERIFY(!on.isNull() && !off.isNull());
        QVERIFY(on != off); // Installed KDecoration renderer actually consumed the saved option.
    }
};
int main(int argc, char **argv)
{
    QTemporaryDir tmp;
    if (!tmp.isValid())
        return 1;
    s_tmp = &tmp;
    qputenv("XDG_CONFIG_HOME", tmp.path().toUtf8());
    qputenv("XDG_CONFIG_DIRS", tmp.path().toUtf8());
    qunsetenv("QT_QPA_PLATFORMTHEME");
    QApplication app(argc, argv);
    DecorationOptionTest test;
    return QTest::qExec(&test, argc, argv);
}
#include "test-decoration-option.moc"

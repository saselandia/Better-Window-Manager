// SPDX-License-Identifier: GPL-2.0-or-later
#include <QApplication>
#include <KPluginMetaData>
#include <KPluginFactory>
#include <KCModule>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QCheckBox>
#include <KDecoration3/DecorationThemeProvider>
#include <cstdio>

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    QJsonArray entries;
    for (const auto &m : KPluginMetaData::findPlugins(QStringLiteral("org.kde.kdecoration3"))) {
        const auto configId = m.value(QStringLiteral("X-KDE-ConfigModule"));
        QJsonObject item{{"id", m.pluginId()}, {"file", m.fileName()}, {"configModule", configId},
                         {"decorationMetadata", m.rawData().value(QStringLiteral("org.kde.kdecoration3"))}};
        if (app.arguments().contains(QStringLiteral("--probe")) && item.value("decorationMetadata").toObject().value("themes").toBool()) {
            const auto factory = KPluginFactory::loadFactory(m);
            if (factory.plugin) {
                auto *provider = factory.plugin->create<KDecoration3::DecorationThemeProvider>(nullptr, QVariantList{item.value("decorationMetadata").toObject().value("themeListKeyword").toString()});
                QJsonArray themes;
                if (provider) {
                    for (const auto &theme : provider->themes())
                        themes.append(QJsonObject{{"id", theme.themeName()}, {"name", theme.visibleName()}, {"configModule", theme.configurationName()}});
                    delete provider;
                }
                item.insert("themes", themes);
            }
        }
        if (!configId.isEmpty()) {
            const auto config = KPluginMetaData::findPluginById(QStringLiteral("org.kde.kdecoration3.kcm"), configId);
            item.insert("configFile", config.fileName());
            item.insert("configMetadataValid", config.isValid());
            // Explicit opt-in factory probe: listing metadata never executes third-party code.
            if (app.arguments().contains(QStringLiteral("--probe"))) {
                const auto factory = KPluginFactory::instantiatePlugin<KCModule>(config, nullptr);
                item.insert("factoryInstantiated", bool(factory.plugin));
                if (factory.plugin) {
                    QJsonArray controls;
                    for (auto *child : factory.plugin->widget()->findChildren<QCheckBox *>())
                        controls.append(QJsonObject{{"name", child->objectName()}, {"label", child->text()}});
                    item.insert("checkboxes", controls);
                    delete factory.plugin;
                } else item.insert("error", factory.errorString);
            }
        }
        entries.append(item);
    }
    printf("%s\n", QJsonDocument(entries).toJson(QJsonDocument::Indented).constData());
}

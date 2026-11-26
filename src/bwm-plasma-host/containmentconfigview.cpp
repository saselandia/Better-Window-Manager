/*
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/containmentconfigview.cpp and the
    wallpaper part of ShellCorona::setWallpaper. The original ContainmentConfiguration.qml
    and ConfigurationContainment*.qml of the installed shell package are loaded unchanged.
*/

#include "containmentconfigview.h"
#include "currentcontainmentactionsmodel.h"
#include "desktopviewhost.h"
#include "wallpaperbridge.h"
#include "viewcorona.h"

#include <QDebug>
#include <QDir>
#include <QFile>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QStandardPaths>
#include <QTimer>
#include <memory>
#include <utility>

#include <KConfigLoader>
#include <KConfigPropertyMap>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <Plasma/Containment>
#include <Plasma/ContainmentActions>
#include <Plasma/Corona>
#include <Plasma/PluginLoader>

using namespace Qt::StringLiterals;

// config-workspace.h of plasma-workspace 6.7.5
#define PLASMA_RELATIVE_DATA_INSTALL_DIR "plasma"

class WallpaperConfigModel : public PlasmaQuick::ConfigModel
{
    Q_OBJECT
public:
    WallpaperConfigModel(QObject *parent);
public Q_SLOTS:
    void repopulate();
Q_SIGNALS:
    void wallpaperPluginsChanged();
};

//////////////////////////////ContainmentConfigView
ContainmentConfigView::ContainmentConfigView(Plasma::Containment *cont, DesktopViewHost *host, QWindow *parent)
    : ConfigView(cont, parent)
    , m_containment(cont)
    , m_host(host)
{
    qmlRegisterAnonymousType<QAbstractItemModel>("QAbstractItemModel", 1);
    setCurrentWallpaper(cont->containment()->wallpaperPlugin());

    syncWallpaperObjects();
}

ContainmentConfigView::~ContainmentConfigView() = default;

void ContainmentConfigView::init()
{
    // BWM: the host Corona carries its own minimal shell package; the containment
    // configuration UI comes from the installed org.kde.plasma.desktop shell.
    const auto shell = KPackage::PackageLoader::self()->loadPackage(u"Plasma/Shell"_s, u"org.kde.plasma.desktop"_s);
    const QUrl source = shell.fileUrl("containmentconfigurationui");
    if (!shell.isValid() || source.isEmpty()) {
        m_error = u"The installed KDE Plasma shell ContainmentConfiguration.qml is missing."_s;
        return;
    }
    setSource(source);
    // Native Plasma opens with Apply disabled even when the image backend
    // normalizes SlidePaths during creation. Clear that initial notification once:
    // leaving unsavedChanges=true would swallow the first real user change.
    // Subsequent changes are handled entirely by the installed QML.
    QTimer::singleShot(0, this, [this] {
        if (auto *root = rootObject(); root && root->metaObject()->indexOfMethod("settingValueChanged()") >= 0) {
            QVariant window;
            if(QMetaObject::invokeMethod(root,"applicationWindow",Q_RETURN_ARG(QVariant,window))) {
                if(auto *app=window.value<QObject*>())
                    if(auto *page=app->property("currentConfigPage").value<QObject*>())page->setProperty("unsavedChanges",false);
            }
            root->setProperty("wasConfigurationChangedSignalSent",false);
            QMetaObject::invokeMethod(root, "settingValueChanged");
        }
    });
}

PlasmaQuick::ConfigModel *ContainmentConfigView::containmentActionConfigModel()
{
    if (!m_containmentActionConfigModel) {
        m_containmentActionConfigModel = new PlasmaQuick::ConfigModel(this);

        const QList<KPluginMetaData> actions = Plasma::PluginLoader::self()->listContainmentActionsMetaData(QString());

        KPackage::Package pkg = KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Generic"));

        for (const KPluginMetaData &plugin : actions) {
            pkg.setDefaultPackageRoot(QStandardPaths::locate(QStandardPaths::GenericDataLocation,
                                                             QStringLiteral(PLASMA_RELATIVE_DATA_INSTALL_DIR "/containmentactions"),
                                                             QStandardPaths::LocateDirectory));
            m_containmentActionConfigModel->appendCategory(plugin.iconName(),
                                                           plugin.name(),
                                                           pkg.filePath("ui", QStringLiteral("config.qml")),
                                                           plugin.pluginId());
        }
    }
    return m_containmentActionConfigModel;
}

QAbstractItemModel *ContainmentConfigView::currentContainmentActionsModel()
{
    if (!m_currentContainmentActionsModel) {
        m_currentContainmentActionsModel = new CurrentContainmentActionsModel(m_containment, this);
    }
    return m_currentContainmentActionsModel;
}

QString ContainmentConfigView::containmentPlugin() const
{
    return m_containment->pluginMetaData().pluginId();
}

void ContainmentConfigView::setContainmentPlugin(const QString &plugin)
{
    if (plugin.isEmpty() || containmentPlugin() == plugin) {
        return;
    }
    // BWM: ShellCorona::setContainmentTypeForScreen is done by the desktop view that
    // owns this containment; it relaunches this dialog for the new containment.
    if (!m_host) {
        return;
    }
    if (auto *replacement = m_host->setContainmentType(plugin)) {
        m_containment = replacement;
        Q_EMIT containmentPluginChanged();
    }
}

PlasmaQuick::ConfigModel *ContainmentConfigView::wallpaperConfigModel()
{
    if (!m_wallpaperConfigModel) {
        // BWM: the disposable host has no session D-Bus, so the upstream
        // org.kde.plasma.kpackage and org.kde.PlasmaShell signals are not connected;
        // the model is repopulated every time this dialog opens.
        m_wallpaperConfigModel = new WallpaperConfigModel(this);
    }
    return m_wallpaperConfigModel;
}

PlasmaQuick::ConfigModel *ContainmentConfigView::containmentPluginsConfigModel()
{
    if (!m_containmentPluginsConfigModel) {
        m_containmentPluginsConfigModel = new PlasmaQuick::ConfigModel(this);

        const QList<KPluginMetaData> actions = Plasma::PluginLoader::self()->listContainmentsMetaDataOfType(QStringLiteral("Desktop"));
        for (const KPluginMetaData &plugin : actions) {
            m_containmentPluginsConfigModel->appendCategory(plugin.iconName(), plugin.name(), QString(), plugin.pluginId());
        }
    }
    return m_containmentPluginsConfigModel;
}

QQmlPropertyMap *ContainmentConfigView::wallpaperConfiguration() const
{
    return m_currentWallpaperConfig;
}

QString ContainmentConfigView::currentWallpaper() const
{
    return m_currentWallpaperPlugin;
}

void ContainmentConfigView::setCurrentWallpaper(const QString &wallpaperPlugin)
{
    if (m_currentWallpaperPlugin == wallpaperPlugin) {
        return;
    }

    delete std::exchange(m_ownWallpaperConfig, nullptr);

    if (m_containment->wallpaperPlugin() == wallpaperPlugin) {
        syncWallpaperObjects();
    } else {
        // we have to construct an independent ConfigPropertyMap when we want to configure wallpapers that are not the current one
        KPackage::Package pkg = KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Generic"));
        pkg.setDefaultPackageRoot(QStringLiteral(PLASMA_RELATIVE_DATA_INSTALL_DIR "/wallpapers"));
        pkg.setPath(wallpaperPlugin);
        QFile file(pkg.filePath("config", QStringLiteral("main.xml")));
        KConfigGroup cfg = m_containment->config().group(u"Wallpaper"_s).group(wallpaperPlugin);
        m_currentWallpaperConfig = m_ownWallpaperConfig = new KConfigPropertyMap(new KConfigLoader(cfg, &file, this), this);
    }

    m_currentWallpaperPlugin = wallpaperPlugin;
    Q_EMIT currentWallpaperChanged();
    Q_EMIT wallpaperConfigurationChanged();
}

void ContainmentConfigView::applyWallpaper()
{
    if (!m_currentWallpaperConfig) {
        return;
    }
    QVariantMap params;
    for (const auto &key : m_currentWallpaperConfig->keys()) {
        if (key.endsWith(QLatin1String("Default"))) {
            continue;
        }
        const QVariant value = m_currentWallpaperConfig->value(key); // https://bugreports.qt.io/browse/QTBUG-130038
        if (value.isValid()) {
            params.insert(key, value);
        }
    }

    if (m_currentWallpaperPlugin == QLatin1String("org.kde.image")) {
        params.insert(u"Image"_s, m_currentWallpaperConfig->value(u"Image"_s));
        params.remove(u"PreviewImage"_s);
    }

    if (!WallpaperBridge::apply(m_containment, m_currentWallpaperPlugin, params)) return;
    if (auto *corona = qobject_cast<ViewCorona *>(m_containment->corona()))
        Q_EMIT corona->wallpaperApplied(m_containment);
    onWallpaperChanged(uint(qMax(0, m_containment->screen())));
}

void ContainmentConfigView::onWallpaperChanged(uint /*screenIdx*/)
{
    Q_EMIT wallpaperConfigurationChanged();
}

void ContainmentConfigView::syncWallpaperObjects()
{
    auto *wallpaperGraphicsObject = m_containment->property("wallpaperGraphicsObject").value<QObject *>();

    if (!wallpaperGraphicsObject) {
        return;
    }
    rootContext()->setContextProperty(QStringLiteral("wallpaper"), wallpaperGraphicsObject);

    // FIXME: why m_wallpaperGraphicsObject->property("configuration").value<ConfigPropertyMap *>() doesn't work?
    m_currentWallpaperConfig = static_cast<QQmlPropertyMap *>(wallpaperGraphicsObject->property("configuration").value<QObject *>());
}

WallpaperConfigModel::WallpaperConfigModel(QObject *parent)
    : PlasmaQuick::ConfigModel(parent)
{
    repopulate();
}

void WallpaperConfigModel::repopulate()
{
    clear();
    for (const KPluginMetaData &m : KPackage::PackageLoader::self()->listPackages(QStringLiteral("Plasma/Wallpaper"))) {
        KPackage::Package pkg = KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Wallpaper"), m.pluginId());
        if (!pkg.isValid()) {
            continue;
        }
        appendCategory(pkg.metadata().iconName(), pkg.metadata().name(), pkg.fileUrl("ui", QStringLiteral("config.qml")).toString(), m.pluginId());
    }
    Q_EMIT wallpaperPluginsChanged();
}

#include "containmentconfigview.moc"

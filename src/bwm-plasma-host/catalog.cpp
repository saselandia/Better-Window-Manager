// SPDX-License-Identifier: GPL-2.0-or-later
#include "catalog.h"
#include <Plasma/PluginLoader>
#include <KPluginMetaData>
#include <KRuntimePlatform>
#include <KNSWidgets/Dialog>
#include <QStandardPaths>
#include <QDir>
#include <QFileInfo>
#include <QJsonObject>
QVariantMap Catalog::runtimeAssessment(const KPluginMetaData &metadata) {
    const auto id=metadata.pluginId();
    // Dependency evidence for reviewed upstream packages, NOT a widget allowlist.
    // Every unknown package remains discoverable and explicitly unassessed.
    QStringList dependencies;
    QString status=QStringLiteral("unassessed");
    if(id=="org.kde.plasma.icontasks" || id=="org.kde.plasma.taskmanager" || id=="org.kde.plasma.pager") {
        dependencies={"org_kde_plasma_window_management","org_kde_plasma_virtual_desktop_management"};
        status="requires-backend-adapter";
    } else if(id=="org.kde.plasma.showdesktop") {
        dependencies={"org.kde.KWin:/KWin or KWindowSystem showingDesktop backend"};
        status="requires-backend-adapter";
    } else if(id=="org.kde.plasma.kickoff") {
        dependencies={"KService application cache","KActivities Stats per-instance favorites","power/session action providers"};
        status="requires-runtime-validation";
    } else if(id=="org.kde.plasma.systemtray") {
        dependencies={"StatusNotifierWatcher","per-child applet services and capabilities"};
        status="requires-runtime-validation";
    }
    const QVariantMap desktopAdapter=id=="org.kde.plasma.showdesktop" ? QVariantMap{
        {"api","KWindowSystem.showingDesktop"},{"implementation","experimental-common-BWM-minimize"},
        {"optInRequired",true},{"liveSessionVerified",false},
        {"remaining",QStringList{"KWin Peek visual effect","TaskManager minimize-all secondary action"}}}:QVariantMap();
    const QVariantMap taskAdapter=(id=="org.kde.plasma.icontasks" || id=="org.kde.plasma.taskmanager") ? QVariantMap{
        {"scope","experimental-window-model-only"},{"optInRequired",true},{"liveSessionVerified",false},
        {"operations",QStringList{"focus","minimize/restore","maximize","close","fullscreen","new-instance","open-urls"}},
        {"ordering","compositor-client-order-with-legacy-snapshot-fallback"},
        {"thumbnails",QVariantMap{{"implementation","opt-in-native-toplevel-image-capture"},{"sessionVerified",false},{"kwinScreencastProtocol",false}}},
        {"remaining",QStringList{"native desktop frontend/session acceptance","native menu input/session acceptance","pinned-launcher/application-specific launch environment","other window operations","delegate geometry"}}}:QVariantMap();
    const QVariantMap desktopProtocol=dependencies.contains("org_kde_plasma_virtual_desktop_management") ? QVariantMap{
        {"implementation","experimental-bwm-plasma-desktops"},{"protocolVersion",4},{"autoLoaded",false},
        {"barrierProtocolVersion",2},{"serverArbitrationVersion",1},{"providerLifecycleVersion",1},
        {"countMirrorVersion",1},{"activationReadbackVersion",1},
        {"activationRequiresControl",true},{"withdrawalScope","same-wayland-connection"},
        {"defaultEnabled",false},{"nativeProviderVerifiedInFixture",true},{"liveSessionVerified",false},
        {"creationSupported",false},{"removalSupported",false},{"crossOutputRelocationSupported",false}}:QVariantMap();
    return {{"version",1},{"status",status},{"operationalVerified",false},{"dependencies",dependencies},
        {"experimentalDesktopAdapter",desktopAdapter},
        {"experimentalTaskSource",taskAdapter},
        {"experimentalNativeDesktopProtocol",desktopProtocol},
        {"declaredExtensions",metadata.rawData().value("X-Plasma-RequiredExtensions").toVariant()},
        {"evidence",status=="unassessed"?"not-reviewed":"reviewed-api-dependencies"}};
}
Catalog::Catalog() {
    m_debounce.setSingleShot(true);m_debounce.setInterval(150);
    connect(&m_debounce,&QTimer::timeout,this,&Catalog::refresh);
    connect(&m_watcher,&QFileSystemWatcher::directoryChanged,&m_debounce,qOverload<>(&QTimer::start));
    connect(&m_watcher,&QFileSystemWatcher::fileChanged,&m_debounce,qOverload<>(&QTimer::start));
    refresh();
}
Catalog::~Catalog(){delete m_download.data();}
QVariantList Catalog::discover() {
    QVariantList entries;
    // PluginLoader merges packaged QML with compiled/resource applets, respecting KDE policy.
    for(const auto &m:Plasma::PluginLoader::self()->listAppletMetaData(QString())) {
        const auto data=m.rawData();
        const auto containment=data.value("X-Plasma-ContainmentType").toString();
        const auto platforms=KRuntimePlatform::runtimePlatform();
        bool compatible=platforms.isEmpty() || m.formFactors().isEmpty();
        for(const auto &platform:platforms)compatible=compatible || m.formFactors().contains(platform);
        // Same visibility criteria as Plasma's widget explorer. A containment can
        // also be a widget (Folder View, CustomEmbedded system tray).
        const bool visible=m.isValid() && !data.value("NoDisplay").toBool() && m.category()!="Containments" && compatible;
        entries.append(QVariantMap{{"id",m.pluginId()},{"name",m.name()},{"metadata",m.fileName()},
            {"nativeLibrary",m.fileName().endsWith(".so")},{"kind",containment.isEmpty() ? "widget" : "containment"},
            {"containmentType",containment},{"provides",data.value("X-Plasma-Provides").toVariant()},
            {"catalogVisible",visible},
            {"formFactors",data.value("X-Plasma-FormFactors").toVariant()},
            {"requiredExtensions",data.value("X-Plasma-RequiredExtensions").toVariant()},
            {"runtime",runtimeAssessment(m)}});
    }
    return entries;
}
void Catalog::refresh() {
    const auto entries=discover();
    const bool different=entries!=m_entries;
    m_entries=entries;updateWatches();
    if(different)emit changed();
}
void Catalog::updateWatches() {
    QStringList folders,files;
    for(const auto &base:QStandardPaths::standardLocations(QStandardPaths::GenericDataLocation)) {
        QString folder=base+"/plasma/plasmoids";
        while(!QFileInfo::exists(folder) && folder!=QDir(folder).rootPath()) folder=QFileInfo(folder).absolutePath();
        if(QFileInfo(folder).isDir() && !folders.contains(folder))folders.append(folder);
    }
    for(const auto &entry:m_entries) {
        const QString path=entry.toMap().value("metadata").toString();
        if(path.endsWith(".json") && QFileInfo::exists(path)) files.append(path);
    }
    for(const auto &old:m_watcher.directories())if(!folders.contains(old))m_watcher.removePath(old);
    for(const auto &old:m_watcher.files())if(!files.contains(old))m_watcher.removePath(old);
    for(const auto &path:folders)if(!m_watcher.directories().contains(path))m_watcher.addPath(path);
    for(const auto &path:files)if(!m_watcher.files().contains(path))m_watcher.addPath(path);
}
void Catalog::getNewWidgets() {
    if(!m_download) {
        const QString provider=QStandardPaths::locate(QStandardPaths::GenericDataLocation,"knsrcfiles/plasmoids.knsrc");
        if(provider.isEmpty()) {m_error=tr("The native plasmoids.knsrc provider is missing.");emit changed();return;}
        m_download=new KNSWidgets::Dialog(provider);
        connect(m_download,&QDialog::finished,this,[this]{refresh();});
    }
    m_download->open();
}

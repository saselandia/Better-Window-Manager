// SPDX-License-Identifier: GPL-2.0-or-later
#include "themeinventory.h"
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <KPluginMetaData>
#include <KConfig>
#include <KConfigGroup>
#include <QJsonObject>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QCryptographicHash>

namespace {
QString componentFor(const QStringList &path) {
    if(path.value(0)=="plasmarc" && path.value(1)=="Theme")return "desktop-svg-reference";
    if(path.value(0)=="kwinrc" && path.value(1)=="org.kde.kdecoration2")return "decoration-reference";
    if(path.contains("Wallpaper"))return "wallpaper-reference";
    return "defaults";
}
void readDefaults(const KConfigGroup &group,const QStringList &path,QJsonArray &entries) {
    for(const auto &key:group.keyList())entries.append(QJsonObject{
        {"groups",QJsonArray::fromStringList(path)},{"key",key},{"value",group.readEntry(key,QString())},
        {"component",componentFor(path)},{"applicationVerified",false}});
    for(const auto &child:group.groupList())readDefaults(group.group(child),path+QStringList{child},entries);
}
QJsonArray defaultsAt(const QString &path) {
    QJsonArray entries;
    if(path.isEmpty() || !QFileInfo(path).isFile())return entries;
    KConfig config(path,KConfig::SimpleConfig);
    for(const auto &group:config.groupList())readDefaults(config.group(group),{group},entries);
    return entries;
}
bool belongsTo(const QString &file,const QString &package) {
    const auto base=QFileInfo(package).canonicalFilePath();
    return !base.isEmpty() && QFileInfo(file).canonicalFilePath().startsWith(base+"/");
}
}

QJsonArray globalThemeInventory() {
    QJsonArray themes;
    auto *loader=KPackage::PackageLoader::self();
    for(const auto &metadata:loader->listPackages("Plasma/LookAndFeel")) {
        const auto package=loader->loadPackage("Plasma/LookAndFeel",metadata.pluginId());
        QJsonObject files;
        for(const auto *key:{"defaults","layoutdefaults","colors","logoutmainscript","splashmainscript","windowswitchermainscript"}) {
            const auto path=package.filePath(key);
            if(!path.isEmpty())files[key]=QJsonObject{{"path",path},{"inherited",!belongsTo(path,package.path())}};
        }
        QJsonArray scripts;
        for(const auto *key:{"layouts","plasmoidsetupscripts"}) {
            const auto directory=package.filePath(key);
            if(directory.isEmpty())continue;
            QDirIterator paths(directory,{"*.js"},QDir::Files,QDirIterator::Subdirectories);
            while(paths.hasNext()) {
                const auto path=paths.next();
                const bool contained=belongsTo(path,directory);
                QFile file(path);QString hash;
                if(contained && file.open(QIODevice::ReadOnly))hash=QString::fromLatin1(QCryptographicHash::hash(file.readAll(),QCryptographicHash::Sha256).toHex());
                scripts.append(QJsonObject{{"contract",key},{"path",path},{"sha256",hash},
                    {"inherited",!belongsTo(path,package.path())},{"executeAllowed",false},
                    {"status",contained ? "requires-reviewed-layout-adapter" : "outside-package-not-read"}});
            }
        }
        themes.append(QJsonObject{{"id",metadata.pluginId()},{"name",metadata.name()},{"packagePath",package.path()},
            {"valid",package.isValid()},{"status","inventory-only"},{"resolvedFiles",files},
            {"defaults",defaultsAt(package.filePath("defaults"))},
            {"layoutDefaults",defaultsAt(package.filePath("layoutdefaults"))},{"scripts",scripts},
            {"configurationContract","Route references to native component KCMs; widgets use discovered KPackage schemas per instance. Preserve user keys/kdedefaults. Never infer widgets by evaluating layouts."}});
    }
    return themes;
}

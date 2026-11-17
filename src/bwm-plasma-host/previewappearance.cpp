// SPDX-License-Identifier: GPL-2.0-or-later
#include "previewappearance.h"
#include <KConfig>
#include <KConfigGroup>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QJsonArray>

bool stagePreviewAppearance(const QString &sourceConfig, QJsonObject *report, QString *error) {
    auto fail=[&](const QString &message){if(error)*error=message;return false;};
    const auto source=QFileInfo(sourceConfig).canonicalFilePath();
    const auto target=QFileInfo(qEnvironmentVariable("XDG_CONFIG_HOME")).canonicalFilePath();
    if(source.isEmpty() || !QFileInfo(source).isDir())return fail("Appearance source must be an existing configuration directory.");
    for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"}) {
        const auto path=QFileInfo(qEnvironmentVariable(name)).canonicalFilePath();
        if(!QFileInfo(path).isDir() || !path.startsWith(QFileInfo(QDir::tempPath()).canonicalFilePath()+"/"))
            return fail("Appearance staging requires existing disposable XDG directories.");
    }
    if(source==target)return fail("Appearance source and disposable destination must differ.");
    for(const auto *name:{"kdeglobals","plasmarc"})if(QFileInfo::exists(target+'/'+name) || QFileInfo(target+'/'+name).isSymLink())
        return fail("Appearance staging cannot overwrite an existing preview configuration.");
    QTemporaryDir staged(target+"/appearance-XXXXXX");
    if(!staged.isValid())return fail("Cannot prepare disposable appearance files.");
    QJsonArray copied;int entryCount=0;
    for(const auto *name:{"kdeglobals","plasmarc"}) {
        KConfig input(source+'/'+name,KConfig::NoGlobals);
        // Sources are least-specific first in KConfig. Keep KDE's immutable/deleted
        // entry handling instead of interpreting its format with an INI parser.
        QStringList defaults;
        auto dirs=qEnvironmentVariable("BWM_R4_APPEARANCE_CONFIG_DIRS").split(QDir::listSeparator(),Qt::SkipEmptyParts);
        for(auto it=dirs.crbegin();it!=dirs.crend();++it)defaults.append(QDir(*it).absoluteFilePath(name));
        defaults.append(source+"/kdedefaults/"+name);
        input.addConfigSources(defaults);
        KConfig output(staged.path()+'/'+name,KConfig::SimpleConfig);
        for(const auto &group:input.groupList()) {
            QStringList keys;
            const KConfigGroup from(&input,group);
            if(QByteArray(name)=="plasmarc") {
                if(group=="Theme")keys={"name"};
            } else if(group.startsWith("Colors:") || group.startsWith("ColorEffects:")) keys=from.keyList();
            else if(group=="Icons")keys={"Theme"};
            else if(group=="General")keys={"ColorScheme","AccentColor","font","fixed","menuFont","toolBarFont","smallestReadableFont"};
            else if(group=="KDE")keys={"LookAndFeelPackage","widgetStyle","AnimationDurationFactor","contrast"};
            KConfigGroup to(&output,group);
            for(const auto &key:keys)if(from.hasKey(key)) {
                to.writeEntry(key,from.readEntry(key,QString()));++entryCount;
            }
        }
        if(!output.sync())return fail("Cannot serialize the native preview appearance.");
        QFile bytes(staged.path()+'/'+name);
        // Empty input legitimately produces no file. Publish an empty native file
        // so a second staging attempt cannot silently change the startup snapshot.
        QByteArray data;
        if(bytes.exists()) {
            if(!bytes.open(QIODevice::ReadOnly))return fail("Cannot read staged native appearance.");
            data=bytes.readAll();
        }
        QSaveFile destination(target+'/'+name);
        if(!destination.open(QIODevice::WriteOnly) || destination.write(data)!=data.size() || !destination.commit())
            return fail("Cannot publish the disposable appearance snapshot.");
        copied.append(name);
    }
    if(report)*report={{"version",1},{"scope","disposable-startup-snapshot"},{"files",copied},{"entries",entryCount},
        {"sourceWritten",false},{"layoutScriptsExecuted",false},{"liveThemeFollowing",false}};
    return true;
}

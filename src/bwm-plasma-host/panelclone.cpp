/*
    SPDX-FileCopyrightText: 2008 Aaron Seigo <aseigo@kde.org>
    SPDX-FileCopyrightText: 2013 Sebastian Kügler <sebas@kde.org>
    SPDX-FileCopyrightText: 2013 Ivan Cukic <ivan.cukic@kde.org>
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors
    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/shellcorona.cpp,
    ShellCorona::clonePanelTo. Keeps native configuration and remaps applet IDs;
    output/view lifecycle is handled by PanelRuntime, not ShellCorona/KWin.
*/
#include "panelclone.h"
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <KConfigGroup>
#include <KConfigLoader>
#include <QSet>

namespace {
bool copyContents(Plasma::Containment *source,Plasma::Containment *target) {
    auto oldConfig=source->config(),newConfig=target->config();source->save(oldConfig);
    oldConfig.copyTo(&newConfig);
    // Old IDs cannot remain in the clone. Read settings from source rather than
    // deleting a copied group that might have the ID of another new applet.
    newConfig.group("Applets").deleteGroup();
    auto general=newConfig.group("General");
    auto order=general.readEntry("AppletOrder",QString()).split(';',Qt::SkipEmptyParts);
    QSet<uint> used;
    for(auto *oldApplet:source->applets()) {
        if(oldApplet->destroyed())continue;
        Plasma::Applet *newApplet=nullptr;
        // Embedded system trays may already create native children during init.
        for(auto *candidate:target->applets())
            if(!used.contains(candidate->id()) && candidate->pluginName()==oldApplet->pluginName()) {newApplet=candidate;break;}
        if(!newApplet)newApplet=target->createApplet(oldApplet->pluginName());
        if(!newApplet || newApplet->failedToLaunch())return false;
        used.insert(newApplet->id());
        for(auto &entry:order)if(entry==QString::number(oldApplet->id()))entry=QString::number(newApplet->id());
        // Applet::config() is already the Configuration subgroup for an applet,
        // but the containment root for a tray. save/copy need the full native
        // applet group, including Shortcuts and vendor data, as in ShellCorona.
        auto oldAppletConfig=oldApplet->isContainment()?oldApplet->config():oldApplet->config().parent();
        auto newAppletConfig=newApplet->isContainment()?newApplet->config():newApplet->config().parent();
        oldApplet->save(oldAppletConfig);
        oldAppletConfig.copyTo(&newAppletConfig);
        auto coronaApplets=source->corona()->config()->group("Applets");
        if(coronaApplets.hasGroup(QString::number(oldApplet->id()))) {
            auto from=coronaApplets.group(QString::number(oldApplet->id()));
            auto to=coronaApplets.group(QString::number(newApplet->id()));from.copyTo(&to);
        }
        auto *oldContainment=qobject_cast<Plasma::Containment*>(oldApplet);
        auto *newContainment=qobject_cast<Plasma::Containment*>(newApplet);
        if(oldContainment && newContainment && !copyContents(oldContainment,newContainment))return false;
        // Embedded tray applets can already have an initialized KConfigLoader.
        // Reload its values as well as notifying QML; otherwise a later save
        // writes the defaults back over the copied native configuration.
        // ConfigLoader may own a different KSharedConfig (FullConfig versus
        // Corona's SimpleConfig) for this filename. Flush the copy before its
        // public load(), so it cannot read the previous on-disk defaults.
        if(!newAppletConfig.sync())return false;
        if(auto *scheme=newApplet->configScheme())scheme->load();
        newApplet->configChanged();
    }
    general.writeEntry("AppletOrder",order.join(';'));
    if(!general.sync())return false;
    if(auto *scheme=target->configScheme())scheme->load();
    target->configChanged();return true;
}
}
bool copyPanelConfiguration(Plasma::Containment *source,Plasma::Containment *target) {
    return source && target && source!=target && source->corona()==target->corona() && copyContents(source,target);
}

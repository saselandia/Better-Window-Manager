// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskpreview.h"
#include <Plasma/Applet>
#include <KConfigLoader>
bool prepareAllDesktopTaskPreview(const QList<Plasma::Applet*> &applets,QString *error){
    for(auto *applet:applets){
        auto *scheme=applet?applet->configScheme():nullptr;
        auto *item=scheme?scheme->KCoreConfigSkeleton::findItem("showOnlyCurrentDesktop"):nullptr;
        if(!item || item->property().metaType()!=QMetaType::fromType<bool>() || item->isImmutable()){
            if(error)*error="The widget has no mutable native showOnlyCurrentDesktop option.";return false;
        }
    }
    for(auto *applet:applets){
        auto *scheme=applet->configScheme();
        scheme->KCoreConfigSkeleton::findItem("showOnlyCurrentDesktop")->setProperty(false);
        if(!scheme->save()){
            if(error)*error="Cannot save the native all-desktops option in the disposable preview.";return false;
        }
    }
    return true;
}

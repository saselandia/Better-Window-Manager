// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <KConfigGroup>
#include <QStringList>

namespace BwmTrayDefaults {
// Plasma's registry auto-enables an enabled-by-default plugin only if it is not
// in knownItems. appletCreated is emitted only for new applets, after the native
// registry initialized its defaults; it is NOT emitted when restoring a layout.
inline bool apply(KConfigGroup general, bool newlyCreated = false) {
    if (!newlyCreated || general.isImmutable() || general.isEntryImmutable("knownItems") || general.isEntryImmutable("extraItems")) return false;
    auto known=general.readEntry("knownItems",QStringList());
    auto enabled=general.readEntry("extraItems",QStringList());
    for(const auto *id:{"org.kde.plasma.clipboard","org.kde.plasma.keyboardlayout"}) {
        if(!known.contains(id))known.append(id);
        enabled.removeAll(id);
    }
    general.writeEntry("knownItems",known);
    general.writeEntry("extraItems",enabled);
    return true;
}
}

// SPDX-License-Identifier: GPL-2.0-or-later
// Conversions between Qt key combinations (what kglobalacceld stores and grabs) and
// Hyprland binds (modmask + xkb keysym). Pure functions, covered by test-keymap.
#pragma once
#include <QString>
#include <optional>
#include <xkbcommon/xkbcommon.h>

namespace BwmKeymap {
// Hyprland modmask bits (wlr/xkb modifier indices, as in `hyprctl -j binds`).
constexpr quint32 ModShift = 1, ModCtrl = 4, ModAlt = 8, ModSuper = 64;

struct HyprKey {
    quint32 modmask = 0;
    xkb_keysym_t sym = XKB_KEY_NoSymbol; // Always the lowercase keysym.
    bool operator==(const HyprKey &o) const { return modmask == o.modmask && sym == o.sym; }
};
size_t qHash(const HyprKey &k, size_t seed = 0);

// One element of a Qt key sequence (modifiers | key) → Hyprland bind. Empty for
// modifier-only combinations and keys without a keysym.
std::optional<HyprKey> fromQt(int combined);
// `hyprctl -j binds` modmask + key name → Hyprland key. Empty if the name is unknown.
std::optional<HyprKey> fromHyprland(quint32 modmask, const QString &keyName);
// Hyprland key → Qt combination (0 if Qt has no key for the keysym).
int toQt(const HyprKey &key);
// "SUPER + SHIFT + s" as hl.bind expects; also the stable id of BWM actions.
QString spec(const HyprKey &key);
}

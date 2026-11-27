// SPDX-License-Identifier: GPL-2.0-or-later
#include "keymap.h"
#include <QHash>
#include <QStringList>
#include <QtGui/private/qxkbcommon_p.h>

namespace BwmKeymap {
namespace {
// Qt key (plus KeypadModifier for keypad keysyms) → lowercase keysym. Built from Qt's own
// keysym table (QXkbCommon::keysymToQtKey), so it matches what Qt clients store.
const QHash<int, xkb_keysym_t> &reverseTable()
{
    static const QHash<int, xkb_keysym_t> table = [] {
        QHash<int, xkb_keysym_t> map;
        const std::pair<xkb_keysym_t, xkb_keysym_t> ranges[] = {
            {0x20, 0x7e}, {0xa0, 0xff}, {0xff00, 0xffff}, {0x1008ff00, 0x1008ffff},
        };
        for (const auto &[first, last] : ranges) {
            for (xkb_keysym_t sym = first; sym <= last; ++sym) {
                const xkb_keysym_t lower = xkb_keysym_to_lower(sym);
                char name[64];
                if (xkb_keysym_get_name(lower, name, sizeof name) <= 0)
                    continue;
                const int qt = QXkbCommon::keysymToQtKey(lower, Qt::NoModifier);
                if (qt == 0 || qt == Qt::Key_unknown)
                    continue;
                const int entry = qt | (QXkbCommon::isKeypad(lower) ? int(Qt::KeypadModifier) : 0);
                if (!map.contains(entry))
                    map.insert(entry, lower);
            }
        }
        return map;
    }();
    return table;
}

bool isModifierKey(int key)
{
    switch (key) {
    case Qt::Key_Shift: case Qt::Key_Control: case Qt::Key_Alt: case Qt::Key_Meta:
    case Qt::Key_Super_L: case Qt::Key_Super_R: case Qt::Key_AltGr: case Qt::Key_Hyper_L:
    case Qt::Key_Hyper_R: case Qt::Key_CapsLock: case Qt::Key_NumLock:
        return true;
    default:
        return false;
    }
}
}

size_t qHash(const HyprKey &k, size_t seed) { return ::qHash(quint64(k.modmask) << 32 | k.sym, seed); }

std::optional<HyprKey> fromQt(int combined)
{
    const auto mods = Qt::KeyboardModifiers(combined & Qt::KeyboardModifierMask);
    int key = combined & ~Qt::KeyboardModifierMask;
    quint32 modmask = 0;
    if (key == Qt::Key_Backtab) {
        key = Qt::Key_Tab;
        modmask |= ModShift;
    }
    if (key == 0 || isModifierKey(key))
        return std::nullopt;
    const auto it = reverseTable().constFind(key | (mods & Qt::KeypadModifier ? int(Qt::KeypadModifier) : 0));
    if (it == reverseTable().constEnd())
        return std::nullopt;
    if (mods & Qt::ShiftModifier) modmask |= ModShift;
    if (mods & Qt::ControlModifier) modmask |= ModCtrl;
    if (mods & Qt::AltModifier) modmask |= ModAlt;
    if (mods & Qt::MetaModifier) modmask |= ModSuper;
    return HyprKey{modmask, *it};
}

std::optional<HyprKey> fromHyprland(quint32 modmask, const QString &keyName)
{
    const QByteArray name = keyName.toUtf8();
    xkb_keysym_t sym = xkb_keysym_from_name(name.constData(), XKB_KEYSYM_NO_FLAGS);
    if (sym == XKB_KEY_NoSymbol)
        sym = xkb_keysym_from_name(name.constData(), XKB_KEYSYM_CASE_INSENSITIVE);
    if (sym == XKB_KEY_NoSymbol)
        return std::nullopt;
    return HyprKey{modmask & (ModShift | ModCtrl | ModAlt | ModSuper), xkb_keysym_to_lower(sym)};
}

int toQt(const HyprKey &key)
{
    const int qt = QXkbCommon::keysymToQtKey(key.sym, Qt::NoModifier);
    if (qt == 0 || qt == Qt::Key_unknown)
        return 0;
    int mods = QXkbCommon::isKeypad(key.sym) ? int(Qt::KeypadModifier) : 0;
    if (key.modmask & ModShift) mods |= Qt::ShiftModifier;
    if (key.modmask & ModCtrl) mods |= Qt::ControlModifier;
    if (key.modmask & ModAlt) mods |= Qt::AltModifier;
    if (key.modmask & ModSuper) mods |= Qt::MetaModifier;
    return qt | mods;
}

QString spec(const HyprKey &key)
{
    QStringList parts;
    if (key.modmask & ModSuper) parts << QStringLiteral("SUPER");
    if (key.modmask & ModCtrl) parts << QStringLiteral("CTRL");
    if (key.modmask & ModAlt) parts << QStringLiteral("ALT");
    if (key.modmask & ModShift) parts << QStringLiteral("SHIFT");
    char name[64];
    if (xkb_keysym_get_name(key.sym, name, sizeof name) > 0)
        parts << QString::fromLatin1(name);
    return parts.join(QStringLiteral(" + "));
}
}

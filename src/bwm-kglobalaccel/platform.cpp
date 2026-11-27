// SPDX-License-Identifier: GPL-2.0-or-later
#include "platform.h"

static BwmPlatform *s_instance = nullptr;

BwmPlatform::BwmPlatform(QObject *parent)
    : KGlobalAccelInterface(parent)
{
    s_instance = this;
}

BwmPlatform *BwmPlatform::instance() { return s_instance; }

bool BwmPlatform::grabKey(int key, bool grab)
{
    // Accept every grab: whether a key becomes a Hyprland bind (or stays with BWM) is
    // decided by Controller. Refusing here would make kglobalacceld forget the key.
    const bool changed = grab ? !m_grabbed.contains(key) : m_grabbed.contains(key);
    if (grab)
        m_grabbed.insert(key);
    else
        m_grabbed.remove(key);
    if (changed)
        Q_EMIT grabsChanged();
    return true;
}

bool BwmPlatform::deliver(int key, bool pressed)
{
    if (!m_grabbed.contains(key))
        return false;
    const bool handled = keyEvent(key, pressed ? ShortcutKeyState::Pressed : ShortcutKeyState::Released);
    // A release is only forwarded to the shortcut that fired; it is never "handled".
    return pressed ? handled : true;
}

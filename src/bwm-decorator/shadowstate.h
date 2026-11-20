// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <KDecoration3/DecorationShadow>
#include <QPointer>
#include <array>
#include <functional>

namespace BwmDeco {
// Decoration::shadowChanged only replaces the shared object. Like KWin's Shadow,
// also observe that object's image, padding and inner rect (Aurorae/third parties).
class ShadowState : public QObject {
public:
    std::function<void()> changed;

    void follow(KDecoration3::DecorationShadow* shadow) {
        if (m_shadow == shadow)
            return;
        for (const auto& c : m_connections)
            QObject::disconnect(c);
        m_shadow = shadow;
        if (shadow) {
            auto update = [this] { invalidate(); };
            m_connections = {
                connect(shadow, &KDecoration3::DecorationShadow::shadowChanged, this, update),
                connect(shadow, &KDecoration3::DecorationShadow::paddingChanged, this, update),
                connect(shadow, &KDecoration3::DecorationShadow::innerShadowRectChanged, this, update),
                connect(shadow, &QObject::destroyed, this, update),
            };
        }
        invalidate();
    }
    void invalidate() { m_pending = true; if (changed) changed(); }
    bool pending() const { return m_pending; }
    void sent() { m_pending = false; }

private:
    QPointer<KDecoration3::DecorationShadow> m_shadow;
    std::array<QMetaObject::Connection, 4> m_connections;
    bool m_pending = true;
};
}

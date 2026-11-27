// SPDX-License-Identifier: GPL-2.0-or-later
// KGlobalAccelInterface backend for Hyprland (static platform plugin "bwm").
// kglobalacceld tells it which key combinations to grab; Controller turns them into
// Hyprland binds and calls deliver() when one of those binds fires.
#pragma once
#include <KGlobalAccelD/kglobalaccel_interface.h>
#include <QSet>

class BwmPlatform : public KGlobalAccelInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID KGlobalAccelInterface_iid FILE "bwm.json")
    Q_INTERFACES(KGlobalAccelInterface)
public:
    explicit BwmPlatform(QObject *parent = nullptr);
    bool grabKey(int key, bool grab) override;
    QSet<int> grabbed() const { return m_grabbed; }
    // Forwards a bind of ours to the registry, as KWin's input filter does.
    bool deliver(int key, bool pressed);
    static BwmPlatform *instance();
Q_SIGNALS:
    void grabsChanged();
private:
    QSet<int> m_grabbed;
};

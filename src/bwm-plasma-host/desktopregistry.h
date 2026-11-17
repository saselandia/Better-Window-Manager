// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QVariantMap>
#include <memory>
struct wl_registry;
// Observe the registry on the existing Qt Wayland connection.
class NativeDesktopRegistry:public QObject {
    Q_OBJECT
public:
    explicit NativeDesktopRegistry(QObject *parent=nullptr);
    ~NativeDesktopRegistry()override;
    bool complete()const;
    bool topologyCompatible()const;
    bool associationPresent(quint32 controlName,quint32 managementName)const;
    bool bindingMatches(quint32 controlName,quint32 managementName)const;
    QVariantMap state()const;
    wl_registry *handle()const;
    quint32 controlName()const;
    bool controlPresent(quint32 name)const;
Q_SIGNALS:
    void changed();
private:
    struct Wire;
    std::unique_ptr<Wire> m_wire;
};

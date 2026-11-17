// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QTimer>
#include <QVariantMap>
#include <memory>
class NativeDesktopRegistry;
class NativeDesktopControl:public QObject {
    Q_OBJECT
public:
    enum class Status {Ready,Pending,Unavailable};
    explicit NativeDesktopControl(QObject *parent=nullptr);
    ~NativeDesktopControl()override;
    Status ensurePaused(bool paused);
    void beginRevision(qint64 revision);
    bool resumed()const;
    QVariantMap state()const;
    static NativeDesktopControl *requiredControl(QObject *owner=nullptr);
    static QVariantMap diagnostics();
Q_SIGNALS:
    void changed();
private:
    struct Wire;
    void availability(bool available);
    void acknowledged(quint32 serial,bool paused);
    void disconnected();
    void connected();
    void send();
    void registryChanged();
    void binding(quint32 managementName);
    bool registryPending()const;
    bool bindingVerified()const;
    QString registryError()const;
    std::unique_ptr<NativeDesktopRegistry> m_registry;
    std::unique_ptr<Wire> m_wire;
    QTimer m_timeout;
    bool m_known=false,m_available=false,m_desired=true,m_hasDesired=false;
    bool m_pending=false,m_confirmed=false,m_failed=false,m_confirmedPaused=true;
    bool m_bindingKnown=false,m_registryWaiting=false,m_registryTimedOut=false,m_registryBlocked=false;
    quint32 m_managementName=0;
    quint32 m_serial=0;
    qint64 m_revision=-1;
    QString m_error;
};

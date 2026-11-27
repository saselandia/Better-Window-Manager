// SPDX-License-Identifier: GPL-2.0-or-later
// Keeps kglobalacceld and Hyprland in agreement:
//  - every bind BWM already has in the running Hyprland (keybinds.json, helpers, user Lua)
//    is registered in kglobalacceld as component "bwm", so KDE sees those keys as taken;
//  - every other key kglobalacceld grabs becomes a Hyprland bind of ours that calls back.
#pragma once
#include "keymap.h"
#include <QHash>
#include <QJsonObject>
#include <QLocalServer>
#include <QLocalSocket>
#include <QFileSystemWatcher>
#include <QObject>
#include <QSet>
#include <QTimer>

class KGlobalAccelD;
class BwmPlatform;
class QProcess;

class Controller : public QObject
{
    Q_OBJECT
public:
    Controller(KGlobalAccelD *daemon, BwmPlatform *platform, QObject *parent = nullptr);
    bool listen();
    // Removes our binds and the state file (daemon stopping or leaving Breeze).
    void shutdown();
    QJsonObject status() const;
    static QString socketPath();
    static QString statePath();

public Q_SLOTS:
    void scheduleSync();

private:
    struct BwmBind {
        BwmKeymap::HyprKey key;
        QString description;
    };
    void startSync();
    void finishSync(const QByteArray &bindsJson);
    QList<BwmBind> parseBwmBinds(const QByteArray &json) const;
    void reconcileBwmComponent(const QList<BwmBind> &binds);
    QString renderState(const QHash<BwmKeymap::HyprKey, QPair<int, QString>> &binds) const;
    void apply(const QString &stateText, const QSet<QString> &bwmSpecs);
    bool runHyprctl(const QStringList &args, int timeoutMs, QByteArray *out = nullptr) const;
    void handleClient(QLocalSocket *socket);
    void watchHyprlandEvents();
    QString friendlyFor(int key) const;
    void notify(const QString &title, const QString &body);

    KGlobalAccelD *m_daemon;
    BwmPlatform *m_platform;
    QLocalServer m_server;
    QLocalSocket m_events;
    QTimer m_syncTimer;
    QFileSystemWatcher m_configWatcher;
    qint64 m_configStamp = -1;
    QStringList m_stripped;
    QProcess *m_bindsQuery = nullptr;
    bool m_syncPending = false;
    QString m_lastState;
    QSet<QString> m_bwmSpecs;
    QSet<BwmKeymap::HyprKey> m_bwmKeys;
    QHash<BwmKeymap::HyprKey, QPair<int, QString>> m_bound;
    QStringList m_revertedEdits;
    QStringList m_notices;
    QString m_lastError;
    int m_syncs = 0;
    int m_triggers = 0;
};

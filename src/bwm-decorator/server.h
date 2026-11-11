// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include "decorator.h"

#include <KConfigWatcher>

#include <QFileSystemWatcher>
#include <QObject>
#include <QSocketNotifier>
#include <QTimer>

#include <map>
#include <memory>

namespace BwmDeco
{

class Server;

// Un cliente (el plugin de Hyprland o una prueba). Sus ventanas mueren con él.
class Connection : public QObject
{
    Q_OBJECT
public:
    Connection(Server *server, int fd);
    ~Connection() override;
    // Envía un mensaje completo; fd >= 0 viaja como SCM_RIGHTS
    bool send(const QByteArray &message, int fd = -1);
    void recreateDecorations();

Q_SIGNALS:
    void closed();

private:
    void readMessages();
    void handle(const Header &header, const char *payload, size_t size);

    Server *m_server;
    int m_fd;
    QSocketNotifier m_notifier;
    bool m_greeted = false;
    std::map<uint32_t, std::unique_ptr<Window>> m_windows;
};

class Server : public QObject
{
    Q_OBJECT
public:
    explicit Server(const QString &socketPath);
    ~Server() override;
    bool listen();
    Bridge *bridge() const { return m_bridge.get(); }

public Q_SLOTS:
    void notifyChange(int type, int arg);

private:
    void accept();
    void watchConfig();
    void configChanged();

    QString m_socketPath;
    int m_fd = -1;
    std::unique_ptr<QSocketNotifier> m_notifier;
    std::unique_ptr<Bridge> m_bridge;
    std::vector<Connection *> m_connections;
    QFileSystemWatcher m_watcher;
    QList<KConfigWatcher::Ptr> m_configWatchers;
    QTimer m_reconfigureTimer;
};

} // namespace BwmDeco

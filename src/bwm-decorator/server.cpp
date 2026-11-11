// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
#include "server.h"
#include "wire.h"

#include <KConfigWatcher>
#include <KSharedConfig>

#include <QDBusConnection>
#include <QDir>
#include <QStandardPaths>

#include <cerrno>
#include <cstring>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

namespace BwmDeco
{

static constexpr size_t MaxMessage = 64 * 1024;

// ───────────────────────────────────────────────────────────── Connection
Connection::Connection(Server *server, int fd)
    : m_server(server)
    , m_fd(fd)
    , m_notifier(fd, QSocketNotifier::Read)
{
    connect(&m_notifier, &QSocketNotifier::activated, this, &Connection::readMessages);
}

Connection::~Connection()
{
    m_windows.clear();
    ::close(m_fd);
}

bool Connection::send(const QByteArray &message, int fd)
{
    iovec iov{const_cast<char *>(message.constData()), size_t(message.size())};
    msghdr msg{};
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
    alignas(cmsghdr) char control[CMSG_SPACE(sizeof(int))];
    if (fd >= 0) {
        msg.msg_control = control;
        msg.msg_controllen = sizeof control;
        cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
        cmsg->cmsg_level = SOL_SOCKET;
        cmsg->cmsg_type = SCM_RIGHTS;
        cmsg->cmsg_len = CMSG_LEN(sizeof(int));
        std::memcpy(CMSG_DATA(cmsg), &fd, sizeof(int));
    }
    // MSG_DONTWAIT: un cliente que no lee no debe bloquear al auxiliar (pierde el mensaje)
    return ::sendmsg(m_fd, &msg, MSG_NOSIGNAL | MSG_DONTWAIT) == ssize_t(message.size());
}

void Connection::recreateDecorations()
{
    for (auto &[id, window] : m_windows)
        window->recreateDecoration();
    send(Writer(Reconfigured, 0).str(m_server->bridge()->plugin()).str(m_server->bridge()->theme()).finish());
}

void Connection::readMessages()
{
    char buffer[MaxMessage];
    for (;;) {
        const ssize_t n = ::recv(m_fd, buffer, sizeof buffer, MSG_DONTWAIT);
        if (n == 0 || (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)) {
            m_notifier.setEnabled(false);
            Q_EMIT closed();
            return;
        }
        if (n < 0)
            return;
        if (size_t(n) < sizeof(Header))
            continue;
        Header header;
        std::memcpy(&header, buffer, sizeof header);
        if (header.magic != Magic || header.size != size_t(n) - sizeof header) {
            send(Writer(Error, header.window).str(QStringLiteral("malformed message")).finish());
            continue;
        }
        if (header.version != Version) {
            send(Writer(Error, header.window).str(QStringLiteral("unsupported protocol version")).finish());
            continue;
        }
        handle(header, buffer + sizeof header, header.size);
    }
}

static bool readState(Reader &r, WindowState &state)
{
    state.size.setWidth(r.f64());
    state.size.setHeight(r.f64());
    state.scale = r.f64();
    state.flags = r.u32();
    state.edges = r.u32();
    state.caption = r.str();
    state.appClass = r.str();
    state.iconName = r.str();
    if (!(state.scale > 0) || state.scale > 8)
        state.scale = 1;
    return r.ok();
}

void Connection::handle(const Header &header, const char *payload, size_t size)
{
    Reader r(payload, size);
    if (!m_greeted && header.type != Hello) {
        send(Writer(Error, header.window).str(QStringLiteral("hello first")).finish());
        return;
    }
    switch (header.type) {
    case Hello:
        r.u32();
        m_greeted = true;
        send(Writer(HelloAck, 0).u32(Version).str(m_server->bridge()->plugin()).str(m_server->bridge()->theme()).finish());
        break;
    case CreateWindow:
    case UpdateWindow: {
        WindowState state;
        if (!readState(r, state)) {
            send(Writer(Error, header.window).str(QStringLiteral("bad window state")).finish());
            return;
        }
        auto it = m_windows.find(header.window);
        if (it == m_windows.end())
            m_windows.emplace(header.window, std::make_unique<Window>(this, header.window, m_server->bridge(), state));
        else
            it->second->setState(state);
        break;
    }
    case DestroyWindow:
        m_windows.erase(header.window);
        break;
    case Pointer: {
        const uint32_t kind = r.u32();
        const double x = r.f64(), y = r.f64();
        const uint32_t button = r.u32(), buttons = r.u32();
        const double delta = r.f64();
        auto it = m_windows.find(header.window);
        if (r.ok() && it != m_windows.end())
            it->second->pointer(kind, QPointF(x, y), button, buttons, delta);
        break;
    }
    case Ping:
        send(Writer(Pong, header.window).finish());
        break;
    default:
        send(Writer(Error, header.window).str(QStringLiteral("unknown message")).finish());
    }
}

// ───────────────────────────────────────────────────────────── Server
Server::Server(const QString &socketPath)
    : m_socketPath(socketPath)
    , m_bridge(std::make_unique<Bridge>())
{
    m_reconfigureTimer.setSingleShot(true);
    m_reconfigureTimer.setInterval(150);
    connect(&m_reconfigureTimer, &QTimer::timeout, this, &Server::configChanged);
    connect(m_bridge.get(), &Bridge::decorationsInvalidated, this, [this] {
        for (Connection *c : m_connections)
            c->recreateDecorations();
    });
    watchConfig();
}

Server::~Server()
{
    for (Connection *c : m_connections)
        delete c;
    if (m_fd >= 0) {
        ::close(m_fd);
        ::unlink(QFile::encodeName(m_socketPath).constData());
    }
}

bool Server::listen()
{
    const QByteArray path = QFile::encodeName(m_socketPath);
    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    if (size_t(path.size()) >= sizeof addr.sun_path)
        return false;
    std::memcpy(addr.sun_path, path.constData(), size_t(path.size()));
    m_fd = ::socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    if (m_fd < 0)
        return false;
    ::unlink(path.constData()); // el candado garantiza que no hay otra instancia
    if (::bind(m_fd, reinterpret_cast<sockaddr *>(&addr), sizeof addr) != 0 || ::listen(m_fd, 8) != 0)
        return false;
    m_notifier = std::make_unique<QSocketNotifier>(m_fd, QSocketNotifier::Read);
    connect(m_notifier.get(), &QSocketNotifier::activated, this, &Server::accept);
    return true;
}

void Server::accept()
{
    for (;;) {
        const int fd = ::accept4(m_fd, nullptr, nullptr, SOCK_CLOEXEC | SOCK_NONBLOCK);
        if (fd < 0)
            return;
        auto *connection = new Connection(this, fd);
        m_connections.push_back(connection);
        connect(connection, &Connection::closed, this, [this, connection] {
            std::erase(m_connections, connection);
            connection->deleteLater();
        });
    }
}

// Recarga en vivo: KConfigWatcher (cambios con notificación de KConfig, como hace Plasma) y además
// el archivo (las herramientas que lo reescriben sin notificar)
void Server::watchConfig()
{
    for (const QString &name : {QStringLiteral("kwinrc"), QStringLiteral("kdeglobals"), QStringLiteral("breezerc")}) {
        auto watcher = KConfigWatcher::create(KSharedConfig::openConfig(name));
        connect(watcher.data(), &KConfigWatcher::configChanged, this, [this] { m_reconfigureTimer.start(); });
        m_configWatchers.append(watcher);
    }
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation);
    m_watcher.addPath(dir);
    for (const QString &name : {QStringLiteral("kwinrc"), QStringLiteral("kdeglobals"), QStringLiteral("breezerc")}) {
        if (QFile::exists(dir + QLatin1Char('/') + name))
            m_watcher.addPath(dir + QLatin1Char('/') + name);
    }
    connect(&m_watcher, &QFileSystemWatcher::fileChanged, this, [this] { m_reconfigureTimer.start(); });
    connect(&m_watcher, &QFileSystemWatcher::directoryChanged, this, [this] { m_reconfigureTimer.start(); });
    // KGlobalSettings.notifyChange: lo emiten plasma-apply-colorscheme y plasma-theme.py
    QDBusConnection::sessionBus().connect(QString(), QStringLiteral("/KGlobalSettings"), QStringLiteral("org.kde.KGlobalSettings"),
                                          QStringLiteral("notifyChange"), this, SLOT(notifyChange(int, int)));
}

void Server::notifyChange(int, int)
{
    m_reconfigureTimer.start();
}

void Server::configChanged()
{
    // Los archivos reemplazados (rename atómico) dejan de estar vigilados: volver a añadirlos
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation);
    for (const QString &name : {QStringLiteral("kwinrc"), QStringLiteral("kdeglobals"), QStringLiteral("breezerc")}) {
        const QString path = dir + QLatin1Char('/') + name;
        if (QFile::exists(path) && !m_watcher.files().contains(path))
            m_watcher.addPath(path);
    }
    KSharedConfig::openConfig(QStringLiteral("kdeglobals"))->reparseConfiguration();
    KSharedConfig::openConfig(QStringLiteral("breezerc"))->reparseConfiguration();
    m_bridge->reconfigure();
}

} // namespace BwmDeco

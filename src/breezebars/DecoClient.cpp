#include "DecoClient.hpp"
#include "barDeco.hpp"
#include "globals.hpp"

#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/config/supplementary/executor/Executor.hpp>

#include <wayland-server-core.h>

#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

using namespace BwmDeco;

std::string decoratorSocketPath() {
    if (const char* p = getenv("BWM_DECORATOR_SOCKET"); p && *p)
        return p;
    const char* runtime = getenv("XDG_RUNTIME_DIR");
    return std::string(runtime && *runtime ? runtime : "/tmp") + "/bwm-decorator.sock";
}

CDecoClient::CDecoClient() {
    m_timer = wl_event_loop_add_timer(g_pCompositor->m_wlEventLoop, &CDecoClient::timerCb, this);
}

CDecoClient::~CDecoClient() {
    if (m_source)
        wl_event_source_remove(m_source);
    if (m_timer)
        wl_event_source_remove(m_timer);
    if (m_fd >= 0)
        close(m_fd);
}

std::string CDecoClient::status() const {
    if (ready())
        return std::format("conectado ({} {})", m_plugin, m_theme);
    return std::format("sin conexión{}", m_lastError.empty() ? "" : ": " + m_lastError);
}

void CDecoClient::ensureConnected() {
    if (m_fd >= 0 || m_retryArmed)
        return;
    connectNow();
}

void CDecoClient::scheduleRetry(int ms) {
    if (!m_timer || m_retryArmed)
        return;
    m_retryArmed = true;
    wl_event_source_timer_update(m_timer, ms);
}

int CDecoClient::timerCb(void* data) {
    auto* self         = static_cast<CDecoClient*>(data);
    self->m_retryArmed = false;
    if (self->m_fd < 0)
        self->connectNow();
    return 0;
}

// El supervisor (decorator.py run) relanza el auxiliar si cae; esto cubre que no esté en marcha
// (inicio de sesión sin él, «stop» a mano). Como mucho una vez cada 15 s.
void CDecoClient::maybeSpawnHelper() {
    const auto now = std::chrono::steady_clock::now();
    if (m_lastSpawn.time_since_epoch().count() != 0 && now - m_lastSpawn < std::chrono::seconds(15))
        return;
    m_lastSpawn      = now;
    const char* home = getenv("HOME");
    if (!home)
        return;
    Config::Supplementary::executor()->spawn(std::format("python3 {}/.config/hypr/skins/plasma/scripts/decorator.py start", home));
}

void CDecoClient::connectNow() {
    if (!g_pGlobalState || !g_pGlobalState->config.enabled->value())
        return; // fuera de Breeze no hace falta (y no se relanza nada)

    const std::string path = decoratorSocketPath();
    sockaddr_un       addr{};
    addr.sun_family = AF_UNIX;
    if (path.size() >= sizeof(addr.sun_path)) {
        m_lastError = "ruta del socket demasiado larga";
        return;
    }
    std::memcpy(addr.sun_path, path.c_str(), path.size() + 1);

    const int fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (fd < 0) {
        m_lastError = strerror(errno);
        scheduleRetry(5000);
        return;
    }
    // Con un socket Unix la conexión es inmediata o falla (no hay EINPROGRESS que esperar)
    if (connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof addr) != 0) {
        m_lastError = strerror(errno);
        close(fd);
        if (errno == ENOENT || errno == ECONNREFUSED)
            maybeSpawnHelper();
        scheduleRetry(m_retryMs);
        m_retryMs = std::min(m_retryMs * 2, 5000);
        return;
    }

    m_fd     = fd;
    m_source = wl_event_loop_add_fd(g_pCompositor->m_wlEventLoop, fd, WL_EVENT_READABLE | WL_EVENT_HANGUP | WL_EVENT_ERROR, &CDecoClient::readableCb, this);
    if (!m_source) {
        disconnect("no se pudo vigilar el socket");
        return;
    }
    m_lastError.clear();
    send(hello());
}

void CDecoClient::disconnect(const std::string& why) {
    if (m_source) {
        wl_event_source_remove(m_source);
        m_source = nullptr;
    }
    if (m_fd >= 0) {
        close(m_fd);
        m_fd = -1;
    }
    const bool wasReady = m_helloAcked;
    m_helloAcked        = false;
    m_lastError         = why;
    if (wasReady && g_pGlobalState) {
        for (auto& b : g_pGlobalState->bars)
            if (b)
                b->onRemoteLost();
    }
    m_retryMs = 300;
    scheduleRetry(m_retryMs);
}

bool CDecoClient::send(const std::vector<uint8_t>& msg) {
    if (m_fd < 0)
        return false;
    const ssize_t n = ::send(m_fd, msg.data(), msg.size(), MSG_DONTWAIT | MSG_NOSIGNAL);
    if (n == static_cast<ssize_t>(msg.size()))
        return true;
    if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK))
        return false; // el auxiliar no lee: se pierde y se reintenta
    if (n < 0)
        disconnect(strerror(errno));
    return false;
}

int CDecoClient::readableCb(int, uint32_t mask, void* data) {
    static_cast<CDecoClient*>(data)->onReadable(mask);
    return 0;
}

void CDecoClient::onReadable(uint32_t mask) {
    // Un tope por llamada: no acaparar el bucle si el auxiliar manda mucho
    for (int i = 0; i < 256 && m_fd >= 0; ++i) {
        static std::vector<uint8_t> buffer(65536 + 64);
        alignas(cmsghdr) char       control[CMSG_SPACE(sizeof(int) * 4)];
        iovec                       iov{buffer.data(), buffer.size()};
        msghdr                      hdr{};
        hdr.msg_iov        = &iov;
        hdr.msg_iovlen     = 1;
        hdr.msg_control    = control;
        hdr.msg_controllen = sizeof control;

        const ssize_t n = recvmsg(m_fd, &hdr, MSG_DONTWAIT | MSG_CMSG_CLOEXEC);
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
                break;
            if (errno == EINTR)
                continue;
            disconnect(strerror(errno));
            return;
        }
        if (n == 0) {
            disconnect("el auxiliar cerró la conexión");
            return;
        }

        std::vector<int> fds;
        for (cmsghdr* c = CMSG_FIRSTHDR(&hdr); c; c = CMSG_NXTHDR(&hdr, c)) {
            if (c->cmsg_level != SOL_SOCKET || c->cmsg_type != SCM_RIGHTS)
                continue;
            const size_t count = (c->cmsg_len - CMSG_LEN(0)) / sizeof(int);
            for (size_t k = 0; k < count; ++k) {
                int fd;
                std::memcpy(&fd, CMSG_DATA(c) + k * sizeof(int), sizeof fd);
                fds.push_back(fd);
            }
        }
        const int fd = fds.empty() ? -1 : fds.front();
        for (size_t k = 1; k < fds.size(); ++k)
            close(fds[k]);

        const auto msg = (hdr.msg_flags & MSG_TRUNC) ? std::nullopt : parse(buffer.data(), static_cast<size_t>(n));
        if (!msg) {
            if (fd >= 0)
                close(fd);
            continue; // mensaje mal formado: se ignora
        }
        dispatch(*msg, fd);
    }
    if (m_fd >= 0 && (mask & (WL_EVENT_HANGUP | WL_EVENT_ERROR)))
        disconnect("el auxiliar cerró la conexión");
}

void CDecoClient::dispatch(const SMessage& msg, int fd) {
    switch (msg.header.type) {
        case ServerMessage::HelloAck: {
            m_helloAcked = true;
            m_plugin     = msg.text1;
            m_theme      = msg.text2;
            m_retryMs    = 300;
            if (g_pGlobalState)
                for (auto& b : g_pGlobalState->bars)
                    if (b)
                        b->onRemoteReady();
            break;
        }
        case ServerMessage::Reconfigured:
            m_plugin = msg.text1;
            m_theme  = msg.text2;
            if (g_pGlobalState)
                for (auto& b : g_pGlobalState->bars)
                    if (b)
                        b->onRemoteReconfigured();
            break;
        case ServerMessage::Error: m_lastError = msg.text1; break;
        default: {
            if (msg.header.window == 0 || !g_pGlobalState)
                break;
            for (auto& b : g_pGlobalState->bars) {
                if (b && b->remoteId() == msg.header.window) {
                    b->onRemoteMessage(msg, fd);
                    return; // la barra se queda con el descriptor
                }
            }
            break;
        }
    }
    if (fd >= 0)
        close(fd);
}

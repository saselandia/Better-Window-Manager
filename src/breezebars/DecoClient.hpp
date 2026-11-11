// Conexión del plugin con bwm-decorator (F6b de docs/BREEZE_PLAN.md).
//
// Nunca bloquea el hilo de Hyprland: socket no bloqueante, lectura desde el bucle de eventos de
// Wayland y envíos con MSG_DONTWAIT (si el auxiliar no lee, el mensaje se pierde y la barra lo vuelve
// a mandar en el siguiente fotograma). Sin auxiliar, las barras dibujan la barra plana de siempre y
// el cliente lo relanza (decorator.py start) y reintenta.
#pragma once

#include "DecoWire.hpp"

#include <chrono>
#include <string>
#include <vector>

struct wl_event_source;

class CDecoClient {
  public:
    CDecoClient();
    ~CDecoClient();

    // Conecta si no lo está (o programa el reintento). Lo llaman las barras al dibujarse.
    void               ensureConnected();
    bool               ready() const {
        return m_fd >= 0 && m_helloAcked;
    }
    // false si no se pudo enviar (sin conexión o el auxiliar no lee): el llamante lo reintentará
    bool               send(const std::vector<uint8_t>& msg);
    uint32_t           newId() {
        return m_nextId++;
    }
    const std::string& theme() const {
        return m_theme;
    }
    const std::string& pluginName() const {
        return m_plugin;
    }
    std::string        status() const;

  private:
    void                                  connectNow();
    void                                  disconnect(const std::string& why);
    void                                  onReadable(uint32_t mask);
    void                                  dispatch(const BwmDeco::SMessage& msg, int fd);
    void                                  scheduleRetry(int ms);
    void                                  maybeSpawnHelper();

    static int                            readableCb(int fd, uint32_t mask, void* data);
    static int                            timerCb(void* data);

    int                                   m_fd         = -1;
    wl_event_source*                      m_source     = nullptr;
    wl_event_source*                      m_timer      = nullptr;
    bool                                  m_helloAcked = false;
    bool                                  m_retryArmed = false;
    uint32_t                              m_nextId     = 1;
    int                                   m_retryMs    = 300;
    std::chrono::steady_clock::time_point m_lastSpawn{};
    std::string                           m_plugin, m_theme, m_lastError;
};

inline std::unique_ptr<CDecoClient> g_pDecoClient;

// Ruta del socket: $BWM_DECORATOR_SOCKET o $XDG_RUNTIME_DIR/bwm-decorator.sock
std::string decoratorSocketPath();

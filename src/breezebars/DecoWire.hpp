// Protocolo de bwm-decorator del lado del plugin (F6b de docs/BREEZE_PLAN.md).
//
// Sin dependencias de Hyprland ni de Qt: sólo la biblioteca estándar y las constantes compartidas
// con el auxiliar (../bwm-decorator/protocol.h). Así se prueba fuera de Hyprland
// (tests/breezebars_wire_test.cpp, tests/test_breezebars.py). Descripción en
// src/bwm-decorator/PROTOCOL.md.
#pragma once

#include "../bwm-decorator/protocol.h"

#include <array>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <vector>

namespace BwmDeco {

    struct SRectD {
        double x = 0, y = 0, w = 0, h = 0;
        bool   operator==(const SRectD&) const = default;
    };

    struct SExtents {
        double left = 0, top = 0, right = 0, bottom = 0;
        bool   operator==(const SExtents&) const = default;
    };

    class CWriter {
      public:
        CWriter(uint16_t type, uint32_t window) {
            Header h{Magic, Version, type, window, 0};
            raw(&h, sizeof h);
        }
        CWriter& u32(uint32_t v) {
            return raw(&v, sizeof v);
        }
        CWriter& f64(double v) {
            return raw(&v, sizeof v);
        }
        CWriter& str(const std::string& s) {
            u32(static_cast<uint32_t>(s.size()));
            return raw(s.data(), s.size());
        }
        std::vector<uint8_t> finish() {
            const uint32_t size = static_cast<uint32_t>(m_data.size() - sizeof(Header));
            std::memcpy(m_data.data() + offsetof(Header, size), &size, sizeof size);
            return std::move(m_data);
        }

      private:
        CWriter& raw(const void* p, size_t n) {
            const auto* b = static_cast<const uint8_t*>(p);
            m_data.insert(m_data.end(), b, b + n);
            return *this;
        }
        std::vector<uint8_t> m_data;
    };

    // Lectura con límites: cualquier mensaje corto o mal formado deja ok() en false.
    class CReader {
      public:
        CReader(const uint8_t* data, size_t size) : m_data(data), m_size(size) {}
        uint32_t u32() {
            uint32_t v = 0;
            take(&v, sizeof v);
            return v;
        }
        double f64() {
            double v = 0;
            take(&v, sizeof v);
            return v;
        }
        std::string str() {
            const uint32_t n = u32();
            if (!m_ok || n > m_size - m_pos) {
                m_ok = false;
                return {};
            }
            std::string s(reinterpret_cast<const char*>(m_data + m_pos), n);
            m_pos += n;
            return s;
        }
        SRectD rect() {
            SRectD r;
            r.x = f64();
            r.y = f64();
            r.w = f64();
            r.h = f64();
            return r;
        }
        bool ok() const {
            return m_ok;
        }

      private:
        void take(void* out, size_t n) {
            if (!m_ok || n > m_size - m_pos) {
                m_ok = false;
                return;
            }
            std::memcpy(out, m_data + m_pos, n);
            m_pos += n;
        }
        const uint8_t* m_data;
        size_t         m_size;
        size_t         m_pos = 0;
        bool           m_ok  = true;
    };

    // ───────────────────────────── cliente → auxiliar

    struct SWindowState {
        double      width = 0, height = 0, scale = 1;
        uint32_t    flags = 0, edges = 0;
        std::string caption, appClass, iconName;
        bool        operator==(const SWindowState&) const = default;
    };

    inline std::vector<uint8_t> hello() {
        return CWriter(ClientMessage::Hello, 0).u32(Version).finish();
    }

    inline std::vector<uint8_t> windowState(bool create, uint32_t id, const SWindowState& s) {
        return CWriter(create ? ClientMessage::CreateWindow : ClientMessage::UpdateWindow, id)
            .f64(s.width)
            .f64(s.height)
            .f64(s.scale)
            .u32(s.flags)
            .u32(s.edges)
            .str(s.caption)
            .str(s.appClass)
            .str(s.iconName)
            .finish();
    }

    inline std::vector<uint8_t> destroyWindow(uint32_t id) {
        return CWriter(ClientMessage::DestroyWindow, id).finish();
    }

    inline std::vector<uint8_t> pointer(uint32_t id, uint32_t kind, double x, double y, uint32_t button, uint32_t buttons, double angleDeltaY) {
        return CWriter(ClientMessage::Pointer, id).u32(kind).f64(x).f64(y).u32(button).u32(buttons).f64(angleDeltaY).finish();
    }

    inline std::vector<uint8_t> ping() {
        return CWriter(ClientMessage::Ping, 0).finish();
    }

    // ───────────────────────────── auxiliar → cliente

    struct SGeometry {
        SExtents borders, resizeOnly;
        double   radius[4] = {0, 0, 0, 0}; // arriba-izq., arriba-der., abajo-der., abajo-izq.
        SRectD   titleBar;
        bool     opaque           = false;
        double   outlineThickness = 0;
        uint32_t outlineColor     = 0; // ARGB
        double   outlineRadius[4] = {0, 0, 0, 0};
    };

    struct SPart {
        uint32_t x = 0, y = 0, w = 0, h = 0; // píxeles dentro del búfer
        SRectD   logical;                    // rectángulo en la decoración
    };

    struct SFrame {
        uint32_t              serial = 0, buffer = 0;
        bool                  hasFd  = false;
        double                scale  = 1;
        uint32_t              width = 0, height = 0, stride = 0, capacity = 0;
        std::array<SPart, 4>  parts; // arriba, abajo, izquierda, derecha
        std::vector<SRectD>   damage;
    };

    struct SShadow {
        uint32_t serial = 0;
        bool     hasFd  = false;
        uint32_t width = 0, height = 0, stride = 0;
        double   dpr = 1;
        SExtents padding;
        SRectD   inner;
    };

    struct SRequest {
        uint32_t    kind = 0, arg = 0;
        SRectD      rect;
        std::string text;
    };

    struct SPointerResult {
        uint32_t kind = 0;
        bool     accepted = false;
        uint32_t section = 0, button = 0;
    };

    struct SMessage {
        Header                        header{};
        std::optional<SGeometry>      geometry;
        std::optional<SFrame>         frame;
        std::optional<SShadow>        shadow;
        std::optional<SRequest>       request;
        std::optional<SPointerResult> pointerResult;
        std::optional<uint32_t>       section;
        std::string                   text1, text2; // HelloAck (plugin, tema), Error, Reconfigured
        uint32_t                      version = 0;
    };

    // Comprueba que un Frame describe piezas dentro de su búfer. Un Frame que no lo cumple se ignora.
    inline bool frameIsSane(const SFrame& f) {
        if (f.buffer > 1 || f.width > 16384 || f.height > 16384 || f.scale <= 0 || f.scale > 8)
            return false;
        if (static_cast<uint64_t>(f.width) * 4 > f.stride || static_cast<uint64_t>(f.stride) * f.height > f.capacity)
            return false;
        for (const auto& p : f.parts)
            if (static_cast<uint64_t>(p.x) + p.w > f.width || static_cast<uint64_t>(p.y) + p.h > f.height)
                return false;
        return true;
    }

    inline bool shadowIsSane(const SShadow& s, size_t mapped) {
        return s.width <= 4096 && s.height <= 4096 && static_cast<uint64_t>(s.width) * 4 <= s.stride && static_cast<uint64_t>(s.stride) * s.height <= mapped;
    }

    // Lee un paquete completo. Devuelve nullopt si la cabecera o la carga no son válidas.
    inline std::optional<SMessage> parse(const uint8_t* data, size_t size) {
        if (size < sizeof(Header))
            return std::nullopt;
        SMessage m;
        std::memcpy(&m.header, data, sizeof(Header));
        if (m.header.magic != Magic || m.header.version != Version || m.header.size > size - sizeof(Header))
            return std::nullopt;
        CReader r(data + sizeof(Header), m.header.size);
        switch (m.header.type) {
            case ServerMessage::HelloAck:
                m.version = r.u32();
                m.text1   = r.str();
                m.text2   = r.str();
                break;
            case ServerMessage::Error: m.text1 = r.str(); break;
            case ServerMessage::Reconfigured:
                m.text1 = r.str();
                m.text2 = r.str();
                break;
            case ServerMessage::Pong: break;
            case ServerMessage::SectionUnderMouse: m.section = r.u32(); break;
            case ServerMessage::Geometry: {
                SGeometry g;
                g.borders    = {r.f64(), r.f64(), r.f64(), r.f64()};
                g.resizeOnly = {r.f64(), r.f64(), r.f64(), r.f64()};
                for (double& v : g.radius)
                    v = r.f64();
                g.titleBar         = r.rect();
                g.opaque           = r.u32() != 0;
                g.outlineThickness = r.f64();
                g.outlineColor     = r.u32();
                for (double& v : g.outlineRadius)
                    v = r.f64();
                m.geometry = g;
                break;
            }
            case ServerMessage::Frame: {
                SFrame f;
                f.serial   = r.u32();
                f.buffer   = r.u32();
                f.hasFd    = r.u32() != 0;
                f.scale    = r.f64();
                f.width    = r.u32();
                f.height   = r.u32();
                f.stride   = r.u32();
                f.capacity = r.u32();
                for (auto& p : f.parts) {
                    p.x       = r.u32();
                    p.y       = r.u32();
                    p.w       = r.u32();
                    p.h       = r.u32();
                    p.logical = r.rect();
                }
                const uint32_t n = r.u32();
                if (!r.ok() || n > 4096)
                    return std::nullopt;
                for (uint32_t i = 0; i < n; ++i)
                    f.damage.push_back(r.rect());
                m.frame = f;
                break;
            }
            case ServerMessage::Shadow: {
                SShadow s;
                s.serial  = r.u32();
                s.hasFd   = r.u32() != 0;
                s.width   = r.u32();
                s.height  = r.u32();
                s.stride  = r.u32();
                s.dpr     = r.f64();
                s.padding = {r.f64(), r.f64(), r.f64(), r.f64()};
                s.inner   = r.rect();
                m.shadow  = s;
                break;
            }
            case ServerMessage::Request: {
                SRequest q;
                q.kind    = r.u32();
                q.arg     = r.u32();
                q.rect    = r.rect();
                q.text    = r.str();
                m.request = q;
                break;
            }
            case ServerMessage::PointerResult: {
                SPointerResult p;
                p.kind          = r.u32();
                p.accepted      = r.u32() != 0;
                p.section       = r.u32();
                p.button        = r.u32();
                m.pointerResult = p;
                break;
            }
            default: break; // tipos futuros: se ignoran
        }
        if (!r.ok())
            return std::nullopt;
        return m;
    }

} // namespace BwmDeco

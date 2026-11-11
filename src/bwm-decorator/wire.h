// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
// Lectura y escritura de mensajes del protocolo (protocol.h, PROTOCOL.md).
#pragma once

#include "protocol.h"

#include <QByteArray>
#include <QRectF>
#include <QString>

#include <cstring>

namespace BwmDeco {

class Writer
{
public:
    Writer(uint16_t type, uint32_t window)
    {
        Header h{Magic, Version, type, window, 0};
        m_data.append(reinterpret_cast<const char *>(&h), sizeof h);
    }
    Writer &u32(uint32_t v) { return raw(&v, sizeof v); }
    Writer &i32(int32_t v) { return raw(&v, sizeof v); }
    Writer &f64(double v) { return raw(&v, sizeof v); }
    Writer &str(const QString &s)
    {
        const QByteArray utf8 = s.toUtf8();
        u32(uint32_t(utf8.size()));
        m_data.append(utf8);
        return *this;
    }
    Writer &rect(const QRectF &r) { return f64(r.x()).f64(r.y()).f64(r.width()).f64(r.height()); }
    QByteArray finish()
    {
        const uint32_t size = uint32_t(m_data.size() - sizeof(Header));
        std::memcpy(m_data.data() + offsetof(Header, size), &size, sizeof size);
        return m_data;
    }

private:
    Writer &raw(const void *p, size_t n)
    {
        m_data.append(static_cast<const char *>(p), qsizetype(n));
        return *this;
    }
    QByteArray m_data;
};

class Reader
{
public:
    Reader(const char *data, size_t size)
        : m_data(data), m_size(size) {}
    bool ok() const { return m_ok; }
    uint32_t u32() { uint32_t v = 0; raw(&v, sizeof v); return v; }
    double f64() { double v = 0; raw(&v, sizeof v); return v; }
    QString str()
    {
        const uint32_t n = u32();
        if (!m_ok || n > m_size - m_pos) {
            m_ok = false;
            return {};
        }
        const QString s = QString::fromUtf8(m_data + m_pos, qsizetype(n));
        m_pos += n;
        return s;
    }

private:
    void raw(void *p, size_t n)
    {
        if (!m_ok || n > m_size - m_pos) {
            m_ok = false;
            return;
        }
        std::memcpy(p, m_data + m_pos, n);
        m_pos += n;
    }
    const char *m_data;
    size_t m_size;
    size_t m_pos = 0;
    bool m_ok = true;
};

} // namespace BwmDeco

// Pruebas de lo que el plugin breezebars hace fuera de Hyprland (F6b): protocolo (DecoWire.hpp) y
// cálculos (DecoLogic.hpp), con el mismo código que compila el plugin. Con un socket de
// bwm-decorator como argumento habla además con el auxiliar real como lo hará el plugin.
//
//   g++ -std=c++2b -I src/breezebars tests/breezebars_wire_test.cpp -o /tmp/t && /tmp/t [socket]
//
// Lo compila y ejecuta tests/test_breezebars.py.
#include "DecoLogic.hpp"
#include "DecoWire.hpp"

#include <chrono>
#include <cstdio>
#include <functional>
#include <poll.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

using namespace BwmDeco;

static int failures = 0;

#define CHECK(cond)                                                                                                                                          \
    do {                                                                                                                                                     \
        if (!(cond)) {                                                                                                                                       \
            std::fprintf(stderr, "FALLO %s:%d: %s\n", __FILE__, __LINE__, #cond);                                                                           \
            ++failures;                                                                                                                                      \
        }                                                                                                                                                    \
    } while (0)

static bool near(double a, double b) {
    return std::abs(a - b) < 1e-6;
}

static void testSections() {
    CHECK(cornerForSection(0) == 0);
    CHECK(cornerForSection(TITLE_BAR_AREA) == 0);
    CHECK(cornerForSection(1) == 4);     // izquierda
    CHECK(cornerForSection(2) == (1 | 4)); // arriba-izquierda
    CHECK(cornerForSection(6) == (2 | 8)); // abajo-derecha
    CHECK(cornerForSection(7) == 2);     // abajo
    std::puts("ok secciones");
}

static void testPartTargets() {
    const auto t = partTargets({100, 50, 800, 528}, {4, 28, 4, 4});
    CHECK((t[0] == SRectD{100, 50, 800, 28}));
    CHECK((t[1] == SRectD{100, 574, 800, 4}));
    CHECK((t[2] == SRectD{100, 78, 4, 496}));
    CHECK((t[3] == SRectD{896, 78, 4, 496}));
    std::puts("ok piezas");
}

static void testDamage() {
    SFrame f;
    f.width = 1200, f.height = 792, f.stride = 4800, f.capacity = 4800 * 792, f.scale = 1.5;
    f.parts = {SPart{0, 0, 1200, 42, {0, 0, 800, 28}}, SPart{0, 42, 1200, 0, {0, 528, 800, 0}}, SPart{0, 42, 0, 750, {0, 28, 0, 500}},
               SPart{0, 42, 0, 750, {800, 28, 0, 500}}};
    CHECK(frameIsSane(f));
    // Un daño lógico en la barra → píxeles a escala 1,5, redondeados hacia fuera
    f.damage = {{10.2, 3, 20, 10}};
    auto d   = damageInBuffer(f, false);
    CHECK(d.size() == 1);
    CHECK((d[0] == SPixelRect{15, 4, 31, 16}));
    // Sin daños o pedido entero: todo el búfer
    f.damage.clear();
    d = damageInBuffer(f, false);
    CHECK(d.size() == 1 && d[0].w == 1200 && d[0].h == 792);
    // Una pieza fuera del búfer no se acepta
    f.parts[0].w = 1300;
    CHECK(!frameIsSane(f));
    std::puts("ok daños");
}

static void testShadow() {
    // La sombra de Breeze: 273×273, interior 1×1 en el centro, relleno 65/53/65/77
    SShadow s;
    s.width = s.height = 273, s.stride = 273 * 4, s.dpr = 1;
    s.padding = {65, 53, 65, 77};
    s.inner   = {136.5, 136.5, 1, 1};
    auto q    = shadowQuads({1000, 500, 800, 528}, s);
    CHECK(q.size() == 8);
    // Esquina superior izquierda: anclada al borde exterior, a su tamaño
    CHECK(near(q[0].dst.x, 935) && near(q[0].dst.y, 447) && near(q[0].dst.w, 136.5) && near(q[0].src.x, 0));
    // Las ocho piezas cubren el borde exterior sin pasarse
    double minX = 1e9, maxX = -1e9;
    for (auto& e : q) {
        minX = std::min(minX, e.dst.x);
        maxX = std::max(maxX, e.dst.x + e.dst.w);
    }
    CHECK(near(minX, 935) && near(maxX, 1865));
    // Ventana pequeña: las esquinas se solapan, se recortan y los lados entre ellas no se dibujan (KWin)
    q = shadowQuads({0, 0, 100, 80}, s);
    CHECK(q.size() == 4);
    for (auto& e : q)
        CHECK(e.dst.w > 0 && e.dst.h > 0 && e.src.w <= 137 && e.src.h <= 137);
    std::puts("ok sombra");
}

static void testActions() {
    CHECK(wheelAction("Maximize/Restore", 120) == eWheelAction::MAXIMIZE);
    CHECK(wheelAction("Maximize/Restore", -120) == eWheelAction::RESTORE);
    CHECK(wheelAction("Previous/Next Desktop", -120) == eWheelAction::NEXT_DESKTOP);
    CHECK(wheelAction("Raise/Lower", 120) == eWheelAction::RAISE);
    CHECK(wheelAction("Change Opacity", 120) == eWheelAction::NOTHING);
    CHECK(wheelAction("Nothing", 120) == eWheelAction::NOTHING);
    CHECK(maximizeAxis(1) == eMaximizeAxis::BOTH);
    CHECK(maximizeAxis(4) == eMaximizeAxis::VERTICAL);
    CHECK(maximizeAxis(2) == eMaximizeAxis::HORIZONTAL);
    const auto c = tooltipColors("[Colors:View]\nBackgroundNormal=1,2,3\n[Colors:Tooltip]\nBackgroundNormal=41,44,48\nForegroundNormal=252,252,252,200\n");
    CHECK(c.background == 0xff292c30u);
    CHECK(c.foreground == 0xc8fcfcfcu);
    CHECK(!parseKdeColor("rojo"));
    std::puts("ok acciones");
}

static void testParse() {
    // Mensaje construido a mano: PointerResult(press, no aceptado, barra, izquierdo)
    auto msg = CWriter(ServerMessage::PointerResult, 7).u32(Press).u32(0).u32(9).u32(1).finish();
    auto m   = parse(msg.data(), msg.size());
    CHECK(m && m->pointerResult && m->header.window == 7 && !m->pointerResult->accepted && m->pointerResult->section == 9);
    // Truncado, magia mala y versión mala: se rechazan
    CHECK(!parse(msg.data(), msg.size() - 2));
    auto bad = msg;
    bad[0] ^= 0xff;
    CHECK(!parse(bad.data(), bad.size()));
    bad = msg;
    bad[4] = 9;
    CHECK(!parse(bad.data(), bad.size()));
    // Cadena con longitud imposible
    auto str = CWriter(ServerMessage::Error, 0).u32(1000000).finish();
    CHECK(!parse(str.data(), str.size()));
    // El estado que envía el plugin se lee con los mismos campos que el auxiliar
    SWindowState st{800, 500, 1.5, Active | Closeable, 1, "título ñ", "kitty", ""};
    auto         ws = windowState(true, 3, st);
    CReader      r(ws.data() + sizeof(Header), ws.size() - sizeof(Header));
    CHECK(near(r.f64(), 800) && near(r.f64(), 500) && near(r.f64(), 1.5) && r.u32() == (Active | Closeable) && r.u32() == 1 && r.str() == "título ñ" &&
          r.str() == "kitty" && r.str().empty() && r.ok());
    std::puts("ok mensajes");
}

// ───────────────────────────────────────────── con el auxiliar real

struct SClient {
    int                                                    fd = -1;
    std::function<void(const SMessage&, int)>              onMessage;

    bool                                                   send(const std::vector<uint8_t>& m) {
        return ::send(fd, m.data(), m.size(), MSG_NOSIGNAL) == static_cast<ssize_t>(m.size());
    }
    // Lee hasta que pred() o pasa el tiempo
    bool pump(const std::function<bool()>& pred, int ms = 5000) {
        const auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);
        while (!pred()) {
            const int left = std::chrono::duration_cast<std::chrono::milliseconds>(end - std::chrono::steady_clock::now()).count();
            if (left <= 0)
                return false;
            pollfd p{fd, POLLIN, 0};
            if (poll(&p, 1, left) <= 0)
                continue;
            std::vector<uint8_t>          buffer(65600);
            alignas(cmsghdr) char         control[CMSG_SPACE(sizeof(int) * 4)];
            iovec                         iov{buffer.data(), buffer.size()};
            msghdr                        hdr{};
            hdr.msg_iov        = &iov;
            hdr.msg_iovlen     = 1;
            hdr.msg_control    = control;
            hdr.msg_controllen = sizeof control;
            const ssize_t n    = recvmsg(fd, &hdr, MSG_CMSG_CLOEXEC);
            if (n <= 0)
                return false;
            int got = -1;
            for (cmsghdr* c = CMSG_FIRSTHDR(&hdr); c; c = CMSG_NXTHDR(&hdr, c))
                if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS)
                    std::memcpy(&got, CMSG_DATA(c), sizeof got);
            auto m = parse(buffer.data(), n);
            CHECK(m.has_value());
            if (m)
                onMessage(*m, got);
            else if (got >= 0)
                close(got);
        }
        return true;
    }
};

static void testHelper(const char* path) {
    SClient c;
    c.fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    std::snprintf(addr.sun_path, sizeof addr.sun_path, "%s", path);
    CHECK(connect(c.fd, reinterpret_cast<sockaddr*>(&addr), sizeof addr) == 0);

    bool                          acked = false;
    std::optional<SGeometry>      geometry;
    std::optional<SFrame>         frame;
    std::vector<uint8_t>          pixels;
    std::optional<SShadow>        shadow;
    std::vector<SPointerResult>   results;
    void*                         maps[2] = {nullptr, nullptr};
    size_t                        sizes[2] = {0, 0};
    c.onMessage = [&](const SMessage& m, int fd) {
        if (m.header.type == ServerMessage::HelloAck)
            acked = true;
        if (m.geometry)
            geometry = m.geometry;
        if (m.frame) {
            const auto& f = *m.frame;
            if (f.hasFd && fd >= 0 && f.buffer < 2) {
                if (maps[f.buffer])
                    munmap(maps[f.buffer], sizes[f.buffer]);
                maps[f.buffer]  = mmap(nullptr, f.capacity, PROT_READ, MAP_SHARED, fd, 0);
                sizes[f.buffer] = f.capacity;
            }
            CHECK(frameIsSane(f));
            if (f.buffer < 2 && maps[f.buffer] && maps[f.buffer] != MAP_FAILED) {
                pixels.assign(static_cast<uint8_t*>(maps[f.buffer]), static_cast<uint8_t*>(maps[f.buffer]) + static_cast<size_t>(f.stride) * f.height);
                frame = f;
            }
        }
        if (m.shadow) {
            shadow = m.shadow;
            if (m.shadow->hasFd && fd >= 0) {
                const size_t size = static_cast<size_t>(m.shadow->stride) * m.shadow->height;
                void*        p    = mmap(nullptr, size, PROT_READ, MAP_SHARED, fd, 0);
                CHECK(p != MAP_FAILED && shadowIsSane(*m.shadow, size));
                if (p != MAP_FAILED)
                    munmap(p, size);
            }
        }
        if (m.pointerResult)
            results.push_back(*m.pointerResult);
        if (fd >= 0)
            close(fd);
    };

    CHECK(c.send(hello()));
    CHECK(c.pump([&] { return acked; }));
    SWindowState st{800, 500, 1.0, Active | Closeable | Maximizeable | Minimizeable | Moveable | Resizeable, 0, "kitty — prueba", "kitty", ""};
    CHECK(c.send(windowState(true, 1, st)));
    CHECK(c.pump([&] { return geometry && frame && shadow; }));
    if (!geometry || !frame) {
        std::puts("sin geometría o imagen del auxiliar");
        ++failures;
        return;
    }
    // Breeze: barra arriba, la imagen cubre el marco entero
    CHECK(geometry->borders.top > 20);
    CHECK(near(frame->parts[0].logical.w, 800 + geometry->borders.left + geometry->borders.right));
    // La barra tiene píxeles opacos en su centro (el título y el fondo de la cabecera)
    const auto& top   = frame->parts[0];
    const auto  pixel = [&](uint32_t x, uint32_t y) { return pixels[static_cast<size_t>(y) * frame->stride + x * 4 + 3]; };
    CHECK(pixel(top.x + top.w / 3, top.y + top.h / 2) == 255);
    // Sombra de nueve trozos completa alrededor de esta ventana
    CHECK(shadow && shadowQuads({0, 0, 800 + geometry->borders.left + geometry->borders.right, 500 + geometry->borders.top + geometry->borders.bottom}, *shadow).size() == 8);

    // Pulsar la barra lejos de los botones: no la acepta, sección 9 → el plugin mueve la ventana
    const double x = geometry->titleBar.x + geometry->titleBar.w * 0.3, y = geometry->titleBar.y + geometry->titleBar.h / 2;
    c.send(pointer(1, Motion, x, y, 0, 0, 0));
    c.send(pointer(1, Press, x, y, 1, 1, 0));
    c.send(pointer(1, Release, x, y, 1, 0, 0));
    CHECK(c.pump([&] { return results.size() >= 2; }));
    CHECK(!results.empty() && results[0].kind == Press && !results[0].accepted && results[0].section == TITLE_BAR_AREA && results[0].button == 1);
    // Rueda sobre la barra: también llega su respuesta (la acción la decide kwinrc)
    results.clear();
    c.send(pointer(1, Wheel, x, y, 0, 0, 120));
    CHECK(c.pump([&] { return !results.empty(); }));
    CHECK(!results.empty() && results[0].kind == Wheel && results[0].section == TITLE_BAR_AREA);

    // Al cambiar el tamaño llega una imagen nueva del tamaño nuevo
    const uint32_t before = frame->serial;
    st.width              = 1000;
    c.send(windowState(false, 1, st));
    CHECK(c.pump([&] { return frame->serial != before && near(frame->parts[0].logical.w, 1000 + geometry->borders.left + geometry->borders.right); }));
    c.send(destroyWindow(1));
    for (int i = 0; i < 2; ++i)
        if (maps[i] && maps[i] != MAP_FAILED)
            munmap(maps[i], sizes[i]);
    close(c.fd);
    std::puts("ok auxiliar");
}

int main(int argc, char** argv) {
    testSections();
    testPartTargets();
    testDamage();
    testShadow();
    testActions();
    testParse();
    if (argc > 1)
        testHelper(argv[1]);
    if (failures)
        std::fprintf(stderr, "%d fallos\n", failures);
    return failures ? 1 : 0;
}

// SPDX-License-Identifier: GPL-2.0-or-later
#include "screenedges.h"
#include <KConfig>
#include <KConfigGroup>
#include <LayerShellQt/Window>
#include <QDir>
#include <QEvent>
#include <QFileInfo>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QProcess>
#include <QScreen>
#include <QStandardPaths>
#include <QWindow>

namespace {
class EdgeSensorWindow : public QWindow {
public:
    EdgeSensorWindow(ScreenEdges::Edge edge, QScreen *screen,
                     std::function<void(ScreenEdges::Edge, QScreen *)> onEnter,
                     std::function<void(ScreenEdges::Edge, QScreen *)> onLeave)
        : m_edge(edge), m_screen(screen), m_onEnter(std::move(onEnter)), m_onLeave(std::move(onLeave)) {
        setFlags(Qt::FramelessWindowHint | Qt::WindowDoesNotAcceptFocus | Qt::Tool);
        setScreen(screen);
    }

protected:
    bool event(QEvent *ev) override {
        if (ev->type() == QEvent::Enter) {
            if (m_onEnter) m_onEnter(m_edge, m_screen);
            return true;
        }
        if (ev->type() == QEvent::Leave) {
            if (m_onLeave) m_onLeave(m_edge, m_screen);
            return true;
        }
        return QWindow::event(ev);
    }

private:
    ScreenEdges::Edge m_edge;
    QPointer<QScreen> m_screen;
    std::function<void(ScreenEdges::Edge, QScreen *)> m_onEnter;
    std::function<void(ScreenEdges::Edge, QScreen *)> m_onLeave;
};

bool edgeFromInt(int value, ScreenEdges::Edge *out) {
    if (value < 0 || value > 7) return false;
    *out = static_cast<ScreenEdges::Edge>(value);
    return true;
}

ScreenEdges::Action electricActionFromName(const QString &name) {
    const QString low = name.trimmed().toLower();
    if (low == QStringLiteral("showdesktop")) return ScreenEdges::Action::ShowDesktop;
    if (low == QStringLiteral("lockscreen")) return ScreenEdges::Action::LockScreen;
    return ScreenEdges::Action::None;
}

bool isCorner(ScreenEdges::Edge edge) {
    return edge == ScreenEdges::Edge::TopLeft || edge == ScreenEdges::Edge::TopRight
        || edge == ScreenEdges::Edge::BottomLeft || edge == ScreenEdges::Edge::BottomRight;
}

LayerShellQt::Window::Anchors anchorsForEdge(ScreenEdges::Edge edge) {
    using W = LayerShellQt::Window;
    switch (edge) {
    case ScreenEdges::Edge::Top: return W::AnchorTop;
    case ScreenEdges::Edge::TopRight: return W::Anchors(W::AnchorTop) | W::AnchorRight;
    case ScreenEdges::Edge::Right: return W::AnchorRight;
    case ScreenEdges::Edge::BottomRight: return W::Anchors(W::AnchorBottom) | W::AnchorRight;
    case ScreenEdges::Edge::Bottom: return W::AnchorBottom;
    case ScreenEdges::Edge::BottomLeft: return W::Anchors(W::AnchorBottom) | W::AnchorLeft;
    case ScreenEdges::Edge::Left: return W::AnchorLeft;
    case ScreenEdges::Edge::TopLeft: return W::Anchors(W::AnchorTop) | W::AnchorLeft;
    }
    return W::AnchorNone;
}
} // namespace

ScreenEdges::ScreenEdges(QObject *parent) : QObject(parent) {
    m_kwinrcPath = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation)
        + QStringLiteral("/kwinrc");
    m_reloadDebounce.setSingleShot(true);
    m_reloadDebounce.setInterval(150);
    connect(&m_reloadDebounce, &QTimer::timeout, this, &ScreenEdges::reload);

    m_delayTimer.setSingleShot(true);
    connect(&m_delayTimer, &QTimer::timeout, this, &ScreenEdges::firePending);

    connect(&m_watcher, &QFileSystemWatcher::fileChanged, this, [this] {
        watchConfig();
        m_reloadDebounce.start();
    });
    connect(&m_watcher, &QFileSystemWatcher::directoryChanged, this, [this] {
        watchConfig();
        m_reloadDebounce.start();
    });
}

ScreenEdges::~ScreenEdges() {
    stop();
}

void ScreenEdges::watchConfig() {
    const QString dir = QFileInfo(m_kwinrcPath).absolutePath();
    if (QDir(dir).exists() && !m_watcher.directories().contains(dir)) {
        m_watcher.addPath(dir);
    }
    if (QFileInfo::exists(m_kwinrcPath) && !m_watcher.files().contains(m_kwinrcPath)) {
        m_watcher.addPath(m_kwinrcPath);
    }
}

void ScreenEdges::start() {
    if (m_running) return;
    m_running = true;
    watchConfig();
    connect(qGuiApp, &QGuiApplication::screenAdded, this, [this](QScreen *) { rebuildSensors(); });
    connect(qGuiApp, &QGuiApplication::screenRemoved, this, [this](QScreen *) { rebuildSensors(); });
    reload();
}

void ScreenEdges::stop() {
    m_running = false;
    m_delayTimer.stop();
    m_reloadDebounce.stop();
    clearSensors();
}

void ScreenEdges::reload() {
    m_config = parseKwinrc(m_kwinrcPath);
    if (m_running) rebuildSensors();
}

void ScreenEdges::setActionHandler(std::function<void(Action, QScreen *)> handler) {
    m_handler = std::move(handler);
}

void ScreenEdges::setFullscreenChecker(std::function<bool(QScreen *)> checker) {
    m_fullscreenChecker = std::move(checker);
}

QString ScreenEdges::edgeName(Edge edge) {
    switch (edge) {
    case Edge::Top: return QStringLiteral("Top");
    case Edge::TopRight: return QStringLiteral("TopRight");
    case Edge::Right: return QStringLiteral("Right");
    case Edge::BottomRight: return QStringLiteral("BottomRight");
    case Edge::Bottom: return QStringLiteral("Bottom");
    case Edge::BottomLeft: return QStringLiteral("BottomLeft");
    case Edge::Left: return QStringLiteral("Left");
    case Edge::TopLeft: return QStringLiteral("TopLeft");
    }
    return QStringLiteral("None");
}

QString ScreenEdges::actionName(Action action) {
    switch (action) {
    case Action::None: return QStringLiteral("None");
    case Action::Overview: return QStringLiteral("Overview");
    case Action::Grid: return QStringLiteral("Grid");
    case Action::WindowViewCurrent: return QStringLiteral("WindowViewCurrent");
    case Action::WindowViewAll: return QStringLiteral("WindowViewAll");
    case Action::ShowDesktop: return QStringLiteral("ShowDesktop");
    case Action::LockScreen: return QStringLiteral("LockScreen");
    case Action::TabBox: return QStringLiteral("TabBox");
    }
    return QStringLiteral("None");
}

ScreenEdges::Config ScreenEdges::parseKwinrc(const QString &kwinrcPath) {
    Config cfg;
    KConfig kwinrc(kwinrcPath, KConfig::SimpleConfig);

    const KConfigGroup windows = kwinrc.group(QStringLiteral("Windows"));
    cfg.delayMs = qBound(0, windows.readEntry("ElectricBorderDelay", 75), 2000);
    cfg.cooldownMs = qBound(50, windows.readEntry("ElectricBorderCooldown", 350), 5000);

    const KConfigGroup screenEdges = kwinrc.group(QStringLiteral("ScreenEdges"));
    cfg.remainActiveOnFullscreen = screenEdges.readEntry("RemainActiveOnFullscreen", false);

    // 1. Named ElectricBorders group (ShowDesktop, LockScreen, etc.)
    const KConfigGroup electric = kwinrc.group(QStringLiteral("ElectricBorders"));
    const QList<QPair<QString, Edge>> named = {
        {QStringLiteral("Top"), Edge::Top},
        {QStringLiteral("TopRight"), Edge::TopRight},
        {QStringLiteral("Right"), Edge::Right},
        {QStringLiteral("BottomRight"), Edge::BottomRight},
        {QStringLiteral("Bottom"), Edge::Bottom},
        {QStringLiteral("BottomLeft"), Edge::BottomLeft},
        {QStringLiteral("Left"), Edge::Left},
        {QStringLiteral("TopLeft"), Edge::TopLeft},
    };
    for (const auto &pair : named) {
        const Action act = electricActionFromName(electric.readEntry(pair.first, QStringLiteral("None")));
        if (act != Action::None) cfg.actions.insert(pair.second, act);
    }

    auto readEdgeList = [&](const KConfigGroup &group, const char *key, const QList<int> &defaults, Action action) {
        const QList<int> raw = group.readEntry(key, defaults);
        for (int val : raw) {
            Edge edge;
            if (edgeFromInt(val, &edge)) cfg.actions.insert(edge, action);
        }
    };

    // 2. TabBox
    readEdgeList(kwinrc.group(QStringLiteral("TabBox")), "BorderActivate", {}, Action::TabBox);

    // 3. WindowView
    const KConfigGroup wv = kwinrc.group(QStringLiteral("Effect-windowview"));
    readEdgeList(wv, "BorderActivate", {}, Action::WindowViewCurrent);
    readEdgeList(wv, "BorderActivateAll", {}, Action::WindowViewAll);

    // 4. Overview & Grid (Plasma 6 default: TopLeft = 7 activates Overview)
    const KConfigGroup ov = kwinrc.group(QStringLiteral("Effect-overview"));
    const bool hasOvKey = ov.hasKey("BorderActivate");
    readEdgeList(ov, "BorderActivate", hasOvKey ? QList<int>{} : QList<int>{int(Edge::TopLeft)}, Action::Overview);
    readEdgeList(ov, "GridBorderActivate", {}, Action::Grid);

    return cfg;
}

bool ScreenEdges::isExteriorEdge(const QRect &screen, const QList<QRect> &allScreens, Edge edge) {
    if (!screen.isValid()) return false;
    // Probe a 4px band just outside the screen along the requested corner or edge.
    // If another output overlaps that probe, this edge/corner is shared between monitors
    // and must NOT host a hot-corner sensor (so pointer travel between displays stays free).
    constexpr int pad = 4;
    QList<QRect> probes;
    const int x1 = screen.left();
    const int y1 = screen.top();
    const int x2 = screen.right() + 1;
    const int y2 = screen.bottom() + 1;
    const int w = screen.width();
    const int h = screen.height();

    switch (edge) {
    case Edge::Top:
        probes.append(QRect(x1 + w / 4, y1 - pad, qMax(1, w / 2), pad));
        break;
    case Edge::Bottom:
        probes.append(QRect(x1 + w / 4, y2, qMax(1, w / 2), pad));
        break;
    case Edge::Left:
        probes.append(QRect(x1 - pad, y1 + h / 4, pad, qMax(1, h / 2)));
        break;
    case Edge::Right:
        probes.append(QRect(x2, y1 + h / 4, pad, qMax(1, h / 2)));
        break;
    case Edge::TopLeft:
        probes.append(QRect(x1 - pad, y1, pad, pad));
        probes.append(QRect(x1, y1 - pad, pad, pad));
        break;
    case Edge::TopRight:
        probes.append(QRect(x2, y1, pad, pad));
        probes.append(QRect(x2 - pad, y1 - pad, pad, pad));
        break;
    case Edge::BottomLeft:
        probes.append(QRect(x1 - pad, y2 - pad, pad, pad));
        probes.append(QRect(x1, y2, pad, pad));
        break;
    case Edge::BottomRight:
        probes.append(QRect(x2, y2 - pad, pad, pad));
        probes.append(QRect(x2 - pad, y2, pad, pad));
        break;
    }

    for (const QRect &other : allScreens) {
        if (other == screen || !other.isValid()) continue;
        for (const QRect &probe : probes) {
            if (other.intersects(probe)) return false;
        }
    }
    return true;
}

void ScreenEdges::clearSensors() {
    const auto sensors = std::exchange(m_sensors, {});
    for (const auto &w : sensors) {
        if (w) {
            w->hide();
            w->deleteLater();
        }
    }
}

void ScreenEdges::rebuildSensors() {
    clearSensors();
    if (!m_running || m_config.actions.isEmpty()) return;

    const auto screens = QGuiApplication::screens();
    QList<QRect> rects;
    rects.reserve(screens.size());
    for (auto *s : screens) rects.append(s->geometry());

    for (auto *screen : screens) {
        const QRect geom = screen->geometry();
        for (auto it = m_config.actions.constBegin(); it != m_config.actions.constEnd(); ++it) {
            const Edge edge = it.key();
            if (it.value() == Action::None) continue;
            if (!isExteriorEdge(geom, rects, edge)) continue;

            auto *win = new EdgeSensorWindow(
                edge, screen,
                [this](Edge e, QScreen *s) { handleEnter(e, s); },
                [this](Edge e, QScreen *s) { handleLeave(e, s); });

            const QSize size = isCorner(edge)
                ? QSize(2, 2)
                : (edge == Edge::Top || edge == Edge::Bottom
                       ? QSize(qMax(40, geom.width() / 3), 2)
                       : QSize(2, qMax(40, geom.height() / 3)));

            using W = LayerShellQt::Window;
            auto *layer = W::get(win);
            layer->setScope(QStringLiteral("bwm-plasma-screenedge"));
            layer->setLayer(W::LayerOverlay);
            layer->setExclusiveZone(-1);
            layer->setKeyboardInteractivity(W::KeyboardInteractivityNone);
            layer->setAnchors(anchorsForEdge(edge));
            layer->setDesiredSize(size);
            layer->setScreen(screen);

            win->resize(size);
            win->show();
            m_sensors.append(win);
        }
    }
}

void ScreenEdges::handleEnter(Edge edge, QScreen *screen) {
    if (!m_running || !m_config.actions.contains(edge)) return;
    // Never fire during window drag or pointer button press (protects §17 snapping).
    if (QGuiApplication::mouseButtons() != Qt::NoButton) return;
    if (m_hasFired && m_cooldown.elapsed() < m_config.cooldownMs) return;

    m_pendingEdge = edge;
    m_pendingScreen = screen;
    if (m_config.delayMs <= 0) {
        firePending();
    } else {
        m_delayTimer.start(m_config.delayMs);
    }
}

void ScreenEdges::handleLeave(Edge edge, QScreen *screen) {
    if (m_delayTimer.isActive() && m_pendingEdge == edge && m_pendingScreen == screen) {
        m_delayTimer.stop();
    }
}

bool ScreenEdges::isFullscreenOn(QScreen *screen) const {
    if (m_fullscreenChecker) return m_fullscreenChecker(screen);
    if (!screen) return false;
    QProcess proc;
    proc.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), QStringLiteral("activewindow")});
    if (!proc.waitForFinished(250) || proc.exitCode() != 0) return false;
    const auto obj = QJsonDocument::fromJson(proc.readAllStandardOutput()).object();
    return obj.value(QStringLiteral("fullscreen")).toInt(0) != 0;
}

void ScreenEdges::firePending() {
    if (!m_running) return;
    if (QGuiApplication::mouseButtons() != Qt::NoButton) return;
    if (m_hasFired && m_cooldown.elapsed() < m_config.cooldownMs) return;
    const Action action = m_config.actions.value(m_pendingEdge, Action::None);
    if (action == Action::None) return;
    if (!m_config.remainActiveOnFullscreen && isFullscreenOn(m_pendingScreen)) return;

    m_cooldown.start();
    m_hasFired = true;
    emit triggered(action, m_pendingScreen);
    if (m_handler) m_handler(action, m_pendingScreen);
}

QJsonObject ScreenEdges::status() const {
    QJsonObject edges;
    for (auto it = m_config.actions.constBegin(); it != m_config.actions.constEnd(); ++it) {
        edges.insert(edgeName(it.key()), actionName(it.value()));
    }
    int activeSensors = 0;
    for (const auto &w : m_sensors) {
        if (w) ++activeSensors;
    }
    return {
        {QStringLiteral("running"), m_running},
        {QStringLiteral("delayMs"), m_config.delayMs},
        {QStringLiteral("cooldownMs"), m_config.cooldownMs},
        {QStringLiteral("remainActiveOnFullscreen"), m_config.remainActiveOnFullscreen},
        {QStringLiteral("actions"), edges},
        {QStringLiteral("sensors"), activeSensors},
    };
}

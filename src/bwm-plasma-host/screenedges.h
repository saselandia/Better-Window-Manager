// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QElapsedTimer>
#include <QFileSystemWatcher>
#include <QHash>
#include <QJsonObject>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QRect>
#include <QTimer>
#include <functional>

class QScreen;
class QWindow;

class ScreenEdges : public QObject {
    Q_OBJECT
public:
    // Matches KWin::ElectricBorder numeric values from kwin 6.7.5 globals.h.
    enum class Edge : int {
        Top = 0,
        TopRight = 1,
        Right = 2,
        BottomRight = 3,
        Bottom = 4,
        BottomLeft = 5,
        Left = 6,
        TopLeft = 7,
    };
    Q_ENUM(Edge)

    enum class Action {
        None,
        Overview,
        Grid,
        WindowViewCurrent,
        WindowViewAll,
        ShowDesktop,
        LockScreen,
        TabBox,
    };
    Q_ENUM(Action)

    struct Config {
        QHash<Edge, Action> actions;
        int delayMs = 75;
        int cooldownMs = 350;
        bool remainActiveOnFullscreen = false;
    };

    explicit ScreenEdges(QObject *parent = nullptr);
    ~ScreenEdges() override;

    void start();
    void stop();
    void reload();

    void setActionHandler(std::function<void(Action, QScreen *)> handler);
    void setFullscreenChecker(std::function<bool(QScreen *)> checker);

    Config config() const { return m_config; }
    QJsonObject status() const;

    // Pure helpers exposed for unit testing.
    static Config parseKwinrc(const QString &kwinrcPath);
    static bool isExteriorEdge(const QRect &screen, const QList<QRect> &allScreens, Edge edge);
    static QString edgeName(Edge edge);
    static QString actionName(Action action);

Q_SIGNALS:
    void triggered(ScreenEdges::Action action, QScreen *screen);

private:
    struct Sensor;
    void rebuildSensors();
    void clearSensors();
    void handleEnter(Edge edge, QScreen *screen);
    void handleLeave(Edge edge, QScreen *screen);
    void firePending();
    bool isFullscreenOn(QScreen *screen) const;
    void watchConfig();

    Config m_config;
    QString m_kwinrcPath;
    QFileSystemWatcher m_watcher;
    QTimer m_reloadDebounce;
    QTimer m_delayTimer;
    QElapsedTimer m_cooldown;
    bool m_running = false;
    bool m_hasFired = false;
    Edge m_pendingEdge = Edge::TopLeft;
    QPointer<QScreen> m_pendingScreen;
    QList<QPointer<QWindow>> m_sensors;
    std::function<void(Action, QScreen *)> m_handler;
    std::function<bool(QScreen *)> m_fullscreenChecker;
};

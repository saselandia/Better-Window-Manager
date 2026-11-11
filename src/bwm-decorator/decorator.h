// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
//
// bwm-decorator: anfitrión de decoraciones KDecoration3 fuera de KWin (fase 6a de
// docs/BREEZE_PLAN.md). Sigue el diseño de kwin v6.7.5: src/decorations/{decorationbridge,
// decoratedwindow,settings}.cpp y src/kcms/decoration/declarative-plugin/preview*.cpp.
#pragma once

#include "palette.h"
#include "protocol.h"

#include <KDecoration3/DecoratedWindow>
#include <KDecoration3/Decoration>
#include <KDecoration3/DecorationSettings>
#include <KDecoration3/Private/DecoratedWindowPrivate>
#include <KDecoration3/Private/DecorationBridge>
#include <KDecoration3/Private/DecorationSettingsPrivate>
#include <KConfigGroup>
#include <KSharedConfig>

#include <QFont>
#include <QIcon>
#include <QPointer>
#include <QRegion>
#include <QTimer>

#include <memory>

class KPluginFactory;

namespace BwmDeco
{

class Connection;
class Window;

struct WindowState {
    QSizeF size{400, 300};
    qreal scale = 1.0;
    uint32_t flags = Closeable | Maximizeable | Minimizeable | Moveable | Resizeable | Shadeable;
    uint32_t edges = 0;
    QString caption;
    QString appClass;
    QString iconName;
};

// kwinrc [org.kde.kdecoration2] como SettingsImpl de KWin
class Settings : public QObject, public KDecoration3::DecorationSettingsPrivateV2
{
    Q_OBJECT
public:
    explicit Settings(KDecoration3::DecorationSettings *parent);
    bool isOnAllDesktopsAvailable() const override { return true; }
    bool isAlphaChannelSupported() const override { return true; }
    bool isCloseOnDoubleClickOnMenu() const override { return m_closeDoubleClickMenu; }
    bool isAlwaysShowExcludeFromCapture() const override { return m_alwaysShowExcludeFromCapture; }
    QList<KDecoration3::DecorationButtonType> decorationButtonsLeft() const override { return m_leftButtons; }
    QList<KDecoration3::DecorationButtonType> decorationButtonsRight() const override { return m_rightButtons; }
    KDecoration3::BorderSize borderSize() const override { return m_borderSize; }
    QFont font() const override { return m_font; }
    QFontMetricsF fontMetrics() const override { return QFontMetricsF(m_font); }

    void readSettings(const QString &recommendedBorderSize);

private:
    QList<KDecoration3::DecorationButtonType> m_leftButtons;
    QList<KDecoration3::DecorationButtonType> m_rightButtons;
    KDecoration3::BorderSize m_borderSize = KDecoration3::BorderSize::Normal;
    bool m_closeDoubleClickMenu = false;
    bool m_alwaysShowExcludeFromCapture = false;
    QFont m_font;
};

class Bridge : public KDecoration3::DecorationBridge
{
    Q_OBJECT
public:
    Bridge();
    ~Bridge() override;

    std::unique_ptr<KDecoration3::DecoratedWindowPrivate> createClient(KDecoration3::DecoratedWindow *client, KDecoration3::Decoration *decoration) override;
    std::unique_ptr<KDecoration3::DecorationSettingsPrivate> settings(KDecoration3::DecorationSettings *parent) override;

    KDecoration3::Decoration *createDecoration(QObject *parent);
    void reconfigure();
    QString plugin() const { return m_plugin; }
    QString theme() const { return m_theme; }
    DecorationPalette *palette() const { return m_palette.get(); }
    QIcon iconFor(const QString &appClass, const QString &iconName);

Q_SIGNALS:
    // Plugin o tema distinto: hay que recrear todas las decoraciones
    void decorationsInvalidated();
    void paletteChanged();

private:
    bool initPlugin(const QString &pluginId);
    void readIconTheme();

    KSharedConfig::Ptr m_kwinrc;
    QString m_plugin;
    QString m_theme;
    QString m_recommendedBorderSize;
    KPluginFactory *m_factory = nullptr;
    std::shared_ptr<KDecoration3::DecorationSettings> m_settings;
    Settings *m_settingsImpl = nullptr;
    std::unique_ptr<DecorationPalette> m_palette;
    QHash<QString, QString> m_iconCache;
};

// Lo que la decoración ve de la ventana (DecoratedWindowImpl de KWin)
class ClientImpl : public KDecoration3::DecoratedWindowPrivateV4
{
public:
    ClientImpl(Window *window, KDecoration3::DecoratedWindow *client, KDecoration3::Decoration *decoration);

    bool isActive() const override;
    QString caption() const override;
    bool isOnAllDesktops() const override;
    bool isShaded() const override;
    QIcon icon() const override;
    bool isMaximized() const override { return isMaximizedHorizontally() && isMaximizedVertically(); }
    bool isMaximizedHorizontally() const override;
    bool isMaximizedVertically() const override;
    bool isKeepAbove() const override;
    bool isKeepBelow() const override;
    bool isCloseable() const override;
    bool isMaximizeable() const override;
    bool isMinimizeable() const override;
    bool providesContextHelp() const override;
    bool isModal() const override;
    bool isShadeable() const override;
    bool isMoveable() const override;
    bool isResizeable() const override;
    qreal width() const override;
    qreal height() const override;
    QSizeF size() const override;
    QPalette palette() const override;
    QColor color(KDecoration3::ColorGroup group, KDecoration3::ColorRole role) const override;
    Qt::Edges adjacentScreenEdges() const override;
    qreal scale() const override;
    qreal nextScale() const override;
    QString windowClass() const override;
    bool hasApplicationMenu() const override { return false; }
    bool isApplicationMenuActive() const override { return false; }
    QString applicationMenuServiceName() const override { return {}; }
    QString applicationMenuObjectPath() const override { return {}; }
    bool isExcludedFromCapture() const override;

    void requestShowToolTip(const QString &text) override;
    void requestHideToolTip() override;
    void requestClose() override;
    void requestToggleMaximization(Qt::MouseButtons buttons) override;
    void requestMinimize() override;
    void requestContextHelp() override;
    void requestToggleOnAllDesktops() override;
    void requestToggleShade() override;
    void requestToggleKeepAbove() override;
    void requestToggleKeepBelow() override;
    void requestShowWindowMenu(const QRect &rect) override;
    void requestToggleExcludeFromCapture() override;
    void showApplicationMenu(int actionId) override;
    void requestShowApplicationMenu(const QRect &rect, int actionId) override;
    void popup(const KDecoration3::Positioner &positioner, QMenu *menu) override;

private:
    Window *m_window;
};

// Una ventana decorada de un cliente: su decoración, sus búferes y sus mensajes
class Window : public QObject
{
    Q_OBJECT
public:
    Window(Connection *connection, uint32_t id, Bridge *bridge, const WindowState &state);
    ~Window() override;

    void setState(const WindowState &state);
    void pointer(uint32_t kind, QPointF pos, uint32_t button, uint32_t buttons, double angleDeltaY);
    void recreateDecoration();
    void request(uint32_t kind, uint32_t arg = 0, const QRectF &rect = {}, const QString &text = {});

    const WindowState &state() const { return m_state; }
    Bridge *bridge() const { return m_bridge; }
    QIcon icon() const { return m_icon; }

private:
    void commit();
    void scheduleRender(const QRegion &damage = QRegion());
    void render();
    void sendGeometry();
    void sendShadow();

    struct Buffer {
        int fd = -1;
        size_t size = 0;
        uchar *data = nullptr;
        bool sent = false;
    };
    bool ensureBuffer(Buffer &buffer, size_t size);
    static void releaseBuffer(Buffer &buffer);

    Connection *m_connection;
    uint32_t m_id;
    Bridge *m_bridge;
    WindowState m_state;
    QIcon m_icon;
    KDecoration3::Decoration *m_decoration = nullptr;
    Buffer m_buffers[2];
    int m_back = 0;
    uint32_t m_serial = 0;
    QRegion m_damage;
    QTimer m_renderTimer;
    bool m_hovered = false;
    QPointF m_lastPointer;
    const void *m_sentShadow = nullptr;
    qint64 m_sentShadowKey = 0;
    uint32_t m_shadowSerial = 0;
};

} // namespace BwmDeco

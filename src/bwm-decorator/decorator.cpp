// SPDX-FileCopyrightText: 2026 BWM
// SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org> (lógica de ajustes y del puente, kwin v6.7.5)
// SPDX-License-Identifier: GPL-2.0-or-later
#include "decorator.h"
#include "server.h"
#include "wire.h"

#include <KDecoration3/DecorationButton>
#include <KDecoration3/DecorationShadow>
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KService>

#include <QCoreApplication>
#include <QGuiApplication>
#include <QHoverEvent>
#include <QImage>
#include <QMouseEvent>
#include <QPainter>
#include <QWheelEvent>

#include <cmath>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

namespace BwmDeco
{

static const QString s_pluginName = QStringLiteral("org.kde.kdecoration3");
static const QString s_configGroup = QStringLiteral("org.kde.kdecoration2");
static const QString s_defaultPlugin = QStringLiteral("org.kde.breeze");
static const QString s_fallbackPlugin = QStringLiteral("org.kde.kwin.aurorae");

// ───────────────────────────────────────────────────────────── Settings (kwin settings.cpp)
static const QHash<QChar, KDecoration3::DecorationButtonType> &buttonNames()
{
    using T = KDecoration3::DecorationButtonType;
    static const QHash<QChar, T> names{
        {QChar('M'), T::Menu}, {QChar('N'), T::ApplicationMenu}, {QChar('S'), T::OnAllDesktops},
        {QChar('H'), T::ContextHelp}, {QChar('I'), T::Minimize}, {QChar('A'), T::Maximize},
        {QChar('X'), T::Close}, {QChar('F'), T::KeepAbove}, {QChar('B'), T::KeepBelow},
        {QChar('E'), T::ExcludeFromCapture}, {QChar('_'), T::Spacer},
    };
    return names;
}

static QList<KDecoration3::DecorationButtonType> buttonsFromString(const QString &buttons)
{
    QList<KDecoration3::DecorationButtonType> ret;
    for (const QChar c : buttons) {
        const auto it = buttonNames().constFind(c);
        if (it != buttonNames().constEnd())
            ret << it.value();
    }
    return ret;
}

static KDecoration3::BorderSize stringToSize(const QString &name)
{
    using B = KDecoration3::BorderSize;
    static const QMap<QString, B> sizes{{QStringLiteral("None"), B::None}, {QStringLiteral("NoSides"), B::NoSides},
                                        {QStringLiteral("Tiny"), B::Tiny}, {QStringLiteral("Normal"), B::Normal},
                                        {QStringLiteral("Large"), B::Large}, {QStringLiteral("VeryLarge"), B::VeryLarge},
                                        {QStringLiteral("Huge"), B::Huge}, {QStringLiteral("VeryHuge"), B::VeryHuge},
                                        {QStringLiteral("Oversized"), B::Oversized}};
    return sizes.value(name, B::Normal); // valores sin sentido = Normal, como KWin
}

// BWM: KWin usa QFontDatabase::systemFont(TitleFont), que con el tema de plataforma de KDE sale de
// kdeglobals [WM] activeFont. El auxiliar corre con la plataforma offscreen: se lee directamente.
static QFont titleFont()
{
    KSharedConfig::Ptr globals = KSharedConfig::openConfig(QStringLiteral("kdeglobals"));
    QFont font;
    const QString wm = globals->group(QStringLiteral("WM")).readEntry("activeFont");
    const QString general = globals->group(QStringLiteral("General")).readEntry("font");
    const QString spec = wm.isEmpty() ? general : wm;
    if (spec.isEmpty() || !font.fromString(spec))
        font = QFont(QStringLiteral("Noto Sans"), 10);
    return font;
}

Settings::Settings(KDecoration3::DecorationSettings *parent)
    : QObject()
    , DecorationSettingsPrivateV2(parent)
{
}

void Settings::readSettings(const QString &recommendedBorderSize)
{
    using T = KDecoration3::DecorationButtonType;
    KSharedConfig::Ptr kwinrc = KSharedConfig::openConfig(QStringLiteral("kwinrc"));
    kwinrc->reparseConfiguration();
    const KConfigGroup config = kwinrc->group(s_configGroup);

    const auto left = buttonsFromString(config.readEntry("ButtonsOnLeft", QStringLiteral("MSE")));
    if (left != m_leftButtons) {
        m_leftButtons = left;
        Q_EMIT decorationSettings()->decorationButtonsLeftChanged(m_leftButtons);
    }
    const auto right = buttonsFromString(config.readEntry("ButtonsOnRight", QStringLiteral("HIAX")));
    if (right != m_rightButtons) {
        m_rightButtons = right;
        Q_EMIT decorationSettings()->decorationButtonsRightChanged(m_rightButtons);
    }
    Q_UNUSED(T::Menu);
    const bool close = config.readEntry("CloseOnDoubleClickOnMenu", false);
    if (close != m_closeDoubleClickMenu) {
        m_closeDoubleClickMenu = close;
        Q_EMIT decorationSettings()->closeOnDoubleClickOnMenuChanged(m_closeDoubleClickMenu);
    }
    const bool exclude = config.readEntry("AlwaysShowExcludeFromCapture", false);
    if (exclude != m_alwaysShowExcludeFromCapture) {
        m_alwaysShowExcludeFromCapture = exclude;
        Q_EMIT decorationSettings()->alwaysShowExcludeFromCaptureChanged(m_alwaysShowExcludeFromCapture);
    }
    auto size = stringToSize(config.readEntry("BorderSize", QStringLiteral("Normal")));
    if (config.readEntry("BorderSizeAuto", true))
        size = stringToSize(recommendedBorderSize);
    if (size != m_borderSize) {
        m_borderSize = size;
        Q_EMIT decorationSettings()->borderSizeChanged(m_borderSize);
    }
    const QFont font = titleFont();
    if (font != m_font) {
        m_font = font;
        Q_EMIT decorationSettings()->fontChanged(m_font);
    }
    Q_EMIT decorationSettings()->reconfigured();
}

// ───────────────────────────────────────────────────────────── Bridge (kwin decorationbridge.cpp)
Bridge::Bridge()
    : KDecoration3::DecorationBridge()
    , m_kwinrc(KSharedConfig::openConfig(QStringLiteral("kwinrc")))
    , m_palette(std::make_unique<DecorationPalette>(QStringLiteral("kdeglobals")))
{
    connect(m_palette.get(), &DecorationPalette::changed, this, &Bridge::paletteChanged);
    readIconTheme();
    m_settings = std::make_shared<KDecoration3::DecorationSettings>(this);
    const KConfigGroup config = m_kwinrc->group(s_configGroup);
    const QString pluginId = config.readEntry("library", s_defaultPlugin);
    if (!initPlugin(pluginId) && pluginId != s_defaultPlugin && !initPlugin(s_defaultPlugin))
        initPlugin(s_fallbackPlugin);
    if (m_settingsImpl)
        m_settingsImpl->readSettings(m_recommendedBorderSize);
}

Bridge::~Bridge() = default;

bool Bridge::initPlugin(const QString &pluginIdIn)
{
    QString pluginId = pluginIdIn;
    const QString theme = m_kwinrc->group(s_configGroup).readEntry("theme", QString());
    // Como migrateAuroraeTheme() de KWin: los temas SVG van con el motor Aurorae v2
    if (pluginId == QLatin1String("org.kde.kwin.aurorae") && theme.startsWith(QLatin1String("__aurorae__svg__")))
        pluginId = QStringLiteral("org.kde.kwin.aurorae.v2");
    const KPluginMetaData metaData = KPluginMetaData::findPluginById(s_pluginName, pluginId);
    if (!metaData.isValid()) {
        qWarning("bwm-decorator: no se encuentra el plugin de decoración %s", qPrintable(pluginId));
        return false;
    }
    auto result = KPluginFactory::loadFactory(metaData);
    if (!result) {
        qWarning("bwm-decorator: error al cargar %s: %s", qPrintable(pluginId), qPrintable(result.errorText));
        return false;
    }
    m_factory = result.plugin;
    m_plugin = pluginIdIn;
    m_recommendedBorderSize.clear();
    m_theme.clear();
    const QVariantMap deco = metaData.rawData().value(s_pluginName).toObject().toVariantMap();
    m_recommendedBorderSize = deco.value(QStringLiteral("recommendedBorderSize")).toString();
    if (deco.value(QStringLiteral("themes")).toBool())
        m_theme = m_kwinrc->group(s_configGroup).readEntry("theme", deco.value(QStringLiteral("defaultTheme")).toString());
    return true;
}

std::unique_ptr<KDecoration3::DecoratedWindowPrivate> Bridge::createClient(KDecoration3::DecoratedWindow *client, KDecoration3::Decoration *decoration)
{
    return std::make_unique<ClientImpl>(static_cast<Window *>(decoration->parent()), client, decoration);
}

std::unique_ptr<KDecoration3::DecorationSettingsPrivate> Bridge::settings(KDecoration3::DecorationSettings *parent)
{
    auto settings = std::make_unique<Settings>(parent);
    m_settingsImpl = settings.get();
    return settings;
}

KDecoration3::Decoration *Bridge::createDecoration(QObject *parent)
{
    if (!m_factory)
        return nullptr;
    QVariantMap args({{QStringLiteral("bridge"), QVariant::fromValue(this)}});
    if (!m_theme.isEmpty())
        args.insert(QStringLiteral("theme"), m_theme);
    auto deco = m_factory->create<KDecoration3::Decoration>(parent, QVariantList{args});
    if (!deco)
        return nullptr;
    deco->setSettings(m_settings);
    deco->create();
    deco->init();
    return deco;
}

void Bridge::reconfigure()
{
    m_kwinrc->reparseConfiguration();
    const KConfigGroup config = m_kwinrc->group(s_configGroup);
    const QString plugin = config.readEntry("library", s_defaultPlugin);
    const QString oldTheme = m_theme;
    const QString oldPlugin = m_plugin;
    if (plugin != m_plugin) {
        initPlugin(plugin);
    } else if (!m_theme.isEmpty() || plugin.startsWith(QLatin1String("org.kde.kwin.aurorae"))) {
        m_theme = config.readEntry("theme", m_theme);
    }
    // La paleta portada de KWin lee la configuración principal del proceso (que en cascada incluye
    // kdeglobals) y en KWin la relee su KConfigWatcher; aquí también puede cambiar sólo el archivo
    KSharedConfig::openConfig()->reparseConfiguration();
    m_palette->update();
    readIconTheme();
    if (m_settingsImpl)
        m_settingsImpl->readSettings(m_recommendedBorderSize);
    if (m_plugin != oldPlugin || m_theme != oldTheme)
        Q_EMIT decorationsInvalidated();
}

void Bridge::readIconTheme()
{
    KSharedConfig::Ptr globals = KSharedConfig::openConfig(QStringLiteral("kdeglobals"));
    globals->reparseConfiguration();
    const QString theme = globals->group(QStringLiteral("Icons")).readEntry("Theme", QStringLiteral("breeze"));
    if (QIcon::themeName() != theme) {
        QIcon::setThemeName(theme);
        m_iconCache.clear();
    }
    QIcon::setFallbackThemeName(QStringLiteral("hicolor"));
}

// BWM: icono de la ventana como lo busca Breeze: el .desktop por id (la clase de Wayland suele ser
// el id) y, si no, el que declara StartupWMClass
QIcon Bridge::iconFor(const QString &appClass, const QString &iconName)
{
    if (!iconName.isEmpty())
        return QIcon::fromTheme(iconName);
    if (appClass.isEmpty())
        return QIcon::fromTheme(QStringLiteral("application-x-executable"));
    auto cached = m_iconCache.constFind(appClass);
    if (cached == m_iconCache.constEnd()) {
        QString icon;
        KService::Ptr service = KService::serviceByDesktopName(appClass);
        if (!service)
            service = KService::serviceByDesktopName(appClass.toLower());
        if (!service) {
            const auto all = KService::allServices();
            for (const auto &s : all) {
                if (s->property<QString>(QStringLiteral("StartupWMClass")).compare(appClass, Qt::CaseInsensitive) == 0) {
                    service = s;
                    break;
                }
            }
        }
        icon = service ? service->icon() : appClass.toLower();
        cached = m_iconCache.insert(appClass, icon);
    }
    QIcon result = QIcon::fromTheme(cached.value());
    return result.isNull() ? QIcon::fromTheme(QStringLiteral("application-x-executable")) : result;
}

// ───────────────────────────────────────────────────────────── ClientImpl (kwin decoratedwindow.cpp)
ClientImpl::ClientImpl(Window *window, KDecoration3::DecoratedWindow *client, KDecoration3::Decoration *decoration)
    : DecoratedWindowPrivateV4(client, decoration)
    , m_window(window)
{
}

#define FLAG(name, bit) bool ClientImpl::name() const { return m_window->state().flags & (bit); }
FLAG(isActive, Active)
FLAG(isOnAllDesktops, OnAllDesktops)
FLAG(isShaded, Shaded)
FLAG(isMaximizedHorizontally, MaximizedHorizontally)
FLAG(isMaximizedVertically, MaximizedVertically)
FLAG(isKeepAbove, KeepAbove)
FLAG(isKeepBelow, KeepBelow)
FLAG(isCloseable, Closeable)
FLAG(isMaximizeable, Maximizeable)
FLAG(isMinimizeable, Minimizeable)
FLAG(providesContextHelp, ProvidesContextHelp)
FLAG(isModal, Modal)
FLAG(isShadeable, Shadeable)
FLAG(isMoveable, Moveable)
FLAG(isResizeable, Resizeable)
FLAG(isExcludedFromCapture, ExcludedFromCapture)
#undef FLAG

QString ClientImpl::caption() const { return m_window->state().caption; }
QIcon ClientImpl::icon() const { return m_window->icon(); }
qreal ClientImpl::width() const { return m_window->state().size.width(); }
qreal ClientImpl::height() const { return m_window->state().size.height(); }
QSizeF ClientImpl::size() const { return m_window->state().size; }
QPalette ClientImpl::palette() const { return m_window->bridge()->palette()->palette(); }
QColor ClientImpl::color(KDecoration3::ColorGroup group, KDecoration3::ColorRole role) const
{
    return m_window->bridge()->palette()->color(group, role);
}
Qt::Edges ClientImpl::adjacentScreenEdges() const { return Qt::Edges(int(m_window->state().edges)); }
qreal ClientImpl::scale() const { return m_window->state().scale; }
qreal ClientImpl::nextScale() const { return m_window->state().scale; }
QString ClientImpl::windowClass() const { return m_window->state().appClass; }

void ClientImpl::requestShowToolTip(const QString &text) { m_window->request(ShowToolTip, 0, {}, text); }
void ClientImpl::requestHideToolTip() { m_window->request(HideToolTip); }
void ClientImpl::requestClose() { m_window->request(Close); }
void ClientImpl::requestToggleMaximization(Qt::MouseButtons buttons) { m_window->request(ToggleMaximization, uint32_t(buttons.toInt())); }
void ClientImpl::requestMinimize() { m_window->request(Minimize); }
void ClientImpl::requestContextHelp() { m_window->request(ContextHelp); }
void ClientImpl::requestToggleOnAllDesktops() { m_window->request(ToggleOnAllDesktops); }
void ClientImpl::requestToggleShade() { m_window->request(ToggleShade); }
void ClientImpl::requestToggleKeepAbove() { m_window->request(ToggleKeepAbove); }
void ClientImpl::requestToggleKeepBelow() { m_window->request(ToggleKeepBelow); }
void ClientImpl::requestShowWindowMenu(const QRect &rect) { m_window->request(ShowWindowMenu, 0, rect); }
void ClientImpl::requestToggleExcludeFromCapture() { m_window->request(ToggleExcludeFromCapture); }
void ClientImpl::showApplicationMenu(int actionId) { m_window->request(ShowApplicationMenu, uint32_t(actionId)); }
void ClientImpl::requestShowApplicationMenu(const QRect &rect, int actionId) { m_window->request(ShowApplicationMenu, uint32_t(actionId), rect); }
// Menús propios de la decoración (QMenu): no hay ventana de Qt que los muestre en este proceso
void ClientImpl::popup(const KDecoration3::Positioner &, QMenu *) {}

// ───────────────────────────────────────────────────────────── Window
Window::Window(Connection *connection, uint32_t id, Bridge *bridge, const WindowState &state)
    : m_connection(connection)
    , m_id(id)
    , m_bridge(bridge)
    , m_state(state)
{
    m_icon = m_bridge->iconFor(m_state.appClass, m_state.iconName);
    m_renderTimer.setSingleShot(true);
    m_renderTimer.setInterval(0);
    connect(&m_renderTimer, &QTimer::timeout, this, &Window::render);
    connect(m_bridge, &Bridge::paletteChanged, this, [this] {
        if (m_decoration)
            Q_EMIT m_decoration->window()->paletteChanged(m_bridge->palette()->palette());
        scheduleRender();
    });
    recreateDecoration();
}

Window::~Window()
{
    delete m_decoration;
    releaseBuffer(m_buffers[0]);
    releaseBuffer(m_buffers[1]);
}

void Window::recreateDecoration()
{
    delete m_decoration;
    m_decoration = m_bridge->createDecoration(this);
    m_sentShadow = nullptr;
    if (!m_decoration) {
        m_connection->send(Writer(Error, m_id).str(QStringLiteral("no decoration plugin")).finish());
        return;
    }
    connect(m_decoration, &KDecoration3::Decoration::damaged, this, [this](const QRegion &r) { scheduleRender(r); });
    connect(m_decoration, &KDecoration3::Decoration::nextStateChanged, this, [this] { commit(); });
    connect(m_decoration, &KDecoration3::Decoration::shadowChanged, this, [this] { scheduleRender(); });
    connect(m_decoration, &KDecoration3::Decoration::sectionUnderMouseChanged, this, [this](Qt::WindowFrameSection section) {
        m_connection->send(Writer(SectionUnderMouse, m_id).u32(uint32_t(section)).finish());
    });
    commit();
}

// Doble búfer de estado de KDecoration3: el anfitrión confirma el estado siguiente (bordes,
// radios…). Sin esto los bordes valen 0 (prueba d de la fase 0).
void Window::commit()
{
    if (!m_decoration)
        return;
    m_decoration->apply(m_decoration->nextState()->clone());
    sendGeometry();
    scheduleRender();
}

void Window::setState(const WindowState &state)
{
    const WindowState old = m_state;
    m_state = state;
    auto *w = m_decoration ? m_decoration->window() : nullptr;
    if (state.appClass != old.appClass || state.iconName != old.iconName) {
        m_icon = m_bridge->iconFor(state.appClass, state.iconName);
        if (w)
            Q_EMIT w->iconChanged(m_icon);
    }
    if (w) {
        const uint32_t changed = state.flags ^ old.flags;
        if (changed & Active)
            Q_EMIT w->activeChanged(state.flags & Active);
        if (changed & (MaximizedHorizontally | MaximizedVertically)) {
            Q_EMIT w->maximizedHorizontallyChanged(state.flags & MaximizedHorizontally);
            Q_EMIT w->maximizedVerticallyChanged(state.flags & MaximizedVertically);
            Q_EMIT w->maximizedChanged((state.flags & MaximizedHorizontally) && (state.flags & MaximizedVertically));
        }
        if (changed & OnAllDesktops)
            Q_EMIT w->onAllDesktopsChanged(state.flags & OnAllDesktops);
        if (changed & KeepAbove)
            Q_EMIT w->keepAboveChanged(state.flags & KeepAbove);
        if (changed & KeepBelow)
            Q_EMIT w->keepBelowChanged(state.flags & KeepBelow);
        if (changed & Shaded)
            Q_EMIT w->shadedChanged(state.flags & Shaded);
        if (changed & Closeable)
            Q_EMIT w->closeableChanged(state.flags & Closeable);
        if (changed & Maximizeable)
            Q_EMIT w->maximizeableChanged(state.flags & Maximizeable);
        if (changed & Minimizeable)
            Q_EMIT w->minimizeableChanged(state.flags & Minimizeable);
        if (changed & ProvidesContextHelp)
            Q_EMIT w->providesContextHelpChanged(state.flags & ProvidesContextHelp);
        if (changed & Shadeable)
            Q_EMIT w->shadeableChanged(state.flags & Shadeable);
        if (changed & Moveable)
            Q_EMIT w->moveableChanged(state.flags & Moveable);
        if (changed & Resizeable)
            Q_EMIT w->resizeableChanged(state.flags & Resizeable);
        if (changed & ExcludedFromCapture)
            Q_EMIT w->excludeFromCaptureChanged(state.flags & ExcludedFromCapture);
        if (state.caption != old.caption)
            Q_EMIT w->captionChanged(state.caption);
        if (state.edges != old.edges)
            Q_EMIT w->adjacentScreenEdgesChanged(Qt::Edges(int(state.edges)));
        if (state.size.width() != old.size.width())
            Q_EMIT w->widthChanged(state.size.width());
        if (state.size.height() != old.size.height())
            Q_EMIT w->heightChanged(state.size.height());
        if (state.size != old.size)
            Q_EMIT w->sizeChanged(state.size);
        if (!qFuzzyCompare(state.scale, old.scale)) {
            Q_EMIT w->nextScaleChanged();
            Q_EMIT w->scaleChanged();
        }
    }
    commit();
}

void Window::pointer(uint32_t kind, QPointF pos, uint32_t button, uint32_t buttons, double angleDeltaY)
{
    if (!m_decoration)
        return;
    const auto mods = Qt::NoModifier;
    switch (kind) {
    case Motion: {
        if (!m_hovered) {
            QHoverEvent enter(QEvent::HoverEnter, pos, pos, QPointF(-1, -1), mods);
            QCoreApplication::sendEvent(m_decoration, &enter);
            m_hovered = true;
        }
        QHoverEvent move(QEvent::HoverMove, pos, pos, m_lastPointer, mods);
        QCoreApplication::sendEvent(m_decoration, &move);
        m_lastPointer = pos;
        break;
    }
    case Leave: {
        QHoverEvent leave(QEvent::HoverLeave, QPointF(-1, -1), QPointF(-1, -1), m_lastPointer, mods);
        QCoreApplication::sendEvent(m_decoration, &leave);
        m_hovered = false;
        break;
    }
    case Press:
    case Release: {
        QMouseEvent event(kind == Press ? QEvent::MouseButtonPress : QEvent::MouseButtonRelease, pos, pos, pos,
                          Qt::MouseButton(button), Qt::MouseButtons(int(buttons)), mods);
        QCoreApplication::sendEvent(m_decoration, &event);
        break;
    }
    case Wheel: {
        QWheelEvent event(pos, pos, QPoint(), QPoint(0, int(angleDeltaY)), Qt::MouseButtons(int(buttons)), mods,
                          Qt::NoScrollPhase, false);
        QCoreApplication::sendEvent(m_decoration, &event);
        break;
    }
    default:
        break;
    }
}

void Window::request(uint32_t kind, uint32_t arg, const QRectF &rect, const QString &text)
{
    m_connection->send(Writer(Request, m_id).u32(kind).u32(arg).rect(rect).str(text).finish());
}

void Window::scheduleRender(const QRegion &damage)
{
    m_damage += damage.isEmpty() && m_decoration ? QRegion(m_decoration->rect().toAlignedRect()) : damage;
    if (!m_renderTimer.isActive())
        m_renderTimer.start();
}

void Window::sendGeometry()
{
    const QMarginsF b = m_decoration->borders();
    const QMarginsF r = m_decoration->resizeOnlyBorders();
    const KDecoration3::BorderRadius radius = m_decoration->borderRadius();
    const KDecoration3::BorderOutline outline = m_decoration->borderOutline();
    Writer msg(Geometry, m_id);
    msg.f64(b.left()).f64(b.top()).f64(b.right()).f64(b.bottom());
    msg.f64(r.left()).f64(r.top()).f64(r.right()).f64(r.bottom());
    msg.f64(radius.topLeft()).f64(radius.topRight()).f64(radius.bottomRight()).f64(radius.bottomLeft());
    msg.rect(m_decoration->titleBar());
    msg.u32(m_decoration->isOpaque() ? 1 : 0);
    msg.f64(outline.thickness()).u32(outline.color().rgba());
    m_connection->send(msg.finish());
}

bool Window::ensureBuffer(Buffer &buffer, size_t size)
{
    if (buffer.fd >= 0 && buffer.size >= size)
        return true;
    releaseBuffer(buffer);
    buffer.fd = memfd_create("bwm-decorator", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (buffer.fd < 0)
        return false;
    // Algo de margen para no reasignar en cada píxel de un redimensionado
    const size_t capacity = size + size / 4;
    if (ftruncate(buffer.fd, off_t(capacity)) != 0) {
        releaseBuffer(buffer);
        return false;
    }
    void *data = mmap(nullptr, capacity, PROT_READ | PROT_WRITE, MAP_SHARED, buffer.fd, 0);
    if (data == MAP_FAILED) {
        releaseBuffer(buffer);
        return false;
    }
    buffer.data = static_cast<uchar *>(data);
    buffer.size = capacity;
    buffer.sent = false;
    return true;
}

void Window::releaseBuffer(Buffer &buffer)
{
    if (buffer.data)
        munmap(buffer.data, buffer.size);
    if (buffer.fd >= 0)
        close(buffer.fd);
    buffer = Buffer{};
}

// Las cuatro piezas del marco (como DecorationItem de KWin), cada una a la escala de su monitor,
// empaquetadas en un búfer: arriba, abajo, y debajo izquierda y derecha juntas.
void Window::render()
{
    if (!m_decoration)
        return;
    sendShadow();

    const qreal s = m_state.scale;
    const QRectF rect = m_decoration->rect();
    const QMarginsF b = m_decoration->borders();
    const QRectF parts[4] = {
        QRectF(0, 0, rect.width(), b.top()),
        QRectF(0, rect.height() - b.bottom(), rect.width(), b.bottom()),
        QRectF(0, b.top(), b.left(), rect.height() - b.top() - b.bottom()),
        QRectF(rect.width() - b.right(), b.top(), b.right(), rect.height() - b.top() - b.bottom()),
    };
    auto px = [s](qreal v) { return int(std::ceil(std::max<qreal>(0, v) * s)); };
    const int topW = px(parts[0].width()), topH = px(parts[0].height());
    const int botW = px(parts[1].width()), botH = px(parts[1].height());
    const int leftW = px(parts[2].width()), rightW = px(parts[3].width()), sideH = px(parts[2].height());
    const QRect dest[4] = {
        QRect(0, 0, topW, topH),
        QRect(0, topH, botW, botH),
        QRect(0, topH + botH, leftW, sideH),
        QRect(leftW, topH + botH, rightW, sideH),
    };
    const int width = std::max({topW, botW, leftW + rightW, 1});
    const int height = std::max(topH + botH + sideH, 1);
    const int stride = width * 4;

    Buffer &buffer = m_buffers[m_back];
    if (!ensureBuffer(buffer, size_t(stride) * size_t(height))) {
        m_connection->send(Writer(Error, m_id).str(QStringLiteral("memfd")).finish());
        return;
    }
    QImage image(buffer.data, width, height, stride, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    {
        QPainter painter(&image);
        painter.setRenderHint(QPainter::Antialiasing);
        for (int i = 0; i < 4; ++i) {
            if (dest[i].isEmpty())
                continue;
            painter.save();
            painter.setClipRect(dest[i]);
            painter.translate(dest[i].topLeft());
            painter.scale(s, s);
            painter.translate(-parts[i].topLeft());
            m_decoration->paint(&painter, parts[i]);
            painter.restore();
        }
    }

    Writer msg(Frame, m_id);
    const bool sendFd = !buffer.sent;
    msg.u32(++m_serial).u32(uint32_t(m_back)).u32(sendFd ? 1 : 0).f64(s);
    msg.u32(uint32_t(width)).u32(uint32_t(height)).u32(uint32_t(stride)).u32(uint32_t(buffer.size));
    for (int i = 0; i < 4; ++i)
        msg.u32(uint32_t(dest[i].x())).u32(uint32_t(dest[i].y())).u32(uint32_t(dest[i].width())).u32(uint32_t(dest[i].height())).rect(parts[i]);
    const QRegion damage = m_damage.isEmpty() ? QRegion(rect.toAlignedRect()) : m_damage;
    msg.u32(uint32_t(damage.rectCount()));
    for (const QRect &r : damage)
        msg.rect(r);
    m_damage = QRegion();
    if (m_connection->send(msg.finish(), sendFd ? buffer.fd : -1))
        buffer.sent = true;
    m_back ^= 1;
}

// La sombra va aparte, una vez por cada sombra distinta (suele ser la misma para todo el tema)
void Window::sendShadow()
{
    const auto shadow = m_decoration->shadow();
    if (!shadow) {
        if (m_sentShadow) {
            m_connection->send(Writer(Shadow, m_id).u32(++m_shadowSerial).u32(0).u32(0).u32(0).u32(0).f64(1)
                                   .f64(0).f64(0).f64(0).f64(0).rect({}).finish());
            m_sentShadow = nullptr;
        }
        return;
    }
    const QImage source = shadow->shadow();
    if (m_sentShadow == shadow.get() && m_sentShadowKey == source.cacheKey())
        return;
    const QImage image = source.convertToFormat(QImage::Format_ARGB32_Premultiplied);
    const size_t size = size_t(image.sizeInBytes());
    const int fd = memfd_create("bwm-decorator-shadow", MFD_CLOEXEC);
    if (fd < 0 || ftruncate(fd, off_t(std::max<size_t>(size, 1))) != 0) {
        if (fd >= 0)
            close(fd);
        return;
    }
    if (size) {
        void *data = mmap(nullptr, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        if (data != MAP_FAILED) {
            memcpy(data, image.constBits(), size);
            munmap(data, size);
        }
    }
    const QMarginsF padding = shadow->padding();
    Writer msg(Shadow, m_id);
    msg.u32(++m_shadowSerial).u32(1).u32(uint32_t(image.width())).u32(uint32_t(image.height())).u32(uint32_t(image.bytesPerLine()));
    msg.f64(image.devicePixelRatio());
    msg.f64(padding.left()).f64(padding.top()).f64(padding.right()).f64(padding.bottom());
    msg.rect(shadow->innerShadowRect());
    m_connection->send(msg.finish(), fd);
    close(fd);
    m_sentShadow = shadow.get();
    m_sentShadowKey = source.cacheKey();
}

} // namespace BwmDeco

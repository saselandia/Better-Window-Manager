/*
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/panelconfigview.cpp (see the header).
*/
#include "panelconfigview.h"
#include "panelsession.h"
#include "panelviewhost.h"
#include "surfaces.h"
#include "viewcorona.h"

#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <LayerShellQt/Window>
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <QAction>
#include <QGuiApplication>
#include <QKeyEvent>
#include <QPlatformSurfaceEvent>
#include <PlasmaQuick/Dialog>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickItem>
#include <QScreen>
#include <algorithm>
#include <cmath>

using namespace Qt::StringLiterals;

PanelRulerView::PanelRulerView(Plasma::Containment *containment, PanelViewHost *panelView, PanelConfigView *mainConfigView)
    : PlasmaWindow()
    , m_containment(containment)
    , m_panelView(panelView)
    , m_mainConfigView(mainConfigView)
{
    m_layerWindow = LayerShellQt::Window::get(this);
    m_layerWindow->setLayer(LayerShellQt::Window::LayerTop);
    // Ruler.qml is pointer-only; keeping KeyboardInteractivityNone + activateOnShow(false)
    // prevents the ruler from stealing keyboard focus (e.g. Escape) from PanelConfigView.
    m_layerWindow->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);
    m_layerWindow->setActivateOnShow(false);
    m_layerWindow->setScope(QStringLiteral("dock"));
    m_layerWindow->setCloseOnDismissed(false);
    m_layerWindow->setScreen(m_panelView->screen());
    setScreen(m_panelView->screen());
    connect(this, &PanelRulerView::mainItemChanged, this, &PanelRulerView::syncPanelLocation);
}

PanelRulerView::~PanelRulerView() = default;

void PanelRulerView::syncPanelLocation()
{
    if (!mainItem() || !m_containment->corona()) {
        return;
    }
    const int screenId = m_containment->screen();
    if (screenId == -1) {
        return;
    }
    const QRect available = m_containment->corona()->availableScreenRect(screenId);

    switch (m_containment->location()) {
    case Plasma::Types::TopEdge:
        setBorders(Qt::BottomEdge);
        break;
    case Plasma::Types::LeftEdge:
        setBorders(Qt::RightEdge);
        break;
    case Plasma::Types::RightEdge:
        setBorders(Qt::LeftEdge);
        break;
    case Plasma::Types::BottomEdge:
    default:
        setBorders(Qt::TopEdge);
    }

    switch (m_containment->location()) {
    case Plasma::Types::LeftEdge:
    case Plasma::Types::RightEdge:
        m_layerWindow->setDesiredSize(QSize(mainItem()->implicitWidth(), available.height()));
        break;
    case Plasma::Types::TopEdge:
    case Plasma::Types::BottomEdge:
    default:
        m_layerWindow->setDesiredSize(QSize(available.width(), mainItem()->implicitHeight()));
        break;
    }

    m_layerWindow->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);
    m_layerWindow->setActivateOnShow(false);
    LayerShellQt::Window::Anchors anchors;
    switch (m_containment->location()) {
    case Plasma::Types::TopEdge:
        anchors.setFlag(LayerShellQt::Window::AnchorTop);
        break;
    case Plasma::Types::LeftEdge:
        anchors.setFlag(LayerShellQt::Window::AnchorLeft);
        break;
    case Plasma::Types::RightEdge:
        anchors.setFlag(LayerShellQt::Window::AnchorRight);
        break;
    case Plasma::Types::BottomEdge:
    default:
        anchors.setFlag(LayerShellQt::Window::AnchorBottom);
        break;
    }

    const bool horizontal = m_containment->formFactor() == Plasma::Types::Horizontal;
    switch (m_panelView->alignment()) {
    case Qt::AlignLeft:
        anchors.setFlag(horizontal ? LayerShellQt::Window::AnchorLeft : LayerShellQt::Window::AnchorTop);
        break;
    case Qt::AlignRight:
        anchors.setFlag(horizontal ? LayerShellQt::Window::AnchorRight : LayerShellQt::Window::AnchorBottom);
        break;
    default:
        break;
    }
    m_layerWindow->setAnchors(anchors);
    requestUpdate();
}

void PanelRulerView::showEvent(QShowEvent *ev)
{
    syncPanelLocation();
    PlasmaWindow::showEvent(ev);
}

//////////////////////////////PanelConfigView
PanelConfigView::PanelConfigView(Plasma::Containment *containment, PanelViewHost *panelView)
    : PlasmaQuick::PopupPlasmaWindow()
    , m_containment(containment)
    , m_panelView(panelView)
    , m_sharedQmlEngine(std::make_unique<PlasmaQuick::SharedQmlEngine>(this))
{
    connect(panelView, &QObject::destroyed, this, &QObject::deleteLater);
    setScreen(panelView->screen());

    m_sharedQmlEngine->setTranslationDomain(QStringLiteral("plasma_shell_org.kde.plasma.desktop"));
    m_sharedQmlEngine->rootContext()->setContextProperties({
        QQmlContext::PropertyPair{u"plasmoid"_s, QVariant::fromValue(containment)},
        QQmlContext::PropertyPair{u"panel"_s, QVariant::fromValue(panelView)},
        QQmlContext::PropertyPair{u"configDialog"_s, QVariant::fromValue(this)},
    });
    connect(containment, &Plasma::Containment::destroyedChanged, this, &QObject::deleteLater);
    if (containment->corona()) {
        connect(containment->corona(), &Plasma::Corona::editModeChanged, this, [this](bool edit) {
            if (!edit) {
                hide();
            }
        });
    }
    // BWM: the layer-shell role and position come from the panel surface, as for
    // the packages' own popups; Qt's xdg placement would open a free window.
    m_anchor = new PopupAnchor(this);
    m_anchor->setObjectName(QStringLiteral("bwmPanelConfigAnchor"));
    m_anchor->setIndependentWindow(true);
    m_anchor->setVisualParent(panelView->rootObject());
    m_anchor->setPopup(this);
    connect(panelView, &PanelViewHost::geometryPolicyChanged, m_anchor, [this] {
        if (m_panelRulerView) m_panelRulerView->syncPanelLocation();
    });
    connect(panelView, &PanelViewHost::placementChanged, m_anchor, [this] {
        if (m_panelRulerView) m_panelRulerView->syncPanelLocation();
    });
    connect(containment, &Plasma::Containment::locationChanged, m_anchor, [this] {
        if (m_panelRulerView) m_panelRulerView->syncPanelLocation();
    });
    qApp->installEventFilter(this);
    setMargin(4);
}

PanelConfigView::~PanelConfigView()
{
    if (m_panelView) {
        m_panelView->setUserConfiguring(false);
    }
}

bool PanelConfigView::init()
{
    const auto shell = KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral("org.kde.plasma.desktop"));
    const QUrl source = shell.fileUrl("panelconfigurationui");
    if (!shell.isValid() || source.isEmpty()) {
        m_error = tr("The installed KDE Plasma shell PanelConfiguration.qml is missing.");
        return false;
    }
    m_sharedQmlEngine->setInitializationDelayed(true);
    m_sharedQmlEngine->setSource(source);
    m_sharedQmlEngine->completeInitialization({{QStringLiteral("panelConfiguration"), QVariant::fromValue(this)}});
    setMainItem(qobject_cast<QQuickItem *>(m_sharedQmlEngine->rootObject()));
    if (!mainItem()) {
        QStringList messages;
        for (const auto &e : m_sharedQmlEngine->mainComponent() ? m_sharedQmlEngine->mainComponent()->errors() : QList<QQmlError>())
            messages.append(e.toString());
        m_error = messages.isEmpty() ? tr("The native panel settings did not load.") : messages.join(u'\n');
        return false;
    }
    if (m_panelRulerView) {
        m_panelRulerView->setMainItem(mainItem()->property("panelRuler").value<QQuickItem *>());
        m_panelRulerView->syncPanelLocation();
    }
    auto syncSize = [this] {
        resize(mainItem()->implicitWidth() + leftPadding() + rightPadding(), mainItem()->implicitHeight() + topPadding() + bottomPadding());
    };
    connect(mainItem(), &QQuickItem::implicitWidthChanged, this, syncSize);
    connect(mainItem(), &QQuickItem::implicitHeightChanged, this, syncSize);
    syncSize();
    mainItem()->setVisible(true);
    return true;
}

void PanelConfigView::showAddWidgetDialog()
{
    if (QAction *addWidgetAction = m_containment->internalAction(QStringLiteral("add widgets"))) {
        addWidgetAction->trigger();
    }
}

void PanelConfigView::addWidget(const QString &plugin, bool atStart)
{
    // Like the shell script engine's panel.addWidget(): the spacer and margins
    // separator are internal widgets that the catalog hides (NoDisplay).
    auto *session = m_panelView ? m_panelView->panelSession() : nullptr;
    if (!session || m_containment->immutable()) {
        return;
    }
    auto *applet = m_containment->createApplet(plugin);
    if (!applet || applet->failedToLaunch()) {
        if (applet) applet->destroy();
        return;
    }
    const uint id = applet->id();
    if (!atStart) {
        return;
    }
    QVariantList order = session->order();
    order.removeAll(QVariant(id));
    order.prepend(id);
    session->requestOrder(order);
}

void PanelConfigView::addPanelSpacer()
{
    // Upstream script: a single existing spacer makes the new one go first, which
    // triggers the spacer centering mode; otherwise the spacer is appended.
    int spacers = 0;
    for (auto *applet : m_containment->applets())
        if (applet->pluginMetaData().pluginId() == QStringLiteral("org.kde.plasma.panelspacer")) ++spacers;
    addWidget(QStringLiteral("org.kde.plasma.panelspacer"), spacers == 1);
}

void PanelConfigView::addPanelMarginsSeparator()
{
    addWidget(QStringLiteral("org.kde.plasma.marginsseparator"), false);
}

bool PanelConfigView::eventFilter(QObject *object, QEvent *event)
{
    // SurfaceCreated precedes Qt's shell-role selection (Qt 6.11.2), the boundary at
    // which LayerShellQt's public API can still assign the layer role (as R4 does).
    // SharedQmlEngine instances share a process-wide QQmlEngine, so filter by this
    // PanelConfigView's own rootContext hierarchy (Set Position… indicators).
    if (event->type() == QEvent::PlatformSurface
        && static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceCreated) {
        auto *dialog = qobject_cast<PlasmaQuick::Dialog *>(object);
        if (dialog && object != this && m_sharedQmlEngine) {
            for (QQmlContext *ctx = qmlContext(dialog); ctx; ctx = ctx->parentContext()) {
                if (ctx == m_sharedQmlEngine->rootContext()) {
                    placeIndicator(dialog);
                    break;
                }
            }
        }
    }
    return false;
}

void PanelConfigView::placeIndicator(QWindow *window)
{
    // PanelConfiguration.qml positions each indicator in the virtual desktop
    // (modelData.virtualX/virtualY). Keep that rectangle on that screen.
    auto update = [window] {
        const QPoint position = window->position();
        QScreen *screen = window->screen();
        if (!screen || !screen->geometry().contains(position)) {
            if (QScreen *at = QGuiApplication::screenAt(position)) screen = at;
        }
        if (!screen) return;
        auto *role = LayerShellQt::Window::get(window);
        role->setScope(QStringLiteral("bwm-r5-edit-indicator"));
        role->setLayer(LayerShellQt::Window::LayerOverlay);
        role->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);
        role->setActivateOnShow(false);
        role->setExclusiveZone(-1);
        role->setScreen(screen);
        role->setAnchors(LayerShellQt::Window::Anchors(LayerShellQt::Window::AnchorTop) | LayerShellQt::Window::AnchorLeft);
        role->setMargins(QMargins(position.x() - screen->geometry().x(), position.y() - screen->geometry().y(), 0, 0));
        QSize wanted = window->size();
        if (wanted.width() <= 0 || wanted.height() <= 0) {
            if (auto *mainItem = window->property("mainItem").value<QQuickItem *>()) {
                int w = int(std::ceil(std::max(mainItem->width(), mainItem->implicitWidth())));
                int h = int(std::ceil(std::max(mainItem->height(), mainItem->implicitHeight())));
                if (auto *m = window->property("margins").value<QObject *>()) {
                    w += m->property("left").toInt() + m->property("right").toInt();
                    h += m->property("top").toInt() + m->property("bottom").toInt();
                }
                wanted = QSize(std::max(wanted.width(), w), std::max(wanted.height(), h));
            }
            wanted = QSize(std::max(1, wanted.width()), std::max(1, wanted.height()));
        }
        role->setDesiredSize(wanted);
        window->setProperty("bwmIndicatorScreen", QVariant::fromValue(screen));
        if (auto *quick = qobject_cast<QQuickWindow *>(window); quick && quick->isVisible())
            quick->update();
        window->requestUpdate();
    };
    if (!window->property("bwmIndicatorPlaced").toBool()) {
        window->setProperty("bwmIndicatorPlaced", true);
        connect(window, &QWindow::xChanged, window, update);
        connect(window, &QWindow::yChanged, window, update);
        connect(window, &QWindow::widthChanged, window, update);
        connect(window, &QWindow::heightChanged, window, update);
    }
    update();
}

void PanelConfigView::keyPressEvent(QKeyEvent *ev)
{
    QQuickWindow::keyPressEvent(ev);
    if (ev->isAccepted()) {
        return;
    }
    if (ev->matches(QKeySequence::Cancel)) {
        ev->accept();
        hide();
    }
}

void PanelConfigView::showEvent(QShowEvent *ev)
{
    if (m_panelView) {
        m_panelView->setUserConfiguring(true);
    }
    PopupPlasmaWindow::showEvent(ev);
}

void PanelConfigView::hideEvent(QHideEvent *ev)
{
    PopupPlasmaWindow::hideEvent(ev);
    if (m_panelView) {
        m_panelView->setUserConfiguring(false);
    }
    if (m_panelRulerView) {
        m_panelRulerView->hide();
    }
    // Like PanelView 6.7.5: closing panel settings leaves edit mode unless edit mode
    // was entered from the desktop (DesktopEditMode stays open until exited there).
    if (m_containment->corona() && m_containment->corona()->isEditMode()) {
        auto *vc = qobject_cast<ViewCorona *>(m_containment->corona());
        if (!vc || !vc->enteredEditModeViaDesktop()) {
            m_containment->corona()->setEditMode(false);
        }
    }
    deleteLater();
}

void PanelConfigView::moveEvent(QMoveEvent *ev)
{
    PlasmaQuick::PlasmaWindow::moveEvent(ev);
    Q_EMIT geometryChanged(QRect(ev->pos(), size()));
}

void PanelConfigView::resizeEvent(QResizeEvent *ev)
{
    PlasmaQuick::PlasmaWindow::resizeEvent(ev);
    Q_EMIT geometryChanged(QRect(position(), ev->size()));
}

QRect PanelConfigView::geometry() const
{
    return QRect(position(), size());
}

PanelRulerView *PanelConfigView::panelRulerView()
{
    if (!m_panelRulerView) {
        m_panelRulerView = std::make_unique<PanelRulerView>(m_containment, m_panelView, this);
        connect(
            m_panelRulerView.get(),
            &PanelRulerView::visibleChanged,
            this,
            [this](bool visible) {
                setMargin(visible ? std::min(m_panelRulerView->width(), m_panelRulerView->height()) + 4 : 4);
            },
            Qt::QueuedConnection);
    }
    if (mainItem()) {
        m_panelRulerView->setMainItem(mainItem()->property("panelRuler").value<QQuickItem *>());
        m_panelRulerView->syncPanelLocation();
    }
    return m_panelRulerView.get();
}

QScreen *PanelConfigView::screenFromWindow(QWindow *window) const
{
    if (!window) {
        return nullptr;
    }
    // BWM: an indicator's output is the one its layer was placed on.
    QScreen *screen = window->property("bwmIndicatorScreen").value<QScreen *>();
    if (!screen) screen = window->screen();
    QQmlEngine::setObjectOwnership(screen, QQmlEngine::CppOwnership);
    return screen;
}

// SPDX-License-Identifier: GPL-2.0-or-later
#include "widgetexplorerview.h"
#include "panelviewhost.h"

#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <LayerShellQt/Window>
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <PlasmaQuick/SharedQmlEngine>
#include <QQmlComponent>
#include <QQuickItem>
#include <QQuickWindow>
#include <QScreen>
#include <QTimer>
#include <QDynamicPropertyChangeEvent>

using namespace Qt::StringLiterals;

WidgetExplorerView::WidgetExplorerView(PanelViewHost *panel)
    : QObject(panel), m_panel(panel), m_containment(panel ? panel->containment() : nullptr)
{
    // A click outside the whitelisted surfaces is the window deactivation that hides the
    // side bar in KWin (hideOnWindowDeactivate), unless a drag or menu is in progress.
    connect(&m_grab, &FocusGrab::cleared, this, [this] {
        m_grab.stop();
        if (m_sidePanel && m_sidePanel->isVisible() && m_sidePanel->property("hideOnWindowDeactivate").toBool())
            m_sidePanel->setVisible(false);
        else
            QTimer::singleShot(250, this, &WidgetExplorerView::updateGrab);
    });
}

WidgetExplorerView::~WidgetExplorerView()
{
    m_grab.stop();
    // The Dialog is owned by the QML root; release the engine (and with it the explorer)
    // while the panel view and its containment still exist.
    m_engine.reset();
}

QQuickItem *WidgetExplorerView::rootItem() const
{
    return m_engine ? qobject_cast<QQuickItem *>(m_engine->rootObject()) : nullptr;
}

bool WidgetExplorerView::isVisible() const
{
    return m_sidePanel && m_sidePanel->isVisible();
}

bool WidgetExplorerView::ensureLoaded()
{
    if (m_engine && rootItem() && m_sidePanel)
        return true;
    if (!m_panel || !m_containment) {
        m_error = tr("The widget explorer needs a live panel.");
        return false;
    }
    const auto shell = KPackage::PackageLoader::self()->loadPackage(u"Plasma/Shell"_s, u"org.kde.plasma.desktop"_s);
    // "explorer" is a directory in the shell package; Desktop.qml loads its WidgetExplorer.qml.
    const QUrl explorer = shell.fileUrl("explorer", u"WidgetExplorer.qml"_s);
    if (!shell.isValid() || explorer.isEmpty()) {
        m_error = tr("The installed KDE Plasma shell WidgetExplorer.qml is missing.");
        return false;
    }
    m_engine = std::make_unique<PlasmaQuick::SharedQmlEngine>(this);
    m_engine->setTranslationDomain(u"plasma_shell_org.kde.plasma.desktop"_s);
    m_engine->setInitializationDelayed(true);
    m_engine->setSource(QUrl::fromLocalFile(QStringLiteral(BWM_WIDGET_EXPLORER_HOST_QML)));
    m_engine->completeInitialization({{u"explorerSource"_s, explorer}, {u"containment"_s, QVariant::fromValue(m_containment.data())}});
    auto *root = rootItem();
    m_sidePanel = root ? root->property("sidePanel").value<QQuickWindow *>() : nullptr;
    if (!root || !m_sidePanel) {
        QStringList messages;
        for (const auto &e : m_engine->mainComponent() ? m_engine->mainComponent()->errors() : QList<QQmlError>())
            messages.append(e.toString());
        m_error = messages.isEmpty() ? tr("The widget explorer host did not load.") : messages.join(u'\n');
        m_engine.reset();
        return false;
    }
    connect(m_sidePanel, &QWindow::heightChanged, this, [this] {
        // The compositor decides the height of a layer anchored top and bottom; the
        // Loader follows it, as Desktop.qml binds it to the available screen height.
        auto *root = rootItem();
        auto *margins = m_sidePanel->property("margins").value<QObject *>();
        const int frame = margins ? margins->property("top").toInt() + margins->property("bottom").toInt() : 0;
        if (root && m_sidePanel->height() > frame)
            root->setProperty("contentHeight", m_sidePanel->height() - frame);
    });
    connect(m_sidePanel, &QWindow::widthChanged, this, &WidgetExplorerView::place);
    connect(m_sidePanel, &QWindow::visibleChanged, this, [this](bool visible) {
        m_grab.stop();
        if (visible) {
            QTimer::singleShot(50, this, &WidgetExplorerView::updateGrab);
            return;
        }
        // BWM: there is no desktop edit mode here; once the side bar is gone and the
        // panel settings did not reopen (WidgetExplorer.qml onClosed), leave edit mode.
        QTimer::singleShot(0, this, [this] {
            if (isVisible() || !m_containment || !m_containment->corona())
                return;
            if (!(m_panel && m_panel->userConfiguring()) && m_containment->corona()->isEditMode())
                m_containment->corona()->setEditMode(false);
        });
    });
    connect(m_panel, &QWindow::widthChanged, this, &WidgetExplorerView::place);
    connect(m_panel, &QWindow::heightChanged, this, &WidgetExplorerView::place);
    connect(m_containment, &Plasma::Containment::locationChanged, this, &WidgetExplorerView::place);
    // The panel's own layer geometry is published as properties (surfaces.cpp).
    m_panel->installEventFilter(this);
    connect(m_sidePanel, &QObject::destroyed, this, [this] {m_engine.release(); m_sidePanel = nullptr;});
    return true;
}

void WidgetExplorerView::place()
{
    if (!m_sidePanel || !m_panel || !m_panel->screen())
        return;
    QScreen *screen = m_panel->screen();
    const QRect area = screen->geometry();
    const bool right = m_containment && m_containment->location() == Plasma::Types::RightEdge;
    auto *root = rootItem();
    if (!m_panel->property("bwmLayerPanel").toBool()) {
        // Plain window preview/tests: the Dialog keeps Qt's own placement on this screen.
        m_sidePanel->setScreen(screen);
        if (root && root->property("contentHeight").toInt() <= 1)
            root->setProperty("contentHeight", area.height());
        return;
    }
    // Desktop.qml uses strictAvailableScreenRect in edit mode, so the side bar never
    // covers a panel. With exclusive zone 0 the compositor already leaves out every reserved
    // zone, the edited panel's included when it reserves one. A panel that does not reserve
    // (preview, Windows Go Below) is avoided with a margin from the output edge.
    QMargins margins;
    const QRect panel = m_panel->property("bwmPanelRect").toRect();
    const bool reserves = m_panel->property("bwmReservationRequested").toBool();
    switch (reserves ? Qt::Edge(0) : Qt::Edge(m_panel->property("bwmPanelEdge").toInt())) {
    case Qt::BottomEdge: margins.setBottom(std::max(0, area.bottom() + 1 - panel.top())); break;
    case Qt::TopEdge: margins.setTop(std::max(0, panel.bottom() + 1 - area.top())); break;
    case Qt::LeftEdge: if (!right) margins.setLeft(std::max(0, panel.right() + 1 - area.left())); break;
    case Qt::RightEdge: if (right) margins.setRight(std::max(0, area.right() + 1 - panel.left())); break;
    default: break;
    }
    using W = LayerShellQt::Window;
    auto *role = W::get(m_sidePanel);
    role->setScope(u"bwm-r5-widget-explorer"_s);
    role->setLayer(W::LayerTop);
    role->setKeyboardInteractivity(W::KeyboardInteractivityOnDemand);
    role->setActivateOnShow(true);
    role->setExclusiveZone(0);
    role->setScreen(screen);
    role->setAnchors(W::Anchors(right ? W::AnchorRight : W::AnchorLeft) | W::AnchorTop | W::AnchorBottom);
    role->setMargins(margins);
    role->setDesiredSize(QSize(std::max(1, m_sidePanel->width()), 0));
    if (m_sidePanel->screen() != screen && !m_sidePanel->handle())
        m_sidePanel->setScreen(screen);
    if (root && root->property("contentHeight").toInt() <= 1)
        root->setProperty("contentHeight", area.height() - margins.top() - margins.bottom());
    m_sidePanel->requestUpdate();
}

void WidgetExplorerView::updateGrab()
{
    if (!isVisible() || m_grab.active() || !FocusGrab::available() || !m_panel)
        return;
    // The edited panel stays usable: dropping a widget on it must not close the side bar.
    m_grab.start({m_sidePanel.data(), m_panel.data()});
}

bool WidgetExplorerView::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == m_panel && event->type() == QEvent::DynamicPropertyChange) {
        const auto name = static_cast<QDynamicPropertyChangeEvent *>(event)->propertyName();
        if (name == "bwmPanelRect" || name == "bwmPanelEdge" || name == "bwmReservationRequested")
            QTimer::singleShot(0, this, &WidgetExplorerView::place);
    }
    return QObject::eventFilter(watched, event);
}

bool WidgetExplorerView::toggle()
{
    if (!ensureLoaded())
        return false;
    if (!isVisible()) {
        // ShellCorona::toggleWidgetExplorer enters edit mode before showing it.
        if (m_containment->corona())
            m_containment->corona()->setEditMode(true);
        place();
    }
    QMetaObject::invokeMethod(rootItem(), "toggleWidgetExplorer", Q_ARG(QVariant, QVariant::fromValue(m_containment.data())));
    return true;
}

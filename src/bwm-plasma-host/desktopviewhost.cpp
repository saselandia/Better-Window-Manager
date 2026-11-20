/*
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2014 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: GPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/desktopview.{h,cpp} for Hyprland
    layer-shell without copying views/Desktop.qml or views/DesktopEditMode.qml.
*/
#include "desktopviewhost.h"
#include "alternativeshelper.h"
#include "configurationsession.h"
#include "containmentconfigview.h"
#include "panelviewhost.h"
#include "viewcorona.h"

#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <LayerShellQt/Window>
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/ConfigView>
#include <PlasmaQuick/Dialog>
#include <PlasmaQuick/SharedQmlEngine>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QEvent>
#include <QGuiApplication>
#include <QKeyEvent>
#include <QPlatformSurfaceEvent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickItem>
#include <QTimer>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <KConfigGroup>
#include <KSharedConfig>
#include <QAction>
#include <QIcon>
#include <KLocalizedString>
#include <algorithm>
#include <cmath>

using namespace Qt::StringLiterals;

namespace {

bool contextBelongsTo(QObject *object, QQmlContext *ancestor)
{
    if (!object || !ancestor)
        return false;
    for (QQmlContext *ctx = qmlContext(object); ctx; ctx = ctx->parentContext()) {
        if (ctx == ancestor)
            return true;
    }
    return false;
}

QSize deriveDialogSize(QWindow *window)
{
    QSize wanted = window ? window->size() : QSize();
    if (window && (wanted.width() <= 0 || wanted.height() <= 0)) {
        if (auto *mainItem = window->property("mainItem").value<QQuickItem *>()) {
            int w = int(std::ceil(std::max(mainItem->width(), mainItem->implicitWidth())));
            int h = int(std::ceil(std::max(mainItem->height(), mainItem->implicitHeight())));
            if (auto *margins = window->property("margins").value<QObject *>()) {
                w += margins->property("left").toInt() + margins->property("right").toInt();
                h += margins->property("top").toInt() + margins->property("bottom").toInt();
            }
            wanted = QSize(std::max(wanted.width(), w), std::max(wanted.height(), h));
        }
        wanted = QSize(std::max(1, wanted.width()), std::max(1, wanted.height()));
    }
    return wanted;
}

} // namespace

DesktopViewHost::DesktopViewHost(Plasma::Corona *corona, bool layerShell, QScreen *targetScreen)
    : PlasmaQuick::ContainmentView(corona)
    , m_layerShell(layerShell)
    , m_targetScreen(targetScreen ? targetScreen : screen())
{
    setResizeMode(SizeRootObjectToView);
    setColor(Qt::transparent);
    setTitle(tr("Desktop"));
    if (m_layerShell) {
        setFlag(Qt::FramelessWindowHint, true);
    }
    if (m_targetScreen) {
        setScreen(m_targetScreen);
    }
    rootContext()->setContextProperty(u"desktop"_s, this);

    if (m_layerShell) {
        configureLayerSurface();
    }

    connect(this, &QWindow::screenChanged, this, [this] {
        if (m_layerShell && m_targetScreen && screen() != m_targetScreen && !handle()) {
            setScreen(m_targetScreen);
        }
        if (m_layerShell) {
            configureLayerSurface();
        }
        Q_EMIT screenToFollowChanged();
        Q_EMIT strictAvailableScreenRectChanged();
        Q_EMIT configuredPanelChanged();
    });

    if (corona) {
        connect(corona, &Plasma::Corona::availableScreenRectChanged, this, [this](int id) {
            if (screen() && QGuiApplication::screens().indexOf(screen()) == id) {
                Q_EMIT strictAvailableScreenRectChanged();
                scheduleCompositorAreaRefresh();
            }
        });
        connect(corona, &Plasma::Corona::editModeChanged, this, [this](bool edit) {
            scheduleCompositorAreaRefresh();
            if (!edit && m_sidePanel && m_sidePanel->isVisible()) {
                m_sidePanel->setVisible(false);
            }
            if (m_layerShell) {
                configureLayerSurface();
            }
        });
    }
    if (auto *vc = qobject_cast<ViewCorona *>(corona)) {
        connect(vc, &ViewCorona::panelBeingConfiguredChanged, this, &DesktopViewHost::configuredPanelChanged);
    }

    connect(&m_sidePanelGrab, &FocusGrab::cleared, this, [this] {
        m_sidePanelGrab.stop();
        if (!m_sidePanel || !m_sidePanel->isVisible())
            return;
        if (!m_sidePanel->property("hideOnWindowDeactivate").toBool())
            return;
        m_sidePanel->setVisible(false);
    });
    connect(&m_alternativesGrab, &FocusGrab::cleared, this, [this] {
        m_alternativesGrab.stop();
        if (m_alternativesDialog && m_alternativesDialog->isVisible()) {
            m_alternativesDialog->close();
        }
    });

    qApp->installEventFilter(this);
    connect(qApp,&QGuiApplication::screenRemoved,this,[this](QScreen *removed){
        if(m_targetScreen!=removed)return;
        hide();QWindow::destroy();m_targetScreen=nullptr;emit screenToFollowChanged();
    });
}
bool DesktopViewHost::setScreenToFollow(QScreen *target) {
    if(!target || !QGuiApplication::screens().contains(target))return false;
    if(m_targetScreen==target)return true;
    if(m_sidePanel)m_sidePanel->hide();
    if(m_alternativesDialog)m_alternativesDialog->hide();
    const bool visible=isVisible();hide();QWindow::destroy();
    m_targetScreen=target;setScreen(target);configureLayerSurface();setGeometry(target->geometry());
    if(containment())containment()->reactToScreenChange();
    m_compositorUsable={};scheduleCompositorAreaRefresh();
    emit screenToFollowChanged();emit strictAvailableScreenRectChanged();
    if(visible)show();return true;
}

DesktopViewHost::~DesktopViewHost()
{
    qApp->removeEventFilter(this);
    m_sidePanelGrab.stop();
    m_alternativesGrab.stop();
    delete m_alternativesEngine.data();
    disconnect(this, nullptr, this, nullptr);
    if (containment()) {
        disconnect(containment(), nullptr, this, nullptr);
    }
    if (m_item) {
        m_item->setVisible(false);
        m_item->setParentItem(nullptr);
    }
    delete rootObject();
}

void DesktopViewHost::setError(const QString &message)
{
    if (m_error != message) {
        m_error = message;
        Q_EMIT errorChanged();
    }
}

void DesktopViewHost::setAccentColor(const QColor &color)
{
    if (m_accentColor != color) {
        m_accentColor = color;
        Q_EMIT accentColorChanged();
    }
}

QRect DesktopViewHost::strictAvailableScreenRect() const
{
    QScreen *s = screenToFollow();
    if (!s)
        return {};
    const QRect geom = s->geometry();
    QRect avail = s->availableGeometry();
    if (corona()) {
        const int id = QGuiApplication::screens().indexOf(s);
        if (id >= 0) {
            const QRect fromCorona = corona()->availableScreenRect(id);
            if (fromCorona.isValid() && !fromCorona.isEmpty()) {
                avail = fromCorona;
            }
        }
    }
    if (!avail.isValid() || avail.isEmpty()) {
        avail = geom;
    }
    QRect local = avail.translated(-geom.topLeft());
    // KWin's strictAvailableScreenRect accounts for every strut. Our Corona only knows its own
    // panels, so intersect with the compositor's usable area when Hyprland reports it.
    if (m_compositorUsable.isValid() && !m_compositorUsable.isEmpty()) {
        const QRect both = local.intersected(m_compositorUsable);
        if (both.isValid() && !both.isEmpty())
            local = both;
    }
    return local;
}

void DesktopViewHost::scheduleCompositorAreaRefresh()
{
    // Exclusive zones are applied by the compositor asynchronously after a commit.
    QTimer::singleShot(150, this, &DesktopViewHost::refreshCompositorArea);
    QTimer::singleShot(700, this, &DesktopViewHost::refreshCompositorArea);
}

void DesktopViewHost::refreshCompositorArea()
{
    const QString runtime = qEnvironmentVariable("BWM_R5_HYPR_RUNTIME");
    QScreen *s = screenToFollow();
    if (runtime.isEmpty() || !s || qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE").isEmpty())
        return;
    if (m_areaQuery && m_areaQuery->state() != QProcess::NotRunning) {
        scheduleCompositorAreaRefresh();
        return;
    }
    auto *process = new QProcess(this);
    m_areaQuery = process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(u"XDG_RUNTIME_DIR"_s, runtime);
    process->setProcessEnvironment(environment);
    connect(process, &QProcess::finished, this, [this, process](int code, QProcess::ExitStatus status) {
        process->deleteLater();
        QScreen *s = screenToFollow();
        if (code != 0 || status != QProcess::NormalExit || !s)
            return;
        const auto doc = QJsonDocument::fromJson(process->readAllStandardOutput());
        QRect usable;
        for (const auto &value : doc.array()) {
            const auto monitor = value.toObject();
            // Runtime-only match by connector; never persisted.
            if (monitor.value(u"name"_s).toString() != s->name())
                continue;
            const auto reserved = monitor.value(u"reserved"_s).toArray();
            if (reserved.size() != 4)
                break;
            const QSize size = s->geometry().size();
            usable = QRect(reserved[0].toInt(), reserved[1].toInt(), size.width() - reserved[0].toInt() - reserved[2].toInt(),
                           size.height() - reserved[1].toInt() - reserved[3].toInt());
            break;
        }
        if (usable != m_compositorUsable) {
            m_compositorUsable = usable;
            Q_EMIT strictAvailableScreenRectChanged();
        }
    });
    process->start(u"hyprctl"_s, {u"-j"_s, u"monitors"_s}, QIODevice::ReadOnly);
}

QObject *DesktopViewHost::configuredPanel() const
{
    auto *vc = qobject_cast<ViewCorona *>(corona());
    if (!vc)
        return nullptr;
    QObject *panel = vc->panelBeingConfigured();
    if (!panel)
        return nullptr;
    auto *panelScreen = panel->property("screenToFollow").value<QScreen *>();
    if (panelScreen && panelScreen != screenToFollow())
        return nullptr;
    return panel;
}

void DesktopViewHost::configureLayerSurface()
{
    if (!m_layerShell)
        return;
    using W = LayerShellQt::Window;
    auto *role = W::get(this);
    role->setScope(u"bwm-r5-desktop"_s);
    role->setLayer(W::LayerBackground);
    role->setAnchors(W::Anchors(W::AnchorTop) | W::AnchorBottom | W::AnchorLeft | W::AnchorRight);
    role->setExclusiveZone(-1);
    role->setDesiredSize(QSize(0, 0));
    role->setKeyboardInteractivity(W::KeyboardInteractivityOnDemand);
    role->setActivateOnShow(false);
    role->setCloseOnDismissed(false);
    role->setWantsToBeOnActiveScreen(false);
    if (QScreen *target = screenToFollow()) {
        if (screen() != target && !handle()) {
            setScreen(target);
        }
        role->setScreen(target);
    }
    if (isVisible()) {
        update();
    }
    requestUpdate();
}

bool DesktopViewHost::load(Plasma::Containment *c)
{
    if (!c || c->destroyed() || c->corona() != corona() || containment()
        || c->containmentType() == Plasma::Containment::Panel
        || c->containmentType() == Plasma::Containment::CustomPanel) {
        setError(tr("A desktop view requires a live desktop containment owned by its Corona."));
        return false;
    }
    QScreen *target = screenToFollow();
    if (!target) {
        setError(tr("A screen is required to load the native desktop view."));
        return false;
    }

    PanelViewHost::registerTypes();
    AlternativesHelper::registerTypes();

    const auto shell = KPackage::PackageLoader::self()->loadPackage(u"Plasma/Shell"_s, u"org.kde.plasma.desktop"_s);
    m_nativeSource = shell.fileUrl("views", u"Desktop.qml"_s);
    if (!shell.isValid() || m_nativeSource.isEmpty()) {
        setError(tr("The installed KDE Plasma shell Desktop.qml is missing."));
        return false;
    }

    const QSize initial = target->geometry().size().isEmpty() ? QSize(1280, 720) : target->geometry().size();
    setScreen(target);
    setGeometry(QRect(target->geometry().topLeft(), initial));
    if (m_layerShell) {
        configureLayerSurface();
    }
    setSource(m_nativeSource);
    QElapsedTimer timer;
    timer.start();
    while (status() == QQmlComponent::Loading && timer.elapsed() < 3000) {
        QCoreApplication::processEvents();
    }
    if (status() != QQmlComponent::Ready || !rootObject()) {
        QStringList messages;
        for (const auto &e : errors())
            messages.append(e.toString());
        setError(messages.isEmpty() ? tr("The native desktop view did not load.") : messages.join(u'\n'));
        return false;
    }
    auto *root = rootObject();
    for (const char *prop : {"containment", "editModeRect"}) {
        if (root->metaObject()->indexOfProperty(prop) < 0) {
            setError(tr("The installed Desktop.qml lacks its required property: %1").arg(QString::fromLatin1(prop)));
            return false;
        }
    }

    setContainment(c);
    m_item = PlasmaQuick::AppletQuickItem::itemForApplet(c);
    if (!m_item || c->failedToLaunch()) {
        setError(tr("The desktop containment item did not initialize."));
        return false;
    }

    // Locate the original sidePanel Dialog declared in Desktop.qml.
    if (!m_sidePanel) {
        m_sidePanel = root->findChild<PlasmaQuick::Dialog *>();
        if (m_sidePanel) {
            m_sidePanel->installEventFilter(this);
            connect(m_sidePanel, &QWindow::visibleChanged, this, [this](bool visible) {
                if (visible) {
                    if (m_layerShell)
                        placeSidePanel(m_sidePanel);
                    QTimer::singleShot(50, this, &DesktopViewHost::updateSidePanelGrab);
                } else {
                    m_sidePanelGrab.stop();
                }
            });
            connect(m_sidePanel, &QWindow::widthChanged, this, [this] {
                if (m_layerShell && m_sidePanel)
                    placeSidePanel(m_sidePanel);
            });
        }
    }

    connectContainment(c);
    connect(this, &PlasmaQuick::ContainmentView::containmentChanged, this, [this] {
        connectContainment(containment());
    });
    connect(screen(), &QScreen::geometryChanged, this, &DesktopViewHost::strictAvailableScreenRectChanged);
    connect(screen(), &QScreen::availableGeometryChanged, this, &DesktopViewHost::strictAvailableScreenRectChanged);

    Q_EMIT strictAvailableScreenRectChanged();
    scheduleCompositorAreaRefresh();
    return true;
}

void DesktopViewHost::connectContainment(Plasma::Containment *c)
{
    if (!c)
        return;
    m_item = PlasmaQuick::AppletQuickItem::itemForApplet(c);
    if (m_connectedContainments.contains(c))
        return;
    m_connectedContainments.append(c);
    connect(c, &Plasma::Containment::showAddWidgetsInterface, this, [this, c](const QPointF &) {
        if (containment() == c)
            toggleWidgetExplorer();
    });
    connect(c, &Plasma::Containment::appletAlternativesRequested, this, [this, c](Plasma::Applet *applet) {
        if (containment() == c)
            showAlternativesForApplet(applet);
    });

    // DesktopView::slotContainmentChanged (plasma-workspace 6.7.5): the desktop's own
    // "Enter Edit Mode" entry of org.kde.contextmenu ("desktop edit mode").
    if (!c->internalAction(QStringLiteral("desktop edit mode")) && c->corona()) {
        auto *desktopEditMode = new QAction(QIcon::fromTheme(QStringLiteral("document-edit")), i18nd("plasmashell", "Enter Edit Mode"), c);
        QAction *editMode = c->corona()->action(QStringLiteral("edit mode"));
        c->setInternalAction(QStringLiteral("desktop edit mode"), desktopEditMode);
        if (editMode)
            connect(desktopEditMode, &QAction::triggered, editMode, &QAction::triggered);
        connect(desktopEditMode, &QAction::triggered, this, [this] {
            auto *vc = qobject_cast<ViewCorona *>(corona());
            if (vc && vc->isEditMode())
                vc->setEnteredEditModeViaDesktop(true);
        });
        connect(c->corona(), &Plasma::Corona::editModeChanged, desktopEditMode, [desktopEditMode](bool editMode) {
            desktopEditMode->setText(editMode ? i18nd("plasmashell", "Exit Edit Mode") : i18nd("plasmashell", "Enter Edit Mode"));
        });
        auto updateEditModeAction = [desktopEditMode](Plasma::Types::ImmutabilityType immutability) {
            switch (immutability) {
            case Plasma::Types::UserImmutable:
                desktopEditMode->setEnabled(false);
                desktopEditMode->setVisible(true);
                break;
            case Plasma::Types::SystemImmutable:
                desktopEditMode->setEnabled(false);
                desktopEditMode->setVisible(false);
                break;
            case Plasma::Types::Mutable:
            default:
                desktopEditMode->setEnabled(true);
                desktopEditMode->setVisible(true);
                break;
            }
        };
        updateEditModeAction(c->corona()->immutability());
        connect(c->corona(), &Plasma::Corona::immutabilityChanged, desktopEditMode, updateEditModeAction);
    }
}

QWindow *DesktopViewHost::configurationWindow() const
{
    if (m_configView)
        return m_configView.data();
    if (auto *session = qobject_cast<ConfigurationSession *>(m_appletConfigSession.data()))
        return session->view();
    return nullptr;
}

Plasma::Containment *DesktopViewHost::setContainmentType(const QString &plugin)
{
    // Adapted from ShellCorona::setContainmentTypeForScreen (plasma-workspace 6.7.5).
    Plasma::Containment *oldContainment = containment();
    auto *vc = qobject_cast<ViewCorona *>(corona());
    if (!oldContainment || !vc || plugin.isEmpty())
        return oldContainment;
    Plasma::Containment *newContainment = vc->createContainmentDelayedForView(plugin);
    if (!newContainment) {
        return oldContainment;
    } else if (!newContainment->pluginMetaData().isValid()) {
        newContainment->deleteLater();
        return oldContainment;
    }

    KConfigGroup oldCg = oldContainment->config();
    KConfigGroup newCg(KSharedConfig::openConfig(oldCg.config()->name()), u"Containments"_s);
    newCg = KConfigGroup(&newCg, QString::number(newContainment->id()));
    KConfigGroup newCg2 = newContainment->config();
    const auto groups = oldCg.groupList();
    for (const QString &group : groups) {
        if (group != QLatin1String("Applets")) {
            KConfigGroup subGroup(&oldCg, group);
            KConfigGroup newSubGroup(&newCg, group);
            subGroup.copyTo(&newSubGroup);
            KConfigGroup newSubGroup2(&newCg2, group);
            subGroup.copyTo(&newSubGroup2);
        }
    }
    newContainment->init();
    const QMap<QString, QString> entryMap = oldCg.entryMap();
    for (auto it = entryMap.constBegin(); it != entryMap.constEnd(); it++) {
        if (it.key() == u"activityId" || it.key() == u"wallpaperplugin" || it.key().startsWith(u"ItemGeometries")) {
            newCg.writeEntry(it.key(), it.value());
            newCg2.writeEntry(it.key(), it.value());
        }
    }
    newContainment->restore(newCg);
    newContainment->updateConstraints(Plasma::Applet::StartupCompletedConstraint);
    newContainment->flushPendingConstraintsEvents();
    Q_EMIT corona()->containmentAdded(newContainment);

    const auto applets = oldContainment->applets();
    for (Plasma::Applet *applet : applets) {
        newContainment->addApplet(applet);
    }
    if (QAction *removeAction = newContainment->internalAction(QStringLiteral("remove"))) {
        removeAction->deleteLater();
    }
    vc->unbind(oldContainment);
    setContainment(newContainment);
    vc->bind(newContainment, this);
    newContainment->setActivity(oldContainment->activity());
    if (rootObject())
        rootObject()->setFocus(true, Qt::MouseFocusReason);
    QTimer::singleShot(2500, oldContainment, &Plasma::Applet::destroy);
    newContainment->save(newCg);
    corona()->requestConfigSync();
    Q_EMIT strictAvailableScreenRectChanged();
    return newContainment;
}

void DesktopViewHost::enterEditMode()
{
    if (!corona() || corona()->immutability() != Plasma::Types::Mutable)
        return;
    if (auto *vc = qobject_cast<ViewCorona *>(corona())) {
        vc->setEnteredEditModeViaDesktop(true);
    }
    corona()->setEditMode(true);
}

void DesktopViewHost::toggleWidgetExplorer()
{
    if (!rootObject() || !containment() || (corona() && corona()->immutability() != Plasma::Types::Mutable))
        return;
    if (corona() && !corona()->isEditMode()) {
        enterEditMode();
    }
    QMetaObject::invokeMethod(rootObject(), "toggleWidgetExplorer",
                              Q_ARG(QVariant, QVariant::fromValue(containment())));
}

QQuickWindow *DesktopViewHost::sidePanel() const
{
    if (m_sidePanel)
        return m_sidePanel.data();
    if (rootObject())
        return rootObject()->findChild<PlasmaQuick::Dialog *>();
    return nullptr;
}

void DesktopViewHost::placeSidePanel(PlasmaQuick::Dialog *dialog)
{
    QScreen *target = screenToFollow();
    if (!dialog || !m_layerShell || !target)
        return;
    using W = LayerShellQt::Window;
    auto *role = W::get(dialog);
    const bool right = dialog->property("sideBarOnRightEdge").toBool();
    role->setScope(u"bwm-r5-desktop-explorer"_s);
    role->setLayer(W::LayerTop);
    role->setKeyboardInteractivity(W::KeyboardInteractivityOnDemand);
    role->setActivateOnShow(true);
    role->setWantsToBeOnActiveScreen(false);
    // Exclusive zone 0 keeps the explorer inside Hyprland's usableArea (respecting both
    // our own reserving panels and any external compositor bar).
    role->setExclusiveZone(0);
    role->setScreen(target);
    role->setAnchors(W::Anchors(right ? W::AnchorRight : W::AnchorLeft) | W::AnchorTop | W::AnchorBottom);
    role->setMargins(QMargins());
    const QSize wanted = deriveDialogSize(dialog);
    role->setDesiredSize(QSize(std::max(1, wanted.width()), 0));
    if (dialog->screen() != target && !dialog->handle()) {
        dialog->setScreen(target);
    }
    if (dialog->isVisible()) {
        dialog->update();
    }
    dialog->requestUpdate();
}

void DesktopViewHost::updateSidePanelGrab()
{
    if (!m_sidePanel || !m_sidePanel->isVisible() || m_sidePanelGrab.active() || !FocusGrab::available())
        return;
    QList<QWindow *> allowed{m_sidePanel.data(), this};
    for (auto *w : QGuiApplication::allWindows()) {
        if (w->isVisible() && (qobject_cast<PanelViewHost *>(w) || w->property("bwmLayerPanel").toBool())) {
            allowed.append(w);
        }
    }
    m_sidePanelGrab.start(allowed);
}

void DesktopViewHost::placeAlternativesDialog(PlasmaQuick::Dialog *dialog, Plasma::Applet *applet)
{
    QScreen *target = screenToFollow();
    if (!dialog || !m_layerShell || !target)
        return;
    using W = LayerShellQt::Window;
    auto *role = W::get(dialog);
    role->setScope(u"bwm-r5-desktop-popup"_s);
    role->setLayer(W::LayerOverlay);
    role->setKeyboardInteractivity(W::KeyboardInteractivityOnDemand);
    role->setActivateOnShow(true);
    role->setWantsToBeOnActiveScreen(false);
    role->setExclusiveZone(0);
    role->setScreen(target);
    role->setAnchors(W::Anchors(W::AnchorTop) | W::AnchorLeft);
    const QSize wanted = deriveDialogSize(dialog);
    const QRect avail = strictAvailableScreenRect();
    QPoint pos(std::max(0, (avail.width() - wanted.width()) / 2),
               std::max(0, (avail.height() - wanted.height()) / 2));
    if (auto *item = PlasmaQuick::AppletQuickItem::itemForApplet(applet)) {
        const QRectF sceneRect = item->mapRectToScene(QRectF(0, 0, item->width(), item->height()));
        const int maxX = std::max(0, avail.width() - wanted.width());
        const int maxY = std::max(0, avail.height() - wanted.height());
        pos = QPoint(std::clamp(int(sceneRect.left()) - avail.left(), 0, maxX),
                     std::clamp(int(sceneRect.bottom()) - avail.top(), 0, maxY));
    }
    role->setMargins(QMargins(pos.x(), pos.y(), 0, 0));
    role->setDesiredSize(wanted);
    if (dialog->screen() != target && !dialog->handle()) {
        dialog->setScreen(target);
    }
    if (dialog->isVisible()) {
        dialog->update();
    }
    dialog->requestUpdate();
}

void DesktopViewHost::showAlternativesForApplet(Plasma::Applet *applet)
{
    if (!applet || applet->destroyed() || !containment() || applet->containment() != containment())
        return;
    if (m_showingAlternatives == applet && m_alternativesDialog && m_alternativesDialog->isVisible())
        return;
    delete m_alternativesEngine.data();
    const auto shell = KPackage::PackageLoader::self()->loadPackage(u"Plasma/Shell"_s, u"org.kde.plasma.desktop"_s);
    QUrl alternativesQML = shell.fileUrl("appletalternativesui");
    if (alternativesQML.isEmpty())
        alternativesQML = shell.fileUrl("explorer", u"AppletAlternatives.qml"_s);
    if (!shell.isValid() || alternativesQML.isEmpty()) {
        setError(tr("The installed KDE Plasma shell AppletAlternatives.qml is missing."));
        return;
    }
    auto *qmlObj = new PlasmaQuick::SharedQmlEngine(this);
    m_alternativesEngine = qmlObj;
    m_showingAlternatives = applet;
    qmlObj->setInitializationDelayed(true);
    qmlObj->setSource(alternativesQML);
    auto *helper = new AlternativesHelper(applet, qmlObj);
    qmlObj->rootContext()->setContextProperty(u"alternativesHelper"_s, helper);
    qmlObj->completeInitialization({{u"alternativesHelper"_s, QVariant::fromValue(helper)}});
    auto *dialog = qobject_cast<PlasmaQuick::Dialog *>(qmlObj->rootObject());
    if (!dialog) {
        setError(tr("The installed AppletAlternatives.qml did not create a Dialog."));
        delete qmlObj;
        return;
    }
    m_alternativesDialog = dialog;
    dialog->setScreen(screenToFollow());
    if (m_layerShell) {
        placeAlternativesDialog(dialog, applet);
        connect(dialog, &QWindow::widthChanged, dialog, [this, dialog, applet] { placeAlternativesDialog(dialog, applet); });
        connect(dialog, &QWindow::heightChanged, dialog, [this, dialog, applet] { placeAlternativesDialog(dialog, applet); });
    }
    connect(dialog, &QWindow::visibleChanged, this, [this, dialog, qmlObj](bool visible) {
        if (visible) {
            if (m_layerShell && FocusGrab::available()) {
                QTimer::singleShot(50, this, [this, dialog] {
                    if (dialog && dialog->isVisible())
                        m_alternativesGrab.start({dialog, this});
                });
            }
            return;
        }
        m_alternativesGrab.stop();
        if (m_alternativesDialog == dialog)
            m_alternativesDialog = nullptr;
        if (m_alternativesEngine == qmlObj) {
            m_alternativesEngine = nullptr;
            m_showingAlternatives = nullptr;
        }
        qmlObj->deleteLater();
    });
    dialog->show();
    dialog->requestActivate();
}

void DesktopViewHost::showConfigurationInterface(Plasma::Applet *applet)
{
    // Adapted from DesktopView::showConfigurationInterface (plasma-workspace 6.7.5).
    if (m_configView) {
        if (m_configView->applet() != applet) {
            m_configView->hide();
            m_configView->deleteLater();
        } else {
            m_configView->show();
            m_configView->requestActivate();
            return;
        }
    }
    if (!applet || !applet->containment())
        return;

    applet->containment()->corona()->setEditMode(false);

    auto *cont = qobject_cast<Plasma::Containment *>(applet);
    if (cont && cont->isContainment() && cont->containmentType() == Plasma::Containment::Desktop) {
        auto *view = new ContainmentConfigView(cont, this);
        m_configView = view;
        // If the layout changed with the dialog open, relaunch it for the new containment
        // (the third argument disconnects when the dialog closes).
        connect(this, &ContainmentView::containmentChanged, view, [this]() {
            if (!containment())
                return;
            if (containment()->property("wallpaperGraphicsObject").value<QObject *>()) {
                showConfigurationInterface(containment());
            } else {
                connect(containment(), &Plasma::Containment::wallpaperGraphicsObjectChanged, this, [this] {
                    disconnect(static_cast<Plasma::Containment *>(sender()), &Plasma::Containment::wallpaperGraphicsObjectChanged, this, nullptr);
                    showConfigurationInterface(static_cast<Plasma::Containment *>(sender()));
                });
            }
        });
        view->init();
        if (!view->error().isEmpty() || !view->rootObject()) {
            setError(view->error().isEmpty() ? tr("The native desktop configuration did not load.") : view->error());
            view->deleteLater();
            return;
        }
        view->setTransientParent(this);
        view->show();
        connect(this, &QObject::destroyed, view, [view] {
            view->hide();
            view->deleteLater();
        });
        return;
    }
    // Widgets use Plasma's original configuration frame, like the desktop dialog.
    delete m_appletConfigSession.data();
    auto *session = new ConfigurationSession(applet,true);
    session->setParent(this);
    if (!session->error().isEmpty() || !session->view()) {
        setError(session->error());
        session->deleteLater();
        return;
    }
    m_appletConfigSession = session;
    connect(session->view(), &QWindow::visibleChanged, session, [session](bool visible) {
        if (!visible)
            session->deleteLater();
    });
    session->show();
}

void DesktopViewHost::keyPressEvent(QKeyEvent *event)
{
    ContainmentView::keyPressEvent(event);
    if (event->isAccepted())
        return;
    if (event->matches(QKeySequence::Cancel) && corona() && corona()->isEditMode()) {
        event->accept();
        if (m_sidePanel && m_sidePanel->isVisible()) {
            m_sidePanel->setVisible(false);
        } else {
            corona()->setEditMode(false);
        }
    }
}

void DesktopViewHost::resizeEvent(QResizeEvent *event)
{
    ContainmentView::resizeEvent(event);
    if (auto *root = rootObject(); root && size().isValid() && root->size() != QSizeF(size())) {
        root->setSize(size());
    }
}

bool DesktopViewHost::eventFilter(QObject *watched, QEvent *event)
{
    if (event->type() == QEvent::PlatformSurface
        && static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceCreated) {
        if (auto *dialog = qobject_cast<PlasmaQuick::Dialog *>(watched)) {
            if (watched != this && contextBelongsTo(dialog, rootContext())) {
                if (!m_sidePanel) {
                    m_sidePanel = dialog;
                    dialog->installEventFilter(this);
                }
                if (m_layerShell && dialog == m_sidePanel) {
                    placeSidePanel(dialog);
                }
            } else if (m_alternativesEngine && contextBelongsTo(dialog, m_alternativesEngine->rootContext())
                       && m_layerShell && m_showingAlternatives) {
                placeAlternativesDialog(dialog, m_showingAlternatives);
            }
        }
    }
    // Under Hyprland, hovering the desktop view can transfer on-demand keyboard focus away from
    // sidePanel; do not let that focus-out hide the explorer while focus stays on our desktop.
    if (m_sidePanel && watched == m_sidePanel && event->type() == QEvent::FocusOut) {
        QWindow *focused = QGuiApplication::focusWindow();
        if (focused == this || qobject_cast<PanelViewHost *>(focused)) {
            return true;
        }
    }
    return false;
}

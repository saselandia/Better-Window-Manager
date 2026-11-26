// SPDX-License-Identifier: GPL-2.0-or-later
#include "notificationhost.h"
#include "surfaces.h"

#include <LayerShellQt/Window>
#include <notificationmanager/server.h>

#include <QDBusConnection>
#include <QDateTime>
#include <QFile>
#include <QGuiApplication>
#include <QPlatformSurfaceEvent>
#include <QQuickItem>
#include <QScreen>
#include <QTimer>

#include <algorithm>
#include <cmath>

namespace {
constexpr auto kNotificationService = "org.freedesktop.Notifications";

QScreen *screenForPopup(QQuickWindow *window)
{
    const auto screens = QGuiApplication::screens();
    const QRect geom = window->geometry();
    if (!geom.isEmpty()) {
        const QPoint center = geom.center();
        for (QScreen *s : screens) {
            if (s && s->geometry().contains(center)) {
                return s;
            }
        }
    }
    const QPoint pos = window->position();
    for (QScreen *s : screens) {
        if (s && s->geometry().contains(pos)) {
            return s;
        }
    }
    if (window->screen()) {
        return window->screen();
    }
    return QGuiApplication::primaryScreen();
}

QSize derivePopupSize(QQuickWindow *window)
{
    QSize wanted = window->size();
    if (wanted.width() > 0 && wanted.height() > 0) {
        return wanted;
    }
    if (auto *mainItem = window->property("mainItem").value<QQuickItem *>()) {
        const qreal iw = std::max(mainItem->implicitWidth(), mainItem->width());
        const qreal ih = std::max(mainItem->implicitHeight(), mainItem->height());
        int w = int(std::ceil(std::max<qreal>(0, iw)));
        int h = int(std::ceil(std::max<qreal>(0, ih)));
        w += window->property("leftPadding").toInt() + window->property("rightPadding").toInt();
        h += window->property("topPadding").toInt() + window->property("bottomPadding").toInt();
        if (wanted.width() <= 0) {
            wanted.setWidth(w);
        }
        if (wanted.height() <= 0) {
            wanted.setHeight(h);
        }
    }
    return QSize(std::max(1, wanted.width()), std::max(1, wanted.height()));
}
} // namespace

NotificationHost::NotificationHost(QString dndStatePath, QObject *parent)
    : QObject(parent)
    , m_dndStatePath(std::move(dndStatePath))
    , m_settings(this)
    , m_ownerWatcher(this)
{
    m_ownerWatcher.setConnection(QDBusConnection::sessionBus());
    m_ownerWatcher.setWatchMode(QDBusServiceWatcher::WatchForUnregistration);
    m_ownerWatcher.addWatchedService(QString::fromLatin1(kNotificationService));
    connect(&m_ownerWatcher, &QDBusServiceWatcher::serviceUnregistered, this, [this](const QString &service) {
        if (service != QLatin1String(kNotificationService) || !m_active) {
            return;
        }
        // Previous owner (e.g. Quickshell or swaync) just stepped aside: claim immediately.
        QTimer::singleShot(0, this, [this] {
            if (m_active && !isValid()) {
                claimService();
            }
        });
    });

    auto &server = NotificationManager::Server::self();
    connect(&server, &NotificationManager::Server::validChanged, this, [this] {
        writeDndState();
        Q_EMIT statusChanged();
    });
    connect(&server, &NotificationManager::Server::inhibitedChanged, this, [this](bool) {
        writeDndState();
        Q_EMIT statusChanged();
    });
    connect(&server, &NotificationManager::Server::serviceOwnershipLost, this, [this] {
        writeDndState();
        Q_EMIT statusChanged();
    });
    connect(&m_settings, &NotificationManager::Settings::settingsChanged, this, [this] {
        writeDndState();
        Q_EMIT statusChanged();
    });
}

NotificationHost::~NotificationHost()
{
    stop();
}

bool NotificationHost::start()
{
    if (!m_active) {
        m_active = true;
        qApp->installEventFilter(this);
        for (QWindow *window : QGuiApplication::allWindows()) {
            if (isNotificationWindow(window)) {
                adaptNotificationWindow(qobject_cast<QQuickWindow *>(window), false);
            }
        }
    }
    const bool ok = claimService();
    writeDndState();
    return ok;
}

void NotificationHost::stop()
{
    if (m_active) {
        m_active = false;
        if (qApp) {
            qApp->removeEventFilter(this);
        }
    }
    removeDndState();
}

bool NotificationHost::claimService()
{
    if (!m_active) {
        return false;
    }
    auto &server = NotificationManager::Server::self();
    const bool ok = server.init();
    writeDndState();
    Q_EMIT statusChanged();
    return ok;
}

bool NotificationHost::isValid() const
{
    return NotificationManager::Server::self().isValid();
}

bool NotificationHost::isInhibited() const
{
    const auto &server = NotificationManager::Server::self();
    if (server.isValid()) {
        return server.inhibited();
    }
    const QDateTime until = m_settings.notificationsInhibitedUntil();
    return until.isValid() && QDateTime::currentDateTimeUtc() < until.toUTC();
}

void NotificationHost::setDoNotDisturb(bool enabled)
{
    if (enabled) {
        m_settings.setNotificationsInhibitedUntil(QDateTime::currentDateTimeUtc().addYears(1));
        m_settings.save();
        NotificationManager::Server::self().setInhibited(true);
    } else {
        m_settings.resetNotificationsInhibitedUntil();
        m_settings.revokeApplicationInhibitions();
        m_settings.setFullscreenFocused(false);
        m_settings.setScreensMirrored(false);
        m_settings.save();
        NotificationManager::Server::self().setInhibited(false);
    }
    writeDndState();
    Q_EMIT statusChanged();
}

void NotificationHost::toggleDoNotDisturb()
{
    setDoNotDisturb(!isInhibited());
}

QJsonObject NotificationHost::status() const
{
    const auto &server = NotificationManager::Server::self();
    QString ownerName;
    if (QObject *owner = reinterpret_cast<QObject *>(server.currentOwner())) {
        ownerName = owner->property("name").toString();
    }
    return QJsonObject{
        {QStringLiteral("active"), m_active},
        {QStringLiteral("valid"), server.isValid()},
        {QStringLiteral("inhibited"), isInhibited()},
        {QStringLiteral("owner"), ownerName},
        {QStringLiteral("popupWindows"), int(m_observedWindows.size())},
    };
}

bool NotificationHost::isNotificationWindow(const QObject *object)
{
    const auto *quick = qobject_cast<const QQuickWindow *>(object);
    return quick && quick->inherits("NotificationWindow");
}

QMargins NotificationHost::popupMarginsForScreen(const QRect &screenGeometry, const QPoint &globalPos, const QSize &size)
{
    if (screenGeometry.isEmpty()) {
        return {};
    }
    const int maxX = std::max(0, screenGeometry.width() - std::max(1, size.width()));
    const int maxY = std::max(0, screenGeometry.height() - std::max(1, size.height()));
    const int localX = std::clamp(globalPos.x() - screenGeometry.x(), 0, maxX);
    const int localY = std::clamp(globalPos.y() - screenGeometry.y(), 0, maxY);
    return QMargins(localX, localY, 0, 0);
}

bool NotificationHost::eventFilter(QObject *watched, QEvent *event)
{
    if (!m_active) {
        return false;
    }
    if (event->type() == QEvent::PlatformSurface &&
        static_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() == QPlatformSurfaceEvent::SurfaceCreated) {
        if (isNotificationWindow(watched)) {
            adaptNotificationWindow(qobject_cast<QQuickWindow *>(watched), true);
        }
    } else if (event->type() == QEvent::Show) {
        if (isNotificationWindow(watched)) {
            adaptNotificationWindow(qobject_cast<QQuickWindow *>(watched), false);
        }
    }
    return false;
}

void NotificationHost::adaptNotificationWindow(QQuickWindow *window, bool creatingSurface)
{
    if (!window) {
        return;
    }
    if (!m_observedWindows.contains(window)) {
        m_observedWindows.insert(window);
        BwmSurface::ensureNativeEffectsCommit(window);
        connect(window, &QObject::destroyed, this, [this, window] {
            m_observedWindows.remove(window);
            m_updatingWindows.remove(window);
            m_requestedPos.remove(window);
        });
        auto sync = [this, guard = QPointer<QQuickWindow>(window)] {
            if (guard) {
                syncNotificationWindow(guard.data(), false);
            }
        };
        connect(window, &QWindow::xChanged, this, sync);
        connect(window, &QWindow::yChanged, this, sync);
        connect(window, &QWindow::widthChanged, this, sync);
        connect(window, &QWindow::heightChanged, this, sync);
        connect(window, &QWindow::visibleChanged, this, sync);
        for (const char *signal : {"takeFocusChanged()", "isCriticalChanged()", "mainItemChanged()"}) {
            if (window->metaObject()->indexOfSignal(signal) >= 0) {
                connect(window, QByteArray(QByteArray("2") + signal).constData(), this, SLOT(syncSenderWindow()));
            }
        }
    }
    syncNotificationWindow(window, creatingSurface);
}

void NotificationHost::syncSenderWindow()
{
    if (auto *window = qobject_cast<QQuickWindow *>(sender())) {
        syncNotificationWindow(window, false);
    }
}

void NotificationHost::syncNotificationWindow(QQuickWindow *window, bool creatingSurface)
{
    if (!window || m_updatingWindows.contains(window)) {
        return;
    }

    // Wayland layer-shell configure events report origin (0, 0) back to QWaylandWindow,
    // which overwrites QWindow::position(). Plasma's Globals.qml always offsets popups by
    // at least popupEdgeDistance (~36 px), so keep the last non-zero requested position.
    const QPoint currentPos = window->position();
    if (!currentPos.isNull() || !m_requestedPos.contains(window)) {
        m_requestedPos.insert(window, currentPos);
    }
    const QPoint effectivePos = m_requestedPos.value(window, currentPos);

    QScreen *targetScreen = nullptr;
    const QSize wanted = derivePopupSize(window);
    const QRect effectiveGeom(effectivePos, wanted);
    const auto screens = QGuiApplication::screens();
    for (QScreen *s : screens) {
        if (s && s->geometry().contains(effectiveGeom.center())) {
            targetScreen = s;
            break;
        }
    }
    if (!targetScreen) {
        for (QScreen *s : screens) {
            if (s && s->geometry().contains(effectivePos)) {
                targetScreen = s;
                break;
            }
        }
    }
    if (!targetScreen) {
        targetScreen = screenForPopup(window);
    }
    if (!targetScreen) {
        return;
    }
    m_updatingWindows.insert(window);

    using W = LayerShellQt::Window;
    auto *role = W::get(window);

    // If the popup moved to a different output after its Wayland surface was created,
    // recreate the surface so layer-shell binds it to the new output.
    if (!creatingSurface && window->handle() && role->screen() && role->screen() != targetScreen) {
        const bool wasVisible = window->isVisible();
        window->hide();
        window->destroy();
        window->setScreen(targetScreen);
        role->setScreen(targetScreen);
        m_updatingWindows.remove(window);
        if (wasVisible) {
            window->show();
        }
        return;
    }

    if (window->screen() != targetScreen) {
        window->setScreen(targetScreen);
    }

    const bool critical = window->property("isCritical").toBool();
    const bool takeFocus = window->property("takeFocus").toBool();
    const QRect screenGeom = targetScreen->geometry();
    const QMargins margins = popupMarginsForScreen(screenGeom, effectivePos, wanted);
    const W::Anchors anchors = W::Anchors(W::AnchorTop) | W::AnchorLeft;
    const W::Layer layer = critical ? W::LayerOverlay : W::LayerTop;
    const W::KeyboardInteractivity interactivity =
        takeFocus ? W::KeyboardInteractivityOnDemand : W::KeyboardInteractivityNone;

    const bool changed = creatingSurface
        || role->screen() != targetScreen
        || role->scope() != QLatin1String("bwm-plasma-notification")
        || role->layer() != layer
        || role->anchors() != anchors
        || role->margins() != margins
        || role->desiredSize() != wanted
        || role->exclusionZone() != -1
        || role->keyboardInteractivity() != interactivity
        || role->activateOnShow() != takeFocus;

    if (changed) {
        role->setScreen(targetScreen);
        role->setScope(QStringLiteral("bwm-plasma-notification"));
        role->setLayer(layer);
        role->setExclusiveZone(-1);
        role->setCloseOnDismissed(true);
        role->setAnchors(anchors);
        role->setMargins(margins);
        role->setDesiredSize(wanted);
        role->setKeyboardInteractivity(interactivity);
        role->setActivateOnShow(takeFocus);
        window->setProperty("bwmNotificationRect",
                            QRect(screenGeom.x() + margins.left(), screenGeom.y() + margins.top(),
                                  wanted.width(), wanted.height()));
        if (window->isVisible()) {
            window->update();
            window->requestUpdate();
        }
    }

    m_updatingWindows.remove(window);
}

void NotificationHost::writeDndState()
{
    if (m_dndStatePath.isEmpty()) {
        return;
    }
    const QByteArray payload = isInhibited() ? QByteArrayLiteral("true\n") : QByteArrayLiteral("false\n");
    const QString tmp = m_dndStatePath + QStringLiteral(".tmp");
    QFile file(tmp);
    if (file.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
        file.write(payload);
        file.flush();
        file.close();
        QFile::remove(m_dndStatePath);
        QFile::rename(tmp, m_dndStatePath);
    }
}

void NotificationHost::removeDndState()
{
    if (!m_dndStatePath.isEmpty()) {
        QFile::remove(m_dndStatePath);
    }
}

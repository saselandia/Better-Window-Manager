// SPDX-License-Identifier: GPL-2.0-or-later
#include "overviewhost.h"
#include "expolayout.h"
#include "taskbridge.h"
#include "tasksource.h"
#include "taskthumbnail.h"
#include <KLocalizedContext>
#include <KWindowEffects>
#include <LayerShellQt/Window>
#include <QEvent>
#include <QFileInfo>
#include <QGuiApplication>
#include <QIcon>
#include <QJsonDocument>
#include <QKeyEvent>
#include <QProcess>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickView>
#include <QScreen>
#include <QTimer>
#include <QUrl>
#include <algorithm>
#include <utility>

namespace {
QByteArray runHyprctlJson(const QString &subcommand) {
    QProcess proc;
    proc.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), subcommand});
    if (!proc.waitForFinished(600) || proc.exitCode() != 0) return {};
    return proc.readAllStandardOutput();
}
} // namespace

OverviewHost::OverviewHost(QString windowHelper, QString minimizeHelper, QObject *parent)
    : QObject(parent), m_windowHelper(std::move(windowHelper)), m_minimizeHelper(std::move(minimizeHelper)) {}

OverviewHost::~OverviewHost() {
    close();
}

QString OverviewHost::normalizeMode(const QString &mode) {
    const QString m = mode.trimmed().toLower();
    if (m == QStringLiteral("grid")) return QStringLiteral("grid");
    if (m == QStringLiteral("windowview") || m == QStringLiteral("windowview-current")) return QStringLiteral("windowview");
    if (m == QStringLiteral("windowview-all") || m == QStringLiteral("all")) return QStringLiteral("windowview-all");
    return QStringLiteral("overview");
}

QString OverviewHost::resolveIconName(const QString &appClass) {
    if (appClass.isEmpty()) return QStringLiteral("window");
    const QString lower = appClass.toLower();
    if (QIcon::hasThemeIcon(lower)) return lower;
    if (QIcon::hasThemeIcon(appClass)) return appClass;
    const QString last = lower.section(QLatin1Char('.'), -1);
    if (!last.isEmpty() && QIcon::hasThemeIcon(last)) return last;
    return QStringLiteral("application-x-executable");
}

void OverviewHost::setSearchText(const QString &text) {
    if (m_searchText == text) return;
    m_searchText = text;
    emit searchTextChanged();
}

void OverviewHost::setMode(const QString &mode) {
    const QString norm = normalizeMode(mode);
    if (m_mode == norm) return;
    m_mode = norm;
    emit stateChanged();
}

OverviewHost::Snapshot OverviewHost::parseSnapshot(
    const QJsonArray &clients,
    const QJsonArray &workspaces,
    const QJsonArray &monitors,
    const QJsonObject &activeWorkspace,
    const std::function<QString(const QString &)> &uuidLookup) {
    Snapshot snap;
    snap.activeWorkspaceId = activeWorkspace.value(QStringLiteral("id")).toInt(1);
    if (snap.activeWorkspaceId <= 0) snap.activeWorkspaceId = 1;

    QHash<int, QString> monitorIdToName;
    QHash<int, QRect> monitorIdToGeom;
    QHash<int, int> monitorActiveWs;
    for (const auto &mVal : monitors) {
        const auto m = mVal.toObject();
        const int id = m.value(QStringLiteral("id")).toInt(-1);
        const QString name = m.value(QStringLiteral("name")).toString();
        const double scale = qMax(0.25, m.value(QStringLiteral("scale")).toDouble(1.0));
        const int logicalW = qRound(m.value(QStringLiteral("width")).toInt(1920) / scale);
        const int logicalH = qRound(m.value(QStringLiteral("height")).toInt(1080) / scale);
        const QRect geom(m.value(QStringLiteral("x")).toInt(0), m.value(QStringLiteral("y")).toInt(0), logicalW, logicalH);
        monitorIdToName.insert(id, name);
        monitorIdToGeom.insert(id, geom);
        monitorActiveWs.insert(id, m.value(QStringLiteral("activeWorkspace")).toObject().value(QStringLiteral("id")).toInt(1));
        if (m.value(QStringLiteral("focused")).toBool()) {
            snap.activeMonitorName = name;
        }
        const auto special = m.value(QStringLiteral("specialWorkspace")).toObject();
        const QString spName = special.value(QStringLiteral("name")).toString();
        if (spName == QStringLiteral("special:magic")) {
            snap.magicOpen = true;
        }
    }

    QMap<int, QVariantMap> wsMap;
    int maxWsId = qMax(4, snap.activeWorkspaceId);
    for (const auto &wVal : workspaces) {
        const auto w = wVal.toObject();
        const int id = w.value(QStringLiteral("id")).toInt(0);
        if (id <= 0) continue; // special workspaces handled separately
        maxWsId = qMax(maxWsId, id);
        wsMap.insert(id, {
            {QStringLiteral("id"), id},
            {QStringLiteral("name"), w.value(QStringLiteral("name")).toString(QString::number(id))},
            {QStringLiteral("monitor"), w.value(QStringLiteral("monitor")).toString()},
            {QStringLiteral("windowCount"), w.value(QStringLiteral("windows")).toInt(0)},
            {QStringLiteral("active"), id == snap.activeWorkspaceId},
        });
    }
    for (int id = 1; id <= maxWsId; ++id) {
        if (!wsMap.contains(id)) {
            wsMap.insert(id, {
                {QStringLiteral("id"), id},
                {QStringLiteral("name"), QString::number(id)},
                {QStringLiteral("monitor"), snap.activeMonitorName},
                {QStringLiteral("windowCount"), 0},
                {QStringLiteral("active"), id == snap.activeWorkspaceId},
            });
        }
    }

    QVariantList winList;
    for (const auto &cVal : clients) {
        const auto c = cVal.toObject();
        if (!c.value(QStringLiteral("mapped")).toBool(true)) continue;
        if (c.value(QStringLiteral("hidden")).toBool(false)) continue;
        const auto wsObj = c.value(QStringLiteral("workspace")).toObject();
        const int wsId = wsObj.value(QStringLiteral("id")).toInt(0);
        const QString wsName = wsObj.value(QStringLiteral("name")).toString();
        const bool isMinimized = (wsName == QStringLiteral("special:minimized"));
        const bool isMagic = (wsName == QStringLiteral("special:magic"));
        const bool isSpecial = wsId < 0;
        if (isSpecial && !isMinimized && !isMagic) continue;

        const QString addr = c.value(QStringLiteral("address")).toString();
        const QString appClass = c.value(QStringLiteral("class")).toString();
        const QString title = c.value(QStringLiteral("title")).toString();
        const int monId = c.value(QStringLiteral("monitor")).toInt(-1);
        const QString monName = monitorIdToName.value(monId);
        const QRect monGeom = monitorIdToGeom.value(monId, QRect(0, 0, 1920, 1080));
        const auto at = c.value(QStringLiteral("at")).toArray();
        const auto sz = c.value(QStringLiteral("size")).toArray();
        const double wx = at.size() >= 2 ? at.at(0).toDouble() - monGeom.x() : 100.0;
        const double wy = at.size() >= 2 ? at.at(1).toDouble() - monGeom.y() : 100.0;
        const double ww = sz.size() >= 2 ? qMax(120.0, sz.at(0).toDouble()) : 800.0;
        const double wh = sz.size() >= 2 ? qMax(90.0, sz.at(1).toDouble()) : 600.0;

        const QString uuid = uuidLookup ? uuidLookup(addr) : QString();
        winList.append(QVariantMap{
            {QStringLiteral("address"), addr},
            {QStringLiteral("uuid"), uuid},
            {QStringLiteral("pid"), c.value(QStringLiteral("pid")).toInt(0)},
            {QStringLiteral("title"), title.isEmpty() ? appClass : title},
            {QStringLiteral("appClass"), appClass},
            {QStringLiteral("iconName"), resolveIconName(appClass)},
            {QStringLiteral("workspaceId"), wsId},
            {QStringLiteral("workspaceName"), wsName},
            {QStringLiteral("monitorName"), monName},
            {QStringLiteral("x"), qMax(0.0, wx)},
            {QStringLiteral("y"), qMax(0.0, wy)},
            {QStringLiteral("width"), ww},
            {QStringLiteral("height"), wh},
            {QStringLiteral("minimized"), isMinimized},
            {QStringLiteral("magic"), isMagic},
            {QStringLiteral("special"), isSpecial},
            {QStringLiteral("floating"), c.value(QStringLiteral("floating")).toBool()},
            {QStringLiteral("fullscreen"), c.value(QStringLiteral("fullscreen")).toInt(0) != 0},
        });

        if (!isSpecial && wsMap.contains(wsId)) {
            auto entry = wsMap[wsId];
            entry[QStringLiteral("windowCount")] = entry.value(QStringLiteral("windowCount")).toInt() + 1;
            wsMap[wsId] = entry;
        }
    }

    for (auto it = wsMap.constBegin(); it != wsMap.constEnd(); ++it) {
        snap.workspaces.append(it.value());
    }
    snap.windows = std::move(winList);
    return snap;
}

OverviewHost::Snapshot OverviewHost::captureLiveSnapshot() const {
    const auto clients = QJsonDocument::fromJson(runHyprctlJson(QStringLiteral("clients"))).array();
    const auto workspaces = QJsonDocument::fromJson(runHyprctlJson(QStringLiteral("workspaces"))).array();
    const auto monitors = QJsonDocument::fromJson(runHyprctlJson(QStringLiteral("monitors"))).array();
    const auto activeWs = QJsonDocument::fromJson(runHyprctlJson(QStringLiteral("activeworkspace"))).object();

    auto *bridge = BwmTaskBridge::thumbnailBridge();
    auto lookup = [bridge](const QString &addr) -> QString {
        return bridge && bridge->source() ? bridge->source()->uuidForAddress(addr) : QString();
    };
    return parseSnapshot(clients, workspaces, monitors, activeWs, lookup);
}

void OverviewHost::refresh() {
    m_snapshot = captureLiveSnapshot();
    emit stateChanged();
}

QVariantList OverviewHost::windowsFor(const QString &monitorName, int workspaceId, bool allWorkspaces, bool includeMinimized) const {
    QVariantList result;
    const QString query = m_searchText.trimmed().toLower();
    for (const auto &v : m_snapshot.windows) {
        const auto m = v.toMap();
        const bool isMin = m.value(QStringLiteral("minimized")).toBool();
        const bool isMagic = m.value(QStringLiteral("magic")).toBool();
        if (isMin && !includeMinimized) continue;
        if (!allWorkspaces) {
            if (!monitorName.isEmpty() && m.value(QStringLiteral("monitorName")).toString() != monitorName) continue;
            if (isMagic) {
                if (!m_snapshot.magicOpen) continue;
            } else if (!isMin && m.value(QStringLiteral("workspaceId")).toInt() != workspaceId) {
                continue;
            }
        }
        if (!query.isEmpty()) {
            const QString title = m.value(QStringLiteral("title")).toString().toLower();
            const QString cls = m.value(QStringLiteral("appClass")).toString().toLower();
            if (!title.contains(query) && !cls.contains(query)) continue;
        }
        result.append(m);
    }
    return result;
}

bool OverviewHost::toggle(const QString &mode) {
    const QString norm = normalizeMode(mode);
    if (isActive()) {
        if (m_mode == norm) {
            close();
            return true;
        }
        setMode(norm);
        return true;
    }
    return open(norm);
}

bool OverviewHost::open(const QString &mode) {
    const QString norm = normalizeMode(mode);
    if (isActive()) {
        setMode(norm);
        return true;
    }

    if (!m_qmlTypesRegistered) {
        qmlRegisterType<ExpoLayout>("org.bwm.kwin.effects", 1, 0, "ExpoLayout");
        qmlRegisterType<ExpoCell>("org.bwm.kwin.effects", 1, 0, "ExpoCell");
        qmlRegisterType<TaskThumbnail>("org.bwm.kwin.effects", 1, 0, "WindowThumbnail");
        m_qmlTypesRegistered = true;
    }

    const QString qmlPath = QStringLiteral(BWM_OVERVIEW_MAIN_QML);
    if (!QFileInfo::exists(qmlPath)) {
        m_error = QStringLiteral("Overview QML not found: ") + qmlPath;
        return false;
    }

    m_error.clear();
    m_mode = norm;
    m_searchText.clear();
    m_snapshot = captureLiveSnapshot();
    emit searchTextChanged();
    emit stateChanged();

    const auto screens = QGuiApplication::screens();
    if (screens.isEmpty()) {
        m_error = QStringLiteral("No screens available");
        return false;
    }

    for (auto *screen : screens) {
        auto *view = new QQuickView;
        view->setColor(Qt::transparent);
        view->setScreen(screen);
        view->setResizeMode(QQuickView::SizeRootObjectToView);
        view->installEventFilter(this);

        QString thumbErr;
        installTaskThumbnails(view->engine(), &thumbErr);

        auto *i18n = new KLocalizedContext(view->engine());
        i18n->setTranslationDomain(QStringLiteral("kwin"));
        view->engine()->rootContext()->setContextObject(i18n);

        const bool isPrimaryScreen = (screen->name() == m_snapshot.activeMonitorName)
            || (m_snapshot.activeMonitorName.isEmpty() && screen == screens.first());
        view->rootContext()->setContextProperty(QStringLiteral("overviewHost"), this);
        view->rootContext()->setContextProperty(QStringLiteral("screenName"), screen->name());
        view->rootContext()->setContextProperty(QStringLiteral("isPrimaryOverviewScreen"), isPrimaryScreen);

        using W = LayerShellQt::Window;
        auto *layer = W::get(view);
        layer->setScope(QStringLiteral("bwm-plasma-overview"));
        layer->setLayer(W::LayerOverlay);
        layer->setExclusiveZone(-1);
        layer->setAnchors(W::Anchors(W::AnchorTop) | W::AnchorBottom | W::AnchorLeft | W::AnchorRight);
        layer->setDesiredSize({0, 0});
        layer->setScreen(screen);
        layer->setKeyboardInteractivity(isPrimaryScreen ? W::KeyboardInteractivityExclusive : W::KeyboardInteractivityOnDemand);

        view->setSource(QUrl::fromLocalFile(qmlPath));
        if (view->status() == QQuickView::Error) {
            QStringList errs;
            for (const auto &e : view->errors()) errs.append(e.toString());
            m_error = errs.join(QStringLiteral("\n"));
            view->deleteLater();
            close();
            return false;
        }

        KWindowEffects::enableBlurBehind(view, true);
        connect(screen, &QObject::destroyed, view, &QObject::deleteLater);
        view->setGeometry(screen->geometry());
        view->show();
        m_views.append(view);
    }

    emit stateChanged();
    return !m_views.isEmpty();
}

void OverviewHost::close() {
    const auto views = std::exchange(m_views, {});
    for (const auto &v : views) {
        if (v) {
            v->hide();
            v->deleteLater();
        }
    }
    if (!views.isEmpty()) {
        emit stateChanged();
        emit closed();
    }
}

bool OverviewHost::eventFilter(QObject *watched, QEvent *event) {
    if (event->type() == QEvent::KeyPress) {
        auto *ke = static_cast<QKeyEvent *>(event);
        if (ke->key() == Qt::Key_Escape) {
            if (!m_searchText.isEmpty()) {
                setSearchText({});
            } else {
                close();
            }
            return true;
        }
    }
    return QObject::eventFilter(watched, event);
}

bool OverviewHost::runHyprctlDispatch(const QStringList &args) const {
    QStringList full = {QStringLiteral("dispatch")};
    full.append(args);
    return QProcess::startDetached(QStringLiteral("hyprctl"), full);
}

void OverviewHost::activateWindow(const QString &address, int workspaceId, bool minimized, bool special) {
    close();
    if (address.isEmpty()) return;
    if (minimized && QFileInfo::exists(m_minimizeHelper)) {
        QProcess::startDetached(QStringLiteral("python3"), {m_minimizeHelper, QStringLiteral("restore"), address});
        return;
    }
    if (special) {
        runHyprctlDispatch({QStringLiteral("focuswindow"), QStringLiteral("address:") + address});
        return;
    }
    if (workspaceId > 0 && workspaceId != m_snapshot.activeWorkspaceId) {
        runHyprctlDispatch({QStringLiteral("workspace"), QString::number(workspaceId)});
    }
    runHyprctlDispatch({QStringLiteral("focuswindow"), QStringLiteral("address:") + address});
}

void OverviewHost::closeWindow(const QString &address) {
    if (address.isEmpty()) return;
    if (QFileInfo::exists(m_windowHelper)) {
        QProcess::startDetached(QStringLiteral("python3"), {m_windowHelper, QStringLiteral("close"), address});
    } else {
        runHyprctlDispatch({QStringLiteral("closewindow"), QStringLiteral("address:") + address});
    }
    QTimer::singleShot(180, this, &OverviewHost::refresh);
}

void OverviewHost::moveWindowToWorkspace(const QString &address, int workspaceId) {
    if (address.isEmpty() || workspaceId <= 0) return;
    runHyprctlDispatch({QStringLiteral("movetoworkspacesilent"), QString::number(workspaceId) + QStringLiteral(",address:") + address});
    QTimer::singleShot(150, this, &OverviewHost::refresh);
}

void OverviewHost::switchToWorkspace(int workspaceId) {
    if (workspaceId <= 0) return;
    close();
    runHyprctlDispatch({QStringLiteral("workspace"), QString::number(workspaceId)});
}

void OverviewHost::addWorkspace() {
    int maxId = 0;
    for (const auto &v : m_snapshot.workspaces) {
        maxId = qMax(maxId, v.toMap().value(QStringLiteral("id")).toInt());
    }
    switchToWorkspace(maxId + 1);
}

QJsonObject OverviewHost::status() const {
    return {
        {QStringLiteral("active"), isActive()},
        {QStringLiteral("mode"), m_mode},
        {QStringLiteral("views"), m_views.size()},
        {QStringLiteral("activeWorkspaceId"), m_snapshot.activeWorkspaceId},
        {QStringLiteral("magicOpen"), m_snapshot.magicOpen},
        {QStringLiteral("windowCount"), m_snapshot.windows.size()},
        {QStringLiteral("workspaceCount"), m_snapshot.workspaces.size()},
        {QStringLiteral("error"), m_error},
    };
}

// SPDX-License-Identifier: GPL-2.0-or-later
#include "controller.h"
#include "platform.h"
#include <KGlobalAccelD/kglobalacceld.h>
#include <KGlobalShortcutInfo>
#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QKeySequence>
#include <QProcess>
#include <QSaveFile>
#include <QStandardPaths>

using BwmKeymap::HyprKey;

namespace {
const QString BwmComponent = QStringLiteral("bwm");
const QString BwmFriendly = QStringLiteral("BWM");
// Description prefix of our binds: identifies them in `hyprctl -j binds`.
const QString OwnPrefix = QStringLiteral("KDE: ");

QString runtimeDir()
{
    const QString dir = qEnvironmentVariable("XDG_RUNTIME_DIR");
    return dir.isEmpty() ? QDir::tempPath() : dir;
}

QStringList bwmAction(const QString &id, const QString &friendly)
{
    return {BwmComponent, id, BwmFriendly, friendly};
}

QString luaString(const QString &s)
{
    QString out = QStringLiteral("\"");
    for (const QChar c : s) {
        if (c == u'\\' || c == u'"')
            out += u'\\';
        if (c == u'\n') {
            out += QStringLiteral("\\n");
            continue;
        }
        out += c;
    }
    return out + u'"';
}
}

Controller::Controller(KGlobalAccelD *daemon, BwmPlatform *platform, QObject *parent)
    : QObject(parent)
    , m_daemon(daemon)
    , m_platform(platform)
{
    m_syncTimer.setSingleShot(true);
    m_syncTimer.setInterval(150);
    connect(&m_syncTimer, &QTimer::timeout, this, &Controller::startSync);
    connect(m_platform, &BwmPlatform::grabsChanged, this, &Controller::scheduleSync);
    connect(&m_server, &QLocalServer::newConnection, this, [this] {
        while (QLocalSocket *socket = m_server.nextPendingConnection())
            handleClient(socket);
    });
    watchHyprlandEvents();
    // kglobalacceld 6.7 lets two actions share a key (the oldest wins), so registrations are
    // only noticed through its configuration write (500 ms after each change). The file is
    // replaced atomically: watch its directory and compare the modification time.
    const QString config = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation);
    QDir().mkpath(config);
    m_configWatcher.addPath(config);
    connect(&m_configWatcher, &QFileSystemWatcher::directoryChanged, this, [this, config] {
        const qint64 stamp = QFileInfo(config + QStringLiteral("/kglobalshortcutsrc")).lastModified().toMSecsSinceEpoch();
        if (stamp != m_configStamp) {
            m_configStamp = stamp;
            scheduleSync();
        }
    });
}

QString Controller::socketPath()
{
    const QString env = qEnvironmentVariable("BWM_KGLOBALACCEL_SOCKET");
    return env.isEmpty() ? runtimeDir() + QStringLiteral("/bwm-kglobalaccel.sock") : env;
}

QString Controller::statePath()
{
    const QString env = qEnvironmentVariable("BWM_KGLOBALACCEL_STATE");
    if (!env.isEmpty())
        return env;
    return QStandardPaths::writableLocation(QStandardPaths::GenericStateLocation) + QStringLiteral("/bwm/kde-shortcuts.lua");
}

bool Controller::listen()
{
    // Only reached after owning org.kde.kglobalaccel, so a leftover socket is stale.
    QLocalServer::removeServer(socketPath());
    m_server.setSocketOptions(QLocalServer::UserAccessOption);
    if (!m_server.listen(socketPath())) {
        qWarning("bwm-kglobalaccel: cannot listen on %s", qPrintable(socketPath()));
        return false;
    }
    // First reconciliation before the event loop runs: D-Bus registrations that arrive
    // meanwhile wait in the queue, so no app can take a key of BWM's in between.
    QByteArray binds;
    if (runHyprctl({QStringLiteral("-j"), QStringLiteral("binds")}, 2000, &binds))
        finishSync(binds);
    else
        scheduleSync();
    return true;
}

void Controller::watchHyprlandEvents()
{
    const QString signature = qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE");
    if (signature.isEmpty() || qEnvironmentVariableIsSet("BWM_KGLOBALACCEL_HYPRCTL"))
        return;
    connect(&m_events, &QLocalSocket::readyRead, this, [this] {
        while (m_events.canReadLine()) {
            const QByteArray line = m_events.readLine();
            // A reload rebuilds every bind: BWM's may have changed (keybinds-manager reload).
            if (line.startsWith("configreloaded>>"))
                scheduleSync();
        }
    });
    m_events.connectToServer(runtimeDir() + QStringLiteral("/hypr/") + signature + QStringLiteral("/.socket2.sock"));
}

void Controller::scheduleSync()
{
    m_syncTimer.start();
}

bool Controller::runHyprctl(const QStringList &args, int timeoutMs, QByteArray *out) const
{
    QString program = qEnvironmentVariable("BWM_KGLOBALACCEL_HYPRCTL");
    if (program.isEmpty())
        program = QStringLiteral("hyprctl");
    QProcess process;
    process.start(program, args);
    if (!process.waitForFinished(timeoutMs) || process.exitStatus() != QProcess::NormalExit || process.exitCode() != 0) {
        process.kill();
        process.waitForFinished(200);
        return false;
    }
    if (out)
        *out = process.readAllStandardOutput();
    return true;
}

void Controller::startSync()
{
    if (m_bindsQuery) {
        m_syncPending = true;
        return;
    }
    QString program = qEnvironmentVariable("BWM_KGLOBALACCEL_HYPRCTL");
    if (program.isEmpty())
        program = QStringLiteral("hyprctl");
    m_bindsQuery = new QProcess(this);
    connect(m_bindsQuery, &QProcess::finished, this, [this](int code, QProcess::ExitStatus st) {
        QProcess *query = m_bindsQuery;
        m_bindsQuery = nullptr;
        const QByteArray output = query->readAllStandardOutput();
        query->deleteLater();
        if (st == QProcess::NormalExit && code == 0) {
            finishSync(output);
        } else {
            m_lastError = QStringLiteral("hyprctl -j binds failed");
        }
        if (m_syncPending) {
            m_syncPending = false;
            scheduleSync();
        }
    });
    connect(m_bindsQuery, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error != QProcess::FailedToStart || !m_bindsQuery)
            return;
        m_bindsQuery->deleteLater();
        m_bindsQuery = nullptr;
        m_lastError = QStringLiteral("hyprctl not found");
    });
    m_bindsQuery->start(program, {QStringLiteral("-j"), QStringLiteral("binds")});
}

QList<Controller::BwmBind> Controller::parseBwmBinds(const QByteArray &json) const
{
    QList<BwmBind> result;
    QSet<HyprKey> seen;
    for (const QJsonValue &value : QJsonDocument::fromJson(json).array()) {
        const QJsonObject bind = value.toObject();
        const QString description = bind.value(QStringLiteral("description")).toString();
        if (description.startsWith(OwnPrefix) || bind.value(QStringLiteral("mouse")).toBool()
            || bind.value(QStringLiteral("catch_all")).toBool() || !bind.value(QStringLiteral("submap")).toString().isEmpty())
            continue;
        const QString name = bind.value(QStringLiteral("key")).toString();
        if (name.isEmpty())
            continue;
        const auto key = BwmKeymap::fromHyprland(quint32(bind.value(QStringLiteral("modmask")).toInt()), name);
        if (!key || seen.contains(*key))
            continue;
        seen.insert(*key);
        result.append({*key, description});
    }
    return result;
}

void Controller::notify(const QString &title, const QString &body)
{
    m_notices.append(title);
    if (!qEnvironmentVariableIsSet("BWM_KGLOBALACCEL_NO_NOTIFY"))
        QProcess::startDetached(QStringLiteral("notify-send"), {QStringLiteral("-a"), QStringLiteral("BWM"), title, body});
}

void Controller::reconcileBwmComponent(const QList<BwmBind> &binds)
{
    QSet<QString> wanted;
    for (const BwmBind &bind : binds) {
        const int qt = BwmKeymap::toQt(bind.key);
        if (!qt)
            continue;
        const QString id = BwmKeymap::spec(bind.key);
        const QString friendly = bind.description.isEmpty() ? id : bind.description;
        const QKeySequence sequence(qt);
        wanted.insert(id);
        // A key BWM uses stays BWM's: an older KDE assignment is removed and the KDE action
        // is left without that key (shown as unassigned in Preferences → Shortcuts).
        const QList<KGlobalShortcutInfo> holders = m_daemon->globalShortcutsByKey(sequence, KGlobalAccel::MatchType::Equal);
        for (const KGlobalShortcutInfo &info : holders) {
            if (info.componentUniqueName() == BwmComponent)
                continue;
            const QStringList other{info.componentUniqueName(), info.uniqueName(), info.componentFriendlyName(), info.friendlyName()};
            QSet<QKeySequence> keys = m_daemon->shortcutKeys(other);
            if (!keys.remove(sequence))
                continue;
            m_daemon->setForeignShortcutKeys(other, keys);
            m_stripped.append(QStringLiteral("%1 (%2)").arg(info.friendlyName(), sequence.toString(QKeySequence::NativeText)));
        }
        const QStringList action = bwmAction(id, friendly);
        const bool known = m_daemon->shortcutKeys(action).size() || m_daemon->defaultShortcutKeys(action).size();
        m_daemon->doRegister(action);
        const QSet<QKeySequence> current = m_daemon->shortcutKeys(action);
        if (current != QSet<QKeySequence>{sequence}) {
            if (known && !current.isEmpty())
                m_revertedEdits.append(friendly);
            m_daemon->setShortcutKeys(action, {sequence}, KGlobalAccelD::SetPresent | KGlobalAccelD::NoAutoloading);
        }
        if (m_daemon->defaultShortcutKeys(action) != QSet<QKeySequence>{sequence})
            m_daemon->setShortcutKeys(action, {sequence}, KGlobalAccelD::IsDefault);
    }
    // Binds BWM no longer has leave the component.
    for (const QStringList &action : m_daemon->allActionsForComponent(bwmAction(QString(), QString()))) {
        if (action.size() > 1 && !wanted.contains(action.at(1)))
            m_daemon->unregister(BwmComponent, action.at(1));
    }
    if (!m_stripped.isEmpty()) {
        notify(QStringLiteral("Atajo de KDE en conflicto con BWM"),
               QStringLiteral("Sin asignar porque BWM ya usa la tecla: %1. Dale otra libre en Preferencias → Atajos.")
                   .arg(m_stripped.join(QStringLiteral(", "))));
        m_stripped.clear();
    }
    if (!m_revertedEdits.isEmpty()) {
        notify(QStringLiteral("Atajo de BWM sin cambios"),
               QStringLiteral("Los atajos de BWM se cambian en Preferencias → BWM — Atajos (%1).")
                   .arg(m_revertedEdits.join(QStringLiteral(", "))));
        m_revertedEdits.clear();
    }
}

QString Controller::friendlyFor(int key) const
{
    const auto infos = m_daemon->globalShortcutsByKey(QKeySequence(key), KGlobalAccel::MatchType::Equal);
    for (const KGlobalShortcutInfo &info : infos)
        return info.componentFriendlyName() + QStringLiteral(": ") + info.friendlyName();
    return QKeySequence(key).toString(QKeySequence::PortableText);
}

void Controller::finishSync(const QByteArray &bindsJson)
{
    ++m_syncs;
    const QList<BwmBind> bwm = parseBwmBinds(bindsJson);
    m_bwmKeys.clear();
    m_bwmSpecs.clear();
    for (const BwmBind &bind : bwm) {
        m_bwmKeys.insert(bind.key);
        m_bwmSpecs.insert(BwmKeymap::spec(bind.key));
    }
    reconcileBwmComponent(bwm);

    QHash<HyprKey, QPair<int, QString>> wanted;
    for (const int key : m_platform->grabbed()) {
        const auto hk = BwmKeymap::fromQt(key);
        if (!hk || m_bwmKeys.contains(*hk))
            continue;
        wanted.insert(*hk, {key, friendlyFor(key)});
    }
    m_bound = wanted;
    const QString state = renderState(wanted);
    if (state == m_lastState)
        return;
    apply(state, m_bwmSpecs);
}

QString Controller::renderState(const QHash<HyprKey, QPair<int, QString>> &binds) const
{
    QStringList keys;
    for (auto it = binds.cbegin(); it != binds.cend(); ++it)
        keys << BwmKeymap::spec(it.key());
    keys.sort();
    QString text = QStringLiteral(
        "-- Generated by bwm-kglobalaccel (src/bwm-kglobalaccel): KDE global shortcuts that BWM\n"
        "-- does not use. Loaded by modules/kde_shortcuts.lua in Breeze only. Do not edit.\n"
        "local trigger = %1\n"
        "local binds = _G.bwm_kde_binds or {}\n"
        "_G.bwm_kde_binds = binds\n"
        "local function add(spec, code, desc)\n"
        "    binds[spec] = {\n"
        "        hl.bind(spec, hl.dsp.exec_cmd(trigger .. \" press \" .. code), { description = desc }),\n"
        "        hl.bind(spec, hl.dsp.exec_cmd(trigger .. \" release \" .. code), { release = true, description = desc }),\n"
        "    }\n"
        "end\n")
                       .arg(luaString(QCoreApplication::applicationFilePath() + QStringLiteral(" --trigger")));
    for (const QString &spec : std::as_const(keys)) {
        for (auto it = binds.cbegin(); it != binds.cend(); ++it) {
            if (BwmKeymap::spec(it.key()) != spec)
                continue;
            text += QStringLiteral("add(%1, %2, %3)\n").arg(luaString(spec)).arg(it.value().first).arg(luaString(OwnPrefix + it.value().second));
        }
    }
    return text;
}

void Controller::apply(const QString &stateText, const QSet<QString> &bwmSpecs)
{
    const QString path = statePath();
    QDir().mkpath(QFileInfo(path).absolutePath());
    QSaveFile state(path);
    if (!state.open(QIODevice::WriteOnly) || state.write(stateText.toUtf8()) < 0 || !state.commit()) {
        m_lastError = QStringLiteral("cannot write ") + path;
        return;
    }
    // Hyprland removes binds by modifiers+key: one also used by BWM is only disabled, never
    // removed, so BWM's own bind (same key, added after a reload) is never touched.
    // Hyprland 0.56.2 crashes (SIGSEGV) on :remove()/:set_enabled() of an expired keybind
    // object (LuaKeybind.cpp checks an always-engaged std::optional, then dereferences a null
    // pointer). Removing the press bind also removes the release bind of the same key, so we
    // never call methods on our refs to remove them (hl.unbind by key string instead) and only
    // disable refs whose tostring() — safe on expired objects — says they are alive.
    QStringList taken;
    for (const QString &spec : bwmSpecs)
        taken << QStringLiteral("[%1]=true").arg(luaString(spec));
    QString script = QStringLiteral("local bwm = {%1}\n"
                                    "for spec, refs in pairs(_G.bwm_kde_binds or {}) do\n"
                                    "    if bwm[spec] then\n"
                                    "        for _, b in ipairs(refs) do\n"
                                    "            if tostring(b) ~= \"HL.Keybind(expired)\" then b:set_enabled(false) end\n"
                                    "        end\n"
                                    "    else\n"
                                    "        hl.unbind(spec)\n"
                                    "    end\n"
                                    "end\n"
                                    "_G.bwm_kde_binds = {}\n")
                         .arg(taken.join(u','));
    if (!stateText.isEmpty())
        script += QStringLiteral("dofile(%1)\n").arg(luaString(path));
    const QString scriptPath = QFileInfo(path).absolutePath() + QStringLiteral("/kde-shortcuts-apply.lua");
    QSaveFile apply(scriptPath);
    if (!apply.open(QIODevice::WriteOnly) || apply.write(script.toUtf8()) < 0 || !apply.commit()) {
        m_lastError = QStringLiteral("cannot write ") + scriptPath;
        return;
    }
    if (!runHyprctl({QStringLiteral("eval"), QStringLiteral("dofile(%1)").arg(luaString(scriptPath))}, 2000)) {
        m_lastError = QStringLiteral("hyprctl eval failed");
        return;
    }
    m_lastState = stateText;
    m_lastError.clear();
}

void Controller::shutdown()
{
    m_syncTimer.stop();
    m_bound.clear();
    apply(QString(), m_bwmSpecs);
    QFile::remove(statePath());
    m_server.close();
}

QJsonObject Controller::status() const
{
    QJsonArray bound;
    for (auto it = m_bound.cbegin(); it != m_bound.cend(); ++it)
        bound.append(QJsonObject{{QStringLiteral("key"), BwmKeymap::spec(it.key())}, {QStringLiteral("action"), it.value().second}});
    // KDE actions whose default key is taken by BWM: shown unassigned (in conflict).
    QJsonArray conflicts;
    for (const QStringList &component : m_daemon->allMainComponents()) {
        if (component.value(0) == BwmComponent)
            continue;
        for (const QStringList &action : m_daemon->allActionsForComponent(component)) {
            const QSet<QKeySequence> active = m_daemon->shortcutKeys(action);
            for (const QKeySequence &sequence : m_daemon->defaultShortcutKeys(action)) {
                if (sequence.count() != 1 || active.contains(sequence))
                    continue;
                const auto hk = BwmKeymap::fromQt(sequence[0].toCombined());
                if (hk && m_bwmKeys.contains(*hk))
                    conflicts.append(QJsonObject{{QStringLiteral("component"), action.value(0)},
                                                 {QStringLiteral("action"), action.value(1)},
                                                 {QStringLiteral("key"), BwmKeymap::spec(*hk)}});
            }
        }
    }
    return {{QStringLiteral("running"), true},
            {QStringLiteral("pid"), qint64(QCoreApplication::applicationPid())},
            {QStringLiteral("syncs"), m_syncs},
            {QStringLiteral("triggers"), m_triggers},
            {QStringLiteral("grabbed"), qsizetype(m_platform->grabbed().size())},
            {QStringLiteral("bwmKeys"), qsizetype(m_bwmKeys.size())},
            {QStringLiteral("bound"), bound},
            {QStringLiteral("conflicts"), conflicts},
            {QStringLiteral("state"), statePath()},
            {QStringLiteral("notices"), QJsonArray::fromStringList(m_notices)},
            {QStringLiteral("lastError"), m_lastError}};
}

void Controller::handleClient(QLocalSocket *socket)
{
    connect(socket, &QLocalSocket::disconnected, socket, &QObject::deleteLater);
    connect(socket, &QLocalSocket::readyRead, this, [this, socket] {
        while (socket->canReadLine()) {
            const QList<QByteArray> words = socket->readLine(256).trimmed().split(' ');
            const QByteArray command = words.value(0);
            if ((command == "press" || command == "release") && words.size() == 2) {
                bool ok = false;
                const int key = words.at(1).toInt(&ok);
                const bool handled = ok && m_platform->deliver(key, command == "press");
                if (handled && command == "press")
                    ++m_triggers;
                socket->write(handled ? "ok\n" : "ignored\n");
            } else if (command == "status") {
                socket->write(QJsonDocument(status()).toJson(QJsonDocument::Compact) + '\n');
            } else if (command == "sync") {
                scheduleSync();
                socket->write("ok\n");
            } else {
                socket->write("error\n");
            }
            socket->flush();
        }
    });
}

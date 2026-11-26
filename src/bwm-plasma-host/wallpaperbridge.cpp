// SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// apply() adapts ShellCorona::setWallpaper, plasma-workspace 6.7.5 (LGPL-2.0-or-later).
#include "wallpaperbridge.h"
#include "viewcorona.h"
#include "desktopviewhost.h"
#include "outputidentity.h"
#include <Plasma/Containment>
#include <KConfigGroup>
#include <KConfigLoader>
#include <KConfigPropertyMap>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QMetaProperty>
#include <QProcess>
#include <QQuickItem>
#include <QQuickItemGrabResult>
#include <QQuickWindow>
#include <QScreen>
#include <QStandardPaths>
#include <QUrl>
#include <QQmlComponent>
#include <QQmlEngine>

using namespace Qt::StringLiterals;

static QString screenDescription(QQuickWindow *view, const QString &fallback)
{
    if (!view || !view->screen()) return fallback;
    const auto id = BwmOutput::identity(view->screen());
    const auto desc = (id.manufacturer + u' ' + id.model + u' ' + id.serial).simplified();
    return desc.isEmpty() ? fallback : desc;
}

WallpaperBridge::WallpaperBridge(ViewCorona *corona, const QString &helper, QObject *parent)
    : QObject(parent), m_corona(corona), m_helper(helper)
{
    m_timer.setSingleShot(true);
    m_timer.setInterval(200);
    connect(&m_timer, &QTimer::timeout, this, &WallpaperBridge::refresh);
    connect(corona, &ViewCorona::wallpaperApplied, this, &WallpaperBridge::schedule);
    connect(corona, &ViewCorona::desktopViewBound, this, [this](Plasma::Containment *c) {
        auto *view = m_corona->viewForContainment(c);
        observe(c, screenDescription(view, view && view->screen() ? u"runtime:"_s + view->screen()->name() : QString()));
    });
    connect(qGuiApp, &QGuiApplication::primaryScreenChanged, this, &WallpaperBridge::schedule);
}

// ShellCorona::setWallpaper, plasma-workspace 6.7.5 (LGPL-2.0-or-later), also used
// by ContainmentConfigView. Write through the original schema/property map, never appletsrc text.
bool WallpaperBridge::apply(Plasma::Containment *c, const QString &plugin, const QVariantMap &params, bool checkOnly)
{
    if (!c || c->destroyed() || (c->immutability() != Plasma::Types::Mutable && plugin != c->wallpaperPlugin())) return false;
    KConfigPropertyMap *config = nullptr;
    std::unique_ptr<KConfigPropertyMap> owned;
    if (plugin != c->wallpaperPlugin() || !c->property("wallpaperGraphicsObject").value<QObject *>()) {
        auto pkg = KPackage::PackageLoader::self()->loadPackage(u"Plasma/Wallpaper"_s, plugin);
        QFile file(pkg.filePath("config", u"main.xml"_s));
        if (!pkg.isValid() || !file.exists()) return false;
        auto *loader = new KConfigLoader(c->config().group(u"Wallpaper"_s).group(plugin), &file);
        owned = std::make_unique<KConfigPropertyMap>(loader);
        loader->setParent(owned.get());
        config = owned.get();
    } else {
        config = qobject_cast<KConfigPropertyMap *>(c->property("wallpaperGraphicsObject").value<QObject *>()->property("configuration").value<QObject *>());
    }
    if (!config) return false;
    for (auto it = params.cbegin(); it != params.cend(); ++it) {
        if (!config->contains(it.key()) || config->isImmutable(it.key())) return false;
    }
    if (checkOnly) return true;
    for (auto it = params.cbegin(); it != params.cend(); ++it) config->insert(it.key(), it.value());
    config->writeConfig();
    c->setWallpaperPlugin(plugin);
    c->config().sync();
    return true;
}

void WallpaperBridge::observe(Plasma::Containment *c, const QString &description)
{
    if (!c) return;
    if (m_descriptions.contains(c)) { m_descriptions[c] = description; schedule(); return; }
    m_descriptions.insert(c, description);
    if (auto *view = m_corona->viewForContainment(c)) {
        connect(view, &QWindow::screenChanged, this, &WallpaperBridge::schedule);
        connect(view, &QWindow::visibleChanged, this, &WallpaperBridge::schedule);
        if (auto *desktop = qobject_cast<DesktopViewHost *>(view))
            connect(desktop, &DesktopViewHost::screenToFollowChanged, this, &WallpaperBridge::schedule);
    }
    connect(c, &Plasma::Containment::wallpaperPluginChanged, this, &WallpaperBridge::schedule);
    connect(c, &Plasma::Containment::wallpaperGraphicsObjectChanged, this, [this, c] { observeItem(c); schedule(); });
    connect(c, &QObject::destroyed, this, [this, c] {
        m_descriptions.remove(c); m_items.remove(c); m_states.remove(c); m_revisions.remove(c); schedule();
    });
    observeItem(c);
    schedule();
}

void WallpaperBridge::observeItem(Plasma::Containment *c)
{
    QObject *item = c->property("wallpaperGraphicsObject").value<QObject *>();
    if (m_items.value(c) == item) return;
    if (m_items.value(c)) disconnect(m_items.value(c), nullptr, this, nullptr);
    m_items[c] = item;
    if (!item) return;
    const auto slot = metaObject()->method(metaObject()->indexOfSlot("schedule()"));
    for (const char *key : {"loading", "accentColor"}) {
        const int p = item->metaObject()->indexOfProperty(key);
        if (p >= 0 && item->metaObject()->property(p).hasNotifySignal())
            connect(item, item->metaObject()->property(p).notifySignal(), this, slot);
    }
    if (auto *map = item->property("configuration").value<QObject *>()) {
        // Image changes include slideshow advancement and drag-and-drop. PreviewImage
        // is intentionally excluded: merely previewing in the config dialog is not Apply.
        for (const char *key : {"Image", "Video", "Poster"}) {
            const int p = map->metaObject()->indexOfProperty(key);
            if (p >= 0) connect(map, map->metaObject()->property(p).notifySignal(), this, slot);
        }
    }
}

void WallpaperBridge::schedule() { m_timer.start(); }

bool WallpaperBridge::setWallpaper(const QJsonObject &request)
{
    const QString source = request.value("source").toString();
    const QString still = request.value("still").toString(source);
    if (!QFileInfo(source).isFile() || !QFileInfo(still).isFile() || !QDir::isAbsolutePath(source)) return false;
    const bool video = request.value("video").toBool();
    if (video) {
        QQmlEngine engine;
        QQmlComponent probe(&engine);
        probe.setData("import QtQuick\nimport QtMultimedia\nItem {}", QUrl());
        if (probe.isError()) return false; // optional module absent: retain the normal fallback
    }
    const QString plugin = video ? u"org.bwm.video"_s : u"org.kde.image"_s;
    const QVariantMap params = video ? QVariantMap{{u"Video"_s, QUrl::fromLocalFile(source)}, {u"Poster"_s, QUrl::fromLocalFile(still)}}
                                    : QVariantMap{{u"Image"_s, QUrl::fromLocalFile(source).toString()}, {u"PreviewImage"_s, u"null"_s}};
    QList<Plasma::Containment *> targets;
    for (auto it = m_descriptions.cbegin(); it != m_descriptions.cend(); ++it) {
        auto *view = m_corona->viewForContainment(it.key());
        if (!view) continue;
        if (!request.value("screen").toString().isEmpty() && request.value("screen").toString() != screenDescription(view, it.value())) continue;
        targets.append(it.key());
    }
    // A locked output must not leave the other outputs partially changed.
    for (auto *c : targets) if (!apply(c, plugin, params, true)) return false;
    for (auto *c : targets) if (!apply(c, plugin, params)) return false;
    schedule();
    return !targets.isEmpty();
}

QJsonObject WallpaperBridge::status() const
{
    QJsonArray screens;
    QList<Plasma::Containment *> keys = m_states.keys();
    std::sort(keys.begin(), keys.end(), [](auto *a, auto *b) { return a->id() < b->id(); });
    for (auto *c : keys) screens.append(m_states.value(c));
    return {{"version", 1}, {"hostPid", qint64(QCoreApplication::applicationPid())}, {"screens", screens}};
}

void WallpaperBridge::refresh()
{
    for (auto it = m_descriptions.cbegin(); it != m_descriptions.cend(); ++it) {
        auto *c = it.key();
        auto *view = m_corona->viewForContainment(c);
        auto *item = qobject_cast<QQuickItem *>(c->property("wallpaperGraphicsObject").value<QObject *>());
        if (!view || !item || !view->isVisible()) { m_states.remove(c); continue; }
        const quint64 revision = ++m_revisions[c];
        const auto *map = qobject_cast<QQmlPropertyMap *>(item->property("configuration").value<QObject *>());
        const QString plugin = c->wallpaperPlugin();
        auto localFile = [](const QVariant &v) {
            QUrl url(v.toString());
            const QString path = url.isLocalFile() ? url.toLocalFile() : (url.scheme().isEmpty() ? v.toString() : QString());
            return QFileInfo(path).isFile() ? QFileInfo(path).absoluteFilePath() : QString();
        };
        QString source, still;
        if (map && (plugin == u"org.kde.image"_s || plugin == u"org.kde.slideshow"_s))
            source = still = localFile(map->value(u"Image"_s));
        if (map && plugin == u"org.bwm.video"_s) {
            source = localFile(map->value(u"Video"_s)); still = localFile(map->value(u"Poster"_s));
        }
        QJsonObject state{{"containment", int(c->id())}, {"screen", screenDescription(view, it.value())}, {"plugin", plugin},
                          {"primary", view->screen() == QGuiApplication::primaryScreen()}, {"source", source}, {"still", still}};
        if (!still.isEmpty()) { m_states[c] = state; continue; }
        if (item->property("loading").toBool()) continue;
        // Render only the wallpaper subtree. A plugin with no local image exports a
        // still when applied/loaded, never continuously for every video frame.
        auto grab = item->grabToImage(QSize(1280, 720));
        if (!grab) continue;
        QPointer<Plasma::Containment> guard(c);
        connect(grab.get(), &QQuickItemGrabResult::ready, this, [this, grab, guard, revision, state]() mutable {
            if (!guard || m_revisions.value(guard) != revision) return;
            const QImage image = grab->image();
            if (image.isNull()) return;
            const auto hash = QCryptographicHash::hash(QByteArrayView(reinterpret_cast<const char *>(image.constBits()), image.sizeInBytes()), QCryptographicHash::Sha256).toHex();
            const QString dir = QStandardPaths::writableLocation(QStandardPaths::GenericCacheLocation) + u"/bwm/plasma-wallpaper"_s;
            QDir().mkpath(dir);
            const QString path = dir + u'/' + QString::fromLatin1(hash) + u".png"_s;
            if (!QFileInfo::exists(path) && !image.save(path)) return;
            state["still"] = path;
            if (state.value("source").toString().isEmpty()) state["source"] = path;
            m_states[guard] = state;
            publish();
        });
    }
    publish();
}

void WallpaperBridge::publish()
{
    Q_EMIT changed();
    if (m_helper.isEmpty() || m_export) return;
    const QByteArray payload = QJsonDocument(status()).toJson(QJsonDocument::Compact);
    if (payload == m_exported || m_states.isEmpty()) return;
    auto *process = new QProcess(this);
    m_export = process;
    process->setProcessChannelMode(QProcess::ForwardedErrorChannel);
    auto complete = [this, process, payload](bool ok) {
        if (m_export != process) return;
        if (ok) m_exported = payload;
        m_export = nullptr;
        process->deleteLater();
        if (ok) QTimer::singleShot(0, this, &WallpaperBridge::publish);
    };
    connect(process, &QProcess::errorOccurred, this, [complete](auto error) { if (error == QProcess::FailedToStart) complete(false); });
    connect(process, &QProcess::finished, this, [complete](int code, auto exit) { complete(code == 0 && exit == QProcess::NormalExit); });
    connect(process, &QProcess::started, this, [process, payload] { process->write(payload); process->closeWriteChannel(); });
    process->start(u"python3"_s, {m_helper, u"export"_s});
    QTimer::singleShot(10000, process, [process] { if (process->state() != QProcess::NotRunning) process->kill(); });
}

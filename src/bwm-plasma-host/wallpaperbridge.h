// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QJsonObject>
#include <QPointer>
#include <QTimer>
#include <QHash>
class ViewCorona;
class QProcess;
namespace Plasma { class Containment; }

// Plasma remains the authority; this exports only a still of our own wallpaper item.
// No screencopy, desktop icons or foreign windows enter the bridge.
class WallpaperBridge : public QObject {
    Q_OBJECT
public:
    explicit WallpaperBridge(ViewCorona *corona, const QString &helper = {}, QObject *parent = nullptr);
    void observe(Plasma::Containment *containment, const QString &description);
    bool setWallpaper(const QJsonObject &request);
    QJsonObject status() const;
    static bool apply(Plasma::Containment *, const QString &plugin, const QVariantMap &parameters, bool checkOnly = false);
public Q_SLOTS:
    void schedule();
Q_SIGNALS:
    void changed();
private:
    void observeItem(Plasma::Containment *);
    void refresh();
    void publish();
    ViewCorona *m_corona;
    QString m_helper;
    QTimer m_timer;
    QHash<Plasma::Containment *, QString> m_descriptions;
    QHash<Plasma::Containment *, QPointer<QObject>> m_items;
    QHash<Plasma::Containment *, QJsonObject> m_states;
    QHash<Plasma::Containment *, quint64> m_revisions;
    QPointer<QProcess> m_export;
    QByteArray m_exported;
};

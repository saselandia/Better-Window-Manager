// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <QDBusServiceWatcher>
#include <QJsonObject>
#include <QObject>
#include <QPointer>
#include <QQuickWindow>
#include <QSet>
#include <QString>

#include <notificationmanager/settings.h>

class NotificationHost : public QObject
{
    Q_OBJECT
public:
    explicit NotificationHost(QString dndStatePath = {}, QObject *parent = nullptr);
    ~NotificationHost() override;

    bool start();
    void stop();
    bool claimService();

    bool isValid() const;
    bool isInhibited() const;
    void setDoNotDisturb(bool enabled);
    void toggleDoNotDisturb();
    QJsonObject status() const;

    static bool isNotificationWindow(const QObject *object);

    // Exposed for unit testing of the screen/margin calculation.
    static QMargins popupMarginsForScreen(const QRect &screenGeometry, const QPoint &globalPos, const QSize &size);

Q_SIGNALS:
    void statusChanged();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private Q_SLOTS:
    void syncSenderWindow();

private:
    void adaptNotificationWindow(QQuickWindow *window, bool creatingSurface);
    void syncNotificationWindow(QQuickWindow *window, bool creatingSurface = false);
    void writeDndState();
    void removeDndState();

    QString m_dndStatePath;
    bool m_active = false;
    NotificationManager::Settings m_settings;
    QDBusServiceWatcher m_ownerWatcher;
    QSet<QQuickWindow *> m_observedWindows;
    QSet<QQuickWindow *> m_updatingWindows;
    QHash<QQuickWindow *, QPoint> m_requestedPos;
};

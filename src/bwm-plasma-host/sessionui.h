// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QJsonObject>
#include <QList>
#include <QPointer>
class QQuickView;
class SessionUi : public QObject {
    Q_OBJECT
public:
    explicit SessionUi(QString powerHelper,QObject *parent=nullptr);
    ~SessionUi() override;
    bool start();
    bool prompt(const QString &action);
    QJsonObject status()const;
    static QString logoutSource(const QString &package={});
public Q_SLOTS:
    void cancel();
    void logout();
    void halt();
    void reboot();
    void suspend(int type);
    void lock();
Q_SIGNALS:
    void closed();
protected:
    bool eventFilter(QObject *,QEvent *) override;
private:
    void execute(const QString &action);
    QString m_power,m_error;
    QList<QPointer<QQuickView>> m_views;
    quint64 m_generation=0;
    bool m_promptOwner=false,m_shutdownOwner=false,m_committed=false;
};

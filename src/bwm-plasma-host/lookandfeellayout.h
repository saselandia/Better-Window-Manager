// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QDBusContext>
#include <QJsonObject>
#include <functional>
class ViewCorona;
class LookAndFeelLayout : public QObject, protected QDBusContext {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.kde.PlasmaShell")
public:
    using Restart = std::function<bool(const QString &, const QString &)>;
    LookAndFeelLayout(ViewCorona *, QString legacy, QString current, std::function<void()> save, QObject *parent=nullptr, Restart restart={});
    ~LookAndFeelLayout() override;
    bool start();
    QJsonObject status() const { return m_status; }
    static QString prepare(const QString &package, const QString &source, const QString &shell);
public Q_SLOTS:
    Q_SCRIPTABLE bool immutable() const;
    Q_SCRIPTABLE void loadLookAndFeelDefaultLayout(const QString &package);
Q_SIGNALS:
    void restartRequested();
private:
    ViewCorona *m_corona;
    QString m_legacy,m_current;
    std::function<void()> m_save;
    Restart m_restart;
    QJsonObject m_status;
    bool m_registered=false,m_busy=false;
};

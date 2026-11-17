// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QProcess>
#include <QTimer>
#include <QStringList>
// One bridge inside the host, no service name or socket. Explicit opt-in only.
class DesktopBridge:public QObject {
    Q_OBJECT
public:
    DesktopBridge(QString runtime,QString program,QStringList prefix,QObject *parent=nullptr);
    ~DesktopBridge()override;
    bool showingDesktop()const{return m_active;}
    bool available()const{return m_available;}
    QString error()const{return m_error;}
    void setShowingDesktop(bool showing);
    bool refresh();
    bool setSuspended(bool suspended);
    static bool suspendAll(bool suspended);
Q_SIGNALS:
    void changed(bool showing);
private:
    void launch();
    QString m_runtime,m_program,m_error;
    QStringList m_prefix;
    bool m_active=false,m_available=false,m_desired=false,m_pending=false;
    bool m_suspended=false;
    QProcess m_process;
    QTimer m_poll,m_timeout;
};

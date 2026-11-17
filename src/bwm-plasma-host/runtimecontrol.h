// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QFileSystemWatcher>
#include <QTimer>
#include <QJsonObject>
#include <memory>
class PanelRuntime;
class QLockFile;
// Explicit preview control channel. Files are integration metadata in a private
// temporary directory, never an alternative to native Plasma configuration.
class RuntimeControl:public QObject {
    Q_OBJECT
public:
    RuntimeControl(PanelRuntime *runtime,QString directory,QString token,QObject *parent=nullptr);
    ~RuntimeControl()override;
    bool start();
    QString error()const{return m_error;}
    qint64 revision()const{return m_revision;}
Q_SIGNALS:
    void applied(qint64 revision);
    void stopRequested();
private:
    bool read();
    QPointer<PanelRuntime> m_runtime;
    QString m_directory,m_token,m_error;
    qint64 m_revision=-1;
    QJsonObject m_last;
    QFileSystemWatcher m_watcher;
    QTimer m_read;
    std::unique_ptr<QLockFile> m_lock;
    bool m_stopped=false;
    bool m_pendingRead=false;
};

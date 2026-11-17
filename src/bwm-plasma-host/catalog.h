// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QVariantList>
#include <QFileSystemWatcher>
#include <QTimer>
#include <QPointer>
namespace KNSWidgets { class Dialog; }
class KPluginMetaData;
class Catalog:public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList entries READ entries NOTIFY changed)
    Q_PROPERTY(QString error READ error NOTIFY changed)
public:
    Catalog();
    ~Catalog() override;
    QVariantList entries()const{return m_entries;}
    QString error()const{return m_error;}
    static QVariantList discover();
    // Dependency assessment, never a certificate that a discovered widget works.
    static QVariantMap runtimeAssessment(const KPluginMetaData &metadata);
    Q_INVOKABLE void refresh();
    Q_INVOKABLE void getNewWidgets();
Q_SIGNALS:
    void changed();
private:
    void updateWatches();
    QVariantList m_entries;
    QString m_error;
    QFileSystemWatcher m_watcher;
    QTimer m_debounce;
    QPointer<KNSWidgets::Dialog> m_download;
};

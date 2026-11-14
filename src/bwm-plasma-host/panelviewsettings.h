// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QVariantMap>
#include <QHash>
#include <QStringList>
class KConfig;
// Supported PanelView 6.7.5 keys in the ORIGINAL plasmashellrc hierarchy. No applet
// configuration, layout, shared BWM preference or package metadata is stored here.
class PanelViewSettings {
public:
    PanelViewSettings(QString fileName,uint containmentId,bool vertical,int screenExtent,QVariantMap defaults,bool nativeVisibility=false);
    bool reload();
    bool apply(const QVariantMap &changes);
    QVariantMap values()const{return m_values;}
    QString error()const{return m_error;}
    QString scope()const{return m_resolution;}
    bool ready()const{return m_ready;}
    QString lockPath()const;
private:
    struct Target {QStringList groups;QString key;};
    QList<Target> targets(const QString &key,bool readFallback=false)const;
    QStringList keys()const;
    bool read(KConfig &config,QVariantMap &values)const;
    bool validate(QVariantMap &values)const;
    QVariantList signature(KConfig &config,const QString &key)const;
    QString m_fileName,m_filePath,m_panel,m_resolution;
    QVariantMap m_defaults,m_values;
    QHash<QString,QVariantList> m_baseline;
    mutable QString m_error;
    bool m_ready=false;
    bool m_nativeVisibility=false;
    int m_screenExtent;
};

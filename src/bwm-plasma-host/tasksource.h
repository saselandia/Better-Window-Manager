// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <abstractwindowtasksmodel.h>
#include <QJsonObject>
#include <QDateTime>
#include <QUuid>
#include <tasktools.h>
#include <QTimer>
class BwmTaskSource:public TaskManager::AbstractWindowTasksModel {
    Q_OBJECT
public:
    static constexpr int ActionCapabilitiesRole=Qt::UserRole+4096;
    explicit BwmTaskSource(QObject *parent=nullptr);
    int rowCount(const QModelIndex &parent={})const override{return parent.isValid()?0:m_rows.size();}
    QModelIndex index(int row,int column=0,const QModelIndex &parent={})const override;
    QVariant data(const QModelIndex &index,int role=Qt::DisplayRole)const override;
    bool apply(const QJsonObject &snapshot);
    void clear();
    QJsonObject thumbnailTarget(const QUuid &uuid)const;
    void requestNewInstance(const QModelIndex &index)override;
    void requestOpenUrls(const QModelIndex &index,const QList<QUrl> &urls)override;
    void requestActivate(const QModelIndex &index)override;
    void requestToggleMinimized(const QModelIndex &index)override;
    void requestToggleMaximized(const QModelIndex &index)override;
    void requestToggleFullScreen(const QModelIndex &index)override;
    void requestClose(const QModelIndex &index)override;
    void requestMove(const QModelIndex &index)override;
    void requestResize(const QModelIndex &index)override;
    void requestToggleNoBorder(const QModelIndex &index)override;
    void requestToggleExcludeFromCapture(const QModelIndex &index)override;
Q_SIGNALS:
    void actionRequested(QJsonObject request);
private:
    struct Row {QString key;QJsonObject data;quintptr serial;QUuid uuid;QDateTime activated;mutable TaskManager::AppData app;mutable bool appDirty=false;};
    const Row *row(const QModelIndex &index)const;
    void request(const QModelIndex &index,const QString &action,const QJsonObject &extra={});
    void invalidateAppData();
    QList<Row> m_rows;
    quintptr m_next=1;
    QTimer m_metadata;
};

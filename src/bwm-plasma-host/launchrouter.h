// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <abstracttasksproxymodeliface.h>
#include <QIdentityProxyModel>
#include <QJsonObject>
#include <KService>
#include <KServiceAction>
// Same resolution/filtering as Backend::jumpListActions/tryDecodeApplicationsUrl
// of plasma-desktop 6.7.5 (applets/taskmanager/backend.cpp, GPL-2.0-or-later,
// Eike Hein), rebuilt with public KService/KDesktopFile APIs. Used to identify
// the original menu's QActions and, in the launch helper, to resolve the Action.
KService::Ptr nativeJumpListService(const QUrl &launcherUrl);
QList<KServiceAction> nativeJumpListActions(const QUrl &launcherUrl);
// Identity proxy inserted with public Qt/LibTaskManager APIs between KDE's
// TaskFilterProxyModel and ConcatenateTasksProxyModel. Pinned-launcher requests
// (no window) leave the disposable host through the BWM launch helper instead
// of LauncherTasksModel's in-process KIO job, which would inherit the preview's
// temporary XDG roots and private D-Bus. Every other request and every row/role
// passes through unchanged; window/startup rows keep their original sources.
class BwmLaunchRouter:public QIdentityProxyModel,public TaskManager::AbstractTasksProxyModelIface {
    Q_OBJECT
public:
    explicit BwmLaunchRouter(QObject *parent=nullptr);
    void requestActivate(const QModelIndex &index)override;
    void requestNewInstance(const QModelIndex &index)override;
    void requestOpenUrls(const QModelIndex &index,const QList<QUrl> &urls)override;
    bool isLauncher(const QModelIndex &index)const;
Q_SIGNALS:
    void launchRequested(QJsonObject request);
    void launchRejected(QString reason);
protected:
    QModelIndex mapIfaceToSource(const QModelIndex &index)const override{return mapToSource(index);}
private:
    void route(const QModelIndex &index,const QList<QUrl> &urls);
};

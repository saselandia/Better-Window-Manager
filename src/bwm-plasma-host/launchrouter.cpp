// SPDX-License-Identifier: GPL-2.0-or-later
#include "launchrouter.h"
#include "tasklauncher.h"
#include <abstracttasksmodel.h>
#include <launchertasksmodel.h>
#include <QConcatenateTablesProxyModel>
#include <QJsonArray>
#include <KDesktopFile>

KService::Ptr nativeJumpListService(const QUrl &launcherUrl){
    if(!validNativeLauncherUrl(launcherUrl))return {};
    QUrl entry=launcherUrl;
    if(entry.scheme()=="applications"){if(const auto service=KService::serviceByMenuId(entry.path()))entry=QUrl::fromLocalFile(service->entryPath());}
    if(!entry.isValid() || !entry.isLocalFile() || !KDesktopFile::isDesktopFile(entry.toLocalFile()))return {};
    return KService::serviceByDesktopPath(entry.toLocalFile());
}
QList<KServiceAction> nativeJumpListActions(const QUrl &launcherUrl){
    QList<KServiceAction> visible;
    if(const auto service=nativeJumpListService(launcherUrl))
        for(const auto &action:service->actions())if(!action.noDisplay())visible.append(action);
    return visible;
}
BwmLaunchRouter::BwmLaunchRouter(QObject *parent):QIdentityProxyModel(parent){}
bool BwmLaunchRouter::isLauncher(const QModelIndex &index)const{
    if(!index.isValid() || index.model()!=this)return false;
    const auto *concat=qobject_cast<const QConcatenateTablesProxyModel*>(sourceModel());
    if(!concat)return false;
    const auto source=concat->mapToSource(mapToSource(index));
    return source.isValid() && qobject_cast<const TaskManager::LauncherTasksModel*>(source.model());
}
void BwmLaunchRouter::route(const QModelIndex &index,const QList<QUrl> &urls){
    // KDE LauncherTasksModel::requestActivate == requestNewInstance == runApp
    // without URLs; requestOpenUrls passes the dropped URLs.
    QString launcher;QJsonArray values;
    if(!validNativeLauncherUrl(index.data(TaskManager::AbstractTasksModel::LauncherUrlWithoutIcon).toUrl(),&launcher)){
        Q_EMIT launchRejected(QStringLiteral("Unsupported pinned launcher URL"));return;
    }
    if(!encodeNativeLaunchUrls(urls,values)){Q_EMIT launchRejected(QStringLiteral("Invalid launcher URLs"));return;}
    Q_EMIT launchRequested({{"version",1},{"action","launcher"},{"launcherUrl",launcher},{"urls",values}});
}
void BwmLaunchRouter::requestActivate(const QModelIndex &index){
    if(isLauncher(index))route(index,{});else AbstractTasksProxyModelIface::requestActivate(index);
}
void BwmLaunchRouter::requestNewInstance(const QModelIndex &index){
    if(isLauncher(index))route(index,{});else AbstractTasksProxyModelIface::requestNewInstance(index);
}
void BwmLaunchRouter::requestOpenUrls(const QModelIndex &index,const QList<QUrl> &urls){
    if(!isLauncher(index)){AbstractTasksProxyModelIface::requestOpenUrls(index,urls);return;}
    if(!urls.isEmpty())route(index,urls); // KDE ignores an empty drop.
}

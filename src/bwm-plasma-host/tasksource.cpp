// SPDX-License-Identifier: GPL-2.0-or-later
#include "tasksource.h"
#include "tasklauncher.h"
#include <QJsonArray>
#include <QIcon>
#include <QRegularExpression>
#include <QRect>
#include <QSet>
#include <QHash>
#include <KSycoca>
#include <cmath>
#include <limits>
namespace {
const QList<int> appRoles{Qt::DecorationRole,TaskManager::AbstractTasksModel::AppId,TaskManager::AbstractTasksModel::AppName,
    TaskManager::AbstractTasksModel::GenericName,TaskManager::AbstractTasksModel::LauncherUrl,TaskManager::AbstractTasksModel::LauncherUrlWithoutIcon,TaskManager::AbstractTasksModel::CanLaunchNewInstance};
TaskManager::AppData resolveAppData(const QJsonObject &d){
    return TaskManager::appDataFromUrl(TaskManager::windowUrlFromMetadata(d.value("appId").toString(),d.value("pid").toInt()),
        QIcon::fromTheme("application-x-executable"));
}
QRect rect(const QJsonValue &value){const auto a=value.toArray();return a.size()==4?QRect(a[0].toInt(),a[1].toInt(),a[2].toInt(),a[3].toInt()):QRect();}
bool validRect(const QJsonValue &value,bool empty=false){
    if(!value.isArray())return false;const auto a=value.toArray();if(empty && a.isEmpty())return true;
    if(a.size()!=4)return false;
    for(const auto &n:a)if(!n.isDouble() || !std::isfinite(n.toDouble()) || std::abs(n.toDouble())>std::numeric_limits<int>::max() || n.toDouble()!=n.toInt())return false;
    return a[2].toInt()>0 && a[3].toInt()>0;
}
}
BwmTaskSource::BwmTaskSource(QObject *parent):AbstractWindowTasksModel(parent){
    // Use the shared native database notification, as KDE's own source does.
    // Coalesce package changes and resolve metadata lazily when a view reads it.
    m_metadata.setParent(this);m_metadata.setSingleShot(true);m_metadata.setInterval(100);
    connect(KSycoca::self(),&KSycoca::databaseChanged,&m_metadata,qOverload<>(&QTimer::start));
    connect(&m_metadata,&QTimer::timeout,this,&BwmTaskSource::invalidateAppData);
}
void BwmTaskSource::invalidateAppData(){
    if(m_rows.isEmpty())return;
    for(auto &r:m_rows)r.appDirty=true;
    emit dataChanged(index(0),index(m_rows.size()-1),appRoles);
}
QModelIndex BwmTaskSource::index(int r,int column,const QModelIndex &parent)const {
    return !parent.isValid() && column==0 && r>=0 && r<m_rows.size()?createIndex(r,column,m_rows[r].serial):QModelIndex();
}
const BwmTaskSource::Row *BwmTaskSource::row(const QModelIndex &i)const {
    return i.isValid() && i.model()==this && i.column()==0 && i.row()>=0 && i.row()<m_rows.size() &&
        i.internalId()==m_rows[i.row()].serial ? &m_rows[i.row()]:nullptr;
}
QVariant BwmTaskSource::data(const QModelIndex &i,int role)const {
    const auto *r=row(i);if(!r)return {};const auto &d=r->data;
    if(r->appDirty && appRoles.contains(role)){r->app=resolveAppData(d);r->appDirty=false;}
    switch(role) {
    case ActionCapabilitiesRole:return QVariantMap{{"provider","org.bwm.window-actions"},{"version",1},{"identity",r->key},
        {"keepAbove",false},{"keepBelow",false},{"excludeFromCapture",d.value("windowTagsSettable").toBool()}};
    case Qt::DisplayRole:return d.value("title").toString();
    case Qt::DecorationRole:return r->app.icon;
    case AppId:return r->app.id.isEmpty()?d.value("appId").toString():r->app.id;
    case AppName:return r->app.name.isEmpty()?d.value("appId").toString():r->app.name;
    case GenericName:return r->app.genericName;
    case LauncherUrl:case LauncherUrlWithoutIcon:return r->app.url;
    case CanLaunchNewInstance:return nativeTaskCanLaunchNewInstance(r->app);
    case WinIdList:return QVariantList{r->uuid};
    case IsWindow:case IsGroupable:case IsClosable:case IsMinimizable:return true;
    case IsMaximizable:return !d.value("fullscreen").toBool();
    case IsActive:return d.value("active").toBool();
    case IsMinimized:case IsHidden:return d.value("minimized").toBool();
    case IsMaximized:return d.value("maximized").toBool();
    case IsFullScreen:return d.value("fullscreen").toBool();
    case IsFullScreenable:return d.value("fullscreenable").toBool();
    case IsMovable:case IsResizable:return d.value("movable").toBool();
    case HasNoBorder:return d.value("noBorder").toBool();
    case CanSetNoBorder:return d.value("windowTagsSettable").toBool();
    case IsExcludedFromCapture:return d.value("excludedFromCapture").toBool();
    case IsDemandingAttention:return d.value("urgent").toBool();
    case VirtualDesktops:return d.value("onAllDesktops").toBool()?QVariantList():QVariantList{d.value("workspace").toString()};
    case IsOnAllVirtualDesktops:return d.value("onAllDesktops").toBool();
    case Geometry:return rect(d.value("geometry"));
    case ScreenGeometry:return rect(d.value("screen"));
    case AppPid:return d.value("pid").toInt();
    case StackingOrder:return d.value("stackingOrder").toInt();
    case LastActivated:return r->activated;
    default:return AbstractTasksModel::data(i,role); // Unsupported action capabilities stay false.
    }
}
bool BwmTaskSource::apply(const QJsonObject &snapshot) {
    if(snapshot.value("version").toInt()!=1 || !snapshot.value("windows").isArray())return false;
    const auto values=snapshot.value("windows").toArray();if(values.size()>4096)return false;
    QHash<QString,QJsonObject> rows;QStringList order;QSet<QString> addresses;
    static const QRegularExpression address("^0x[0-9a-fA-F]+$"),generation("^[0-9]+$");
    for(const auto &value:values) {
        if(!value.isObject())return false;auto d=value.toObject();
        if(!address.match(d.value("address").toString()).hasMatch() || !generation.match(d.value("generation").toString()).hasMatch() ||
            !d.value("pid").isDouble() || d.value("pid").toInt()<=0 || d.value("pid").toDouble()!=d.value("pid").toInt() ||
            !d.value("title").isString() || !d.value("appId").isString() || d.value("workspace").toString().isEmpty())return false;
        for(const auto &flag:{"active","minimized","maximized","fullscreen","urgent","onAllDesktops"})if(!d.value(flag).isBool())return false;
        for(const auto &flag:{"fullscreenable","movable","windowTagsSettable","noBorder","excludedFromCapture"})
            if(d.contains(flag) && !d.value(flag).isBool())return false; // Optional v1 fields: absent = false.
        if(d.contains("stackingOrder")){
            const auto z=d.value("stackingOrder");
            if(!z.isDouble() || !std::isfinite(z.toDouble()) || z.toDouble()<0 ||
                z.toDouble()>std::numeric_limits<int>::max() || z.toDouble()!=z.toInt())return false;
        }else d.insert("stackingOrder",int(order.size())); // Legacy v1 snapshots: presentation-order fallback.
        if(!validRect(d.value("geometry")) || !validRect(d.value("screen"),true))return false;
        const auto addr=d.value("address").toString();if(addresses.contains(addr))return false;addresses.insert(addr);
        const auto key=addr+'|'+QString::number(d.value("pid").toInt())+'|'+d.value("generation").toString();rows.insert(key,d);order.append(key);
    }
    for(int i=m_rows.size()-1;i>=0;--i)if(!rows.contains(m_rows[i].key)) {beginRemoveRows({},i,i);m_rows.removeAt(i);endRemoveRows();}
    QSet<QString> present;
    for(int i=0;i<m_rows.size();++i) {
        auto &r=m_rows[i];const auto d=rows.value(r.key);present.insert(r.key);
        if(d!=r.data) {
            if(d.value("active").toBool() && !r.data.value("active").toBool())r.activated=QDateTime::currentDateTimeUtc();
            QList<int> roles;
            const auto changed=[&](const char *key,std::initializer_list<int> affected){if(d.value(key)!=r.data.value(key))for(int role:affected)roles.append(role);};
            changed("title",{Qt::DisplayRole});changed("appId",{AppId,AppName,GenericName,Qt::DecorationRole,LauncherUrl,LauncherUrlWithoutIcon});
            changed("active",{IsActive,LastActivated});changed("minimized",{IsMinimized,IsHidden});changed("maximized",{IsMaximized});
            changed("fullscreen",{IsFullScreen,IsMaximizable});changed("urgent",{IsDemandingAttention});changed("workspace",{VirtualDesktops});
            changed("fullscreenable",{IsFullScreenable});
            changed("movable",{IsMovable,IsResizable});changed("noBorder",{HasNoBorder});
            changed("windowTagsSettable",{CanSetNoBorder,ActionCapabilitiesRole});changed("excludedFromCapture",{IsExcludedFromCapture});
            changed("onAllDesktops",{VirtualDesktops,IsOnAllVirtualDesktops});
            changed("geometry",{Geometry});changed("screen",{ScreenGeometry});
            changed("stackingOrder",{StackingOrder});
            if(d.value("appId")!=r.data.value("appId")){r.app=resolveAppData(d);r.appDirty=false;}
            r.data=d;if(!roles.isEmpty())emit dataChanged(index(i),index(i),roles);
        }
    }
    for(const auto &key:order)if(!present.contains(key)) {
        const auto d=rows[key];const int i=m_rows.size();beginInsertRows({},i,i);
        const auto app=resolveAppData(d);
        m_rows.append({key,d,m_next++,QUuid::createUuid(),d.value("active").toBool()?QDateTime::currentDateTimeUtc():QDateTime(),app});endInsertRows();
    }
    return true;
}
void BwmTaskSource::clear(){while(!m_rows.isEmpty()){const int r=m_rows.size()-1;beginRemoveRows({},r,r);m_rows.removeLast();endRemoveRows();}}
QJsonObject BwmTaskSource::thumbnailTarget(const QUuid &uuid)const {
    if(uuid.isNull())return {};
    for(const auto &r:m_rows)if(r.uuid==uuid && !r.data.value("minimized").toBool()){
        bool normal=false;const int workspace=r.data.value("workspace").toString().toInt(&normal);
        if(!normal || workspace<=0 || workspace==99 || !validRect(r.data.value("screen")))return {};
        return {{"identity",r.key},{"address",r.data.value("address")}};
    }
    return {};
}
void BwmTaskSource::request(const QModelIndex &i,const QString &action,const QJsonObject &extra) {
    const auto *r=row(i);if(!r)return;
    QJsonObject request{{"version",1},{"action",action},
        {"address",r->data.value("address")},{"pid",r->data.value("pid")},{"generation",r->data.value("generation")}};
    for(auto it=extra.begin();it!=extra.end();++it)request.insert(it.key(),it.value());
    emit actionRequested(request);
}
void BwmTaskSource::requestNewInstance(const QModelIndex &i){
    const auto *r=row(i);if(!r)return;
    if(r->appDirty){r->app=resolveAppData(r->data);r->appDirty=false;}
    // Like WaylandTasksModel: CanLaunchNewInstance controls the generic menu
    // entry, not explicit requests (e.g. middle-click or a keyboard modifier).
    if(nativeTaskApplication(r->app))request(i,"new-instance");
}
void BwmTaskSource::requestOpenUrls(const QModelIndex &i,const QList<QUrl> &urls){
    const auto *r=row(i);if(!r || urls.isEmpty() || urls.size()>128)return;
    if(r->appDirty){r->app=resolveAppData(r->data);r->appDirty=false;}
    if(!nativeTaskApplication(r->app))return;
    QJsonArray values;if(!encodeNativeLaunchUrls(urls,values))return;
    request(i,"open-urls",{{"urls",values}});
}
void BwmTaskSource::requestActivate(const QModelIndex &i){request(i,"focus");}
void BwmTaskSource::requestToggleMinimized(const QModelIndex &i){request(i,"toggle-minimize");}
void BwmTaskSource::requestToggleMaximized(const QModelIndex &i){request(i,"maximize");}
void BwmTaskSource::requestToggleFullScreen(const QModelIndex &i){
    const auto *r=row(i);if(!r || !r->data.value("fullscreenable").toBool())return;
    request(i,"fullscreen",{{"state",!r->data.value("fullscreen").toBool()}});
}
void BwmTaskSource::requestClose(const QModelIndex &i){request(i,"close");}
void BwmTaskSource::requestMove(const QModelIndex &i){const auto *r=row(i);if(r && r->data.value("movable").toBool())request(i,"move");}
void BwmTaskSource::requestResize(const QModelIndex &i){const auto *r=row(i);if(r && r->data.value("movable").toBool())request(i,"resize");}
void BwmTaskSource::requestToggleNoBorder(const QModelIndex &i){
    const auto *r=row(i);if(!r || !r->data.value("windowTagsSettable").toBool())return;
    request(i,"no-border",{{"state",!r->data.value("noBorder").toBool()}}); // Desired state, never a blind toggle.
}
void BwmTaskSource::requestToggleExcludeFromCapture(const QModelIndex &i){
    const auto *r=row(i);if(!r || !r->data.value("windowTagsSettable").toBool())return;
    request(i,"no-capture",{{"state",!r->data.value("excludedFromCapture").toBool()}});
}

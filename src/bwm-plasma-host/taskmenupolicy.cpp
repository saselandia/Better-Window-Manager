// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskmenupolicy.h"
#include "tasksource.h"
#include "tasklauncher.h"
#include "launchrouter.h"
#include <QIcon>
#include <KFilePlacesModel>
#include <QJsonArray>
#include <memory>
#include <QApplication>
#include <QAbstractItemModel>
#include <QCryptographicHash>
#include <QFile>
#include <QMenu>
#include <QQuickItem>
#include <QQmlContext>
#include <QQmlEngine>
#include <QJSValue>
#include <QSet>
#include <QScopeGuard>
namespace {
QModelIndex modelIndex(QObject *context){
    auto value=context->property("modelIndex");
    if(value.metaType()==QMetaType::fromType<QJSValue>())value=value.value<QJSValue>().toVariant();
    return value.value<QModelIndex>();
}
QVariantMap capabilities(const QModelIndex &i){return i.data(BwmTaskSource::ActionCapabilitiesRole).toMap();}
bool isManaged(const QModelIndex &i){const auto c=capabilities(i);return i.isValid() && c.value("provider")=="org.bwm.window-actions" && c.value("version").toInt()==1;}
}
TaskMenuPolicy::TaskMenuPolicy(QObject *parent):QObject(parent){
    if(auto *app=QCoreApplication::instance())app->installEventFilter(this);
}
TaskMenuPolicy::~TaskMenuPolicy(){setSuspended(true);for(auto *action:m_masks.keys())unmask(action);if(auto *app=QCoreApplication::instance())app->removeEventFilter(this);}
void TaskMenuPolicy::attach(QObject *root){if(root && !m_roots.contains(root))m_roots.append(root);}
bool TaskMenuPolicy::owned(QObject *object)const{
    QSet<QObject*> seen;QList<QObject*> pending{object};
    while(!pending.isEmpty()){
        auto *current=pending.takeLast();if(!current || seen.contains(current))continue;seen.insert(current);
        for(const auto &root:m_roots)if(root==current)return true;
        pending.append(current->parent());if(auto *item=qobject_cast<QQuickItem*>(current))pending.append(item->parentItem());
    }
    return false;
}
QObject *TaskMenuPolicy::contextFor(QMenu *menu)const{
    for(auto *action:menu->actions())for(auto *p=action->parent();p;p=p->parent())
        if(p->inherits("QMenuProxy") && p->metaObject()->indexOfProperty("modelIndex")>=0 &&
           p->metaObject()->indexOfProperty("backend")>=0 && p->metaObject()->indexOfProperty("mpris2Source")>=0 && owned(p))return p;
    return nullptr;
}
bool TaskMenuPolicy::managed(const QModelIndex &index)const{
    if(!isManaged(index))return false;
    if(index.data(TaskManager::AbstractTasksModel::IsGroupParent).toBool()){
        const auto count=index.model()->rowCount(index);if(count<=0 || count>4096)return false;
        for(int r=0;r<count;++r)if(!managed(index.model()->index(r,0,index)))return false;
    }
    return true;
}
bool TaskMenuPolicy::allowed(const QModelIndex &index,const QString &operation)const{
    if(!managed(index))return false;
    if(index.data(TaskManager::AbstractTasksModel::IsGroupParent).toBool()){
        const auto count=index.model()->rowCount(index);if(count<=0 || count>4096)return false;
        for(int r=0;r<count;++r)if(!allowed(index.model()->index(r,0,index),operation))return false;
        return true;
    }
    return capabilities(index).value(operation).toBool();
}
void TaskMenuPolicy::release(QMenu *menu){
    if(!m_bound.contains(menu))return;
    // Detach before signals from restoring actions can reenter or destroy menus.
    const auto bound=m_bound.take(menu);
    for(const auto &connection:bound.connections)disconnect(connection);
    for(const auto &connection:bound.routed)disconnect(connection);
    for(const auto &action:bound.actions)if(action)unmask(action);
    if(bound.menu && bound.blocked)bound.menu->setEnabled(bound.previouslyEnabled);
}
void TaskMenuPolicy::unmask(QAction *action){
    const auto mask=m_masks.take(action);if(!mask.group)return;
    // Qt's removeAction alone does not recompute enabled. Re-enable this
    // single-action mask first, restoring the current explicit/native state.
    if(mask.action && mask.action->actionGroup()==mask.group){
        mask.group->setEnabled(true);
        if(mask.action)mask.group->removeAction(mask.action);
    }
    mask.group->deleteLater();
}
void TaskMenuPolicy::setSuspended(bool value){
    m_suspended=value;if(!value)return;
    for(auto *menu:m_bound.keys()){if(menu)menu->close();release(menu);}
}
bool TaskMenuPolicy::apply(QMenu *menu){
    if(!menu || m_applying.contains(menu))return false;
    m_applying.insert(menu);
    const auto applying=qScopeGuard([this,menu]{m_applying.remove(menu);});
    auto *context=contextFor(menu);const auto index=context?modelIndex(context):QModelIndex();
    const bool window=context && managed(index);
    const bool launcher=context && index.isValid() && index.data(TaskManager::AbstractTasksModel::IsLauncher).toBool();
    if(!window && !launcher){release(menu);return false;}
    if(m_suspended){menu->close();return true;}
    auto *qml=QQmlEngine::contextForObject(context);const auto source=qml?qml->resolvedUrl(QUrl(QStringLiteral("ContextMenu.qml"))):QUrl();
    QFile file(source.scheme()=="qrc"?":"+source.path():source.toLocalFile());
    const bool reviewed=file.open(QIODevice::ReadOnly) && QCryptographicHash::hash(file.readAll(),QCryptographicHash::Sha256).toHex()==QByteArrayLiteral(BWM_TASK_CONTEXT_SHA256);
    if(!m_bound.contains(menu)){
        Bound bound;bound.menu=menu;bound.index=index;
        auto *model=const_cast<QAbstractItemModel*>(index.model());
        const auto close=[guard=QPointer<QMenu>(menu)]{if(guard)guard->close();};
        bound.connections={connect(model,&QAbstractItemModel::rowsAboutToBeRemoved,this,close),
            connect(model,&QAbstractItemModel::rowsAboutToBeInserted,this,close),
            connect(model,&QAbstractItemModel::rowsAboutToBeMoved,this,close),
            connect(model,&QAbstractItemModel::modelAboutToBeReset,this,close),
            connect(model,&QAbstractItemModel::layoutAboutToBeChanged,this,close),
            connect(menu,&QObject::destroyed,this,[this,menu]{
                // QMenuProxy is already destroying its QWidget. Do not emit
                // enabled changes into a half-destroyed QML owner; actions
                // leave the disabled group themselves when they are deleted.
                auto i=m_bound.find(menu);if(i==m_bound.end())return;
                for(const auto &connection:i->connections)disconnect(connection);
                for(const auto &connection:i->routed)disconnect(connection);
                m_bound.erase(i);
            })};
        m_bound.insert(menu,bound);
    }
    auto &bound=m_bound[menu];
    if(!reviewed){m_error="Native task menu source changed or unavailable";if(!bound.blocked)bound.previouslyEnabled=menu->isEnabled();bound.blocked=true;menu->setEnabled(false);return true;}
    routeLaunchActions(menu,context,index);
    const QHash<QString,QString> operations{{"window-keep-above","keepAbove"},{"window-keep-below","keepBelow"},{"view-private","excludeFromCapture"}};
    if(window)for(auto *action:menu->actions()){
        auto *item=action->parent();if(!item || !item->inherits("QMenuItem"))continue;
        const auto operation=operations.value(item->property("icon").toString());if(operation.isEmpty())continue;
        if(allowed(index,operation)){unmask(action);continue;}
        if(action->actionGroup() && (!m_masks.contains(action) || action->actionGroup()!=m_masks.value(action).group)){
            m_error="Unsupported window action has a foreign group";if(!bound.blocked)bound.previouslyEnabled=menu->isEnabled();bound.blocked=true;menu->setEnabled(false);continue;
        }
        mask(action);
        if(!bound.actions.contains(action))bound.actions.append(action);
    }
    for(auto *action:menu->actions())if(action->menu())apply(action->menu());
    return true;
}
bool TaskMenuPolicy::mask(QAction *action){
    if(m_masks.contains(action))return true;
    if(action->actionGroup())return false;
    auto *group=new QActionGroup(this);group->setExclusive(false);group->setEnabled(false);group->addAction(action);
    m_masks.insert(action,{action,group});
    connect(action,&QObject::destroyed,this,[this,action]{const auto mask=m_masks.take(action);if(mask.group)mask.group->deleteLater();});
    return true;
}
namespace {
// Undo menu mnemonic markup: "&&" is a literal '&', a single '&' marks the
// accelerator that KDE's KAcceleratorManager inserts when the menu is shown.
QString withoutMnemonics(const QString &text){
    QString plain;plain.reserve(text.size());
    for(qsizetype i=0;i<text.size();++i){
        if(text.at(i)==QLatin1Char('&') && i+1<text.size()){++i;plain.append(text.at(i));continue;}
        if(text.at(i)!=QLatin1Char('&'))plain.append(text.at(i));
    }
    return plain;
}
// ContextMenu.qml 6.7.5 (reviewed by SHA256) shows Backend actions with
// TextMetrics.ElideRight after doubling '&'. Compare that presentation only.
bool sameJumpListEntry(const QAction *action,const KServiceAction &entry){
    if(action->isSeparator()!=entry.isSeparator() || action->menu())return false;
    if(entry.isSeparator())return true;
    if(action->icon().name()!=QIcon::fromTheme(entry.icon()).name())return false;
    const auto expected=entry.text(),actual=withoutMnemonics(action->text());
    if(actual==expected)return true;
    if(!actual.endsWith(QChar(0x2026)))return false;
    const auto prefix=actual.chopped(1);return !prefix.isEmpty() && expected.startsWith(prefix);
}
}
namespace {
bool sameTitle(const QAction *action,const QString &expected){
    const auto actual=withoutMnemonics(action->text());
    if(actual==expected)return true;
    if(!actual.endsWith(QChar(0x2026)))return false;
    const auto prefix=actual.chopped(1);return !prefix.isEmpty() && expected.startsWith(prefix);
}
struct Place {QString title,icon;QUrl url;};
// Same rows as Backend::placesActions (plasma-desktop 6.7.5): every non-hidden
// KFilePlacesModel entry. The host reads a read-only snapshot of the caller's
// user-places.xbel (preview-isolated.py), so titles/URLs are the user's.
QList<Place> visiblePlaces(){
    QList<Place> places;KFilePlacesModel model;
    for(int i=0;i<model.rowCount();++i){
        const auto index=model.index(i,0);if(model.isHidden(index))continue;
        places.append({index.data(Qt::DisplayRole).toString(),index.data(Qt::DecorationRole).value<QIcon>().name(),index.data(KFilePlacesModel::UrlRole).toUrl()});
    }
    return places;
}
}
void TaskMenuPolicy::routeLaunchActions(QMenu *menu,QObject *context,const QModelIndex &index){
    auto &bound=m_bound[menu];
    // QActions created by the original Backend for this menu are parented to
    // the ContextMenu object itself: Places/Recent Files sections and the
    // .desktop jump list (always last, top level). Declared QML items own their
    // actions; Places beyond the first group live in Backend-made submenus.
    QList<QAction*> created;bool topLevel=false;
    for(auto *action:menu->actions()){
        if(action->parent()==context)created.append(action);
        else if(action->parent() && action->parent()->inherits("QMenuItem"))topLevel=true;
    }
    if(created.isEmpty())return;
    const auto launcherUrl=index.data(TaskManager::AbstractTasksModel::LauncherUrlWithoutIcon).toUrl();
    const auto entries=topLevel?nativeJumpListActions(launcherUrl):QList<KServiceAction>();
    QString encoded;
    const bool denied=nativeInProcessLaunchDenied();
    const auto service=nativeJumpListService(launcherUrl);
    QString entryUrl;
    const bool launchable=denied && validNativeLauncherUrl(launcherUrl,&encoded) && service &&
        validNativeLauncherUrl(QUrl::fromLocalFile(service->entryPath()),&entryUrl);
    bool matched=launchable && !entries.isEmpty() && created.size()>=entries.size();
    const int first=entries.isEmpty()?created.size():created.size()-entries.size();
    for(int i=0;matched && i<entries.size();++i)if(!sameJumpListEntry(created.at(first+i),entries.at(i)))matched=false;
    if(!denied)m_error="In-process desktop launches are not denied; native launch actions masked";
    else if(!entries.isEmpty() && !matched)m_error="Jump-list actions do not match the desktop entry; masked";
    std::unique_ptr<QList<Place>> places;
    const auto routeOnce=[&](QAction *action,const QJsonObject &request){
        if(bound.routed.contains(action))return;
        // KDE's own handler stays connected; KIOSK denies its in-process job.
        bound.routed.insert(action,connect(action,&QAction::triggered,this,[this,request]{Q_EMIT launchRequested(request);}));
        ++m_routedActions;
    };
    for(int i=0;i<created.size();++i){
        auto *action=created.at(i);
        if(matched && i>=first){
            const auto &entry=entries.at(i-first);
            if(!entry.isSeparator())routeOnce(action,{{"version",1},{"action","service-action"},{"launcherUrl",encoded},{"serviceAction",entry.name()}});
            continue;
        }
        if(action->isSeparator() || action->menu())continue; // Place group submenus are applied on their own.
        // "N more Places…" only re-opens KDE's menu (Backend::showAllPlaces).
        if(topLevel && action->icon().name()==QStringLiteral("view-more-symbolic"))continue;
        if(launchable && !(matched && i>=first)){
            if(!places)places=std::make_unique<QList<Place>>(visiblePlaces());
            const Place *found=nullptr;int count=0;
            for(const auto &place:*places)if(place.icon==action->icon().name() && sameTitle(action,place.title)){found=&place;++count;}
            QJsonArray urls;
            if(count==1 && encodeNativeLaunchUrls({found->url},urls)){
                // Backend places lambda: ApplicationLauncherJob(service from the
                // .desktop path) with {url} — the helper's "launcher" request.
                routeOnce(action,{{"version",1},{"action","launcher"},{"launcherUrl",entryUrl},{"urls",urls}});
                unmask(action);bound.actions.removeAll(action);
                continue;
            }
        }
        // Recent Files need activity statistics from the caller's bus and are not
        // routed; unmatched or ambiguous entries stay visible but disabled.
        if(!m_masks.contains(action)){
            if(!mask(action)){m_error="Native launch action has a foreign group";if(!bound.blocked)bound.previouslyEnabled=menu->isEnabled();bound.blocked=true;menu->setEnabled(false);continue;}
            ++m_maskedLaunchActions;
        }
        if(!bound.actions.contains(action))bound.actions.append(action);
    }
}
bool TaskMenuPolicy::eventFilter(QObject *object,QEvent *event){
    if(event->type()==QEvent::Show)if(auto *menu=qobject_cast<QMenu*>(object))apply(menu);
    return QObject::eventFilter(object,event);
}
QVariantMap TaskMenuPolicy::state()const{
    return {{"scope","reviewed-native-task-menu-for-BWM-indices-and-pinned-launchers"},{"boundMenus",m_bound.size()},
        {"maskedActions",m_masks.size()},{"routedLaunchActions",m_routedActions},{"maskedLaunchActions",m_maskedLaunchActions},
        {"inProcessLaunchDenied",nativeInProcessLaunchDenied()},{"suspended",m_suspended},{"lastError",m_error},{"operationalVerified",false}};
}

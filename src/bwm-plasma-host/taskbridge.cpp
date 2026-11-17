// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskbridge.h"
#include "taskthumbnail.h"
#include <windowtasksmodel.h>
#include <concatenatetasksproxymodel.h>
#include "tasklauncher.h"
#include <tasksmodel.h>
#include <QAbstractProxyModel>
#include <QConcatenateTablesProxyModel>
#include <QCoreApplication>
#include <QFileInfo>
#include <QJsonDocument>
#include <QProcessEnvironment>
#include <QStandardPaths>
#include <QQuickItem>
#include <unistd.h>
#include <signal.h>
namespace {
QPointer<BwmTaskBridge> sharedBridge;
QSet<BwmTaskBridge*> bridges;
bool suspended=false;
void stop(QProcess &process){const auto pid=process.processId();if(pid>0 && ::getpgid(pid)==pid)::kill(-pid,SIGKILL);process.kill();}
}
BwmTaskBridge::BwmTaskBridge(QString runtime,QString config,QString program,QString helper,QObject *parent)
    :QObject(parent),m_runtime(std::move(runtime)),m_config(std::move(config)),m_program(std::move(program)),m_helper(std::move(helper)),m_source(this) {
    bridges.insert(this);m_suspended=suspended;
    m_menus.setSuspended(m_suspended);
    m_poll.setInterval(750);connect(&m_poll,&QTimer::timeout,this,&BwmTaskBridge::tick);
    for(auto *timer:{&m_snapshotTimeout,&m_actionTimeout}){timer->setSingleShot(true);timer->setInterval(8000);}
    connect(&m_snapshotTimeout,&QTimer::timeout,this,[this]{m_error="Task snapshot timed out";m_snapshotValid=false;stop(m_snapshot);m_source.clear();});
    connect(&m_actionTimeout,&QTimer::timeout,this,[this]{m_error="Task action timed out";m_actions.clear();stop(m_action);});
    for(auto *process:{&m_snapshot,&m_action}) {
        process->setChildProcessModifier([]{::setsid();});
        connect(process,&QProcess::errorOccurred,this,[this,process](QProcess::ProcessError error){
            if(error!=QProcess::FailedToStart)return;
            m_error="Task helper failed to start";
            if(process==&m_snapshot){m_snapshotTimeout.stop();m_snapshotValid=false;m_source.clear();}else{m_actionTimeout.stop();m_actions.clear();}
        });
    }
    connect(&m_snapshot,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),this,[this](int code,QProcess::ExitStatus status){
        m_snapshotTimeout.stop();const auto bytes=m_snapshot.readAllStandardOutput();
        if(!active()){m_snapshotValid=false;m_source.clear();return;}
        QJsonParseError error;const auto doc=QJsonDocument::fromJson(bytes,&error);
        if(code || status!=QProcess::NormalExit || bytes.size()>4*1024*1024 || error.error!=QJsonParseError::NoError ||
            !doc.isObject() || !m_source.apply(doc.object())) {m_error="Task snapshot unavailable or invalid";m_snapshotValid=false;m_source.clear();}
        else {m_snapshotValid=true;emit snapshotCommitted(m_snapshotSequence);}
    });
    connect(&m_action,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),this,[this](int code,QProcess::ExitStatus status){
        m_actionTimeout.stop();const auto bytes=m_action.readAllStandardOutput();
        QJsonParseError error;const auto result=QJsonDocument::fromJson(bytes,&error);
        if(code || status!=QProcess::NormalExit || bytes.size()>4096 || error.error!=QJsonParseError::NoError ||
            !result.isObject() || result.object().value("version").toInt()!=1 || !result.object().value("accepted").toBool()){
            m_error="Task action rejected or failed";m_actions.clear();
        }
        startAction();
    });
    connect(&m_source,&BwmTaskSource::actionRequested,this,&BwmTaskBridge::enqueue);
    // .desktop Actions from KDE's original task menu leave through the same
    // queue and launch helper; the in-process KDE job is denied by KIOSK.
    connect(&m_menus,&TaskMenuPolicy::launchRequested,this,&BwmTaskBridge::enqueue);
}
BwmTaskBridge::~BwmTaskBridge(){
    m_menus.setSuspended(true);
    bridges.remove(this);
    m_poll.stop();m_snapshotTimeout.stop();m_actionTimeout.stop();
    for(auto *process:{&m_snapshot,&m_action}){disconnect(process,nullptr,this,nullptr);if(process->state()!=QProcess::NotRunning){stop(*process);process->waitForFinished(1000);}}
    restore();
}
void BwmTaskBridge::enqueue(const QJsonObject &request){
    if(!m_snapshotValid || !active()){m_error="Task request dropped: native task source inactive";return;}
    if(m_actions.size()>=64){m_error="Too many pending task actions";return;}
    const auto kind=request.value("action").toString();
    m_actions.enqueue(request);
    if(kind=="launcher" || kind=="service-action"){++m_launchRequests;Q_EMIT launchQueued(request);}
    startAction();
}
void BwmTaskBridge::restore(){
    for(const auto &binding:m_bound)if(binding.target && binding.target->sourceModel()==&m_source)binding.target->setSourceModel(binding.previous);
    m_bound.clear();
    for(const auto &route:m_routes){
        if(route.filter && route.router && route.filter->sourceModel()==route.router)route.filter->setSourceModel(route.concat);
        if(route.router)route.router->deleteLater();
    }
    m_routes.clear();
}
void BwmTaskBridge::installRoutes(const QSet<QAbstractProxyModel*> &filters){
    for(auto it=m_routes.begin();it!=m_routes.end();){
        const auto route=it.value();
        if(route.filter && route.router && filters.contains(route.filter) && route.filter->sourceModel()==route.router &&
           route.router->sourceModel()==route.concat){++it;continue;}
        if(route.filter && route.router && route.filter->sourceModel()==route.router && route.concat)route.filter->setSourceModel(route.concat);
        if(route.router)route.router->deleteLater();
        it=m_routes.erase(it);
    }
    for(auto *filter:filters){
        if(m_routes.contains(filter))continue;
        auto *concat=qobject_cast<TaskManager::ConcatenateTasksProxyModel*>(filter->sourceModel());if(!concat)continue;
        auto *router=new BwmLaunchRouter(this);router->setSourceModel(concat);
        connect(router,&BwmLaunchRouter::launchRequested,this,&BwmTaskBridge::enqueue);
        connect(router,&BwmLaunchRouter::launchRejected,this,[this](const QString &reason){m_error=reason;});
        // Virtual QAbstractProxyModel::setSourceModel: TaskFilterProxyModel
        // re-resolves AbstractTasksModelIface on the router (public contract).
        filter->setSourceModel(router);
        m_routes.insert(filter,{filter,concat,router});
    }
}
void BwmTaskBridge::start(QProcess &process,const QString &operation){
    auto env=QProcessEnvironment::systemEnvironment();env.insert("XDG_RUNTIME_DIR",m_runtime);env.insert("XDG_CONFIG_HOME",m_config);
    process.setProcessEnvironment(env);process.setStandardErrorFile(QProcess::nullDevice());
    QStringList arguments{m_helper,operation=="launch"?QStringLiteral("action"):operation};
    if(operation=="launch")arguments<<"--launcher"<<QCoreApplication::applicationFilePath();
    process.start(m_program,arguments);
}
void BwmTaskBridge::attach(QObject *root){
    m_menus.attach(root);
    if(!root)return;for(const auto &old:m_roots)if(old==root)return;
    m_roots.append(root);if(!m_suspended)m_poll.start();QTimer::singleShot(0,this,&BwmTaskBridge::tick);
}
void BwmTaskBridge::discover(QAbstractItemModel *model,QSet<QAbstractItemModel*> &seen,QSet<TaskManager::WindowTasksModel*> &targets,QSet<QAbstractProxyModel*> &filters){
    if(!model || seen.contains(model))return;seen.insert(model);
    if(auto *windows=qobject_cast<TaskManager::WindowTasksModel*>(model)){targets.insert(windows);return;}
    if(auto *concat=qobject_cast<QConcatenateTablesProxyModel*>(model))for(auto *source:concat->sourceModels())discover(source,seen,targets,filters);
    if(auto *proxy=qobject_cast<QAbstractProxyModel*>(model)){
        // Only KDE's own filter → concatenation link of a TasksModel; third-party
        // proxy chains are left untouched (their in-process launches stay denied).
        auto *source=proxy->sourceModel();
        if(auto *router=qobject_cast<BwmLaunchRouter*>(source))source=router->sourceModel();
        if(QByteArray(proxy->metaObject()->className())=="TaskManager::TaskFilterProxyModel" &&
           qobject_cast<TaskManager::ConcatenateTasksProxyModel*>(source))filters.insert(proxy);
        discover(proxy->sourceModel(),seen,targets,filters);
    }
}
void BwmTaskBridge::tick(){
    if(m_suspended)return;
    QSet<QAbstractItemModel*> seen;QSet<TaskManager::WindowTasksModel*> targets;QSet<QAbstractProxyModel*> filters;
    QSet<QObject*> objects;
    QSet<TaskManager::TasksModel*> taskModels;
    for(int i=m_roots.size()-1;i>=0;--i) {
        auto *root=m_roots[i].data();if(!root){m_roots.removeAt(i);continue;}
        // AppletQuickItems keep QObject ownership outside the containment item.
        // The native panel reparents them visually, so QObject::findChildren
        // alone misses their TasksModels. Traverse both graphs without forcing
        // item creation or changing either ownership hierarchy.
        QList<QObject*> pending{root};
        while(!pending.isEmpty()){
            auto *object=pending.takeLast();if(!object || objects.contains(object))continue;
            objects.insert(object);
            if(auto *tasks=qobject_cast<TaskManager::TasksModel*>(object))taskModels.insert(tasks);
            if(auto *model=qobject_cast<QAbstractItemModel*>(object))discover(model,seen,targets,filters);
            for(auto *child:object->children())pending.append(child);
            if(auto *item=qobject_cast<QQuickItem*>(object))for(auto *child:item->childItems())pending.append(child);
        }
    }
    m_taskModels.clear();for(auto *tasks:taskModels)m_taskModels.append(tasks);
    for(auto it=m_bound.begin();it!=m_bound.end();) {
        if(!it.value().target || !targets.contains(it.key())){
            const auto binding=it.value();if(binding.target && binding.target->sourceModel()==&m_source)binding.target->setSourceModel(binding.previous);
            it=m_bound.erase(it);
        }else ++it;
    }
    for(auto *target:targets) {
        auto *previous=target->sourceModel();
        if(m_bound.contains(target) && previous==&m_source)continue;
        // A third-party widget may deliberately install another source. Keep it;
        // this adapter is for KDE's default Wayland source, not every proxy.
        m_bound.remove(target);
        if(previous && QByteArray(previous->metaObject()->className())!="TaskManager::WaylandTasksModel") {
            m_error="Custom task source left unchanged";continue;
        }
        m_bound.insert(target,{target,previous});target->setSourceModel(&m_source);
    }
    installRoutes(filters);
    if(m_bound.isEmpty()){m_actions.clear();m_snapshotValid=false;m_source.clear();if(m_roots.isEmpty())m_poll.stop();return;}
    if(m_snapshot.state()==QProcess::NotRunning){++m_snapshotSequence;start(m_snapshot,"snapshot");m_snapshotTimeout.start();}
}
void BwmTaskBridge::startAction(){
    if(!m_snapshotValid || !active()){m_actions.clear();return;}
    if(m_action.state()!=QProcess::NotRunning || m_actions.isEmpty())return;
    const auto request=m_actions.dequeue();const auto action=request.value("action").toString();
    start(m_action,action=="new-instance" || action=="open-urls" || action=="launcher" || action=="service-action"?"launch":"action");
    m_action.write(QJsonDocument(request).toJson(QJsonDocument::Compact));m_action.closeWriteChannel();m_actionTimeout.start();
}
bool BwmTaskBridge::active()const {
    if(m_suspended)return false;
    bool rootAlive=false;for(const auto &root:m_roots)if(root){rootAlive=true;break;}
    if(!rootAlive)return false;
    for(const auto &binding:m_bound)if(binding.target && binding.target->sourceModel()==&m_source)return true;
    return false;
}
void BwmTaskBridge::attachEnabled(QObject *root){
    if(qEnvironmentVariable("BWM_R4_TASK_ACTIONS")!="1")return;
    if(!sharedBridge){
        sharedBridge=new BwmTaskBridge(qEnvironmentVariable("BWM_R4_TASK_RUNTIME"),qEnvironmentVariable("BWM_R4_TASK_CONFIG"),
            QStandardPaths::findExecutable("python3"),QStringLiteral(BWM_TASK_HELPER_SOURCE),qApp);
        sharedBridge->setSuspended(suspended);
    }
    sharedBridge->attach(root);
}
bool BwmTaskBridge::setSuspended(bool value) {
    m_suspended=value;
    m_menus.setSuspended(value);
    if(value){
        m_poll.stop();m_actions.clear();m_snapshotValid=false;m_source.clear();m_snapshotTimeout.stop();
        if(m_snapshot.state()!=QProcess::NotRunning)stop(m_snapshot); // Read-only query, never a mutating action.
    }else if(!m_roots.isEmpty())m_poll.start();
    return m_action.state()==QProcess::NotRunning && m_snapshot.state()==QProcess::NotRunning;
}
bool BwmTaskBridge::suspendAll(bool value) {
    suspended=value;bool idle=true;
    for(auto *bridge:bridges)idle=bridge->setSuspended(value) && idle;
    return idle;
}
QVariantMap BwmTaskBridge::state()const {
    int views=0,desktopFilters=0,windowRows=0,launchers=0;
    for(const auto &tasks:m_taskModels)if(tasks){
        ++views;if(tasks->filterByCurrentVirtualDesktop())++desktopFilters;
        for(int r=0;r<tasks->rowCount();++r){
            const auto index=tasks->index(r,0);
            if(index.data(TaskManager::AbstractTasksModel::IsWindow).toBool() || index.data(TaskManager::AbstractTasksModel::IsGroupParent).toBool())++windowRows;
            if(index.data(TaskManager::AbstractTasksModel::IsLauncher).toBool())++launchers;
        }
    }
    return {{"enabled",true},{"scope","window-model-only"},{"boundModels",m_bound.size()},
        {"taskViewDiagnosticsVersion",1},{"viewModels",views},{"currentDesktopFilteringViews",desktopFilters},
        {"visibleWindowRows",windowRows},{"launcherRows",launchers},
        {"windowCount",m_source.rowCount()},{"snapshotAvailable",m_snapshotValid},
        {"suspended",m_suspended},{"actionInFlight",m_action.state()!=QProcess::NotRunning},
        {"snapshotInFlight",m_snapshot.state()!=QProcess::NotRunning},
        {"quiescent",m_actions.isEmpty() && m_action.state()==QProcess::NotRunning && m_snapshot.state()==QProcess::NotRunning},
        {"pendingActions",m_actions.size()},{"lastError",m_error},{"operationalVerified",false},
        {"menuPolicy",m_menus.state()},
        {"thumbnails",taskThumbnailDiagnostics()},
        {"applicationLauncher",QVariantMap{{"backend","KIO::ApplicationLauncherJob"},{"callerContextRequired",true},{"startupAcceptanceOnly",true},{"applicationReadinessVerified",false},
            {"pinnedLauncherRoutes",m_routes.size()},{"launchRequests",m_launchRequests},{"inProcessLaunchDenied",nativeInProcessLaunchDenied()}}},
        {"supportedActions",QStringList{"focus","toggle-minimize","maximize","close","fullscreen","new-instance","open-urls","launcher","service-action",
            "move","resize","no-border","no-capture"}},
        {"remaining",QStringList{"native desktop frontend/session acceptance","recent-document menu section (masked)",
            "keep-above/below (no Hyprland backend)","delegate geometry"}}};
}
QVariantMap BwmTaskBridge::diagnostics(){return sharedBridge?sharedBridge->state():QVariantMap{{"enabled",false},{"operationalVerified",false}};}
BwmTaskBridge *BwmTaskBridge::thumbnailBridge(){return sharedBridge && sharedBridge->active()?sharedBridge.data():nullptr;}

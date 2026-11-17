// SPDX-License-Identifier: GPL-2.0-or-later
#include "taskthumbnail.h"
#include "taskbridge.h"
#include "thumbnail-foreign-client.h"
#include "thumbnail-mapping-client.h"
#include "thumbnail-source-client.h"
#include "thumbnail-copy-client.h"
#include <QGuiApplication>
#include <QtGui/qguiapplication_platform.h>
#include <QPainter>
#include <QQuickWindow>
#include <QQuickRenderTarget>
#include <QQmlEngine>
#include <QQmlAbstractUrlInterceptor>
#include <QCryptographicHash>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QProcessEnvironment>
#include <QElapsedTimer>
#include <QPointer>
#include <QTimer>
#include <QTransform>
#include <QSet>
#include <wayland-client.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <unistd.h>
#include <functional>
#include <cerrno>
#include <cstring>
#include <vector>
namespace {
constexpr qint64 MaxBuffer=64*1024*1024,MaxTotal=128*1024*1024;
qint64 allocated=0;
int captures=0;
quint64 frames=0;
QString lastError;
bool guardedCompositor=false,syntheticFixture=false;
class ThumbnailWire:public QObject {
public:
    struct Entry {
        ThumbnailWire *wire;
        ext_foreign_toplevel_handle_v1 *handle=nullptr;
        hyprland_toplevel_window_mapping_handle_v1 *mapping=nullptr;
        quint64 address=0;
        bool closed=false;
        ~Entry(){if(mapping)hyprland_toplevel_window_mapping_handle_v1_destroy(mapping);if(handle)ext_foreign_toplevel_handle_v1_destroy(handle);}
    };
    wl_display *display=nullptr;
    wl_registry *registry=nullptr;
    wl_shm *shm=nullptr;
    ext_foreign_toplevel_list_v1 *list=nullptr;
    hyprland_toplevel_mapping_manager_v1 *mapping=nullptr;
    ext_foreign_toplevel_image_capture_source_manager_v1 *source=nullptr;
    ext_image_copy_capture_manager_v1 *copy=nullptr;
    std::vector<std::unique_ptr<Entry>> entries;
    QHash<quint32,QByteArray> globals;
    bool blocked=false;
    QTimer changed;
    explicit ThumbnailWire(QObject *parent):QObject(parent){
        changed.setSingleShot(true);changed.setInterval(0);
        auto *native=qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>();
        display=native?native->display():nullptr;if(!display)return;
        registry=wl_display_get_registry(display);
        static const wl_registry_listener listeners={global,removed};wl_registry_add_listener(registry,&listeners,this);
        wl_display_flush(display);
    }
    ~ThumbnailWire()override {
        entries.clear();
        if(copy)ext_image_copy_capture_manager_v1_destroy(copy);
        if(source)ext_foreign_toplevel_image_capture_source_manager_v1_destroy(source);
        if(mapping)hyprland_toplevel_mapping_manager_v1_destroy(mapping);
        if(list)ext_foreign_toplevel_list_v1_destroy(list);
        if(shm)wl_shm_destroy(shm);
        if(registry)wl_registry_destroy(registry);
    }
    bool ready()const{return (guardedCompositor || syntheticFixture) && !blocked && shm && list && mapping && source && copy;}
    static ThumbnailWire *instance(){static QPointer<ThumbnailWire> wire;if(!wire)wire=new ThumbnailWire(qApp);return wire;}
    void notify(){changed.start();}
    void map(Entry *entry){
        if(!mapping || entry->mapping || entry->closed || !entry->handle)return;
        entry->mapping=hyprland_toplevel_mapping_manager_v1_get_window_for_toplevel(mapping,entry->handle);
        static const hyprland_toplevel_window_mapping_handle_v1_listener listener={
            [](void *p,auto *,uint32_t hi,uint32_t lo){auto *e=static_cast<Entry*>(p);e->address=(quint64(hi)<<32)|lo;e->wire->notify();},
            [](void *p,auto *){auto *e=static_cast<Entry*>(p);e->closed=true;e->wire->notify();}};
        hyprland_toplevel_window_mapping_handle_v1_add_listener(entry->mapping,&listener,entry);
    }
    Entry *find(quint64 address)const {
        Entry *found=nullptr;
        for(const auto &e:entries)if(!e->closed && e->address==address){if(found)return nullptr;found=e.get();}
        return found;
    }
    static void global(void *p,wl_registry *registry,uint32_t name,const char *interface,uint32_t){
        auto *w=static_cast<ThumbnailWire*>(p);const QByteArray type(interface);
        const QSet<QByteArray> supported={"wl_shm","ext_foreign_toplevel_list_v1","hyprland_toplevel_mapping_manager_v1",
            "ext_foreign_toplevel_image_capture_source_manager_v1","ext_image_copy_capture_manager_v1"};
        if(!supported.contains(type))return;
        if(w->globals.values().contains(type)){w->blocked=true;lastError="Ambiguous capture protocol globals; restart preview";w->notify();return;}
        w->globals.insert(name,type);
        if(type=="wl_shm"){
            w->shm=static_cast<wl_shm*>(wl_registry_bind(registry,name,&wl_shm_interface,1));
            static const wl_shm_listener listener={[](void *,wl_shm *,uint32_t){}};wl_shm_add_listener(w->shm,&listener,w);
        }
        else if(type=="ext_foreign_toplevel_list_v1"){
            w->list=static_cast<ext_foreign_toplevel_list_v1*>(wl_registry_bind(registry,name,&ext_foreign_toplevel_list_v1_interface,1));
            static const ext_foreign_toplevel_list_v1_listener listeners={
                [](void *p,auto *,ext_foreign_toplevel_handle_v1 *handle){
                    auto *w=static_cast<ThumbnailWire*>(p);
                    if(w->entries.size()>=4096){ext_foreign_toplevel_handle_v1_destroy(handle);w->blocked=true;lastError="Capture handle budget exceeded; restart preview";w->notify();return;}
                    auto entry=std::make_unique<Entry>();entry->wire=w;entry->handle=handle;auto *e=entry.get();w->entries.push_back(std::move(entry));
                    static const ext_foreign_toplevel_handle_v1_listener listener={
                        [](void *p,auto *){auto *e=static_cast<Entry*>(p);e->closed=true;e->wire->notify();},
                        [](void *,auto *){},[](void *,auto *,const char *){},[](void *,auto *,const char *){},[](void *,auto *,const char *){}};
                    ext_foreign_toplevel_handle_v1_add_listener(handle,&listener,e);w->map(e);w->notify();
                },[](void *p,auto *){auto *w=static_cast<ThumbnailWire*>(p);w->blocked=true;w->notify();}};
            ext_foreign_toplevel_list_v1_add_listener(w->list,&listeners,w);
        }else if(type=="hyprland_toplevel_mapping_manager_v1"){
            w->mapping=static_cast<hyprland_toplevel_mapping_manager_v1*>(wl_registry_bind(registry,name,&hyprland_toplevel_mapping_manager_v1_interface,1));
            for(const auto &entry:w->entries)w->map(entry.get());
        }else if(type=="ext_foreign_toplevel_image_capture_source_manager_v1")
            w->source=static_cast<ext_foreign_toplevel_image_capture_source_manager_v1*>(wl_registry_bind(registry,name,&ext_foreign_toplevel_image_capture_source_manager_v1_interface,1));
        else if(type=="ext_image_copy_capture_manager_v1")w->copy=static_cast<ext_image_copy_capture_manager_v1*>(wl_registry_bind(registry,name,&ext_image_copy_capture_manager_v1_interface,1));
        w->notify();
    }
    static void removed(void *p,wl_registry *,uint32_t name){auto *w=static_cast<ThumbnailWire*>(p);if(w->globals.remove(name)){w->blocked=true;lastError="Capture global removed; restart preview";w->notify();}}
};
class Capture {
public:
    TaskThumbnail *item;
    ThumbnailWire *wire;
    ext_image_capture_source_v1 *source=nullptr;
    ext_image_copy_capture_session_v1 *session=nullptr;
    ext_image_copy_capture_frame_v1 *frame=nullptr;
    wl_buffer *buffer=nullptr;
    void *pixels=MAP_FAILED;
    qint64 bytes=0;
    uint32_t width=0,height=0,format=0,transform=0;
    uint32_t pendingWidth=0,pendingHeight=0,pendingFormat=0;
    bool formatsPending=false,hasFormat=false,stopped=false;
    QTimer next,timeout;
    Capture(TaskThumbnail *i,ThumbnailWire *w,ThumbnailWire::Entry *entry):item(i),wire(w){
        ++captures;next.setSingleShot(true);next.setInterval(250);timeout.setSingleShot(true);timeout.setInterval(2000);
        QObject::connect(&next,&QTimer::timeout,item,[this]{capture();});
        QObject::connect(&timeout,&QTimer::timeout,item,[this]{fail("Window capture timed out");});
        source=ext_foreign_toplevel_image_capture_source_manager_v1_create_source(wire->source,entry->handle);
        session=ext_image_copy_capture_manager_v1_create_session(wire->copy,source,0); // No cursor or output capture.
        static const ext_image_copy_capture_session_v1_listener listeners={
            [](void *p,auto *,uint32_t width,uint32_t height){auto *c=static_cast<Capture*>(p);c->constraints();c->pendingWidth=width;c->pendingHeight=height;},
            [](void *p,auto *,uint32_t format){auto *c=static_cast<Capture*>(p);c->constraints();if(TaskThumbnail::pixelFormat(format)!=QImage::Format_Invalid){c->pendingFormat=format;c->hasFormat=true;}},
            [](void *p,auto *,wl_array *){static_cast<Capture*>(p)->constraints();},
            [](void *p,auto *,uint32_t,wl_array *){static_cast<Capture*>(p)->constraints();},
            [](void *p,auto *){static_cast<Capture*>(p)->prepare();},
            [](void *p,auto *){static_cast<Capture*>(p)->fail("Window capture stopped");}};
        ext_image_copy_capture_session_v1_add_listener(session,&listeners,this);timeout.start();
        wl_display_flush(wire->display);
    }
    ~Capture(){--captures;next.stop();timeout.stop();releaseBuffer();if(session)ext_image_copy_capture_session_v1_destroy(session);if(source)ext_image_capture_source_v1_destroy(source);}
    void constraints(){if(!formatsPending){formatsPending=true;hasFormat=false;pendingWidth=width;pendingHeight=height;}}
    void releaseBuffer(){
        if(frame){ext_image_copy_capture_frame_v1_destroy(frame);frame=nullptr;}
        if(buffer){wl_buffer_destroy(buffer);buffer=nullptr;}
        if(pixels!=MAP_FAILED){munmap(pixels,size_t(bytes));pixels=MAP_FAILED;allocated-=bytes;bytes=0;}
    }
    void fail(const QString &reason){if(stopped)return;stopped=true;next.stop();timeout.stop();lastError=reason;item->captureFailed(reason);}
    void prepare(){
        if(stopped)return;formatsPending=false;next.stop();timeout.stop();releaseBuffer();
        if(!hasFormat || !TaskThumbnail::validBufferSize(pendingWidth,pendingHeight)){fail("No supported bounded shared-memory capture buffer");return;}
        width=pendingWidth;height=pendingHeight;format=pendingFormat;
        const qint64 size=qint64(width)*height*4;
        if(allocated+size>MaxTotal){fail("Window capture memory budget exceeded");return;}
        const int fd=memfd_create("bwm-task-thumbnail",MFD_CLOEXEC);
        if(fd<0){fail("Cannot allocate a window capture buffer");return;}
        if(ftruncate(fd,size)!=0){close(fd);fail("Cannot size window capture buffer");return;}
        pixels=mmap(nullptr,size_t(size),PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
        if(pixels==MAP_FAILED){close(fd);fail("Cannot map window capture buffer");return;}
        bytes=size;allocated+=bytes;
        auto *pool=wl_shm_create_pool(wire->shm,fd,int(size));close(fd);
        buffer=wl_shm_pool_create_buffer(pool,0,int(width),int(height),int(width*4),format);wl_shm_pool_destroy(pool);
        static const wl_buffer_listener listener={[](void *,wl_buffer *){}};wl_buffer_add_listener(buffer,&listener,this);
        capture();
    }
    void capture(){
        if(stopped || frame || !buffer)return;
        if(!wire->ready()){fail("Window capture provider unavailable");return;}
        frame=ext_image_copy_capture_session_v1_create_frame(session);transform=0;
        static const ext_image_copy_capture_frame_v1_listener listeners={
            [](void *p,auto *,uint32_t t){static_cast<Capture*>(p)->transform=t;},
            [](void *,auto *,int32_t,int32_t,int32_t,int32_t){},[](void *,auto *,uint32_t,uint32_t,uint32_t){},
            [](void *p,auto *){
                auto *c=static_cast<Capture*>(p);c->timeout.stop();ext_image_copy_capture_frame_v1_destroy(c->frame);c->frame=nullptr;
                const auto image=QImage(static_cast<uchar*>(c->pixels),int(c->width),int(c->height),int(c->width*4),
                    TaskThumbnail::pixelFormat(c->format));
                auto result=TaskThumbnail::transformed(image,c->transform);
                if(result.isNull()){c->fail("Invalid capture transform");return;}
                c->item->acceptFrame(result.scaled(512,512,Qt::KeepAspectRatio,Qt::SmoothTransformation).copy());++frames;c->next.start();
            },[](void *p,auto *,uint32_t reason){
                auto *c=static_cast<Capture*>(p);
                if(reason==EXT_IMAGE_COPY_CAPTURE_FRAME_V1_FAILURE_REASON_BUFFER_CONSTRAINTS){
                    ext_image_copy_capture_frame_v1_destroy(c->frame);c->frame=nullptr;c->timeout.start();
                }else c->fail("Window capture frame failed");
            }};
        ext_image_copy_capture_frame_v1_add_listener(frame,&listeners,this);
        ext_image_copy_capture_frame_v1_attach_buffer(frame,buffer);
        ext_image_copy_capture_frame_v1_damage_buffer(frame,0,0,int(width),int(height));
        ext_image_copy_capture_frame_v1_capture(frame);
        // Later frames legitimately wait for damage on a static window. Keep the
        // last image and the single pending frame until damage, hide or withdrawal.
        if(!item->ready())timeout.start();
        wl_display_flush(wire->display);
    }
};
class ThumbnailRedirect:public QQmlAbstractUrlInterceptor {
public:
    QUrl intercept(const QUrl &url,DataType type)override {
        if(type==QmlFile && url==QUrl("qrc:/qt/qml/plasma/applet/org/kde/plasma/taskmanager/PipeWireThumbnail.qml"))
            return QUrl::fromLocalFile(QStringLiteral(BWM_TASK_THUMBNAIL_QML));
        return url;
    }
};
}
struct TaskThumbnail::State {
    QPointer<BwmTaskBridge> bridge;
    QPointer<QQuickWindow> window;
    ThumbnailWire::Entry *entry=nullptr;
    QString identity;
    quint64 requiredSequence=0;
    std::unique_ptr<Capture> capture;
    QList<QMetaObject::Connection> connections;
    QMetaObject::Connection windowVisibility;
};
TaskThumbnail::TaskThumbnail(QQuickItem *parent):QQuickPaintedItem(parent),m_state(std::make_unique<State>()) {
    m_state->connections.append(connect(this,&QQuickItem::visibleChanged,this,&TaskThumbnail::reconsider));
    m_state->connections.append(connect(this,&QQuickItem::windowChanged,this,&TaskThumbnail::watchWindow));
    auto *wire=ThumbnailWire::instance();m_state->connections.append(connect(&wire->changed,&QTimer::timeout,this,&TaskThumbnail::reconsider));
    // A C++ parent can associate the window in the base constructor, before our
    // windowChanged connection exists. Observe that initial window as well.
    watchWindow(window());
    QTimer::singleShot(0,this,&TaskThumbnail::reconsider);
}
TaskThumbnail::~TaskThumbnail(){
    // QQuickItem's base destructor detaches from the window and emits signals.
    // QObject auto-disconnection happens later, after our State has been freed.
    // Disconnect our own callbacks while State is still alive; retain unrelated
    // destroyed/property connections that Qt/QML need for their normal cleanup.
    for(const auto &connection:m_state->connections)QObject::disconnect(connection);
    QObject::disconnect(m_state->windowVisibility);
    m_state->capture.reset();
}
void TaskThumbnail::watchWindow(QQuickWindow *window){
    QObject::disconnect(m_state->windowVisibility);m_state->window=window;
    if(window)m_state->windowVisibility=connect(window,&QWindow::visibleChanged,this,[this]{reconsider();});
    reconsider();
}
void TaskThumbnail::setUuid(const QString &uuid){if(m_uuid==uuid)return;m_uuid=uuid;m_failedIdentity.clear();resetCapture();emit uuidChanged();reconsider();}
void TaskThumbnail::resetCapture(){m_state->capture.reset();m_state->entry=nullptr;m_state->identity.clear();if(!m_image.isNull()){m_image={};emit readyChanged();update();}}
void TaskThumbnail::reconsider(){
    auto *wire=ThumbnailWire::instance();auto *bridge=BwmTaskBridge::thumbnailBridge();
    if(bridge && m_state->bridge!=bridge){
        if(m_state->bridge)disconnect(m_state->bridge,nullptr,this,nullptr);m_state->bridge=bridge;
        m_state->connections.append(connect(bridge,&BwmTaskBridge::snapshotCommitted,this,[this](quint64 sequence){
            reconsider();
            if(m_state->entry && !m_state->capture && sequence>=m_state->requiredSequence && captures<8)
                m_state->capture=std::make_unique<Capture>(this,ThumbnailWire::instance(),m_state->entry);
        }));
        m_state->connections.append(connect(bridge->source(),&QAbstractItemModel::rowsRemoved,this,[this]{reconsider();}));
        m_state->connections.append(connect(bridge->source(),&QAbstractItemModel::modelReset,this,[this]{reconsider();}));
    }
    const auto target=bridge?bridge->source()->thumbnailTarget(QUuid(m_uuid)):QJsonObject();
    const auto key=target.value("identity").toString();
    const bool presented=window() && (window()->isVisible() || !window()->renderTarget().isNull());
    if(!wire->ready() || !bridge || !isVisible() || !presented || key.isEmpty() || key==m_failedIdentity){resetCapture();return;}
    bool ok=false;const auto address=target.value("address").toString().toULongLong(&ok,16);
    auto *entry=ok?wire->find(address):nullptr;
    if(!entry || entry->closed){resetCapture();return;}
    if(m_state->entry==entry && m_state->identity==key)return;
    resetCapture();m_state->entry=entry;m_state->identity=key;
    // Bind the stable foreign handle first, then require a snapshot started after
    // that binding. Reused addresses/PIDs cannot select a different live window
    // using the old task identity. Subsequent captures keep the same handle.
    m_state->requiredSequence=bridge->snapshotSequence()+1;
    QTimer::singleShot(0,bridge,&BwmTaskBridge::tick);
}
void TaskThumbnail::acceptFrame(const QImage &image){m_image=image;emit readyChanged();update();}
void TaskThumbnail::captureFailed(const QString &){m_failedIdentity=m_state->identity;const auto key=m_failedIdentity;QTimer::singleShot(0,this,[this,key]{if(m_failedIdentity==key && m_state->identity==key)resetCapture();});}
void TaskThumbnail::paint(QPainter *p){if(m_image.isNull())return;const auto size=m_image.size().scaled(boundingRect().size().toSize(),Qt::KeepAspectRatio);p->setRenderHint(QPainter::SmoothPixmapTransform);p->drawImage(QRectF((width()-size.width())/2,(height()-size.height())/2,size.width(),size.height()),m_image);}
bool TaskThumbnail::validBufferSize(quint32 width,quint32 height){return width>0 && height>0 && width<=8192 && height<=8192 && qint64(width)*height*4<=MaxBuffer;}
QImage::Format TaskThumbnail::pixelFormat(quint32 format){
    switch(format){
    case WL_SHM_FORMAT_ARGB8888:return QImage::Format_ARGB32_Premultiplied;
    case WL_SHM_FORMAT_XRGB8888:return QImage::Format_RGB32;
    case WL_SHM_FORMAT_ABGR8888:return QImage::Format_RGBA8888_Premultiplied;
    case WL_SHM_FORMAT_XBGR8888:return QImage::Format_RGBX8888;
    case WL_SHM_FORMAT_ARGB2101010:return QImage::Format_A2RGB30_Premultiplied;
    case WL_SHM_FORMAT_XRGB2101010:return QImage::Format_RGB30;
    case WL_SHM_FORMAT_ABGR2101010:return QImage::Format_A2BGR30_Premultiplied;
    case WL_SHM_FORMAT_XBGR2101010:return QImage::Format_BGR30;
    default:return QImage::Format_Invalid;
    }
}
QImage TaskThumbnail::transformed(const QImage &image,quint32 transform){
    if(transform>7)return {};
    QTransform matrix;
    if(transform>=4)matrix.scale(-1,1);
    matrix.rotate((transform%4)*90);
    return image.transformed(matrix);
}
bool installTaskThumbnails(QQmlEngine *engine,QString *error){
    if(QGuiApplication::platformName()=="wayland"){
        const auto status=thumbnailCompositorGuardStatus();guardedCompositor=status.value("verified").toBool();
        if(!guardedCompositor){
            if(error)*error=QString("Window capture blocked: %1 (Wayland peer pid=%2, process=%3). %4 Guard BWM_SCREENSHARE_MONITOR_GUARD_V1 unverified; see docs/BREEZE_R4_THUMBNAILS.md.")
                .arg(status.value("reason").toString()).arg(status.value("peerPid").toInt())
                .arg(status.value("peerProcess").toString(),status.value("error").toString());
            return false;
        }
    }
    QFile original(":/qt/qml/plasma/applet/org/kde/plasma/taskmanager/PipeWireThumbnail.qml");
    if(!engine || !original.open(QIODevice::ReadOnly) || QCryptographicHash::hash(original.readAll(),QCryptographicHash::Sha256).toHex()!=
        QByteArrayLiteral("b76fc7105bb69bf00a1cad94533fc0292a6ca7171409ec89bee75d2f68077e6b")){
        if(error)*error="Unreviewed native PipeWireThumbnail.qml; capture adaptation blocked";return false;
    }
    qmlRegisterType<TaskThumbnail>("org.bwm.nativetasks",1,0,"WindowThumbnail");
    auto *redirect=new ThumbnailRedirect;engine->addUrlInterceptor(redirect);
    QObject::connect(engine,&QObject::destroyed,[redirect]{delete redirect;});ThumbnailWire::instance();return true;
}
QVariantMap taskThumbnailDiagnostics(){
    if(qEnvironmentVariable("BWM_R4_TASK_THUMBNAILS")!="1")return {{"enabled",false}};
    auto *wire=ThumbnailWire::instance();return {{"enabled",true},{"backend","ext-image-copy-capture-v1"},{"protocolsReady",wire->ready()},
        {"activeCaptures",captures},{"bufferBytes",allocated},{"frames",QVariant::fromValue(frames)},{"lastError",lastError},
        {"compositorMonitorGuardVerified",guardedCompositor},{"syntheticFixture",syntheticFixture},
        {"physicalCaptureVerified",false},{"outputsCaptured",false},{"framesWrittenToDisk",false}};
}
void allowSyntheticThumbnailFixtureForTest(){syntheticFixture=true;}
bool thumbnailGuardReportMatches(const QJsonObject &report,int expectedPeerPid){
    const auto version=report.value("version"),pid=report.value("pid");
    return expectedPeerPid>0 && version.isDouble() && version.toDouble()==1.0 &&
        pid.isDouble() && pid.toDouble()==double(expectedPeerPid);
}
QVariantMap thumbnailGuardIpcStatus(int expectedPeerPid,const QString &runtime){
    QVariantMap status{{"verified",false},{"verificationMethod","compositor-ipc"}};
    const auto fail=[&](const QString &reason){status.insert("reason",reason);return status;};
    if(expectedPeerPid<=0)return fail("ipc-invalid-expected-pid");
    QProcess process;
    auto env=QProcessEnvironment::systemEnvironment();
    if(!runtime.isEmpty())env.insert("XDG_RUNTIME_DIR",runtime);
    process.setProcessEnvironment(env);
    process.setStandardErrorFile(QProcess::nullDevice());
    process.start("hyprctl",{"-j","version"},QIODevice::ReadOnly);
    QElapsedTimer elapsed;elapsed.start();
    if(!process.waitForStarted(500))return fail("ipc-client-did-not-start");
    QByteArray bytes;
    while(true){
        bytes+=process.read(65537-bytes.size());
        if(bytes.size()>65536){process.kill();process.waitForFinished(500);return fail("ipc-response-exceeds-limit");}
        if(process.state()==QProcess::NotRunning)break;
        const int remaining=2000-int(elapsed.elapsed());
        if(remaining<=0){process.kill();process.waitForFinished(500);return fail("ipc-response-timed-out");}
        process.waitForReadyRead(qMin(remaining,50));
    }
    if(process.exitStatus()!=QProcess::NormalExit || process.exitCode()!=0)return fail("ipc-query-failed");
    QJsonParseError error;const auto document=QJsonDocument::fromJson(bytes,&error);
    if(error.error!=QJsonParseError::NoError || !document.isObject())return fail("ipc-invalid-json");
    const auto value=document.object().value("bwmScreenshareMonitorGuard");
    if(!value.isObject())return fail("ipc-report-missing-install-reporting-patch");
    const auto report=value.toObject();
    status.insert("reportedGuard",report.toVariantMap());
    if(!thumbnailGuardReportMatches(report,expectedPeerPid))return fail("ipc-report-does-not-match-wayland-peer");
    status.insert("verified",true);status.insert("reason","guard-reported-by-wayland-peer");return status;
}
QVariantMap thumbnailCompositorGuardStatus(){
    QVariantMap status{{"version",1},{"verified",false},{"capturesStarted",false},{"uid",uint(getuid())}};
    const auto fail=[&](const QString &reason,const QString &error=QString()){status.insert("reason",reason);if(!error.isEmpty())status.insert("error",error);return status;};
    auto *native=qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>();
    auto *display=native?native->display():nullptr;
    if(!display)return fail("no-native-wayland-display");
    ucred peer{};socklen_t size=sizeof(peer);
    if(getsockopt(wl_display_get_fd(display),SOL_SOCKET,SO_PEERCRED,&peer,&size)!=0 || size!=sizeof(peer))return fail("peer-credentials-unavailable",QString::fromLocal8Bit(strerror(errno)));
    status.insert("peerPid",peer.pid);status.insert("peerUid",uint(peer.uid));
    if(peer.pid<=0)return fail("peer-pid-unavailable");
    if(peer.uid!=getuid())return fail("peer-has-different-uid");
    QFile name(QString("/proc/%1/comm").arg(peer.pid));
    if(name.open(QIODevice::ReadOnly))status.insert("peerProcess",QString::fromLocal8Bit(name.readLine(256)).trimmed());
    // Keep direct attestation where /proc is readable; filecaps can deny it even
    // for the same UID. An installed executable is never a substitute.
    const auto inspect=[&]() -> QString {
        QFile executable(QString("/proc/%1/exe").arg(peer.pid));
        if(!executable.open(QIODevice::ReadOnly)){status.insert("executableError",executable.errorString());return "cannot-read-peer-executable";}
        const auto imageSize=executable.size();status.insert("loadedImageBytes",imageSize);
        status.insert("loadedImageDeleted",QFileInfo(executable.fileName()).symLinkTarget().endsWith(" (deleted)"));
        if(imageSize>512LL*1024*1024)return "peer-executable-exceeds-read-limit";
        const QByteArray marker="BWM_SCREENSHARE_MONITOR_GUARD_V1";QByteArray previous;qint64 read=0;
        while(true){
            const auto part=executable.read(1024*1024);
            if(part.isEmpty())break;
            read+=part.size();status.insert("loadedImageBytesRead",read);
            if((previous+part).contains(marker))return "guard-marker-present";
            previous=part.right(marker.size()-1);
        }
        if(executable.error()!=QFileDevice::NoError){status.insert("executableError",executable.errorString());return "peer-executable-read-failed";}
        return read?"guard-marker-not-found-in-loaded-image":"peer-executable-was-empty";
    };
    const auto inspected=inspect();status.insert("executableReason",inspected);
    if(inspected=="guard-marker-present"){
        status.insert("verified",true);status.insert("reason",inspected);status.insert("verificationMethod","peer-executable");return status;
    }
    auto runtime=qEnvironmentVariable("BWM_R4_TASK_RUNTIME");
    if(runtime.isEmpty())runtime=qEnvironmentVariable("BWM_R4_GUARD_RUNTIME");
    if(runtime.isEmpty())runtime=qEnvironmentVariable("XDG_RUNTIME_DIR");
    const auto ipc=thumbnailGuardIpcStatus(peer.pid,runtime);status.insert("ipc",ipc);
    status.insert("reason",ipc.value("reason"));
    if(ipc.value("verified").toBool()){status.insert("verified",true);status.insert("verificationMethod","compositor-ipc");}
    return status;
}

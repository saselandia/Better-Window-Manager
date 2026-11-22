// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// Controlled scene and frame sampler. Refuses every display except its fresh private peer.
#include <QGuiApplication>
#include <QQuickWindow>
#include <QTimer>
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusInterface>
#include <QDBusArgument>
#include <QDBusUnixFileDescriptor>
#include <QImage>
#include <LayerShellQt/Window>
#include <wayland-client.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <chrono>
#include <memory>
#include <cstring>
#include <iostream>
#include "r7-screencopy-client.h"

static void check(bool ok, const char *why) { if (!ok) qFatal("%s", why); }
static double now() { return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
static void jsonLine(QFile &file, const QJsonObject &value) {
    check(file.write(QJsonDocument(value).toJson(QJsonDocument::Compact) + '\n') > 0, "Cannot write sample"); file.flush();
}
static wl_display *privateDisplay(const QString &root) {
    check(root.startsWith(QDir::tempPath()+"/bwm-r7-"), "Not an R7 disposable root");
    for (auto key : {"XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"})
        check(QFileInfo(qEnvironmentVariable(key)).canonicalFilePath().startsWith(root+"/"), key);
    check(qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS").startsWith("unix:path="+root+"/"), "Not a private bus");
    const auto display = qEnvironmentVariable("WAYLAND_DISPLAY");
    check(display == qEnvironmentVariable("BWM_R7_DISPLAY"), "Wrong display");
    auto *peer = wl_display_connect(qPrintable(display)); check(peer, "Cannot connect private display");
    ucred credentials{}; socklen_t length = sizeof(credentials);
    check(getsockopt(wl_display_get_fd(peer), SOL_SOCKET, SO_PEERCRED, &credentials, &length) == 0 && credentials.uid == getuid()
          && credentials.pid == qEnvironmentVariableIntValue("BWM_R7_COMPOSITOR_PID"), "Display is not the fresh compositor");
    return peer;
}

struct Copy {
    wl_display *display; wl_shm *shm = nullptr; wl_output *output = nullptr;
    zwlr_screencopy_manager_v1 *manager = nullptr;
    wl_buffer *buffer = nullptr; void *memory = MAP_FAILED; size_t bytes = 0;
    uint32_t format = 0, width = 0, height = 0, stride = 0, flags = 0;
    bool done = false, failed = false; double presentation = 0; int rawCenterAlpha=255;
    explicit Copy(wl_display *d) : display(d) {
        auto *registry = wl_display_get_registry(display);
        const wl_registry_listener listener{[](void *p, wl_registry *r, uint32_t id, const char *interface, uint32_t version) {
            auto &s = *static_cast<Copy *>(p);
            if (!std::strcmp(interface, wl_shm_interface.name)) s.shm = static_cast<wl_shm *>(wl_registry_bind(r,id,&wl_shm_interface,1));
            if (!std::strcmp(interface, wl_output_interface.name) && !s.output) s.output = static_cast<wl_output *>(wl_registry_bind(r,id,&wl_output_interface,1));
            if (!std::strcmp(interface, zwlr_screencopy_manager_v1_interface.name)) s.manager = static_cast<zwlr_screencopy_manager_v1 *>(wl_registry_bind(r,id,&zwlr_screencopy_manager_v1_interface,std::min(2u,version)));
        }, [](void*,wl_registry*,uint32_t){}};
        wl_registry_add_listener(registry,&listener,this); check(wl_display_roundtrip(display)>=0,"No private globals");
        wl_registry_destroy(registry); check(shm && output && manager,"Private screencopy unavailable");
    }
    QImage capture() {
        done = failed = false; presentation = 0; flags = 0;
        auto *frame = zwlr_screencopy_manager_v1_capture_output(manager,0,output);
        const zwlr_screencopy_frame_v1_listener listener{
            [](void *p, zwlr_screencopy_frame_v1 *f, uint32_t format, uint32_t w, uint32_t h, uint32_t stride) {
                auto &s = *static_cast<Copy *>(p); s.format=format;s.width=w;s.height=h;s.stride=stride;s.bytes=size_t(stride)*h;
                check(w>0 && w<=4096 && h>0 && h<=4096 && stride>=w*4 && s.bytes<=64*1024*1024,"Invalid SHM layout");
                const int fd=memfd_create("bwm-r7-frame",MFD_CLOEXEC);check(fd>=0 && ftruncate(fd,s.bytes)==0,"No frame storage");
                s.memory=mmap(nullptr,s.bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);check(s.memory!=MAP_FAILED,"Cannot map frame");
                auto *pool=wl_shm_create_pool(s.shm,fd,s.bytes);s.buffer=wl_shm_pool_create_buffer(pool,0,w,h,stride,format);wl_shm_pool_destroy(pool);close(fd);
                zwlr_screencopy_frame_v1_copy(f,s.buffer);
            },
            [](void *p,zwlr_screencopy_frame_v1*,uint32_t flags){static_cast<Copy*>(p)->flags=flags;},
            [](void *p,zwlr_screencopy_frame_v1*,uint32_t hi,uint32_t lo,uint32_t ns){auto &s=*static_cast<Copy*>(p);s.presentation=(double((uint64_t(hi)<<32)|lo)*1000)+ns/1e6;s.done=true;},
            [](void *p,zwlr_screencopy_frame_v1*){auto &s=*static_cast<Copy*>(p);s.failed=s.done=true;},
            [](void*,zwlr_screencopy_frame_v1*,uint32_t,uint32_t,uint32_t,uint32_t){}, nullptr, nullptr};
        zwlr_screencopy_frame_v1_add_listener(frame,&listener,this);
        while(!done)check(wl_display_dispatch(display)>=0,"Private compositor disconnected");
        check(!failed && buffer,"Capture failed");
        QImage::Format imageFormat;
        switch(format){
            case WL_SHM_FORMAT_XRGB8888:imageFormat=QImage::Format_RGB32;break;
            case WL_SHM_FORMAT_ARGB8888:imageFormat=QImage::Format_ARGB32_Premultiplied;break;
            case WL_SHM_FORMAT_XBGR8888:imageFormat=QImage::Format_RGBX8888;break;
            case WL_SHM_FORMAT_ABGR8888:imageFormat=QImage::Format_RGBA8888_Premultiplied;break;
            default:qFatal("Unsupported SHM format %u",format);
        }
        rawCenterAlpha=(reinterpret_cast<const uint32_t*>(static_cast<const char*>(memory)+(height/2)*stride)[width/2]>>24)&255;
        QImage image(static_cast<uchar*>(memory),width,height,stride,imageFormat);
        auto owned=(flags & ZWLR_SCREENCOPY_FRAME_V1_FLAGS_Y_INVERT) ? image.flipped(Qt::Vertical) : image.copy();
        zwlr_screencopy_frame_v1_destroy(frame);wl_buffer_destroy(buffer);buffer=nullptr;munmap(memory,bytes);memory=MAP_FAILED;
        return owned.convertToFormat(QImage::Format_RGB32);
    }
    ~Copy(){zwlr_screencopy_manager_v1_destroy(manager);wl_output_destroy(output);wl_shm_destroy(shm);}
};

static QImage kwinCapture() {
    int pipefd[2];check(pipe2(pipefd,O_CLOEXEC)==0,"No screenshot pipe");
    QDBusInterface api("org.kde.KWin.ScreenShot2","/org/kde/KWin/ScreenShot2","org.kde.KWin.ScreenShot2");
    QVariantMap options{{"include-cursor",false},{"native-resolution",true}};
    const auto reply=api.callWithArgumentList(QDBus::Block,"CaptureWorkspace",{options,QVariant::fromValue(QDBusUnixFileDescriptor(pipefd[1]))});close(pipefd[1]);
    if(reply.type()==QDBusMessage::ErrorMessage)qFatal("%s",qPrintable(reply.errorMessage()));
    check(!reply.arguments().isEmpty(),"No screenshot result");const auto meta=qdbus_cast<QVariantMap>(reply.arguments().first());
    const int width=meta["width"].toInt(),height=meta["height"].toInt(),stride=meta["stride"].toInt();const qint64 count=qint64(stride)*height;
    check(width>0 && width<=4096 && height>0 && height<=4096 && stride>=width*4 && count<=64*1024*1024,"Bad KWin image layout");
    QByteArray pixels(count,Qt::Uninitialized);qint64 offset=0;
    while(offset<count){pollfd fd{pipefd[0],POLLIN,0};check(poll(&fd,1,5000)>0,"Screenshot timeout");auto n=read(pipefd[0],pixels.data()+offset,count-offset);check(n>0,"Short screenshot");offset+=n;}close(pipefd[0]);
    return QImage(reinterpret_cast<const uchar*>(pixels.constData()),width,height,stride,QImage::Format(meta["format"].toInt())).convertToFormat(QImage::Format_RGB32).copy();
}

int main(int argc,char **argv) {
    const auto root=QFileInfo(qEnvironmentVariable("BWM_R7_ROOT")).canonicalFilePath();
    auto *peer=privateDisplay(root);
    QGuiApplication app(argc,argv);app.setQuitOnLastWindowClosed(false);QGuiApplication::setDesktopFileName("bwm-r7-scene");
    check(argc>=2,"Missing mode");const auto mode=QString::fromLocal8Bit(argv[1]);
    if(mode=="capture") {
        check(argc>=4,"Missing capture backend/duration");const auto backend=QString::fromLocal8Bit(argv[2]);
        std::unique_ptr<Copy> copy;
        if(backend=="hyprland")copy=std::make_unique<Copy>(peer);
        else {
            check(backend=="kwin","Invalid backend");
            const auto pid=QDBusConnection::sessionBus().interface()->servicePid("org.kde.KWin");
            check(pid.isValid() && pid.value()==uint(qEnvironmentVariableIntValue("BWM_R7_COMPOSITOR_PID")),"Wrong KWin bus");
        }
        QFile output(root+"/frames.jsonl");check(output.open(QIODevice::WriteOnly),"Cannot write frames");
        const bool save=qEnvironmentVariableIsSet("BWM_R7_SAVE_FRAMES");if(save)QDir().mkdir(root+"/frames");
        const double end=now()+QString::fromLocal8Bit(argv[3]).toDouble()*1000;
        for(int index=0;now()<end;++index) {
            const double begin=now();const auto image=copy?copy->capture():kwinCapture();const double received=now();
            int left=image.width(),right=-1,top=image.height(),bottom=-1,maxSignal=0;
            for(int y=0;y<image.height();++y){const auto *row=reinterpret_cast<const QRgb*>(image.constScanLine(y));int rowLeft=image.width(),rowRight=-1,rowSignal=0,run=0,longestRun=0;
                for(int x=0;x<image.width();++x){const auto px=row[x];
                    if(qGreen(px)-qRed(px)>2 && qBlue(px)-qGreen(px)>1){rowLeft=std::min(rowLeft,x);rowRight=std::max(rowRight,x);rowSignal=std::max(rowSignal,qGreen(px)-qRed(px));longestRun=std::max(longestRun,++run);}else run=0;
                }
                // Neither an app icon nor scattered title glyphs are our solid rectangle.
                if(longestRun>=32){left=std::min(left,rowLeft);right=std::max(right,rowRight);top=std::min(top,y);bottom=std::max(bottom,y);maxSignal=std::max(maxSignal,rowSignal);}
            }
            QJsonObject sample{{"index",index},{"requestedMs",begin},{"receivedMs",received},{"presentationMs",copy?copy->presentation:0},
                {"shmFormat",copy?double(copy->format):-1},{"rawCenterAlpha",copy?copy->rawCenterAlpha:255},
                {"box",right<0?QJsonArray():QJsonArray{left,top,right-left+1,bottom-top+1}},{"opacity",maxSignal/128.0},{"output",QJsonArray{image.width(),image.height()}}};
            jsonLine(output,sample);
            if(save)check(image.save(root+QString("/frames/%1.png").arg(index,5,10,QChar('0')),"PNG",1),"Cannot save frame");
            QFile ready(root+"/capture-ready");if(index==0){check(ready.open(QIODevice::WriteOnly),"Cannot signal capture");ready.write("ready");}
        }
        copy.reset();wl_display_disconnect(peer);return 0;
    }
    check(mode=="scene","Unknown mode");wl_display_disconnect(peer);
    QQuickWindow background;background.setColor(QColor("#202020"));background.resize(800,600);
    auto *layer=LayerShellQt::Window::get(&background);layer->setLayer(LayerShellQt::Window::LayerBackground);
    layer->setAnchors(LayerShellQt::Window::Anchors::fromInt(15));layer->setExclusiveZone(-1);layer->setScope("bwm-r7-background");
    layer->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);background.show();
    QFile events(root+"/events.jsonl");check(events.open(QIODevice::WriteOnly),"Cannot write events");
    std::unique_ptr<QQuickWindow> window;int sequence=-1;
    QTimer timer;timer.setInterval(5);timer.setTimerType(Qt::PreciseTimer);
    QObject::connect(&timer,&QTimer::timeout,&app,[&]{
        QFile file(root+"/command.json");if(!file.open(QIODevice::ReadOnly))return;
        const auto command=QJsonDocument::fromJson(file.readAll()).object();const int next=command["sequence"].toInt(-1);if(next<=sequence)return;sequence=next;
        const auto action=command["action"].toString();const double time=now();
        if(action=="open") {
            window=std::make_unique<QQuickWindow>();if(!qEnvironmentVariableIsSet("BWM_R7_DECORATED"))window->setFlags(Qt::Window|Qt::FramelessWindowHint);window->setTitle("BWM R7 scene");window->setColor(QColor("#20a0e0"));window->resize(300,200);window->show();
            if(command.contains("closeAfterMs"))QTimer::singleShot(command["closeAfterMs"].toInt(),&app,[&,next]{
                if(sequence!=next || !window)return;
                const double time=now();sequence=next+1;window.reset();
                jsonLine(events,{{"sequence",sequence},{"action","close"},{"monotonicMs",time}});
            });
        }
        else if(action=="close")window.reset();
        // Hyprland receives explicit geometry from the driver, like kwin-window.py.
        // Its XDG maximize handler toggles even for unset requests in 0.56.2.
        else if(action=="maximize" && window && qEnvironmentVariable("BWM_R7_BACKEND")!="hyprland")window->showMaximized();
        else if(action=="restore" && window && qEnvironmentVariable("BWM_R7_BACKEND")!="hyprland")window->showNormal();
        else if(action=="quit")app.quit();
        jsonLine(events,{{"sequence",next},{"action",action},{"monotonicMs",time}});
    });timer.start();QTimer::singleShot(60000,&app,&QCoreApplication::quit);
    return app.exec();
}

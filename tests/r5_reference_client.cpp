// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// Test client for a new, private KWin only. Never connects to the session display/bus.
#include <QGuiApplication>
#include <QTimer>
#include <QScreen>
#include <QFile>
#include <QDir>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusInterface>
#include <QDBusReply>
#include <QDBusArgument>
#include <QDBusUnixFileDescriptor>
#include <QImage>
#include <wayland-client.h>
#include "fake-input-client.h"
#include <linux/input-event-codes.h>
#include <poll.h>
#include <unistd.h>
#include <cstring>
#include <iostream>
#include <algorithm>

static void check(bool ok,const char *message){if(!ok)qFatal("%s",message);}
int main(int argc,char **argv) {
    QGuiApplication app(argc,argv);
    QFile marker(qEnvironmentVariable("BWM_R5_REFERENCE_MARKER"));
    check(QFileInfo(marker).canonicalFilePath().startsWith(QDir::tempPath()+"/bwm-r5-reference-"),"Not a disposable R5 reference root");
    check(marker.open(QIODevice::ReadOnly),"Reference marker missing");
    const auto data=QJsonDocument::fromJson(marker.readAll()).object();
    check(qEnvironmentVariable("XDG_RUNTIME_DIR")==data["runtime"].toString(),"Reference runtime mismatch");
    check(qEnvironmentVariable("WAYLAND_DISPLAY")==data["display"].toString(),"Reference Wayland display mismatch");
    const auto pid=QDBusConnection::sessionBus().interface()->servicePid(QStringLiteral("org.kde.KWin"));
    check(pid.isValid() && pid.value()==data["pid"].toInteger(),"The bus does not belong to the new KWin");
    check(argc>=2,"Missing command");const QString command=QString::fromLocal8Bit(argv[1]);
    if(command=="capture") {
        check(argc>=3,"Missing image destination");
        int pipefd[2];check(pipe(pipefd)==0,"Cannot create capture pipe");
        QDBusInterface api("org.kde.KWin.ScreenShot2","/org/kde/KWin/ScreenShot2","org.kde.KWin.ScreenShot2");
        QVariantMap options{{"include-decoration",false},{"include-shadow",false},{"include-cursor",false},{"native-resolution",true}};
        const QString method=argc>3 && QString::fromLocal8Bit(argv[3])=="workspace" ? QStringLiteral("CaptureWorkspace") : QStringLiteral("CaptureActiveWindow");
        auto reply=api.callWithArgumentList(QDBus::Block,method,{options,QVariant::fromValue(QDBusUnixFileDescriptor(pipefd[1]))});
        close(pipefd[1]);
        if(reply.type()==QDBusMessage::ErrorMessage)qFatal("%s",qPrintable(reply.errorMessage()));
        check(!reply.arguments().isEmpty(),"No screenshot result");
        const auto meta=qdbus_cast<QVariantMap>(reply.arguments().first());
        const int width=meta.value("width").toInt(),height=meta.value("height").toInt(),stride=meta.value("stride").toInt();
        const qint64 count=qint64(stride)*height;
        check(width>0 && width<=8192 && height>0 && height<=8192 && stride>=width*4 && count<128*1024*1024,"Invalid image layout");
        QByteArray pixels(count,Qt::Uninitialized);qint64 offset=0;
        while(offset<count){pollfd fd{pipefd[0],POLLIN,0};check(poll(&fd,1,5000)>0,"Screenshot pipe timeout");auto n=read(pipefd[0],pixels.data()+offset,count-offset);check(n>0,"Short screenshot");offset+=n;}
        close(pipefd[0]);
        QImage image(reinterpret_cast<const uchar*>(pixels.constData()),width,height,stride,QImage::Format(meta.value("format").toInt()));
        check(image.save(QString::fromLocal8Bit(argv[2])),"Cannot save screenshot");
        std::cout<<QJsonDocument(QJsonObject{{"width",width},{"height",height},{"scale",meta.value("scale").toDouble()},{"window",meta.value("windowId").toString()}}).toJson().constData();
    } else if(command=="input" || command=="input-keepalive") {
        check(argc>=(command=="input-keepalive" ? 3 : 4),"Missing input arguments");
        auto *display=wl_display_connect(qPrintable(data["display"].toString()));check(display,"Cannot connect reference input display");
        org_kde_kwin_fake_input *input=nullptr;
        auto *registry=wl_display_get_registry(display);
        const wl_registry_listener listener{
            [](void *p,wl_registry *r,uint32_t name,const char *interface,uint32_t version){
                if(!std::strcmp(interface,"org_kde_kwin_fake_input"))*static_cast<org_kde_kwin_fake_input**>(p)=static_cast<org_kde_kwin_fake_input*>(wl_registry_bind(r,name,&org_kde_kwin_fake_input_interface,std::min(version,6u)));
            },[](void*,wl_registry*,uint32_t){}
        };
        wl_registry_add_listener(registry,&listener,&input);wl_display_roundtrip(display);check(input,"Private KWin does not expose its test input protocol");
        org_kde_kwin_fake_input_authenticate(input,"BWM R5 disposable fixture","Native Plasma UI regression");
        wl_display_roundtrip(display);
        if(command=="input-keepalive") {
            QFile ready(QString::fromLocal8Bit(argv[2]));check(ready.open(QIODevice::WriteOnly),"Cannot signal private input readiness");ready.write("ready");ready.close();
            return app.exec(); // Keep seat capabilities stable while individual commands run.
        }
        const QString action=QString::fromLocal8Bit(argv[2]);
        if(action=="key") {
            const uint key=QString::fromLocal8Bit(argv[3]).toUInt();
            org_kde_kwin_fake_input_keyboard_key(input,key,1);org_kde_kwin_fake_input_keyboard_key(input,key,0);
        } else {
            check(argc>=6,"Missing pointer arguments");
            org_kde_kwin_fake_input_pointer_motion_absolute(input,wl_fixed_from_double(QString::fromLocal8Bit(argv[3]).toDouble()),wl_fixed_from_double(QString::fromLocal8Bit(argv[4]).toDouble()));
            const uint button=QString::fromLocal8Bit(argv[5]).toUInt();
            if(action!="move"){org_kde_kwin_fake_input_button(input,button,1);org_kde_kwin_fake_input_button(input,button,0);}
        }
        wl_display_roundtrip(display);wl_proxy_destroy(reinterpret_cast<wl_proxy*>(input));wl_registry_destroy(registry);wl_display_disconnect(display);
    } else if(command=="outputs") {
        QJsonArray outputs;for(auto *s:QGuiApplication::screens())outputs.append(QJsonObject{{"name",s->name()},{"description",(s->manufacturer()+' '+s->model()+' '+s->serialNumber()).simplified()},{"width",s->size().width()},{"height",s->size().height()},{"dpr",s->devicePixelRatio()}});
        std::cout<<QJsonDocument(outputs).toJson().constData();
    } else check(false,"Unknown reference command");
}

// SPDX-FileCopyrightText: 2016 Eike Hein <hein@kde.org>
// SPDX-FileCopyrightText: 2023 Harald Sitter <sitter@kde.org>
// SPDX-License-Identifier: LGPL-2.1-only
// The desktop launch policy adapts canLauchNewInstance from plasma-workspace
// 6.7.5/tasktools.cpp. That helper is declared but not exported by LibTaskManager.
// BWM launch-job supervision below is original code under the same terms.
// Pinned-launcher service resolution mirrors runApp (plasma-workspace 6.7.5
// tasktools.cpp, same terms) without its OpenUrlJob/executable fallback.
// Jump-list resolution lives in launchrouter.cpp (GPL-2.0-or-later).
#include "tasklauncher.h"
#include "launchrouter.h"
#include <KIO/ApplicationLauncherJob>
#include <KAuthorized>
#include <KJob>
#include <KServiceAction>
#include <QCoreApplication>
#include <QEventLoop>
#include <QTimer>
#include <QPointer>
#include <QJsonDocument>
#include <QJsonArray>
#include <QElapsedTimer>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
KService::Ptr nativeTaskApplication(const TaskManager::AppData &app){
    KService::Ptr service;
    if(app.url.scheme()=="applications")service=KService::serviceByMenuId(app.url.path());
    else if(app.url.isLocalFile())service=KService::serviceByDesktopPath(app.url.toLocalFile());
    // Do not turn PID/executable fallback metadata into an arbitrary command.
    return service && service->isApplication()?service:KService::Ptr();
}
bool nativeTaskCanLaunchNewInstance(const TaskManager::AppData &app){
    const auto service=nativeTaskApplication(app);
    if(!service || service->noDisplay() || service->property<bool>(QStringLiteral("SingleMainWindow")) ||
       service->property<bool>(QStringLiteral("X-GNOME-SingleWindow")))return false;
    for(const auto &action:service->actions()){
        const auto name=action.name();
        if(name=="WindowNew" || (name.startsWith("new",Qt::CaseInsensitive) && name.endsWith("window",Qt::CaseInsensitive)))return false;
    }
    return true;
}
KService::Ptr nativeLauncherApplication(const QUrl &url){
    if(!validNativeLauncherUrl(url))return {};
    KService::Ptr service;
    if(url.scheme()=="applications")service=KService::serviceByMenuId(url.path());
    else if(url.scheme()=="preferred")service=KService::serviceByStorageId(TaskManager::defaultApplication(url));
    else if(url.isLocalFile())service=KService::serviceByDesktopPath(url.toLocalFile());
    return service && service->isApplication()?service:KService::Ptr();
}
bool validNativeLauncherUrl(const QUrl &url,QString *encoded){
    const auto text=url.toString(QUrl::FullyEncoded);
    if(!url.isValid() || url.isRelative() || text.isEmpty() || text.size()>4096 || text.contains(QChar::Null))return false;
    if(url.scheme()!="applications" && url.scheme()!="preferred" && url.scheme()!="file")return false;
    if(encoded)*encoded=text;return true;
}
bool encodeNativeLaunchUrls(const QList<QUrl> &urls,QJsonArray &values){
    if(urls.size()>128)return false;
    qsizetype bytes=0;
    for(const auto &url:urls){
        const auto encoded=url.toString(QUrl::FullyEncoded);bytes+=encoded.size();
        if(!url.isValid() || url.isRelative() || encoded.isEmpty() || encoded.size()>4096 || bytes>60000 || encoded.contains(QChar::Null))return false;
        values.append(encoded);
    }
    return true;
}
bool nativeInProcessLaunchDenied(){
    // ApplicationLauncherJob/OpenUrlJob check run_desktop_files and command
    // launches check shell_access before spawning anything.
    return !KAuthorized::authorize(KAuthorized::RUN_DESKTOP_FILES) && !KAuthorized::authorize(KAuthorized::SHELL_ACCESS);
}
namespace {
bool parseUrls(const QJsonValue &input,QList<QUrl> &urls){
    if(!input.isArray())return false;
    const auto values=input.toArray();if(values.size()>128)return false;
    for(const auto &value:values){
        if(!value.isString() || value.toString().isEmpty() || value.toString().size()>4096 || value.toString().contains(QChar::Null))return false;
        const auto url=QUrl::fromEncoded(value.toString().toUtf8(),QUrl::StrictMode);
        if(!url.isValid() || url.isRelative() || url.scheme().isEmpty())return false;
        urls.append(url);
    }
    return true;
}
QString runLauncherJob(KIO::ApplicationLauncherJob *job){
    job->setUiDelegate(nullptr);
    QPointer<KJob> held=job;QEventLoop loop;QTimer deadline;deadline.setSingleShot(true);
    bool finished=false,accepted=false;
    QObject::connect(job,&KJob::result,&loop,[&](KJob *result){finished=true;accepted=result->error()==0;loop.quit();});
    QObject::connect(&deadline,&QTimer::timeout,&loop,&QEventLoop::quit);
    deadline.start(3000);job->start();if(!finished)loop.exec();
    if(!finished){if(held)held->kill(KJob::Quietly);return QStringLiteral("native-launch-timed-out");}
    return accepted?QString():QStringLiteral("native-launch-job-rejected");
}
}
QJsonObject launchNativeTaskApplication(const QJsonObject &request){
    QJsonObject reply{{"version",1},{"accepted",false}};
    const auto reject=[&](const QString &reason){reply.insert("reason",reason);return reply;};
    const auto operation=request.value("action").toString();
    if(request.value("version")!=QJsonValue(1))return reject("invalid-launch-request");
    KIO::ApplicationLauncherJob *job=nullptr;
    if(operation=="new-instance" || operation=="open-urls"){
        const auto appId=request.value("appId").toString();const auto pid=request.value("pid");
        if(appId.isEmpty() || appId.size()>512 || appId.contains(QChar::Null) || !pid.isDouble() || pid.toDouble()!=pid.toInt() || pid.toInt()<=0)
            return reject("invalid-launch-request");
        QList<QUrl> urls;if(!parseUrls(request.value("urls"),urls))return reject("invalid-launch-url");
        if((operation=="new-instance" && !urls.isEmpty()) || (operation=="open-urls" && urls.isEmpty()))return reject("invalid-launch-urls");
        const auto app=TaskManager::appDataFromUrl(TaskManager::windowUrlFromMetadata(appId,pid.toInt()));
        const auto service=nativeTaskApplication(app);
        if(!service)return reject("native-application-launch-unavailable");
        job=new KIO::ApplicationLauncherJob(service);job->setUrls(urls);
    }else if(operation=="launcher" || operation=="service-action"){
        const auto raw=request.value("launcherUrl").toString();
        if(raw.isEmpty() || raw.size()>4096 || raw.contains(QChar::Null))return reject("invalid-launcher-url");
        const auto launcherUrl=QUrl::fromEncoded(raw.toUtf8(),QUrl::StrictMode);
        if(!validNativeLauncherUrl(launcherUrl))return reject("invalid-launcher-url");
        if(operation=="launcher"){
            QList<QUrl> urls;if(!parseUrls(request.value("urls"),urls))return reject("invalid-launch-url");
            // runApp's OpenUrlJob/executable fallback is deliberately not reproduced.
            const auto service=nativeLauncherApplication(launcherUrl);
            if(!service)return reject("native-launcher-application-unavailable");
            job=new KIO::ApplicationLauncherJob(service);job->setUrls(urls);
        }else{
            const auto name=request.value("serviceAction").toString();
            if(name.isEmpty() || name.size()>256 || name.contains(QChar::Null) || request.contains("urls"))return reject("invalid-service-action");
            KServiceAction selected;int count=0;
            for(const auto &action:nativeJumpListActions(launcherUrl))if(!action.isSeparator() && action.name()==name){selected=action;++count;}
            if(count!=1)return reject("native-service-action-unavailable");
            job=new KIO::ApplicationLauncherJob(selected);
        }
    }else return reject("invalid-launch-request");
    const auto failure=runLauncherJob(job);
    if(!failure.isEmpty())return reject(failure);
    reply.insert("accepted",true);reply.insert("launchHandedOff",true);return reply;
}
int runNativeTaskLauncher(){
    QByteArray input;QElapsedTimer elapsed;elapsed.start();bool complete=false;
    while(input.size()<=65536 && elapsed.elapsed()<1000){
        pollfd pipe{STDIN_FILENO,POLLIN,0};const int ready=poll(&pipe,1,qMax(1,1000-int(elapsed.elapsed())));
        if(ready<0 && errno==EINTR)continue;
        if(ready<=0)break;
        char bytes[4096];const auto count=read(STDIN_FILENO,bytes,sizeof(bytes));
        if(count<0 && errno==EINTR)continue;
        if(count<0)break;
        if(count==0){complete=true;break;}input.append(bytes,count);
    }
    // App stdout/stderr must never keep the action reply pipe open or mix with
    // its JSON. Only this CLOEXEC descriptor carries the startup receipt.
    const int response=fcntl(STDOUT_FILENO,F_DUPFD_CLOEXEC,3);
    const int quiet=open("/dev/null",O_WRONLY|O_CLOEXEC);
    if(response<0 || quiet<0){if(response>=0)close(response);if(quiet>=0)close(quiet);return 2;}
    if(dup2(quiet,STDOUT_FILENO)<0 || dup2(quiet,STDERR_FILENO)<0){close(quiet);close(response);return 2;}
    close(quiet);
    QJsonObject reply{{"version",1},{"accepted",false},{"reason","invalid-launch-input"}};
    QJsonParseError error;const auto document=QJsonDocument::fromJson(input,&error);
    if(complete && input.size()<=65536 && error.error==QJsonParseError::NoError && document.isObject())reply=launchNativeTaskApplication(document.object());
    const auto output=QJsonDocument(reply).toJson(QJsonDocument::Compact)+'\n';
    qsizetype sent=0;
    while(sent<output.size()){
        const auto count=write(response,output.constData()+sent,output.size()-sent);
        if(count<0 && errno==EINTR)continue;
        if(count<=0){close(response);return 2;}sent+=count;
    }
    close(response);return reply.value("accepted").toBool()?0:2;
}

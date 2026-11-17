// SPDX-License-Identifier: GPL-2.0-or-later
#include "desktopbridge.h"
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QProcessEnvironment>
#include <QRegularExpression>
#include <QSet>
#include <unistd.h>
#include <signal.h>
namespace {
QSet<DesktopBridge*> bridges;
bool suspended=false;
void stopProcess(QProcess &process) {
    const auto pid=process.processId();
    if(pid>0 && ::getpgid(pid)==pid)::kill(-pid,SIGKILL); // Only our new session's process group.
    process.kill();
}
}
DesktopBridge::DesktopBridge(QString runtime,QString program,QStringList prefix,QObject *parent)
    :QObject(parent),m_runtime(std::move(runtime)),m_program(std::move(program)),m_prefix(std::move(prefix)) {
    bridges.insert(this);m_suspended=suspended;
    const QFileInfo directory(m_runtime);
    m_available=directory.isDir() && !directory.isSymLink() && directory.ownerId()==::getuid() &&
        !(directory.permissions()&(QFile::ReadGroup|QFile::WriteGroup|QFile::ExeGroup|QFile::ReadOther|QFile::WriteOther|QFile::ExeOther)) &&
        directory.canonicalFilePath()==directory.absoluteFilePath() && QFileInfo(m_program).isExecutable();
    m_poll.setInterval(250);connect(&m_poll,&QTimer::timeout,this,&DesktopBridge::refresh);
    m_timeout.setSingleShot(true);m_timeout.setInterval(5000);
    m_process.setChildProcessModifier([]{::setsid();});
    connect(&m_timeout,&QTimer::timeout,this,[this]{m_error="Desktop action timed out";m_pending=false;stopProcess(m_process);});
    connect(&m_process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),this,[this](int code,QProcess::ExitStatus status){
        m_timeout.stop();
        if(code || status!=QProcess::NormalExit){if(m_error.isEmpty())m_error="Desktop action failed";m_pending=false;}
        refresh();if(m_pending)launch();
    });
    connect(&m_process,&QProcess::errorOccurred,this,[this](QProcess::ProcessError error){
        if(error==QProcess::FailedToStart){m_timeout.stop();m_pending=false;m_error="Desktop action could not start";}
    });
    if(m_available){refresh();m_poll.start();}
}
DesktopBridge::~DesktopBridge(){
    bridges.remove(this);
    m_poll.stop();m_timeout.stop();disconnect(&m_process,nullptr,this,nullptr);
    if(m_process.state()!=QProcess::NotRunning){stopProcess(m_process);m_process.waitForFinished(1000);}
}
bool DesktopBridge::refresh() {
    // The common manager clears its state before restoring each window. Do not
    // publish completion (or let the host exit) in the middle of that operation.
    if(m_process.state()!=QProcess::NotRunning)return true;
    bool active=false;
    const QFileInfo info(m_runtime+"/bwm-show-desktop.json");
    if(info.exists() || info.isSymLink()) {
        if(!info.isFile() || info.isSymLink() || info.ownerId()!=::getuid() || info.size()>1024*1024){m_error="Invalid desktop state";return false;}
        QFile file(info.absoluteFilePath());if(!file.open(QIODevice::ReadOnly)){m_error="Desktop state unavailable";return false;}
        QJsonParseError error;const auto data=QJsonDocument::fromJson(file.readAll(),&error);
        if(error.error!=QJsonParseError::NoError || !data.isObject() || !data.object().value("windows").isArray()){m_error="Invalid desktop state";return false;}
        const auto windows=data.object().value("windows").toArray();
        static const QRegularExpression address("^0x[0-9a-fA-F]+$");
        for(const auto &window:windows)if(!window.isString() || !address.match(window.toString()).hasMatch()) {
            m_error="Invalid desktop state";return false;
        }
        active=!windows.isEmpty();
    }
    if(m_active!=active){m_active=active;emit changed(active);}
    return true;
}
void DesktopBridge::setShowingDesktop(bool showing) {
    if(!m_available || m_suspended)return;
    m_desired=showing;m_pending=true;m_error.clear();launch();
}
void DesktopBridge::launch() {
    if(m_suspended)return;
    if(m_process.state()!=QProcess::NotRunning)return;
    if(!refresh()){m_pending=false;return;}
    if(m_active==m_desired){m_pending=false;return;}
    m_pending=false;
    auto args=m_prefix;args<<"show-desktop"<<(m_desired?"enter":"leave");
    auto env=QProcessEnvironment::systemEnvironment();env.insert("XDG_RUNTIME_DIR",m_runtime);
    if(!qEnvironmentVariableIsEmpty("BWM_R4_DESKTOP_CONFIG"))env.insert("XDG_CONFIG_HOME",qEnvironmentVariable("BWM_R4_DESKTOP_CONFIG"));
    m_process.setProcessEnvironment(env);m_process.setStandardOutputFile(QProcess::nullDevice());
    m_process.setStandardErrorFile(QProcess::nullDevice());m_process.start(m_program,args);m_timeout.start();
}
bool DesktopBridge::setSuspended(bool value) {
    m_suspended=value;
    if(value)m_pending=false; // Finish the current transaction; discard deferred toggles.
    return m_process.state()==QProcess::NotRunning;
}
bool DesktopBridge::suspendAll(bool value) {
    suspended=value;bool idle=true;
    for(auto *bridge:bridges)idle=bridge->setSuspended(value) && idle;
    return idle;
}

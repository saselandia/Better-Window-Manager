// SPDX-License-Identifier: GPL-2.0-or-later
#include "runtimecontrol.h"
#include "panelruntime.h"
#include <QLockFile>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QRegularExpression>
#include <cmath>
#include <unistd.h>

RuntimeControl::RuntimeControl(PanelRuntime *runtime,QString dir,QString token,QObject *parent)
    :QObject(parent),m_runtime(runtime),m_directory(std::move(dir)),m_token(std::move(token)) {
    m_read.setSingleShot(true);m_read.setInterval(25);
    connect(&m_watcher,&QFileSystemWatcher::directoryChanged,&m_read,qOverload<>(&QTimer::start));
    connect(&m_read,&QTimer::timeout,this,[this]{read();});
}
RuntimeControl::~RuntimeControl()=default;
bool RuntimeControl::start() {
    const QFileInfo directory(m_directory);
    const auto foreign=QFile::ReadGroup|QFile::WriteGroup|QFile::ExeGroup|QFile::ReadOther|QFile::WriteOther|QFile::ExeOther;
    if(!m_runtime || m_lock || !directory.isDir() || directory.isSymLink() ||
       directory.canonicalFilePath()!=directory.absoluteFilePath() || !directory.canonicalFilePath().startsWith(QDir::tempPath()+"/") ||
       directory.ownerId()!=::getuid() || (directory.permissions() & foreign) ||
       !QRegularExpression("^[a-f0-9]{64}$").match(m_token).hasMatch()) {
        m_error=QStringLiteral("Preview control requires a private temporary directory, a live runtime and a session token.");return false;
    }
    m_lock=std::make_unique<QLockFile>(m_directory+"/control-owner.lock");
    if(!m_lock->tryLock(0)){m_lock.reset();m_error=QStringLiteral("Another preview owns this control channel.");return false;}
    if(!m_watcher.addPath(m_directory) || !read()){m_watcher.removePaths(m_watcher.directories());m_lock.reset();return false;}
    return true;
}
bool RuntimeControl::read() {
    if(m_stopped || !m_runtime)return false;
    const auto reject=[this](const QString &error){m_error=error;return false;};
    const QFileInfo input(m_directory+"/control.json");
    if(!input.isFile() || input.isSymLink() || input.size()>4096)return reject(QStringLiteral("Invalid preview control file."));
    QFile file(input.absoluteFilePath());if(!file.open(QIODevice::ReadOnly))return reject(QStringLiteral("Cannot read preview control."));
    QJsonParseError parse;const auto document=QJsonDocument::fromJson(file.readAll(),&parse);
    if(parse.error!=QJsonParseError::NoError || !document.isObject())return reject(QStringLiteral("Malformed preview control JSON."));
    const auto command=document.object();const double number=command.value("revision").toDouble(-1);
    if(command.value("version").toInt(-1)!=1 || command.value("token").toString()!=m_token ||
       !std::isfinite(number) || number<0 || number>9007199254740991.0 || std::floor(number)!=number)
        return reject(QStringLiteral("Invalid preview control version, token or revision."));
    const qint64 revision=qint64(number);
    if(revision==m_revision && command==m_last)return true; // our atomic ack also changes the directory
    if(revision<=m_revision)return reject(QStringLiteral("Preview control revision must increase."));
    const auto action=command.value("command").toString();const auto skin=command.value("skin").toString();
    if(action!="skin" && action!="stop" && action!="status")return reject(QStringLiteral("Unknown preview control command."));
    if(action=="skin" && skin!="plasma" && skin!="retro" && skin!="default")return reject(QStringLiteral("Unknown preview skin."));
    if(action!="status" && !m_runtime->setSkin(action=="stop" ? "default" : skin))return reject(m_runtime->error());
    m_revision=revision;m_last=command;
    const QJsonObject ack{{"version",1},{"token",m_token},{"revision",double(revision)},{"ok",true},
        {"command",action},{"skin",m_runtime->skin()},{"panels",QJsonArray::fromVariantList(m_runtime->panels())},
        {"runtime",QJsonObject::fromVariantMap(m_runtime->readiness())}};
    QSaveFile output(m_directory+"/ack.json");const auto bytes=QJsonDocument(ack).toJson();
    if(!output.open(QIODevice::WriteOnly) || !output.setPermissions(QFile::ReadOwner|QFile::WriteOwner) ||
       output.write(bytes)!=bytes.size() || !output.commit()) {
        m_runtime->setSkin("default");return reject(QStringLiteral("Cannot acknowledge preview control; views withdrawn."));
    }
    m_error.clear();emit applied(revision);
    if(action=="stop"){m_stopped=true;m_read.stop();emit stopRequested();}
    return true;
}

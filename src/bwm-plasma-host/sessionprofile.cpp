// SPDX-License-Identifier: GPL-2.0-or-later
#include "profilestore.h"
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QStandardPaths>
#include <QUuid>
#include <unistd.h>
#include <stdexcept>

namespace {
const QStringList sessionFiles={"appletsrc","plasmashellrc","assignments.json","desktop-assignments.json"};
QString base(){return QStandardPaths::writableLocation(QStandardPaths::GenericStateLocation)+"/bwm/plasma/session-profiles";}
void require(bool ok){if(!ok)throw std::runtime_error("Invalid native session generation");}
void write(const QString &path,const QByteArray &data){QSaveFile f(path);require(f.open(QIODevice::WriteOnly));f.setPermissions(QFile::ReadOwner|QFile::WriteOwner);require(f.write(data)==data.size()&&f.commit());}
QByteArray read(const QString &path){QFile f(path);if(!f.exists())return {};require(QFileInfo(f).isFile()&&!QFileInfo(f).isSymLink()&&QFileInfo(f).ownerId()==getuid()&&f.size()<=16*1024*1024&&f.open(QIODevice::ReadOnly));return f.readAll();}
void validGeneration(const QString &root){QFileInfo f(root);require(root.startsWith(base()+"/")&&f.isDir()&&!f.isSymLink()&&f.ownerId()==getuid()&&f.canonicalFilePath()==f.absoluteFilePath());}
}
QString ProfileStore::sessionRoot(const QString &legacy){
    const auto bytes=read(legacy+"/active-session.json");
    if(bytes.isEmpty()&&!QFileInfo::exists(legacy+"/active-session.json"))return legacy;
    const auto active=QJsonDocument::fromJson(bytes).object();
    require(active.value("version").toInt()==1);const auto root=active.value("directory").toString();validGeneration(root);return root;
}
QString ProfileStore::checkpointSession(const QString &source){
    require(QFileInfo(source).isDir());
    QDir().mkpath(base());const QString root=base()+"/"+QUuid::createUuid().toString(QUuid::Id128);
    require(QDir().mkdir(root));QFile::setPermissions(root,QFile::ReadOwner|QFile::WriteOwner|QFile::ExeOwner);
    validGeneration(root);
    for(const auto &name:sessionFiles)write(root+"/"+name,read(source+"/"+name));
    sealSession(root);return root;
}
void ProfileStore::sealSession(const QString &root){
    validGeneration(root);QJsonObject hashes;
    for(const auto &name:sessionFiles)hashes[name]=QString::fromLatin1(QCryptographicHash::hash(read(root+"/"+name),QCryptographicHash::Sha256).toHex());
    write(root+"/session.json",QJsonDocument(QJsonObject{{"version",1},{"directory",root},{"files",hashes}}).toJson());
}

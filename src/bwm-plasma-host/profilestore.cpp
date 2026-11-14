// SPDX-License-Identifier: GPL-2.0-or-later
#include "profilestore.h"
#include "migration.h"
#include "outputidentity.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QLockFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QCryptographicHash>
#include <QRegularExpression>
#include <QStandardPaths>
#include <QSet>
#include <QUuid>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <unistd.h>

namespace {
const QStringList files={"layout","plasmashellrc","legacy.json","report.json","bindings.json"};
const auto privateMode=QFile::ReadOwner|QFile::WriteOwner|QFile::ExeOwner;
using Data=QHash<QString,QByteArray>;
void require(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
QString sha(const QByteArray &bytes){return QString::fromLatin1(QCryptographicHash::hash(bytes,QCryptographicHash::Sha256).toHex());}
QString id(){return QUuid::createUuid().toString(QUuid::Id128);}
bool validId(const QString &value){return QRegularExpression("^[a-f0-9]{32}$").match(value).hasMatch();}
QString stateBase() {
    const auto home=QStandardPaths::writableLocation(QStandardPaths::GenericStateLocation);
    require(!home.isEmpty() && QDir::isAbsolutePath(home),"An absolute XDG state home is required");
    return QDir::cleanPath(home+"/bwm/plasma/panel-profiles");
}
QString privateDirectory(const QString &path) {
    const QFileInfo info(path);
    const auto foreign=QFile::ReadGroup|QFile::WriteGroup|QFile::ExeGroup|QFile::ReadOther|QFile::WriteOther|QFile::ExeOther;
    require(info.isDir() && !info.isSymLink() && info.ownerId()==::getuid() && !(info.permissions() & foreign) &&
        info.canonicalFilePath()==info.absoluteFilePath(),"Profile directory must be private, owned and canonical");
    const auto canonical=info.canonicalFilePath();
    require(canonical.startsWith(QDir::tempPath()+"/") || canonical==stateBase() || canonical.startsWith(stateBase()+"/"),
        "Profile must be temporary or inside the BWM Plasma XDG state authority");
    return info.canonicalFilePath();
}
void mkdir(const QString &path){require(QDir().mkdir(path) && QFile::setPermissions(path,privateMode),"Cannot create private profile directory");}
QString ensureStateBase() {
    const auto base=stateBase();const auto home=QStandardPaths::writableLocation(QStandardPaths::GenericStateLocation);
    // Do not chmod pre-existing application/user directories or follow aliases.
    const auto owned=[](const QString &path){const QFileInfo info(path);return info.isDir() && !info.isSymLink() && info.ownerId()==::getuid() && info.canonicalFilePath()==info.absoluteFilePath();};
    if(!QFileInfo::exists(home)) {
        require(owned(QFileInfo(home).absolutePath()),"XDG state home needs an existing owned canonical parent");mkdir(home);
    }
    require(owned(home),"XDG state home must be owned and canonical");
    auto path=home;for(const auto &component:{"bwm","plasma","panel-profiles"}) {
        path+='/'+QString::fromLatin1(component);if(!QFileInfo::exists(path))mkdir(path);
        require(owned(path),"BWM state directory must not be a symlink or foreign directory");
    }
    return privateDirectory(base);
}
QByteArray read(const QString &path) {
    const QFileInfo info(path);
    require(info.isFile() && !info.isSymLink() && info.ownerId()==::getuid() && info.size()<=16*1024*1024,"Invalid native profile file");
    QFile file(path);require(file.open(QIODevice::ReadOnly),"Cannot read native profile file");return file.readAll();
}
QJsonObject json(const QByteArray &bytes) {
    QJsonParseError error;const auto doc=QJsonDocument::fromJson(bytes,&error);
    require(error.error==QJsonParseError::NoError && doc.isObject(),"Invalid profile metadata JSON");return doc.object();
}
void write(const QString &path,const QByteArray &bytes) {
    QSaveFile file(path);
    require(file.open(QIODevice::WriteOnly) && file.setPermissions(QFile::ReadOwner|QFile::WriteOwner) &&
        file.write(bytes)==bytes.size() && file.commit(),"Cannot commit native profile file");
}
Data readData(const QString &directory) {
    privateDirectory(directory);Data result;for(const auto &name:files)result.insert(name,read(directory+'/'+name));return result;
}
void writeData(const QString &directory,const Data &data){for(const auto &name:files)write(directory+'/'+name,data.value(name));}
QHash<uint,QString> outputs(const QJsonObject &metadata) {
    require(metadata.value("version").toInt(-1)==1 && metadata.value("panels").isArray(),"Unsupported output-binding metadata");
    QHash<uint,QString> result;
    for(const auto &p:metadata.value("panels").toArray()) {
        require(p.isObject(),"Invalid panel binding");const auto panel=p.toObject();
        const auto value=panel.value("containmentId").toDouble(-1);const auto description=panel.value("outputDescription").toString();
        require(std::isfinite(value) && value>=1 && value<=std::numeric_limits<uint>::max() && std::floor(value)==value,"Invalid native containment ID");
        const uint key=uint(value);
        require(!result.contains(key) && BwmOutput::resolve(description,{}).status!="invalid-output-description","Invalid or duplicate output binding");
        result.insert(key,description);
    }
    require(!result.isEmpty(),"A native panel profile needs output bindings");return result;
}
class ValidationCorona:public Plasma::Corona {public:QRect screenGeometry(int)const override{return {0,0,1024,768};}};
QJsonObject validate(const Data &data) {
    const auto metadata=json(data.value("bindings.json"));const auto bindings=outputs(metadata);
    const auto source=sha(data.value("legacy.json"));
    require(metadata.value("sourceSha256").toString()==source && json(data.value("report.json")).value("sourceSha256").toString()==source,"Profile provenance does not match its archived source");
    // Native loading can normalize configuration: validate a COPY so inspecting a
    // profile never changes its authoritative native files, unknown keys included.
    QTemporaryDir copy;require(copy.isValid(),"Cannot create native profile validation copy");
    write(copy.path()+"/layout",data.value("layout"));
    ValidationCorona corona;corona.loadLayout(copy.path()+"/layout");
    QSet<uint> actual;
    for(auto *c:corona.containments()) {
        require(c && !c->failedToLaunch() && (c->containmentType()==Plasma::Containment::Panel || c->containmentType()==Plasma::Containment::CustomPanel),"This profile requires loadable native panel containments");
        actual.insert(c->id());
    }
    require(actual==QSet<uint>(bindings.keyBegin(),bindings.keyEnd()),"Output bindings differ from the native panel IDs");
    return metadata;
}
struct Snapshot {Data data;QByteArray manifest;};
Snapshot readSnapshot(const QString &directory,const QString &snapshot) {
    privateDirectory(directory);const auto bytes=read(directory+"/snapshot.json");const auto manifest=json(bytes);
    require(validId(snapshot) && manifest.value("version").toInt(-1)==1 && manifest.value("snapshot").toString()==snapshot,"Unsupported snapshot metadata");
    const auto data=readData(directory);const auto hashes=manifest.value("files").toObject();const auto keys=hashes.keys();
    require(QSet<QString>(keys.cbegin(),keys.cend())==QSet<QString>(files.cbegin(),files.cend()),"Snapshot file inventory changed");
    for(const auto &name:files)require(hashes.value(name).toString()==sha(data.value(name)),"Snapshot native data or metadata changed");
    validate(data);return {data,bytes};
}
}

ProfileStore::ProfileStore(QString root):m_root(privateDirectory(root)) {
    m_lock=std::make_unique<QLockFile>(m_root+"/profile-owner.lock");
    require(m_lock->tryLock(0),"Another process owns this native profile");
    m_head=json(read(m_root+"/head.json"));
    require(m_head.value("version").toInt(-1)==1 && validId(m_head.value("generation").toString()),"Unsupported profile head");
    privateDirectory(m_root+"/generations");privateDirectory(m_root+"/snapshots");
    m_bindings=validate(readData(generationDirectory()));
}
ProfileStore::~ProfileStore()=default;
QString ProfileStore::generationDirectory()const{return m_root+"/generations/"+m_head.value("generation").toString();}
QString ProfileStore::layoutFile()const{return generationDirectory()+"/layout";}
QString ProfileStore::viewSettingsFile()const{return generationDirectory()+"/plasmashellrc";}
QHash<uint,QString> ProfileStore::assignments()const{return outputs(m_bindings);}
void ProfileStore::unchangedHead()const{require(json(read(m_root+"/head.json"))==m_head,"Profile head changed elsewhere; reopen before writing");}
QJsonObject ProfileStore::info()const {
    return {{"status","native-profile-ready"},{"directory",m_root},{"generation",m_head.value("generation")},
        {"layoutFile",layoutFile()},{"viewSettingsFile",viewSettingsFile()},{"panels",m_bindings.value("panels")},
        {"sourceSha256",m_bindings.value("sourceSha256")},
        {"storage",m_root.startsWith(stateBase()+"/") ? "xdg-state" : "temporary"},{"activationAllowed",false}};
}
QJsonObject ProfileStore::importStage(const QString &stage,const QString &destination) {
    const auto parent=privateDirectory(QFileInfo(destination).absolutePath());
    require(!QFileInfo::exists(destination) && QFileInfo(destination).fileName()!="." && QFileInfo(destination).fileName()!="..","Profile destination exists or is invalid");
    const QFileInfo source(stage);require(source.canonicalFilePath().startsWith(parent+'/') && !source.isSymLink(),"Stage must be inside the isolated configuration root");
    QTemporaryDir work(parent+"/.bwm-profile-XXXXXX");require(work.isValid(),"Cannot prepare native profile");
    mkdir(work.path()+"/generations");mkdir(work.path()+"/snapshots");const auto generation=id();
    const auto target=work.path()+"/generations/"+generation;mkdir(target);
    // Verify the captured copy, not mutable source files read a second time.
    for(const auto &name:{"layout","plasmashellrc","legacy.json","report.json"})write(target+'/'+name,read(stage+'/'+name));
    const auto report=BwmMigration::verify(target);
    require(report.value("viewSettingsContractVersion").toInt(-1)==1,"Native view staging contract is required for profile import");
    QJsonArray panels;for(const auto &p:report.value("panels").toArray()) {
        const auto panel=p.toObject();panels.append(QJsonObject{{"containmentId",panel.value("containmentId")},{"outputDescription",panel.value("outputDescription")}});
    }
    const QJsonObject bindings{{"version",1},{"sourceSha256",report.value("sourceSha256")},{"panels",panels}};
    write(target+"/bindings.json",QJsonDocument(bindings).toJson());validate(readData(target));
    write(work.path()+"/head.json",QJsonDocument(QJsonObject{{"version",1},{"generation",generation}}).toJson());
    require(!QFileInfo::exists(destination) && QDir().rename(work.path(),destination),"Cannot publish profile without overwriting an existing destination");
    work.setAutoRemove(false);ProfileStore profile(destination);return profile.info();
}
QJsonObject ProfileStore::checkpoint() {
    unchangedHead();const auto data=readData(generationDirectory());validate(data);
    const auto snapshot=id();QTemporaryDir work(m_root+"/snapshots/.prepare-XXXXXX");require(work.isValid(),"Cannot prepare profile checkpoint");
    writeData(work.path(),data);QJsonObject hashes;for(const auto &name:files)hashes.insert(name,sha(data.value(name)));
    const QJsonObject manifest{{"version",1},{"snapshot",snapshot},{"sourceGeneration",m_head.value("generation")},{"files",hashes}};
    write(work.path()+"/snapshot.json",QJsonDocument(manifest).toJson());unchangedHead();
    require(QDir().rename(work.path(),m_root+"/snapshots/"+snapshot),"Cannot publish profile checkpoint");work.setAutoRemove(false);
    return {{"status","native-profile-checkpoint"},{"snapshot",snapshot},{"directory",m_root+"/snapshots/"+snapshot},{"activationAllowed",false}};
}
QJsonObject ProfileStore::restore(const QString &snapshot) {
    require(validId(snapshot),"Invalid profile snapshot ID");unchangedHead();
    const auto data=readSnapshot(m_root+"/snapshots/"+snapshot,snapshot).data;
    const auto metadata=validate(data);const auto generation=id();
    QTemporaryDir work(m_root+"/generations/.restore-XXXXXX");require(work.isValid(),"Cannot prepare restored profile");writeData(work.path(),data);
    const auto target=m_root+"/generations/"+generation;
    require(QDir().rename(work.path(),target),"Cannot publish restored generation");work.setAutoRemove(false);
    auto next=m_head;next["generation"]=generation;
    // Keep the old generation/path intact. Even a retained KSharedConfig owner
    // cannot write into the restored file through its cached old filename.
    unchangedHead();write(m_root+"/head.json",QJsonDocument(next).toJson());m_head=next;m_bindings=metadata;
    auto result=info();result["status"]="native-profile-restored";result["restoredSnapshot"]=snapshot;return result;
}
QJsonObject ProfileStore::exportToState(const QString &name) {
    require(QRegularExpression("^[a-z0-9][a-z0-9._-]{0,63}$").match(name).hasMatch(),"Invalid persistent profile name");
    unchangedHead();const auto data=readData(generationDirectory());validate(data);
    const auto base=ensureStateBase(),destination=base+'/'+name;
    require(!QFileInfo::exists(destination) && !QFileInfo(destination).isSymLink(),"Persistent profile destination exists; refusing to overwrite it");
    QTemporaryDir work(base+"/.publish-XXXXXX");require(work.isValid(),"Cannot prepare persistent profile export");
    mkdir(work.path()+"/generations");mkdir(work.path()+"/snapshots");const auto generation=id();
    mkdir(work.path()+"/generations/"+generation);writeData(work.path()+"/generations/"+generation,data);
    int count=0;
    for(const auto &snapshot:QDir(m_root+"/snapshots").entryList(QDir::Dirs|QDir::NoDotAndDotDot,QDir::Name)) {
        const auto captured=readSnapshot(m_root+"/snapshots/"+snapshot,snapshot);
        const auto target=work.path()+"/snapshots/"+snapshot;mkdir(target);writeData(target,captured.data);write(target+"/snapshot.json",captured.manifest);++count;
    }
    auto head=m_head;head["generation"]=generation;
    write(work.path()+"/head.json",QJsonDocument(head).toJson());unchangedHead();
    require(!QFileInfo::exists(destination) && !QFileInfo(destination).isSymLink() && QDir().rename(work.path(),destination),"Cannot publish persistent profile without replacing a destination");
    work.setAutoRemove(false);ProfileStore profile(destination);auto result=profile.info();
    result["status"]="native-profile-exported";result["copiedSnapshots"]=count;result["sourceGeneration"]=m_head.value("generation");return result;
}

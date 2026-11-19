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
#include <algorithm>
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
bool validName(const QString &value){return QRegularExpression("^[a-z0-9][a-z0-9._-]{0,63}$").match(value).hasMatch();}
bool present(const QString &path){const QFileInfo info(path);return info.exists() || info.isSymLink();}
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
QJsonObject profileInfo(const QString &root,const QJsonObject &head,const QJsonObject &bindings) {
    const auto directory=root+"/generations/"+head.value("generation").toString();
    return {{"status","native-profile-ready"},{"directory",root},{"generation",head.value("generation")},
        {"layoutFile",directory+"/layout"},{"viewSettingsFile",directory+"/plasmashellrc"},{"panels",bindings.value("panels")},
        {"sourceSha256",bindings.value("sourceSha256")},
        {"storage",root.startsWith(stateBase()+"/") ? "xdg-state" : "temporary"},{"activationAllowed",false}};
}
constexpr qint64 maxRevision=9007199254740991LL;
// One lock order everywhere: selection, previous profile (if different), target.
// Reads never create the state authority. Invalid metadata is never auto-reset.
struct SelectionLease {
    QString base=stateBase(),directory=base+"/.selection",path=directory+"/selection.json";
    std::unique_ptr<QLockFile> lock;
    bool existed=false;QByteArray bytes;
    QJsonObject state{{"version",1},{"revision",0},{"profile",QJsonValue(QJsonValue::Null)}};
    explicit SelectionLease(bool create) {
        if(create)ensureStateBase();
        if(!present(base))return;
        privateDirectory(base);
        if(!present(directory)){if(!create)return;mkdir(directory);}
        privateDirectory(directory);lock=std::make_unique<QLockFile>(directory+"/owner.lock");
        require(lock->tryLock(0),"Another process owns the profile selection");
        existed=present(path);if(!existed)return;
        bytes=read(path);state=json(bytes);
        const auto number=state.value("revision").toDouble(-1);
        const auto profile=state.value("profile");
        require(state.value("version").toInt(-1)==1 && std::isfinite(number) && number>=1 && number<=maxRevision && std::floor(number)==number &&
            (profile.isNull() || (profile.isString() && validName(profile.toString()))),"Unsupported profile selection metadata");
        require(profile.isNull() ? !state.contains("sourceSha256") :
            QRegularExpression("^[a-f0-9]{64}$").match(state.value("sourceSha256").toString()).hasMatch(),"Invalid selected profile provenance");
    }
    qint64 revision()const{return qint64(state.value("revision").toDouble());}
    QString name()const{return state.value("profile").toString();}
    void unchanged()const{require(present(path)==existed && (!existed || read(path)==bytes),"Profile selection changed elsewhere; inspect it before retrying");}
    QJsonObject result()const{return {{"version",1},{"status",name().isEmpty()?"profile-unselected":"profile-selected"},
        {"selectionFile",path},{"revision",revision()},{"selectedProfile",state.value("profile")},
        {"activationAllowed",false},{"replacementReady",false},{"scope","persistent-profile-intent"}};}
};
void sameSource(const SelectionLease &selection,const ProfileStore &profile) {
    require(profile.info().value("sourceSha256")==selection.state.value("sourceSha256"),"Selected profile provenance changed; explicitly select it again");
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
QString ProfileStore::layoutFile()const{return (m_edit?m_edit->path():generationDirectory())+"/layout";}
QString ProfileStore::viewSettingsFile()const{return (m_edit?m_edit->path():generationDirectory())+"/plasmashellrc";}
QHash<uint,QString> ProfileStore::assignments()const{return outputs(m_bindings);}
void ProfileStore::beginEditing() {
    require(!m_edit,"A native profile edit session is already open");unchangedHead();
    auto work=std::make_unique<QTemporaryDir>(m_root+"/generations/.edit-XXXXXX");
    require(work->isValid(),"Cannot prepare native profile edit session");
    const auto data=readData(generationDirectory());validate(data);writeData(work->path(),data);m_edit=std::move(work);
}
void ProfileStore::commitEditing(const QHash<uint,QString> &assignments) {
    require(bool(m_edit),"No native profile edit session is open");unchangedHead();
    auto data=readData(m_edit->path());
    // Preserve metadata/provenance fields. Only the panel/output inventory changes.
    auto bindings=json(data.value("bindings.json"));QJsonArray panels;
    auto ids=assignments.keys();std::sort(ids.begin(),ids.end());
    for(auto id:ids) {
        QJsonObject panel;
        for(const auto &previous:bindings.value("panels").toArray())if(previous.toObject().value("containmentId").toDouble()==id) {panel=previous.toObject();break;}
        panel["containmentId"]=double(id);panel["outputDescription"]=assignments.value(id);panels.append(panel);
    }
    bindings["panels"]=panels;data["bindings.json"]=QJsonDocument(bindings).toJson();validate(data);
    const auto generation=id();QTemporaryDir work(m_root+"/generations/.commit-XXXXXX");
    require(work.isValid(),"Cannot prepare edited native generation");writeData(work.path(),data);
    unchangedHead();require(QDir().rename(work.path(),m_root+"/generations/"+generation),"Cannot publish edited native generation");
    work.setAutoRemove(false);auto next=m_head;next["generation"]=generation;
    unchangedHead();write(m_root+"/head.json",QJsonDocument(next).toJson());m_head=next;m_bindings=bindings;
    m_edit.reset();
}
void ProfileStore::unchangedHead()const{require(json(read(m_root+"/head.json"))==m_head,"Profile head changed elsewhere; reopen before writing");}
QJsonObject ProfileStore::info()const {
    return profileInfo(m_root,m_head,m_bindings);
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
    require(!m_edit,"Close the native edit session before taking a checkpoint");
    unchangedHead();const auto data=readData(generationDirectory());validate(data);
    const auto snapshot=id();QTemporaryDir work(m_root+"/snapshots/.prepare-XXXXXX");require(work.isValid(),"Cannot prepare profile checkpoint");
    writeData(work.path(),data);QJsonObject hashes;for(const auto &name:files)hashes.insert(name,sha(data.value(name)));
    const QJsonObject manifest{{"version",1},{"snapshot",snapshot},{"sourceGeneration",m_head.value("generation")},{"files",hashes}};
    write(work.path()+"/snapshot.json",QJsonDocument(manifest).toJson());unchangedHead();
    require(QDir().rename(work.path(),m_root+"/snapshots/"+snapshot),"Cannot publish profile checkpoint");work.setAutoRemove(false);
    return {{"status","native-profile-checkpoint"},{"snapshot",snapshot},{"directory",m_root+"/snapshots/"+snapshot},{"activationAllowed",false}};
}
QJsonObject ProfileStore::restore(const QString &snapshot) {
    require(!m_edit,"Close the native edit session before restoring a snapshot");
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
QJsonObject ProfileStore::recover(const QString &root,const QString &snapshot) {
    require(validId(snapshot),"Invalid profile snapshot ID");const auto directory=privateDirectory(root);
    QLockFile lock(directory+"/profile-owner.lock");require(lock.tryLock(0),"Another process owns this native profile");
    privateDirectory(directory+"/generations");privateDirectory(directory+"/snapshots");
    const auto headPath=directory+"/head.json";
    const auto present=[](const QString &path){const QFileInfo info(path);return info.exists() || info.isSymLink();};
    const bool hadHead=present(headPath);const auto previous=hadHead ? read(headPath) : QByteArray();
    // Preserve unknown object fields when readable, but do not downgrade a known
    // future schema. The generation itself need not be valid/loadable to recover.
    const auto parsed=QJsonDocument::fromJson(previous);auto next=parsed.isObject() ? parsed.object() : QJsonObject();
    require(!next.contains("version") || next.value("version").toInt(-1)==1,"Unsupported profile head version for recovery");
    const auto unchanged=[&]{require(present(headPath)==hadHead && (!hadHead || read(headPath)==previous),
        "Profile head changed elsewhere; retry recovery after inspecting it");};
    const auto data=readSnapshot(directory+"/snapshots/"+snapshot,snapshot).data;
    const auto metadata=validate(data);unchanged();
    const auto generation=id();next["version"]=1;next["generation"]=generation;
    QTemporaryDir work(directory+"/generations/.recover-XXXXXX");require(work.isValid(),"Cannot prepare recovered profile");
    writeData(work.path(),data);
    const auto recoveries=directory+"/recoveries";if(!present(recoveries))mkdir(recoveries);privateDirectory(recoveries);
    QTemporaryDir archive(recoveries+"/.prepare-XXXXXX");require(archive.isValid(),"Cannot prepare profile recovery record");
    if(hadHead)write(archive.path()+"/head.json",previous);
    const QJsonObject record{{"version",1},{"snapshot",snapshot},{"generation",generation},{"previousHeadPresent",hadHead},
        {"previousHeadSha256",hadHead ? QJsonValue(sha(previous)) : QJsonValue(QJsonValue::Null)}};
    write(archive.path()+"/recovery.json",QJsonDocument(record).toJson());unchanged();
    require(QDir().rename(work.path(),directory+"/generations/"+generation),"Cannot publish recovered generation");work.setAutoRemove(false);
    const auto archivePath=recoveries+'/'+generation;
    require(QDir().rename(archive.path(),archivePath),"Cannot publish profile recovery record");archive.setAutoRemove(false);
    // Both complete directories exist before the only selection write. Earlier
    // failures leave the original head intact; old generations are never edited.
    unchanged();write(headPath,QJsonDocument(next).toJson());
    auto result=profileInfo(directory,next,metadata);result["status"]="native-profile-recovered";
    result["recoveredSnapshot"]=snapshot;result["recoveryDirectory"]=archivePath;result["previousHeadPresent"]=hadHead;return result;
}
QJsonObject ProfileStore::exportToState(const QString &name) {
    require(!m_edit,"Close the native edit session before exporting a profile");
    require(validName(name),"Invalid persistent profile name");
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

QJsonObject ProfileSelection::info() {
    SelectionLease selection(false);auto result=selection.result();result["profileValidated"]=false;
    if(!selection.name().isEmpty()) {
        try {
            ProfileStore profile(selection.base+'/'+selection.name());sameSource(selection,profile);
            profile.unchangedHead();result["profile"]=profile.info();result["profileValidated"]=true;
        } catch(const std::exception &e){result["profileError"]=QString::fromUtf8(e.what());}
    }
    selection.unchanged();return result;
}
QJsonObject ProfileSelection::select(const QString &name,qint64 expectedRevision) {
    require(validName(name),"Invalid persistent profile name");return update(name,expectedRevision);
}
QJsonObject ProfileSelection::clear(qint64 expectedRevision){return update({},expectedRevision);}
QJsonObject ProfileSelection::update(const QString &name,qint64 expectedRevision) {
    require(expectedRevision>=0 && expectedRevision<=maxRevision,"Invalid expected selection revision");
    SelectionLease selection(true);require(selection.revision()==expectedRevision,"Profile selection revision changed; inspect it before retrying");
    // Clearing a broken/missing selected generation must remain possible. Only
    // its directory and lease are needed; do not construct its invalid Corona.
    std::unique_ptr<QLockFile> previous;
    if(!selection.name().isEmpty() && selection.name()!=name) {
        const auto root=selection.base+'/'+selection.name();
        if(present(root)) {
            privateDirectory(root);previous=std::make_unique<QLockFile>(root+"/profile-owner.lock");
            require(previous->tryLock(0),"Another process owns the previously selected native profile");
        }
    }
    std::unique_ptr<ProfileStore> profile;
    if(!name.isEmpty())profile=std::make_unique<ProfileStore>(selection.base+'/'+name);
    const auto source=profile ? profile->info().value("sourceSha256") : QJsonValue();
    if(selection.name()==name && (name.isEmpty() || selection.state.value("sourceSha256")==source)) {
        selection.unchanged();if(profile)profile->unchangedHead();auto result=selection.result();result["changed"]=false;return result;
    }
    require(selection.revision()<maxRevision,"Profile selection revision exhausted");
    auto next=selection.state;next["revision"]=selection.revision()+1;next["profile"]=name.isEmpty()?QJsonValue(QJsonValue::Null):QJsonValue(name);
    if(profile)next["sourceSha256"]=source;else next.remove("sourceSha256");
    if(profile)profile->unchangedHead();selection.unchanged();write(selection.path,QJsonDocument(next).toJson());selection.state=next;
    auto result=selection.result();result["changed"]=true;return result;
}
std::unique_ptr<ProfileStore> ProfileSelection::openSelected() {
    SelectionLease selection(false);require(!selection.name().isEmpty(),"No native profile has been selected");
    auto profile=std::make_unique<ProfileStore>(selection.base+'/'+selection.name());sameSource(selection,*profile);
    profile->unchangedHead();selection.unchanged();return profile;
}

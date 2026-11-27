// SPDX-License-Identifier: GPL-2.0-or-later
#include "kns.h"
#include "catalog.h"
#include <KNSCore/EngineBase>
#include <KNSCore/Entry>
#include <KNSCore/ErrorCode>
#include <KNSCore/Question>
#include <KNSCore/QuestionListener>
#include <KNSCore/ResultsStream>
#include <KNSCore/SearchRequest>
#include <KNSCore/Transaction>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QEventLoop>
#include <functional>
#include <QJsonArray>
#include <QSet>
#include <QStandardPaths>
#include <QTimer>
#include <memory>
#include <QFile>
#include <QDir>

namespace {
// Fail closed: KNewStuff only asks before overwriting a file or continuing after an
// install-time warning. Nothing is answered affirmatively without a person.
class CancelAllQuestions : public KNSCore::QuestionListener {
public:
    QJsonArray asked;
    void askQuestion(KNSCore::Question *question) override {
        asked.append(QJsonObject{{"title",question->title()},{"question",question->question().left(300)}});
        question->setResponse(question->questionType()==KNSCore::Question::YesNoQuestion ? KNSCore::Question::NoResponse : KNSCore::Question::CancelResponse);
    }
};

QString statusName(KNSCore::Entry::Status status) {
    switch(status) {
    case KNSCore::Entry::Downloadable:return "downloadable";
    case KNSCore::Entry::Installed:return "installed";
    case KNSCore::Entry::Updateable:return "updateable";
    case KNSCore::Entry::Deleted:return "deleted";
    case KNSCore::Entry::Installing:return "installing";
    case KNSCore::Entry::Updating:return "updating";
    default:return "invalid";
    }
}

QJsonObject entryJson(const KNSCore::Entry &entry) {
    QJsonArray downloads;
    for(const auto &link:entry.downloadLinkInformationList())downloads.append(QJsonObject{
        {"id",link.id},{"name",link.name},{"sizeKiB",qint64(link.size)},
        {"distribution",link.distributionType},{"descriptionLink",link.descriptionLink},{"tags",QJsonArray::fromStringList(link.tags)}});
    return QJsonObject{{"uniqueId",entry.uniqueId()},{"name",entry.name()},{"version",entry.version()},
        {"providerId",entry.providerId()},{"category",entry.category()},{"downloadCount",entry.downloadCount()},
        {"homepage",entry.homepage().toString()},{"license",entry.license()},{"downloads",downloads},
        {"status",statusName(entry.status())},{"summary",entry.summary().left(200)},
        {"installedFiles",QJsonArray::fromStringList(entry.installedFiles())}};
}

// Spin the event loop until done() holds or the deadline passes (no nested quit races).
bool waitFor(int timeoutMs,const std::function<bool()> &done) {
    QElapsedTimer timer;timer.start();
    while(!done() && timer.elapsed()<timeoutMs)
        QCoreApplication::processEvents(QEventLoop::WaitForMoreEvents,50);
    return done();
}

struct Engine {
    KNSCore::EngineBase engine;
    QJsonArray errors;
    bool ready=false;
    QString provider;
    bool start(int timeoutMs,const QString &name="plasmoids") {
        if(!QStringList{"plasmoids","lookandfeel","plasma-themes","colorschemes","aurorae","window-decorations","icons","xcursor"}.contains(name)){
            errors.append("Unsupported store provider");return false;
        }
        provider=QStandardPaths::locate(QStandardPaths::GenericDataLocation,"knsrcfiles/"+name+".knsrc");
        if(provider.isEmpty()){errors.append("The native "+name+".knsrc provider is missing.");return false;}
        QString engineProvider=provider;
        if(name!="plasmoids") {
            // Same provider/category/installer as the native KCM, but no automatic
            // adoption. xcursor's legacy InstallPath ignores XDG_DATA_HOME.
            QFile original(provider);if(!original.open(QIODevice::ReadOnly)){errors.append("Cannot read native provider");return false;}
            QStringList lines;
            for(const auto &line:QString::fromUtf8(original.readAll()).split('\n')) {
                if(line.startsWith("AdoptionCommand=")||line.startsWith("AliasFor="))continue;
                if(line.startsWith("InstallPath=")){lines.append("TargetDir=icons");continue;}
                lines.append(line);
            }
            const auto directory=QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation)+"/bwm-kns-providers";
            QDir().mkpath(directory);engineProvider=directory+"/"+name+".knsrc";
            QFile copy(engineProvider);if(!copy.open(QIODevice::WriteOnly)){errors.append("Cannot stage isolated provider");return false;}
            copy.write(lines.join('\n').toUtf8());copy.close();
        }
        QObject::connect(&engine,&KNSCore::EngineBase::signalErrorCode,&engine,[this](KNSCore::ErrorCode::ErrorCode code,const QString &message,const QVariant &){
            errors.append(QJsonObject{{"code",int(code)},{"message",message}});
        });
        QObject::connect(&engine,&KNSCore::EngineBase::signalProvidersLoaded,&engine,[this]{ready=true;});
        if(!engine.init(engineProvider)){errors.append("EngineBase::init failed for "+provider);return false;}
        waitFor(timeoutMs,[this]{return ready;});
        if(!ready)errors.append("Timed out loading the KNewStuff providers.");
        return ready;
    }
    KNSCore::Entry::List find(const KNSCore::SearchRequest &request,int timeoutMs) {
        KNSCore::Entry::List found;bool finished=false;
        auto *stream=engine.search(request);
        QObject::connect(stream,&KNSCore::ResultsStream::entriesFound,stream,[&found](const KNSCore::Entry::List &entries){found+=entries;});
        QObject::connect(stream,&KNSCore::ResultsStream::finished,stream,[&finished]{finished=true;});
        stream->fetch();
        waitFor(timeoutMs,[&finished]{return finished;});
        if(!finished){errors.append("Timed out waiting for search results.");stream->deleteLater();}
        return found;
    }
    KNSCore::Entry exact(const QString &id,int timeoutMs) {
        for(const auto &entry:find(KNSCore::SearchRequest(KNSCore::SortMode::Downloads,KNSCore::Filter::ExactEntryId,id),timeoutMs))
            if(entry.uniqueId()==id)return entry;
        return {};
    }
};

QSet<QString> catalogIds(const Catalog &catalog) {
    QSet<QString> ids;for(const auto &value:catalog.entries())ids.insert(value.toMap().value("id").toString());return ids;
}

QJsonObject runTransaction(Engine &e,KNSCore::Transaction *transaction,int timeoutMs,KNSCore::Entry &updated) {
    bool finished=false;QJsonArray events;
    QObject::connect(transaction,&KNSCore::Transaction::signalEntryEvent,transaction,[&](const KNSCore::Entry &entry,KNSCore::Entry::EntryEvent event){
        updated=entry;events.append(QJsonObject{{"event",int(event)},{"status",statusName(entry.status())}});
    });
    QObject::connect(transaction,&KNSCore::Transaction::signalErrorCode,transaction,[&e](KNSCore::ErrorCode::ErrorCode code,const QString &message,const QVariant &){
        e.errors.append(QJsonObject{{"code",int(code)},{"message",message}});
    });
    QObject::connect(transaction,&KNSCore::Transaction::finished,transaction,[&finished]{finished=true;});
    waitFor(timeoutMs,[&finished,transaction]{return finished || transaction->isFinished();});
    if(!finished && !transaction->isFinished())e.errors.append("Timed out waiting for the KNewStuff transaction.");
    return QJsonObject{{"events",events},{"finished",finished || transaction->isFinished()}};
}
}

namespace BwmKns {
QJsonObject search(const QString &term,int page,int timeoutMs,const QString &provider) {
    CancelAllQuestions questions;Engine e;QJsonArray results;
    if(e.start(timeoutMs,provider))
        for(const auto &entry:e.find(KNSCore::SearchRequest(KNSCore::SortMode::Downloads,KNSCore::Filter::None,term,{},page,20),timeoutMs))
            results.append(entryJson(entry));
    return QJsonObject{{"provider",e.provider},{"term",term},{"page",page},{"results",results},{"errors",e.errors},{"questions",questions.asked}};
}

QJsonObject install(const QString &uniqueId,int timeoutMs,const QString &provider) {
    CancelAllQuestions questions;Engine e;Catalog catalog;
    const auto before=catalogIds(catalog);
    QJsonObject result{{"uniqueId",uniqueId},{"catalogBefore",int(before.size())}};
    if(e.start(timeoutMs/2,provider)) {
        auto entry=e.exact(uniqueId,timeoutMs/2);
        if(!entry.isValid())e.errors.append("No store entry with that id.");
        else {
            result["entry"]=entryJson(entry);
            KNSCore::Entry updated=entry;
            result["transaction"]=runTransaction(e,KNSCore::Transaction::installLatest(&e.engine,entry),timeoutMs,updated);
            result["installed"]=entryJson(updated);
            // The live catalog notices the new package through its single watcher (debounced).
            QSet<QString> after;
            if(provider=="plasmoids")waitFor(5000,[&]{after=catalogIds(catalog);return after!=before;});
            after=catalogIds(catalog);
            QJsonArray added;for(const auto &id:after-before)added.append(id);
            result["catalogAdded"]=added;
        }
    }
    result["errors"]=e.errors;result["questions"]=questions.asked;
    return result;
}

QJsonObject uninstall(const QString &uniqueId,int timeoutMs,const QString &provider) {
    CancelAllQuestions questions;Engine e;Catalog catalog;
    const auto before=catalogIds(catalog);
    QJsonObject result{{"uniqueId",uniqueId}};
    if(e.start(timeoutMs/2,provider)) {
        auto entry=e.exact(uniqueId,timeoutMs/2);
        if(!entry.isValid())e.errors.append("No store entry with that id.");
        else if(entry.status()!=KNSCore::Entry::Installed && entry.status()!=KNSCore::Entry::Updateable)
            e.errors.append("The KNewStuff cache does not list this entry as installed: "+statusName(entry.status()));
        else {
            result["entry"]=entryJson(entry);
            KNSCore::Entry updated=entry;
            result["transaction"]=runTransaction(e,KNSCore::Transaction::uninstall(&e.engine,entry),timeoutMs,updated);
            result["after"]=entryJson(updated);
            QSet<QString> after;
            waitFor(5000,[&]{after=catalogIds(catalog);return after!=before;});
            after=catalogIds(catalog);
            QJsonArray removed;for(const auto &id:before-after)removed.append(id);
            result["catalogRemoved"]=removed;
        }
    }
    result["errors"]=e.errors;result["questions"]=questions.asked;
    return result;
}

QJsonObject metadata(const QString &uniqueId,int timeoutMs,const QString &provider) {
    CancelAllQuestions questions;Engine e;QJsonObject result;
    if(e.start(timeoutMs,provider))result=entryJson(e.exact(uniqueId,timeoutMs));
    result["errors"]=e.errors;result["questions"]=questions.asked;return result;
}
}

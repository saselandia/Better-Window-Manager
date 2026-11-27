// SPDX-License-Identifier: GPL-2.0-or-later
// Test-only native Store client. Never built into or installed as the daily host.
#include "kns.h"
#include <QApplication>
#include <QDir>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonArray>
#include <unistd.h>
int main(int argc,char **argv) {
    for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR","XDG_STATE_HOME"}) {
        const QFileInfo root(qEnvironmentVariable(name));
        if(!root.isDir() || root.isSymLink() || root.ownerId()!=getuid() ||
           !root.canonicalFilePath().startsWith(QDir::tempPath()+"/") ||
           (root.permissions() & (QFile::ReadGroup|QFile::WriteGroup|QFile::ExeGroup|QFile::ReadOther|QFile::WriteOther|QFile::ExeOther))){
            fprintf(stderr,"Store probes require existing disposable XDG roots.\n");return 2;
        }
    }
    QApplication app(argc,argv);const auto args=app.arguments();
    if(args.size()!=4 && !(args.size()==5 && args[2]=="search"))return 2;
    const auto provider=args[1],command=args[2],value=args[3];QJsonObject result;
    if(command=="search")result=BwmKns::search(value,args.size()==5 ? args[4].toInt() : 0,45000,provider);
    else if(command=="metadata")result=BwmKns::metadata(value,45000,provider);
    else if(command=="install")result=BwmKns::install(value,120000,provider);
    else if(command=="uninstall")result=BwmKns::uninstall(value,60000,provider);
    else return 2;
    puts(QJsonDocument(result).toJson().constData());return result.value("errors").toArray().isEmpty()?0:9;
}

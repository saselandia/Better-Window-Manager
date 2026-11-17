// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <KService>
#include <KSycoca>
#include <QCoreApplication>
#include <QDir>
#include <QImage>
#include <QProcess>
#include <QSaveFile>
#include <QtCore/qtestsupport_core.h>

// Test data shared by the native delegate and the offscreen metadata regression.
// Never rely on an application installed in the user's service database, and
// never rebuild that database outside the runner's disposable XDG directories.
struct TaskApplicationFixture {
    QString id,name=QStringLiteral("BWM native delegate fixture"),error;
    bool prepare(const QString &root,const QString &builder){
        if(root.isEmpty() || qEnvironmentVariable("XDG_DATA_HOME")!=root+"/data" ||
            qEnvironmentVariable("XDG_CACHE_HOME")!=root+"/cache" ||
            !qEnvironmentVariableIsEmpty("KDESYCOCA")){
            error="Application fixture requires the runner's private XDG roots";return false;
        }
        id="org.bwm.r4.delegate."+QString::number(QCoreApplication::applicationPid());
        const auto directory=root+"/data/applications",icon=root+"/data/delegate-fixture.png";
        if(!QDir().mkpath(directory)){error="Cannot create fixture application directory";return false;}
        QImage image(16,16,QImage::Format_ARGB32);image.fill(Qt::red);
        if(!image.save(icon)){error="Cannot write fixture icon";return false;}
        QSaveFile desktop(directory+'/'+id+".desktop");
        if(!desktop.open(QIODevice::WriteOnly)){error="Cannot open fixture desktop entry";return false;}
        const auto data=QString("[Desktop Entry]\nType=Application\nName=%1\nExec=/usr/bin/false\nIcon=%2\nStartupWMClass=%3\nNoDisplay=true\n").arg(name,icon,id).toUtf8();
        if(desktop.write(data)!=data.size() || !desktop.commit()){error="Cannot save fixture desktop entry";return false;}
        QProcess build;build.start(builder,{"--noincremental"});
        if(!build.waitForFinished(10000) || build.exitStatus()!=QProcess::NormalExit || build.exitCode()!=0){
            error="Cannot build fixture service database";return false;
        }
        if(!KSycoca::absoluteFilePath().startsWith(root+"/cache/")){
            error="Service database is outside fixture cache";return false;
        }
        if(!QTest::qWaitFor([&]{
            const auto service=KService::serviceByStorageId(id+".desktop");
            return service && service->name()==name;
        },3000)){error="Fixture application missing from native service database";return false;}
        return true;
    }
};

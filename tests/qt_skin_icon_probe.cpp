// SPDX-License-Identifier: GPL-2.0-or-later
// Native Qt/QPA proof in disposable XDG roots. Local receiver mode needs no bus/display.
#include <QApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QIcon>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QTimer>
#include <KIconLoader>

static void write(const QString &path,const QByteArray &bytes) {
    QSaveFile file(path);
    if(!file.open(QIODevice::WriteOnly) || file.write(bytes)!=bytes.size() || !file.commit())qFatal("Cannot write fixture");
}
static void selectTheme(const QString &name) {
    write(qEnvironmentVariable("XDG_CONFIG_HOME")+"/kdeglobals",
          "[KDE]\nwidgetStyle=Fusion\n[Icons]\nTheme="+name.toUtf8()+"\n");
}
int main(int argc,char **argv) {
    if(argc!=2 || QByteArray(argv[1])!="--local-refresh")return 2;
    for(const char *key:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"})
        if(!QFileInfo(qEnvironmentVariable(key)).canonicalFilePath().startsWith(QDir::tempPath()+"/"))return 2;
    const QStringList names{"BwmProbeRetro","BwmProbeBreeze","BwmProbeCustom"};
    const QStringList colors{"#c44234","#3478c4","#7b34c4"};
    for(int i=0;i<names.size();++i) {
        const QString path=qEnvironmentVariable("XDG_DATA_HOME")+"/icons/"+names[i];
        QDir().mkpath(path+"/16x16/actions");
        write(path+"/index.theme","[Icon Theme]\nName="+names[i].toUtf8()+"\nDirectories=16x16/actions\nInherits=hicolor\n[16x16/actions]\nSize=16\nType=Fixed\nContext=Actions\n");
        QImage image(16,16,QImage::Format_ARGB32);image.fill(QColor(colors[i]));
        if(!image.save(path+"/16x16/actions/bwm-transition-fixture.png"))return 3;
    }
    selectTheme(names[0]);
    QApplication app(argc,argv);
    QIcon retained=QIcon::fromTheme("bwm-transition-fixture");
    auto color=[](const QIcon &icon){const auto image=icon.pixmap(16,16).toImage();return image.isNull() ? QStringLiteral("missing") : image.pixelColor(8,8).name();};
    QJsonArray snapshots;
    auto sample=[&]{snapshots.append(QJsonObject{{"theme",QIcon::themeName()},
        {"fresh",color(QIcon::fromTheme("bwm-transition-fixture"))},{"retained",color(retained)}});};
    sample();
    const QList<int> sequence{1,0,2};
    int step=0;
    QTimer timer;
    QObject::connect(&timer,&QTimer::timeout,&app,[&]{
        sample();
        if(step==sequence.size()) {
            puts(QJsonDocument(QJsonObject{{"backend",qEnvironmentVariable("QT_QPA_PLATFORMTHEME")},
                {"snapshots",snapshots},{"explicitIconThemeOverride",false},
                {"transport","local-KF6-receiver"}}).toJson().constData());
            app.quit();return;
        }
        selectTheme(names[sequence[step++]]);
        {
            // Test-only invocation of the installed KF6 receiver (6.29.0 source
            // reviewed). No socket or user-session IPC; transport is NOT tested.
            // Reimplementing it misses Qt's system-theme cache invalidation.
            for(int group=0;group<6;++group)
                if(!QMetaObject::invokeMethod(KIconLoader::global(),"_k_refreshIcons",Qt::DirectConnection,Q_ARG(int,group)))
                    qFatal("Installed native receiver contract changed");
        }
    });
    timer.start(250);
    return app.exec();
}

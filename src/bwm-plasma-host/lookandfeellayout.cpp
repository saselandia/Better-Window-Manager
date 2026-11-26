// SPDX-License-Identifier: GPL-2.0-or-later
#include "lookandfeellayout.h"
#include "layouttemplate.h"
#include "profilestore.h"
#include "viewcorona.h"
#include "outputidentity.h"
#include "panelviewsettings.h"
#include <Plasma/Containment>
#include <KConfig>
#include <KConfigGroup>
#include <KPackage/PackageLoader>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QFile>
#include <QJsonDocument>
#include <QProcess>
#include <QQuickWindow>
#include <QSaveFile>
#include <QScreen>
#include <QTimer>
#include <QRegularExpression>
#include <stdexcept>

namespace {
void writeJson(const QString &path,const QJsonObject &object){QSaveFile f(path);if(!f.open(QIODevice::WriteOnly))throw std::runtime_error("Cannot save native layout metadata");f.write(QJsonDocument(object).toJson());if(!f.commit())throw std::runtime_error("Cannot commit layout metadata");}
QString description(QScreen *s){auto id=BwmOutput::identity(s);return(id.manufacturer+' '+id.model+' '+id.serial).simplified();}
}
LookAndFeelLayout::LookAndFeelLayout(ViewCorona *corona,QString legacy,QString current,std::function<void()> save,QObject *parent,Restart restart)
    :QObject(parent),m_corona(corona),m_legacy(legacy),m_current(current),m_save(std::move(save)),m_restart(std::move(restart)){}
LookAndFeelLayout::~LookAndFeelLayout(){if(m_registered){auto bus=QDBusConnection::sessionBus();bus.unregisterObject("/PlasmaShell");bus.unregisterService("org.kde.plasmashell");}}
bool LookAndFeelLayout::start(){
    auto bus=QDBusConnection::sessionBus();
    // DontQueueService and DontAllowReplacement: never displace a real plasmashell.
    if(!bus.interface()||bus.interface()->registerService("org.kde.plasmashell",QDBusConnectionInterface::DontQueueService,QDBusConnectionInterface::DontAllowReplacement)!=QDBusConnectionInterface::ServiceRegistered)return false;
    if(!bus.registerObject("/PlasmaShell",this,QDBusConnection::ExportScriptableSlots)){bus.unregisterService("org.kde.plasmashell");return false;}
    m_registered=true;m_status={{"registered",true},{"layout",true},{"evaluateScript",false}};return true;
}
bool LookAndFeelLayout::immutable()const{return !m_corona||m_corona->immutability()!=Plasma::Types::Mutable;}
QString LookAndFeelLayout::prepare(const QString &package,const QString &source,const QString &shell){
    if(!QRegularExpression("^[A-Za-z0-9_.-]+$").match(package).hasMatch())throw std::runtime_error("Invalid look-and-feel ID");
    const auto candidate=ProfileStore::checkpointSession(source);
    // Fresh native layout in a new path: no KSharedConfig held by the daily Corona is overwritten.
    {QSaveFile empty(candidate+"/appletsrc");if(!empty.open(QIODevice::WriteOnly)||!empty.commit())throw std::runtime_error("Cannot stage layout");}
    {
        ViewCorona staged;staged.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",shell));
        staged.loadLayout(candidate+"/appletsrc");
        QList<std::shared_ptr<QQuickWindow>> windows;QJsonObject desktopBindings;
        for(auto *screen:QGuiApplication::screens()){
            auto *c=staged.createContainment("org.kde.plasma.folder");if(!c)throw std::runtime_error("Cannot stage desktop");
            auto w=std::make_shared<QQuickWindow>();w->setScreen(screen);staged.bind(c,w.get());windows.append(w);
            const auto desc=description(screen);if(!desc.isEmpty())desktopBindings[QString::number(c->id())]=desc;
        }
        LayoutTemplateRunner runner(&staged,QGuiApplication::primaryScreen(),{});
        if(!runner.runLookAndFeel(package))throw std::runtime_error(runner.error().toStdString());
        if(runner.createdPanels().isEmpty())throw std::runtime_error("Theme layout created no panels");
        QJsonObject bindings;
        for(auto *panel:runner.createdPanels()){
            auto *c=panel->containment();auto *screen=QGuiApplication::screens().value(panel->screen());if(!c||!screen)throw std::runtime_error("Invalid layout output");
            const auto extent=(c->formFactor()==Plasma::Types::Vertical?screen->geometry().height():screen->geometry().width());
            QVariantMap defaults{{"floating",true},{"floatingApplets",false},{"panelOpacity",2},{"thickness",44},
                {"minLength",64},{"maxLength",extent},{"alignment",1},{"panelLengthMode",0},{"offset",0},{"panelVisibility",0}};
            PanelViewSettings settings(candidate+"/plasmashellrc",c->id(),c->formFactor()==Plasma::Types::Vertical,extent,defaults,true);
            auto changes=panel->pendingViewSettings();
            for(const auto &key:{QString("minLength"),QString("maxLength")})
                if(changes.contains(key))changes[key]=qBound(64,changes[key].toInt(),extent);
            if(!settings.reload()||!settings.apply(changes))throw std::runtime_error(settings.error().toStdString());
            const auto desc=description(screen);if(!desc.isEmpty())bindings[QString::number(c->id())]=desc;
        }
        staged.saveLayout(candidate+"/appletsrc");staged.config()->sync();
        writeJson(candidate+"/assignments.json",bindings);writeJson(candidate+"/desktop-assignments.json",desktopBindings);
    }
    ProfileStore::sealSession(candidate);return candidate;
}
void LookAndFeelLayout::loadLookAndFeelDefaultLayout(const QString &package){
    bool editing=m_corona&&m_corona->isEditMode();
    if(m_corona)for(auto *c:m_corona->containments()){
        editing=editing||c->isUserConfiguring();
        for(auto *applet:c->applets())editing=editing||applet->isUserConfiguring();
    }
    if(m_busy||immutable()||editing){if(calledFromDBus())sendErrorReply("org.bwm.LayoutLocked","Close desktop/panel/widget editing before replacing the layout");return;}
    m_busy=true;
    try{
        m_save();const auto previous=ProfileStore::checkpointSession(m_current);
        const auto candidate=prepare(package,previous,QStringLiteral(BWM_SHELL_SOURCE_DIR));
        m_status={{"package",package},{"previous",previous},{"candidate",candidate},{"phase","prepared"}};
        writeJson(m_legacy+"/last-layout.json",m_status);
        const bool launched=m_restart?m_restart(candidate,previous):QProcess::startDetached("python3",{QStringLiteral(BWM_SESSION_UI_HELPER),"replace-layout",QString::number(QCoreApplication::applicationPid()),candidate,previous});
        if(!launched)throw std::runtime_error("Cannot start layout supervisor");
        QTimer::singleShot(100,this,[this]{emit restartRequested();});
    }catch(const std::exception &error){
        m_busy=false;m_status={{"package",package},{"error",QString::fromUtf8(error.what())},{"phase","rejected"}};
        try{writeJson(m_legacy+"/last-layout.json",m_status);}catch(...){}
        QProcess::startDetached("notify-send",{"-a","BWM","No se pudo aplicar la disposición",QString::fromUtf8(error.what())});
        if(calledFromDBus())sendErrorReply("org.bwm.LayoutRejected",QString::fromUtf8(error.what()));
    }
}

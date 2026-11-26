// SPDX-FileCopyrightText: 2000 Matthias Ettrich <ettrich@kde.org>
// SPDX-FileCopyrightText: 2007 Urs Wolfer <uwolfer@kde.org>
// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: MIT
// Theme context/signal contract adapted from plasma-workspace 6.7.5
// logout-greeter/shutdowndlg.cpp. Original installed theme QML is loaded unchanged.
#include "sessionui.h"
#include "themehost.h"
#include <KConfigGroup>
#include <KWindowEffects>
#include <QDBusReply>
#include <QDBusInterface>
#include <KSharedConfig>
#include <KLocalizedContext>
#include <KPackage/PackageLoader>
#include <LayerShellQt/Window>
#include <QDBusAbstractAdaptor>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QGuiApplication>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlPropertyMap>
#include <QQuickView>
#include <QQuickItem>
#include <QScreen>
#include <QProcess>
#include <QTimer>
#include <QEvent>
#include <utility>

class LogoutThemeHost final : public ThemeHost {
public:
    using ThemeHost::ThemeHost;
    void initialize(){componentComplete();}
    QQuickItem *themeItem()const{return childItems().isEmpty()?nullptr:childItems().first();}
};

class LogoutPromptAdapter : public QDBusAbstractAdaptor {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface","org.kde.LogoutPrompt")
public: explicit LogoutPromptAdapter(SessionUi *ui):QDBusAbstractAdaptor(ui),m_ui(ui){}
public Q_SLOTS:
    void promptLogout(){m_ui->prompt("logout");}
    void promptShutDown(){m_ui->prompt("shutdown");}
    void promptReboot(){m_ui->prompt("reboot");}
    void promptAll(){m_ui->prompt("all");}
private:SessionUi *m_ui;
};
class ShutdownAdapter : public QDBusAbstractAdaptor {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface","org.kde.Shutdown")
public:explicit ShutdownAdapter(SessionUi *ui):QDBusAbstractAdaptor(ui),m_ui(ui){}
public Q_SLOTS:
    void logout(){m_ui->logout();}
    void logoutAndShutdown(){m_ui->halt();}
    void logoutAndReboot(){m_ui->reboot();}
private:SessionUi *m_ui;
};
SessionUi::SessionUi(QString helper,QObject *parent):QObject(parent),m_power(helper){}
SessionUi::~SessionUi(){cancel();auto bus=QDBusConnection::sessionBus();if(m_promptOwner){bus.unregisterObject("/LogoutPrompt");bus.unregisterService("org.kde.LogoutPrompt");}if(m_shutdownOwner){bus.unregisterObject("/Shutdown");bus.unregisterService("org.kde.Shutdown");}}
bool SessionUi::start(){
    auto bus=QDBusConnection::sessionBus();auto *iface=bus.interface();if(!iface)return false;
    auto claim=[&](const QString &name){return iface->registerService(name,QDBusConnectionInterface::DontQueueService,QDBusConnectionInterface::DontAllowReplacement)==QDBusConnectionInterface::ServiceRegistered;};
    // Keep existing owners untouched. Only the implemented interfaces are advertised;
    // saveSession deliberately has no method (it is excluded from BWM).
    if(claim("org.kde.LogoutPrompt")){new LogoutPromptAdapter(this);m_promptOwner=bus.registerObject("/LogoutPrompt",this,QDBusConnection::ExportAdaptors);if(!m_promptOwner)bus.unregisterService("org.kde.LogoutPrompt");}
    if(claim("org.kde.Shutdown")){new ShutdownAdapter(this);m_shutdownOwner=bus.registerObject("/Shutdown",this,QDBusConnection::ExportAdaptors);if(!m_shutdownOwner)bus.unregisterService("org.kde.Shutdown");}
    return m_promptOwner;
}
QString SessionUi::logoutSource(const QString &id){
    auto config=KSharedConfig::openConfig("kdeglobals");config->reparseConfiguration();
    auto package=KPackage::PackageLoader::self()->loadPackage("Plasma/LookAndFeel",id.isEmpty()?config->group("KDE").readEntry("LookAndFeelPackage",QString("org.kde.breeze.desktop")):id);
    auto path=package.filePath("logoutmainscript");
    if(path.isEmpty())path=KPackage::PackageLoader::self()->loadPackage("Plasma/LookAndFeel","org.kde.breeze.desktop").filePath("logoutmainscript");
    return path;
}
bool SessionUi::prompt(const QString &action){
    if(!QStringList{"all","logout","shutdown","reboot"}.contains(action))return false;
    if(!m_views.isEmpty())return true;
    const auto source=logoutSource();if(source.isEmpty()){m_error="No logout theme installed";return false;}
    m_error.clear();m_committed=false;++m_generation;
    QDBusInterface login("org.freedesktop.login1","/org/freedesktop/login1","org.freedesktop.login1.Manager",QDBusConnection::systemBus());
    login.setTimeout(800);
    const auto can=[&](const char *method){QDBusReply<QString> reply=login.call(method);return reply.isValid()&&(reply.value()=="yes"||reply.value()=="challenge");};
    const bool canShutdown=can("CanPowerOff"),canSleep=can("CanSuspend"),canHibernate=can("CanHibernate");
    for(auto *screen:QGuiApplication::screens()){
        // Each window owns a separate engine: Qt.quit from a theme closes only this UI.
        auto *view=new QQuickView;
        auto *theme=new LogoutThemeHost(view->contentItem());
        view->setProperty("bwmLogoutTheme",QVariant::fromValue<QObject*>(theme));
        theme->setSize(screen->geometry().size());
        connect(view,&QWindow::widthChanged,theme,[view,theme]{theme->setWidth(view->width());});
        connect(view,&QWindow::heightChanged,theme,[view,theme]{theme->setHeight(view->height());});
        m_views.append(view);view->installEventFilter(this);view->setColor(Qt::transparent);view->setScreen(screen);view->setResizeMode(QQuickView::SizeRootObjectToView);
        connect(theme,&ThemeHost::quitRequested,this,&SessionUi::cancel);
        QVariantMap properties;
        const auto contextProperty=[&](const QString &name,const QVariant &value){properties.insert(name,value);};
        contextProperty("screenGeometry",screen->geometry());
        contextProperty("sdtype",action=="logout"?0:action=="reboot"?1:action=="shutdown"?2:-1);
        auto *types=new QQmlPropertyMap(view);for(const auto &pair:QList<QPair<QString,int>>{{"ShutdownTypeDefault",-1},{"ShutdownTypeNone",0},{"ShutdownTypeReboot",1},{"ShutdownTypeHalt",2},{"ShutdownTypeLogout",3}})types->insert(pair.first,pair.second);
        contextProperty("ShutdownType",QVariant::fromValue<QObject*>(types));contextProperty("maysd",canShutdown);contextProperty("canLogout",true);
        auto *sleep=new QQmlPropertyMap(view);sleep->insert("StandbyState",canSleep);sleep->insert("SuspendState",canSleep);sleep->insert("HibernateState",canHibernate);contextProperty("spdMethods",QVariant::fromValue<QObject*>(sleep));
        for(const char *key:{"rebootToFirmwareSetup","isUefi","rebootToBootLoaderMenu","softwareUpdatePending","choose"})contextProperty(key,false);
        contextProperty("rebootToBootLoaderEntry",QString());contextProperty("bootManager","None");
        auto *options=new QQmlPropertyMap(view);options->insert("options",QStringList());options->insert("default",0);contextProperty("rebootOptions",QVariant::fromValue<QObject*>(options));
        using W=LayerShellQt::Window;auto *layer=W::get(view);layer->setScope("bwm-plasma-logout");layer->setLayer(W::LayerOverlay);layer->setExclusiveZone(-1);layer->setAnchors(W::Anchors(W::AnchorTop)|W::AnchorBottom|W::AnchorLeft|W::AnchorRight);layer->setDesiredSize({0,0});layer->setScreen(screen);layer->setKeyboardInteractivity(W::KeyboardInteractivityExclusive);
        theme->setContextProperties(properties);theme->setSource(QUrl::fromLocalFile(source));theme->initialize();
        if(!m_views.contains(view))return false;
        if(!theme->ready()||!theme->themeItem()){m_error="Cannot load logout theme: "+theme->error();cancel();return false;}
        auto *root=theme->themeItem();
        connect(root,SIGNAL(logoutRequested()),this,SLOT(logout()));connect(root,SIGNAL(haltRequested()),this,SLOT(halt()));
        connect(root,SIGNAL(rebootRequested()),this,SLOT(reboot()));connect(root,SIGNAL(suspendRequested(int)),this,SLOT(suspend(int)));
        connect(root,SIGNAL(lockScreenRequested()),this,SLOT(lock()));connect(root,SIGNAL(cancelRequested()),this,SLOT(cancel()));
        KWindowEffects::enableBlurBehind(view,true);
        connect(screen,&QObject::destroyed,view,&QObject::deleteLater);view->setGeometry(screen->geometry());view->show();
    }
    return !m_views.isEmpty();
}
void SessionUi::cancel(){++m_generation;const auto views=std::exchange(m_views,{});for(const auto &v:views)if(v){v->hide();v->deleteLater();}if(!views.isEmpty())emit closed();}
bool SessionUi::eventFilter(QObject *watched,QEvent *event){
    bool current=false;for(const auto &view:m_views)if(view&&view==watched)current=true;
    const auto generation=m_generation;
    if(current&&event->type()==QEvent::FocusOut)QTimer::singleShot(50,this,[this,generation]{
        if(generation!=m_generation)return;
        auto *focused=QGuiApplication::focusWindow();
        for(const auto &view:m_views)if(view&&view==focused)return;
        cancel(); // original Greeter closes when focus leaves its dialog set
    });
    return false;
}
void SessionUi::execute(const QString &action){if(m_committed)return;m_committed=true;cancel();QProcess::startDetached(m_power,{action,"--confirmed"});}
void SessionUi::logout(){execute("logout");}void SessionUi::halt(){execute("shutdown");}void SessionUi::reboot(){execute("reboot");}
void SessionUi::lock(){execute("lock");}void SessionUi::suspend(int type){if(type==1||type==2)execute("suspend");else if(type==4)execute("hibernate");}
QJsonObject SessionUi::status()const{return{{"windows",m_views.size()},{"promptOwner",m_promptOwner},{"shutdownOwner",m_shutdownOwner},{"error",m_error},{"source",logoutSource()}};}
#include "sessionui.moc"

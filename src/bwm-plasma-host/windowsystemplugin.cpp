// SPDX-License-Identifier: GPL-2.0-or-later
// Process-local KWindowSystem adapter, ABI pinned by CMake. Installed KDE backend
// still owns activation, tokens, exports, shadows and effects. No compositor plugin.
#include "desktopbridge.h"
#include <KWindowSystem>
#include <private/kwindowsystem_p.h>
#include <private/kwindowsystemplugininterface_p.h>
#include <QCoreApplication>
#include <QGuiApplication>
#include <QDir>
#include <QJsonArray>
#include <QJsonObject>
#include <QPluginLoader>
#include <QStandardPaths>
#include <memory>
class BwmWindowSystem final:public KWindowSystemPrivateV5 {
public:
    explicit BwmWindowSystem(KWindowSystemPrivate *original):m_original(original) {
        if(qEnvironmentVariable("BWM_R4_DESKTOP_ACTIONS")=="1") {
            m_desktop=std::make_unique<DesktopBridge>(qEnvironmentVariable("BWM_R4_DESKTOP_RUNTIME"),
                QStandardPaths::findExecutable("python3"),QStringList{QStringLiteral(BWM_WINDOW_MANAGER_SOURCE),"--native-serialized"});
            // Do not recurse into KWindowSystem::self() while its backend is constructed.
            QObject::connect(m_desktop.get(),&DesktopBridge::changed,m_desktop.get(),[](bool active){
                Q_EMIT KWindowSystem::self()->showingDesktopChanged(active);
            });
        }
    }
    void activateWindow(QWindow *w,long t)override{if(m_original)m_original->activateWindow(w,t);}
    bool showingDesktop()override{return enabled()?m_desktop->showingDesktop():m_original && m_original->showingDesktop();}
    void setShowingDesktop(bool b)override{if(enabled())m_desktop->setShowingDesktop(b);else if(m_original)m_original->setShowingDesktop(b);}
#if KWINDOWSYSTEM_BUILD_DEPRECATED_SINCE(6,19)
    void requestToken(QWindow *w,uint32_t s,const QString &id)override{if(auto *p=v2())p->requestToken(w,s,id);}
#endif
    void setCurrentToken(const QString &s)override{if(auto *p=v2())p->setCurrentToken(s);}
    quint32 lastInputSerial(QWindow *w)override{auto *p=v2();return p?p->lastInputSerial(w):0;}
    void setMainWindow(QWindow *w,const QString &h)override{if(auto *p=v2())p->setMainWindow(w,h);}
#if KWINDOWSYSTEM_BUILD_DEPRECATED_SINCE(6,28)
    void exportWindow(QWindow *w)override{if(auto *p=v2())p->exportWindow(w);}
    void unexportWindow(QWindow *w)override{if(auto *p=v2())p->unexportWindow(w);}
#endif
    QFuture<QString> xdgActivationToken(QWindow *w,uint32_t s,const QString &id)override{auto *p=dynamic_cast<KWindowSystemPrivateV3*>(m_original.get());return p?p->xdgActivationToken(w,s,id):QFuture<QString>();}
    void setXdgToplevelTag(QWindow *w,const QString &s)override{if(auto *p=dynamic_cast<KWindowSystemPrivateV4*>(m_original.get()))p->setXdgToplevelTag(w,s);}
    void setXdgToplevelDescription(QWindow *w,const QString &s)override{if(auto *p=dynamic_cast<KWindowSystemPrivateV4*>(m_original.get()))p->setXdgToplevelDescription(w,s);}
    QFuture<QString> exportToplevel(QWindow *w)override{auto *p=dynamic_cast<KWindowSystemPrivateV5*>(m_original.get());return p?p->exportToplevel(w):QFuture<QString>();}
    void unexportToplevel(QWindow *w)override{if(auto *p=dynamic_cast<KWindowSystemPrivateV5*>(m_original.get()))p->unexportToplevel(w);}
private:
    bool enabled()const{return m_desktop && m_desktop->available();}
    KWindowSystemPrivateV2 *v2()const{return dynamic_cast<KWindowSystemPrivateV2*>(m_original.get());}
    std::unique_ptr<KWindowSystemPrivate> m_original;
    std::unique_ptr<DesktopBridge> m_desktop;
};
class BwmWindowSystemPlugin final:public KWindowSystemPluginInterface {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID KWindowSystemPluginInterface_iid FILE "windowsystemplugin.json")
    Q_INTERFACES(KWindowSystemPluginInterface)
public:
    BwmWindowSystemPlugin() {
        // The upstream wrapper checks static plugins first. Delegate everything
        // except showingDesktop to its normal dynamic plugin for this platform.
        for(const auto &base:QCoreApplication::libraryPaths())for(const auto &folder:{"/kf6/org.kde.kwindowsystem.platforms","/kf6/kwindowsystem"}) {
            QDir dir(base+folder);for(const auto &name:dir.entryList(QDir::Files)) {
                auto loader=std::make_unique<QPluginLoader>(dir.absoluteFilePath(name));
                const auto data=loader->metaData();
                if(data.value("IID").toString()!=KWindowSystemPluginInterface_iid)continue;
                if(!data.value("MetaData").toObject().value("platforms").toArray().contains(QGuiApplication::platformName()))continue;
                if(auto *factory=qobject_cast<KWindowSystemPluginInterface*>(loader->instance())){m_factory=factory;m_loader=std::move(loader);return;}
            }
        }
    }
    KWindowSystemPrivate *createWindowSystem()override{return new BwmWindowSystem(m_factory?m_factory->createWindowSystem():nullptr);}
    KWindowEffectsPrivate *createEffects()override{return m_factory?m_factory->createEffects():nullptr;}
    KWindowShadowPrivate *createWindowShadow()override{return m_factory?m_factory->createWindowShadow():nullptr;}
    KWindowShadowTilePrivate *createWindowShadowTile()override{return m_factory?m_factory->createWindowShadowTile():nullptr;}
private:
    std::unique_ptr<QPluginLoader> m_loader;
    KWindowSystemPluginInterface *m_factory=nullptr;
};
#include "windowsystemplugin.moc"

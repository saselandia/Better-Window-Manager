// SPDX-License-Identifier: GPL-2.0-or-later
#include "viewcorona.h"
#include "containmentmanagement.h"
#include "desktopviewhost.h"
#include "outputidentity.h"
#include "traydefaults.h"
#include <Plasma/Containment>
#include <Plasma/PluginLoader>
#include <PlasmaQuick/Dialog>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <KPluginMetaData>
#include <KConfigLoader>
#include <QMap>
#include <QAction>
#include <QGuiApplication>
#include <QIcon>
#include <KLocalizedString>
#include <KWindowSystem>
#include <QMenu>
#include <QQuickWindow>
#include <QQuickItem>
#include <QQuickItemGrabResult>
#include <QScreen>
#include <QLoggingCategory>
#include <QProcess>
#include <QProcessEnvironment>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QTimer>
Q_LOGGING_CATEGORY(lcBwmCorona,"bwm.r5.corona",QtWarningMsg)
namespace {
QScreen *boundScreen(QQuickWindow *window) {
    if(auto *desktop=qobject_cast<DesktopViewHost*>(window))return desktop->screenToFollow();
    return window ? window->screen() : nullptr;
}
}
ViewCorona::ViewCorona() {
    connect(this,&Plasma::Corona::containmentAdded,this,[this](Plasma::Containment *containment){
        connect(containment,&Plasma::Containment::appletCreated,this,[](Plasma::Applet *applet,const QRectF &){
            if(applet->pluginMetaData().pluginId()!=QLatin1String("org.kde.plasma.systemtray"))return;
            auto general=applet->config().group(QStringLiteral("General"));
            if(!BwmTrayDefaults::apply(general,true))return;
            // SystemTraySettings already caches the native registry defaults.
            // Use its own KConfigLoader save/read contract to update that cache.
            if(auto *scheme=applet->configScheme()) {
                for(const auto *key:{"knownItems","extraItems"})if(auto *item=scheme->findItemByName(key)) {
                    item->setWriteFlags(KConfigBase::Notify);
                    item->setProperty(general.readEntry(key,QStringList()));
                }
                scheme->save();scheme->read();
            }
        });
    });
    for(auto *screen:QGuiApplication::screens())observe(screen);
    for(int i=0;i<numScreens();++i)m_screenIds.insert(QGuiApplication::screens()[i],i);
    connect(qApp,&QGuiApplication::screenAdded,this,[this](QScreen *screen){observe(screen);Q_EMIT screenAdded(QGuiApplication::screens().indexOf(screen));notifyScreens();});
    connect(qApp,&QGuiApplication::screenRemoved,this,[this](QScreen *screen){
        m_availableRects.remove(screen);
        const int previous=m_screenIds.value(screen,-1);if(previous>=0)Q_EMIT screenRemoved(previous);notifyScreens();
    });
    // ShellCorona 6.7.5 registers "add panel" on the Corona action collection (read by
    // DesktopEditMode.qml). "edit mode" is libplasma's own Corona action (toggle); only
    // DesktopView's "desktop edit mode" entry marks edit mode as entered via the desktop.
    auto *addPanel=new QAction(QIcon::fromTheme(QStringLiteral("list-add")),i18nd("plasmashell","Add Panel"),this);
    setAction(QStringLiteral("add panel"),addPanel);
    connect(this,&Plasma::Corona::editModeChanged,this,[this](bool edit){
        if(!edit)setEnteredEditModeViaDesktop(false);
    });
    // ShellCorona 6.7.5: edit mode shows the desktop (setDashboardShown(edit)), so the
    // zoomed-out DesktopEditMode.qml is not covered by windows, and leaving "show desktop"
    // leaves edit mode. KWindowSystem::setShowingDesktop reaches BWM's common minimize
    // manager through the host's window-system adapter; only with that adapter enabled.
    if(qEnvironmentVariable("BWM_R4_DESKTOP_ACTIONS")==QLatin1String("1")) {
        connect(this,&Plasma::Corona::editModeChanged,this,[](bool edit){KWindowSystem::setShowingDesktop(edit);});
        connect(KWindowSystem::self(),&KWindowSystem::showingDesktopChanged,this,[this](bool showing){
            if(!showing && isEditMode())setEditMode(false);
        });
    }
    auto *manage=new QAction(QIcon::fromTheme(QStringLiteral("video-display")),i18ndc("plasmashell","@action:button","Manage Desktops and Panels…"),this);
    setAction(QStringLiteral("manage-containments"),manage);
    connect(manage,&QAction::triggered,this,&ViewCorona::showContainmentManagement);
    connect(this,&Plasma::Corona::containmentAdded,this,[this](Plasma::Containment *c){
        connect(c,&Plasma::Containment::screenChanged,this,&ViewCorona::updateManagementAction);
        connect(c,&Plasma::Applet::destroyedChanged,this,&ViewCorona::updateManagementAction);
        updateManagementAction();
    });
    connect(this,&Plasma::Corona::screenRemoved,this,&ViewCorona::updateManagementAction);
    connect(this,&Plasma::Corona::immutabilityChanged,this,&ViewCorona::updateManagementAction);
    updateManagementAction();
}
ViewCorona::~ViewCorona() {
    delete m_management.data();
    delete m_addPanelMenu.data();
    for(const auto &view:m_ownedDesktops)delete view.data();
    // Corona destroys its containments in the base destructor, after our map dies.
    for(auto *containment:m_views.keys())forget(containment);
}
void ViewCorona::updateManagementAction() {
    auto *manage=action(QStringLiteral("manage-containments"));if(!manage)return;
    QSet<int> ids;for(auto *c:containments())if(!c->destroyed())ids.insert(c->screen()>=0?c->screen():c->lastScreen());
    manage->setVisible(ids.size()>1);manage->setEnabled(immutability()==Plasma::Types::Mutable);
}
void ViewCorona::showContainmentManagement() {
    if(!m_desktopViewsActive || immutability()!=Plasma::Types::Mutable)return;
    // ShellCorona leaves desktop edit mode before swapping desktop surfaces.
    setEditMode(false);
    if(m_management && m_management->window()){m_management->window()->show();m_management->window()->requestActivate();return;}
    auto *view=new ContainmentManagement(this);
    if(!view->init()){qWarning()<<"The native Plasma containment manager did not load";delete view;return;}
    m_management=view;
}
QWindow *ViewCorona::managementWindow()const{return m_management ? m_management->window() : nullptr;}
void ViewCorona::setDesktopViewsActive(bool active) {
    if(m_desktopViewsActive==active)return;
    m_desktopViewsActive=active;
    if(!active){
        setEditMode(false);
        if(m_management && m_management->window())m_management->window()->close();
        if(m_addPanelMenu)m_addPanelMenu->close();
    }
    for(const auto &view:m_ownedDesktops)if(view){
        if(active && view->screenToFollow())view->show();
        else {
            view->hide();
            if(auto *configuration=view->configurationWindow())configuration->hide();
            if(auto *side=view->sidePanel())side->hide();
            if(auto *alternatives=view->alternativesDialog())alternatives->hide();
        }
    }
}
QQuickWindow *ViewCorona::viewForContainment(const Plasma::Containment *c)const{return m_views.value(c).window.data();}
bool ViewCorona::moveContainmentToScreen(Plasma::Containment *c,int id) {
    const auto screens=QGuiApplication::screens();
    if(!m_desktopViewsActive || !c || c->corona()!=this || c->destroyed() || c->immutable() || immutability()!=Plasma::Types::Mutable || id<0 || id>=screens.size())return false;
    auto *target=screens[id];
    const auto identity=BwmOutput::identity(target);
    const auto description=(identity.manufacturer+' '+identity.model+' '+identity.serial).simplified();
    if(description.isEmpty() || BwmOutput::resolveScreen(description)!=target)return false;
    if(c->screen()==id)return true;
    if(!isDesktop(c)) {
        emit movePanelRequested(c,target);
        return viewForContainment(c) && viewForContainment(c)->screen()==target;
    }
    auto *source=qobject_cast<DesktopViewHost*>(viewForContainment(c));
    auto *old=source ? source->screenToFollow() : nullptr;
    const int oldId=c->screen()>=0 ? c->screen() : c->lastScreen();
    DesktopViewHost *other=nullptr;
    for(auto it=m_views.cbegin();it!=m_views.cend();++it)
        if(isDesktop(it.key()) && it.key()!=c && boundScreen(it.value().window.data())==target) {
            other=qobject_cast<DesktopViewHost*>(it.value().window.data());break;
        }
    // A disconnected desktop can have no view yet. Recreate its host while
    // retaining the containment and all widget objects from the native layout.
    if(!source) {
        source=new DesktopViewHost(this,other ? other->usesLayerShell() : QGuiApplication::platformName()==QStringLiteral("wayland"),target);
        bind(c,source);
        if(!source->load(c)){unbind(c);delete source;return false;}
        m_ownedDesktops.append(source);
    }
    // The layer-shell output cannot be changed while mapped. Each host recreates
    // only its platform surface, retaining its real containment and widget objects.
    if(other) {
        if(!old && oldId>=0)m_pendingScreens.insert(other->containment(),oldId);
        const bool moved=other->setScreenToFollow(old);
        m_pendingScreens.remove(other->containment());other->containment()->reactToScreenChange();
        if(!moved)return false;
    }
    if(!source->setScreenToFollow(target)){if(other)other->setScreenToFollow(target);return false;}
    source->show();
    requestConfigSync();return true;
}
QString ViewCorona::containmentPreviewPath(Plasma::Containment *c)const {
    if(!c)return {};
    if(m_previews.contains(c->id()))return m_previews.value(c->id());
    const auto wallpaper=c->config().group(QStringLiteral("Wallpaper")).group(c->wallpaperPlugin()).group(QStringLiteral("General"));
    return wallpaper.readEntry(QStringLiteral("Image"),QString());
}
void ViewCorona::grabContainmentPreview(Plasma::Containment *c) {
    auto *view=viewForContainment(c);
    if(!c || !view || !view->isExposed() || !m_previewDirectory.isValid() || m_previewPending.contains(c->id()))return;
    const auto result=view->contentItem()->grabToImage(view->size().scaled(QSize(512,512),Qt::KeepAspectRatio));
    if(!result)return;
    const auto id=c->id();m_previewPending.insert(id);QPointer<Plasma::Containment> owner(c);
    connect(result.data(),&QQuickItemGrabResult::ready,this,[this,result,owner,id]{
        m_previewPending.remove(id);if(!owner || owner->destroyed())return;
        const auto path=m_previewDirectory.filePath(QString::number(id)+QStringLiteral(".png"));
        if(result->saveToFile(path)){m_previews.insert(id,path);emit containmentPreviewReady(owner,path);}
    });
}
void ViewCorona::setEnteredEditModeViaDesktop(bool viaDesktop) {
    if(m_enteredEditModeViaDesktop==viaDesktop)return;
    m_enteredEditModeViaDesktop=viaDesktop;
    Q_EMIT enteredEditModeViaDesktopChanged();
}
void ViewCorona::setPanelBeingConfigured(QObject *panel) {
    if(m_panelBeingConfigured==panel)return;
    m_panelBeingConfigured=panel;
    Q_EMIT panelBeingConfiguredChanged();
}
QMenu *ViewCorona::addPanelMenu()const{return m_addPanelMenu.data();}
void ViewCorona::showAddPanelContextMenu(const QPoint &pos) {
    // ShellCorona::showAddPanelContextMenu + populateAddPanelsMenu (plasma-workspace 6.7.5):
    // Panel containment plugins as "Empty <name>" and panel layout templates, sorted by name.
    if(immutability()!=Plasma::Types::Mutable)return;
    delete m_addPanelMenu.data();
    QPointer<QScreen> target=QGuiApplication::screenAt(pos);
    if(!target)target=QGuiApplication::primaryScreen();
    auto *menu=new QMenu();
    menu->setAttribute(Qt::WA_DeleteOnClose);
    QMap<QString,QPair<KPluginMetaData,KPluginMetaData>> sorted;
    for(const KPluginMetaData &plugin:Plasma::PluginLoader::listContainmentsMetaDataOfType(QStringLiteral("Panel"))) {
        if(plugin.rawData().value(u"NoDisplay").toBool())continue;
        sorted.insert(plugin.name(),qMakePair(plugin,KPluginMetaData()));
    }
    auto filter=[](const KPluginMetaData &md)->bool{
        return !md.rawData().value(u"NoDisplay").toBool() && md.value(u"X-Plasma-ContainmentCategories",QStringList()).contains(QLatin1String("panel"));
    };
    for(const auto &tpl:KPackage::PackageLoader::self()->findPackages(QStringLiteral("Plasma/LayoutTemplate"),QString(),filter))
        sorted.insert(tpl.name(),qMakePair(KPluginMetaData(),tpl));
    KPackage::Package package=KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/LayoutTemplate"));
    for(auto it=sorted.cbegin();it!=sorted.cend();++it) {
        QAction *action=nullptr;
        if(it.value().first.isValid()) {
            const KPluginMetaData plugin=it.value().first;
            action=menu->addAction(i18ndc("plasmashell","Creates an empty containment (%1 is the containment name)","Empty %1",plugin.name()));
            if(!plugin.iconName().isEmpty())action->setIcon(QIcon::fromTheme(plugin.iconName()));
            action->setData(plugin.pluginId());
        } else {
            const KPluginMetaData plugin=it.value().second;
            package.setPath(plugin.pluginId());
            if(package.filePath("mainscript").isEmpty())continue;
            action=menu->addAction(plugin.name());
            action->setData(QStringLiteral("plasma-desktop-template:%1").arg(plugin.pluginId()));
        }
        action->setObjectName(action->data().toString());
    }
    connect(menu,&QMenu::triggered,this,[this,target](QAction *action){
        const QString plugin=action->data().toString();
        const auto fallback=[this,target,plugin]{
            if(immutability()!=Plasma::Types::Mutable)return;
            auto *focused=QGuiApplication::focusWindow();
            Q_EMIT addPanelRequested(plugin,focused ? focused->screen() : target.data());
        };
        // Plasma asks KWin for the active output when the action is selected.
        // Ask Hyprland asynchronously, resolving its physical description through
        // the same identity rules as saved panel assignments.
        if(qEnvironmentVariableIsEmpty("HYPRLAND_INSTANCE_SIGNATURE")){fallback();return;}
        auto *query=new QProcess(this);
        auto environment=QProcessEnvironment::systemEnvironment();
        const auto runtime=qEnvironmentVariable("BWM_R5_HYPR_RUNTIME");
        if(!runtime.isEmpty())environment.insert(QStringLiteral("XDG_RUNTIME_DIR"),runtime);
        query->setProcessEnvironment(environment);
        auto finish=[this,query,plugin,fallback]{
            const auto monitors=QJsonDocument::fromJson(query->readAllStandardOutput()).array();
            query->deleteLater();
            if(immutability()!=Plasma::Types::Mutable)return;
            for(const auto &value:monitors){
                const auto monitor=value.toObject();
                if(!monitor.value(QStringLiteral("focused")).toBool())continue;
                if(auto *screen=BwmOutput::resolveScreen(monitor.value(QStringLiteral("description")).toString())){
                    Q_EMIT addPanelRequested(plugin,screen);return;
                }
            }
            fallback();
        };
        connect(query,&QProcess::finished,this,finish);
        connect(query,&QProcess::errorOccurred,this,[query,finish](QProcess::ProcessError error){if(error==QProcess::FailedToStart)finish();});
        QTimer::singleShot(1500,query,[query]{if(query->state()!=QProcess::NotRunning)query->kill();});
        query->start(QStringLiteral("hyprctl"),{QStringLiteral("-j"),QStringLiteral("monitors")},QIODevice::ReadOnly);
    });
    m_addPanelMenu=menu;
    menu->popup(pos);
}
int ViewCorona::numScreens()const{return QGuiApplication::screens().size();}
QRect ViewCorona::screenGeometry(int id)const {
    const auto screens=QGuiApplication::screens();
    if(id==-1){QRect full;for(auto *screen:screens)full=full.united(screen->geometry());return full;}
    return id>=0 && id<screens.size() ? screens[id]->geometry() : QRect();
}
QRect ViewCorona::availableScreenRect(int id)const {
    const auto screens=QGuiApplication::screens();
    if(id<0 || id>=screens.size())return {};
    auto *screen=screens[id];
    const QRect published=m_availableRects.value(screen);
    if(published.isValid() && !published.isEmpty() && screen->geometry().contains(published))return published;
    return screen->availableGeometry();
}
QRegion ViewCorona::availableScreenRegion(int id)const{return availableScreenRect(id);}
void ViewCorona::setScreenAvailableRect(QScreen *screen,const QRect &rect) {
    if(!screen)return;
    const QRect previous=m_availableRects.value(screen);
    const QRect next=(rect.isValid() && !rect.isEmpty() && screen->geometry().contains(rect)) ? rect : QRect();
    if(previous==next)return;
    if(next.isValid())m_availableRects.insert(screen,next);
    else m_availableRects.remove(screen);
    const int id=QGuiApplication::screens().indexOf(screen);
    if(id>=0){Q_EMIT availableScreenRectChanged(id);Q_EMIT availableScreenRegionChanged(id);}
}
bool ViewCorona::isDesktop(const Plasma::Containment *containment) {
    return containment && containment->containmentType()!=Plasma::Containment::Panel
        && containment->containmentType()!=Plasma::Containment::CustomPanel;
}
int ViewCorona::screenForContainment(const Plasma::Containment *containment)const {
    if(m_pendingScreens.contains(containment))return m_pendingScreens.value(containment);
    auto *window=m_views.value(containment).window.data();
    const int screen=QGuiApplication::screens().indexOf(boundScreen(window));
    // ShellCorona 6.7.5 shows the desktop view and its panels before the desktop containment
    // gets its screen; the original Folder View evaluates corona.isScreenUiReady(screen) only
    // when that screen changes. Keep desktops screenless until their view and panels are ready.
    // Once assigned it is kept (ShellCorona does not take it back when a panel is added later).
    if(screen>=0 && isDesktop(containment) && !m_desktopsWithScreen.contains(containment)) {
        if(!window->isVisible() || !panelsReady(screen)){
            qCInfo(lcBwmCorona)<<"desktop"<<containment->id()<<"waits: visible"<<window->isVisible()<<"panelsReady"<<panelsReady(screen);
            return -1;
        }
        qCInfo(lcBwmCorona)<<"desktop"<<containment->id()<<"gets screen"<<screen;
        m_desktopsWithScreen.insert(containment);
    }
    return screen;
}
bool ViewCorona::panelsReady(int screen)const {
    for(auto it=m_views.constBegin();it!=m_views.constEnd();++it) {
        auto *window=it.value().window.data();
        if(!window || isDesktop(it.key()) || QGuiApplication::screens().indexOf(window->screen())!=screen)continue;
        if(!window->isVisible() || !it.key()->isUiReady()){
            qCInfo(lcBwmCorona)<<"panel"<<it.key()->id()<<"not ready: visible"<<window->isVisible()<<"uiReady"<<it.key()->isUiReady();
            return false;
        }
    }
    return true;
}
bool ViewCorona::isScreenUiReady(int screen)const {
    // ShellCorona::isScreenUiReady 6.7.5: the screen's desktop view is visible and every panel
    // view on it is visible with its containment UI ready. Screens without a desktop view
    // (panel-only hosts) only check their panels.
    if(screen<0 || screen>=numScreens())return false;
    for(auto it=m_views.constBegin();it!=m_views.constEnd();++it) {
        auto *window=it.value().window.data();
        if(window && isDesktop(it.key()) && QGuiApplication::screens().indexOf(boundScreen(window))==screen && !window->isVisible())return false;
    }
    return panelsReady(screen);
}
void ViewCorona::updateDesktopScreens() {
    for(auto it=m_views.cbegin();it!=m_views.cend();++it)
        if(isDesktop(it.key()))const_cast<Plasma::Containment*>(it.key())->reactToScreenChange();
}
void ViewCorona::bind(Plasma::Containment *containment,QQuickWindow *window) {
    if(!containment || containment->corona()!=this || !window)return;
    if(m_views.contains(containment) && m_views.value(containment).window==window)return;
    forget(containment);
    Binding binding;binding.window=window;
    binding.containmentDestroyed=connect(containment,&QObject::destroyed,this,[this,containment]{forget(containment);});
    binding.windowDestroyed=connect(window,&QObject::destroyed,this,[this,containment]{forget(containment);containment->reactToScreenChange();});
    binding.screenChanged=connect(window,&QQuickWindow::screenChanged,this,[containment]{containment->reactToScreenChange();});
    if(auto *desktop=qobject_cast<DesktopViewHost*>(window))
        binding.targetChanged=connect(desktop,&DesktopViewHost::screenToFollowChanged,this,[containment]{containment->reactToScreenChange();});
    binding.windowVisible=connect(window,&QWindow::visibleChanged,this,[this]{updateDesktopScreens();});
    binding.uiReady=connect(containment,&Plasma::Containment::uiReadyChanged,this,[this]{updateDesktopScreens();});
    m_views.insert(containment,binding);
    containment->reactToScreenChange();
    if (isDesktop(containment)) Q_EMIT desktopViewBound(containment);
}
void ViewCorona::forget(const Plasma::Containment *containment) {
    m_desktopsWithScreen.remove(containment);
    const auto binding=m_views.take(containment);
    disconnect(binding.containmentDestroyed);disconnect(binding.windowDestroyed);disconnect(binding.screenChanged);
    disconnect(binding.targetChanged);
    disconnect(binding.windowVisible);disconnect(binding.uiReady);
}
void ViewCorona::unbind(Plasma::Containment *containment) {
    if(!containment || !m_views.contains(containment))return;
    forget(containment);containment->reactToScreenChange();
}
void ViewCorona::observe(QScreen *screen) {
    connect(screen,&QScreen::geometryChanged,this,[this]{notifyScreens();});
    connect(screen,&QScreen::availableGeometryChanged,this,[this]{notifyScreens();});
}
void ViewCorona::notifyScreens() {
    m_screenIds.clear();for(int i=0;i<numScreens();++i)m_screenIds.insert(QGuiApplication::screens()[i],i);
    for(int i=0;i<numScreens();++i) {
        Q_EMIT screenGeometryChanged(i);Q_EMIT availableScreenRectChanged(i);Q_EMIT availableScreenRegionChanged(i);
    }
    for(auto it=m_views.cbegin();it!=m_views.cend();++it)const_cast<Plasma::Containment*>(it.key())->reactToScreenChange();
}

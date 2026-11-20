// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelruntime.h"
#include <QAction>
#include "viewcorona.h"
#include "panelviewhost.h"
#include "panelclone.h"
#include "layouttemplate.h"
#include <KConfig>
#include <KConfigGroup>
#include <QLockFile>
#include "panelviewsettings.h"
#include "outputidentity.h"
#include "panelsession.h"
#include "packagewindows.h"
#include "surfaces.h"
#include "taskbridge.h"
#include "desktopbridge.h"
#include "nativedesktopcontrol.h"
#include <Plasma/Containment>
#include <QGuiApplication>
#include <QScreen>
#include <QScopedValueRollback>
#include <algorithm>

namespace {
Qt::Edge edge(Plasma::Types::Location value) {
    switch(value){case Plasma::Types::TopEdge:return Qt::TopEdge;case Plasma::Types::BottomEdge:return Qt::BottomEdge;
    case Plasma::Types::LeftEdge:return Qt::LeftEdge;case Plasma::Types::RightEdge:return Qt::RightEdge;default:return Qt::Edge(0);}
}
QString edgeName(Qt::Edge value) {
    switch (value) {
    case Qt::LeftEdge: return QStringLiteral("left");
    case Qt::TopEdge: return QStringLiteral("top");
    case Qt::RightEdge: return QStringLiteral("right");
    case Qt::BottomEdge: return QStringLiteral("bottom");
    }
    return {};
}
}
PanelRuntime::PanelRuntime(ViewCorona *corona,QString settings,bool layers,QObject *parent,bool nativePanelPolicy)
    :QObject(parent),m_corona(corona),m_settingsFile(std::move(settings)),m_layerSurfaces(layers),m_nativePanelPolicy(nativePanelPolicy) {
    m_reconcile.setSingleShot(true);m_reconcile.setInterval(0);
    connect(&m_reconcile,&QTimer::timeout,this,&PanelRuntime::reconcile);
    if(corona)connect(corona,&Plasma::Corona::editModeChanged,&m_reconcile,qOverload<>(&QTimer::start));
    if(corona)connect(corona,&ViewCorona::movePanelRequested,this,[this](Plasma::Containment *c,QScreen *target){
        if(c && view(c->id()))moveToOutput(c->id(),target);
    });
    if(auto *control=NativeDesktopControl::requiredControl(this))connect(control,&NativeDesktopControl::changed,this,[this,control]{
        if(m_skin=="plasma"){
            if(!control->resumed()){
                BwmTaskBridge::suspendAll(true);DesktopBridge::suspendAll(true);
                // Hide input surfaces before returning to Wayland event
                // dispatch. Actual teardown stays in the queued reconcile.
                const auto frames=m_views.values();
                for(const auto &frame:frames)if(frame){
                    frame->setProperty("bwmControlWithdrawn",true);
                    frame->hide();
                    if(frame && frame->panelSession())frame->panelSession()->packageWindows()->suspend();
                }
            }
            else if(!m_quiescing){BwmTaskBridge::suspendAll(false);DesktopBridge::suspendAll(false);}
        }
        m_reconcile.start();
    });
    for(auto *screen:QGuiApplication::screens())observe(screen);
    connect(qApp,&QGuiApplication::screenAdded,this,[this](QScreen *screen){observe(screen);m_reconcile.start();});
    // Withdraw immediately: never leave a panel visible on Qt's fallback output.
    connect(qApp,&QGuiApplication::screenRemoved,this,[this](QScreen *screen){
        for(uint id:m_views.keys())if(m_views.value(id) && m_views.value(id)->property("bwmRuntimeScreen").value<QScreen*>()==screen)drop(id);
        reconcile();
    });
}
PanelRuntime::~PanelRuntime(){m_reconcile.stop();dropAll();}
PanelViewHost *PanelRuntime::view(uint id)const{return m_views.value(id).data();}
QHash<uint,QString> PanelRuntime::assignments()const {
    QHash<uint,QString> result;
    if(m_corona)for(auto *c:m_corona->containments())if(!c->destroyed() && m_assignments.contains(c->id()))result.insert(c->id(),m_assignments.value(c->id()));
    return result;
}
QVariantMap PanelRuntime::readiness()const {
    QVariantList outputs;
    for(auto *screen:QGuiApplication::screens()) {
        const auto identity=BwmOutput::identity(screen);
        const auto geometry=screen->geometry();
        outputs.append(QVariantMap{{"manufacturer",identity.manufacturer},{"model",identity.model},{"serial",identity.serial},
            {"serialAvailable",!identity.serial.trimmed().isEmpty()},
            {"description",(identity.manufacturer+' '+identity.model+' '+identity.serial).simplified()},
            {"name",screen->name()}, // Diagnostic only, never a persistent binding.
            {"geometry",QVariantMap{{"x",geometry.x()},{"y",geometry.y()},{"width",geometry.width()},{"height",geometry.height()}}}});
    }
    QVariantList panels;bool rendered=m_skin=="plasma" && !m_status.isEmpty() && m_error.isEmpty();
    QStringList blockers{"isolated-preview-only","session-validation-pending"};
    if(m_skin!="plasma")blockers.append("skin-inactive");
    if(m_status.isEmpty())blockers.append("no-panels");
    if(!m_error.isEmpty())blockers.append("runtime-error");
    for(const auto &value:m_status) {
        auto row=value.toMap();const auto id=row.value("containmentId").toUInt();auto *frame=view(id);
        auto presentation=frame ? frame->presentationState() : QVariantMap();
        const bool matched=frame && frame->screen()==BwmOutput::resolveScreen(m_assignments.value(id)) &&
            row.value("status")=="visible";
        const bool ready=matched && presentation.value("renderReady").toBool();rendered=rendered && ready;
        QStringList reasons;
        const auto widgets=frame && frame->panelSession() ? frame->panelSession()->widgetBackends() : QVariantList();
        bool backendsVerified=frame && frame->panelSession() && !widgets.isEmpty();
        if(widgets.isEmpty())reasons.append("widget-inventory-unavailable-or-empty");
        for(const auto &widget:widgets) {
            const auto data=widget.toMap(),assessment=data.value("runtime").toMap();
            const bool verified=assessment.value("operationalVerified").toBool() && !data.value("failedToLaunch").toBool();
            backendsVerified=backendsVerified && verified;
            const QString reason=data.value("failedToLaunch").toBool()?"widget-launch-failed":
                assessment.value("status")=="requires-backend-adapter"?"widget-backend-adapter-required":"widget-runtime-unverified";
            if(!verified && !reasons.contains(reason))reasons.append(reason);
        }
        row["widgetBackends"]=widgets;row["widgetBackendsVerified"]=backendsVerified;
        row["packageWindows"]=frame && frame->panelSession() ? frame->panelSession()->packageWindows()->capabilities() : QVariantList();
        row["widgetInventoryScope"]="direct-panel-instances";
        if(!matched)reasons.append(row.value("status")=="visible"?QString("output-changed"):row.value("status").toString());
        if(frame && !presentation.value("nativeViewLoaded").toBool())reasons.append("native-view-not-loaded");
        if(frame && !presentation.value("exposed").toBool())reasons.append("surface-not-exposed");
        if(frame && !presentation.value("visible").toBool())reasons.append("surface-hidden");
        if(frame && !presentation.value("frameSubmitted").toBool())reasons.append("frame-not-submitted");
        if(!presentation.value("renderError").toString().isEmpty())reasons.append("scene-graph-error");
        if(!presentation.value("surfaceError").toString().isEmpty())reasons.append("surface-policy-error");
        const auto capabilities=frame ? frame->capabilities() : QVariantMap();
        row["capabilities"]=capabilities;
        const bool requested=capabilities.value("reservationRequested").toBool();
        if(!capabilities.value("reservedArea").toBool())reasons.append(requested?"reserved-area-unverified":"reserved-area-unavailable");
        row["reservationRequested"]=requested;row["exclusiveZoneRequested"]=capabilities.value("exclusiveZoneRequested",-1);
        row["visible"]=frame && frame->isVisible();
        row["presentation"]=presentation;row["renderReady"]=ready;row["blockers"]=reasons;
        row["surfaceRole"]=m_nativePanelPolicy?"native-policy-test":m_layerSurfaces?"layer-preview":"window-preview";
        panels.append(row);for(const auto &reason:reasons)if(!blockers.contains(reason))blockers.append(reason);
    }
    // No production authority is installed. Even a successful software-rendered
    // frame cannot authorize withdrawing the user's existing daily panel.
    return {{"version",1},{"scope","isolated-preview"},{"skin",m_skin},{"renderReady",rendered},
        {"nativeActionsQuiescing",m_quiescing},
        {"nativeDesktopControl",NativeDesktopControl::diagnostics()},
        {"qtPlatform",QGuiApplication::platformName()},{"availableOutputs",outputs},{"taskSource",BwmTaskBridge::diagnostics()},
        {"replacementReady",false},{"nativePanelPolicy",m_nativePanelPolicy},{"blockers",blockers},{"panels",panels}};
}
void PanelRuntime::observe(QScreen *screen) {
    connect(screen,&QScreen::geometryChanged,&m_reconcile,qOverload<>(&QTimer::start));
    connect(screen,&QScreen::availableGeometryChanged,&m_reconcile,qOverload<>(&QTimer::start));
}
bool PanelRuntime::setAssignments(const QHash<uint,QString> &outputs) {
    if(!m_corona){m_error=tr("A live native Corona is required.");emit changed();return false;}
    if(m_nativePanelPolicy && !m_layerSurfaces){m_error=tr("Native panel policy requires layer surfaces.");emit changed();return false;}
    if(m_settingsFile.trimmed().isEmpty()){m_error=tr("A native view preferences file is required.");emit changed();return false;}
    QSet<uint> expected;
    for(auto *c:m_corona->containments())if(!c->destroyed()) {
        if(c->containmentType()!=Plasma::Containment::Panel && c->containmentType()!=Plasma::Containment::CustomPanel)
            continue;
        expected.insert(c->id());
    }
    if(expected.isEmpty() || QSet<uint>(outputs.keyBegin(),outputs.keyEnd())!=expected){m_error=tr("Bindings must cover exactly the live native panels.");emit changed();return false;}
    for(const auto &description:outputs)if(BwmOutput::resolve(description,{}).status=="invalid-output-description") {
        m_error=tr("Panel bindings require output descriptions, not connector names.");emit changed();return false;
    }
    const auto before=m_status;const bool clearedError=!m_error.isEmpty();
    m_assignments=outputs;m_error.clear();reconcile();if(clearedError && before==m_status)emit changed();return true;
}
bool PanelRuntime::setSkin(const QString &value) {
    if(value!="plasma" && value!="retro" && value!="default"){m_error=tr("Unknown BWM skin.");emit changed();return false;}
    auto *control=NativeDesktopControl::requiredControl();
    const auto peer=control?control->ensurePaused(value!="plasma"):NativeDesktopControl::Status::Ready;
    const bool suspend=value!="plasma" || peer!=NativeDesktopControl::Status::Ready;
    const bool taskIdle=BwmTaskBridge::suspendAll(suspend);
    const bool desktopIdle=DesktopBridge::suspendAll(suspend);
    m_quiescing=peer==NativeDesktopControl::Status::Pending || (value!="plasma" && (!taskIdle || !desktopIdle));
    if(peer==NativeDesktopControl::Status::Unavailable){m_error=control->state().value("lastError").toString();m_quiescing=false;return false;}
    if(m_quiescing){m_error=tr("Waiting for native panel actions to finish.");return false;}
    const auto before=m_status;const bool notify=m_skin!=value || !m_error.isEmpty();
    m_skin=value;m_error.clear();reconcile();if(notify && before==m_status)emit changed();return true;
}
void PanelRuntime::moveToOutput(uint id,QScreen *target) {
    auto *frame=view(id);if(!frame || !target || !QGuiApplication::screens().contains(target))return;
    if(!m_outputMovesAllowed){frame->setError(tr("Moving the panel to another output is not available in this host."));return;}
    const auto identity=BwmOutput::identity(target);
    const auto description=(identity.manufacturer+' '+identity.model+' '+identity.serial).simplified();
    QString state;
    if(description.isEmpty() || BwmOutput::resolveScreen(description,&state)!=target) {
        frame->setError(tr("The target output has no unique description."));return;
    }
    frame->setError({});
    if(frame->userConfiguring())m_reopenSettings.insert(id);
    m_assignments[id]=description;reconcile();
}
void PanelRuntime::cloneToOutput(uint id,int location,QScreen *target) {
    auto *frame=view(id);if(!frame || !m_corona)return;
    if(!m_panelCloningAllowed){frame->setError(tr("Cloning panels is not available in this host."));return;}
    if(!target || !QGuiApplication::screens().contains(target) || edge(Plasma::Types::Location(location))==Qt::Edge(0)) {
        frame->setError(tr("Cloning requires a live output and a panel edge."));return;
    }
    const auto identity=BwmOutput::identity(target);
    const auto description=(identity.manufacturer+' '+identity.model+' '+identity.serial).simplified();
    if(description.isEmpty() || BwmOutput::resolveScreen(description)!=target) {
        frame->setError(tr("The target output has no unique description."));return;
    }
    auto *source=frame->containment();
    if(!source || source->immutability()!=Plasma::Types::Mutable || m_corona->immutability()!=Plasma::Types::Mutable) {
        frame->setError(tr("Cloning is locked by KDE policy."));return;
    }
    // Same native preferences transaction lock as PanelViewSettings. Keep every
    // unknown subgroup/key and resolution scope, as ShellCorona::clonePanelTo.
    PanelViewSettings settings(m_settingsFile,id,false,1,{});QLockFile lock(settings.lockPath());
    if(!lock.tryLock(0)){frame->setError(tr("Another BWM panel preference transaction is running."));return;}
    auto *copy=m_corona->createContainment(source->pluginName());
    if(!copy || copy->failedToLaunch()) {if(copy)delete copy;frame->setError(tr("Cannot create the cloned panel."));return;}
    const auto discard=[this,copy] {
        QList<Plasma::Applet*> pending{copy};QList<uint> ids;
        while(!pending.isEmpty()) {auto *a=pending.takeLast();ids.append(a->id());
            if(auto *c=qobject_cast<Plasma::Containment*>(a))for(auto *child:c->applets())pending.append(child);}
        auto config=copy->config();delete copy;config.deleteGroup();
        for(uint id:ids)m_corona->config()->group("Applets").group(QString::number(id)).deleteGroup();
    };
    if(!copyPanelConfiguration(source,copy)) {discard();frame->setError(tr("Cannot copy native widget configuration."));return;}
    KConfig preferences(m_settingsFile,KConfig::FullConfig);
    auto from=KConfigGroup(&preferences,"PlasmaViews").group(QString("Panel %1").arg(id));
    auto to=KConfigGroup(&preferences,"PlasmaViews").group(QString("Panel %1").arg(copy->id()));
    from.copyTo(&to);
    if(!preferences.sync()){preferences.markAsClean();discard();frame->setError(tr("Cannot sync cloned panel preferences."));return;}
    copy->setLocation(Plasma::Types::Location(location));
    copy->setFormFactor(location==Plasma::Types::LeftEdge || location==Plasma::Types::RightEdge ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
    frame->setError({});m_assignments.insert(copy->id(),description);reconcile();
}
bool PanelRuntime::addPanel(const QString &actionData,QScreen *target) {
    if(!m_corona)return false;
    const auto fail=[this](const QString &message){m_error=message;emit changed();return false;};
    if(!m_panelAddingAllowed)return fail(tr("Adding panels is not available in this host."));
    if(m_corona->immutability()!=Plasma::Types::Mutable)return fail(tr("Adding panels is locked by KDE policy."));
    if(!target || !QGuiApplication::screens().contains(target))return fail(tr("Adding a panel requires a live output."));
    const auto identity=BwmOutput::identity(target);
    const auto description=(identity.manufacturer+' '+identity.model+' '+identity.serial).simplified();
    if(description.isEmpty() || BwmOutput::resolveScreen(description)!=target)return fail(tr("The target output has no unique description."));
    QHash<Plasma::Containment*,QVariantMap> existing;
    for(auto it=m_views.cbegin();it!=m_views.cend();++it) {
        auto *frame=it.value().data();if(!frame || !frame->containment())continue;
        existing.insert(frame->containment(),{{"screen",QGuiApplication::screens().indexOf(frame->screen())},
            {"thickness",frame->property("thickness")},{"alignment",frame->property("alignment")},
            {"minLength",frame->property("minimumLength")},{"maxLength",frame->property("maximumLength")},
            {"offset",frame->property("offset")}});
    }
    LayoutTemplateRunner runner(m_corona,target,existing);
    const bool ok=runner.run(actionData);
    // Like ShellCorona, panels created before a script error are kept (the template is not transactional).
    QHash<uint,QVariantMap> pending;
    for(auto *panel:runner.createdPanels()) {
        auto *c=panel->containment();if(!c)continue;
        m_assignments.insert(c->id(),description);pending.insert(c->id(),panel->pendingViewSettings());
        m_initialPanelSettings.insert(c->id(),panel->pendingViewSettings());
    }
    reconcile();
    QStringList errors;if(!ok)errors.append(runner.error());
    for(auto it=pending.cbegin();it!=pending.cend();++it) {
        if(it.value().isEmpty())continue;
        auto *frame=view(it.key());
        if(!frame){errors.append(tr("The new panel %1 has no view on this output.").arg(it.key()));continue;}
        if(!frame->error().isEmpty())errors.append(frame->error());
    }
    m_corona->requestConfigSync();
    if(!errors.isEmpty())return fail(errors.join(u'\n'));
    m_error.clear();emit changed();return true;
}
void PanelRuntime::drop(uint id) {
    auto *frame=m_views.take(id).data();if(!frame)return;
    frame->hide();
    if(auto *session=frame->panelSession())session->packageWindows()->suspend();
    if(m_corona)m_corona->unbind(frame->containment());
    delete frame; // closes ConfigurationSession; its pending controls are not applied
}
void PanelRuntime::dropAll() {
    for(uint id:m_views.keys())drop(id);
    if(m_corona)for(auto *screen:QGuiApplication::screens())m_corona->setScreenAvailableRect(screen,{});
}
void PanelRuntime::updateReservations() {
    if(!m_nativePanelPolicy)return;
    // ShellCorona::shouldPanelReserveSpace (plasma-workspace 6.7.5): only the
    // thickest NormalPanel on the same screen AND edge reserves. BWM uses the
    // lowest containment ID for ties, so a reload cannot arbitrarily swap owner.
    QHash<QPair<QScreen*,int>,uint> owners;
    auto ids=m_views.keys();std::sort(ids.begin(),ids.end());
    for(uint id:ids) {
        auto *frame=view(id);
        if(!frame || !frame->isVisible() || !frame->containment() || frame->containment()->destroyed() ||
           frame->visibilityMode()!=PanelViewEnums::NormalPanel || m_skin!="plasma")continue;
        const auto key=qMakePair(frame->screen(),int(frame->containment()->location()));
        const auto previous=owners.value(key);auto *old=view(previous);
        if(!old || frame->thickness()>old->thickness())owners[key]=id;
    }
    const bool editing=m_corona && m_corona->isEditMode();
    auto selected=owners.values();
    if(editing)for(uint id:ids)if(auto *frame=view(id);frame && frame->isVisible() && frame->containment() &&
        !frame->containment()->destroyed() && m_skin=="plasma" && !selected.contains(id))selected.append(id);
    // Withdraw previous owners first. Wayland commits are independent; this is
    // not a compositor-wide atomic transaction, but never deliberately adds zones.
    for(uint id:ids)if(!selected.contains(id))BwmSurface::setPanelReservationPolicy(view(id),false,editing);
    for(uint id:selected)BwmSurface::setPanelReservationPolicy(view(id),true,editing);
    // Compute each reserving panel's usableArea bounds (in compositor surface order,
    // matching IHyprRenderer::arrangeLayerArray) and the screen's final available rect
    // (matching ShellCorona::_availableScreenRect) so adjacent-edge panels and corner
    // popups never collide or drift out of sync.
    for(auto *screen:QGuiApplication::screens()) {
        QList<QPair<uint,PanelViewHost*>> onScreen,reserving;
        for(uint id:ids) {
            auto *frame=view(id);
            if(!frame || frame->screen()!=screen)continue;
            onScreen.append({id,frame});
            if(frame->isVisible() && frame->property("bwmExclusiveZoneRequested").toInt()>0)reserving.append({id,frame});
        }
        std::sort(reserving.begin(),reserving.end(),[](const auto &a,const auto &b){
            if(a.second->surfaceOrder()!=b.second->surfaceOrder())return a.second->surfaceOrder()<b.second->surfaceOrder();
            return a.first<b.first;
        });
        const QRect full=screen->geometry();
        QRect usable=full;
        QHash<PanelViewHost*,QRect> boundsByView;
        for(const auto &[id,frame]:reserving) {
            Q_UNUSED(id);
            boundsByView.insert(frame,usable);
            const int zone=frame->property("bwmExclusiveZoneRequested").toInt();
            QRect next=usable;
            switch(Qt::Edge(frame->property("bwmPanelEdge").toInt())) {
            case Qt::TopEdge:next.setTop(next.top()+zone);break;
            case Qt::BottomEdge:next.setBottom(next.bottom()-zone);break;
            case Qt::LeftEdge:next.setLeft(next.left()+zone);break;
            case Qt::RightEdge:next.setRight(next.right()-zone);break;
            default:break;
            }
            if(next.isValid() && !next.isEmpty())usable=next;
        }
        const QRect publishedAvailable=reserving.isEmpty() ? QRect() : usable;
        if(m_corona)m_corona->setScreenAvailableRect(screen,publishedAvailable);
        for(const auto &[id,frame]:onScreen) {
            Q_UNUSED(id);
            BwmSurface::setPanelLayoutContext(frame,boundsByView.value(frame,full),publishedAvailable);
        }
    }
}
void PanelRuntime::reconcile() {
    if(m_reconciling)return;
    QScopedValueRollback<bool> guard(m_reconciling,true);
    if(!m_corona){dropAll();m_status.clear();emit changed();return;}
    QSet<uint> live;QVariantList status;
    for(auto *c:m_corona->containments()) {
        if(c->destroyed() || !m_assignments.contains(c->id()))continue;
        const uint id=c->id();live.insert(id);
        if(!m_observed.contains(id)) {
            m_observed.insert(id);
            connect(c,&Plasma::Containment::locationChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&Plasma::Containment::formFactorChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&Plasma::Applet::destroyedChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&QObject::destroyed,this,[this,id]{m_observed.remove(id);m_initialPanelSettings.remove(id);m_reconcile.start();});
        }
        QString state;auto *screen=BwmOutput::resolveScreen(m_assignments.value(id),&state);
        const auto side=edge(c->location());
        if(m_skin!="plasma")state="skin-inactive";
        else if(auto *control=NativeDesktopControl::requiredControl();control && !control->resumed())state="native-desktop-not-ready";
        else if(side==Qt::Edge(0))state="unsupported-panel-edge";
        else if((side==Qt::LeftEdge || side==Qt::RightEdge)!=(c->formFactor()==Plasma::Types::Vertical))state="inconsistent-panel-orientation";
        auto *frame=view(id);
        if(frame && (state!="matched" || frame->screen()!=screen || frame->property("bwmRuntimeScreen").value<QScreen*>()!=screen ||
            frame->property("bwmRuntimeEdge").toInt()!=int(side))) {drop(id);frame=nullptr;}
        QString error;
        if(frame) {
            const bool vertical=c->formFactor()==Plasma::Types::Vertical;
            const auto scope=(vertical ? QString("Vertical") : QString("Horizontal"))+QString::number(vertical ? screen->size().height() : screen->size().width());
            if(frame->capabilities().value("viewSettingsScope").toString()!=scope && !frame->reloadViewSettings()) {
                error=frame->error();drop(id);frame=nullptr;state="view-unavailable";
            }
        }
        if(state=="matched" && !frame) {
            frame=new PanelViewHost(m_corona,m_settingsFile);frame->setScreen(screen);
            frame->setProperty("bwmRuntimeScreen",QVariant::fromValue(screen));frame->setProperty("bwmRuntimeEdge",int(side));
            // Keep it non-reserving until every view is present and the owner of
            // each edge has been selected. Mode 0 in its native config is intact.
            if(m_nativePanelPolicy)frame->setProperty("bwmPanelReservationAllowed",false);
            if(m_layerSurfaces)BwmSurface::configurePanel(frame,side,m_nativePanelPolicy?0:64,m_nativePanelPolicy);
            m_corona->bind(c,frame);
            if(!frame->load(c)) {error=frame->error();m_corona->unbind(c);delete frame;frame=nullptr;state="view-unavailable";}
            else {
                // Finish the original template's view preferences before the first
                // edit-mode reservation is frozen. Otherwise the provisional 48 px
                // constructor size survives until leaving edit mode (template: 46/36).
                if(m_initialPanelSettings.contains(id)) {
                    const auto initial=m_initialPanelSettings.take(id);
                    if(initial.isEmpty() || frame->applyViewSettings(initial))
                        QMetaObject::invokeMethod(frame,"reflow",Qt::DirectConnection);
                }
                m_views.insert(id,frame);
                connect(frame,&PanelViewHost::policyChanged,&m_reconcile,qOverload<>(&QTimer::start));
                connect(frame,&PanelViewHost::geometryPolicyChanged,&m_reconcile,qOverload<>(&QTimer::start));
                connect(frame,&QWindow::visibleChanged,&m_reconcile,qOverload<>(&QTimer::start));
                connect(frame,&QWindow::screenChanged,this,[this,id,screen](QScreen *now){
                    if(now!=screen){if(auto *v=view(id))v->hide();m_reconcile.start();}
                });
                // Queued: the request comes from a handler of the settings that the move destroys.
                connect(frame,&PanelViewHost::screenToFollowRequested,this,[this,id](QScreen *target){moveToOutput(id,target);},Qt::QueuedConnection);
                connect(frame,&PanelViewHost::cloneRequested,this,[this,id](int location,QScreen *target){cloneToOutput(id,location,target);},Qt::QueuedConnection);
                frame->show();
                if(m_reopenSettings.remove(id))
                    QTimer::singleShot(0,this,[this,id]{
                        auto *v=view(id);if(!v || !v->containment())return;
                        if(auto *configure=v->containment()->internalAction(QStringLiteral("configure")))configure->trigger();
                    });
            }
        }
        if(frame){
            if(frame->property("bwmControlWithdrawn").toBool()){
                frame->setProperty("bwmControlWithdrawn",false);frame->show();
            }
            state="visible";
        }
        status.append(QVariantMap{{"containmentId",id},{"outputDescription",m_assignments.value(id)},
            {"edge",edgeName(side)},
            {"status",state},{"error",error},{"visible",frame && frame->isVisible()},
            {"waylandVerified",false},{"reservedArea",false}});
    }
    for(uint id:m_views.keys())if(!live.contains(id))drop(id);
    updateReservations();
    if(status!=m_status){m_status=status;emit changed();}
}

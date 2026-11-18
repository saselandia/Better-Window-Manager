// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelruntime.h"
#include "viewcorona.h"
#include "panelviewhost.h"
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
        if(c->containmentType()!=Plasma::Containment::Panel && c->containmentType()!=Plasma::Containment::CustomPanel) {
            m_error=tr("This runtime only hosts native panel containments.");emit changed();return false;
        }
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
void PanelRuntime::drop(uint id) {
    auto *frame=m_views.take(id).data();if(!frame)return;
    frame->hide();
    if(auto *session=frame->panelSession())session->packageWindows()->suspend();
    if(m_corona)m_corona->unbind(frame->containment());
    delete frame; // closes ConfigurationSession; its pending controls are not applied
}
void PanelRuntime::dropAll(){for(uint id:m_views.keys())drop(id);}
void PanelRuntime::reconcile() {
    if(m_reconciling)return;
    QScopedValueRollback<bool> guard(m_reconciling,true);
    if(!m_corona){dropAll();m_status.clear();emit changed();return;}
    QHash<QScreen*,int> nativeOutputs;
    if(m_nativePanelPolicy)for(auto *c:m_corona->containments())if(!c->destroyed() && m_assignments.contains(c->id()))
        if(auto *screen=BwmOutput::resolveScreen(m_assignments.value(c->id())))++nativeOutputs[screen];
    QSet<uint> live;QVariantList status;
    for(auto *c:m_corona->containments()) {
        if(c->destroyed() || !m_assignments.contains(c->id()))continue;
        const uint id=c->id();live.insert(id);
        if(!m_observed.contains(id)) {
            m_observed.insert(id);
            connect(c,&Plasma::Containment::locationChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&Plasma::Containment::formFactorChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&Plasma::Applet::destroyedChanged,&m_reconcile,qOverload<>(&QTimer::start));
            connect(c,&QObject::destroyed,this,[this,id]{m_observed.remove(id);m_reconcile.start();});
        }
        QString state;auto *screen=BwmOutput::resolveScreen(m_assignments.value(id),&state);
        const auto side=edge(c->location());
        if(m_skin!="plasma")state="skin-inactive";
        else if(auto *control=NativeDesktopControl::requiredControl();control && !control->resumed())state="native-desktop-not-ready";
        else if(m_nativePanelPolicy && nativeOutputs.value(screen)>1)state="native-policy-output-conflict";
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
            if(m_layerSurfaces)BwmSurface::configurePanel(frame,side,m_nativePanelPolicy?0:64,m_nativePanelPolicy);
            m_corona->bind(c,frame);
            if(!frame->load(c)) {error=frame->error();m_corona->unbind(c);delete frame;frame=nullptr;state="view-unavailable";}
            else {
                m_views.insert(id,frame);
                connect(frame,&QWindow::screenChanged,this,[this,id,screen](QScreen *now){
                    if(now!=screen){if(auto *v=view(id))v->hide();m_reconcile.start();}
                });
                frame->show();
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
    if(status!=m_status){m_status=status;emit changed();}
}

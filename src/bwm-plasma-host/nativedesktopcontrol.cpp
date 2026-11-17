// SPDX-License-Identifier: GPL-2.0-or-later
#include "nativedesktopcontrol.h"
#include "desktopregistry.h"
#include "qwayland-bwm-plasma-desktop-control-v1.h"
#include <QCoreApplication>
#include <QGuiApplication>
#include <QPointer>
namespace {QPointer<NativeDesktopControl> shared;}
struct NativeDesktopControl::Wire:QtWayland::bwm_plasma_desktop_control_v1 {
    NativeDesktopControl *owner;
    quint32 globalName;
    Wire(NativeDesktopControl *o,wl_registry *registry,quint32 name):owner(o),globalName(name){init(registry,name,2);}
    ~Wire()override{if(isInitialized())destroy();}
    void bwm_plasma_desktop_control_v1_availability(uint32_t value)override{owner->availability(value==1);}
    void bwm_plasma_desktop_control_v1_acknowledged(uint32_t serial,uint32_t value)override{if(value<=1)owner->acknowledged(serial,value);}
    void bwm_plasma_desktop_control_v1_desktop_global(uint32_t name)override{owner->binding(name);}
};
NativeDesktopControl::NativeDesktopControl(QObject *parent):QObject(parent){
    m_timeout.setSingleShot(true);m_timeout.setInterval(1000);
    connect(&m_timeout,&QTimer::timeout,this,[this]{
        m_registryTimedOut=m_registryWaiting;m_registryWaiting=false;m_pending=false;m_confirmed=false;m_failed=true;
        m_error=m_registryTimedOut?"Native desktop registry verification timed out":"Native desktop barrier timed out";emit changed();
    });
    if(QGuiApplication::platformName().startsWith("wayland")){
        m_registry=std::make_unique<NativeDesktopRegistry>(this);
        connect(m_registry.get(),&NativeDesktopRegistry::changed,this,&NativeDesktopControl::registryChanged);
    }
}
NativeDesktopControl::~NativeDesktopControl(){
    m_timeout.stop();
    m_wire.reset();
    m_registry.reset();
}
void NativeDesktopControl::beginRevision(qint64 revision){
    if(revision==m_revision)return;m_revision=revision;
    if(m_failed || m_registryTimedOut){m_failed=false;m_registryTimedOut=false;m_error.clear();}
}
void NativeDesktopControl::send(){
    if(!m_wire || (!m_desired && (!bindingVerified() || m_registryTimedOut)))return;
    m_pending=true;m_confirmed=false;m_timeout.start();
    if(!m_desired && !m_known)return; // First availability precedes the first request.
    if(++m_serial==0)++m_serial;
    m_wire->set_paused(m_serial,m_desired);
}
NativeDesktopControl::Status NativeDesktopControl::ensurePaused(bool paused){
    if(!m_hasDesired || paused!=m_desired){
        m_hasDesired=true;m_desired=paused;m_pending=false;m_confirmed=false;m_failed=false;m_registryTimedOut=false;m_registryWaiting=false;m_error.clear();m_timeout.stop();
    }
    if(!paused && m_registry){
        if(m_registry->state().value("restartRequired").toBool()){m_error=registryError();return Status::Unavailable;}
        if(m_registryTimedOut)return Status::Unavailable;
        if(registryPending()){
            if(m_failed)return Status::Unavailable;
            if(!m_registryWaiting){m_registryWaiting=true;m_timeout.start();}
            return Status::Pending;
        }
        if(!bindingVerified()){m_error=registryError();return Status::Unavailable;}
    }
    if(!m_wire){
        // No own server/connection can execute a queued native activation.
        // Entering Breeze still requires an explicit positive round-trip.
        if(paused){m_confirmed=true;m_confirmedPaused=true;return Status::Ready;}
        m_error="Native desktop control protocol unavailable";return Status::Unavailable;
    }
    if(!paused && m_known && !m_available){m_error="Native desktop provider disabled or unavailable";return Status::Unavailable;}
    if(m_confirmed && m_confirmedPaused==paused)return Status::Ready;
    if(m_failed)return Status::Unavailable;
    if(!m_pending)send();
    return Status::Pending;
}
void NativeDesktopControl::availability(bool value){
    m_known=true;m_available=value;
    if(!value && m_hasDesired && !m_desired){
        m_timeout.stop();m_pending=false;m_confirmed=false;m_failed=true;m_error="Native desktop provider disabled or unavailable";
    }else if((value || m_desired) && m_hasDesired && !m_confirmed && !m_registryTimedOut){m_failed=false;m_error.clear();send();}
    emit changed();
}
void NativeDesktopControl::acknowledged(quint32 serial,bool paused){
    if(!m_hasDesired || m_failed || !m_pending || !serial || serial!=m_serial || paused!=m_desired || (!paused && (!m_available || !bindingVerified() || m_registryTimedOut)))return;
    m_timeout.stop();m_pending=false;m_confirmed=true;m_confirmedPaused=paused;m_error.clear();emit changed();
}
void NativeDesktopControl::disconnected(){
    m_timeout.stop();m_known=false;m_available=false;m_pending=false;m_confirmed=false;m_failed=false;m_registryWaiting=false;m_bindingKnown=false;m_managementName=0;
    m_error="Native desktop control connection lost";emit changed();
}
void NativeDesktopControl::connected(){
    m_timeout.stop();m_known=false;m_available=false;m_pending=false;m_confirmed=false;m_failed=m_registryTimedOut;m_registryWaiting=false;m_bindingKnown=false;m_managementName=0;
    m_error=m_registryTimedOut?"Native desktop registry verification timed out":QString();
    emit changed(); // A new server generation must never inherit a previous confirmation.
}
bool NativeDesktopControl::registryPending()const{
    return m_registry && (!m_registry->complete() || (m_registry->topologyCompatible() && (!m_wire || !m_bindingKnown)));
}
bool NativeDesktopControl::bindingVerified()const{
    return m_registry && m_wire && m_bindingKnown && m_registry->bindingMatches(m_wire->globalName,m_managementName);
}
QString NativeDesktopControl::registryError()const{
    return m_registry && m_registry->state().value("restartRequired").toBool()
        ?"Native desktop provider unavailable: desktop registry was ambiguous; restart this auxiliary"
        :"Native desktop provider unavailable: registry missing, incompatible, ambiguous or unpaired";
}
void NativeDesktopControl::binding(quint32 name){m_bindingKnown=true;m_managementName=name;registryChanged();}
void NativeDesktopControl::registryChanged(){
    if(m_wire && !m_registry->controlPresent(m_wire->globalName)){m_wire.reset();disconnected();}
    if(!m_wire && m_registry->topologyCompatible()){
        m_wire=std::make_unique<Wire>(this,m_registry->handle(),m_registry->controlName());connected();
    }
    if(registryPending()){emit changed();return;}
    if(m_registryWaiting){m_registryWaiting=false;m_timeout.stop();}
    if(!bindingVerified()){
        const bool wasActive=m_confirmed || m_pending;
        m_registryBlocked=true;m_confirmed=false;m_pending=false;
        if(!m_desired){
            m_failed=true;m_error=registryError();m_timeout.stop();
            // Revoke our existing control immediately; this is not a barrier
            // for any other provider. Its ack cannot confirm the desired resume.
            const auto registry=m_registry->state();
            const bool ambiguous=registry.value("managementGlobals").toInt()>1 || registry.value("controlGlobals").toInt()>1;
            if(wasActive && ambiguous && m_wire && m_registry->associationPresent(m_wire->globalName,m_managementName)){
                if(++m_serial==0)++m_serial;m_wire->set_paused(m_serial,true);
            }
        }
    }else if(!m_registryTimedOut){
        if(m_registryBlocked){m_registryBlocked=false;m_failed=false;m_error.clear();}
        if(m_hasDesired && !m_desired && !m_failed && !m_confirmed && !m_pending)send();
    }
    emit changed();
}
bool NativeDesktopControl::resumed()const{return bindingVerified() && !m_registryTimedOut && m_wire && m_known && m_available && m_confirmed && !m_confirmedPaused;}
QVariantMap NativeDesktopControl::state()const{
    return {{"required",true},{"connected",bool(m_wire)},{"providerAvailable",m_known && m_available},
        {"desiredPaused",m_desired},{"pending",m_pending},{"confirmed",m_confirmed},{"confirmedPaused",m_confirmedPaused},
        {"resumed",resumed()},{"serial",m_serial},{"lastError",m_error},{"scope","same-wayland-connection"},{"operationalVerified",false},
        {"registry",m_registry?m_registry->state():QVariantMap{}},{"bindingVerified",bindingVerified()},{"managementGlobal",m_managementName},
        {"registryWaiting",m_registryWaiting},{"registryTimedOut",m_registryTimedOut},{"bindingKnown",m_bindingKnown}};
}
NativeDesktopControl *NativeDesktopControl::requiredControl(QObject *owner){
    if(qEnvironmentVariable("BWM_R4_NATIVE_DESKTOPS")!="1")return nullptr;
    if(!shared)shared=new NativeDesktopControl(owner?owner:qApp);
    return shared;
}
QVariantMap NativeDesktopControl::diagnostics(){return shared?shared->state():QVariantMap{{"required",false},{"operationalVerified",false}};}

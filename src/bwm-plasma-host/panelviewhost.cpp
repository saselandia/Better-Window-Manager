// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelviewhost.h"
#include "panelsession.h"
#include "packagewindows.h"
#include "surfaces.h"
#include "panelviewsettings.h"
#include "panelconfigview.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <KSvg/FrameSvg>
#include <QQmlContext>
#include <QQmlEngine>
#include <QScreen>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QPlatformSurfaceEvent>
#include <algorithm>
#include <cmath>

void PanelViewHost::registerTypes() {
    static const int registered=qmlRegisterUncreatableMetaObject(PanelViewEnums::staticMetaObject,
        "org.kde.plasma.shell.panel",0,1,"Global",QStringLiteral("Enum metadata only"));
    Q_UNUSED(registered);
}
PanelViewHost::PanelViewHost(Plasma::Corona *corona,QString viewSettingsFile):ContainmentView(corona),m_viewSettingsFile(std::move(viewSettingsFile)) {
    m_reflow.setSingleShot(true);m_reflow.setInterval(0);
    connect(&m_reflow,&QTimer::timeout,this,&PanelViewHost::reflow);
    connect(this,&PlasmaQuick::ContainmentView::locationChanged,this,[this]{emit policyChanged();m_reflow.start();});
    connect(this,&PlasmaQuick::ContainmentView::formFactorChanged,&m_reflow,qOverload<>(&QTimer::start));
    connect(&m_floatingAnimation,&QPropertyAnimation::valueChanged,this,[this]{updateMask();});
    setTranslationDomain("plasma_shell_org.kde.plasma.desktop");
    rootContext()->setContextProperty("panel",this);
    connect(this,&QWindow::screenChanged,this,&PanelViewHost::screenToFollowChanged);
    connect(&m_theme,&Plasma::Theme::themeChanged,this,&PanelViewHost::adaptiveOpacityEnabledChanged);
    connect(this,&QWindow::visibleChanged,this,[this]{invalidateFrame();});
    connect(this,&QWindow::screenChanged,this,[this]{invalidateFrame();});
    connect(this,&QWindow::widthChanged,this,[this]{invalidateFrame();});
    connect(this,&QWindow::heightChanged,this,[this]{invalidateFrame();});
    // Render-thread callbacks only retain atomic counters, never GUI/derived
    // members. A late swap from a frame begun before hide/resize cannot certify
    // the new surface, even when its notification arrives after show().
    connect(this,&QQuickWindow::beforeRendering,this,[frames=m_frames]{
        frames->rendering.store(frames->surface.load());
    },Qt::DirectConnection);
    connect(this,&QQuickWindow::frameSwapped,this,[frames=m_frames]{
        frames->submitted.store(frames->rendering.load());
    },Qt::DirectConnection);
    connect(this,&QQuickWindow::sceneGraphInvalidated,this,[frames=m_frames]{
        ++frames->surface;
    },Qt::DirectConnection);
    connect(this,&QQuickWindow::sceneGraphError,this,[this](QQuickWindow::SceneGraphError,const QString &message){
        invalidateFrame();m_renderError=message.isEmpty()?tr("Scene graph initialization failed."):message;
    });
}
void PanelViewHost::invalidateFrame(){++m_frames->surface;}
bool PanelViewHost::event(QEvent *event) {
    const bool result=ContainmentView::event(event);
    if((event->type()==QEvent::Expose && !isExposed()) ||
       (event->type()==QEvent::PlatformSurface && static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed))invalidateFrame();
    return result;
}
QVariantMap PanelViewHost::presentationState()const {
    const bool loaded=capabilities().value("nativeViewLoaded").toBool();
    const bool submitted=m_frames->submitted.load()==m_frames->surface.load();
    return {{"nativeViewLoaded",loaded},{"visible",isVisible()},{"exposed",isExposed()},
        {"frameSubmitted",submitted},{"renderError",m_renderError},{"surfaceError",property("bwmSurfaceError").toString()},
        {"renderReady",loaded && isVisible() && isExposed() && submitted && m_renderError.isEmpty() && property("bwmSurfaceError").toString().isEmpty()},
        {"compositorPresentationVerified",false}};
}
PanelViewHost::~PanelViewHost() {
    // The settings' QML holds "panel": destroy it now, not after a deferred delete.
    delete m_configView.data();
    disconnect(this,nullptr,this,nullptr);
    m_reflow.stop();m_floatingAnimation.stop();
    if(containment())disconnect(containment(),nullptr,this,nullptr);
    delete m_session.data();
    if(m_item){m_item->setVisible(false);m_item->setParentItem(nullptr);}
    if(rootObject())rootObject()->setProperty("containment",QVariant::fromValue<QQuickItem*>(nullptr));
    // SharedQmlEngine 6.7.5 guards its root with QPointer. Destroy QML while the
    // adapter properties exist, without trying to load an empty source URL.
    delete rootObject();
}
PanelSession *PanelViewHost::panelSession()const{return m_session.data();}
void PanelViewHost::setError(const QString &message){if(m_error!=message){m_error=message;emit errorChanged();}}
bool PanelViewHost::vertical()const{return containment() && containment()->formFactor()==Plasma::Types::Vertical;}
QVariantMap PanelViewHost::capabilities()const {
    QStringList keys={"floating","floatingApplets","panelOpacity","thickness","minLength","maxLength"};
    const bool native=property("bwmNativePanelPolicy").toBool();if(native)keys.append("panelVisibility");
    return {{"nativePanelSource",m_nativeSource},{"nativeViewLoaded",bool(m_item) && rootObject() && status()==QQmlComponent::Ready},
        {"fixedOpacityModes",true},{"floatingSvg",true},
        {"nativeInputMask",true},{"adaptiveWindowBackend",false},{"autohide",false},
        {"minimumLength",m_minimumLength},{"maximumLength",m_maximumLength},
        {"viewSettingsReady",m_settings && m_settings->ready()},{"viewSettingsScope",m_settings ? m_settings->scope() : QString()},
        {"persistentViewKeys",keys},{"nativeVisibilityPolicy",native},
        {"reservationRequested",property("bwmReservationRequested").toBool()},
        {"exclusiveZoneRequested",property("bwmExclusiveZoneRequested").isValid()?property("bwmExclusiveZoneRequested").toInt():-1},
        {"reservedArea",false},{"compositorBlur",false},{"externalPanelShadows",false},{"waylandVerified",false}};
}
bool PanelViewHost::load(Plasma::Containment *c) {
    if(!c || c->destroyed() || c->corona()!=corona() || containment() ||
        (c->containmentType()!=Plasma::Containment::Panel && c->containmentType()!=Plasma::Containment::CustomPanel)) {
        setError(tr("A new panel view requires a live containment owned by its Corona."));return false;
    }
    registerTypes();
    m_settingsDefaults={{"floating",int(m_floating)},{"floatingApplets",int(m_floatingApplets)},
        {"panelOpacity",m_opacity},{"thickness",m_requestedThickness},{"minLength",m_minimumLength},{"maxLength",m_maximumLength},
        {"alignment",m_alignment},{"panelLengthMode",m_lengthMode},{"offset",m_offset}};
    const bool native=property("bwmNativePanelPolicy").toBool();
    if(native)m_settingsDefaults.insert("panelVisibility",PanelViewEnums::NormalPanel);
    if(!screen()){setError(tr("A screen is required to resolve native panel preferences."));return false;}
    const bool vertical=c->formFactor()==Plasma::Types::Vertical;
    m_settings=std::make_unique<PanelViewSettings>(m_viewSettingsFile,c->id(),vertical,vertical ? screen()->size().height() : screen()->size().width(),m_settingsDefaults,native);
    if(!m_settings->reload()){setError(m_settings->error());return false;}
    useViewSettings(m_settings->values());
    const auto original=KPackage::PackageLoader::self()->loadPackage("Plasma/Shell","org.kde.plasma.desktop");
    m_nativeSource=original.fileUrl("views",QStringLiteral("Panel.qml"));
    if(!original.isValid() || m_nativeSource.isEmpty()) {
        setError(tr("The installed KDE Plasma shell Panel.qml is missing."));return false;
    }
    m_lastVertical=c->formFactor()==Plasma::Types::Vertical;
    const int extent=std::clamp(m_length,m_minimumLength,m_maximumLength);
    const QSize initial=m_lastVertical ? QSize(m_thickness,extent) : QSize(extent,m_thickness);
    setMinimumSize(initial);setMaximumSize(initial);resize(initial);
    setSource(m_nativeSource);
    QElapsedTimer timer;timer.start();
    while(status()==QQmlComponent::Loading && timer.elapsed()<3000)QCoreApplication::processEvents();
    if(status()!=QQmlComponent::Ready || !rootObject()) {
        QStringList messages;for(const auto &e:errors())messages.append(e.toString());
        setError(messages.isEmpty() ? tr("The native panel view did not load.") : messages.join('\n'));return false;
    }
    auto *root=rootObject();
    for(const char *property:{"containment","panelMask","floatingness","floatingnessTarget","floatingnessAnimationDuration",
        "fixedLeftFloatingPadding","fixedRightFloatingPadding","fixedTopFloatingPadding","fixedBottomFloatingPadding","minPanelWidth","minPanelHeight"})
        if(root->metaObject()->indexOfProperty(property)<0){setError(tr("The installed Panel.qml lacks its required host property: %1").arg(QString::fromLatin1(property)));return false;}
    for(const char *signal:{SIGNAL(fixedLeftFloatingPaddingChanged()),SIGNAL(fixedRightFloatingPaddingChanged()),
        SIGNAL(fixedTopFloatingPaddingChanged()),SIGNAL(fixedBottomFloatingPaddingChanged()),
        SIGNAL(minPanelHeightChanged()),SIGNAL(minPanelWidthChanged())})
        connect(root,signal,&m_reflow,SLOT(start()));
    connect(root,SIGNAL(floatingnessTargetChanged()),this,SLOT(animateFloating()));
    connect(root,SIGNAL(panelMaskChanged()),this,SLOT(updateMask()));
    m_floatingAnimation.setTargetObject(root);m_floatingAnimation.setPropertyName("floatingness");
    // The base view supplies native containment parenting and configureRequested. Route
    // configuration through one PanelSession, rather than opening a second ConfigView.
    m_session=new PanelSession(c,false);m_session->setParent(this);
    setProperty("bwmPanelSession",QVariant::fromValue(m_session.data()));
    setContainment(c);
    m_item=PlasmaQuick::AppletQuickItem::itemForApplet(c);
    if(!m_item || c->failedToLaunch()) {
        setError(c->launchErrorMessage().isEmpty() ? tr("The native panel containment did not load.") : c->launchErrorMessage());return false;
    }
    m_session->bindPanelItem(m_item);m_session->packageWindows()->refresh();
    connect(c,&Plasma::Containment::statusChanged,this,[this](Plasma::Types::ItemStatus state){
        if(property("bwmLayerPanel").toBool())BwmSurface::setPanelAcceptsInput(this,state==Plasma::Types::AcceptingInputStatus);
    });
    reflow();animateFloating();updateMask();setError({});return true;
}
void PanelViewHost::setThickness(int value) {
    if(value<16 || value>256){setError(tr("Preview panel thickness must be between 16 and 256 logical pixels."));return;}
    if(m_userConfiguring && m_settings){applyViewSettings({{"thickness",value}});emit geometryPolicyChanged();return;}
    m_requestedThickness=value;setError({});m_reflow.start();
}
QVariantMap PanelViewHost::viewSettings()const{return m_settings ? m_settings->values() : QVariantMap();}
QString PanelViewHost::settingsScope()const {
    if(!screen())return {};
    return (vertical()?QString("Vertical"):QString("Horizontal"))+QString::number(vertical()?screen()->size().height():screen()->size().width());
}
void PanelViewHost::useViewSettings(const QVariantMap &values) {
    m_requestedThickness=values.value("thickness").toInt();m_thickness=m_requestedThickness;
    m_minimumLength=values.value("minLength").toInt();m_maximumLength=values.value("maxLength").toInt();
    m_floating=values.value("floating").toInt()!=0;m_floatingApplets=values.value("floatingApplets").toInt()!=0;
    m_opacity=values.value("panelOpacity").toInt();
    m_visibility=values.value("panelVisibility",PanelViewEnums::WindowsGoBelow).toInt();
    m_alignment=values.value("alignment",m_alignment).toInt();m_lengthMode=values.value("panelLengthMode",m_lengthMode).toInt();
    // PanelView::restore: a centered panel has no offset, others never a negative one.
    m_offset=m_alignment==Qt::AlignCenter ? 0 : std::max(0,values.value("offset",m_offset).toInt());
    emit geometryPolicyChanged();emit policyChanged();emit placementChanged();emit viewSettingsChanged();m_reflow.start();
}
bool PanelViewHost::reloadViewSettings() {
    if(!containment() || !screen() || !m_settings){setError(tr("Load the native panel before its preferences."));return false;}
    auto replacement=std::make_unique<PanelViewSettings>(m_viewSettingsFile,containment()->id(),vertical(),vertical()?screen()->size().height():screen()->size().width(),m_settingsDefaults,property("bwmNativePanelPolicy").toBool());
    if(!replacement->reload()){setError(replacement->error());return false;}
    m_settings=std::move(replacement);useViewSettings(m_settings->values());setError({});return true;
}
bool PanelViewHost::applyViewSettings(const QVariantMap &changes) {
    if(!m_settings || !containment() || !screen()){setError(tr("Load the native panel before applying preferences."));return false;}
    if(settingsScope()!=m_settings->scope()){setError(tr("Panel output or orientation changed; reload preferences before applying."));return false;}
    if(containment()->immutable()){setError(tr("The native panel is locked."));return false;}
    auto supported=changes;
    if(supported.contains("thickness") && rootObject()) {
        auto value=supported.value("thickness");bool ok=false;const double number=value.toDouble(&ok);
        if(ok && value.metaType().id()!=QMetaType::QString && value.metaType().id()!=QMetaType::Bool && std::isfinite(number) && std::floor(number)==number && number>=16 && number<=256) {
            const int minimum=rootObject()->property(vertical()?"minPanelWidth":"minPanelHeight").toInt();
            supported["thickness"]=std::max(int(number),minimum);
        }
    }
    if(!m_settings->apply(supported)){setError(m_settings->error());return false;}
    useViewSettings(m_settings->values());setError({});return true;
}
void PanelViewHost::setLength(int value) {
    // A negative preferred length is the native Layout's unspecified value.
    if(value<0)return;
    // On orientation changes the original Binding can see the previous axis's
    // maximum size until reflow publishes the new constraints. Keep the length.
    if(containment() && vertical()!=m_lastVertical)return;
    value=std::clamp(value,0,8192);
    if(value==m_length)return;m_length=value;emit geometryPolicyChanged();m_reflow.start();
}
bool PanelViewHost::setLengthRange(int minimum,int maximum) {
    if(minimum<64 || maximum>8192 || minimum>maximum){setError(tr("Invalid preview panel length range."));return false;}
    m_minimumLength=minimum;m_maximumLength=maximum;setError({});m_reflow.start();return true;
}
void PanelViewHost::setOpacityMode(int value) {
    if(value!=PanelViewEnums::Opaque && value!=PanelViewEnums::Translucent) {
        setError(tr("Adaptive panel opacity needs the common window backend, which is not connected."));return;
    }
    setError({});if(m_opacity==value)return;
    if(m_userConfiguring && m_settings){applyViewSettings({{"panelOpacity",value}});emit policyChanged();return;}
    m_opacity=value;emit policyChanged();
}
void PanelViewHost::setFloating(bool value) {
    if(m_floating==value)return;
    if(m_userConfiguring && m_settings){applyViewSettings({{"floating",int(value)}});emit policyChanged();return;}
    m_floating=value;emit policyChanged();m_reflow.start();
}
void PanelViewHost::setFloatingApplets(bool value) {
    if(m_floatingApplets==value)return;
    if(m_userConfiguring && m_settings){applyViewSettings({{"floatingApplets",int(value)}});emit policyChanged();return;}
    m_floatingApplets=value;emit policyChanged();
}
void PanelViewHost::setBackgroundHints(int value) {
    if(m_backgroundHints==value)return;m_backgroundHints=value;emit backgroundHintsChanged();updateMask();
}
int PanelViewHost::enabledBorders()const {
    int mask=KSvg::FrameSvg::AllBorders;
    if(m_floating || !containment())return mask;
    switch(location()) {
    case Plasma::Types::TopEdge:return mask & ~KSvg::FrameSvg::TopBorder;
    case Plasma::Types::BottomEdge:return mask & ~KSvg::FrameSvg::BottomBorder;
    case Plasma::Types::LeftEdge:return mask & ~KSvg::FrameSvg::LeftBorder;
    case Plasma::Types::RightEdge:return mask & ~KSvg::FrameSvg::RightBorder;
    default:return mask;
    }
}
QRect PanelViewHost::dogdeGeometryByDistance(int distance)const {
    if(!screen())return {};
    const auto rect=property("bwmPanelRect").isValid() ? property("bwmPanelRect").toRect() : geometry();
    const int bounded=std::clamp(distance,-256,256);
    return rect.adjusted(-bounded,-bounded,bounded,bounded).intersected(screen()->geometry());
}
void PanelViewHost::reflow() {
    auto *root=rootObject();
    if(!root || !containment())return;
    const int minimum=root->property(vertical() ? "minPanelWidth" : "minPanelHeight").toInt();
    const int actual=std::clamp(std::max(m_requestedThickness,minimum),16,1024);
    if(m_thickness!=actual){m_thickness=actual;emit geometryPolicyChanged();}
    const auto padding=[root](const char *name){return std::clamp(root->property(name).toInt(),0,256);};
    const int pads=vertical() ? padding("fixedTopFloatingPadding")+padding("fixedBottomFloatingPadding")
        : padding("fixedLeftFloatingPadding")+padding("fixedRightFloatingPadding");
    const int total=m_thickness+(vertical() ? padding("fixedLeftFloatingPadding")+padding("fixedRightFloatingPadding")
        : padding("fixedTopFloatingPadding")+padding("fixedBottomFloatingPadding"));
    const int side=screen() ? (vertical() ? screen()->size().height() : screen()->size().width()) : 0;
    // PanelView::preferredSize 6.7.5. Panel.length is the content hint (m_contentLength).
    int extent=0;
    if(m_lengthMode==PanelViewEnums::FillAvailable && side>0)extent=side;
    else if(m_lengthMode==PanelViewEnums::FitContent && side>0)extent=std::max(total,std::min(side,m_length+pads));
    else {
        const int minimum=std::max(10,m_minimumLength);
        const int maximum=std::max(minimum,side>0 ? std::min(m_maximumLength,side-m_offset) : m_maximumLength);
        extent=std::clamp(m_length+pads,minimum,maximum);
    }
    const QSize wanted=vertical() ? QSize(total,extent) : QSize(extent,total);
    setMinimumSize(wanted);setMaximumSize(wanted);
    if(size()!=wanted)resize(wanted);
    root->setSize(wanted);m_lastVertical=vertical();updateMask();
    BwmSurface::setPanelPlacement(this,{m_alignment,m_offset,m_lengthMode});
    if(property("bwmLayerPanel").toBool())BwmSurface::setPanelVisibility(this,m_visibility,m_thickness);
}
void PanelViewHost::animateFloating() {
    auto *root=rootObject();if(!root)return;
    m_floatingAnimation.stop();
    const double from=root->property("floatingness").toDouble(),to=root->property("floatingnessTarget").toDouble();
    m_floatingAnimation.setStartValue(from);m_floatingAnimation.setEndValue(to);
    m_floatingAnimation.setDuration(std::max(0,root->property("floatingnessAnimationDuration").toInt()));
    m_floatingAnimation.setEasingCurve(from>to ? QEasingCurve::InCubic : QEasingCurve::OutCubic);
    if(from!=to)m_floatingAnimation.start();
    m_reflow.start();
}
void PanelViewHost::updateMask() {
    auto *root=rootObject();if(!root)return;
    const auto value=root->property("panelMask");
    if(value.metaType().id()!=QMetaType::QRegion)return;
    auto region=value.value<QRegion>();
    if(root->property("floatingness").toDouble()!=0)region.translate(root->property("floatingTranslucentItemOffset").toPoint());
    setMask(region);
}
void PanelViewHost::showConfigurationInterface(Plasma::Applet *applet) {
    if(!applet)return;
    // PanelView::showConfigurationInterface 6.7.5: the panel's own "configure"
    // (Enter Edit Mode) toggles its original Panel Settings and the edit mode.
    if(applet==containment()) {
        if(m_configView && m_configView->isVisible()){m_configView->hide();return;}
        if(m_configView){m_configView->show();m_configView->requestActivate();return;}
        auto *view=new PanelConfigView(containment(),this);
        if(!view->init()){setError(view->error());delete view;return;}
        m_configView=view;
        if(corona())corona()->setEditMode(true);
        view->show();view->requestActivate();
        return;
    }
    if(corona() && corona()->isEditMode())corona()->setEditMode(false);
    if(m_session)m_session->configure(applet->id());
}

int PanelViewHost::minThickness()const {
    auto *root=rootObject();return root ? root->property(vertical() ? "minPanelWidth" : "minPanelHeight").toInt() : 0;
}
bool PanelViewHost::persist(const QVariantMap &changes) {
    // Only the original Panel Settings write through, as PanelView does on every set.
    if(!m_userConfiguring || !m_settings)return false;
    return applyViewSettings(changes);
}
void PanelViewHost::setUserConfiguring(bool value) {
    if(m_userConfiguring==value)return;m_userConfiguring=value;
    if(containment())containment()->setUserConfiguring(value);
    emit userConfiguringChanged();
}
void PanelViewHost::setLengthMode(int value) {
    if(value<PanelViewEnums::FillAvailable || value>PanelViewEnums::Custom || value==m_lengthMode)return;
    if(persist({{"panelLengthMode",value}}))return;
    if(m_userConfiguring && m_settings)return; // A refused write keeps the stored value.
    m_lengthMode=value;emit placementChanged();m_reflow.start();
}
void PanelViewHost::setAlignment(int value) {
    if((value!=Qt::AlignLeft && value!=Qt::AlignRight && value!=Qt::AlignCenter) || value==m_alignment)return;
    // Like PanelView::restore, a centered panel keeps no offset.
    QVariantMap changes{{"alignment",value}};if(value==Qt::AlignCenter && m_offset)changes.insert("offset",0);
    if(persist(changes))return;
    if(m_userConfiguring && m_settings)return;
    m_alignment=value;if(value==Qt::AlignCenter)m_offset=0;emit placementChanged();m_reflow.start();
}
void PanelViewHost::setOffset(int value) {
    if(value==m_offset || value<-8192 || value>8192)return;
    // PanelView::setOffset: shrink the maximum so offset + length stay on the output.
    QVariantMap changes{{"offset",value}};
    const int side=screen() ? (vertical() ? screen()->size().height() : screen()->size().width()) : 0;
    if(side>0 && value+m_maximumLength>side)changes.insert("maxLength",std::max(64,side-value));
    if(changes.contains("maxLength") && m_minimumLength>changes.value("maxLength").toInt())changes.insert("minLength",changes.value("maxLength"));
    if(persist(changes))return;
    if(m_userConfiguring && m_settings)return;
    m_offset=value;if(changes.contains("maxLength"))m_maximumLength=changes.value("maxLength").toInt();
    emit placementChanged();emit geometryPolicyChanged();m_reflow.start();
}
void PanelViewHost::setMinimumLength(int value) {
    if(value==m_minimumLength || value<64 || value>8192)return;
    QVariantMap changes{{"minLength",value}};if(value>m_maximumLength)changes.insert("maxLength",value);
    if(persist(changes))return;
    if(m_userConfiguring && m_settings)return;
    m_minimumLength=value;m_maximumLength=std::max(m_maximumLength,value);emit geometryPolicyChanged();m_reflow.start();
}
void PanelViewHost::setMaximumLength(int value) {
    if(value==m_maximumLength || value<64 || value>8192)return;
    QVariantMap changes{{"maxLength",value}};if(value<m_minimumLength)changes.insert("minLength",value);
    if(persist(changes))return;
    if(m_userConfiguring && m_settings)return;
    m_maximumLength=value;m_minimumLength=std::min(m_minimumLength,value);emit geometryPolicyChanged();m_reflow.start();
}
void PanelViewHost::setVisibilityMode(int value) {
    if(value==m_visibility)return;
    // AutoHide/DodgeWindows need a window backend that the host does not have.
    const bool native=property("bwmNativePanelPolicy").toBool();
    if(value!=PanelViewEnums::WindowsGoBelow && !(native && value==PanelViewEnums::NormalPanel)) {
        setError(tr("This panel visibility mode has no controller in the BWM host."));emit policyChanged();return;
    }
    if(persist({{"panelVisibility",value}}))return;
    if(m_userConfiguring && m_settings){emit policyChanged();return;}
    m_visibility=value;emit policyChanged();m_reflow.start();
}
void PanelViewHost::setScreenToFollow(QScreen *target) {
    // Moving a panel to another output belongs to the runtime, which binds by description.
    if(!target || target==screen())return;
    setError(tr("Moving the panel to another output is not available in this host."));emit screenToFollowChanged();
}
void PanelViewHost::clonePanelTo(int location,QScreen *target) {
    if(receivers(SIGNAL(cloneRequested(int,QScreen*)))>0){emit cloneRequested(location,target);return;}
    setError(tr("Cloning panels is not available in this host."));
}

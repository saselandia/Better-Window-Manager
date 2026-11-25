// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelviewhost.h"
#include "panelshadows_p.h"
#include <KWindowEffects>
#include "alternativeshelper.h"
#include "panelsession.h"
#include "packagewindows.h"
#include "surfaces.h"
#include "panelviewsettings.h"
#include "panelconfigview.h"
#include "widgetexplorerview.h"
#include "viewcorona.h"
#include "taskbridge.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/Dialog>
#include <PlasmaQuick/PopupPlasmaWindow>
#include <PlasmaQuick/SharedQmlEngine>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <KSvg/FrameSvg>
#include <QQmlContext>
#include <QQmlEngine>
#include <QScreen>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QGuiApplication>
#include <QPlatformSurfaceEvent>
#include <QKeyEvent>
#include <algorithm>
#include <cmath>

void PanelViewHost::registerTypes() {
    static const int registered=qmlRegisterUncreatableMetaObject(PanelViewEnums::staticMetaObject,
        "org.kde.plasma.shell.panel",0,1,"Global",QStringLiteral("Enum metadata only"));
    Q_UNUSED(registered);
    AlternativesHelper::registerTypes();
}
PanelViewHost::PanelViewHost(Plasma::Corona *corona,QString viewSettingsFile):ContainmentView(corona),m_viewSettingsFile(std::move(viewSettingsFile)) {
    m_reflow.setSingleShot(true);m_reflow.setInterval(0);
    connect(this,&QWindow::xChanged,this,&PanelViewHost::updateMask);
    connect(this,&QWindow::yChanged,this,&PanelViewHost::updateMask);
    connect(this,&QWindow::widthChanged,this,&PanelViewHost::updateMask);
    connect(this,&QWindow::heightChanged,this,&PanelViewHost::updateMask);
    connect(&m_reflow,&QTimer::timeout,this,&PanelViewHost::reflow);
    connect(this,&PlasmaQuick::ContainmentView::locationChanged,this,[this](Plasma::Types::Location location){
        // PanelView 6.7.5 follows a new edge with the form factor and restore(). Outside
        // its Panel Settings the R4 contract stands: the runtime recreates the view and
        // the caller rereads the preferences of the new scope explicitly.
        if(m_userConfiguring && containment())adoptLocation(location);
        emit policyChanged();m_reflow.start();
    });
    connect(this,&PlasmaQuick::ContainmentView::formFactorChanged,&m_reflow,qOverload<>(&QTimer::start));
    connect(&m_floatingAnimation,&QPropertyAnimation::valueChanged,this,[this]{updateMask();});
    // PanelView 6.7.5: leaving the panel rehides it after 500 ms; edit mode re-evaluates.
    m_unhideTimer.setSingleShot(true);m_unhideTimer.setInterval(500);
    connect(&m_unhideTimer,&QTimer::timeout,this,&PanelViewHost::restoreAutoHide);
    if(corona)connect(corona,&Plasma::Corona::editModeChanged,this,&PanelViewHost::restoreAutoHide);
    m_hideAnimation.setDuration(200);
    connect(&m_hideAnimation,&QVariantAnimation::valueChanged,this,[this](const QVariant &value){
        contentItem()->setPosition(value.toPointF());
    });
    setTranslationDomain("plasma_shell_org.kde.plasma.desktop");
    rootContext()->setContextProperty("panel",this);
    connect(this,&QWindow::screenChanged,this,&PanelViewHost::screenToFollowChanged);
    connect(&m_theme,&Plasma::Theme::themeChanged,this,&PanelViewHost::adaptiveOpacityEnabledChanged);
    connect(&m_theme,&Plasma::Theme::themeChanged,this,&PanelViewHost::updateMask);
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
    static std::atomic<quint64> nextSurfaceOrder{1};
    // PanelView::event 6.7.5 for the edge-activated modes. Entering the hidden strip is
    // what KWin's screen edge does for the original: it reveals the panel.
    switch(event->type()) {
    case QEvent::FocusOut:
    case QEvent::Hide:
        if(event->type()==QEvent::Hide)m_containsMouse=false;
        // Do not leave AcceptingInput armed after returning to an application:
        // Hyprland gives an on-demand layer keyboard focus even on mere hover.
        if(containment() && containment()->status()==Plasma::Types::AcceptingInputStatus)
            containment()->setStatus(Plasma::Types::PassiveStatus);
        break;
    case QEvent::KeyPress:
        // PanelView::keyPressEvent 6.7.5 also releases its input mode on Escape.
        if(static_cast<QKeyEvent*>(event)->key()==Qt::Key_Escape && containment() &&
           containment()->status()==Plasma::Types::AcceptingInputStatus)
            containment()->setStatus(Plasma::Types::PassiveStatus);
        break;
    case QEvent::Show:
        m_surfaceOrder=nextSurfaceOrder.fetch_add(1);
        break;
    case QEvent::Enter:
        m_containsMouse=true;
        if(edgeActivated()){m_unhideTimer.stop();if(m_autoHidden)setAutoHideEnabled(false);}
        break;
    case QEvent::Leave:
        m_containsMouse=false;if(edgeActivated())m_unhideTimer.start();break;
    case QEvent::DragEnter:
        m_containsDrag=true;
        if(edgeActivated()){m_unhideTimer.stop();if(m_autoHidden)setAutoHideEnabled(false);}
        break;
    case QEvent::DragLeave:
        m_containsDrag=false;m_containsMouse=false;if(edgeActivated())m_unhideTimer.start();break;
    case QEvent::Drop:m_containsDrag=false;break;
    default:break;
    }
    const bool result=ContainmentView::event(event);
    if((event->type()==QEvent::Expose && !isExposed()) ||
       (event->type()==QEvent::PlatformSurface && static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed))invalidateFrame();
    return result;
}
void PanelViewHost::resizeEvent(QResizeEvent *event) {
    ContainmentView::resizeEvent(event);
    if(auto *root=rootObject();root && size().isValid() && root->size()!=QSizeF(size())) {
        root->setSize(size());
        updateMask();
    }
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
    // The explorer, alternatives and settings QML hold "panel"/the containment:
    // destroy them now, not after a deferred delete.
    delete m_alternativesEngine.data();
    delete m_widgetExplorer.data();
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
        {"nativeInputMask",true},{"adaptiveWindowBackend",false},{"autohide",native},
        {"autoHideBackend",native?QStringLiteral("bwm-edge-strip"):QString()},{"autoHidden",m_autoHidden},{"touchingWindow",m_touchingWindow},
        {"minimumLength",m_minimumLength},{"maximumLength",m_maximumLength},
        {"viewSettingsReady",m_settings && m_settings->ready()},{"viewSettingsScope",m_settings ? m_settings->scope() : QString()},
        {"persistentViewKeys",keys},{"nativeVisibilityPolicy",native},
        {"reservationRequested",property("bwmReservationRequested").toBool()},
        {"reservationOwner",property("bwmPanelReservationAllowed").isValid()?property("bwmPanelReservationAllowed").toBool():native},
        {"editModeReservation",property("bwmPanelEditing").toBool()},
        {"exclusiveZoneRequested",property("bwmExclusiveZoneRequested").isValid()?property("bwmExclusiveZoneRequested").toInt():-1},
        {"nativeShadowRequests",PanelShadows::self()->windowState(const_cast<PanelViewHost*>(this))},
        {"blurAvailable",KWindowEffects::isEffectAvailable(KWindowEffects::BlurBehind)},
        {"contrastAvailable",KWindowEffects::isEffectAvailable(KWindowEffects::BackgroundContrast)},
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
    // These signals can be emitted while KSvg is evaluating its mask/margins.
    // Reading panelMask and publishing enabledBorders synchronously from there
    // re-enters the same QML binding. Apply after its evaluation has completed.
    connect(root,SIGNAL(panelMaskChanged()),this,SLOT(updateMask()),Qt::QueuedConnection);
    // PanelView observes padding independently from the graphical mask. A style
    // can change these SVG margins without changing the mask at all.
    for(const char *signal:{SIGNAL(leftShadowMarginChanged()),SIGNAL(topShadowMarginChanged()),
        SIGNAL(rightShadowMarginChanged()),SIGNAL(bottomShadowMarginChanged())})
        connect(root,signal,this,SLOT(updateMask()),Qt::QueuedConnection);
    // Panel.qml decides DodgeWindows from its own TasksModel (touchingWindow), as for
    // PanelView. Its window model gets the BWM source when task actions are enabled.
    if(root->metaObject()->indexOfSignal("touchingWindowChanged()")>=0)
        connect(root,SIGNAL(touchingWindowChanged()),this,SLOT(updateTouchingWindow()));
    BwmTaskBridge::attachEnabled(root);
    m_floatingAnimation.setTargetObject(root);m_floatingAnimation.setPropertyName("floatingness");
    // The base view supplies native containment parenting and configureRequested. Route
    // configuration through one PanelSession, rather than opening a second ConfigView.
    m_session=new PanelSession(c,false,true);m_session->setParent(this);
    setProperty("bwmPanelSession",QVariant::fromValue(m_session.data()));
    setContainment(c);
    m_item=PlasmaQuick::AppletQuickItem::itemForApplet(c);
    if(!m_item || c->failedToLaunch()) {
        setError(c->launchErrorMessage().isEmpty() ? tr("The native panel containment did not load.") : c->launchErrorMessage());return false;
    }
    m_session->bindPanelItem(m_item);m_session->packageWindows()->refresh();
    // libplasma's "add widgets" internal action emits showAddWidgetsInterface; plasmashell
    // answers it with ShellCorona::toggleWidgetExplorer, here the panel's own side bar.
    connect(c,&Plasma::Containment::showAddWidgetsInterface,this,[this]{toggleWidgetExplorer();});
    connect(c,&Plasma::Containment::appletAlternativesRequested,this,&PanelViewHost::showAlternativesForApplet);
    connect(c,&Plasma::Containment::statusChanged,this,[this](Plasma::Types::ItemStatus state){
        if(property("bwmLayerPanel").toBool())BwmSurface::setPanelAcceptsInput(this,state==Plasma::Types::AcceptingInputStatus);
        // PanelView::refreshStatus: attention or input shows the panel for a while.
        if(state==Plasma::Types::NeedsAttentionStatus || state==Plasma::Types::AcceptingInputStatus)showTemporarily();
        else restoreAutoHide();
    });
    connect(c,&Plasma::Applet::activated,this,[this]{if(edgeActivated())showTemporarily();});
    connect(c,&Plasma::Containment::userConfiguringChanged,this,[this](bool configuring){
        if(configuring)showTemporarily();else m_unhideTimer.start();
    });
    updateTouchingWindow();
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
    restoreAutoHide();
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
    if(m_backgroundHints==Plasma::Types::NoBackground)return KSvg::FrameSvg::NoBorder;
    if(!containment())return mask;
    const auto *root=rootObject();
    if(!root || root->property("floatingness").toDouble()==0) {
        switch(location()) {
        case Plasma::Types::TopEdge:mask &= ~KSvg::FrameSvg::TopBorder;break;
        case Plasma::Types::BottomEdge:mask &= ~KSvg::FrameSvg::BottomBorder;break;
        case Plasma::Types::LeftEdge:mask &= ~KSvg::FrameSvg::LeftBorder;break;
        case Plasma::Types::RightEdge:mask &= ~KSvg::FrameSvg::RightBorder;break;
        default:break;
        }
    }
    if(root && screen()) {
        const auto bounds=screen()->geometry();
        // wl_layer_shell doesn't report global position to QWindow. Qt may
        // reset x/y to zero after configure; use the anchoring owner's geometry.
        const auto rect=property("bwmPanelRect").isValid() ? property("bwmPanelRect").toRect() : geometry();
        if(rect.x()-qRound(root->property("leftShadowMargin").toReal())<=bounds.left())mask &= ~KSvg::FrameSvg::LeftBorder;
        if(rect.y()-qRound(root->property("topShadowMargin").toReal())<=bounds.top())mask &= ~KSvg::FrameSvg::TopBorder;
        if(rect.x()+rect.width()+qRound(root->property("rightShadowMargin").toReal())>=bounds.x()+bounds.width())mask &= ~KSvg::FrameSvg::RightBorder;
        if(rect.y()+rect.height()+qRound(root->property("bottomShadowMargin").toReal())>=bounds.y()+bounds.height())mask &= ~KSvg::FrameSvg::BottomBorder;
    }
    return mask;
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
    int side=screen() ? (vertical() ? screen()->size().height() : screen()->size().width()) : 0;
    if(side>0 && property("bwmExclusiveZoneRequested").toInt()>0 && property("bwmPanelBounds").isValid()) {
        const QRect bounds=property("bwmPanelBounds").toRect();
        if(!bounds.isEmpty() && screen()->geometry().contains(bounds))
            side=vertical() ? bounds.height() : bounds.width();
    }
    // PanelView::preferredSize 6.7.5. Panel.length is the content hint (m_contentLength).
    int extent=0;
    if(m_lengthMode==PanelViewEnums::FillAvailable && side>0)extent=side;
    else if(m_lengthMode==PanelViewEnums::FitContent && side>0)extent=std::max(total,std::min(side,m_length+pads));
    else {
        const int minimum=std::max(10,m_minimumLength);
        const int maximum=std::max(minimum,side>0 ? std::min(m_maximumLength,side-m_offset) : m_maximumLength);
        extent=std::clamp(m_length+pads,minimum,maximum);
    }
    const bool stretchedLayer=m_lengthMode==PanelViewEnums::FillAvailable && property("bwmLayerPanel").toBool();
    const QSize wanted=vertical() ? QSize(total,extent) : QSize(extent,total);
    const QSize minSize=stretchedLayer
        ? (vertical() ? QSize(total,std::min(extent,total)) : QSize(std::min(extent,total),total))
        : wanted;
    setMinimumSize(minSize);setMaximumSize(wanted);
    const int currentCross=vertical() ? width() : height();
    const int currentLength=vertical() ? height() : width();
    const bool keepConfiguredLength=stretchedLayer && isVisible()
        && QGuiApplication::platformName().startsWith(QStringLiteral("wayland"))
        && m_lastLengthMode==m_lengthMode && m_lastVertical==vertical()
        && currentCross==total && currentLength>0 && currentLength<=extent;
    if(!keepConfiguredLength && size()!=wanted)resize(wanted);
    root->setSize(size());m_lastVertical=vertical();m_lastLengthMode=m_lengthMode;
    if(m_hideAnimation.state()!=QAbstractAnimation::Running)contentItem()->setPosition(m_autoHidden?hiddenOffset():QPointF());
    updateMask();
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
    const int borders=enabledBorders();
    if(m_lastEnabledBorders!=borders){m_lastEnabledBorders=borders;emit policyChanged();}
    if(m_autoHidden) {
        PanelShadows::self()->removeWindow(this);
        KWindowEffects::enableBlurBehind(this,false);
        KWindowEffects::enableBackgroundContrast(this,false);
        // Only a strip on the output edge takes input while hidden, like KWin's edge.
        constexpr int strip=2;QRect rect(QPoint(),size());
        switch(containment()?containment()->location():Plasma::Types::BottomEdge){
        case Plasma::Types::TopEdge:rect.setHeight(strip);break;
        case Plasma::Types::LeftEdge:rect.setWidth(strip);break;
        case Plasma::Types::RightEdge:rect.setLeft(rect.right()+1-strip);break;
        default:rect.setTop(rect.bottom()+1-strip);break;
        }
        setMask(QRegion(rect));return;
    }
    const auto value=root->property("panelMask");
    auto region=value.metaType().id()==QMetaType::QRegion ? value.value<QRegion>() : QRegion();
    region.translate(root->property("floatingTranslucentItemOffset").toPoint());
    if(region.isEmpty())region=QRegion(QRect(QPoint(),size()));
    const bool background=m_backgroundHints!=Plasma::Types::NoBackground;
    KWindowEffects::enableBlurBehind(this,background && m_theme.blurBehindEnabled(),region);
    KWindowEffects::enableBackgroundContrast(this,background && m_theme.backgroundContrastEnabled(),
        m_theme.backgroundContrast(),m_theme.backgroundIntensity(),m_theme.backgroundSaturation(),region);
    // Plasma's graphical mask is tight; input extends to the physical edge for Fitts's law.
    QRect input(QPoint(),size());const auto bound=region.boundingRect();
    switch(location()) {
    case Plasma::Types::LeftEdge:input.setRight(bound.right());break;
    case Plasma::Types::TopEdge:input.setBottom(bound.bottom());break;
    case Plasma::Types::RightEdge:input.setLeft(bound.left());break;
    case Plasma::Types::BottomEdge:input.setTop(bound.top());break;
    default:break;
    }
    setMask(input);
    const QMargins padding(qRound(root->property("leftShadowMargin").toReal()),qRound(root->property("topShadowMargin").toReal()),
        qRound(root->property("rightShadowMargin").toReal()),qRound(root->property("bottomShadowMargin").toReal()));
    PanelShadows::self()->addWindow(this,KSvg::FrameSvg::EnabledBorders(enabledBorders()),padding);
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
        connect(view,&QWindow::xChanged,this,&PanelViewHost::relativeConfigRectChanged);
        connect(view,&QWindow::yChanged,this,&PanelViewHost::relativeConfigRectChanged);
        connect(view,&QWindow::widthChanged,this,&PanelViewHost::relativeConfigRectChanged);
        connect(view,&QWindow::heightChanged,this,&PanelViewHost::relativeConfigRectChanged);
        connect(view,&QWindow::visibleChanged,this,&PanelViewHost::relativeConfigRectChanged);
        if(corona())corona()->setEditMode(true);
        view->show();view->requestActivate();
        emit relativeConfigRectChanged();
        return;
    }
    if(corona() && corona()->isEditMode())corona()->setEditMode(false);
    if(m_session)m_session->configure(applet->id());
}

WidgetExplorerView *PanelViewHost::widgetExplorer()const{return m_widgetExplorer.data();}
bool PanelViewHost::toggleWidgetExplorer() {
    if(!containment())return false;
    if(!m_widgetExplorer)m_widgetExplorer=new WidgetExplorerView(this);
    // PanelConfigView 6.7.5 hides once the side bar takes focus; WidgetExplorer.qml
    // reopens it through "configure" when the explorer closes.
    if(!m_widgetExplorer->isVisible() && m_configView && m_configView->isVisible())m_configView->hide();
    if(!m_widgetExplorer->toggle()){setError(m_widgetExplorer->error());return false;}
    return true;
}

void PanelViewHost::showAlternativesForApplet(Plasma::Applet *applet) {
    // Adapted from plasma-workspace 6.7.5 ShellCorona::showAlternativesForApplet
    // (LGPL-2.0-or-later): loads the installed explorer/AppletAlternatives.qml.
    if(!applet || applet->destroyed() || !containment() || applet->containment()!=containment())return;
    if(m_showingAlternatives==applet && m_alternativesDialog && m_alternativesDialog->isVisible())return;
    delete m_alternativesEngine.data();
    const auto shell=KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"),QStringLiteral("org.kde.plasma.desktop"));
    QUrl alternativesQML=shell.fileUrl("appletalternativesui");
    if(alternativesQML.isEmpty())alternativesQML=shell.fileUrl("explorer",QStringLiteral("AppletAlternatives.qml"));
    if(!shell.isValid() || alternativesQML.isEmpty()) {
        setError(tr("The installed KDE Plasma shell AppletAlternatives.qml is missing."));return;
    }
    containment()->setStatus(Plasma::Types::RequiresAttentionStatus);
    auto *qmlObj=new PlasmaQuick::SharedQmlEngine(this);
    m_alternativesEngine=qmlObj;
    m_showingAlternatives=applet;
    qmlObj->setTranslationDomain(QStringLiteral("plasma_shell_org.kde.plasma.desktop"));
    qmlObj->setInitializationDelayed(true);
    qmlObj->setSource(alternativesQML);
    auto *helper=new AlternativesHelper(applet,qmlObj);

    struct AlternativesSurfaceFilter : QObject {
        QPointer<PanelViewHost> panel;
        QPointer<PlasmaQuick::SharedQmlEngine> engine;
        QPointer<AlternativesHelper> helper;
        AlternativesSurfaceFilter(PanelViewHost *p,PlasmaQuick::SharedQmlEngine *e,AlternativesHelper *h):QObject(e),panel(p),engine(e),helper(h) {
            qApp->installEventFilter(this);
        }
        void attach(PlasmaQuick::Dialog *dialog) {
            if(!dialog || !panel || !helper)return;
            dialog->installEventFilter(this);
            if(!panel->property("bwmLayerPanel").toBool())return;
            if(dialog->findChild<PopupAnchor*>(QStringLiteral("bwmAlternativesPopupAnchor"),Qt::FindDirectChildrenOnly))return;
            auto *anchor=new PopupAnchor(dialog);
            anchor->setObjectName(QStringLiteral("bwmAlternativesPopupAnchor"));
            anchor->setIndependentWindow(true);
            anchor->setVisualParent(helper->applet());
            anchor->setPopup(dialog);
        }
        bool eventFilter(QObject *watched,QEvent *event) override {
            if(event->type()==QEvent::PlatformSurface &&
               static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceCreated) {
                if(auto *dialog=qobject_cast<PlasmaQuick::Dialog*>(watched); dialog && engine) {
                    for(QQmlContext *ctx=qmlContext(dialog);ctx;ctx=ctx->parentContext()) {
                        if(ctx==engine->rootContext()){attach(dialog);break;}
                    }
                }
            }
            if(event->type()==QEvent::FocusOut && qobject_cast<PlasmaQuick::Dialog*>(watched) && panel) {
                // Hyprland gives keyboard focus to an on-demand layer on hover;
                // moving the pointer over the panel, its handle popup or Panel Settings
                // is not an outside click (FocusGrab handles outside clicks).
                QWindow *focused=QGuiApplication::focusWindow();
                if(focused==panel.data() || (panel->m_configView && focused==panel->m_configView.data()))
                    return true;
                if(auto *popup=qobject_cast<PlasmaQuick::PopupPlasmaWindow*>(focused))
                    if(popup->visualParent() && popup->visualParent()->window()==panel.data())
                        return true;
            }
            return QObject::eventFilter(watched,event);
        }
    };
    auto *filter=new AlternativesSurfaceFilter(this,qmlObj,helper);
    if(auto *preDialog=qobject_cast<PlasmaQuick::Dialog*>(qmlObj->rootObject()))
        filter->attach(preDialog);
    qmlObj->completeInitialization({{QStringLiteral("alternativesHelper"),QVariant::fromValue(helper)}});
    qApp->removeEventFilter(filter);
    auto *dialog=qobject_cast<PlasmaQuick::Dialog*>(qmlObj->rootObject());
    if(!dialog) {
        containment()->setStatus(Plasma::Types::ActiveStatus);
        m_showingAlternatives=nullptr;m_alternativesEngine=nullptr;
        delete qmlObj;setError(tr("Alternatives UI does not inherit from Dialog."));return;
    }
    filter->attach(dialog);
    m_alternativesDialog=dialog;
    dialog->requestActivate();
    const auto cleanup=[this,qmlObj,dialog,applet,cont=QPointer<Plasma::Containment>(containment())] {
        if(m_showingAlternatives==applet) {
            if(cont)cont->setStatus(Plasma::Types::ActiveStatus);
            m_showingAlternatives=nullptr;
        }
        if(m_alternativesDialog==dialog)m_alternativesDialog=nullptr;
        if(m_alternativesEngine==qmlObj)m_alternativesEngine=nullptr;
        qmlObj->deleteLater();
    };
    connect(applet,&Plasma::Applet::destroyedChanged,qmlObj,[cleanup](bool destroyed){if(destroyed)cleanup();});
    connect(dialog,&QQuickWindow::visibleChanged,qmlObj,[cleanup](bool visible){if(!visible)cleanup();});
}

void PanelViewHost::adoptLocation(Plasma::Types::Location location) {
    Qt::Edge edge;
    switch(location) {
    case Plasma::Types::TopEdge:edge=Qt::TopEdge;break;
    case Plasma::Types::BottomEdge:edge=Qt::BottomEdge;break;
    case Plasma::Types::LeftEdge:edge=Qt::LeftEdge;break;
    case Plasma::Types::RightEdge:edge=Qt::RightEdge;break;
    default:return;
    }
    const bool verticalEdge=edge==Qt::LeftEdge || edge==Qt::RightEdge;
    containment()->setFormFactor(verticalEdge ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
    // The preferences scope (Horizontal<width>/Vertical<height>) follows the orientation.
    if(m_settings && settingsScope()!=m_settings->scope() && !reloadViewSettings())return;
    reflow();
    // The same layer surface moves to the new edge; the runtime keeps this view.
    setProperty("bwmRuntimeEdge",int(edge));
    BwmSurface::setPanelEdge(this,edge);
}
int PanelViewHost::minThickness()const {
    auto *root=rootObject();return root ? root->property(vertical() ? "minPanelWidth" : "minPanelHeight").toInt() : 0;
}
bool PanelViewHost::persist(const QVariantMap &changes) {
    // Only the original Panel Settings write through, as PanelView does on every set.
    if(!m_userConfiguring || !m_settings)return false;
    return applyViewSettings(changes);
}
QRect PanelViewHost::relativeConfigRect()const {
    if(!m_configView || !m_configView->isVisible() || !screen())return {};
    const QRect popupRect=m_configView->property("bwmPopupRect").toRect();
    const QRect rect=popupRect.isValid() && !popupRect.isEmpty() ? popupRect : m_configView->geometry();
    return rect.translated(-screen()->geometry().topLeft());
}
void PanelViewHost::setUserConfiguring(bool value) {
    if(m_userConfiguring==value)return;m_userConfiguring=value;
    if(containment())containment()->setUserConfiguring(value);
    if(auto *vc=qobject_cast<ViewCorona*>(corona())) {
        if(value)vc->setPanelBeingConfigured(this);
        else if(vc->panelBeingConfigured()==this)vc->setPanelBeingConfigured(nullptr);
    }
    emit userConfiguringChanged();
    emit relativeConfigRectChanged();
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
    // AutoHide/DodgeWindows use the edge strip, which needs the native policy's surface
    // flush with the output edge; the preview surface keeps a gap.
    const bool native=property("bwmNativePanelPolicy").toBool() && property("bwmLayerPanel").toBool();
    if(value!=PanelViewEnums::WindowsGoBelow && !(native && value>=PanelViewEnums::NormalPanel && value<=PanelViewEnums::DodgeWindows)) {
        setError(tr("This panel visibility mode has no controller in the BWM host."));emit policyChanged();return;
    }
    if(persist({{"panelVisibility",value}}))return;
    if(m_userConfiguring && m_settings){emit policyChanged();return;}
    m_visibility=value;emit policyChanged();m_reflow.start();restoreAutoHide();
}
bool PanelViewHost::edgeActivated()const {
    return (m_visibility==PanelViewEnums::AutoHide || m_visibility==PanelViewEnums::DodgeWindows) &&
        property("bwmLayerPanel").toBool() && property("bwmNativePanelPolicy").toBool();
}
// restoreAutoHide/setAutoHideEnabled/showTemporarily/updateTouchingWindow follow
// plasma-workspace 6.7.5 shell/panelview.cpp (GPL-2.0-or-later, Marco Martin and KDE
// contributors). The hide/reveal itself is BWM's edge strip, not the KWin protocol.
void PanelViewHost::restoreAutoHide() {
    bool autoHide=true;
    disconnect(m_transientWindowVisibleWatcher);
    if(!edgeActivated())autoHide=false;
    else if(m_containsMouse || m_containsDrag)autoHide=false;
    else if(corona() && corona()->isEditMode())autoHide=false;
    else if(containment() && containment()->status()>=Plasma::Types::NeedsAttentionStatus &&
            containment()->status()!=Plasma::Types::HiddenStatus)autoHide=false;
    else {
        for(QWindow *window:QGuiApplication::topLevelWindows()) {
            if(window->transientParent()==this && window->isVisible()) {
                m_transientWindowVisibleWatcher=connect(window,&QWindow::visibleChanged,this,&PanelViewHost::restoreAutoHide);
                autoHide=false;break;
            }
        }
    }
    setAutoHideEnabled(autoHide);
}
void PanelViewHost::setAutoHideEnabled(bool enabled) {
    const bool hide=enabled && edgeActivated() &&
        (m_visibility==PanelViewEnums::AutoHide || (m_visibility==PanelViewEnums::DodgeWindows && m_touchingWindow));
    if(hide==m_autoHidden)return;
    m_autoHidden=hide;applyAutoHide(true);emit policyChanged();
}
void PanelViewHost::showTemporarily() {
    setAutoHideEnabled(false);
    auto *timer=new QTimer(this);timer->setSingleShot(true);timer->setInterval(3000);
    connect(timer,&QTimer::timeout,this,&PanelViewHost::restoreAutoHide);
    connect(timer,&QTimer::timeout,timer,&QObject::deleteLater);
    timer->start();
}
void PanelViewHost::updateTouchingWindow() {
    if(!rootObject())return;
    m_touchingWindow=rootObject()->property("touchingWindow").toBool();
    restoreAutoHide();
}
QPointF PanelViewHost::hiddenOffset()const {
    switch(containment()?containment()->location():Plasma::Types::BottomEdge){
    case Plasma::Types::TopEdge:return QPointF(0,-height());
    case Plasma::Types::LeftEdge:return QPointF(-width(),0);
    case Plasma::Types::RightEdge:return QPointF(width(),0);
    default:return QPointF(0,height());
    }
}
void PanelViewHost::applyAutoHide(bool animate) {
    const QPointF target=m_autoHidden?hiddenOffset():QPointF();
    m_hideAnimation.stop();
    updateMask();
    if(!animate || !isVisible() || contentItem()->position()==target){contentItem()->setPosition(target);return;}
    m_hideAnimation.setEasingCurve(m_autoHidden?QEasingCurve::InCubic:QEasingCurve::OutCubic);
    m_hideAnimation.setStartValue(contentItem()->position());m_hideAnimation.setEndValue(target);
    m_hideAnimation.start();
}
void PanelViewHost::setScreenToFollow(QScreen *target) {
    // Moving a panel to another output belongs to the runtime, which binds by description.
    if(!target || target==screen())return;
    if(receivers(SIGNAL(screenToFollowRequested(QScreen*)))>0){emit screenToFollowRequested(target);return;}
    setError(tr("Moving the panel to another output is not available in this host."));emit screenToFollowChanged();
}
void PanelViewHost::clonePanelTo(int location,QScreen *target) {
    if(receivers(SIGNAL(cloneRequested(int,QScreen*)))>0){emit cloneRequested(location,target);return;}
    setError(tr("Cloning panels is not available in this host."));
}

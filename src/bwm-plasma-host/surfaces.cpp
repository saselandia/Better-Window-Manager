// SPDX-License-Identifier: GPL-2.0-or-later
#include "surfaces.h"
#include <LayerShellQt/Window>
#include <QScreen>
#include <QGuiApplication>
#include <QtWaylandClient/private/qwaylanddisplay_p.h>
#include <QtWaylandClient/private/qwaylandscreen_p.h>
#include <qqml.h>
#include <algorithm>
#include <QDynamicPropertyChangeEvent>
#include <QPlatformSurfaceEvent>
#include <cmath>
#include <cstring>
#include <memory>
#include <QTimer>
#include <QLoggingCategory>
Q_LOGGING_CATEGORY(lcBwmAnchor,"bwm.r4.anchor",QtWarningMsg)
namespace BwmSurface {
class EffectsCommit final:public QObject {
public:
    explicit EffectsCommit(QQuickWindow *window):QObject(window),window(window){window->installEventFilter(this);}
    bool eventFilter(QObject *,QEvent *event)override {
        if(event->type()==QEvent::Expose && !pending) {
            pending=true;
            QTimer::singleShot(0,this,[this]{pending=false;if(window->isExposed())window->update();});
        }
        return false;
    }
private:
    QQuickWindow *window;bool pending=false;
};
void ensureNativeEffectsCommit(QQuickWindow *window) {
    if(!window || window->property("bwmNativeEffectsCommit").toBool())return;
    window->setProperty("bwmNativeEffectsCommit",true);new EffectsCommit(window);
}
QRect placePopup(const QRect &area,const QRect &anchor,QSize wanted,Qt::Edge edge,int gap) {
    if(area.isEmpty() || wanted.width()<=0 || wanted.height()<=0 || gap<0)return {};
    const QSize size(std::min(wanted.width(),area.width()),std::min(wanted.height(),area.height()));
    const int cx=anchor.x()+anchor.width()/2-size.width()/2;
    const int cy=anchor.y()+anchor.height()/2-size.height()/2;
    QPoint primary,other;
    switch(edge) {
    case Qt::BottomEdge:primary={cx,anchor.top()-gap-size.height()};other={cx,anchor.bottom()+1+gap};break;
    case Qt::TopEdge:primary={cx,anchor.bottom()+1+gap};other={cx,anchor.top()-gap-size.height()};break;
    case Qt::LeftEdge:primary={anchor.right()+1+gap,cy};other={anchor.left()-gap-size.width(),cy};break;
    case Qt::RightEdge:primary={anchor.left()-gap-size.width(),cy};other={anchor.right()+1+gap,cy};break;
    default:return {};
    }
    const QRect preferred(primary,size),alternative(other,size);
    auto intersectedArea=[&](const QRect &rect){const auto visible=rect.intersected(area);return qint64(visible.width())*visible.height();};
    QPoint point=primary;
    if(!area.contains(preferred) && intersectedArea(alternative)>intersectedArea(preferred))point=other;
    point.setX(std::clamp(point.x(),area.left(),area.right()+1-size.width()));
    point.setY(std::clamp(point.y(),area.top(),area.bottom()+1-size.height()));
    return {point,size};
}
QRect withoutPanelStrip(const QRect &area,const QRect &panel,Qt::Edge edge) {
    if(area.isEmpty() || panel.isEmpty() || !area.intersects(panel))return area;
    QRect result=area;
    switch(edge) {
    case Qt::BottomEdge:result.setBottom(std::min(area.bottom(),panel.top()-1));break;
    case Qt::TopEdge:result.setTop(std::max(area.top(),panel.bottom()+1));break;
    case Qt::LeftEdge:result.setLeft(std::max(area.left(),panel.right()+1));break;
    case Qt::RightEdge:result.setRight(std::min(area.right(),panel.left()-1));break;
    default:break;
    }
    return result.isValid() ? result : area;
}
static PanelPlacement windowPlacement(QQuickWindow *window) {
    PanelPlacement placement;
    if(window->property("bwmPanelAlignment").isValid())placement.alignment=window->property("bwmPanelAlignment").toInt();
    placement.offset=window->property("bwmPanelOffset").toInt();
    if(window->property("bwmPanelLengthMode").isValid())placement.lengthMode=window->property("bwmPanelLengthMode").toInt();
    return placement;
}
int panelStart(const PanelPlacement &placement,int screenExtent,int panelExtent) {
    const int offset=placement.lengthMode==2 ? placement.offset : 0;
    switch(placement.alignment) {
    case Qt::AlignRight:return screenExtent-panelExtent-offset;
    // The layer path of PanelView 6.7.5 sets no margin for a centered panel, so
    // the compositor centers it: publish that position, not a shifted one.
    case Qt::AlignCenter:return (screenExtent-panelExtent)/2;
    default:return offset;
    }
}
static void panelGeometry(QQuickWindow *window,Qt::Edge edge,int gap) {
    if(!window->screen())return;
    const QRect screen=window->screen()->geometry();
    QRect bounds=screen;
    const bool reserves=window->property("bwmExclusiveZoneRequested").toInt()>0;
    if(reserves && window->property("bwmPanelBounds").isValid()) {
        const QRect candidate=window->property("bwmPanelBounds").toRect();
        if(!candidate.isEmpty() && screen.contains(candidate))bounds=candidate;
    }
    const bool vertical=edge==Qt::LeftEdge || edge==Qt::RightEdge;
    const int start=panelStart(windowPlacement(window),vertical?bounds.height():bounds.width(),vertical?window->height():window->width());
    QPoint pos;
    switch(edge) {
    case Qt::BottomEdge:pos={bounds.left()+start,bounds.bottom()+1-gap-window->height()};break;
    case Qt::TopEdge:pos={bounds.left()+start,bounds.top()+gap};break;
    case Qt::LeftEdge:pos={bounds.left()+gap,bounds.top()+start};break;
    case Qt::RightEdge:pos={bounds.right()+1-gap-window->width(),bounds.top()+start};break;
    default:return;
    }
    window->setProperty("bwmPanelRect",QRect(pos,window->size()));
    // Wayland does not report a layer surface position back to Qt. Plasma packages and
    // PlasmaQuick::Dialog use mapToGlobal(), so publish the anchored position to QWindow.
    if(window->position()!=pos)window->setPosition(pos);
    window->setProperty("bwmPanelEdge",int(edge));
}
using LayerWindow=LayerShellQt::Window;

static LayerWindow::Anchor layerAnchor(Qt::Edge edge) {
    switch (edge) {
    case Qt::TopEdge: return LayerWindow::AnchorTop;
    case Qt::BottomEdge: return LayerWindow::AnchorBottom;
    case Qt::LeftEdge: return LayerWindow::AnchorLeft;
    case Qt::RightEdge: return LayerWindow::AnchorRight;
    }
    return LayerWindow::AnchorNone;
}

PanelAnchoring nativePanelAnchoring(Qt::Edge edge, int screenExtent, int panelExtent, bool explicitExclusiveEdge,
                                    const PanelPlacement &along) {
    const bool vertical = edge == Qt::LeftEdge || edge == Qt::RightEdge;
    const auto exclusiveEdge = layerAnchor(edge);
    const auto leading = vertical ? LayerWindow::AnchorTop : LayerWindow::AnchorLeft;
    const auto trailing = vertical ? LayerWindow::AnchorBottom : LayerWindow::AnchorRight;
    PanelAnchoring placement{LayerWindow::Anchors(exclusiveEdge), exclusiveEdge, {}};
    const int offset = along.lengthMode == 2 ? along.offset : 0;
    // PanelView::updateLayerWindow 6.7.5: FillAvailable stretches between both
    // perpendicular anchors (zero desired extent along that axis) so the compositor
    // fits the panel inside usableArea when adjacent edges reserve space without
    // overflowing or overlapping corners. Custom/FitContent keep a single side anchor
    // (or none for center) with explicit size so perpendicular reservations do not
    // shrink a fixed-length panel.
    if (along.lengthMode == 0) {
        placement.anchors |= LayerWindow::Anchors(leading) | trailing;
    } else if (along.alignment == Qt::AlignLeft || (along.alignment != Qt::AlignRight && along.alignment != Qt::AlignCenter)) {
        placement.anchors |= leading;
        vertical ? placement.margins.setTop(offset) : placement.margins.setLeft(offset);
    } else if (along.alignment == Qt::AlignRight) {
        placement.anchors |= trailing;
        vertical ? placement.margins.setBottom(offset) : placement.margins.setRight(offset);
    }
    if (!explicitExclusiveEdge && along.lengthMode != 0) {
        // On older protocol versions a corner alone cannot reserve space.
        const int start = std::clamp(panelStart(along, screenExtent, panelExtent), 0, std::max(0, screenExtent - panelExtent));
        const int unused = std::max(0, screenExtent - panelExtent - start);
        placement.anchors |= LayerWindow::Anchors(leading) | trailing;
        placement.margins = vertical ? QMargins(0, start, 0, unused) : QMargins(start, 0, unused, 0);
    }
    return placement;
}

static bool supportsExplicitExclusiveEdge(QScreen *screen) {
    // Use Qt's registry for this connection. Do not open another display, bind
    // another layer-shell global, or block the GUI on a registry round trip.
    const auto *waylandScreen = dynamic_cast<const QtWaylandClient::QWaylandScreen *>(screen->handle());
    if (!waylandScreen) return false;
    uint version = 0;
    for (const auto &global : waylandScreen->display()->globals()) {
        if (global.interface != QStringLiteral("zwlr_layer_shell_v1")) continue;
        if (version) return false;
        version = global.version;
    }
    return version >= 5;
}

static void updatePanelPolicy(QQuickWindow *window) {
    if(!window->screen())return;
    using W=LayerShellQt::Window;auto *role=W::get(window);
    const auto edge=Qt::Edge(window->property("bwmPanelEdge").toInt());
    const bool vertical=edge==Qt::LeftEdge || edge==Qt::RightEdge;
    const int gap=window->property("bwmPanelGap").toInt();
    QMargins margins(edge==Qt::LeftEdge?gap:0,edge==Qt::TopEdge?gap:0,edge==Qt::RightEdge?gap:0,edge==Qt::BottomEdge?gap:0);
    const auto exclusiveEdge=layerAnchor(edge);
    W::Anchors anchors=exclusiveEdge;
    int zone=-1;QString error;
    if(window->property("bwmNativePanelPolicy").toBool()) {
        const int available=vertical?window->screen()->size().height():window->screen()->size().width();
        const int length=vertical?window->height():window->width();
        const auto placement=nativePanelAnchoring(edge,available,length,supportsExplicitExclusiveEdge(window->screen()),windowPlacement(window));
        anchors=placement.anchors;
        margins=placement.margins;
        const int cross=vertical?window->width():window->height();
        const int crossAvailable=vertical?window->screen()->size().width():window->screen()->size().height();
        if(window->property("bwmPanelOutputUnavailable").toBool())error=QStringLiteral("Native panel output changed; recreate its bound surface.");
        else if(length<=0 || length>available || cross<=0 || cross>crossAvailable)error=QStringLiteral("Native panel surface does not fit its output.");
        else if((window->property("bwmPanelVisibility").toInt()==0 || window->property("bwmPanelEditing").toBool()) && window->isVisible() &&
                (!window->property("bwmPanelReservationAllowed").isValid() || window->property("bwmPanelReservationAllowed").toBool()))
            zone=window->property("bwmPanelEditing").toBool()?window->property("bwmEditReservationZone").toInt():window->property("bwmReservationThickness").toInt();
    } else {
        // Preview without reservation: same side anchors as the native path, keeping the gap.
        const int available=vertical?window->screen()->size().height():window->screen()->size().width();
        const auto placement=nativePanelAnchoring(edge,available,vertical?window->height():window->width(),true,windowPlacement(window));
        anchors=placement.anchors;
        margins=QMargins(margins.left()+placement.margins.left(),margins.top()+placement.margins.top(),
                         margins.right()+placement.margins.right(),margins.bottom()+placement.margins.bottom());
    }
    const bool stretchedH=anchors.testFlags(W::Anchors(W::AnchorLeft)|W::AnchorRight);
    const bool stretchedV=anchors.testFlags(W::Anchors(W::AnchorTop)|W::AnchorBottom);
    const bool sizeMatches=(stretchedH || role->desiredSize().width()==window->width())
        && (stretchedV || role->desiredSize().height()==window->height());
    const bool roleChanged=role->anchors()!=anchors || role->exclusiveEdge()!=exclusiveEdge
        || role->margins()!=margins || role->exclusionZone()!=zone || !sizeMatches;
    window->setProperty("bwmSurfaceError",error);
    window->setProperty("bwmReservationRequested",zone>0);
    window->setProperty("bwmExclusiveZoneRequested",zone);
    panelGeometry(window,edge,gap);
    if(roleChanged) {
        role->setExclusiveZone(-1); // Withdraw the old request before changing geometry.
        role->setAnchors(anchors);
        role->setExclusiveEdge(exclusiveEdge);
        role->setMargins(margins);role->setDesiredSize(window->size());role->setExclusiveZone(zone);
        // A reservation handoff can change only layer-shell state, with an entirely
        // unchanged scene. QQuickWindow::update forces a render/commit; QWindow's
        // requestUpdate alone can leave the new exclusive zone pending indefinitely.
        window->update();
    }
}
void setPanelLayoutContext(QQuickWindow *window,const QRect &panelBounds,const QRect &availableRect) {
    if(!window)return;
    const bool boundsChanged=window->property("bwmPanelBounds").toRect()!=panelBounds ||
        window->property("bwmPanelBounds").isValid()!=panelBounds.isValid();
    const bool availChanged=window->property("bwmAvailableRect").toRect()!=availableRect ||
        window->property("bwmAvailableRect").isValid()!=availableRect.isValid();
    if(boundsChanged)window->setProperty("bwmPanelBounds",panelBounds.isValid()?QVariant(panelBounds):QVariant());
    if(availChanged)window->setProperty("bwmAvailableRect",availableRect.isValid()?QVariant(availableRect):QVariant());
    if(boundsChanged && window->property("bwmLayerPanel").toBool())
        panelGeometry(window,Qt::Edge(window->property("bwmPanelEdge").toInt()),window->property("bwmPanelGap").toInt());
}
bool setPanelVisibility(QQuickWindow *window,int mode,int thickness) {
    // 0 NormalPanel reserves; 1 AutoHide, 2 DodgeWindows and 3 WindowsGoBelow do not
    // (PanelView::updateExclusiveZone). 0..2 only with the explicit native policy.
    if(!window || !window->property("bwmLayerPanel").toBool() || mode<0 || mode>3 || thickness<16 || thickness>1024 ||
       (mode!=3 && !window->property("bwmNativePanelPolicy").toBool()))return false;
    window->setProperty("bwmPanelVisibility",mode);window->setProperty("bwmReservationThickness",thickness);
    updatePanelPolicy(window);return window->property("bwmSurfaceError").toString().isEmpty();
}
void setPanelReservationPolicy(QQuickWindow *window,bool allowed,bool editing) {
    if(!window || !window->property("bwmNativePanelPolicy").toBool())return;
    if(window->property("bwmPanelReservationAllowed").isValid() && window->property("bwmPanelReservationAllowed").toBool()==allowed &&
        window->property("bwmPanelEditing").toBool()==editing)return;
    // PanelView::updateExclusiveZone 6.7.5: entering edit mode only gives a
    // complete-frame zone to a panel which had none. Freeze the value while
    // configuring, preserving an existing owner's thickness-only reservation.
    if(editing && !window->property("bwmPanelEditing").toBool()) {
        const auto edge=Qt::Edge(window->property("bwmPanelEdge").toInt());
        const bool vertical=edge==Qt::LeftEdge || edge==Qt::RightEdge;
        const int previous=LayerShellQt::Window::get(window)->exclusionZone();
        window->setProperty("bwmEditReservationZone",previous>0?previous:(vertical?window->width():window->height()));
    }
    window->setProperty("bwmPanelReservationAllowed",allowed);window->setProperty("bwmPanelEditing",editing);updatePanelPolicy(window);
}
void configurePanel(QQuickWindow *window,Qt::Edge edge,int gap,bool nativePolicy) {
    if(!window || gap<0 || (edge!=Qt::TopEdge && edge!=Qt::BottomEdge && edge!=Qt::LeftEdge && edge!=Qt::RightEdge))return;
    ensureNativeEffectsCommit(window);
    // Native policy is explicit opt-in, never inferred from installed packages.
    if(nativePolicy)gap=0;
    window->setProperty("bwmLayerPanel",true);
    window->setProperty("bwmNativePanelPolicy",nativePolicy);window->setProperty("bwmPanelGap",gap);
    window->setProperty("bwmPanelOutputUnavailable",false);
    window->setProperty("bwmPanelVisibility",3);window->setProperty("bwmReservationThickness",48);
    window->setProperty("bwmPanelEdge",int(edge));
    auto *role=LayerShellQt::Window::get(window);
    role->setScope(nativePolicy?"bwm-r4-native-policy":"bwm-r4-preview");role->setLayer(LayerShellQt::Window::LayerTop);
    role->setExclusiveZone(-1);role->setCloseOnDismissed(true);
    // Same window setup as PanelView 6.7.5: transparent, frameless and without focus, so that
    // clicking a widget does not deactivate the Dialog it toggles (hideOnWindowDeactivate).
    window->setColor(Qt::transparent);
    setPanelAcceptsInput(window,false);
    auto update=[window]{updatePanelPolicy(window);};
    QObject::connect(window,&QQuickWindow::widthChanged,window,update);
    QObject::connect(window,&QQuickWindow::heightChanged,window,update);
    QObject::connect(window,&QWindow::visibleChanged,window,update);
    auto screenConnection=std::make_shared<QMetaObject::Connection>();
    const QPointer<QScreen> expectedScreen=window->screen();
    auto bindScreen=[window,update,screenConnection,nativePolicy,expectedScreen](QScreen *screen){
        QObject::disconnect(*screenConnection);
        auto *interface=LayerShellQt::Window::get(window);
        // Qt can assign a fallback output before the runtime's screenRemoved/
        // screenChanged callbacks run. Never remap a positive reservation there.
        if(nativePolicy && (!expectedScreen || screen!=expectedScreen.data())) {
            window->setProperty("bwmPanelOutputUnavailable",true);
            interface->setExclusiveZone(-1);window->hide();update();return;
        }
        const bool remap=window->isVisible() && interface->screen()!=screen;
        if(remap){window->hide();window->destroy();}
        interface->setScreen(screen);
        if(screen)*screenConnection=QObject::connect(screen,&QScreen::geometryChanged,window,update);
        update();if(remap)window->show();
    };
    QObject::connect(window,&QQuickWindow::screenChanged,window,bindScreen);
    bindScreen(window->screen());
}
void setPanelPlacement(QQuickWindow *window,const PanelPlacement &placement) {
    if(!window)return;
    const auto current=windowPlacement(window);
    window->setProperty("bwmPanelAlignment",placement.alignment);
    window->setProperty("bwmPanelOffset",placement.offset);
    window->setProperty("bwmPanelLengthMode",placement.lengthMode);
    if(window->property("bwmLayerPanel").toBool() && (current.alignment!=placement.alignment || current.offset!=placement.offset || current.lengthMode!=placement.lengthMode))
        updatePanelPolicy(window);
}
void setPanelEdge(QQuickWindow *window,Qt::Edge edge) {
    if(!window || !window->property("bwmLayerPanel").toBool() || (edge!=Qt::TopEdge && edge!=Qt::BottomEdge && edge!=Qt::LeftEdge && edge!=Qt::RightEdge))return;
    if(window->property("bwmPanelEdge").toInt()==int(edge))return;
    window->setProperty("bwmPanelEdge",int(edge));updatePanelPolicy(window);
}
void setPanelAcceptsInput(QQuickWindow *window,bool accepts) {
    if(!window)return;
    window->setFlag(Qt::FramelessWindowHint,true);
    window->setFlag(Qt::WindowDoesNotAcceptFocus,!accepts);
    auto *role=LayerShellQt::Window::get(window);
    // Revealing/recreating a panel is not a request to activate it. A focused widget
    // may accept input, but geometry/status updates must never activate the panel.
    role->setActivateOnShow(false);
    role->setKeyboardInteractivity(accepts ? LayerShellQt::Window::KeyboardInteractivityOnDemand : LayerShellQt::Window::KeyboardInteractivityNone);
    window->update();
}
void registerTypes(){qmlRegisterType<PopupAnchor>("org.bwm.plasma.host",1,0,"PopupAnchor");}
}
void PopupAnchor::bindMainItem() {
    auto *next=m_popup ? m_popup->property("mainItem").value<QQuickItem*>() : nullptr;
    if(m_watchedMainItem==next)return;
    if(m_watchedMainItem)disconnect(m_watchedMainItem,nullptr,this,nullptr);
    m_watchedMainItem=next;
    if(m_watchedMainItem) {
        connect(m_watchedMainItem,&QQuickItem::implicitWidthChanged,this,&PopupAnchor::update);
        connect(m_watchedMainItem,&QQuickItem::implicitHeightChanged,this,&PopupAnchor::update);
    }
    update();
}
void PopupAnchor::setPopup(QQuickWindow *popup) {
    BwmSurface::ensureNativeEffectsCommit(popup);
    if(m_popup==popup)return;
    m_grab.stop();++m_grabGeneration;
    if(m_popup){m_popup->removeEventFilter(this);disconnect(m_popup,nullptr,this,nullptr);}
    if(m_watchedMainItem){disconnect(m_watchedMainItem,nullptr,this,nullptr);m_watchedMainItem=nullptr;}
    if(m_boundScreen)disconnect(m_boundScreen,nullptr,this,nullptr);
    m_popup=popup;
    m_roleConfigured=false;m_boundScreen=nullptr;
    if(popup) {
        if(m_panel && m_panel->property("bwmLayerPanel").toBool())LayerShellQt::Window::get(popup);
        popup->installEventFilter(this);
        connect(popup,&QQuickWindow::widthChanged,this,&PopupAnchor::update);
        connect(popup,&QQuickWindow::heightChanged,this,&PopupAnchor::update);
        connect(popup,&QQuickWindow::visibleChanged,this,&PopupAnchor::update);
        connect(popup,&QQuickWindow::visibleChanged,this,&PopupAnchor::visibilityChanged);
        connect(popup,&QQuickWindow::xChanged,this,[this]{if(m_requestedPosition)update();});
        connect(popup,&QQuickWindow::yChanged,this,[this]{if(m_requestedPosition)update();});
        if(popup->metaObject()->indexOfSignal("mainItemChanged()")>=0)
            connect(popup,SIGNAL(mainItemChanged()),this,SLOT(bindMainItem()));
        bindMainItem();
    }
    update();visibilityChanged();emit changed();
}
PopupAnchor::PopupAnchor(QObject *parent):QObject(parent) {
    // Hyprland keeps keyboard focus on a layer when a click hits no surface, so a Dialog
    // with hideOnWindowDeactivate would never close. A cleared focus grab is that deactivation.
    connect(&m_grab,&FocusGrab::cleared,this,[this]{
        qCDebug(lcBwmAnchor)<<"focus grab cleared"<<(m_popup ? m_popup->objectName() : QString());
        m_grab.stop();
        if(m_popup && m_popup->isVisible() && m_popup->property("hideOnWindowDeactivate").toBool())m_popup->setVisible(false);
    });
}
void PopupAnchor::visibilityChanged() {
    m_grab.stop();
    const auto generation=++m_grabGeneration;
    if(m_popup && m_popup->isVisible())QTimer::singleShot(0,this,[this,generation]{tryFocusGrab(0,generation);});
}
void PopupAnchor::setNonInteractive(bool enabled) {
    if(m_nonInteractive==enabled)return;
    m_nonInteractive=enabled;visibilityChanged();update();
}
void PopupAnchor::tryFocusGrab(int attempt,quint64 generation) {
    if(generation!=m_grabGeneration)return;
    if(!m_popup || !m_popup->isVisible() || m_nonInteractive || m_grab.active())return;
    if(!m_panel || !m_panel->property("bwmLayerPanel").toBool() || !FocusGrab::available())return;
    if(!m_popup->property("hideOnWindowDeactivate").toBool())return;
    // The panel stays whitelisted so its launcher can toggle the popup closed itself, like a
    // click on a Plasma panel (it never takes focus). Only mapped companion Dialogs
    // belonging to this panel may join; another output/package must remain outside.
    QList<QWindow*> windows{m_popup.data(),m_panel.data()};
    for(auto *window:QGuiApplication::allWindows())
        if(window->isVisible() && window->isExposed() && window->property("bwmPackageWindowNonInteractive").toBool()) {
            auto *anchor=window->findChild<PopupAnchor*>(QStringLiteral("bwmPackagePopupAnchor"),Qt::FindDirectChildrenOnly);
            if(anchor && anchor->m_panel==m_panel)windows.append(window);
        }
    const bool started=m_grab.start(windows);
    qCDebug(lcBwmAnchor)<<"focus grab"<<m_popup->objectName()<<"started"<<started<<"attempt"<<attempt<<"windows"<<windows.size();
    if(!started && attempt<20)QTimer::singleShot(25,this,[this,attempt,generation]{tryFocusGrab(attempt+1,generation);});
}
void PopupAnchor::setVisualParent(QQuickItem *parent) {
    if(m_parent==parent)return;
    if(m_parent)disconnect(m_parent,nullptr,this,nullptr);
    m_parent=parent;
    if(parent) {
        connect(parent,&QObject::destroyed,this,[this]{
            m_parent=nullptr;m_grab.stop();++m_grabGeneration;
            if(m_popup)m_popup->hide();
        });
        connect(parent,&QQuickItem::windowChanged,this,&PopupAnchor::bindPanel);
        connect(parent,&QQuickItem::xChanged,this,&PopupAnchor::update);
        connect(parent,&QQuickItem::yChanged,this,&PopupAnchor::update);
        connect(parent,&QQuickItem::widthChanged,this,&PopupAnchor::update);
        connect(parent,&QQuickItem::heightChanged,this,&PopupAnchor::update);
    }
    bindPanel();emit changed();
}
void PopupAnchor::bindPanel() {
    m_grab.stop();++m_grabGeneration;
    if(m_panel){m_panel->removeEventFilter(this);disconnect(m_panel,nullptr,this,nullptr);}
    m_panel=m_parent ? m_parent->window() : nullptr;
    if(m_panel) {
        m_panel->installEventFilter(this);
        connect(m_panel,&QQuickWindow::afterAnimating,this,[this]{if(m_popup && m_popup->isVisible())update();});
        connect(m_panel,&QQuickWindow::widthChanged,this,&PopupAnchor::update);
        connect(m_panel,&QQuickWindow::heightChanged,this,&PopupAnchor::update);
        connect(m_panel,&QQuickWindow::screenChanged,this,&PopupAnchor::update);
        connect(m_panel,&QQuickWindow::visibleChanged,this,[this](bool visible){
            if(!visible){m_grab.stop();++m_grabGeneration;if(m_popup)m_popup->hide();}
        });
    }
    update();visibilityChanged();
}
bool PopupAnchor::eventFilter(QObject *object,QEvent *event) {
    if(object==m_panel && event->type()==QEvent::DynamicPropertyChange) {
        const auto name=static_cast<QDynamicPropertyChangeEvent*>(event)->propertyName();
        if(name=="bwmPanelRect" || name=="bwmPanelEdge" || name=="bwmAvailableRect")update();
    }
    if(object==m_popup && event->type()==QEvent::PlatformSurface &&
       static_cast<QPlatformSurfaceEvent*>(event)->surfaceEventType()==QPlatformSurfaceEvent::SurfaceCreated) {
        update();
    }
    return false;
}
void PopupAnchor::update() {
    if(m_updating || !m_popup || !m_parent || !m_panel || !m_panel->property("bwmLayerPanel").toBool())return;
    if(!m_panel->screen())return;
    m_updating=true;
    auto *screen=m_panel->screen();
    const bool remap=m_roleConfigured && m_boundScreen!=screen;
    if(m_boundScreen!=screen) {
        if(m_boundScreen)disconnect(m_boundScreen,nullptr,this,nullptr);
        connect(screen,&QScreen::geometryChanged,this,&PopupAnchor::update);
        connect(screen,&QScreen::availableGeometryChanged,this,&PopupAnchor::update);
    }
    const bool expanded=remap && !m_independentWindow && m_parent->property("expanded").toBool();
    const bool restoreWindow=remap && m_independentWindow && m_popup->isVisible();
    if(remap){m_popup->hide();m_popup->destroy();}
    m_boundScreen=screen;m_roleConfigured=true;
    if(m_popup->screen()!=screen)m_popup->setScreen(screen);
    const QRect panel=m_panel->property("bwmPanelRect").toRect();
    const QRect anchor=m_parent->mapRectToScene(QRectF(0,0,m_parent->width(),m_parent->height())).toAlignedRect().translated(panel.topLeft());
    const QRect area=m_panel->property("bwmAvailableRect").isValid() ? m_panel->property("bwmAvailableRect").toRect() : screen->availableGeometry();
    const auto edge=Qt::Edge(m_panel->property("bwmPanelEdge").toInt());
    const bool useUsableZone=m_panel->property("bwmExclusiveZoneRequested").toInt()>0 && !m_requestedPosition;
    auto *role=LayerShellQt::Window::get(m_popup);
    role->setScope("bwm-r4-popup");role->setLayer(LayerShellQt::Window::LayerOverlay);
    role->setExclusiveZone(useUsableZone ? 0 : -1);
    role->setKeyboardInteractivity(m_nonInteractive ? LayerShellQt::Window::KeyboardInteractivityNone : LayerShellQt::Window::KeyboardInteractivityOnDemand);
    role->setCloseOnDismissed(true);role->setScreen(screen);role->setActivateOnShow(!m_nonInteractive);
    QSize wanted=m_popup->size();
    auto *mainItem=m_popup->property("mainItem").value<QQuickItem*>();
    if(mainItem && mainItem!=m_watchedMainItem)bindMainItem();
    auto mainItemSize=[&](bool preferImplicitOnly)->QSize {
        if(!mainItem)return {};
        qreal iw=mainItem->implicitWidth(),ih=mainItem->implicitHeight();
        if(!preferImplicitOnly) {
            iw=std::max(iw,mainItem->width());
            ih=std::max(ih,mainItem->height());
        }
        if(iw<=0 || ih<=0) {
            for(QObject *child:mainItem->children()) {
                if(!child || !std::strstr(child->metaObject()->className(),"LayoutAttached"))continue;
                if(iw<=0) {
                    const qreal pref=child->property("preferredWidth").toReal();
                    const qreal minw=child->property("minimumWidth").toReal();
                    if(pref>0)iw=pref; else if(minw>0)iw=minw;
                }
                if(ih<=0) {
                    const qreal pref=child->property("preferredHeight").toReal();
                    const qreal minh=child->property("minimumHeight").toReal();
                    if(pref>0)ih=pref; else if(minh>0)ih=minh;
                }
            }
        }
        int w=int(std::ceil(std::max<qreal>(0,iw)));
        int h=int(std::ceil(std::max<qreal>(0,ih)));
        if(w>0 || h>0) {
            if(auto *margins=m_popup->property("margins").value<QObject*>()) {
                w+=margins->property("left").toInt()+margins->property("right").toInt();
                h+=margins->property("top").toInt()+margins->property("bottom").toInt();
            } else {
                w+=m_popup->property("leftPadding").toInt()+m_popup->property("rightPadding").toInt();
                h+=m_popup->property("topPadding").toInt()+m_popup->property("bottomPadding").toInt();
            }
        }
        return {w,h};
    };
    // Shared ToolTipDialog (PopupPlasmaWindow, not user-resizable AppletPopup) can keep a
    // stale/default QQuickWindow size (e.g. 640x480 or an earlier group tooltip) after
    // LayerShellQt configure. Always fit its desired layer size to mainItem's implicit size.
    const bool isIntrinsicPopup=m_popup->inherits("PlasmaQuick::PopupPlasmaWindow") && !m_popup->inherits("PlasmaQuick::AppletPopup");
    if(isIntrinsicPopup) {
        const QSize intrinsic=mainItemSize(true);
        if(intrinsic.width()>0 && intrinsic.height()>0) {
            wanted=intrinsic;
            if(m_popup->size()!=wanted)m_popup->resize(wanted);
        }
    }
    if(wanted.width()<=0 || wanted.height()<=0) {
        // PlasmaQuick::Dialog syncs its window size from mainItem in showEvent, which runs
        // after QWindow::create() (SurfaceCreated). A Top|Left layer surface cannot be created
        // with a zero desiredSize: derive an initial non-zero size before showEvent resizes it.
        const QSize derived=mainItemSize(false);
        wanted=QSize(std::max(wanted.width(),derived.width()),std::max(wanted.height(),derived.height()));
        wanted=QSize(std::max(1,wanted.width()),std::max(1,wanted.height()));
    }
    QRect placed=BwmSurface::placePopup(area,anchor,wanted,edge);
    if(m_requestedPosition && !placed.isEmpty()) {
        // A package position is honoured inside the available area, like
        // Dialog::repositionIfOffScreen, without covering the panel strip it was opened from
        // (packages such as Andromeda assume the panel touches the screen edge).
        const QRect free=BwmSurface::withoutPanelStrip(area,panel,edge);
        const QRect bounds=free.width()>=placed.width() && free.height()>=placed.height() ? free : area;
        placed.moveTo(std::clamp(m_popup->x(),bounds.left(),bounds.right()+1-placed.width()),
                      std::clamp(m_popup->y(),bounds.top(),bounds.bottom()+1-placed.height()));
    }
    qCDebug(lcBwmAnchor)<<"popup"<<m_popup->objectName()<<"requested"<<m_requestedPosition<<"usableZone"<<useUsableZone<<"pos"<<m_popup->position()<<"size"<<m_popup->size()
        <<"panel"<<panel<<"anchor"<<anchor<<"area"<<area<<"screen"<<screen->name()<<screen->geometry()<<"placed"<<placed<<"plasmoidScreen"<<m_parent->property("screenGeometry")<<"avail"<<m_parent->property("availableScreenRect")<<"global"<<m_parent->mapToGlobal(QPointF(0,0))<<"panelWinPos"<<m_panel->position();
    if(!placed.isEmpty()) {
        using W=LayerShellQt::Window;
        W::Anchors popupAnchors=W::Anchors(W::AnchorTop)|W::AnchorLeft;
        QMargins popupMargins(placed.x()-screen->geometry().x(),placed.y()-screen->geometry().y(),0,0);
        if(useUsableZone) {
            // exclusiveZone=0 places the popup inside Hyprland's usableArea (excluding both
            // our own reserving panels and any external bars). Along the panel's own edge,
            // Hyprland already offset by `zone`, so only a floating overhang (size - zone)
            // needs margin; along the perpendicular axis, align relative to `area`.
            const int zone=m_panel->property("bwmExclusiveZoneRequested").toInt();
            const int overhangH=std::max(0,panel.width()-zone);
            const int overhangV=std::max(0,panel.height()-zone);
            switch(edge) {
            case Qt::BottomEdge:
                popupAnchors=W::Anchors(W::AnchorBottom)|W::AnchorLeft;
                popupMargins=QMargins(std::max(0,placed.left()-area.left()),0,0,overhangV);
                break;
            case Qt::TopEdge:
                popupAnchors=W::Anchors(W::AnchorTop)|W::AnchorLeft;
                popupMargins=QMargins(std::max(0,placed.left()-area.left()),overhangV,0,0);
                break;
            case Qt::LeftEdge:
                popupAnchors=W::Anchors(W::AnchorLeft)|W::AnchorTop;
                popupMargins=QMargins(overhangH,std::max(0,placed.top()-area.top()),0,0);
                break;
            case Qt::RightEdge:
                popupAnchors=W::Anchors(W::AnchorRight)|W::AnchorTop;
                popupMargins=QMargins(0,std::max(0,placed.top()-area.top()),overhangH,0);
                break;
            default:break;
            }
        }
        role->setAnchors(popupAnchors);
        role->setDesiredSize(placed.size());
        role->setMargins(popupMargins);
        m_popup->setProperty("bwmPopupRect",placed);
        // Publish the final position (fixed positions are disabled in main): packages that
        // place companion Dialogs from root.x/y, such as Andromeda's avatar, follow it.
        // The resulting move signal is ignored while m_updating is set.
        if(m_requestedPosition && m_popup->position()!=placed.topLeft())m_popup->setPosition(placed.topLeft());
        if(m_popup->isVisible()){m_popup->update();m_popup->requestUpdate();}
    }
    m_updating=false;
    if(expanded)QTimer::singleShot(0,this,[this]{if(m_parent && m_popup)m_parent->setProperty("expanded",true);});
    else if(restoreWindow)QTimer::singleShot(0,this,[this]{if(m_popup)m_popup->show();});
}

// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QRect>
#include <QQuickItem>
#include <QQuickWindow>
#include <LayerShellQt/Window>
#include "focusgrab.h"
namespace BwmSurface {
// All inputs/outputs are logical pixels in the same screen coordinate system.
QRect placePopup(const QRect &available, const QRect &anchor, QSize wanted, Qt::Edge panelEdge, int gap=0);
void configurePanel(QQuickWindow *window, Qt::Edge edge, int gap=64, bool nativePolicy=false);
struct PanelAnchoring {
    LayerShellQt::Window::Anchors anchors;
    LayerShellQt::Window::Anchor exclusiveEdge;
    QMargins margins;
};
// Placement along the panel's axis, as PanelView 6.7.5: Qt::AlignLeft/AlignCenter/
// AlignRight and LengthMode FillAvailable(0)/FitContent(1)/Custom(2). The offset
// only applies to a Custom length on a side alignment, like its layer anchoring.
struct PanelPlacement {int alignment=Qt::AlignLeft;int offset=0;int lengthMode=2;};
// Start of the panel along its axis, relative to the output (logical pixels).
int panelStart(const PanelPlacement &placement,int screenExtent,int panelExtent);
PanelAnchoring nativePanelAnchoring(Qt::Edge edge, int screenExtent, int panelExtent, bool explicitExclusiveEdge,
                                    const PanelPlacement &placement=PanelPlacement());
// Updates the anchoring of a configured panel surface without changing its role.
void setPanelPlacement(QQuickWindow *window, const PanelPlacement &placement);
// Moves a configured panel surface to another screen edge in place, as
// PanelView::updateLayerWindow re-anchors a mapped panel when its location changes.
void setPanelEdge(QQuickWindow *window, Qt::Edge edge);
// Explicit opt-in controller: native NormalPanel (0) or WindowsGoBelow (3).
// A positive exclusive zone is a request, never confirmation by the compositor.
bool setPanelVisibility(QQuickWindow *window, int mode, int thickness);
// Available area minus the strip on the panel's side (logical pixels).
QRect withoutPanelStrip(const QRect &area, const QRect &panel, Qt::Edge edge);
// PanelView::refreshStatus (plasma-workspace 6.7.5): a panel never takes keyboard focus
// unless its containment reports AcceptingInputStatus (e.g. a widget with a text field).
void setPanelAcceptsInput(QQuickWindow *window, bool accepts);
void registerTypes();
}
class QScreen;
class PopupAnchor:public QObject {
    Q_OBJECT
    Q_PROPERTY(QQuickWindow *popup READ popup WRITE setPopup NOTIFY changed)
    Q_PROPERTY(QQuickItem *visualParent READ visualParent WRITE setVisualParent NOTIFY changed)
public:
    explicit PopupAnchor(QObject *parent=nullptr);
    QQuickWindow *popup()const{return m_popup;}
    QQuickItem *visualParent()const{return m_parent;}
    void setPopup(QQuickWindow *);
    void setVisualParent(QQuickItem *);
    void setUseRequestedPosition(bool enabled) {m_requestedPosition=enabled;update();}
    void setIndependentWindow(bool enabled) {m_independentWindow=enabled;}
    // Notification/OSD/tooltip/output-only Dialogs: overlay role without keyboard focus.
    void setNonInteractive(bool enabled) {m_nonInteractive=enabled;update();}
Q_SIGNALS:
    void changed();
protected:
    bool eventFilter(QObject *,QEvent *) override;
private:
    void update();
    void visibilityChanged();
    void tryFocusGrab(int attempt);
    void bindPanel();
    QPointer<QQuickWindow> m_popup;
    QPointer<QQuickItem> m_parent;
    QPointer<QQuickWindow> m_panel;
    QPointer<QScreen> m_boundScreen;
    bool m_roleConfigured=false;
    bool m_updating=false;
    bool m_requestedPosition=false;
    bool m_independentWindow=false;
    bool m_nonInteractive=false;
    FocusGrab m_grab;
};

// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "focusgrab.h"
#include <QObject>
#include <QPointer>
#include <QString>
#include <memory>

class PanelViewHost;
class QQuickItem;
class QQuickWindow;
namespace Plasma {class Containment;}
namespace PlasmaQuick {class SharedQmlEngine;}

// R5: the original "Add Widgets" side bar. It loads the installed, unmodified
// org.kde.plasma.desktop explorer/WidgetExplorer.qml through qml/WidgetExplorerHost.qml,
// which provides what plasma-desktop 6.7.5 Desktop.qml gives it (no DesktopView here).
// Like ShellCorona::toggleWidgetExplorer, opening it enters the Corona edit mode.
// BWM: the side panel Dialog is a layer next to the edited panel; a Hyprland focus grab
// stands in for the window deactivation that hides it in KWin.
class WidgetExplorerView : public QObject {
    Q_OBJECT
public:
    explicit WidgetExplorerView(PanelViewHost *panel);
    ~WidgetExplorerView() override;
    // Toggles the side bar for the panel's containment. False (with error()) if the
    // installed explorer or its host cannot load.
    bool toggle();
    bool isVisible() const;
    QString error() const {return m_error;}
    QQuickItem *rootItem() const;
    QQuickWindow *sidePanel() const {return m_sidePanel;}
protected:
    bool eventFilter(QObject *watched, QEvent *event) override;
private:
    bool ensureLoaded();
    void place();
    void updateGrab();
    QPointer<PanelViewHost> m_panel;
    QPointer<Plasma::Containment> m_containment;
    std::unique_ptr<PlasmaQuick::SharedQmlEngine> m_engine;
    QPointer<QQuickWindow> m_sidePanel;
    FocusGrab m_grab;
    QString m_error;
};

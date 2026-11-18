/*
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/panelconfigview.{h,cpp}. It loads the
    installed, unmodified org.kde.plasma.desktop configuration/PanelConfiguration.qml
    with the same context objects (plasmoid, panel, configDialog) for the BWM host's
    PanelViewHost. Changes (BWM): no ShellCorona/KWayland/X11; the popup is placed with
    the host's layer-shell PopupAnchor; scripted spacer/separator additions use the
    containment API; window focus follows the host instead of PanelView focus tracking.
*/
#pragma once

#include <PlasmaQuick/PlasmaWindow>
#include <PlasmaQuick/PopupPlasmaWindow>
#include <PlasmaQuick/SharedQmlEngine>
#include <QPointer>
#include <memory>

class PanelViewHost;
class PanelConfigView;
class PopupAnchor;
namespace Plasma {class Containment;}
namespace LayerShellQt {class Window;}

class PanelRulerView : public PlasmaQuick::PlasmaWindow
{
    Q_OBJECT
public:
    PanelRulerView(Plasma::Containment *containment, PanelViewHost *panelView, PanelConfigView *mainConfigView);
    ~PanelRulerView() override;
    void syncPanelLocation();

protected:
    void showEvent(QShowEvent *ev) override;

private:
    Plasma::Containment *const m_containment;
    PanelViewHost *const m_panelView;
    PanelConfigView *const m_mainConfigView;
    LayerShellQt::Window *m_layerWindow = nullptr;
};

class PanelConfigView : public PlasmaQuick::PopupPlasmaWindow
{
    Q_OBJECT
    Q_PROPERTY(PanelRulerView *panelRulerView READ panelRulerView CONSTANT)
    Q_PROPERTY(QRect geometry READ geometry NOTIFY geometryChanged)

public:
    PanelConfigView(Plasma::Containment *containment, PanelViewHost *panelView);
    ~PanelConfigView() override;

    // Returns false (with error()) if the installed PanelConfiguration.qml cannot load.
    bool init();
    QString error() const { return m_error; }

    PanelRulerView *panelRulerView();
    QRect geometry() const;
    Q_INVOKABLE QScreen *screenFromWindow(QWindow *window) const;

public Q_SLOTS:
    void showAddWidgetDialog();
    void addPanelSpacer();
    void addPanelMarginsSeparator();

protected:
    void keyPressEvent(QKeyEvent *ev) override;
    void showEvent(QShowEvent *ev) override;
    void hideEvent(QHideEvent *ev) override;
    void moveEvent(QMoveEvent *ev) override;
    void resizeEvent(QResizeEvent *ev) override;

Q_SIGNALS:
    void geometryChanged(const QRect &geometry);

private:
    void addWidget(const QString &plugin, bool atStart);
    Plasma::Containment *m_containment;
    QPointer<PanelViewHost> m_panelView;
    std::unique_ptr<PanelRulerView> m_panelRulerView;
    std::unique_ptr<PlasmaQuick::SharedQmlEngine> m_sharedQmlEngine;
    PopupAnchor *m_anchor = nullptr;
    QString m_error;
};

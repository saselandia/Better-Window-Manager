/*
    SPDX-FileCopyrightText: 2013 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2014 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: GPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/desktopview.{h,cpp} for Hyprland
    layer-shell without copying views/Desktop.qml or views/DesktopEditMode.qml.
*/
#pragma once

#include "focusgrab.h"

#include <PlasmaQuick/ContainmentView>
#include <QColor>
#include <QPointer>
#include <QRect>
#include <QScreen>
#include <QUrl>

namespace Plasma {
class Applet;
class Containment;
class Corona;
}
class QProcess;
namespace PlasmaQuick {
class AppletQuickItem;
class ConfigView;
class Dialog;
class SharedQmlEngine;
}

class DesktopViewHost : public PlasmaQuick::ContainmentView
{
    Q_OBJECT
    Q_PROPERTY(QRect strictAvailableScreenRect READ strictAvailableScreenRect NOTIFY strictAvailableScreenRectChanged)
    Q_PROPERTY(QScreen *screenToFollow READ screenToFollow NOTIFY screenToFollowChanged)
    Q_PROPERTY(QObject *configuredPanel READ configuredPanel NOTIFY configuredPanelChanged)
    Q_PROPERTY(bool usedInAccentColor READ usedInAccentColor CONSTANT)
    Q_PROPERTY(QColor accentColor READ accentColor WRITE setAccentColor NOTIFY accentColorChanged)
    Q_PROPERTY(bool showPreviewBanner READ showPreviewBanner CONSTANT)
    Q_PROPERTY(QString error READ error NOTIFY errorChanged)

public:
    explicit DesktopViewHost(Plasma::Corona *corona, bool layerShell = false, QScreen *targetScreen = nullptr);
    ~DesktopViewHost() override;

    bool load(Plasma::Containment *containment);
    QString error() const { return m_error; }
    QUrl nativeSource() const { return m_nativeSource; }

    QRect strictAvailableScreenRect() const;
    QScreen *screenToFollow() const { return m_targetScreen.data(); }
    bool setScreenToFollow(QScreen *screen);
    QObject *configuredPanel() const;
    bool usedInAccentColor() const { return false; }
    QColor accentColor() const { return m_accentColor; }
    void setAccentColor(const QColor &color);
    bool showPreviewBanner() const { return false; }

    Q_INVOKABLE void enterEditMode();
    Q_INVOKABLE void toggleWidgetExplorer();
    void showAlternativesForApplet(Plasma::Applet *applet);
    // ShellCorona::setContainmentTypeForScreen 6.7.5 for this view (Wallpaper page "Layout").
    Plasma::Containment *setContainmentType(const QString &plugin);
    QWindow *configurationWindow() const;

    QQuickWindow *sidePanel() const;
    QQuickWindow *alternativesDialog() const { return m_alternativesDialog.data(); }

Q_SIGNALS:
    void strictAvailableScreenRectChanged();
    void screenToFollowChanged();
    void configuredPanelChanged();
    void accentColorChanged();
    void errorChanged();

protected:
    void showConfigurationInterface(Plasma::Applet *applet) override;
    void keyPressEvent(QKeyEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    void configureLayerSurface();
    void placeSidePanel(PlasmaQuick::Dialog *dialog);
    void updateSidePanelGrab();
    void placeAlternativesDialog(PlasmaQuick::Dialog *dialog, Plasma::Applet *applet);
    void setError(const QString &message);
    void connectContainment(Plasma::Containment *containment);
    void scheduleCompositorAreaRefresh();
    void refreshCompositorArea();

    bool m_layerShell = false;
    QPointer<QScreen> m_targetScreen;
    QUrl m_nativeSource;
    QString m_error;
    QColor m_accentColor = Qt::transparent;
    QPointer<PlasmaQuick::AppletQuickItem> m_item;
    QPointer<PlasmaQuick::Dialog> m_sidePanel;
    QPointer<PlasmaQuick::SharedQmlEngine> m_alternativesEngine;
    QPointer<QQuickWindow> m_alternativesDialog;
    QPointer<Plasma::Applet> m_showingAlternatives;
    QPointer<PlasmaQuick::ConfigView> m_configView;
    QList<QPointer<Plasma::Containment>> m_connectedContainments;
    // Hyprland's usable area of this output (all exclusive zones, also those of external bars),
    // in output-local coordinates; invalid when unknown (no compositor IPC).
    QRect m_compositorUsable;
    QPointer<QProcess> m_areaQuery;
    QPointer<QObject> m_appletConfigSession;
    FocusGrab m_sidePanelGrab;
    FocusGrab m_alternativesGrab;
};

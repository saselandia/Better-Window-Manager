// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <Plasma/Corona>
#include <QPointer>
#include <QHash>
#include <QSet>
#include <QTemporaryDir>
class QMenu;
class QQuickWindow;
class QScreen;
class QWindow;
class ContainmentManagement;
class DesktopViewHost;
class ViewCorona : public Plasma::Corona {
    Q_OBJECT
    Q_PROPERTY(QObject *panelBeingConfigured READ panelBeingConfigured NOTIFY panelBeingConfiguredChanged)
public:
    // ShellCorona API used by the original PanelConfiguration.qml, Desktop.qml and DesktopEditMode.qml.
    Q_INVOKABLE bool enteredEditModeViaDesktop()const{return m_enteredEditModeViaDesktop;}
    void setEnteredEditModeViaDesktop(bool viaDesktop);
    QObject *panelBeingConfigured()const{return m_panelBeingConfigured.data();}
    void setPanelBeingConfigured(QObject *panel);
    Q_INVOKABLE void showAddPanelContextMenu(const QPoint &pos);
    QMenu *addPanelMenu()const;
    QQuickWindow *viewForContainment(const Plasma::Containment *containment)const;
    bool moveContainmentToScreen(Plasma::Containment *containment,int screen);
    Q_INVOKABLE void showContainmentManagement();
    QWindow *managementWindow()const;
    void setDesktopViewsActive(bool active);
    QString containmentPreviewPath(Plasma::Containment *containment)const;
    void grabContainmentPreview(Plasma::Containment *containment);
    // ShellCorona::isScreenUiReady, read by the original Folder View (org.kde.desktopcontainment)
    // on both desktop and panel containments.
    Q_INVOKABLE bool isScreenUiReady(int screen)const;
    // Corona::createContainmentDelayed is protected; ShellCorona uses it to swap the desktop layout.
    Plasma::Containment *createContainmentDelayedForView(const QString &plugin){return createContainmentDelayed(plugin);}
    ViewCorona();
    ~ViewCorona()override;
    int numScreens()const override;
    QRect screenGeometry(int id)const override;
    QRect availableScreenRect(int id)const override;
    QRegion availableScreenRegion(int id)const override;
    int screenForContainment(const Plasma::Containment *containment)const override;
    void bind(Plasma::Containment *containment,QQuickWindow *window);
    void unbind(Plasma::Containment *containment);
    // Publishes the usable rect of a screen after subtracting our own reserving panels,
    // matching ShellCorona::_availableScreenRect 6.7.5. Pass an invalid rect to reset.
    void setScreenAvailableRect(QScreen *screen,const QRect &rect);
Q_SIGNALS:
    void panelBeingConfiguredChanged();
    void enteredEditModeViaDesktopChanged();
    // Action data of ShellCorona::populateAddPanelsMenu: a Panel containment plugin ID or
    // "plasma-desktop-template:<layout template ID>".
    void addPanelRequested(const QString &actionData,QScreen *screen);
    void movePanelRequested(Plasma::Containment *containment,QScreen *screen);
    void containmentPreviewReady(Plasma::Containment *containment,const QString &path);
private:
    void observe(QScreen *screen);
    void notifyScreens();
    struct Binding {
        QPointer<QQuickWindow> window;
        QMetaObject::Connection containmentDestroyed,windowDestroyed,screenChanged,targetChanged,windowVisible,uiReady;
    };
    void forget(const Plasma::Containment *containment);
    static bool isDesktop(const Plasma::Containment *containment);
    bool panelsReady(int screen)const;
    void updateDesktopScreens();
    void updateManagementAction();
    QHash<const Plasma::Containment*,Binding> m_views;
    QHash<const Plasma::Containment*,int> m_pendingScreens;
    QList<QPointer<DesktopViewHost>> m_ownedDesktops;
    bool m_desktopViewsActive=true;
    QHash<QScreen*,int> m_screenIds;
    QHash<QScreen*,QRect> m_availableRects;
    mutable QSet<const Plasma::Containment*> m_desktopsWithScreen;
    QPointer<QObject> m_panelBeingConfigured;
    QPointer<QMenu> m_addPanelMenu;
    bool m_enteredEditModeViaDesktop=false;
    QPointer<ContainmentManagement> m_management;
    QTemporaryDir m_previewDirectory;
    QHash<uint,QString> m_previews;
    QSet<uint> m_previewPending;
};

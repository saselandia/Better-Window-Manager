// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <Plasma/Corona>
#include <QPointer>
#include <QHash>
class QMenu;
class QQuickWindow;
class QScreen;
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
    // ShellCorona::isScreenUiReady, read by the original Folder View (org.kde.desktopcontainment)
    // on both desktop and panel containments.
    Q_INVOKABLE bool isScreenUiReady(int screen)const;
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
    void addPanelRequested(const QString &templateId,QScreen *screen);
private:
    void observe(QScreen *screen);
    void notifyScreens();
    struct Binding {
        QPointer<QQuickWindow> window;
        QMetaObject::Connection containmentDestroyed,windowDestroyed,screenChanged;
    };
    void forget(const Plasma::Containment *containment);
    QHash<const Plasma::Containment*,Binding> m_views;
    QHash<QScreen*,int> m_screenIds;
    QHash<QScreen*,QRect> m_availableRects;
    QPointer<QObject> m_panelBeingConfigured;
    QPointer<QMenu> m_addPanelMenu;
    bool m_enteredEditModeViaDesktop=false;
};

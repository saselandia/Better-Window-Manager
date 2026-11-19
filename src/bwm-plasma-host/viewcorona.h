// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <Plasma/Corona>
#include <QPointer>
#include <QHash>
class QQuickWindow;
class QScreen;
class ViewCorona : public Plasma::Corona {
    Q_OBJECT
public:
    // ShellCorona API used by the original PanelConfiguration.qml. The host has
    // no desktop containment, so edit mode is always entered from a panel.
    Q_INVOKABLE bool enteredEditModeViaDesktop()const{return false;}
    // ShellCorona::isScreenUiReady, read by the original Folder View (org.kde.desktopcontainment)
    // also when it is added to a panel. There is no desktop view here: a screen is ready when
    // every panel view bound on it is visible and its containment reports uiReady.
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
};

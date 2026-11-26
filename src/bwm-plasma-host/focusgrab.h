// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QList>
#include <QHash>
struct wl_surface;
class QWindow;
class FocusGrabClient;
// hyprland_focus_grab_v1 (hyprland-protocols): keyboard focus is limited to the whitelisted
// surfaces and a click outside them clears the grab. This is the Hyprland equivalent of the
// focus change that makes KWin deactivate a PlasmaCore.Dialog with hideOnWindowDeactivate.
// Without the protocol (other compositors, offscreen tests) available() is false and start()
// does nothing: the Dialog keeps its native behaviour.
class FocusGrab : public QObject {
    Q_OBJECT
public:
    explicit FocusGrab(QObject *parent=nullptr);
    ~FocusGrab() override;
    static bool available();
    // The first window is the keyboard destination (committed alone first, so the compositor
    // focuses it), the rest are companions added in a second commit. All must
    // be visible and exposed before committing: a panel alone must never grab input
    // while its popup is still mapping. Hiding/destroying any member releases the grab.
    // Transient companions (tooltips over the panel) are whitelisted too, but hiding or
    // destroying one only removes it from the grab: Kickoff hides its button tooltip when
    // it expands, and releasing the whole grab then gave the keyboard back to the previous
    // window, which closed the launcher it had just opened.
    bool start(const QList<QWindow*> &windows,const QList<QWindow*> &transient={});
    void stop();
    bool active()const{return m_client;}
Q_SIGNALS:
    void cleared();
private:
    bool eventFilter(QObject *, QEvent *) override;
    void dropTransient(QWindow *window);
    FocusGrabClient *m_client=nullptr;
    QList<QPointer<QWindow>> m_windows;
    QList<QMetaObject::Connection> m_connections;
    QHash<QWindow*,wl_surface*> m_transient;
};

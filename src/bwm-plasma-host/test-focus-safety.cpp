// SPDX-License-Identifier: GPL-2.0-or-later
// Run only through check-focus-safety.py, against its disposable nested Hyprland.
#include "surfaces.h"
#include <LayerShellQt/Window>
#include <QGuiApplication>
#include <QPlatformSurfaceEvent>
#include <QQuickWindow>
#include <QTest>
#include <QSignalSpy>
#include <memory>

class FocusSafetyTest:public QObject {
    Q_OBJECT
    void popupRole(QQuickWindow &w) {
        auto *role=LayerShellQt::Window::get(&w);
        role->setLayer(LayerShellQt::Window::LayerOverlay);
        role->setAnchors(LayerShellQt::Window::Anchors(LayerShellQt::Window::AnchorTop)|LayerShellQt::Window::AnchorLeft);
        role->setExclusiveZone(-1);role->setDesiredSize({160,100});
        role->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityOnDemand);
        role->setActivateOnShow(false);w.resize(160,100);
    }
private Q_SLOTS:
    void initTestCase() {
        QVERIFY(qEnvironmentVariable("BWM_FOCUS_NESTED")=="1");
        QVERIFY(QGuiApplication::platformName().startsWith("wayland"));
        QTRY_VERIFY(FocusGrab::available());
    }
    void unmappedPopupCannotGrabThroughItsPanel() {
        QQuickWindow panel;panel.resize(500,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge);
        panel.show();QTRY_VERIFY(panel.isExposed());
        QQuickWindow popup;popupRole(popup);
        FocusGrab grab;
        QVERIFY(!grab.start({&popup,&panel}));QVERIFY(!grab.active());
        popup.show(); // Visible isn't enough: no configure/expose has arrived yet.
        QVERIFY(!popup.isExposed());
        QVERIFY(!grab.start({&popup,&panel}));QVERIFY(!grab.active());
        QTRY_VERIFY(popup.isExposed());
        QVERIFY(grab.start({&popup,&panel}));QVERIFY(grab.active());
        popup.hide();QVERIFY(!grab.active());
    }
    void losingAnySurfaceReleasesInput_data() {
        QTest::addColumn<int>("operation");
        QTest::newRow("hide-popup")<<0;QTest::newRow("hide-panel")<<1;
        QTest::newRow("destroy-popup-surface")<<2;QTest::newRow("delete-panel")<<3;
    }
    void losingAnySurfaceReleasesInput() {
        QFETCH(int,operation);
        auto panel=std::make_unique<QQuickWindow>();panel->resize(500,48);
        BwmSurface::configurePanel(panel.get(),Qt::BottomEdge);panel->show();QTRY_VERIFY(panel->isExposed());
        QQuickWindow popup;popupRole(popup);popup.show();QTRY_VERIFY(popup.isExposed());
        FocusGrab grab;QVERIFY(grab.start({&popup,panel.get()}));
        if(operation==0)popup.hide();
        if(operation==1)panel->hide();
        if(operation==2)popup.destroy();
        if(operation==3)panel.reset();
        QVERIFY(!grab.active());
    }
    void passiveSurfacesNeverStartGrabs() {
        QQuickWindow passive;popupRole(passive);passive.setFlag(Qt::WindowDoesNotAcceptFocus,true);
        passive.show();QTRY_VERIFY(passive.isExposed());
        FocusGrab grab;QVERIFY(!grab.start({&passive}));QVERIFY(!grab.active());
    }
    void compositorClearDisarmsThePreviousGrab() {
        QQuickWindow first,second;popupRole(first);popupRole(second);
        first.show();second.show();QTRY_VERIFY(first.isExposed() && second.isExposed());
        FocusGrab oldGrab,newGrab;QSignalSpy cleared(&oldGrab,&FocusGrab::cleared);
        QVERIFY(oldGrab.start({&first}));QVERIFY(newGrab.start({&second}));
        QTRY_COMPARE(cleared.count(),1);QVERIFY(!oldGrab.active());
        QVERIFY(newGrab.active());newGrab.stop();
    }
    void grabKeepsKeyboardOnPopupNotPanel() {
        // Hyprland's refocusKeyboard picks any committed surface of an unordered map when the
        // focused one is outside the whitelist. If that was the panel, Qt reported the panel as
        // focus window and PopupPlasmaWindow hid the launcher it had just opened. Repeat with
        // fresh surfaces: the map order is not fixed.
        QQuickWindow app;app.setTitle("BWM focus fixture");app.resize(500,350);app.show();
        QTRY_VERIFY(app.isExposed());app.requestActivate();QTRY_VERIFY(app.isActive());
        for(int round=0;round<12;++round) {
            QQuickWindow panel;panel.resize(500,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge);
            panel.show();QTRY_VERIFY(panel.isExposed());
            QQuickItem widget(panel.contentItem());widget.setSize({32,32});
            QQuickWindow popup;popup.resize(160,100);popup.setProperty("hideOnWindowDeactivate",true);
            QList<QWindow*> focused;
            auto connection=connect(qApp,&QGuiApplication::focusWindowChanged,this,[&focused](QWindow *w){focused.append(w);});
            PopupAnchor anchor;anchor.setPopup(&popup);anchor.setVisualParent(&widget);
            popup.show();QTRY_VERIFY(popup.isExposed());
            QTRY_VERIFY_WITH_TIMEOUT(QGuiApplication::focusWindow()==&popup,2000);
            QTest::qWait(150);
            disconnect(connection);
            QVERIFY2(!focused.contains(&panel),qPrintable(QStringLiteral("round %1: panel received keyboard focus").arg(round)));
            QCOMPARE(QGuiApplication::focusWindow(),&popup);
            popup.hide();
            app.requestActivate();QTRY_VERIFY(app.isActive());
        }
    }
    void hidingTransientTooltipKeepsTheGrab() {
        // Kickoff hides its button tooltip when it expands. The tooltip was a full grab
        // member, so hiding it released the grab, returned the keyboard to the previous
        // window and PopupPlasmaWindow closed the launcher right after opening it.
        QQuickWindow app;app.setTitle("BWM focus fixture");app.resize(500,350);app.show();
        QTRY_VERIFY(app.isExposed());app.requestActivate();QTRY_VERIFY(app.isActive());
        QQuickWindow panel;panel.resize(500,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge);
        panel.show();QTRY_VERIFY(panel.isExposed());
        QQuickWindow tip;popupRole(tip);tip.setFlag(Qt::WindowDoesNotAcceptFocus,true);
        LayerShellQt::Window::get(&tip)->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);
        tip.show();QTRY_VERIFY(tip.isExposed());
        QQuickWindow popup;popupRole(popup);popup.show();QTRY_VERIFY(popup.isExposed());
        FocusGrab grab;QVERIFY(grab.start({&popup,&panel},{&tip}));
        QTRY_VERIFY_WITH_TIMEOUT(QGuiApplication::focusWindow()==&popup,2000);
        tip.hide();
        QVERIFY(grab.active());
        QTest::qWait(300);
        QCOMPARE(QGuiApplication::focusWindow(),&popup);
        QVERIFY(grab.active());
        panel.hide();QVERIFY(!grab.active()); // A required member still releases it.
    }
    void closingPopupPreservesApplicationFocus() {
        QQuickWindow app;app.setTitle("BWM focus fixture");app.resize(500,350);app.show();
        QTRY_VERIFY(app.isExposed());app.requestActivate();QTRY_VERIFY(app.isActive());
        QQuickWindow panel;panel.resize(500,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge);
        panel.show();QTRY_VERIFY(panel.isExposed());
        QVERIFY(!LayerShellQt::Window::get(&panel)->activateOnShow());
        QTRY_VERIFY(app.isActive());
        QQuickItem widget(panel.contentItem());widget.setSize({32,32});
        QQuickWindow popup;popup.resize(160,100);popup.setProperty("hideOnWindowDeactivate",true);
        PopupAnchor anchor;anchor.setPopup(&popup);anchor.setVisualParent(&widget);
        for(int i=0;i<4;++i) {
            popup.show();popup.hide(); // Old deferred retries must never arm a closed popup.
        }
        app.requestActivate();QTRY_VERIFY(app.isActive());QTest::qWait(650);
        QVERIFY(app.isActive());
        popup.show();QTRY_VERIFY(popup.isExposed());QTest::qWait(80);popup.hide();
        app.requestActivate();QTRY_VERIFY(app.isActive());QTest::qWait(650);
        QVERIFY(app.isActive());
    }
};
QTEST_MAIN(FocusSafetyTest)
#include "test-focus-safety.moc"

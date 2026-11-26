// SPDX-License-Identifier: GPL-2.0-or-later
#include "surfaces.h"
#include <LayerShellQt/Window>
#include <QScreen>
#include <QtTest>
#include <PlasmaQuick/AppletPopup>
class SurfaceTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void geometry_data() {
        QTest::addColumn<QRect>("area");QTest::addColumn<QRect>("anchor");QTest::addColumn<QSize>("size");QTest::addColumn<int>("edge");QTest::addColumn<QRect>("expected");
        QTest::newRow("bottom-second-output")<<QRect(2560,0,2560,1440)<<QRect(2700,1320,40,40)<<QSize(400,300)<<int(Qt::BottomEdge)<<QRect(2560,1020,400,300);
        QTest::newRow("top-negative-origin")<<QRect(-1920,0,1920,1080)<<QRect(-900,50,40,40)<<QSize(300,200)<<int(Qt::TopEdge)<<QRect(-1030,90,300,200);
        QTest::newRow("left-offset")<<QRect(0,720,2560,1440)<<QRect(20,900,40,40)<<QSize(400,300)<<int(Qt::LeftEdge)<<QRect(60,770,400,300);
        QTest::newRow("right-offset")<<QRect(0,720,2560,1440)<<QRect(2500,900,40,40)<<QSize(400,300)<<int(Qt::RightEdge)<<QRect(2100,770,400,300);
        QTest::newRow("flip")<<QRect(0,0,1920,1080)<<QRect(900,1000,40,40)<<QSize(300,300)<<int(Qt::TopEdge)<<QRect(770,700,300,300);
        QTest::newRow("oversize")<<QRect(0,0,200,100)<<QRect(50,40,40,40)<<QSize(1000,900)<<int(Qt::BottomEdge)<<QRect(0,0,200,100);
        QTest::newRow("reserved-region")<<QRect(0,40,1000,700)<<QRect(400,10,40,30)<<QSize(200,100)<<int(Qt::TopEdge)<<QRect(320,40,200,100);
    }
    void geometry(){QFETCH(QRect,area);QFETCH(QRect,anchor);QFETCH(QSize,size);QFETCH(int,edge);QFETCH(QRect,expected);QCOMPARE(BwmSurface::placePopup(area,anchor,size,Qt::Edge(edge)),expected);}
    void invalid(){QVERIFY(BwmSurface::placePopup({},QRect(0,0,10,10),QSize(20,20),Qt::BottomEdge).isEmpty());QVERIFY(BwmSurface::placePopup(QRect(0,0,100,100),{},QSize(20,20),Qt::BottomEdge,-1).isEmpty());}
    void rolePropertiesAndTransformedAnchor() {
        QQuickWindow panel;panel.resize(300,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge,64);
        auto *panelRole=LayerShellQt::Window::get(&panel);QCOMPARE(panelRole->exclusionZone(),-1);
        QCOMPARE(panelRole->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityNone);
        QVERIFY(!panelRole->activateOnShow());
        QVERIFY(panel.flags().testFlag(Qt::WindowDoesNotAcceptFocus));QCOMPARE(panel.color(),QColor(Qt::transparent));
        BwmSurface::setPanelAcceptsInput(&panel,true);
        QVERIFY(!panelRole->activateOnShow());
        QCOMPARE(panelRole->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityOnDemand);QVERIFY(!panel.flags().testFlag(Qt::WindowDoesNotAcceptFocus));
        BwmSurface::setPanelAcceptsInput(&panel,false);
        QCOMPARE(panelRole->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityNone);
        QQuickItem widget(panel.contentItem());widget.setPosition({20.5,10.5});widget.setSize({31,21});widget.setScale(1.25);
        QQuickWindow popup;popup.resize(100,80);PopupAnchor adapter;adapter.setPopup(&popup);adapter.setVisualParent(&widget);
        auto expected=[&]{const QRect anchor=widget.mapRectToScene(QRectF(0,0,widget.width(),widget.height())).toAlignedRect().translated(panel.property("bwmPanelRect").toRect().topLeft());return BwmSurface::placePopup(panel.screen()->geometry(),anchor,popup.size(),Qt::BottomEdge);};
        QCOMPARE(popup.property("bwmPopupRect").toRect(),expected());
        auto *role=LayerShellQt::Window::get(&popup);QCOMPARE(role->exclusionZone(),-1);QCOMPARE(role->layer(),LayerShellQt::Window::LayerOverlay);
        QCOMPARE(QPoint(role->margins().left(),role->margins().top()),expected().topLeft()-panel.screen()->geometry().topLeft());
        panel.setProperty("bwmAvailableRect",QRect(panel.screen()->geometry().topLeft(),QSize(200,100)));
        QVERIFY(QRect(panel.screen()->geometry().topLeft(),QSize(200,100)).contains(popup.property("bwmPopupRect").toRect()));
        panel.setProperty("bwmAvailableRect",QVariant());panel.resize(320,60);QCOMPARE(popup.property("bwmPopupRect").toRect(),expected());
    }
    void popupBordersFollowStrategyAndRealPlacement() {
        // PopupPlasmaWindowPrivate::updateBorders rules on the placed layer rect: the panel side
        // (AtPanelEdges) and an output edge it touches (AtScreenEdges) lose their border, so the
        // theme draws square corners there; libplasma's own recomputation does not win.
        QQuickWindow panel;panel.resize(300,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge,0);
        QQuickItem widget(panel.contentItem());widget.setPosition({0,4});widget.setSize({40,40});
        PlasmaQuick::AppletPopup popup;popup.resize(200,120);popup.setPopupDirection(Qt::TopEdge);
        popup.setRemoveBorderStrategy(PlasmaQuick::PopupPlasmaWindow::AtScreenEdges|PlasmaQuick::PopupPlasmaWindow::AtPanelEdges);
        PopupAnchor adapter;adapter.setPopup(&popup);adapter.setVisualParent(&widget);
        const QRect placed=popup.property("bwmPopupRect").toRect();
        QCOMPARE(placed.left(),panel.screen()->geometry().left());
        QCOMPARE(popup.borders(),Qt::Edges(Qt::TopEdge|Qt::RightEdge));
        popup.setBorders(Qt::LeftEdge|Qt::RightEdge|Qt::TopEdge|Qt::BottomEdge); // libplasma's guess
        QTRY_COMPARE(popup.borders(),Qt::Edges(Qt::TopEdge|Qt::RightEdge));
        // A floating panel margin keeps every border, as in Plasma.
        popup.setMargin(8);
        QTRY_COMPARE(popup.borders(),Qt::Edges(Qt::LeftEdge|Qt::RightEdge|Qt::TopEdge|Qt::BottomEdge));
        // No strategy (applet default): all borders.
        popup.setMargin(0);popup.setRemoveBorderStrategy({});
        QTRY_COMPARE(popup.borders(),Qt::Edges(Qt::LeftEdge|Qt::RightEdge|Qt::TopEdge|Qt::BottomEdge));
    }
    void packageRequestedGeometryIsPreservedAndClamped() {
        QQuickWindow panel;panel.resize(300,48);BwmSurface::configurePanel(&panel,Qt::BottomEdge);
        QQuickItem widget(panel.contentItem());widget.setSize({32,32});
        panel.setProperty("bwmAvailableRect",QRect(-100,20,600,400));
        QQuickWindow popup;popup.resize(100,80);popup.setPosition({40,70});
        PopupAnchor adapter;adapter.setIndependentWindow(true);adapter.setUseRequestedPosition(true);
        adapter.setPopup(&popup);adapter.setVisualParent(&widget);
        QCOMPARE(popup.property("bwmPopupRect").toRect(),QRect(40,70,100,80));
        popup.setPosition({900,-100});
        QCOMPARE(popup.property("bwmPopupRect").toRect(),QRect(400,20,100,80));
        // A request that would cover the panel strip ends right above it.
        const QRect strip=panel.property("bwmPanelRect").toRect();
        panel.setProperty("bwmAvailableRect",QRect(strip.left(),strip.bottom()-399,600,400));
        popup.setPosition({strip.left()+10,strip.top()});
        QCOMPARE(popup.property("bwmPopupRect").toRect(),QRect(strip.left()+10,strip.top()-80,100,80));
    }
    void focusGrabWithoutProtocolIsInert() {
        // Offscreen (or a compositor without hyprland_focus_grab_v1): no grab, no signal, the
        // Dialog keeps its own hideOnWindowDeactivate behaviour.
        QVERIFY(!FocusGrab::available());
        QQuickWindow window;window.resize(10,10);window.show();
        FocusGrab grab;QSignalSpy cleared(&grab,&FocusGrab::cleared);
        QVERIFY(!grab.start({&window}));QVERIFY(!grab.active());grab.stop();QCOMPARE(cleared.count(),0);
    }
    void panelStrip() {
        const QRect area(0,0,1000,800);
        QCOMPARE(BwmSurface::withoutPanelStrip(area,QRect(0,700,640,48),Qt::BottomEdge),QRect(0,0,1000,700));
        QCOMPARE(BwmSurface::withoutPanelStrip(area,QRect(0,0,1000,40),Qt::TopEdge),QRect(0,40,1000,760));
        QCOMPARE(BwmSurface::withoutPanelStrip(area,QRect(0,0,44,800),Qt::LeftEdge),QRect(44,0,956,800));
        QCOMPARE(BwmSurface::withoutPanelStrip(area,QRect(956,0,44,800),Qt::RightEdge),QRect(0,0,956,800));
        QCOMPARE(BwmSurface::withoutPanelStrip(area,QRect(2000,0,44,800),Qt::RightEdge),area);
    }
    void nativePolicyRequests_data() {
        QTest::addColumn<int>("edge");
        for(auto edge:{Qt::TopEdge,Qt::BottomEdge,Qt::LeftEdge,Qt::RightEdge})QTest::newRow(qPrintable(QString::number(int(edge))))<<int(edge);
    }
    void explicitReservationEdgeKeepsThePanelExtent() {
        using W=LayerShellQt::Window;
        struct Example { Qt::Edge side; W::Anchor exclusive; W::Anchor leading; W::Anchor trailing; };
        const Example examples[] = {
            {Qt::LeftEdge, W::AnchorLeft, W::AnchorTop, W::AnchorBottom},
            {Qt::RightEdge, W::AnchorRight, W::AnchorTop, W::AnchorBottom},
            {Qt::TopEdge, W::AnchorTop, W::AnchorLeft, W::AnchorRight},
            {Qt::BottomEdge, W::AnchorBottom, W::AnchorLeft, W::AnchorRight},
        };
        for (const auto &[side, exclusive, leading, trailing] : examples) {
            const auto modern = BwmSurface::nativePanelAnchoring(side, 1440, 640, true);
            QCOMPARE(modern.exclusiveEdge, exclusive);
            QCOMPARE(modern.anchors, W::Anchors(exclusive) | leading);
            QVERIFY(!modern.anchors.testFlag(trailing)); // LayerShellQt sends the requested size.
            QCOMPARE(modern.margins, QMargins());

            const auto legacy = BwmSurface::nativePanelAnchoring(side, 1440, 640, false);
            QCOMPARE(legacy.anchors, modern.anchors | trailing);
            QCOMPARE(legacy.exclusiveEdge, exclusive);
            QCOMPARE(legacy.margins, trailing == W::AnchorBottom ? QMargins(0, 0, 0, 800) : QMargins(0, 0, 800, 0));
            // The compositor places the legacy zero-size (stretched) axis in
            // already usable space. A 44 px perpendicular reservation reduces
            // its first configure to 596 px and is subtracted again if Qt resizes.
            QCOMPARE(1440 - 44 - legacy.margins.bottom() - legacy.margins.right(), 596);
        }
    }
    void nativeAnchoringFollowsPanelViewPlacement() {
        // PanelView::updateLayerWindow 6.7.5: right alignment anchors the trailing
        // side with the Custom offset as margin; center anchors neither side; a full
        // length is the leading corner. The legacy path places the same rectangle.
        using W=LayerShellQt::Window;
        const BwmSurface::PanelPlacement right{Qt::AlignRight,100,2},center{Qt::AlignCenter,0,2},fill{Qt::AlignRight,100,0},fit{Qt::AlignRight,100,1};
        auto a=BwmSurface::nativePanelAnchoring(Qt::BottomEdge,1440,640,true,right);
        QCOMPARE(a.anchors,W::Anchors(W::AnchorBottom)|W::AnchorRight);QCOMPARE(a.margins,QMargins(0,0,100,0));
        a=BwmSurface::nativePanelAnchoring(Qt::LeftEdge,1440,640,true,right);
        QCOMPARE(a.anchors,W::Anchors(W::AnchorLeft)|W::AnchorBottom);QCOMPARE(a.margins,QMargins(0,0,0,100));
        a=BwmSurface::nativePanelAnchoring(Qt::BottomEdge,1440,640,true,center);
        QCOMPARE(a.anchors,W::Anchors(W::AnchorBottom));QCOMPARE(a.margins,QMargins());
        a=BwmSurface::nativePanelAnchoring(Qt::TopEdge,1440,1440,true,fill);
        // PanelView::updateLayerWindow 6.7.5: FillAvailable anchors both perpendicular sides
        // so adjacent-edge reservations constrain its stretched length without overflow.
        QCOMPARE(a.anchors,W::Anchors(W::AnchorTop)|W::AnchorLeft|W::AnchorRight);QCOMPARE(a.margins,QMargins());
        a=BwmSurface::nativePanelAnchoring(Qt::LeftEdge,900,900,true,fill);
        QCOMPARE(a.anchors,W::Anchors(W::AnchorLeft)|W::AnchorTop|W::AnchorBottom);QCOMPARE(a.margins,QMargins());
        // FitContent ignores the offset, as PanelView does.
        a=BwmSurface::nativePanelAnchoring(Qt::BottomEdge,1440,640,true,fit);QCOMPARE(a.margins,QMargins());
        a=BwmSurface::nativePanelAnchoring(Qt::BottomEdge,1440,640,false,right);
        QCOMPARE(a.margins,QMargins(700,0,100,0));
        a=BwmSurface::nativePanelAnchoring(Qt::BottomEdge,1440,640,false,center);
        QCOMPARE(a.margins,QMargins(400,0,400,0));
        QCOMPARE(BwmSurface::panelStart(right,1440,640),700);QCOMPARE(BwmSurface::panelStart(center,1440,640),400);
        QCOMPARE(BwmSurface::panelStart(fit,1440,640),800);
    }
    void adjacentEdgeLayoutAndCornerPopups() {
        QQuickWindow leftPanel;
        const QRect screen=leftPanel.screen()->geometry();
        const int topReserve=48,leftReserve=56,bottomReserve=40;
        leftPanel.resize(leftReserve,screen.height()-topReserve-bottomReserve);
        BwmSurface::configurePanel(&leftPanel,Qt::LeftEdge,0,true);
        BwmSurface::setPanelPlacement(&leftPanel,{Qt::AlignLeft,0,0});
        leftPanel.show();
        QVERIFY(BwmSurface::setPanelVisibility(&leftPanel,0,leftReserve));
        const QRect bounds(screen.x(),screen.y()+topReserve,screen.width(),screen.height()-topReserve-bottomReserve);
        const QRect avail(screen.x()+leftReserve,screen.y()+topReserve,screen.width()-leftReserve,screen.height()-topReserve-bottomReserve);
        BwmSurface::setPanelLayoutContext(&leftPanel,bounds,avail);
        QCOMPARE(leftPanel.property("bwmPanelRect").toRect(),QRect(screen.x(),screen.y()+topReserve,leftReserve,bounds.height()));
        // Widget near the top-left corner of the Left panel: popup must stay inside avail
        // (below topReserve and right of leftReserve), never overlapping either panel.
        QQuickItem topWidget(leftPanel.contentItem());
        topWidget.setPosition({4,4});topWidget.setSize({48,40});
        QQuickWindow popup;popup.resize(300,200);
        PopupAnchor anchor;anchor.setPopup(&popup);anchor.setVisualParent(&topWidget);
        const QRect topPlaced=popup.property("bwmPopupRect").toRect();
        QVERIFY2(avail.contains(topPlaced),qPrintable(QString("top corner popup %1,%2 %3x%4 escaped avail %5,%6 %7x%8")
            .arg(topPlaced.x()).arg(topPlaced.y()).arg(topPlaced.width()).arg(topPlaced.height())
            .arg(avail.x()).arg(avail.y()).arg(avail.width()).arg(avail.height())));
        QCOMPARE(topPlaced.left(),screen.x()+leftReserve);
        QCOMPARE(topPlaced.top(),screen.y()+topReserve);
        // Move widget near the bottom-left corner: popup must stay above bottomReserve.
        topWidget.setPosition({4,qreal(bounds.height()-44)});
        const QRect bottomPlaced=popup.property("bwmPopupRect").toRect();
        QVERIFY(avail.contains(bottomPlaced));
        QCOMPARE(bottomPlaced.left(),screen.x()+leftReserve);
        QCOMPARE(bottomPlaced.bottom(),avail.bottom());
    }
    void nativePolicyRequests() {
        QFETCH(int,edge);const auto side=Qt::Edge(edge);const bool vertical=side==Qt::LeftEdge || side==Qt::RightEdge;
        QQuickWindow window;window.resize(vertical?QSize(64,300):QSize(300,64));
        BwmSurface::configurePanel(&window,side,0,true);auto *role=LayerShellQt::Window::get(&window);
        QVERIFY(BwmSurface::setPanelVisibility(&window,0,40));QCOMPARE(role->exclusionZone(),-1); // Hidden.
        window.show();QTRY_COMPARE(role->exclusionZone(),40);
        using W=LayerShellQt::Window;
        const auto anchor=side==Qt::TopEdge?W::AnchorTop:side==Qt::BottomEdge?W::AnchorBottom:side==Qt::LeftEdge?W::AnchorLeft:W::AnchorRight;
        const W::Anchors perpendicular=vertical?W::Anchors(W::AnchorTop)|W::AnchorBottom:W::Anchors(W::AnchorLeft)|W::AnchorRight;
        QCOMPARE(role->anchors(),perpendicular|anchor);QCOMPARE(role->exclusiveEdge(),anchor);
        QCOMPARE(vertical?role->margins().bottom():role->margins().right(),(vertical?window.screen()->size().height():window.screen()->size().width())-300);
        QVERIFY(window.property("bwmReservationRequested").toBool());
        QVERIFY(!BwmSurface::setPanelVisibility(&window,4,40));QCOMPARE(role->exclusionZone(),40);
        QVERIFY(!BwmSurface::setPanelVisibility(&window,0,0));QCOMPARE(role->exclusionZone(),40);
        // AutoHide/DodgeWindows never reserve (PanelView::updateExclusiveZone).
        for(int mode:{1,2}){QVERIFY(BwmSurface::setPanelVisibility(&window,mode,40));QCOMPARE(role->exclusionZone(),-1);}
        QVERIFY(BwmSurface::setPanelVisibility(&window,0,40));QCOMPARE(role->exclusionZone(),40);
        window.hide();QCOMPARE(role->exclusionZone(),-1);QVERIFY(!window.property("bwmReservationRequested").toBool());
        window.show();QTRY_COMPARE(role->exclusionZone(),40);
        QVERIFY(BwmSurface::setPanelVisibility(&window,3,40));QCOMPARE(role->exclusionZone(),-1);
        QVERIFY(BwmSurface::setPanelVisibility(&window,0,48));QCOMPARE(role->exclusionZone(),48);
        if(vertical)window.resize(64,window.screen()->size().height()+1);else window.resize(window.screen()->size().width()+1,64);
        QTRY_COMPARE(role->exclusionZone(),-1);QVERIFY(!window.property("bwmSurfaceError").toString().isEmpty());
        window.resize(vertical?QSize(64,300):QSize(300,64));QTRY_COMPARE(role->exclusionZone(),48);
        QVERIFY(window.property("bwmSurfaceError").toString().isEmpty());
        QQuickWindow preview;preview.resize(300,48);BwmSurface::configurePanel(&preview,Qt::BottomEdge);
        QVERIFY(!BwmSurface::setPanelVisibility(&preview,0,40));QCOMPARE(W::get(&preview)->exclusionZone(),-1);
        for(int mode:{1,2})QVERIFY(!BwmSurface::setPanelVisibility(&preview,mode,40));
    }
};
QTEST_MAIN(SurfaceTest)
#include "test-surfaces.moc"

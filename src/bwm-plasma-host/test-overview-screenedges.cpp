// SPDX-License-Identifier: GPL-2.0-or-later
#include "expolayout.h"
#include "overviewhost.h"
#include "screenedges.h"
#include <QJsonArray>
#include <QJsonObject>
#include <QQuickItem>
#include <QTemporaryDir>
#include <QTest>
#include <QFile>

class T8OverviewScreenEdgesTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void parseKwinrcDefaults() {
        QTemporaryDir dir;
        QVERIFY(dir.isValid());
        const auto cfg = ScreenEdges::parseKwinrc(dir.path() + QStringLiteral("/kwinrc"));
        QCOMPARE(cfg.delayMs, 75);
        QCOMPARE(cfg.cooldownMs, 350);
        QCOMPARE(cfg.remainActiveOnFullscreen, false);
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::TopLeft, ScreenEdges::Action::None),
                 ScreenEdges::Action::Overview);
        QCOMPARE(cfg.actions.size(), 1);
    }

    void parseKwinrcCustomEdgesAndDisableOverview() {
        QTemporaryDir dir;
        QVERIFY(dir.isValid());
        const QString path = dir.path() + QStringLiteral("/kwinrc");
        QFile f(path);
        QVERIFY(f.open(QIODevice::WriteOnly));
        f.write(
            "[Windows]\n"
            "ElectricBorderDelay=120\n"
            "ElectricBorderCooldown=500\n"
            "[ScreenEdges]\n"
            "RemainActiveOnFullscreen=true\n"
            "[Effect-overview]\n"
            "BorderActivate=\n"
            "GridBorderActivate=1\n"
            "[Effect-windowview]\n"
            "BorderActivate=5\n"
            "BorderActivateAll=3\n"
            "[ElectricBorders]\n"
            "Bottom=ShowDesktop\n"
            "[TabBox]\n"
            "BorderActivate=6\n");
        f.close();

        const auto cfg = ScreenEdges::parseKwinrc(path);
        QCOMPARE(cfg.delayMs, 120);
        QCOMPARE(cfg.cooldownMs, 500);
        QCOMPARE(cfg.remainActiveOnFullscreen, true);
        QVERIFY(!cfg.actions.contains(ScreenEdges::Edge::TopLeft));
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::TopRight), ScreenEdges::Action::Grid);
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::BottomLeft), ScreenEdges::Action::WindowViewCurrent);
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::BottomRight), ScreenEdges::Action::WindowViewAll);
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::Bottom), ScreenEdges::Action::ShowDesktop);
        QCOMPARE(cfg.actions.value(ScreenEdges::Edge::Left), ScreenEdges::Action::TabBox);
    }

    void exteriorEdgesMultiMonitorAndFractionalScale() {
        // Real dual-monitor layout: MSI 1440p at (0,720) + LG 4K@1.5x (logical 2560x1440) at (2560,0).
        const QRect msi(0, 720, 2560, 1440);
        const QRect lg(2560, 0, 2560, 1440);
        const QList<QRect> screens = {msi, lg};

        QVERIFY(ScreenEdges::isExteriorEdge(msi, screens, ScreenEdges::Edge::TopLeft));
        QVERIFY(ScreenEdges::isExteriorEdge(msi, screens, ScreenEdges::Edge::Left));
        QVERIFY(ScreenEdges::isExteriorEdge(msi, screens, ScreenEdges::Edge::BottomLeft));
        QVERIFY(!ScreenEdges::isExteriorEdge(msi, screens, ScreenEdges::Edge::TopRight));
        QVERIFY(!ScreenEdges::isExteriorEdge(msi, screens, ScreenEdges::Edge::Right));

        QVERIFY(ScreenEdges::isExteriorEdge(lg, screens, ScreenEdges::Edge::TopLeft));
        QVERIFY(ScreenEdges::isExteriorEdge(lg, screens, ScreenEdges::Edge::TopRight));
        QVERIFY(ScreenEdges::isExteriorEdge(lg, screens, ScreenEdges::Edge::Right));
        QVERIFY(!ScreenEdges::isExteriorEdge(lg, screens, ScreenEdges::Edge::BottomLeft));
        QVERIFY(!ScreenEdges::isExteriorEdge(lg, screens, ScreenEdges::Edge::Left));
    }

    void overviewSnapshotHandlesMonitorsFractionalScaleMinimizedAndMagic() {
        const QJsonArray monitors = {
            QJsonObject{
                {"id", 0}, {"name", "DP-1"}, {"x", 0}, {"y", 720},
                {"width", 2560}, {"height", 1440}, {"scale", 1.0}, {"focused", true},
                {"activeWorkspace", QJsonObject{{"id", 1}}},
                {"specialWorkspace", QJsonObject{{"id", -98}, {"name", "special:magic"}}},
            },
            QJsonObject{
                {"id", 1}, {"name", "DP-2"}, {"x", 2560}, {"y", 0},
                {"width", 3840}, {"height", 2160}, {"scale", 1.5}, {"focused", false},
                {"activeWorkspace", QJsonObject{{"id", 2}}},
                {"specialWorkspace", QJsonObject{{"id", 0}, {"name", ""}}},
            },
        };
        const QJsonArray workspaces = {
            QJsonObject{{"id", 1}, {"name", "1"}, {"monitor", "DP-1"}, {"windows", 1}},
            QJsonObject{{"id", 2}, {"name", "2"}, {"monitor", "DP-2"}, {"windows", 1}},
        };
        const QJsonArray clients = {
            QJsonObject{
                {"address", "0x101"}, {"pid", 1001}, {"class", "kitty"}, {"title", "Terminal"},
                {"monitor", 0}, {"mapped", true}, {"hidden", false},
                {"workspace", QJsonObject{{"id", 1}, {"name", "1"}}},
                {"at", QJsonArray{100, 820}}, {"size", QJsonArray{900, 600}},
            },
            QJsonObject{
                {"address", "0x102"}, {"pid", 1002}, {"class", "firefox"}, {"title", "Browser"},
                {"monitor", 1}, {"mapped", true}, {"hidden", false},
                {"workspace", QJsonObject{{"id", 2}, {"name", "2"}}},
                {"at", QJsonArray{2660, 100}}, {"size", QJsonArray{1200, 800}},
            },
            QJsonObject{
                {"address", "0x103"}, {"pid", 1003}, {"class", "dolphin"}, {"title", "Files"},
                {"monitor", 0}, {"mapped", true}, {"hidden", false},
                {"workspace", QJsonObject{{"id", -99}, {"name", "special:minimized"}}},
                {"at", QJsonArray{50, 770}}, {"size", QJsonArray{800, 500}},
            },
            QJsonObject{
                {"address", "0x104"}, {"pid", 1004}, {"class", "org.kde.kate"}, {"title", "Notes"},
                {"monitor", 0}, {"mapped", true}, {"hidden", false},
                {"workspace", QJsonObject{{"id", -98}, {"name", "special:magic"}}},
                {"at", QJsonArray{200, 900}}, {"size", QJsonArray{700, 500}},
            },
        };

        const auto snap = OverviewHost::parseSnapshot(
            clients, workspaces, monitors, QJsonObject{{"id", 1}},
            [](const QString &addr) { return QStringLiteral("uuid-") + addr; });

        QCOMPARE(snap.activeWorkspaceId, 1);
        QCOMPARE(snap.magicOpen, true);
        QCOMPARE(snap.activeMonitorName, QStringLiteral("DP-1"));
        QCOMPARE(snap.windows.size(), 4);
        QVERIFY(snap.workspaces.size() >= 4);

        // Verify fractional-scale monitor coordinate subtraction (2660 - 2560 = 100).
        bool foundFirefox = false;
        bool foundMagic = false;
        for (const auto &v : snap.windows) {
            const auto m = v.toMap();
            if (m.value("address").toString() == "0x102") {
                foundFirefox = true;
                QCOMPARE(m.value("x").toDouble(), 100.0);
                QCOMPARE(m.value("uuid").toString(), QStringLiteral("uuid-0x102"));
            }
            if (m.value("address").toString() == "0x104") {
                foundMagic = true;
                QCOMPARE(m.value("magic").toBool(), true);
            }
        }
        QVERIFY(foundFirefox);
        QVERIFY(foundMagic);
    }

    void expoLayoutNonOverlappingPlacement() {
        struct TestExpoLayout : public ExpoLayout {
            using ExpoLayout::updatePolish;
        };
        TestExpoLayout layout;
        layout.setSize(QSizeF(1280, 720));

        QList<ExpoCell *> cells;
        QList<QQuickItem *> contents;
        const QList<QRectF> naturals = {
            QRectF(20, 20, 800, 600),
            QRectF(100, 60, 900, 500),
            QRectF(300, 120, 640, 480),
            QRectF(40, 200, 720, 540),
        };
        for (int i = 0; i < naturals.size(); ++i) {
            auto *content = new QQuickItem(&layout);
            auto *cell = new ExpoCell(&layout);
            cell->setLayout(&layout);
            cell->setContentItem(content);
            cell->setNaturalX(naturals[i].x());
            cell->setNaturalY(naturals[i].y());
            cell->setNaturalWidth(naturals[i].width());
            cell->setNaturalHeight(naturals[i].height());
            cell->setPartialActivationFactor(1.0);
            cell->componentComplete();
            cells.append(cell);
            contents.append(content);
        }

        layout.updatePolish();
        QVERIFY(layout.isReady());
        const QRectF bounds(0, 0, 1280.5, 720.5);
        for (int i = 0; i < cells.size(); ++i) {
            const QRectF ri(contents[i]->x(), contents[i]->y(), contents[i]->width(), contents[i]->height());
            QVERIFY2(ri.width() > 50 && ri.height() > 50, "Cell has invalid placed size");
            QVERIFY2(bounds.contains(ri), "Cell placed outside layout bounds");
            for (int j = i + 1; j < cells.size(); ++j) {
                const QRectF rj(contents[j]->x(), contents[j]->y(), contents[j]->width(), contents[j]->height());
                QVERIFY2(!ri.intersects(rj), "Placed cells overlap");
            }
        }
    }
};

QTEST_MAIN(T8OverviewScreenEdgesTest)
#include "test-overview-screenedges.moc"

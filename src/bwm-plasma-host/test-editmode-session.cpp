// SPDX-License-Identifier: GPL-2.0-or-later
// R5 session check: drives the original PanelConfiguration.qml of a disposable
// layer-shell panel in the running Hyprland and measures where the compositor
// placed each surface (hyprctl layers). No pointer input, no daily panel changes.
// Run through check-edit-mode-session.py, which isolates every XDG root.
#include "outputidentity.h"
#include "panelconfigview.h"
#include "panelruntime.h"
#include "panelviewhost.h"
#include "viewcorona.h"
#include <KConfig>
#include <KConfigGroup>
#include <KPackage/PackageLoader>
#include <Plasma/Containment>
#include <PlasmaQuick/Dialog>
#include <QAction>
#include <QDir>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QQmlContext>
#include <QQmlExpression>
#include <QQuickItem>
#include <QScreen>
#include <QTest>
#include <QtPlugin>

Q_IMPORT_PLUGIN(BwmWindowSystemPlugin)

namespace {
QList<QRect> layers(const QString &ns)
{
    QProcess process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(QStringLiteral("XDG_RUNTIME_DIR"), qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));
    process.setProcessEnvironment(environment);
    process.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), QStringLiteral("layers")});
    if (!process.waitForFinished(3000)) return {};
    QList<QRect> result;
    const auto monitors = QJsonDocument::fromJson(process.readAllStandardOutput()).object();
    for (const auto &monitor : monitors) {
        const auto levels = monitor.toObject().value(QStringLiteral("levels")).toObject();
        for (const auto &level : levels)
            for (const auto &layer : level.toArray()) {
                const auto o = layer.toObject();
                if (o.value(QStringLiteral("namespace")).toString() == ns)
                    result.append(QRect(o.value(QStringLiteral("x")).toInt(), o.value(QStringLiteral("y")).toInt(),
                                        o.value(QStringLiteral("w")).toInt(), o.value(QStringLiteral("h")).toInt()));
            }
    }
    return result;
}
QJsonObject rect(const QRect &r) { return {{"x", r.x()}, {"y", r.y()}, {"w", r.width()}, {"h", r.height()}}; }
PanelConfigView *openDialog()
{
    for (auto *window : QGuiApplication::allWindows())
        if (auto *dialog = qobject_cast<PanelConfigView *>(window))
            if (dialog->isVisible()) return dialog;
    return nullptr;
}
}

class EditModeSessionTest : public QObject
{
    Q_OBJECT
    QJsonArray m_steps;
    void record(const QString &name, const QRect &expected, const QRect &observed)
    {
        m_steps.append(QJsonObject{{"step", name}, {"expected", rect(expected)}, {"observed", rect(observed)}, {"passed", expected == observed}});
    }
    // Waits until hyprctl reports the expected rectangle (or times out and records it).
    void expectPanel(const QString &name, const std::function<QRect()> &expected)
    {
        QRect observed;
        const bool matched = QTest::qWaitFor([&] {
            const auto all = layers(QStringLiteral("bwm-r4-preview"));
            observed = all.size() == 1 ? all.first() : QRect();
            return observed == expected();
        }, 4000);
        record(name, expected(), observed);
        QVERIFY2(matched, qPrintable(QStringLiteral("%1: expected %2,%3 %4x%5, Hyprland %6,%7 %8x%9").arg(name)
            .arg(expected().x()).arg(expected().y()).arg(expected().width()).arg(expected().height())
            .arg(observed.x()).arg(observed.y()).arg(observed.width()).arg(observed.height())));
    }

private Q_SLOTS:
    void originalPanelSettingsInHyprland()
    {
        const auto output = qEnvironmentVariable("BWM_R5_OUTPUT");
        QVERIFY2(!output.isEmpty(), "BWM_R5_OUTPUT is required");
        QCOMPARE(QGuiApplication::platformName(), QStringLiteral("wayland"));
        auto *screen = BwmOutput::resolveScreen(output);
        QVERIFY2(screen, "The output description did not resolve to one screen");
        const QRect S = screen->geometry();
        const int gap = 64; // R4 preview gap above the edge, so it never covers the daily panel.

        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(QStringLiteral("bwm-r5-session-appletsrc"));
        auto *c = corona.createContainment(QStringLiteral("org.kde.panel"));
        QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);
        c->setFormFactor(Plasma::Types::Horizontal);
        QVERIFY(c->createApplet(QStringLiteral("org.kde.plasma.analogclock")));
        const uint id = c->id();
        PanelRuntime runtime(&corona, QStringLiteral("plasmashellrc"), true);
        runtime.setOutputMovesAllowed(true);
        QVERIFY2(runtime.setAssignments({{id, output}}), qPrintable(runtime.error()));
        QVERIFY2(runtime.setSkin(QStringLiteral("plasma")), qPrintable(runtime.error()));
        QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        QPointer<PanelViewHost> view = runtime.view(id);
        expectPanel(QStringLiteral("fill-width"), [&] { return QRect(S.x(), S.bottom() + 1 - gap - view->height(), S.width(), view->height()); });

        c->internalAction(QStringLiteral("configure"))->trigger();
        QPointer<PanelConfigView> dialog;
        QTRY_VERIFY((dialog = openDialog()));
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 1);
        auto *root = dialog->mainItem();
        QStringList errors;
        const auto run = [&](const QString &code, QWindow *target = nullptr) {
            QQmlContext context(qmlContext(dialog->mainItem()));
            context.setContextProperty(QStringLiteral("bwmTarget"), QVariant::fromValue(target));
            QQmlExpression e(&context, dialog->mainItem(), code);
            e.evaluate();
            if (e.hasError()) errors.append(e.error().toString());
        };
        Q_UNUSED(root);

        // Length: Custom (index 2), then the three alignments.
        run(QStringLiteral("widthBox.activated(2)"));
        QTRY_COMPARE(view->lengthMode(), 2);
        QTRY_VERIFY(view->width() < S.width());
        expectPanel(QStringLiteral("custom-left"), [&] { return QRect(S.x(), S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        run(QStringLiteral("alignmentBox.activated(2)"));
        QTRY_COMPARE(view->alignment(), int(Qt::AlignRight));
        expectPanel(QStringLiteral("custom-right"), [&] { return QRect(S.right() + 1 - view->width(), S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        run(QStringLiteral("alignmentBox.activated(1)"));
        QTRY_COMPARE(view->alignment(), int(Qt::AlignCenter));
        expectPanel(QStringLiteral("custom-center"), [&] { return QRect(S.x() + (S.width() - view->width()) / 2, S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });

        // Floating (index 2): the original frame floats and the window grows by its margins.
        const int before = view->height();
        run(QStringLiteral("floatingBox.activated(2)"));
        QTRY_VERIFY(view->floating());
        QTRY_COMPARE(view->rootObject()->property("floatingness").toDouble(), 1.0);
        QTRY_VERIFY(view->height() > before);
        expectPanel(QStringLiteral("floating-center"), [&] { return QRect(S.x() + (S.width() - view->width()) / 2, S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });

        // Set Position…: indicators are overlay layers on every screen.
        run(QStringLiteral("setPositionButton.checked = true"));
        const int expectedIndicators = 4 * QGuiApplication::screens().size() - 1;
        QTRY_COMPARE_WITH_TIMEOUT(layers(QStringLiteral("bwm-r5-edit-indicator")).size(), expectedIndicators, 5000);
        int inside = 0;
        for (const auto &r : layers(QStringLiteral("bwm-r5-edit-indicator")))
            for (auto *s : QGuiApplication::screens())
                if (s->geometry().contains(r)) { ++inside; break; }
        m_steps.append(QJsonObject{{"step", "indicators"}, {"count", expectedIndicators}, {"insideAScreen", inside}, {"passed", inside == expectedIndicators}});
        QCOMPARE(inside, expectedIndicators);

        // Edges on the same output: the view and its settings stay, as in PanelView.
        struct Edge { int location; const char *name; };
        for (const Edge edge : {Edge{Plasma::Types::TopEdge, "top"}, Edge{Plasma::Types::LeftEdge, "left"},
                                Edge{Plasma::Types::RightEdge, "right"}, Edge{Plasma::Types::BottomEdge, "bottom"}}) {
            run(QStringLiteral("setPositionButton.checked = true; setPositionButton.moveTo(%1)").arg(edge.location));
            QTRY_COMPARE(int(c->location()), edge.location);
            QVERIFY2(dialog && dialog->isVisible(), "The panel settings must stay open");
            QCOMPARE(runtime.view(id), view.data());
            const bool vertical = edge.location == Plasma::Types::LeftEdge || edge.location == Plasma::Types::RightEdge;
            QTRY_COMPARE(c->formFactor(), vertical ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
            QTRY_VERIFY(vertical ? view->height() < S.height() : view->width() < S.width());
            expectPanel(QStringLiteral("edge-") + QLatin1String(edge.name), [&] {
                const int w = view->width(), h = view->height();
                switch (edge.location) {
                case Plasma::Types::TopEdge: return QRect(S.x() + (S.width() - w) / 2, S.y() + gap, w, h);
                case Plasma::Types::LeftEdge: return QRect(S.x() + gap, S.y() + (S.height() - h) / 2, w, h);
                case Plasma::Types::RightEdge: return QRect(S.right() + 1 - gap - w, S.y() + (S.height() - h) / 2, w, h);
                default: return QRect(S.x() + (S.width() - w) / 2, S.bottom() + 1 - gap - h, w, h);
                }
            });
        }

        // Another output (when there is one): the runtime moves the panel and reopens its settings.
        QScreen *other = nullptr;
        for (auto *s : QGuiApplication::screens()) if (s != screen) other = s;
        if (other) {
            run(QStringLiteral("setPositionButton.checked = true"));
            QWindow *indicator = nullptr;
            QTRY_VERIFY_WITH_TIMEOUT([&] {
                for (auto *w : QGuiApplication::allWindows())
                    if (qobject_cast<PlasmaQuick::Dialog *>(w) && w->isVisible() && w->property("bwmIndicatorScreen").value<QScreen *>() == other) {indicator = w; return true;}
                return false;
            }(), 5000);
            run(QStringLiteral("setPositionButton.moveTo(%1, bwmTarget)").arg(int(Plasma::Types::BottomEdge)), indicator);
            QTRY_VERIFY_WITH_TIMEOUT(runtime.view(id) && runtime.view(id) != view.data() && runtime.view(id)->screen() == other, 5000);
            view = runtime.view(id);
            QTRY_VERIFY((dialog = openDialog()));
            const QRect O = other->geometry();
            expectPanel(QStringLiteral("other-output"), [&] { return QRect(O.x() + (O.width() - view->width()) / 2, O.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        }

        QVERIFY2(errors.isEmpty(), qPrintable(errors.join(u'\n')));
        dialog->requestActivate();
        QTRY_VERIFY(dialog->isActive());
        QTest::keyClick(dialog, Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());
        {
            KConfig config(QStringLiteral("plasmashellrc"), KConfig::SimpleConfig);
            const auto g = KConfigGroup(&config, QStringLiteral("PlasmaViews")).group(QStringLiteral("Panel %1").arg(id));
            m_steps.append(QJsonObject{{"step", "stored"}, {"alignment", g.readEntry("alignment", 0)}, {"panelLengthMode", g.readEntry("panelLengthMode", -1)},
                                       {"floating", g.readEntry("floating", -1)}, {"location", int(c->location())}});
            QCOMPARE(g.readEntry("floating", 0), 1);
            QCOMPARE(g.readEntry("alignment", 0), int(Qt::AlignCenter));
        }
        runtime.setSkin(QStringLiteral("default"));
        QTRY_VERIFY(layers(QStringLiteral("bwm-r4-preview")).isEmpty());
        puts(QJsonDocument(QJsonObject{{"steps", m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
};

QTEST_MAIN(EditModeSessionTest)
#include "test-editmode-session.moc"

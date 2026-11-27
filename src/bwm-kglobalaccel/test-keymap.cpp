// SPDX-License-Identifier: GPL-2.0-or-later
#include "keymap.h"
#include <QKeySequence>
#include <QTest>

using namespace BwmKeymap;

class KeymapTest : public QObject
{
    Q_OBJECT
private Q_SLOTS:
    void qtToHyprland_data()
    {
        QTest::addColumn<QString>("sequence");
        QTest::addColumn<QString>("spec");
        QTest::newRow("letter") << "Meta+Shift+S" << "SUPER + SHIFT + s";
        QTest::newRow("print") << "Print" << "Print";
        QTest::newRow("ctrl-alt-t") << "Ctrl+Alt+T" << "CTRL + ALT + t";
        QTest::newRow("function") << "Alt+F1" << "ALT + F1";
        QTest::newRow("space") << "Alt+Space" << "ALT + space";
        QTest::newRow("equal") << "Meta+=" << "SUPER + equal";
        QTest::newRow("period") << "Meta+." << "SUPER + period";
        QTest::newRow("media") << "Volume Up" << "XF86AudioRaiseVolume";
        QTest::newRow("arrow") << "Meta+Left" << "SUPER + Left";
        QTest::newRow("backtab") << "Backtab" << "SHIFT + Tab";
    }
    void qtToHyprland()
    {
        QFETCH(QString, sequence);
        QFETCH(QString, spec);
        const QKeySequence seq = QKeySequence::fromString(sequence, QKeySequence::PortableText);
        QVERIFY(!seq.isEmpty());
        const auto key = fromQt(seq[0].toCombined());
        QVERIFY(key.has_value());
        QCOMPARE(BwmKeymap::spec(*key), spec);
    }
    void modifierOnlyAndUnknownAreSkipped()
    {
        QVERIFY(!fromQt(int(Qt::Key_Meta) | int(Qt::MetaModifier)).has_value());
        QVERIFY(!fromQt(Qt::Key_Shift).has_value());
        QVERIFY(!fromQt(0).has_value());
    }
    void hyprlandRoundTrip_data()
    {
        QTest::addColumn<int>("modmask");
        QTest::addColumn<QString>("name");
        QTest::addColumn<QString>("sequence");
        QTest::newRow("upper-name") << int(ModSuper) << "A" << "Meta+A";
        QTest::newRow("return") << int(ModSuper) << "RETURN" << "Meta+Return";
        QTest::newRow("space") << int(ModAlt) << "SPACE" << "Alt+Space";
        QTest::newRow("print") << 0 << "Print" << "Print";
        QTest::newRow("shift-s") << int(ModSuper | ModShift) << "S" << "Meta+Shift+S";
        QTest::newRow("volume") << 0 << "XF86AudioRaiseVolume" << "Volume Up";
        QTest::newRow("grave") << int(ModAlt) << "grave" << "Alt+`";
    }
    void hyprlandRoundTrip()
    {
        QFETCH(int, modmask);
        QFETCH(QString, name);
        QFETCH(QString, sequence);
        const auto key = fromHyprland(quint32(modmask), name);
        QVERIFY(key.has_value());
        const int qt = toQt(*key);
        QCOMPARE(QKeySequence(qt).toString(QKeySequence::PortableText), sequence);
        // Hyprland → Qt → Hyprland gives back the same bind.
        QCOMPARE(fromQt(qt), key);
    }
    void unknownHyprlandName()
    {
        QVERIFY(!fromHyprland(0, QStringLiteral("NotAKeySym")).has_value());
    }
};
QTEST_MAIN(KeymapTest)
#include "test-keymap.moc"

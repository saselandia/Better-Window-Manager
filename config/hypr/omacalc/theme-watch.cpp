// BWM regression checks for the Omacalc palette-path adapter (QtTest).
#include <QtTest>
#include <QDir>
#include <QFile>
#include <QSaveFile>
#include <QSettings>
#include <QTemporaryDir>
#include "backend.h"

class ThemeWatchTest : public QObject {
    Q_OBJECT
    QTemporaryDir temporary;
    QByteArray previousOverride;

    void write(const QString &path, const QByteArray &background, bool atomic = true) {
        const QByteArray colors = "background = \"" + background
            + "\"\nforeground = \"#eeeeee\"\naccent = \"#aabbcc\"\nselection = \"#334455\"\n";
        if (atomic) {
            QSaveFile file(path);
            QVERIFY(file.open(QIODevice::WriteOnly));
            QCOMPARE(file.write(colors), qint64(colors.size()));
            QVERIFY(file.commit());
        } else {
            QFile file(path);
            QVERIFY(file.open(QIODevice::WriteOnly | QIODevice::Truncate));
            QCOMPARE(file.write(colors), qint64(colors.size()));
        }
    }

private slots:
    void initTestCase() {
        QVERIFY(temporary.isValid());
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope, temporary.path());
    }
    void init() { previousOverride = qgetenv("OMACALC_THEME_FILE"); }
    void cleanup() {
        if (previousOverride.isNull()) qunsetenv("OMACALC_THEME_FILE");
        else qputenv("OMACALC_THEME_FILE", previousOverride);
    }
    void overrideUsesTheNativeOmarchyColors() {
        const QString path = temporary.filePath("override.toml");
        write(path, "#fafafa");
        qputenv("OMACALC_THEME_FILE", path.toUtf8());
        Backend calculator;
        QCOMPARE(calculator.themeBackground(), QStringLiteral("#fafafa"));
        QCOMPARE(calculator.themeForeground(), QStringLiteral("#eeeeee"));
        QCOMPARE(calculator.themeAccent(), QStringLiteral("#aabbcc"));
        QCOMPARE(calculator.themeSelection(), QStringLiteral("#334455"));
        QVERIFY(!calculator.darkMode());
    }
    void repeatedAtomicChangesPreserveTheCalculation() {
        const QString path = temporary.filePath("atomic.toml");
        write(path, "#fafafa");
        qputenv("OMACALC_THEME_FILE", path.toUtf8());
        Backend calculator;
        for (const QString &key : {"2", "+", "3", "="}) calculator.pressKey(key);
        QCOMPARE(calculator.display(), QStringLiteral("5"));
        write(path, "#112233");
        QTRY_COMPARE(calculator.themeBackground(), QStringLiteral("#112233"));
        QVERIFY(calculator.darkMode());
        write(path, "#334455");
        QTRY_COMPARE(calculator.themeBackground(), QStringLiteral("#334455"));
        QCOMPARE(calculator.display(), QStringLiteral("5"));
        QCOMPARE(calculator.expression(), QStringLiteral("2 + 3"));
    }
    void inPlaceWritesRetintTheOpenCalculator() {
        const QString path = temporary.filePath("in-place.toml");
        write(path, "#112233");
        qputenv("OMACALC_THEME_FILE", path.toUtf8());
        Backend calculator;
        write(path, "#fafafa", false);
        QTRY_COMPARE(calculator.themeBackground(), QStringLiteral("#fafafa"));
        QVERIFY(!calculator.darkMode());
    }
    void firstPaletteCanAppearAfterLaunch() {
        const QString directory = temporary.filePath("new/palette");
        const QString path = directory + "/colors.toml";
        qputenv("OMACALC_THEME_FILE", path.toUtf8());
        Backend calculator;
        QVERIFY(QDir().mkpath(directory));
        write(path, "#556677");
        QTRY_COMPARE(calculator.themeBackground(), QStringLiteral("#556677"));
    }
};

QTEST_MAIN(ThemeWatchTest)
#include "theme-watch.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
// KDE-style client for check-daemon.py: registers global shortcuts through the original
// KGlobalAccel framework and reports activations/changes on stdout. Commands on stdin.
#include <KGlobalAccel>
#include <KGlobalShortcutInfo>
#include <QAction>
#include <QDBusInterface>
#include <QDBusMetaType>
#include <QDBusReply>
#include <QGuiApplication>
#include <QSocketNotifier>
#include <cstdio>
#include <unistd.h>

static void out(const QString &line)
{
    printf("%s\n", qPrintable(line));
    fflush(stdout);
}

static QString keys(QAction *action)
{
    QStringList list;
    for (const QKeySequence &k : KGlobalAccel::self()->shortcut(action))
        list << k.toString(QKeySequence::PortableText);
    return list.join(u',');
}

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("bwmtestclient"));
    app.setApplicationDisplayName(QStringLiteral("BWM test client"));
    qDBusRegisterMetaType<QKeySequence>();
    qDBusRegisterMetaType<QList<QKeySequence>>();

    QAction free(nullptr), taken(nullptr);
    free.setObjectName(QStringLiteral("free-action"));
    free.setText(QStringLiteral("Free action"));
    taken.setObjectName(QStringLiteral("taken-action"));
    taken.setText(QStringLiteral("Taken action"));
    QObject::connect(&free, &QAction::triggered, [] { out(QStringLiteral("triggered free")); });
    QObject::connect(&taken, &QAction::triggered, [] { out(QStringLiteral("triggered taken")); });
    QObject::connect(KGlobalAccel::self(), &KGlobalAccel::globalShortcutChanged, [&](QAction *action, const QKeySequence &) {
        out(QStringLiteral("changed %1=%2").arg(action == &free ? QStringLiteral("free") : QStringLiteral("taken"), keys(action)));
    });
    KGlobalAccel::setGlobalShortcut(&free, QKeySequence(QStringLiteral("Meta+Shift+K")));
    KGlobalAccel::setGlobalShortcut(&taken, QKeySequence(QStringLiteral("Alt+F1")));
    out(QStringLiteral("assigned free=%1 taken=%2").arg(keys(&free), keys(&taken)));

    QSocketNotifier input(STDIN_FILENO, QSocketNotifier::Read);
    QObject::connect(&input, &QSocketNotifier::activated, [&] {
        char buffer[256];
        const ssize_t n = read(STDIN_FILENO, buffer, sizeof buffer - 1);
        if (n <= 0) {
            app.quit();
            return;
        }
        buffer[n] = 0;
        const QString command = QString::fromUtf8(buffer).trimmed();
        if (command == QLatin1String("query")) {
            out(QStringLiteral("keys free=%1 taken=%2").arg(keys(&free), keys(&taken)));
            const QList<QKeySequence> bwm = KGlobalAccel::self()->globalShortcut(QStringLiteral("bwm"), QStringLiteral("ALT + F1"));
            QStringList list;
            for (const QKeySequence &k : bwm)
                list << k.toString(QKeySequence::PortableText);
            out(QStringLiteral("bwm=%1").arg(list.join(u',')));
        } else if (command == QLatin1String("edit-bwm")) {
            // What kcm_keys does when the user reassigns a key of another component.
            QDBusInterface daemon(QStringLiteral("org.kde.kglobalaccel"), QStringLiteral("/kglobalaccel"), QStringLiteral("org.kde.KGlobalAccel"));
            const QStringList action{QStringLiteral("bwm"), QStringLiteral("ALT + F1"), QStringLiteral("BWM"), QString()};
            QDBusReply<void> reply = daemon.call(QStringLiteral("setForeignShortcutKeys"), action,
                                                 QVariant::fromValue(QList<QKeySequence>{QKeySequence(QStringLiteral("Meta+J"))}));
            out(reply.isValid() ? QStringLiteral("edited") : QStringLiteral("edit-failed ") + reply.error().message());
        }
    });
    return app.exec();
}

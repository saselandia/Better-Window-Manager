// SPDX-License-Identifier: GPL-2.0-or-later
// Runs inside a disposable nested Hyprland + private D-Bus session via check-notifications-session.py.
#include "notificationhost.h"
#include "panelviewhost.h"
#include "surfaces.h"
#include "viewcorona.h"

#include <KPackage/PackageLoader>
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <notificationmanager/server.h>

#include <QApplication>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QScreen>
#include <QSocketNotifier>
#include <QTimer>

#include <csignal>
#include <cstring>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

namespace {
int g_sigFd[2]{-1, -1};
void onSignal(int)
{
    char b = 1;
    const ssize_t ignored = ::write(g_sigFd[0], &b, 1);
    (void)ignored;
}
} // namespace

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    app.setQuitOnLastWindowClosed(false);

    if (::socketpair(AF_UNIX, SOCK_STREAM, 0, g_sigFd) == 0) {
        std::signal(SIGTERM, onSignal);
        std::signal(SIGINT, onSignal);
        auto *sn = new QSocketNotifier(g_sigFd[1], QSocketNotifier::Read, &app);
        QObject::connect(sn, &QSocketNotifier::activated, &app, [&app, sn] {
            sn->setEnabled(false);
            char b = 0;
            const ssize_t ignored = ::read(g_sigFd[1], &b, 1);
            (void)ignored;
            app.quit();
        });
    }

    const QString runtimeDir = qEnvironmentVariable("XDG_RUNTIME_DIR");
    if (runtimeDir.isEmpty()) {
        fprintf(stderr, "XDG_RUNTIME_DIR is required\n");
        return 2;
    }

    QScreen *screen = QGuiApplication::primaryScreen();
    if (!screen) {
        fprintf(stderr, "No QScreen available\n");
        return 3;
    }

    NotificationHost notificationHost(runtimeDir + QStringLiteral("/bwm-plasma-dnd"));
    notificationHost.start();

    ViewCorona corona;
    auto shell = KPackage::PackageLoader::self()->loadPackage(
        QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR));
    if (!shell.isValid()) {
        fprintf(stderr, "Invalid Plasma/Shell package\n");
        return 4;
    }
    corona.setKPackage(shell);

    auto *panel = corona.createContainment(QStringLiteral("org.kde.panel"));
    if (!panel) {
        fprintf(stderr, "Could not create panel containment\n");
        return 5;
    }
    panel->setFormFactor(Plasma::Types::Horizontal);
    panel->setLocation(Plasma::Types::BottomEdge);
    panel->createApplet(QStringLiteral("org.kde.plasma.notifications"));

    PanelViewHost::registerTypes();
    BwmSurface::registerTypes();
    PanelViewHost view(&corona);
    view.setScreen(screen);
    BwmSurface::configurePanel(&view, Qt::BottomEdge, 0, true);
    corona.bind(panel, &view);
    if (!view.load(panel)) {
        fprintf(stderr, "PanelViewHost load failed: %s\n", qPrintable(view.error()));
        return 6;
    }
    view.show();

    const QString sockPath = runtimeDir + QStringLiteral("/bwm-plasma-host.sock");
    int ctlFd = ::socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    QSocketNotifier *ctlNotifier = nullptr;
    if (ctlFd >= 0) {
        const QByteArray rawPath = QFile::encodeName(sockPath);
        sockaddr_un addr{};
        addr.sun_family = AF_UNIX;
        if (rawPath.size() < int(sizeof(addr.sun_path))) {
            ::unlink(rawPath.constData());
            std::memcpy(addr.sun_path, rawPath.constData(), size_t(rawPath.size()) + 1);
            if (::bind(ctlFd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) == 0 && ::listen(ctlFd, 8) == 0) {
                ::chmod(rawPath.constData(), 0600);
                ctlNotifier = new QSocketNotifier(ctlFd, QSocketNotifier::Read, &app);
                QObject::connect(ctlNotifier, &QSocketNotifier::activated, &app, [ctlFd, &notificationHost] {
                    const int client = ::accept4(ctlFd, nullptr, nullptr, SOCK_CLOEXEC);
                    if (client < 0) return;
                    char buf[256]{};
                    const ssize_t n = ::read(client, buf, sizeof(buf) - 1);
                    QByteArray reply("err\n");
                    if (n > 0) {
                        const QString line = QString::fromUtf8(buf, int(n)).trimmed();
                        if (line == QLatin1String("dnd-status")) {
                            reply = notificationHost.isInhibited() ? "true\n" : "false\n";
                        } else if (line == QLatin1String("dnd-toggle")) {
                            notificationHost.toggleDoNotDisturb();
                            reply = notificationHost.isInhibited() ? "true\n" : "false\n";
                        } else if (line == QLatin1String("dnd-set true")) {
                            notificationHost.setDoNotDisturb(true);
                            reply = notificationHost.isInhibited() ? "true\n" : "false\n";
                        } else if (line == QLatin1String("dnd-set false")) {
                            notificationHost.setDoNotDisturb(false);
                            reply = notificationHost.isInhibited() ? "true\n" : "false\n";
                        } else if (line == QLatin1String("notifications-status")) {
                            reply = QJsonDocument(notificationHost.status()).toJson(QJsonDocument::Compact) + "\n";
                        }
                    }
                    const ssize_t ignored = ::write(client, reply.constData(), size_t(reply.size()));
                    (void)ignored;
                    ::close(client);
                });
            }
        }
    }

    const QString readyPath = runtimeDir + QStringLiteral("/bwm-plasma-host.ready");
    if (QFile f(readyPath); f.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
        f.write(QByteArray::number(::getpid()) + "\n");
        f.close();
    }

    const int rc = app.exec();
    notificationHost.stop();
    delete ctlNotifier;
    if (ctlFd >= 0) ::close(ctlFd);
    QFile::remove(sockPath);
    QFile::remove(readyPath);
    view.hide();
    corona.unbind(panel);
    return rc;
}

// SPDX-License-Identifier: GPL-2.0-or-later
// bwm-kglobalaccel: KDE global shortcuts service (org.kde.kglobalaccel) for Breeze on
// Hyprland. Embeds the original kglobalacceld 6.7.5 library, like KWin does on Wayland,
// with the "bwm" platform backend (platform.cpp). See README.md.
#include "controller.h"
#include "platform.h"
#include <KGlobalAccelD/kglobalacceld.h>
#include <QGuiApplication>
#include <QJsonDocument>
#include <QSocketNotifier>
#include <QtPlugin>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

Q_IMPORT_PLUGIN(BwmPlatform)

// Client mode, run by our Hyprland binds and by kde-shortcuts.py: no Qt application.
static int sendCommand(const char *command, bool printReply)
{
    const char *custom = getenv("BWM_KGLOBALACCEL_SOCKET");
    const char *runtime = getenv("XDG_RUNTIME_DIR");
    char path[sizeof(sockaddr_un::sun_path)];
    if (custom && *custom)
        snprintf(path, sizeof path, "%s", custom);
    else
        snprintf(path, sizeof path, "%s/bwm-kglobalaccel.sock", runtime && *runtime ? runtime : "/tmp");
    const int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    sockaddr_un address{};
    address.sun_family = AF_UNIX;
    strncpy(address.sun_path, path, sizeof address.sun_path - 1);
    if (fd < 0 || connect(fd, reinterpret_cast<sockaddr *>(&address), sizeof address) != 0) {
        if (fd >= 0)
            close(fd);
        return 2;
    }
    timeval timeout{2, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
    std::string line = std::string(command) + "\n";
    if (write(fd, line.data(), line.size()) != ssize_t(line.size())) {
        close(fd);
        return 2;
    }
    std::string reply;
    char buffer[4096];
    while (reply.find('\n') == std::string::npos) {
        const ssize_t n = read(fd, buffer, sizeof buffer);
        if (n <= 0)
            break;
        reply.append(buffer, size_t(n));
    }
    close(fd);
    if (printReply)
        fputs(reply.c_str(), stdout);
    return reply.rfind("ok", 0) == 0 || reply.rfind("{", 0) == 0 ? 0 : 1;
}

static int s_signalPipe[2] = {-1, -1};
static void onSignal(int)
{
    const char byte = 1;
    (void)!write(s_signalPipe[1], &byte, 1);
}

int main(int argc, char **argv)
{
    if (argc == 4 && strcmp(argv[1], "--trigger") == 0) {
        const std::string command = std::string(argv[2]) + " " + argv[3];
        return sendCommand(command.c_str(), false);
    }
    if (argc == 2 && strcmp(argv[1], "--status") == 0)
        return sendCommand("status", true);
    if (argc == 2 && strcmp(argv[1], "--sync") == 0)
        return sendCommand("sync", true);

    qputenv("KGLOBALACCELD_PLATFORM", "bwm");
    QCoreApplication::setAttribute(Qt::AA_DisableSessionManager);
    QGuiApplication::setDesktopSettingsAware(false);
    QGuiApplication::setQuitLockEnabled(false);
    QGuiApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("kglobalaccel"));
    app.setQuitOnLastWindowClosed(false);

    if (socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, s_signalPipe) != 0)
        return 1;
    std::signal(SIGTERM, onSignal);
    std::signal(SIGINT, onSignal);

    KGlobalAccelD daemon;
    if (!daemon.init()) {
        fprintf(stderr, "bwm-kglobalaccel: org.kde.kglobalaccel is already owned or the bus is unavailable\n");
        return 1;
    }
    BwmPlatform *platform = BwmPlatform::instance();
    if (!platform) {
        fprintf(stderr, "bwm-kglobalaccel: the bwm platform backend was not loaded\n");
        return 1;
    }
    Controller controller(&daemon, platform);
    if (!controller.listen())
        return 1;
    QSocketNotifier notifier(s_signalPipe[0], QSocketNotifier::Read);
    QObject::connect(&notifier, &QSocketNotifier::activated, &app, [&] {
        notifier.setEnabled(false);
        controller.shutdown();
        app.quit();
    });
    return app.exec();
}

// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
//
// bwm-decorator [--socket RUTA]
//
// Dibuja las decoraciones reales de KDE (KDecoration3: Breeze, Aurorae y las de terceros) para el
// plugin breezebars de Hyprland. Sin ventanas propias: plataforma Qt «offscreen». Una instancia por
// socket (candado RUTA.lock); el supervisor la relanza si muere (skins/plasma/scripts/decorator.py).
#include "server.h"

#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QStandardPaths>

#include <cstdio>
#include <fcntl.h>
#include <sys/file.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (qEnvironmentVariableIsEmpty("QT_QPA_PLATFORM"))
        qputenv("QT_QPA_PLATFORM", "offscreen");
    QGuiApplication app(argc, argv);
    QGuiApplication::setApplicationName(QStringLiteral("bwm-decorator"));
    QGuiApplication::setDesktopFileName(QStringLiteral("bwm-decorator"));

    QString socketPath;
    const QStringList args = app.arguments();
    for (int i = 1; i < args.size(); ++i) {
        if (args[i] == QLatin1String("--socket") && i + 1 < args.size())
            socketPath = args[++i];
        else if (args[i] == QLatin1String("--help") || args[i] == QLatin1String("-h")) {
            std::puts("bwm-decorator [--socket RUTA]  (por defecto $XDG_RUNTIME_DIR/bwm-decorator.sock)");
            return 0;
        }
    }
    if (socketPath.isEmpty()) {
        QString runtime = QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation);
        if (runtime.isEmpty())
            runtime = QDir::tempPath();
        socketPath = runtime + QStringLiteral("/bwm-decorator.sock");
    }

    // Una sola instancia por socket
    const QByteArray lockPath = QFile::encodeName(socketPath + QStringLiteral(".lock"));
    const int lockFd = ::open(lockPath.constData(), O_RDWR | O_CREAT | O_CLOEXEC, 0600);
    if (lockFd < 0 || ::flock(lockFd, LOCK_EX | LOCK_NB) != 0) {
        std::fprintf(stderr, "bwm-decorator: ya hay otra instancia en %s\n", qPrintable(socketPath));
        return 3;
    }

    BwmDeco::Server server(socketPath);
    if (!server.listen()) {
        std::fprintf(stderr, "bwm-decorator: no se puede escuchar en %s\n", qPrintable(socketPath));
        return 2;
    }
    std::fprintf(stderr, "bwm-decorator: %s (plugin %s, tema %s)\n", qPrintable(socketPath),
                 qPrintable(server.bridge()->plugin()), qPrintable(server.bridge()->theme()));
    return app.exec();
}

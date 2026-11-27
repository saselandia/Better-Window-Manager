// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
#include <QString>
// Headless "Get New Widgets" cycle on the native KNewStuff provider (plasmoids.knsrc):
// the same provider, Entry and Transaction objects that KNSWidgets::Dialog drives, without
// a dialog. Every question KNewStuff asks is answered with Cancel/No (fail closed).
// Installs into the caller's XDG_DATA_HOME; main.cpp only allows temporary roots.
namespace BwmKns {
QJsonObject search(const QString &term, int page, int timeoutMs=30000, const QString &provider="plasmoids");
QJsonObject install(const QString &uniqueId, int timeoutMs=120000, const QString &provider="plasmoids");
QJsonObject uninstall(const QString &uniqueId, int timeoutMs=60000, const QString &provider="plasmoids");
QJsonObject metadata(const QString &uniqueId, int timeoutMs=30000, const QString &provider="plasmoids");
}

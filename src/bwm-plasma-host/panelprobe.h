// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
#include <QString>
namespace BwmMigration {
QJsonObject probePanel(const QString &directory, const QString &shellPath, bool nativeFrame=false);
}

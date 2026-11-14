// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
namespace BwmMigration {
QJsonObject stage(const QString &proposalPath);
QJsonObject verify(const QString &directory);
}

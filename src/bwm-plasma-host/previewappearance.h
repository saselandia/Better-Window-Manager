// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
#include <QString>

// Copy an allowlist of resolved native appearance settings into fresh temporary
// XDG files, before QApplication/native platform theme caches are constructed.
bool stagePreviewAppearance(const QString &sourceConfig, QJsonObject *report, QString *error);

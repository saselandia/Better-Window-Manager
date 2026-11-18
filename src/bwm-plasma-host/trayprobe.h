// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
#include <QVariant>

bool nativeTrayPropertiesLoaded(const QVariant &status, const QVariant &category);
QJsonObject probeNativeTray(int expectedRows, bool checkProperties);

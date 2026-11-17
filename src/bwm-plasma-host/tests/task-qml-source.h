// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QCryptographicHash>
#include <QFile>
#include <QQmlContext>
#include <QQmlEngine>
#include <QVariantMap>

// Test-only provenance check shared with the offscreen original-menu regression.
// A QQmlContext baseUrl may be a directory or the declaring component's URL;
// it is not an object's source location. Resolve the resource as QML does and
// verify the reviewed original, while callers identify the live Task delegate
// by its interface/ownership in the installed KDE widget.
inline QVariantMap taskQmlSource(QObject *delegate){
    auto *context=QQmlEngine::contextForObject(delegate);
    const auto url=context?context->resolvedUrl(QUrl(QStringLiteral("Task.qml"))):QUrl();
    QFile file(url.scheme()=="qrc"?":"+url.path():url.toLocalFile());
    const auto hash=file.open(QIODevice::ReadOnly)?QCryptographicHash::hash(file.readAll(),QCryptographicHash::Sha256).toHex():QByteArray();
    return {{"baseUrl",context?context->baseUrl().toString():QString()},
        {"resolvedUrl",url.toString()},{"sha256",QString::fromLatin1(hash)},
        {"reviewed",hash==QByteArrayLiteral("ae8dbfabf98cb377f79fcb2a3295d5afccf1d1b5ce359d39e0fae627f9a7d334")}};
}

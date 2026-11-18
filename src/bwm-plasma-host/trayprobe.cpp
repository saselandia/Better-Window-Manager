// SPDX-License-Identifier: GPL-2.0-or-later
#include "trayprobe.h"
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <Plasma/Plasma>
#include <QAbstractItemModel>
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QEventLoop>
#include <QIcon>
#include <QTimer>

namespace {
class ProbeCorona : public Plasma::Corona {
public:
    QRect screenGeometry(int) const override { return {0, 0, 1280, 800}; }
};
}

bool nativeTrayPropertiesLoaded(const QVariant &status, const QVariant &category) {
    // Both status roles expose the mapped enum, returned as an int by Plasma
    // 6.7.5's implicit QVariant conversion. UnknownStatus is the initial value.
    using ItemStatus = Plasma::Types::ItemStatus;
    const auto type = status.metaType();
    if (type.id() != QMetaType::Int && type != QMetaType::fromType<ItemStatus>()) return false;
    const auto value = status.toInt();
    return (value == ItemStatus::ActiveStatus || value == ItemStatus::PassiveStatus ||
            value == ItemStatus::NeedsAttentionStatus) && !category.toString().isEmpty();
}

QJsonObject probeNativeTray(int expectedRows, bool checkProperties) {
    QJsonObject result{{"version", 1}, {"modelReady", false}, {"nativeRows", 0}, {"hostNameOwned", false}};
    const auto bus = QDBusConnection::sessionBus();
    if (!bus.isConnected()) {
        result["status"] = "filtered-bus-unavailable";
        return result;
    }
    ProbeCorona corona;
    auto *panel = corona.createContainment(QStringLiteral("org.kde.panel"));
    auto *tray = panel ? panel->createApplet(QStringLiteral("org.kde.plasma.systemtray")) : nullptr;
    auto *model = tray && !tray->failedToLaunch() ? tray->property("systemTrayModel").value<QAbstractItemModel *>() : nullptr;
    const auto roles = model ? model->roleNames() : QHash<int, QByteArray>();
    const int itemType = roles.key("itemType", -1);
    const int source = roles.key("DataEngineSource", -1);
    const int status = roles.key("Status", -1);
    const int category = roles.key("Category", -1);
    const int icon = roles.key("Icon", -1);
    if (!model || itemType < 0 || source < 0 || (checkProperties && (status < 0 || category < 0 || icon < 0))) {
        result["status"] = "native-tray-model-unavailable";
        return result;
    }
    QStringList items;
    int propertiesRead = 0;
    int usableIcons = 0;
    const auto readModel = [&] {
        items.clear();
        propertiesRead = 0;
        usableIcons = 0;
        for (int row = 0; row < model->rowCount(); ++row) {
            const auto index = model->index(row, 0);
            if (index.data(itemType).toString() != QStringLiteral("StatusNotifier")) continue;
            items.append(index.data(source).toString());
            if (!checkProperties) continue;
            if (nativeTrayPropertiesLoaded(index.data(status), index.data(category))) ++propertiesRead;
            if (!index.data(icon).value<QIcon>().pixmap(QSize(22, 22)).isNull()) ++usableIcons;
        }
        items.sort(Qt::CaseSensitive);
    };
    QEventLoop loop;
    QTimer sample;
    int consecutive = 0;
    QObject::connect(&sample, &QTimer::timeout, &loop, [&] {
        readModel();
        consecutive = items.size() == expectedRows ? consecutive + 1 : 0;
        if (consecutive >= 4 && (!checkProperties || (propertiesRead == expectedRows && usableIcons == expectedRows))) loop.quit();
    });
    QTimer::singleShot(2500, &loop, &QEventLoop::quit);
    sample.start(50);
    loop.exec();
    readModel();
    const auto name = QStringLiteral("org.kde.StatusNotifierHost-%1").arg(QCoreApplication::applicationPid());
    const auto owner = bus.interface()->serviceOwner(name);
    const bool owned = owner.isValid() && owner.value() == bus.baseService();
    result["hostNameOwned"] = owned;
    result["nativeRows"] = items.size();
    result["modelReady"] = consecutive >= 4 && items.size() == expectedRows && owned;
    if (checkProperties) {
        result["nativePropertiesCount"] = propertiesRead;
        result["nativeUsableIconCount"] = usableIcons;
    }
    // Used only by the caller to compare snapshots without showing item identifiers.
    result["itemDigest"] = QString::fromLatin1(QCryptographicHash::hash(items.join(QChar(0)).toUtf8(), QCryptographicHash::Sha256).toHex());
    result["status"] = result["modelReady"].toBool() ? "native-tray-rows-observed" : "native-tray-rows-unverified";
    return result;
}

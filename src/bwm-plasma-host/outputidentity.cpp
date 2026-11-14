// SPDX-License-Identifier: GPL-2.0-or-later
#include "outputidentity.h"
#include <QGuiApplication>
#include <QScreen>
#include <QRegularExpression>
namespace BwmOutput {
QString normalized(QString value) {
    value=value.simplified();if(value.startsWith("desc:",Qt::CaseInsensitive))value=value.mid(5).simplified();
    return value.toCaseFolded();
}
Identity identity(QScreen *screen){return {screen->manufacturer(),screen->model(),screen->serialNumber()};}
Match resolve(const QString &description,const QList<Identity> &outputs) {
    const auto wanted=normalized(description);
    static const QRegularExpression connector("^(?:DP|HDMI(?:-A|-B)?|eDP|DVI(?:-D|-I|-A)?|VGA|Virtual|HEADLESS)-?\\d+(?:-\\d+)*$",QRegularExpression::CaseInsensitiveOption);
    if(wanted.isEmpty() || connector.match(wanted).hasMatch())return {-1,"invalid-output-description"};
    QList<int> matches;
    for(int i=0;i<outputs.size();++i) {
        const auto &o=outputs[i];const auto model=normalized(o.model);
        if(model.isEmpty())continue; // No connector-name fallback, even on offscreen.
        const auto full=normalized(o.manufacturer+' '+o.model+' '+o.serial);
        const auto tail=normalized(o.model+' '+o.serial);
        // Qt Wayland 6.11.2 exposes wl_output make/model but no QScreen serial.
        // Hyprland appends an EDID serial to that exact make/model. Permit only
        // that complete prefix plus a single serial field, then require uniqueness
        // across all screens below. Never strip a known Qt serial or use substrings.
        const auto modelMarker=' '+model+' ';
        const int modelAt=wanted.lastIndexOf(modelMarker);
        // The live MSI advertises "Co., Ltd." via wl_output, whereas the
        // Hyprland description has "Co. Ltd.". Normalize commas ONLY in the
        // complete manufacturer prefix, never in the model or serial fields.
        auto make=normalized(o.manufacturer);make.remove(',');
        auto requestedMake=modelAt>=0?wanted.left(modelAt):QString();requestedMake.remove(',');
        const auto suffix=modelAt>=0?wanted.mid(modelAt+modelMarker.size()):QString();
        const bool missingSerial=normalized(o.serial).isEmpty() && !normalized(o.manufacturer).isEmpty() &&
            modelAt>=0 && requestedMake==make && !suffix.isEmpty() && !suffix.contains(QRegularExpression("\\s"));
        // A model-only request is useful when unique. A longer EDID description must
        // end in the complete model/serial sequence; arbitrary substrings are unsafe.
        if(wanted==full || wanted==model || wanted==tail || wanted.endsWith(' '+tail) || missingSerial)matches.append(i);
    }
    if(matches.isEmpty())return {-1,"output-unavailable"};
    if(matches.size()!=1)return {-1,"ambiguous-output-description"};
    return {matches.first(),"matched"};
}
QScreen *resolveScreen(const QString &description,QString *status) {
    QList<Identity> identities;const auto screens=QGuiApplication::screens();
    for(auto *screen:screens)identities.append(identity(screen));
    const auto match=resolve(description,identities);if(status)*status=match.status;
    return match.index>=0 ? screens[match.index] : nullptr;
}
}

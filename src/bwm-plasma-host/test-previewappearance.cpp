// SPDX-License-Identifier: GPL-2.0-or-later
// Read-only subprocess probe: QApplication and the original KDE icon/palette engines.
#include <QApplication>
#include <QIcon>
#include <QImage>
#include <QJsonDocument>
#include <QJsonObject>
#include <Plasma/Theme>
int main(int argc,char **argv) {
    QApplication app(argc,argv);
    const auto icon=QIcon::fromTheme("bwm-r4-native-appearance-fixture");
    const auto pixels=icon.pixmap(16,16).toImage();
    Plasma::Theme theme;
    QJsonObject report{{"version",1},{"qtPlatform",QGuiApplication::platformName()},
        {"iconTheme",QIcon::themeName()},{"iconNull",icon.isNull()},
        {"iconPixel",pixels.isNull()?QString():pixels.pixelColor(8,8).name()},
        {"windowColor",app.palette().color(QPalette::Window).name()},
        {"fontSize",app.font().pointSizeF()},{"plasmaTheme",theme.themeName()}};
    puts(QJsonDocument(report).toJson(QJsonDocument::Compact).constData());return 0;
}

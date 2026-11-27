// SPDX-License-Identifier: GPL-2.0-or-later
#include "tests/nested-input.h"
#include <QFile>
#include <QDir>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QProcess>
#include <QQuickWindow>
#include <QScopeGuard>
#include <QtTest>

namespace {
QByteArray hypr(const QStringList &args) {
    QProcess p;p.start("hyprctl",args);
    if(!p.waitForFinished(3000)||p.exitCode()!=0)return {};
    return p.readAllStandardOutput();
}
QString quoted(const QString &text) {auto a=QJsonDocument(QJsonArray{text}).toJson(QJsonDocument::Compact);return QString::fromUtf8(a.mid(1,a.size()-2));}
double factor(){return QJsonDocument::fromJson(hypr({"getoption","cursor:zoom_factor","-j"})).object().value("float").toDouble();}
}
class ZoomShortcutsTest:public QObject {
    Q_OBJECT
private Q_SLOTS:
    void physicalShortcut_data() {
        QTest::addColumn<QString>("layout");QTest::addColumn<QString>("symbol");QTest::addColumn<bool>("shift");
        QTest::newRow("us-equal")<<QString("us")<<QString("equal")<<false;
        QTest::newRow("es-equal")<<QString("es")<<QString("equal")<<true;
        QTest::newRow("us-plus")<<QString("us")<<QString("plus")<<true;
        QTest::newRow("es-plus")<<QString("es")<<QString("plus")<<false;
        QTest::newRow("us-keypad")<<QString("us")<<QString("KP_Add")<<false;
        QTest::newRow("es-keypad")<<QString("es")<<QString("KP_Add")<<false;
    }
    void physicalShortcut() {
        QFETCH(QString,layout);QFETCH(QString,symbol);QFETCH(bool,shift);
        NestedInput input;QVERIFY2(input.open(layout),qPrintable(input.error));
        auto cleanup=qScopeGuard([]{hypr({"reload"});});
        QTRY_VERIFY_WITH_TIMEOUT(QJsonDocument::fromJson(hypr({"-j","binds"})).array().isEmpty(),2000);
        const auto config=QFileInfo(qEnvironmentVariable("BWM_FOCUS_CONFIG")).dir().path();
        const auto runtime=config+"/zoom-runtime";QDir().mkpath(runtime+"/hypr");
        const auto signature=qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE");
        const auto target=qEnvironmentVariable("XDG_RUNTIME_DIR")+"/hypr/"+signature;
        const auto link=runtime+"/hypr/"+signature;
        if(!QFileInfo::exists(link))QVERIFY(QFile::link(target,link));
        const auto ownConfig=qEnvironmentVariable("XDG_CONFIG_HOME");QDir().mkpath(ownConfig+"/illogical-impulse");
        QFile selected(ownConfig+"/illogical-impulse/config.json");QVERIFY(selected.open(QIODevice::WriteOnly));
        selected.write("{\"appearance\":{\"bwmTheme\":\"plasma\"}}");selected.close();
        QFile::remove(config+"/zoom.log");
        QFile helper(config+"/zoom-helper.py");QVERIFY(helper.open(QIODevice::WriteOnly));
        const auto code="import importlib.util, pathlib, sys\n"
            "spec=importlib.util.spec_from_file_location('zoom',"+quoted(QStringLiteral(BWM_REPO_DIR)+"/config/hypr/skins/plasma/scripts/desktop-actions.py")+")\n"
            "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n"
            "module.RUNTIME=pathlib.Path(sys.argv[1]);module.STATE=module.RUNTIME/'bwm-plasma-zoom.json'\n"
            "sys.exit(module.main(sys.argv[2:]))\n";
        helper.write(code.toUtf8());helper.close();
        hypr({"eval","hl.config({input={kb_layout="+quoted(layout)+"},cursor={zoom_factor=1}})"});
        QFile binds(QStringLiteral(BWM_REPO_DIR)+"/config/hypr/keybinds.json");QVERIFY(binds.open(QIODevice::ReadOnly));
        for(const auto &value:QJsonDocument::fromJson(binds.readAll()).array()) {
            const auto bind=value.toObject();const auto command=bind.value("exec").toString();
            if(!bind.value("enabled").toBool()||!command.contains("/plasma/scripts/desktop-actions.py zoom "))continue;
            QStringList mods;for(const auto &m:bind.value("mods").toArray())mods.append(m.toString());
            const auto combo=(mods+QStringList{bind.value("key").toString()}).join(" + ");
            const auto action=command.section(' ',-1);
            if(!QStringList{"in","out","reset"}.contains(action))continue;
            const auto exec="env XDG_CONFIG_HOME="+ownConfig+" python3 "+config+"/zoom-helper.py "+runtime+" zoom "+action+" >"+config+"/zoom.log 2>&1";
            QVERIFY(hypr({"eval","hl.bind("+quoted(combo)+",hl.dsp.exec_cmd("+quoted(exec)+"))"}).contains("ok"));
        }
        QQuickWindow window;window.setTitle("BWM zoom fixture");window.resize(300,200);window.show();
        QTRY_VERIFY(window.isExposed());
        QVERIFY(input.shortcut(symbol,shift));
        QTest::qWait(300);
        QFile log(config+"/zoom.log");if(log.open(QIODevice::ReadOnly))qInfo().noquote()<<log.readAll();
        QTRY_VERIFY_WITH_TIMEOUT(factor()>1.01,3000);
        QVERIFY(input.shortcut(symbol=="KP_Add"?"KP_Subtract":"minus"));QTRY_VERIFY_WITH_TIMEOUT(qAbs(factor()-1)<.001,3000);
        QVERIFY(input.shortcut(symbol,shift));QTRY_VERIFY_WITH_TIMEOUT(factor()>1.01,3000);
        QVERIFY(input.shortcut("0"));QTRY_VERIFY_WITH_TIMEOUT(qAbs(factor()-1)<.001,3000);
    }
};
QTEST_MAIN(ZoomShortcutsTest)
#include "test-zoom-shortcuts.moc"

// SPDX-License-Identifier: GPL-2.0-or-later
// Original KDE VirtualDesktopInfo/filters against the REAL Hyprland frontend of
// bwm-plasma-desktops. Run only by check-desktops-hyprland.py, which starts a
// disposable nested Hyprland, loads the module there and destroys it afterwards.
// Never point this at the user's session compositor.
#include "tasksource.h"
#include "nativedesktopcontrol.h"
#include <virtualdesktopinfo.h>
#include <taskfilterproxymodel.h>
#include <QGuiApplication>
#include <QScreen>
#include <QJsonArray>
#include <QJsonDocument>
#include <QProcess>
#include <QtTest>
namespace {
QByteArray hyprctl(const QStringList &arguments){
    QProcess process;process.start(QStringLiteral("hyprctl"),arguments);
    if(!process.waitForFinished(3000) || process.exitCode()!=0)return {};
    return process.readAllStandardOutput();
}
QJsonObject json(const QStringList &arguments){return QJsonDocument::fromJson(hyprctl(QStringList{"-j"}+arguments)).object();}
int activeWorkspace(){return json({"activeworkspace"}).value("id").toInt();}
}
class HyprlandDesktopTest:public QObject {
    Q_OBJECT
    bool snapshot(BwmTaskSource &source){
        QProcess helper;helper.start(QStringLiteral("python3"),{QStringLiteral(BWM_TASK_HELPER_SOURCE),"snapshot"});
        if(!helper.waitForFinished(5000) || helper.exitCode()!=0)return false;
        return source.apply(QJsonDocument::fromJson(helper.readAllStandardOutput()).object());
    }
    // KDE resolves both fixture windows to kitty.desktop: identify them by PID.
    QStringList titles(const QAbstractItemModel &model){
        QHash<int,QString> classes;
        for(const auto &value:QJsonDocument::fromJson(hyprctl({"-j","clients"})).array())
            classes.insert(value.toObject().value("pid").toInt(),value.toObject().value("class").toString());
        QStringList values;for(int r=0;r<model.rowCount();++r)values<<classes.value(model.index(r,0).data(TaskManager::AbstractTasksModel::AppPid).toInt());
        values.sort();return values;
    }
private Q_SLOTS:
    void initTestCase(){
        QCOMPARE(QGuiApplication::platformName(),"wayland");
        QCOMPARE(qEnvironmentVariable("BWM_R4_NESTED_HYPRLAND"),"1");
        QCOMPARE(qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE"),qEnvironmentVariable("BWM_R4_NESTED_SIGNATURE"));
        const auto provider=json({"bwm-plasma-desktops"});
        QVERIFY2(provider.value("enabled").toBool() && provider.value("arbitrationState").toString()=="active",
            qPrintable(QJsonDocument(provider).toJson(QJsonDocument::Compact)));
    }
    void originalKdeConsumersFollowTheRealFrontend(){
        NativeDesktopControl control;
        QTRY_VERIFY_WITH_TIMEOUT(control.ensurePaused(false)==NativeDesktopControl::Status::Ready,3000);
        TaskManager::VirtualDesktopInfo info,second;
        QTRY_COMPARE_WITH_TIMEOUT(info.numberOfDesktops(),4,3000);
        QCOMPARE(info.desktopIds(),QVariantList({QString("1"),QString("2"),QString("3"),QString("4")}));
        QTRY_COMPARE(info.currentDesktop().toString(),"1");QCOMPARE(activeWorkspace(),1);
        // Activation through KDE's own API is applied by Hyprland's dispatcher.
        info.requestActivate(QString("2"));
        QTRY_COMPARE(activeWorkspace(),2);QTRY_COMPARE(second.currentDesktop().toString(),"2");
        // Hyprland-side change (keyboard/IPC) is reflected back to KDE consumers.
        hyprctl({"dispatch","hl.dsp.focus({ workspace = \"3\" })"});
        QTRY_COMPARE(info.currentDesktop().toString(),"3");
        info.requestActivate(QString("1"));QTRY_COMPARE(activeWorkspace(),1);
        QTRY_COMPARE(info.currentDesktopByScreenName(QGuiApplication::primaryScreen()->name()).toString(),"1");
        // Current-desktop filter of the original TaskFilterProxyModel with the
        // real snapshot helper: only the window on the current workspace shows.
        BwmTaskSource source;QVERIFY(snapshot(source));QCOMPARE(source.rowCount(),2);
        TaskManager::TaskFilterProxyModel filter;filter.setSourceModel(&source);
        filter.setScreenGeometry(QGuiApplication::primaryScreen()->geometry());filter.setFilterByCurrentVirtualDesktop(true);
        QTRY_COMPARE(titles(filter),QStringList{"bwm-r4-nested-a"});
        info.requestActivate(QString("2"));QTRY_COMPARE(activeWorkspace(),2);
        QTRY_COMPARE(titles(filter),QStringList{"bwm-r4-nested-b"});
        info.requestActivate(QString("1"));QTRY_COMPARE(activeWorkspace(),1);
        // Common count from the BWM bridge is mirrored live; no file read in the compositor.
        QCOMPARE(QJsonDocument::fromJson(hyprctl({"bwm-plasma-desktops-count","6"})).object().value("accepted").toBool(),true);
        QTRY_COMPARE(info.numberOfDesktops(),6);
        hyprctl({"bwm-plasma-desktops-count","4"});QTRY_COMPARE(info.numberOfDesktops(),4);
        // Paused connection: KDE requests are ignored until ownership resumes.
        QTRY_VERIFY(control.ensurePaused(true)==NativeDesktopControl::Status::Ready);
        info.requestActivate(QString("2"));QTest::qWait(300);QCOMPARE(activeWorkspace(),1);
        QTRY_VERIFY(control.ensurePaused(false)==NativeDesktopControl::Status::Ready);
        info.requestActivate(QString("2"));QTRY_COMPARE(activeWorkspace(),2);
        info.requestActivate(QString("1"));QTRY_COMPARE(activeWorkspace(),1);
        // Unsupported capabilities stay explicit.
        info.requestCreateDesktop(0);info.requestRemoveDesktop(0);QTest::qWait(200);QCOMPARE(info.numberOfDesktops(),4);
        const auto provider=json({"bwm-plasma-desktops"});
        QVERIFY(provider.value("appliedActivations").toInt()>=4);
        QCOMPARE(provider.value("lastError").toString(),QString());
    }
};
QTEST_MAIN(HyprlandDesktopTest)
#include "test-desktops-hyprland.moc"

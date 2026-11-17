// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <tasktools.h>
#include <KServiceAction>
#include <QJsonArray>
#include <QJsonObject>
KService::Ptr nativeTaskApplication(const TaskManager::AppData &app);
bool nativeTaskCanLaunchNewInstance(const TaskManager::AppData &app);
// Same resolution as LauncherTasksModel/runApp for pinned launchers, limited to
// registered applications (no OpenUrlJob/executable fallback).
KService::Ptr nativeLauncherApplication(const QUrl &launcherUrl);
// Bounded encoding shared by window, launcher and drop requests.
bool encodeNativeLaunchUrls(const QList<QUrl> &urls,QJsonArray &values);
bool validNativeLauncherUrl(const QUrl &url,QString *encoded=nullptr);
// In this process: true when KIOSK denies KIO desktop/command launches.
bool nativeInProcessLaunchDenied();
// No panel/capture. Uses the caller environment restored by the Python dispatcher.
QJsonObject launchNativeTaskApplication(const QJsonObject &request);
int runNativeTaskLauncher();

// SPDX-License-Identifier: GPL-2.0-or-later
#include "nightlightmodule.h"
#include <KLocalizedString>
#include <QCheckBox>
#include <QDir>
#include <QFormLayout>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QSpinBox>
#include <QTimer>

NightlightModule::NightlightModule(QObject *parent, const KPluginMetaData &data)
    : NightlightModule(parent, data, {QStringLiteral("python3"), QDir::homePath() + QStringLiteral("/.config/hypr/scripts/nightlight.py")}) {}

NightlightModule::NightlightModule(QObject *parent, const KPluginMetaData &data, const QStringList &backend)
    : KCModule(parent, data), m_backend(backend) {
    setButtons(Apply | Default);
    m_timeout.setSingleShot(true);
    connect(&m_timeout, &QTimer::timeout, &m_process, &QProcess::kill);
    auto *layout = new QFormLayout(widget());
    auto *description = new QLabel(i18nd("bwm", "These settings are shared by all BWM skins."), widget());
    description->setWordWrap(true);
    layout->addRow(description);
    m_enabled = new QCheckBox(i18nd("bwm", "Enable Night Light"), widget());
    m_enabled->setObjectName(QStringLiteral("enabled"));
    m_temperature = new QSpinBox(widget());
    m_temperature->setObjectName(QStringLiteral("temperature"));
    m_temperature->setRange(2500, 6500);
    m_temperature->setSingleStep(100);
    m_temperature->setSuffix(QStringLiteral(" K"));
    m_temperature->setValue(4000);
    layout->addRow(m_enabled);
    layout->addRow(i18nd("bwm", "Color temperature:"), m_temperature);
    m_error = new QLabel(widget());
    m_error->setObjectName(QStringLiteral("error"));
    m_error->setWordWrap(true);
    m_error->setTextInteractionFlags(Qt::TextSelectableByMouse);
    layout->addRow(m_error);
    widget()->setEnabled(false);
    connect(m_enabled, &QCheckBox::toggled, this, &NightlightModule::updateChanged);
    connect(m_temperature, &QSpinBox::valueChanged, this, &NightlightModule::updateChanged);
    connect(&m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error == QProcess::FailedToStart) {
            m_timeout.stop();
            m_error->setText(i18nd("bwm", "Could not start the BWM Night Light controller."));
            widget()->setEnabled(true);
        }
    });
    connect(&m_process, &QProcess::finished, this, [this](int status, QProcess::ExitStatus exit) {
        m_timeout.stop();
        widget()->setEnabled(true);
        QJsonParseError error;
        const auto document = QJsonDocument::fromJson(m_process.readAllStandardOutput(), &error);
        const auto state = document.object();
        const auto temperature = state.value(QStringLiteral("temperature"));
        const auto enabled = state.value(QStringLiteral("enabled"));
        if (exit != QProcess::NormalExit || status != 0 || error.error != QJsonParseError::NoError
            || !enabled.isBool() || !temperature.isDouble() || temperature.toInt() < 2500 || temperature.toInt() > 6500) {
            m_error->setText(i18nd("bwm", "The BWM controller did not return valid settings. Changes have not been confirmed."));
            return;
        }
        m_error->clear();
        m_savedEnabled = enabled.toBool();
        m_savedTemperature = temperature.toInt();
        m_valid = true;
        m_enabled->setChecked(m_savedEnabled);
        m_temperature->setValue(m_savedTemperature);
        updateChanged();
    });
}

void NightlightModule::request(const QStringList &arguments) {
    if (m_process.state() != QProcess::NotRunning || m_backend.isEmpty()) return;
    widget()->setEnabled(false);
    m_error->clear();
    m_process.start(m_backend.first(), m_backend.mid(1) + arguments);
    m_timeout.start(15000);
}

void NightlightModule::load() { request({QStringLiteral("--status")}); }
void NightlightModule::save() {
    if (!m_valid) return;
    request({QStringLiteral("--temperature"), QString::number(m_temperature->value()),
             m_enabled->isChecked() ? QStringLiteral("--on") : QStringLiteral("--off")});
    // KCModule::save is synchronous: the host may unload the page immediately on return.
    // Finish this one controller transaction before allowing navigation to destroy the process.
    if (!m_process.waitForFinished(10000) && m_process.state() != QProcess::NotRunning) {
        m_process.kill();
        m_process.waitForFinished(1000);
    }
}
void NightlightModule::defaults() {
    m_enabled->setChecked(false);
    m_temperature->setValue(4000);
}
void NightlightModule::updateChanged() {
    setNeedsSave(m_valid && (m_enabled->isChecked() != m_savedEnabled || m_temperature->value() != m_savedTemperature));
    setRepresentsDefaults(!m_enabled->isChecked() && m_temperature->value() == 4000);
}

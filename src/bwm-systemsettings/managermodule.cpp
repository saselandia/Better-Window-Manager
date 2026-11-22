// SPDX-License-Identifier: GPL-2.0-or-later
#include "managermodule.h"
#include <KLocalizedString>
#include <QCheckBox>
#include <QComboBox>
#include <QDir>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QLabel>
#include <QLineEdit>
#include <QLocale>
#include <QProcess>
#include <QScrollArea>
#include <QSpinBox>
#include <QVBoxLayout>

ManagerModule::ManagerModule(QObject *parent, const KPluginMetaData &data)
    : ManagerModule(parent, data, {QStringLiteral("python3"), QDir::homePath() + QStringLiteral("/.config/hypr/skins/plasma/scripts/native-settings.py"), data.value(QStringLiteral("X-BWM-Category"))}) {}
ManagerModule::ManagerModule(QObject *parent, const KPluginMetaData &data, const QStringList &backend)
    : KCModule(parent, data), m_backend(backend) {
    // There is no invented factory default for a user's applications, monitors or shortcuts.
    setButtons(Apply);
    auto *layout = new QVBoxLayout(widget());
    auto *notice = new QLabel(data.value(QStringLiteral("X-BWM-Category")) == QStringLiteral("effects")
        ? i18nd("bwm", "Desktop effects supported by Breeze. Changes apply only when you press Apply.")
        : i18nd("bwm", "Shared BWM settings. Changes apply only when you press Apply."), widget());
    notice->setWordWrap(true);
    layout->addWidget(notice);
    auto *scroll = new QScrollArea(widget());
    scroll->setWidgetResizable(true);
    m_fields = new QWidget(scroll);
    m_form = new QFormLayout(m_fields);
    scroll->setWidget(m_fields);
    layout->addWidget(scroll);
    m_error = new QLabel(widget());
    m_error->setObjectName(QStringLiteral("error"));
    m_error->setWordWrap(true);
    m_error->setTextInteractionFlags(Qt::TextSelectableByMouse);
    layout->addWidget(m_error);
}

bool ManagerModule::request(const QString &action, const QJsonObject &payload, QJsonObject &response) {
    QProcess process;
    if (m_backend.isEmpty()) return false;
    process.start(m_backend.first(), m_backend.mid(1) + QStringList{action});
    if (!process.waitForStarted(3000)) {
        m_error->setText(i18nd("bwm", "Could not start the BWM controller."));
        return false;
    }
    process.write(QJsonDocument(payload).toJson(QJsonDocument::Compact));
    process.closeWriteChannel();
    if (!process.waitForFinished(60000)) {
        process.kill();
        process.waitForFinished(1000);
        m_error->setText(i18nd("bwm", "The controller timed out. Some changes may have applied. Reset to read the current state."));
        return false;
    }
    QJsonParseError error;
    const auto doc = QJsonDocument::fromJson(process.readAllStandardOutput(), &error);
    response = doc.object();
    if (process.exitStatus() != QProcess::NormalExit || process.exitCode() || error.error != QJsonParseError::NoError
        || !response.value(QStringLiteral("fields")).isArray() || !response.value(QStringLiteral("revision")).isString()) {
        m_error->setText(response.value(QStringLiteral("error")).toString(i18nd("bwm", "The controller did not confirm the changes. Reset to read the current state.")));
        return false;
    }
    m_error->clear();
    return true;
}
void ManagerModule::populate(const QJsonObject &response) {
    m_readers.clear();
    m_writers.clear();
    m_defaults = {};
    m_values = {};
    while (m_form->rowCount()) m_form->removeRow(0);
    m_revision = response.value(QStringLiteral("revision")).toString();
    for (const auto &entry : response.value(QStringLiteral("fields")).toArray()) {
        const auto f = entry.toObject();
        const auto key = f.value(QStringLiteral("key")).toString();
        const auto value = f.value(QStringLiteral("value"));
        const auto type = f.value(QStringLiteral("type")).toString();
        QWidget *editor = nullptr;
        if (type == QStringLiteral("bool")) {
            auto *e = new QCheckBox(m_fields);
            e->setChecked(value.toBool());
            m_readers[key] = [e] { return QJsonValue(e->isChecked()); };
            m_writers[key] = [e](const QJsonValue &v) { e->setChecked(v.toBool()); };
            connect(e, &QCheckBox::toggled, this, &ManagerModule::updateChanged);
            editor = e;
        } else if (type == QStringLiteral("choice")) {
            auto *e = new QComboBox(m_fields);
            for (const auto &c : f.value(QStringLiteral("choices")).toArray()) {
                const auto choice = c.toObject();
                e->addItem(choice.value(QStringLiteral("label")).toString(), choice.value(QStringLiteral("value")).toVariant());
            }
            e->setCurrentIndex(e->findData(value.toVariant()));
            m_readers[key] = [e] { return QJsonValue::fromVariant(e->currentData()); };
            m_writers[key] = [e](const QJsonValue &v) { e->setCurrentIndex(e->findData(v.toVariant())); };
            connect(e, &QComboBox::currentIndexChanged, this, &ManagerModule::updateChanged);
            editor = e;
        } else if (type == QStringLiteral("int")) {
            auto *e = new QSpinBox(m_fields);
            e->setRange(f.value(QStringLiteral("min")).toInt(), f.value(QStringLiteral("max")).toInt());
            e->setValue(value.toInt());
            m_readers[key] = [e] { return QJsonValue(e->value()); };
            m_writers[key] = [e](const QJsonValue &v) { e->setValue(v.toInt()); };
            connect(e, &QSpinBox::valueChanged, this, &ManagerModule::updateChanged);
            editor = e;
        } else if (type == QStringLiteral("real")) {
            auto *e = new QDoubleSpinBox(m_fields);
            e->setRange(f.value(QStringLiteral("min")).toDouble(), f.value(QStringLiteral("max")).toDouble());
            e->setDecimals(f.value(QStringLiteral("decimals")).toInt(2));
            e->setSingleStep(f.value(QStringLiteral("step")).toDouble(0.25));
            e->setValue(value.toDouble());
            m_readers[key] = [e] { return QJsonValue(e->value()); };
            m_writers[key] = [e](const QJsonValue &v) { e->setValue(v.toDouble()); };
            connect(e, &QDoubleSpinBox::valueChanged, this, &ManagerModule::updateChanged);
            editor = e;
        } else {
            auto *e = new QLineEdit(value.toString(), m_fields);
            m_readers[key] = [e] { return QJsonValue(e->text()); };
            m_writers[key] = [e](const QJsonValue &v) { e->setText(v.toString()); };
            connect(e, &QLineEdit::textChanged, this, &ManagerModule::updateChanged);
            editor = e;
        }
        editor->setObjectName(key);
        m_values.insert(key, value);
        if (f.contains(QStringLiteral("default"))) m_defaults.insert(key, f.value(QStringLiteral("default")));
        const auto labelKey = QLocale().language() == QLocale::Spanish ? QStringLiteral("label") : QStringLiteral("label_en");
        m_form->addRow(f.value(labelKey).toString(f.value(QStringLiteral("label")).toString()), editor);
    }
    setButtons(m_defaults.isEmpty() ? Apply : Apply | Default);
    updateChanged();
}
QJsonObject ManagerModule::changes() const {
    QJsonObject result;
    for (auto it = m_readers.cbegin(); it != m_readers.cend(); ++it)
        if (it.value()() != m_values.value(it.key())) result.insert(it.key(), it.value()());
    return result;
}
void ManagerModule::updateChanged() {
    setNeedsSave(!changes().isEmpty());
    bool atDefaults = !m_defaults.isEmpty();
    for (auto it = m_defaults.constBegin(); it != m_defaults.constEnd(); ++it)
        atDefaults = atDefaults && m_readers.value(it.key())() == it.value();
    setRepresentsDefaults(atDefaults);
}
void ManagerModule::defaults() {
    for (auto it = m_defaults.constBegin(); it != m_defaults.constEnd(); ++it) m_writers.value(it.key())(it.value());
    updateChanged();
}
void ManagerModule::load() {
    QJsonObject response;
    if (request(QStringLiteral("load"), {}, response)) { m_fields->setEnabled(true); populate(response); }
    else { m_fields->setEnabled(false); m_revision.clear(); }
}
void ManagerModule::save() {
    if (m_revision.isEmpty()) return;
    QJsonObject response;
    if (request(QStringLiteral("save"), {{QStringLiteral("revision"), m_revision}, {QStringLiteral("changes"), changes()}}, response)) populate(response);
}

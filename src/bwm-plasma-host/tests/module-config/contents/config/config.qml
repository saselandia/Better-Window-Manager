// SPDX-License-Identifier: GPL-2.0-or-later
import org.kde.plasma.configuration
ConfigModel {
    ConfigCategory { name: "File category"; source: "File.qml" }
    ConfigCategory {
        name: "Module category"
        configUiModule: "org.bwm.r4.configpages"
        configUiComponent: "ModulePage"
        // The complete module pair takes precedence over this valid, different page.
        source: "File.qml"
    }
}

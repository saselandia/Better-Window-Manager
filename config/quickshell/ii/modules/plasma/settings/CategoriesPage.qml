/*
   SPDX-FileCopyrightText: 2017 Marco Martin <mart@kde.org>

   SPDX-License-Identifier: LGPL-2.0-only
*/

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
// BWM: models from SettingsState (Catalog.js) instead of org.kde.systemsettings (C++)

Kirigami.ScrollablePage {
    id: mainColumn
    readonly property bool searchMode: searchField.text.length > 0

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false

    header: Kirigami.AbstractApplicationHeader {
        id: pageHeader

        // TODO Plasma 6.6 align size to grid
        height: Math.round((sizeHelper.implicitHeight + Kirigami.Units.smallSpacing * 2) * Screen.devicePixelRatio) / Screen.devicePixelRatio

        // Not visible; just to get its size so we can match this custom header
        // with the height of a standard header
        QQC2.ToolButton {
            id: sizeHelper
            visible: false
            icon.name: "go-previous"
        }

        contentItem: RowLayout {
            id: rowLayout
            // FIXME: left and right anchors shouldn't be needed here, but if
            // they're removed, the layout doesn't span the full width
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing

            Keys.onDownPressed: event => {
                categoryView.currentIndex = 0;
                event.accepted = false; // Pass to KeyNavigation.down
            }

            Kirigami.SearchField {
                id: searchField

                focus: !Kirigami.InputMethod.willShowOnActive
                Layout.fillWidth: true
                onTextChanged: {
                    SettingsState.filterText = text; // BWM
                }

                KeyNavigation.right: hamburgerMenuButton

                KeyNavigation.down: categoryView

                KeyNavigation.backtab: KeyNavigation.left
                KeyNavigation.tab: KeyNavigation.right

                Keys.onDownPressed: event => rowLayout.Keys.downPressed(event)
                // BWM: no C++ focus chain (systemsettings.giveFocus)
            }

            HamburgerMenuButton {
                id: hamburgerMenuButton

                KeyNavigation.left: searchField

                KeyNavigation.down: categoryView

                KeyNavigation.backtab: KeyNavigation.left
                KeyNavigation.tab: KeyNavigation.down

                Keys.onDownPressed: event => rowLayout.Keys.downPressed(event)
            }
        }
    }

    // We don't want it to go into default property and be reparented to a
    // ScrollView, otherwise after clearing search term the scrollbar would
    // appear and shift the fading out placeholder to the left.
    property Item __placeholder: Loader {
        parent: mainColumn
        anchors.centerIn: parent
        width: parent.width - (Kirigami.Units.gridUnit * 4)
        opacity: categoryView.count === 0 ? 1 : 0
        active: opacity > 0
        visible: active
        Behavior on opacity {
            NumberAnimation {
                duration: Kirigami.Units.longDuration
                easing.type: Easing.InOutQuad
            }
        }
        sourceComponent: Kirigami.PlaceholderMessage {
            width: parent.width
            icon.name: "edit-none"
            text: SettingsI18n.i18nc("A search yielded no results", "No items matching your search")
        }
    }

    Binding {
        target: categoryView
        property: "currentIndex"
        value: mainColumn.searchMode
            ? SettingsState.activeSearchRow
            : SettingsState.activeCategoryRow
    }

    ListView {
        id: categoryView

        model: mainColumn.searchMode ? SettingsState.searchModel : SettingsState.categoryModel

        activeFocusOnTab: true
        keyNavigationWraps: true
        Accessible.role: Accessible.List

        KeyNavigation.up: searchField
        KeyNavigation.backtab: hamburgerMenuButton
        Keys.onUpPressed: event => {
            if (categoryView.currentIndex === 0) {
                categoryView.currentIndex = -1;
            }
            event.accepted = false; // Pass to KeyNavigation.up
        }
        // BWM: Tab moves on to the module view through the normal focus chain

        section {
            property: "categoryDisplayRole"
            delegate: Kirigami.ListSectionHeader {

                required property string section

                width: ListView.view.width
                label: section
            }
        }

        delegate: CategoryItem {
            id: delegate

            required property int index
            required property var model
            required property bool isCategory
            required property int depth
            required property bool isKCM
            required property string iconName
            required property int childCount // BWM: rowCount of the C++ model

            text: model.display
            icon.name: iconName

            showArrow: isCategory && childCount > 1
            // Only indent subcategory icons in the search view
            leadingPadding: (depth > 1 && searchField.text.length > 0) ? (( depth - 1 ) * Kirigami.Units.iconSizes.smallMedium) + Kirigami.Units.largeSpacing : 0

            hoverEnabled: !isCategory || !mainColumn.searchMode
            enabled: !isCategory || !mainColumn.searchMode

            highlighted: ListView.isCurrentItem

            onClicked: {
                if (!enabled) { return; }
                if (isKCM || mainColumn.searchMode || SettingsState.activeCategoryRow !== index) {
                    SettingsState.loadModule(categoryView.model.get(index)); // BWM: row data, not QModelIndex
                }
                if (!mainColumn.searchMode && root.pageStack.depth > 1) {
                    root.pageStack.currentIndex = 1;
                }
            }
            onFocusChanged: {
                if (isCategory && mainColumn.searchMode) {
                    return;
                }
                if (focus) {
                    categoryView.positionViewAtIndex(index, ListView.Contain);
                }
            }
            Keys.onEnterPressed: clicked();
            Keys.onReturnPressed: clicked();

            Keys.onLeftPressed: {
                if (LayoutMirroring.enabled) {
                    clicked();
                }
            }
            Keys.onRightPressed: {
                if (!LayoutMirroring.enabled) {
                    clicked();
                }
            }
        }
    }
}

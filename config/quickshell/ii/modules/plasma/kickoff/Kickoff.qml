/*
    SPDX-FileCopyrightText: 2011 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2012 Gregor Taetzner <gregor@freenet.de>
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2013 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2015 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2021 Mikel Johnson <mikel5764@gmail.com>
    SPDX-FileCopyrightText: 2021 Noah Davis <noahadvs@gmail.com>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
// BWM: el attached Plasmoid de libplasma no existe fuera de un contenedor de Plasma: lo da el singleton Plasmoid.qml de este módulo
import org.kde.plasma.core as PlasmaCore
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami

import "code/tools.js" as Tools
import qs

// BWM: raíz del Kickoff portado (main.qml de plasma-desktop 6.7.5, applets/kickoff). En vez de un
// PlasmoidItem es un Item normal que KickoffWindow.qml coloca en una capa emergente; expanded,
// hideOnWindowDeactivate y fullRepresentationItem sustituyen a las propiedades del PlasmoidItem.
// Las demás piezas leen «kickoff.*» como en Plasma (id del documento).
Item {
    id: kickoff

    // BWM: estado del PlasmoidItem
    // Sincronizado en los dos sentidos con GlobalStates (sin enlace: el QML de Plasma asigna
    // kickoff.expanded = false al lanzar algo, y un enlace se rompería ahí)
    property bool expanded: false
    Component.onCompleted: expanded = GlobalStates.plasmaKickoffOpen
    onExpandedChanged: if (GlobalStates.plasmaKickoffOpen !== expanded) GlobalStates.plasmaKickoffOpen = expanded
    Connections {
        target: GlobalStates
        function onPlasmaKickoffOpenChanged() {
            if (kickoff.expanded !== GlobalStates.plasmaKickoffOpen)
                kickoff.expanded = GlobalStates.plasmaKickoffOpen;
        }
    }
    property bool hideOnWindowDeactivate: !Plasmoid.configuration.pin
    property Item fullRepresentationItem: fullRepresentation
    // BWM: en Plasma, Escape lo recoge el PlasmaQuick::Dialog a nivel de ventana (la búsqueda
    // reenvía las teclas a la vista, que se queda con ella). Primero vacía la búsqueda; si ya
    // está vacía, cierra.
    Shortcut {
        sequence: "Escape"
        // Mientras está abierto, Kickoff tiene el teclado en exclusiva (layer-shell): basta con la
        // aplicación, y así funciona aunque su capa no sea la ventana activa de Qt
        context: Qt.ApplicationShortcut
        enabled: kickoff.expanded
        onActivated: {
            if (kickoff.searchField && kickoff.searchField.text.length > 0)
                kickoff.searchField.clear();
            else
                kickoff.expanded = false;
        }
    }
    implicitWidth: fullRepresentation.implicitWidth
    implicitHeight: fullRepresentation.implicitHeight

    // BWM: Plasma inyecta i18n/i18nc en el contexto del plasmoide (las piezas los llaman sin calificar)
    function i18n(...args) { return KickoffI18n.i18n(...args); }
    function i18nc(...args) { return KickoffI18n.i18nc(...args); }

    // The properties are defined here instead of the singleton because each
    // instance of Kickoff requires different instances of these properties

    readonly property bool inPanel: [
        PlasmaCore.Types.TopEdge,
        PlasmaCore.Types.RightEdge,
        PlasmaCore.Types.BottomEdge,
        PlasmaCore.Types.LeftEdge,
    ].includes(Plasmoid.location)
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    // Used to prevent the width from changing frequently when the scrollbar appears or disappears
    readonly property bool mayHaveGridWithScrollBar: Plasmoid.configuration.applicationsDisplay === 0
        || (Plasmoid.configuration.favoritesDisplay === 0 && kickoff.rootModel.favoritesModel.count > minimumGridRowCount * minimumGridRowCount)

    //BEGIN Models
    readonly property Kicker.RootModel rootModel: Kicker.RootModel {
        autoPopulate: false

        // BWM: sin Applet de Plasma (appletInterface) las acciones «añadir al panel/escritorio» no aparecen

        appNameFormat: Plasmoid.configuration.appNameFormat
        flat: true // have categories, but no subcategories
        sorted: Plasmoid.configuration.alphaSort
        showSeparators: !sorted && Plasmoid.configuration.applicationsDisplay != 0
        showRootSeparator: true
        showTopLevelItems: true

        showAllApps: true
        showAllAppsCategorized: false
        showRecentApps: false
        showRecentDocs: false
        showPowerSession: false
        showFavoritesPlaceholder: true
        highlightNewlyInstalledApps: Plasmoid.configuration.highlightNewlyInstalledApps

        Component.onCompleted: {
            favoritesModel.initForClient("org.kde.plasma.kickoff.favorites.instance-" + Plasmoid.id)

            if (!Plasmoid.configuration.favoritesPortedToKAstats) {
                if (favoritesModel.count < 1) {
                    favoritesModel.portOldFavorites(Plasmoid.configuration.favorites);
                }
                Plasmoid.configuration.favoritesPortedToKAstats = true;
            }
        }
    }

    readonly property Kicker.RunnerModel runnerModel: Kicker.RunnerModel {
        query: kickoff.searchField ? kickoff.searchField.text : ""
        onRequestUpdateQuery: query => {
            if (kickoff.searchField) {
                kickoff.searchField.text = query;
            }
        }
        mergeResults: true
        favoritesModel: kickoff.rootModel.favoritesModel
    }

    readonly property Kicker.ComputerModel computerModel: Kicker.ComputerModel {
        favoritesModel: kickoff.rootModel.favoritesModel
        systemApplications: Plasmoid.configuration.systemApplications
        Component.onCompleted: {
            //systemApplications = Plasmoid.configuration.systemApplications;
        }
    }

    readonly property alias recentUsageModel: recentUsageModel
    Kicker.RecentUsageModel {
        id: recentUsageModel
        favoritesModel: kickoff.rootModel.favoritesModel
    }

    readonly property alias frequentUsageModel: frequentUsageModel
    Kicker.RecentUsageModel {
        id: frequentUsageModel
        favoritesModel: kickoff.rootModel.favoritesModel
        ordering: 1 // Popular / Frequently Used
    }
    //END

    //BEGIN UI elements
    // Set in FullRepresentation.qml
    property Item header: null

    // Set in Header.qml
    // QTBUG Using PC3.TextField as type makes assignment fail
    // "Cannot assign QObject* to TextField_QMLTYPE_8*"
    property Item searchField: null

    // Set in FullRepresentation.qml, ApplicationPage.qml, PlacesPage.qml
    property Item sideBar: null // is null when searching
    property Item contentArea: null // is searchView when searching

    // Set in NormalPage.qml
    property Item footer: null

    // True when central pane (and header) LayoutMirroring diverges from global
    // LayoutMirroring, in order to achieve the desired sidebar position
    readonly property bool paneSwap: Plasmoid.configuration.paneSwap
    readonly property bool sideBarOnRight: (Application.layoutDirection == Qt.RightToLeft) != paneSwap
    // References to items according to their focus chain order
    readonly property Item firstHeaderItem: header ? (paneSwap ? header.pinButton : header.avatar) : null
    readonly property Item lastHeaderItem: header ? (paneSwap ? header.avatar : header.pinButton) : null
    readonly property Item firstCentralPane: paneSwap ? contentArea : sideBar
    readonly property Item lastCentralPane: paneSwap ? sideBar : contentArea

    readonly property Item dragSource: Item {
        id: dragSource // BUG 449426
        property Item sourceItem
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.CopyAction | Qt.LinkAction | Qt.MoveAction
    }
    //END

    //BEGIN Metrics
    readonly property KSvg.FrameSvgItem backgroundMetrics: KSvg.FrameSvgItem {
        // Inset defaults to a negative value when not set by margin hints
        readonly property real leftPadding: Math.round(margins.left - Math.max(inset.left, 0))
        readonly property real rightPadding: Math.round(margins.right - Math.max(inset.right, 0))
        readonly property real topPadding: Math.round(margins.top - Math.max(inset.top, 0))
        readonly property real bottomPadding: Math.round(margins.bottom - Math.max(inset.bottom, 0))
        readonly property real spacing: Math.round(leftPadding)
        visible: false
        imagePath: Plasmoid.formFactor === PlasmaCore.Types.Planar ? "widgets/background" : "dialogs/background"
    }

    // This is here rather than in the singleton with the other metrics items
    // because the list delegate's height depends on a configuration setting
    // and the singleton can't access those
    readonly property real listDelegateHeight: listDelegate.height
    KickoffListDelegate {
        id: listDelegate
        visible: false
        enabled: false
        model: null
        index: -1
        text: "asdf"
        url: ""
        decoration: "start-here-kde"
        description: "asdf"
        action: null
        indicator: null
        // BWM: propiedad requerida que el original no da. Plasma crea esto de forma síncrona y sólo
        // avisa; en la carga asíncrona del Loader de Quickshell aborta la creación de Kickoff (y al
        // destruir lo ya creado, KSvg tiraba el shell)
        isMultilineText: false
    }

    // Used to show smaller Kickoff on small screens
    readonly property int minimumGridRowCount: Math.min(Screen.desktopAvailableWidth, Screen.desktopAvailableHeight) * Screen.devicePixelRatio < KickoffSingleton.gridCellSize * 4 + (fullRepresentationItem ? fullRepresentationItem.normalPage.preferredSideBarWidth : KickoffSingleton.gridCellSize * 2) ? 2 : 4
    //END

    // BWM: Plasmoid.icon sale de Plasmoid.configuration.icon en Plasmoid.qml

    // BWM: el botón del panel es el de modules/plasma/panel (PanelContent.qml); aquí sólo la vista completa
    FullRepresentation {
        id: fullRepresentation
        anchors.fill: parent
        focus: true
    }

    Kicker.ProcessRunner {
        id: processRunner
    }

    // BWM: «Editar aplicaciones…» (kmenuedit) del menú contextual del plasmoide: sin contenedor de
    // Plasma no hay ese menú; las acciones de cada app siguen en su propio menú contextual.
} // root

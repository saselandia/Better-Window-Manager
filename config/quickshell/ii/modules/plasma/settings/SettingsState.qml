// SPDX-License-Identifier: GPL-2.0-or-later
pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import "Catalog.js" as Catalog

/**
 * BWM F11: what systemsettings' C++ object `systemsettings` gives its QML (categoryModel,
 * subCategoryModel, searchModel, active rows, loadModule, defaults indicators), built from
 * Catalog.js instead of KCM metadata categories. The ported sidebar uses it under that role.
 */
Singleton {
    id: root

    readonly property bool spanish: Qt.locale().name.startsWith("es")
    // org.bwm.kcm (src/bwm-kcmhost) may be missing: KCM pages then say so instead of failing
    readonly property var kcmApi: {
        try { return Qt.createQmlObject("import org.bwm.kcm; KcmHost {}", root, "kcmApi"); }
        catch (e) { console.warn("BWM settings: org.bwm.kcm not installed"); return null; }
    }
    property string filterText: ""
    property bool defaultsIndicatorsVisible: false
    property var current: null       // { entry, section, parent }
    property int activeCategoryRow: -1
    property int activeSubCategoryRow: -1
    property int activeSearchRow: -1
    property string subCategoryTitle: ""
    property var subCategoryEntry: null
    // ModuleView: a KCM has unapplied changes, so changing page asks first (askBeforeLeaving)
    property bool unsavedChanges: false
    property var askBeforeLeaving: null

    function label(entry) {
        if (entry.kind === "kcm") {
            const info = root.kcmApi ? root.kcmApi.info(entry.module) : null;
            if (info && info.name) return info.name;
        }
        return entry.name ? entry.name[root.spanish ? 1 : 0] : entry.id;
    }
    function iconFor(entry) {
        if (entry.kind === "kcm") {
            const info = root.kcmApi ? root.kcmApi.info(entry.module) : null;
            if (info && info.icon) return info.icon;
        }
        return entry.icon || "preferences-system";
    }
    function sectionName(section) { return section.name[root.spanish ? 1 : 0]; }

    property ListModel categoryModel: ListModel {}
    property ListModel subCategoryModel: ListModel {}
    property ListModel searchModel: ListModel {}

    function row(entry, section, depth) {
        return { display: root.label(entry), iconName: root.iconFor(entry), entryId: entry.id,
                 isCategory: !!entry.items, isKCM: !entry.items, depth: depth,
                 categoryDisplayRole: root.sectionName(section), childCount: entry.items ? entry.items.length : 0,
                 showDefaultIndicator: false };
    }
    function rebuild() {
        categoryModel.clear();
        for (const s of Catalog.sections)
            for (const item of s.items) categoryModel.append(row(item, s, 1));
        rebuildSearch();
    }
    function words(entry) {
        return (root.label(entry) + " " + (entry.name || []).join(" ") + " " + (entry.keywords || "") + " " + entry.id)
            .toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }
    function rebuildSearch() {
        searchModel.clear();
        const f = root.filterText.trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
        if (!f) return;
        let lastParent = null;
        for (const l of Catalog.leaves()) {
            if (!root.words(l.entry).includes(f) && !(l.parent && root.words(l.parent).includes(f))) continue;
            if (l.parent && l.parent !== lastParent) searchModel.append(row(l.parent, l.section, 1));
            lastParent = l.parent;
            searchModel.append(row(l.entry, l.section, l.parent ? 2 : 1));
        }
        root.activeSearchRow = -1;
        for (let i = 0; i < searchModel.count; i++)
            if (root.current && searchModel.get(i).entryId === root.current.entry.id) root.activeSearchRow = i;
    }
    onFilterTextChanged: rebuildSearch()

    function locate(id) { return Catalog.leaves().find(l => l.entry.id === id) || null; }
    function openSubCategory(id) {
        const s = Catalog.sections.find(s => s.items.some(i => i.id === id));
        const cat = s.items.find(i => i.id === id);
        root.subCategoryEntry = cat;
        root.subCategoryTitle = root.label(cat);
        subCategoryModel.clear();
        for (const child of cat.items) subCategoryModel.append(row(child, s, 2));
    }

    // Select by model row data, like systemsettings' loadModule(QModelIndex)
    function loadModule(rowData) {
        if (!rowData) return;
        if (rowData.isCategory) {
            const s = Catalog.sections.find(s => s.items.some(i => i.id === rowData.entryId));
            const cat = s.items.find(i => i.id === rowData.entryId);
            root.select(cat.items[0].id);
        } else {
            root.select(rowData.entryId);
        }
    }
    function select(id, force) {
        const target = root.locate(id);
        if (!target) return false;
        if (!force && root.unsavedChanges && root.askBeforeLeaving && root.current && target.entry.id !== root.current.entry.id) {
            root.askBeforeLeaving(() => root.select(id, true));
            return true;
        }
        root.current = target;
        const topId = target.parent ? target.parent.id : target.entry.id;
        root.activeCategoryRow = -1;
        for (let i = 0; i < categoryModel.count; i++) if (categoryModel.get(i).entryId === topId) root.activeCategoryRow = i;
        if (target.parent) {
            if (!root.subCategoryEntry || root.subCategoryEntry.id !== target.parent.id) root.openSubCategory(target.parent.id);
            root.activeSubCategoryRow = target.parent.items.indexOf(target.entry);
        } else {
            root.subCategoryEntry = null;
            root.subCategoryTitle = "";
            subCategoryModel.clear();
            root.activeSubCategoryRow = -1;
        }
        rebuildSearch();
        return true;
    }
    function openPage(page) {
        const found = Catalog.find(page, root.label);
        return found ? root.select(found.entry.id, true) : false;
    }

    Component.onCompleted: rebuild()
}

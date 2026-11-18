// SPDX-FileCopyrightText: 2022-2026 vaxerski
// SPDX-License-Identifier: BSD-3-Clause
// Unmodified function excerpts from src/config/shared/actions/ConfigActions.cpp,
// Hyprland v0.56.2 (efb50993780079460b0cbed1363e2166a2de1d9f).
// Full license: ../../../../licenses/Hyprland-BSD-3-Clause.txt

static bool tryMoveFocusToMonitor(PHLMONITOR monitor) {
    if (!monitor)
        return false;

    const auto LASTMONITOR = Desktop::focusState()->monitor();
    if (!LASTMONITOR || LASTMONITOR == monitor)
        return false;

    static auto PFOLLOWMOUSE = CConfigValue<Config::INTEGER>("input:follow_mouse");
    static auto PNOWARPS     = CConfigValue<Config::INTEGER>("cursor:no_warps");

    g_pInputManager->unconstrainMouse();

    const auto PNEWMAINWORKSPACE = monitor->m_activeWorkspace;
    const auto PNEWWORKSPACE     = monitor->m_activeSpecialWorkspace ? monitor->m_activeSpecialWorkspace : PNEWMAINWORKSPACE;
    auto       PNEWWINDOW        = PNEWWORKSPACE->getFocusCandidate();

    if (PNEWWINDOW) {
        updateRelativeCursorCoords();
        Desktop::focusState()->fullWindowFocus(PNEWWINDOW, Desktop::FOCUS_REASON_KEYBIND);
        PNEWWINDOW->warpCursor();

        if (*PNOWARPS == 0 || *PFOLLOWMOUSE < 2) {
            g_pInputManager->m_forcedFocus = PNEWWINDOW;
            g_pInputManager->simulateMouseMovement();
            g_pInputManager->m_forcedFocus.reset();
        }
    } else {
        Desktop::focusState()->rawWindowFocus(nullptr, Desktop::FOCUS_REASON_KEYBIND);
        Pointer::pointerController()->warpTo(monitor->middle());
    }
    Desktop::focusState()->rawMonitorFocus(monitor);

    return true;
}

ActionResult Actions::focusMonitor(PHLMONITOR mon) {
    if (!mon)
        return actionError("Bad monitor", eActionErrorLevel::WARNING, eActionErrorCode::NO_TARGET);

    tryMoveFocusToMonitor(mon);

    return {};
}

ActionResult Actions::changeWorkspace(PHLWORKSPACE ws) {
    if (!ws)
        return actionError("Invalid workspace", eActionErrorLevel::WARNING, eActionErrorCode::NO_TARGET);

    static auto PHIDESPECIALONWORKSPACECHANGE = CConfigValue<Config::INTEGER>("binds:hide_special_on_workspace_change");
    static auto PWORKSPACECENTERON            = CConfigValue<Config::INTEGER>("binds:workspace_center_on");

    const auto  PMONITOR = Desktop::focusState()->monitor();
    if (!PMONITOR)
        return actionError("No focused monitor", eActionErrorLevel::WARNING, eActionErrorCode::INVALID_STATE);

    if (ws->m_isSpecialWorkspace) {
        PMONITOR->setSpecialWorkspace(ws);
        g_pInputManager->simulateMouseMovement();
        return {};
    }

    const auto PMONITORWORKSPACEOWNER = PMONITOR == ws->m_monitor ? PMONITOR : ws->m_monitor.lock();
    if (!PMONITORWORKSPACEOWNER)
        return actionError("Workspace has no monitor", eActionErrorLevel::WARNING, eActionErrorCode::INVALID_STATE);

    updateRelativeCursorCoords();

    Desktop::focusState()->rawMonitorFocus(PMONITORWORKSPACEOWNER);

    if (*PHIDESPECIALONWORKSPACECHANGE)
        PMONITORWORKSPACEOWNER->setSpecialWorkspace(nullptr);
    PMONITORWORKSPACEOWNER->changeWorkspace(ws, false, true);

    if (PMONITOR != PMONITORWORKSPACEOWNER) {
        Vector2D middle  = PMONITORWORKSPACEOWNER->middle();
        auto     pWindow = ws->getFocusCandidate();

        if (pWindow) {
            Desktop::focusState()->fullWindowFocus(pWindow, Desktop::FOCUS_REASON_KEYBIND);
            if (*PWORKSPACECENTERON == 1)
                middle = pWindow->middle();
        } else
            Desktop::focusState()->rawWindowFocus(nullptr, Desktop::FOCUS_REASON_KEYBIND);

        Pointer::pointerController()->warpTo(middle);
    }

    if (!g_pInputManager->m_lastFocusOnLS) {
        if (Desktop::focusState()->surface())
            g_pInputManager->sendMotionEventsToFocused();
        else
            g_pInputManager->simulateMouseMovement();
    }

    const static auto PWARPONWORKSPACECHANGE = CConfigValue<Config::INTEGER>("cursor:warp_on_change_workspace");

    if (*PWARPONWORKSPACECHANGE > 0) {
        auto PLAST     = ws->getLastFocusedWindow();
        auto HLSurface = Desktop::View::CWLSurface::fromResource(g_pSeatManager->m_state.pointerFocus.lock());

        if (PLAST && (!HLSurface || HLSurface->view()->type() == Desktop::View::VIEW_TYPE_WINDOW))
            PLAST->warpCursor(*PWARPONWORKSPACECHANGE == 2);
    }

    return {};
}

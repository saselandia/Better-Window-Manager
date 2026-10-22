#define WLR_USE_UNSTABLE

#include <unistd.h>

#include <any>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/config/ConfigManager.hpp>
#include <hyprland/src/config/shared/parserUtils/ParserUtils.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <hyprland/src/desktop/rule/windowRule/WindowRuleEffectContainer.hpp>
#include <hyprland/src/config/lua/bindings/LuaBindingsInternal.hpp>
#include <hyprland/src/config/lua/types/LuaConfigColor.hpp>

#include <hyprutils/string/VarList.hpp>

#include <algorithm>

#include "barDeco.hpp"
#include "SnapHelper.hpp"
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/managers/KeybindManager.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include "globals.hpp"

extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

// Do NOT change this function.
APICALL EXPORT std::string PLUGIN_API_VERSION() {
    return HYPRLAND_API_VERSION;
}

static void onNewWindow(PHLWINDOW window) {
    if (!validMapped(window))
        return;

    if (std::ranges::any_of(window->m_windowDecorations, [](const auto& d) { return d->getDisplayName() == "Hyprbar"; }))
        return;

    auto bar = makeUnique<CHyprBar>(window);
    g_pGlobalState->bars.emplace_back(bar);
    bar->m_self = bar;
    HyprlandAPI::addWindowDecoration(PHANDLE, window, std::move(bar));
}

static void onPreConfigReload() {
    g_pGlobalState->buttons.clear();
}

static void onConfigReloaded() {
    for (auto& b : g_pGlobalState->bars) {
        if (!b)
            continue;

        b->onConfigReloaded();
    }
}

static void onUpdateWindowRules(PHLWINDOW window) {
    const auto BARIT = std::find_if(g_pGlobalState->bars.begin(), g_pGlobalState->bars.end(), [window](const auto& bar) { return bar->getOwner() == window; });

    if (BARIT == g_pGlobalState->bars.end())
        return;

    (*BARIT)->updateRules();
    window->updateWindowDecos();
}

Hyprlang::CParseResult onNewButton(const char* K, const char* V) {
    std::string                 v = V;
    Hyprutils::String::CVarList vars(v);

    Hyprlang::CParseResult      result;

    // hyprbars-button = bgcolor, size, icon, action, fgcolor

    if (vars[0].empty() || vars[1].empty()) {
        result.setError("bgcolor and size cannot be empty");
        return result;
    }

    float size = 10;
    try {
        size = std::stof(vars[1]);
    } catch (std::exception& e) {
        result.setError("failed to parse size");
        return result;
    }

    bool userfg  = false;
    auto fgcolor = Config::ParserUtils::parseColor("rgb(ffffff)");
    auto bgcolor = Config::ParserUtils::parseColor(vars[0]);

    if (!bgcolor) {
        result.setError("invalid bgcolor");
        return result;
    }

    if (vars.size() == 5) {
        userfg  = true;
        fgcolor = Config::ParserUtils::parseColor(vars[4]);
    }

    if (!fgcolor) {
        result.setError("invalid fgcolor");
        return result;
    }

    g_pGlobalState->buttons.push_back(SHyprButton{vars[3], userfg, *fgcolor, *bgcolor, size, vars[2]});

    for (auto& b : g_pGlobalState->bars) {
        b->m_bButtonsDirty = true;
    }

    return result;
}

int newLuaButton(lua_State* L) {
    if (!lua_istable(L, 1))
        return Config::Lua::Bindings::Internal::configError(L, "add_button: expected a table { bg_color, fg_color, size, icon, action }");

    SHyprButton button;

    {
        Hyprutils::Utils::CScopeGuard x([L] { lua_pop(L, 1); });

        lua_getfield(L, 1, "bg_color");

        Config::Lua::CLuaConfigColor parser(0);
        auto                         err = parser.parse(L);
        if (err.errorCode != Config::Lua::PARSE_ERROR_OK)
            return Config::Lua::Bindings::Internal::configError(L, "add_button: failed to parse bg_color");

        button.bgcol = parser.parsed();
    }

    {
        Hyprutils::Utils::CScopeGuard x([L] { lua_pop(L, 1); });

        lua_getfield(L, 1, "fg_color");

        Config::Lua::CLuaConfigColor parser(0);
        auto                         err = parser.parse(L);
        if (err.errorCode != Config::Lua::PARSE_ERROR_OK)
            return Config::Lua::Bindings::Internal::configError(L, "add_button: failed to parse fg_color");

        button.fgcol = parser.parsed();
    }

    {
        Hyprutils::Utils::CScopeGuard x([L] { lua_pop(L, 1); });

        lua_getfield(L, 1, "size");

        if (!lua_isnumber(L, -1))
            return Config::Lua::Bindings::Internal::configError(L, "add_button: size must be an integer");

        button.size = lua_tointeger(L, -1);
    }

    {
        Hyprutils::Utils::CScopeGuard x([L] { lua_pop(L, 1); });

        lua_getfield(L, 1, "icon");

        if (!lua_isstring(L, -1))
            return Config::Lua::Bindings::Internal::configError(L, "add_button: icon must be a string");

        button.icon = lua_tostring(L, -1);
    }

    {
        Hyprutils::Utils::CScopeGuard x([L] { lua_pop(L, 1); });

        lua_getfield(L, 1, "action");

        if (!lua_isstring(L, -1))
            return Config::Lua::Bindings::Internal::configError(L, "add_button: action must be a string");

        button.cmd = lua_tostring(L, -1);
    }

    g_pGlobalState->buttons.push_back(std::move(button));

    for (auto& b : g_pGlobalState->bars) {
        b->m_bButtonsDirty = true;
    }

    return 0;
}


static bool         s_bAltDragging       = false;
static PHLWINDOWREF s_pAltDraggedWindow;
static PHLWINDOWREF s_pNativeDraggedWindow;
static bool         s_bHasLastDraggedBox = false;
static CBox         s_lastDraggedBox;

static void onGlobalMouseMove(const Vector2D& coords) {
    const Vector2D mousePos = g_pInputManager->getMouseCoordsInternal();

    PHLWINDOW draggedWin = s_bAltDragging ? s_pAltDraggedWindow.lock() : nullptr;
    bool      barHandled = false;

    if (g_pGlobalState) {
        for (const auto& bar : g_pGlobalState->bars) {
            if (bar && bar->isDragging()) {
                if (!draggedWin)
                    draggedWin = bar->getOwner();
                barHandled = true;
                break;
            }
        }
    }

    if (!draggedWin && g_layoutManager && g_layoutManager->dragController()) {
        if (g_layoutManager->dragController()->mode() == MBIND_MOVE) {
            if (auto target = g_layoutManager->dragController()->target()) {
                draggedWin = target->window();
                if (!barHandled && !s_bAltDragging)
                    s_pNativeDraggedWindow = draggedWin;
            }
        }
    }

    if (validMapped(draggedWin)) {
        if (s_bHasLastDraggedBox)
            g_pHyprRenderer->damageBox(s_lastDraggedBox);

        g_pHyprRenderer->damageWindow(draggedWin, true);
        CBox curBox = draggedWin->layoutTarget()->position();
        curBox.expand(48);
        s_lastDraggedBox     = curBox;
        s_bHasLastDraggedBox = true;

        updateSnapPreview(mousePos);
    } else {
        if (s_bHasLastDraggedBox) {
            g_pHyprRenderer->damageBox(s_lastDraggedBox);
            s_bHasLastDraggedBox = false;
        }
        if (g_bSnapPreviewActive)
            hideSnapPreview();
    }
}

static void onGlobalMouseButton(Event::SCallbackInfo& info, IPointer::SButtonEvent e) {
    const auto MODS = g_pInputManager->getModsFromAllKBs();
    const auto ALTMASK = g_pKeybindManager->stringToModMask("ALT");
    const auto SUPERMASK = g_pKeybindManager->stringToModMask("SUPER");

    if (e.button == BTN_LEFT) {
        if (e.state == WL_POINTER_BUTTON_STATE_PRESSED) {
            if ((MODS & ALTMASK) != 0 || (MODS & SUPERMASK) != 0) {
                auto pWindow = g_pCompositor->vectorToWindowUnified(
                    g_pInputManager->getMouseCoordsInternal(),
                    Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS | Desktop::View::ALLOW_FLOATING);
                if (!pWindow)
                    pWindow = Desktop::focusState()->window();

                if (validMapped(pWindow)) {
                    s_bAltDragging = true;
                    s_pAltDraggedWindow = pWindow;

                    CBox curBox = pWindow->layoutTarget()->position();
                    bool wasFullscreen = pWindow->isFullscreen();
                    bool wasSnapped = pWindow->m_ruleApplicator && pWindow->m_ruleApplicator->m_tagKeeper.isTagged("snapped");

                    g_pHyprRenderer->damageWindow(pWindow, true);

                    if (wasFullscreen)
                        g_pCompositor->setWindowFullscreenInternal(pWindow, FSMODE_NONE);

                    Config::Actions::clearTags(pWindow);
                    pWindow->updateWindowData();

                    if (wasSnapped || wasFullscreen) {
                        Vector2D targetSize = pWindow->layoutTarget()->position().size();
                        if (wasSnapped) {
                            auto optSize = getAndConsumePreSnapSize(pWindow);
                            targetSize = optSize.value_or(Vector2D{900, 600});
                        }

                        Vector2D mousePos = g_pInputManager->getMouseCoordsInternal();
                        float ratioX = curBox.w > 0 ? std::clamp((double)((mousePos.x - curBox.x) / curBox.w), 0.05, 0.95) : 0.5f;
                        float ratioY = curBox.h > 0 ? std::clamp((double)((mousePos.y - curBox.y) / curBox.h), 0.05, 0.95) : 0.5f;

                        Vector2D newPos = {mousePos.x - targetSize.x * ratioX, mousePos.y - targetSize.y * ratioY};
                        CBox newBox = {newPos.round(), targetSize};

                        pWindow->layoutTarget()->setPositionGlobal(newBox);
                        g_layoutManager->setTargetGeom(newBox, pWindow->layoutTarget());
                        pWindow->layoutTarget()->warpPositionSize();
                        pWindow->updateWindowDecos();
                        g_pHyprRenderer->damageWindow(pWindow, true);
                    }
                }
            }
        } else {
            // Button release
            if (s_bHasLastDraggedBox) {
                g_pHyprRenderer->damageBox(s_lastDraggedBox);
                s_bHasLastDraggedBox = false;
            }
            hideSnapPreview();
            if (s_bAltDragging) {
                s_bAltDragging = false;
                auto pWin = s_pAltDraggedWindow.lock();
                s_pAltDraggedWindow.reset();
                s_pNativeDraggedWindow.reset();
                if (g_layoutManager && g_layoutManager->dragController() && g_layoutManager->dragController()->mode() == MBIND_MOVE)
                    g_pKeybindManager->changeMouseBindMode(MBIND_INVALID);
                if (validMapped(pWin)) {
                    checkAndTriggerEdgeSnap(pWin, g_pInputManager->getMouseCoordsInternal());
                }
            } else if (auto pNativeWin = s_pNativeDraggedWindow.lock()) {
                s_pNativeDraggedWindow.reset();
                bool anyBarDragging = false;
                if (g_pGlobalState) {
                    for (const auto& bar : g_pGlobalState->bars) {
                        if (bar && bar->isDragging()) {
                            anyBarDragging = true;
                            break;
                        }
                    }
                }
                if (!anyBarDragging && validMapped(pNativeWin)) {
                    if (g_layoutManager && g_layoutManager->dragController() && g_layoutManager->dragController()->mode() == MBIND_MOVE)
                        g_pKeybindManager->changeMouseBindMode(MBIND_INVALID);
                    checkAndTriggerEdgeSnap(pNativeWin, g_pInputManager->getMouseCoordsInternal());
                }
            }
        }
    } else if (e.button == BTN_RIGHT) {
        if (e.state == WL_POINTER_BUTTON_STATE_PRESSED && (MODS & ALTMASK) != 0) {
            auto pWindow = g_pCompositor->vectorToWindowUnified(
                g_pInputManager->getMouseCoordsInternal(),
                Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS | Desktop::View::ALLOW_FLOATING);
            if (!pWindow)
                pWindow = Desktop::focusState()->window();

            if (validMapped(pWindow)) {
                Config::Actions::clearTags(pWindow);
                pWindow->updateWindowData();
            }
        }
    }
}

APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    PHANDLE = handle;

    const std::string HASH        = __hyprland_api_get_hash();
    const std::string CLIENT_HASH = __hyprland_api_get_client_hash();

    if (HASH != CLIENT_HASH) {
        HyprlandAPI::addNotification(PHANDLE, "[hyprbars] Failure in initialization: Version mismatch (headers ver is not equal to running hyprland ver)",
                                     CHyprColor{1.0, 0.2, 0.2, 1.0}, 5000);
        throw std::runtime_error("[hb] Version mismatch");
    }


    g_pGlobalState                    = makeUnique<SGlobalState>();
    g_pGlobalState->nobarRuleIdx      = Desktop::Rule::windowEffects()->registerEffect("hyprbars:no_bar");
    g_pGlobalState->barColorRuleIdx   = Desktop::Rule::windowEffects()->registerEffect("hyprbars:bar_color");
    g_pGlobalState->titleColorRuleIdx = Desktop::Rule::windowEffects()->registerEffect("hyprbars:title_color");

    static auto P  = Event::bus()->m_events.window.open.listen([&](PHLWINDOW w) { onNewWindow(w); });
    static auto P3 = Event::bus()->m_events.window.updateRules.listen([&](PHLWINDOW w) { onUpdateWindowRules(w); });
    static auto P_GlobalMouse = Event::bus()->m_events.input.mouse.button.listen([&](IPointer::SButtonEvent e, Event::SCallbackInfo& info) { onGlobalMouseButton(info, e); });
    static auto P_GlobalMouseMove = Event::bus()->m_events.input.mouse.move.listen([&](Vector2D coords, Event::SCallbackInfo& info) { onGlobalMouseMove(coords); });
    static auto P_Render = Event::bus()->m_events.render.stage.listen([&](eRenderStage stage) { renderSnapPreviewOverlay(stage); });

    g_pGlobalState->config.barColor            = makeShared<Config::Values::CColorValue>("plugin:hyprbars:bar_color", "Change the bar color", 0x88333333);
    g_pGlobalState->config.textColor           = makeShared<Config::Values::CColorValue>("plugin:hyprbars:col.text", "Change the text color", 0xffffffff);
    g_pGlobalState->config.inactiveButtonColor = makeShared<Config::Values::CColorValue>(
        "plugin:hyprbars:inactive_button_color", "Change the inactive button's color. 0x00000000 means unset", 0x00000000);
    g_pGlobalState->config.barHeight       = makeShared<Config::Values::CIntValue>("plugin:hyprbars:bar_height", "Change the bar's height", 15);
    g_pGlobalState->config.barTextSize     = makeShared<Config::Values::CIntValue>("plugin:hyprbars:bar_text_size", "Change the bar's text size", 10);
    g_pGlobalState->config.barTitleEnabled = makeShared<Config::Values::CBoolValue>("plugin:hyprbars:bar_title_enabled", "Whether to enable titles in the bar", true);
    g_pGlobalState->config.barBlur         = makeShared<Config::Values::CBoolValue>("plugin:hyprbars:bar_blur", "Whether to enable blur of the bar", false);
    g_pGlobalState->config.barTextFont     = makeShared<Config::Values::CStringValue>("plugin:hyprbars:bar_text_font", "Bar's text font", "Sans");
    g_pGlobalState->config.barTextAlign    = makeShared<Config::Values::CStringValue>("plugin:hyprbars:bar_text_align", "Bar's text alignment", "center");
    g_pGlobalState->config.barPartOfWindow =
        makeShared<Config::Values::CBoolValue>("plugin:hyprbars:bar_part_of_window", "Whether the bar is a part of the window (reserves space)", true);
    g_pGlobalState->config.barPrecedenceOverBorder =
        makeShared<Config::Values::CBoolValue>("plugin:hyprbars:bar_precedence_over_border", "Whether the bar is before, or after the border", false);
    g_pGlobalState->config.barButtonsAlignment = makeShared<Config::Values::CStringValue>("plugin:hyprbars:bar_buttons_alignment", "Alignment of the bar buttons", "right");
    g_pGlobalState->config.barPadding          = makeShared<Config::Values::CIntValue>("plugin:hyprbars:bar_padding", "Padding of the bar", 7);
    g_pGlobalState->config.barButtonPadding    = makeShared<Config::Values::CIntValue>("plugin:hyprbars:bar_button_padding", "Padding of the bar buttons", 5);
    g_pGlobalState->config.enabled             = makeShared<Config::Values::CBoolValue>("plugin:hyprbars:enabled", "Whether bars are enabled", true);
    g_pGlobalState->config.iconOnHover         = makeShared<Config::Values::CBoolValue>("plugin:hyprbars:icon_on_hover", "Whether to use an icon on hover of the buttons", false);
    g_pGlobalState->config.onDoubleClick       = makeShared<Config::Values::CStringValue>("plugin:hyprbars:on_double_click", "Action to execute on double click of the bar", "");

    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.textColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.inactiveButtonColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barHeight);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barTextSize);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barTitleEnabled);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barBlur);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barTextFont);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barTextAlign);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barPartOfWindow);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barPrecedenceOverBorder);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barButtonsAlignment);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barPadding);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barButtonPadding);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.enabled);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.iconOnHover);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.onDoubleClick);

    if (Config::mgr()->type() == Config::CONFIG_LEGACY)
        HyprlandAPI::addConfigKeyword(PHANDLE, "plugin:hyprbars:hyprbars-button", onNewButton, Hyprlang::SHandlerOptions{});
    else
        HyprlandAPI::addLuaFunction(PHANDLE, "hyprbars", "add_button", ::newLuaButton);
    static auto P4 = Event::bus()->m_events.config.preReload.listen([&] { onPreConfigReload(); });
    static auto P5 = Event::bus()->m_events.config.reloaded.listen([&] { onConfigReloaded(); });

    // add deco to existing windows
    for (auto& w : g_pCompositor->m_windows) {
        if (w->isHidden() || !w->m_isMapped)
            continue;

        onNewWindow(w);
    }

    HyprlandAPI::reloadConfig();

    return {"hyprbars", "A plugin to add title bars to windows.", "Vaxry", "1.0"};
}

APICALL EXPORT void PLUGIN_EXIT() {
    for (auto& m : g_pCompositor->m_monitors)
        m->m_scheduledRecalc = true;

    g_pHyprRenderer->m_renderPass.removeAllOfType("CBarPassElement");

    Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->barColorRuleIdx);
    Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->titleColorRuleIdx);
    Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->nobarRuleIdx);
}

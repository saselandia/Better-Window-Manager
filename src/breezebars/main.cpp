#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#define WLR_USE_UNSTABLE

#include <unistd.h>
#include <elf.h>
#include </usr/include/link.h>
#include <dlfcn.h>

#define protected public
#include <hyprutils/signal/Signal.hpp>
#undef protected

#include <any>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/state/ViewState.hpp>
#include <hyprland/src/desktop/state/ViewHitTester.hpp>
#include <hyprland/src/state/MonitorState.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
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
#include <set>

#include "barDeco.hpp"
#include "CSDDetect.hpp"
#include "SquareTop.hpp"
#include "SnapHelper.hpp"
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/managers/KeybindManager.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include "globals.hpp"
#include "DecoClient.hpp"
#include "barRemote.hpp"

extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

// Quita sólo las etiquetas de encaje (snapped, snapped_<borde>, quick-tile.py). Antes se borraban
// todas las de la ventana, también las que ponen otros (reglas, scripts, modos de workspace).
static void clearSnapTags(PHLWINDOW window) {
    if (!window || !window->m_ruleApplicator)
        return;
    std::vector<std::string> snapTags;
    for (auto tag : window->m_ruleApplicator->m_tagKeeper.getTags()) {
        if (tag.ends_with('*'))
            continue; // las de reglas no se quitan a mano
        if (tag == "snapped" || tag.starts_with("snapped_"))
            snapTags.push_back(tag);
    }
    for (const auto& tag : snapTags)
        Config::Actions::tag("-" + tag, window);
}

// Do NOT change this function.
APICALL EXPORT std::string PLUGIN_API_VERSION() {
    return HYPRLAND_API_VERSION;
}

static void onNewWindow(PHLWINDOW window) {
    if (!g_pGlobalState || !Desktop::View::validMapped(window))
        return;

    if (std::ranges::any_of(window->m_windowDecorations, [](const auto& d) { return d->getDisplayName() == "Breezebar"; }))
        return;

    auto bar = makeUnique<CHyprBar>(window);
    g_pGlobalState->bars.emplace_back(bar);
    bar->m_self = bar;
    WP<CHyprBar> weak = bar;
    HyprlandAPI::addWindowDecoration(PHANDLE, window, std::move(bar));
    // Sombra de la decoración de KDE (sólo se dibuja con bwm-decorator)
    HyprlandAPI::addWindowDecoration(PHANDLE, window, makeUnique<CBreezeShadow>(window, weak));
}

// F7: one authoritative frame snapshot for IPC and placement.lua. Addresses always carry PID.
struct SFrameSnapshot {
    SDecoDetection detection;
    bool visible=false;
    double left=0,top=0,right=0,bottom=0;
    std::string kind="none";
};
static SFrameSnapshot frameSnapshot(PHLWINDOW w) {
    SFrameSnapshot s;s.detection=detectDecorations(w);
    if(!g_pGlobalState||!g_pGlobalState->config.enabled->value())return s;
    for(auto& b:g_pGlobalState->bars)if(b&&b->getOwner()==w) {
        b->updateRules();s.visible=!b->m_hidden;
        if(s.visible) {
            const auto info=b->getPositioningInfo();
            s.left=info.desiredExtents.topLeft.x;s.top=info.desiredExtents.topLeft.y;
            s.right=info.desiredExtents.bottomRight.x;s.bottom=info.desiredExtents.bottomRight.y;
            s.kind=b->remoteActive()?"kde":"flat";
        }
        break;
    }
    return s;
}
static std::string csdReport(eHyprCtlOutputFormat format,std::string) {
    const bool json=format==FORMAT_JSON;
    std::string out=json?"{\"version\":1,\"api\":\"breezebars-csd\",\"enabled\":"+std::string(g_pGlobalState->config.enabled->value()?"true":"false")+",\"windows\":[":std::format("bwm-decorator: {} | csd-api=1\n",g_pDecoClient?g_pDecoClient->status():"no client");
    bool first=true;
    for(auto& w:Desktop::windowState()->windows()) {
        if(!w->m_isMapped)continue;
        auto s=frameSnapshot(w);const auto& d=s.detection;
        const auto address=std::format("0x{:x}",reinterpret_cast<uintptr_t>(w.get()));
        auto reason=!g_pGlobalState->config.enabled->value()?"skin inactive: breezebars disabled":d.reason;
        if(json) {
            if(!first)out+=",";first=false;
            out+=std::format(R"({{"address":"{}","pid":{},"class":"{}","title":"{}","visible":{},"ready":{},"reason":"{}","kind":"{}","xdgRequested":{},"kdeRequested":{},"sent":{},"applied":{},"observed":{{"x11":{},"xdg":{},"kde":{},"kdeExplicit":{},"gtkFrameExtents":{},"motifNoBorder":{},"special":{},"noBar":{},"decorate":{},"fullscreen":{}}},"borders":{{"left":{},"top":{},"right":{},"bottom":{}}}}})",
                address,w->getPID(),escapeJSONStrings(w->m_class),escapeJSONStrings(w->m_title),s.visible,d.ready,escapeJSONStrings(reason),s.kind,d.xdgRequested,d.kdeRequested,d.sent,d.applied,d.observed.x11,d.observed.xdg,d.observed.kde,d.observed.kdeExplicit,d.observed.gtkFrameExtents,d.observed.motifNoBorder,d.observed.overrideRedirect||d.observed.x11Special,d.observed.noBar,d.observed.decorate,d.observed.fullscreen,s.left,s.top,s.right,s.bottom);
        } else out+=std::format("{} | {} | barra={} ({}) | address={} pid={} | xdg={} kde={} sent={} applied={} | {}\n",w->m_class,w->m_title.substr(0,40),s.visible?"si":"no",s.kind,address,w->getPID(),d.xdgRequested,d.kdeRequested,d.sent,d.applied,reason);
    }
    if(json)out+="]}";
    return out;
}
static int luaDecoration(lua_State* L) {
    const std::string address=luaL_checkstring(L,1);
    const pid_t pid=lua_gettop(L)>1?luaL_checkinteger(L,2):0;
    for(auto& w:Desktop::windowState()->windows()) {
        if(!w->m_isMapped||std::format("0x{:x}",reinterpret_cast<uintptr_t>(w.get()))!=address||(pid&&w->getPID()!=pid))continue;
        // Lua window.open listeners may run before the plugin's open listener. Attach once first.
        onNewWindow(w);
        auto s=frameSnapshot(w);
        lua_newtable(L);
        lua_pushboolean(L,s.visible);lua_setfield(L,-2,"visible");
        lua_pushboolean(L,s.detection.ready);lua_setfield(L,-2,"ready");
        lua_pushinteger(L,w->getPID());lua_setfield(L,-2,"pid");
        lua_pushstring(L,s.detection.reason.c_str());lua_setfield(L,-2,"reason");
        lua_newtable(L);
        for(auto [key,value]:{std::pair{"left",s.left},{"top",s.top},{"right",s.right},{"bottom",s.bottom}}) {lua_pushnumber(L,value);lua_setfield(L,-2,key);}
        lua_setfield(L,-2,"borders");return 1;
    }
    lua_pushnil(L);return 1;
}

static void onPreConfigReload() {
    if (!g_pGlobalState)
        return;
    g_pGlobalState->buttons.clear();
}

static void onConfigReloaded() {
    if (!g_pGlobalState)
        return;
    for (auto& b : g_pGlobalState->bars) {
        if (!b)
            continue;

        b->onConfigReloaded();
    }
}

static void onUpdateWindowRules(PHLWINDOW window) {
    if (!g_pGlobalState)
        return;
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

    SHyprButton button{vars[3], userfg, *fgcolor, *bgcolor, size, vars[2]};
    if (button.icon.starts_with("breeze:"))
        button.breezeKind = button.icon.substr(7);
    g_pGlobalState->buttons.push_back(std::move(button));

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
        if (button.icon.starts_with("breeze:"))
            button.breezeKind = button.icon.substr(7);
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

    if (Desktop::View::validMapped(draggedWin)) {
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
                auto pWindow = Desktop::CViewHitTester{*Desktop::viewState()}.windowAt(
                    g_pInputManager->getMouseCoordsInternal(),
                    Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS | Desktop::View::ALLOW_FLOATING);
                if (!pWindow)
                    pWindow = Desktop::focusState()->window();

                if (Desktop::View::validMapped(pWindow)) {
                    s_bAltDragging = true;
                    s_pAltDraggedWindow = pWindow;

                    CBox curBox = pWindow->layoutTarget()->position();
                    bool wasFullscreen = Fullscreen::controller()->isFullscreen(pWindow);
                    bool wasSnapped = pWindow->m_ruleApplicator && pWindow->m_ruleApplicator->m_tagKeeper.isTagged("snapped");

                    g_pHyprRenderer->damageWindow(pWindow, true);

                    if (wasFullscreen)
                        Fullscreen::controller()->setFullscreenMode(pWindow, Fullscreen::FSMODE_NONE);

                    clearSnapTags(pWindow);
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
                if (Desktop::View::validMapped(pWin)) {
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
                if (!anyBarDragging && Desktop::View::validMapped(pNativeWin)) {
                    if (g_layoutManager && g_layoutManager->dragController() && g_layoutManager->dragController()->mode() == MBIND_MOVE)
                        g_pKeybindManager->changeMouseBindMode(MBIND_INVALID);
                    checkAndTriggerEdgeSnap(pNativeWin, g_pInputManager->getMouseCoordsInternal());
                }
            }
        }
    } else if (e.button == BTN_RIGHT) {
        if (e.state == WL_POINTER_BUTTON_STATE_PRESSED && (MODS & ALTMASK) != 0) {
            auto pWindow = Desktop::CViewHitTester{*Desktop::viewState()}.windowAt(
                g_pInputManager->getMouseCoordsInternal(),
                Desktop::View::RESERVED_EXTENTS | Desktop::View::INPUT_EXTENTS | Desktop::View::ALLOW_FLOATING);
            if (!pWindow)
                pWindow = Desktop::focusState()->window();

            if (Desktop::View::validMapped(pWindow)) {
                clearSnapTags(pWindow);
                pWindow->updateWindowData();
            }
        }
    }
}

static void cleanupLegacyPinnedModule() {
    std::set<std::pair<void*, void*>> activePairs;
    auto collectFrom = [&](auto& sig) {
        for (const auto& w : sig.m_vListeners) {
            if (w.impl_ && w.m_data)
                activePairs.insert({(void*)w.impl_, w.m_data});
        }
    };

    if (Event::bus()) {
        collectFrom(Event::bus()->m_events.window.open);
        collectFrom(Event::bus()->m_events.window.updateRules);
        collectFrom(Event::bus()->m_events.input.mouse.button);
        collectFrom(Event::bus()->m_events.input.mouse.move);
        collectFrom(Event::bus()->m_events.render.stage);
        collectFrom(Event::bus()->m_events.config.preReload);
        collectFrom(Event::bus()->m_events.config.reloaded);
    }

    dl_iterate_phdr(
        [](struct dl_phdr_info* info, size_t, void* data) -> int {
            if (!info->dlpi_name || std::string(info->dlpi_name).find("hyprbars") == std::string::npos)
                return 0;

            uintptr_t selfAddr = (uintptr_t)&cleanupLegacyPinnedModule;
            for (int i = 0; i < info->dlpi_phnum; ++i) {
                const auto& ph = info->dlpi_phdr[i];
                if (ph.p_type == PT_LOAD) {
                    uintptr_t start = info->dlpi_addr + ph.p_vaddr;
                    uintptr_t end   = start + ph.p_memsz;
                    if (selfAddr >= start && selfAddr < end)
                        return 0; // Skip our own module
                }
            }

            auto* pairs = static_cast<std::set<std::pair<void*, void*>>*>(data);
            for (int i = 0; i < info->dlpi_phnum; ++i) {
                const auto& ph = info->dlpi_phdr[i];
                if (ph.p_type == PT_LOAD && (ph.p_flags & PF_W)) {
                    uintptr_t start = info->dlpi_addr + ph.p_vaddr;
                    uintptr_t end   = start + ph.p_memsz;
                    for (uintptr_t addr = (start + 7) & ~uintptr_t(7); addr + sizeof(CHyprSignalListener) <= end; addr += 8) {
                        auto* cand = reinterpret_cast<CHyprSignalListener*>(addr);
                        if (cand->impl_ && cand->m_data && pairs->contains({(void*)cand->impl_, cand->m_data})) {
                            cand->reset();
                        }
                    }
                }
            }
            return 0;
        },
        &activePairs);
}

APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    PHANDLE = handle;

    const std::string HASH        = __hyprland_api_get_hash();
    const std::string CLIENT_HASH = __hyprland_api_get_client_hash();

    if (HASH != CLIENT_HASH) {
        HyprlandAPI::addNotification(PHANDLE, "[breezebars] Failure in initialization: Version mismatch (headers ver is not equal to running hyprland ver)",
                                     CHyprColor{1.0, 0.2, 0.2, 1.0}, 5000);
        throw std::runtime_error("[hb] Version mismatch");
    }

    cleanupLegacyPinnedModule();

    g_pGlobalState                    = makeUnique<SGlobalState>();
    g_pGlobalState->nobarRuleIdx      = Desktop::Rule::windowEffects()->registerEffect("breezebars:no_bar");
    g_pGlobalState->barColorRuleIdx   = Desktop::Rule::windowEffects()->registerEffect("breezebars:bar_color");
    g_pGlobalState->titleColorRuleIdx = Desktop::Rule::windowEffects()->registerEffect("breezebars:title_color");

    g_pGlobalState->pOpenListener        = Event::bus()->m_events.window.open.listen([](PHLWINDOW w) { onNewWindow(w); });
    g_pGlobalState->pUpdateRulesListener = Event::bus()->m_events.window.updateRules.listen([](PHLWINDOW w) { onUpdateWindowRules(w); });
    g_pGlobalState->pMouseButtonListener = Event::bus()->m_events.input.mouse.button.listen([](IPointer::SButtonEvent e, Event::SCallbackInfo& info) { onGlobalMouseButton(info, e); });
    g_pGlobalState->pMouseMoveListener   = Event::bus()->m_events.input.mouse.move.listen([](Vector2D coords, Event::SCallbackInfo& info) { onGlobalMouseMove(coords); });
    g_pGlobalState->pRenderListener      = Event::bus()->m_events.render.stage.listen([](eRenderStage stage) {
        if (stage == RENDER_POST_WINDOWS)
            squareBarredWindowTops();
        renderSnapPreviewOverlay(stage);
        renderDecorationToolTip(stage);
    });

    g_pGlobalState->config.barColor            = makeShared<Config::Values::CColorValue>("plugin:breezebars:bar_color", "Change the bar color", 0x88333333);
    g_pGlobalState->config.textColor           = makeShared<Config::Values::CColorValue>("plugin:breezebars:col.text", "Change the text color", 0xffffffff);
    g_pGlobalState->config.inactiveButtonColor = makeShared<Config::Values::CColorValue>(
        "plugin:breezebars:inactive_button_color", "Change the inactive button's color. 0x00000000 means unset", 0x00000000);
    g_pGlobalState->config.inactiveBarColor =
        makeShared<Config::Values::CColorValue>("plugin:breezebars:inactive_bar_color", "Bar color of unfocused windows. 0x00000000 means same as bar_color", 0x00000000);
    g_pGlobalState->config.inactiveTextColor =
        makeShared<Config::Values::CColorValue>("plugin:breezebars:col.inactive_text", "Title/icon color of unfocused windows. 0x00000000 means same as col.text", 0x00000000);
    g_pGlobalState->config.barHeight       = makeShared<Config::Values::CIntValue>("plugin:breezebars:bar_height", "Change the bar's height", 15);
    g_pGlobalState->config.barTextSize     = makeShared<Config::Values::CIntValue>("plugin:breezebars:bar_text_size", "Change the bar's text size", 10);
    g_pGlobalState->config.barTitleEnabled = makeShared<Config::Values::CBoolValue>("plugin:breezebars:bar_title_enabled", "Whether to enable titles in the bar", true);
    g_pGlobalState->config.barBlur         = makeShared<Config::Values::CBoolValue>("plugin:breezebars:bar_blur", "Whether to enable blur of the bar", false);
    g_pGlobalState->config.barTextFont     = makeShared<Config::Values::CStringValue>("plugin:breezebars:bar_text_font", "Bar's text font", "Sans");
    g_pGlobalState->config.barTextAlign    = makeShared<Config::Values::CStringValue>("plugin:breezebars:bar_text_align", "Bar's text alignment", "center");
    g_pGlobalState->config.barPartOfWindow =
        makeShared<Config::Values::CBoolValue>("plugin:breezebars:bar_part_of_window", "Whether the bar is a part of the window (reserves space)", true);
    g_pGlobalState->config.barPrecedenceOverBorder =
        makeShared<Config::Values::CBoolValue>("plugin:breezebars:bar_precedence_over_border", "Whether the bar is before, or after the border", false);
    g_pGlobalState->config.barButtonsAlignment = makeShared<Config::Values::CStringValue>("plugin:breezebars:bar_buttons_alignment", "Alignment of the bar buttons", "right");
    g_pGlobalState->config.barPadding          = makeShared<Config::Values::CIntValue>("plugin:breezebars:bar_padding", "Padding of the bar", 7);
    g_pGlobalState->config.barButtonPadding    = makeShared<Config::Values::CIntValue>("plugin:breezebars:bar_button_padding", "Padding of the bar buttons", 5);
    g_pGlobalState->config.enabled             = makeShared<Config::Values::CBoolValue>("plugin:breezebars:enabled", "Whether bars are enabled", true);
    g_pGlobalState->config.iconOnHover         = makeShared<Config::Values::CBoolValue>("plugin:breezebars:icon_on_hover", "Whether to use an icon on hover of the buttons", false);
    g_pGlobalState->config.onDoubleClick       = makeShared<Config::Values::CStringValue>("plugin:breezebars:on_double_click", "Action to execute on double click of the bar", "");
    g_pGlobalState->config.onWheel             = makeShared<Config::Values::CStringValue>(
        "plugin:breezebars:on_wheel", "Mouse wheel on the title bar, as kwinrc CommandTitlebarWheel (Raise/Lower, Maximize/Restore, Previous/Next Desktop, Nothing)", "Nothing");

    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.barColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.textColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.inactiveButtonColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.inactiveBarColor);
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.inactiveTextColor);
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
    HyprlandAPI::addConfigValueV2(PHANDLE, g_pGlobalState->config.onWheel);

    // Conexión con bwm-decorator (decoraciones de KDE). Nunca bloquea: si no está, barra plana.
    g_pDecoClient = std::make_unique<CDecoClient>();
    // Cambiar de ventana activa o de título repinta las barras (y así se envía el estado nuevo)
    g_pGlobalState->pActiveListener = Event::bus()->m_events.window.active.listen([](PHLWINDOW, Desktop::eFocusReason) {
        for (auto& b : g_pGlobalState->bars)
            if (b)
                b->damageEntire();
    });
    g_pGlobalState->pTitleListener = Event::bus()->m_events.window.title.listen([](PHLWINDOW w) {
        for (auto& b : g_pGlobalState->bars)
            if (b && b->getOwner() == w)
                b->damageEntire();
    });

    if (Config::mgr()->type() == Config::CONFIG_LEGACY)
        HyprlandAPI::addConfigKeyword(PHANDLE, "plugin:breezebars:breezebars-button", onNewButton, Hyprlang::SHandlerOptions{});
    else
        HyprlandAPI::addLuaFunction(PHANDLE, "breezebars", "add_button", ::newLuaButton);
    g_pGlobalState->csdCommand = HyprlandAPI::registerHyprCtlCommand(PHANDLE, SHyprCtlCommand{.name = "hyprbars-csd", .exact = true, .fn = csdReport});
    g_pGlobalState->breezeCsdCommand = HyprlandAPI::registerHyprCtlCommand(PHANDLE, SHyprCtlCommand{.name="breezebars-csd",.exact=true,.fn=csdReport});
    HyprlandAPI::addLuaFunction(PHANDLE,"breezebars","decoration",luaDecoration);
    g_pGlobalState->pPreReloadListener = Event::bus()->m_events.config.preReload.listen([] { onPreConfigReload(); });
    g_pGlobalState->pReloadedListener  = Event::bus()->m_events.config.reloaded.listen([] { onConfigReloaded(); });

    // F7: install negotiation callbacks before attaching decorations.
    try { initDecorationDetection(); } catch (...) { closeDecorationDetection(); throw; }

    // add deco to existing windows
    for (auto& w : Desktop::windowState()->windows()) {
        if (w->isHidden() || !w->m_isMapped)
            continue;

        onNewWindow(w);
    }

    HyprlandAPI::reloadConfig();

    // Nombre propio (no «hyprbars»): el de Retro es el plugin de Omarchy, que se registra como hyprbars, y
    // los dos pueden estar cargados a la vez.
    return {"breezebars", "Breeze (KDE) title bars for BWM, a fork of hyprbars.", "Vaxry, BWM", "1.0"};
}

APICALL EXPORT void PLUGIN_EXIT() {
    g_pDecoClient.reset();
    clearDecorationToolTip();
    hideSnapPreview();
    closeDecorationDetection();
    for (auto& m : State::monitorState()->monitors())
        m->m_scheduledRecalc = true;

    g_pHyprRenderer->m_renderPass.removeAllOfType("CBarPassElement");
    g_pHyprRenderer->m_renderPass.removeAllOfType("CSnapPreviewPassElement");
    g_pHyprRenderer->m_renderPass.removeAllOfType("CBreezeShadowPassElement");
    g_pHyprRenderer->m_renderPass.removeAllOfType("CBreezeToolTipPassElement");
    removeSquareTopElements();

    if (g_pGlobalState) {
        g_pGlobalState->pOpenListener.reset();
        g_pGlobalState->pUpdateRulesListener.reset();
        g_pGlobalState->pMouseButtonListener.reset();
        g_pGlobalState->pMouseMoveListener.reset();
        g_pGlobalState->pRenderListener.reset();
        g_pGlobalState->pPreReloadListener.reset();
        g_pGlobalState->pReloadedListener.reset();
        g_pGlobalState->pActiveListener.reset();
        g_pGlobalState->pTitleListener.reset();
        if (g_pGlobalState->csdCommand)
            HyprlandAPI::unregisterHyprCtlCommand(PHANDLE, g_pGlobalState->csdCommand);

        if(g_pGlobalState->breezeCsdCommand)HyprlandAPI::unregisterHyprCtlCommand(PHANDLE,g_pGlobalState->breezeCsdCommand);
        Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->barColorRuleIdx);
        Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->titleColorRuleIdx);
        Desktop::Rule::windowEffects()->unregisterEffect(g_pGlobalState->nobarRuleIdx);
    }
}

#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/protocols/XDGShell.hpp>
#include <hyprland/src/xwayland/XSurface.hpp>
#include <hyprland/src/config/shared/actions/ConfigActions.hpp>
#include <hyprland/src/helpers/Monitor.hpp>
#include <hyprland/src/event/EventBus.hpp>

#include <unordered_map>
#include <memory>
#include <format>
#include <string>

extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

inline HANDLE PHANDLE = nullptr;

struct SWindowHooks {
    PHLWINDOWREF        window;
    CHyprSignalListener stateListener;
};

static std::unordered_map<uintptr_t, SWindowHooks> g_hooks;
static std::unordered_map<uintptr_t, int>          g_originalWorkspaces;

static void minimizeWindow(PHLWINDOW pw) {
    if (!pw || !validMapped(pw))
        return;

    auto origWS = pw->m_workspace;
    if (!origWS || origWS->m_isSpecialWorkspace)
        return;

    uintptr_t addr = (uintptr_t)pw.get();
    g_originalWorkspaces[addr] = origWS->m_id;

    // Tag for external tools / Quickshell
    Config::Actions::tag(std::format("from_ws_{}", origWS->m_id), pw);

    auto minWS = g_pCompositor->getWorkspaceByName("special:minimized");
    if (!minWS)
        minWS = g_pCompositor->getWorkspaceByString("special:minimized");
    if (!minWS && pw->m_monitor.lock())
        minWS = g_pCompositor->createNewWorkspace(g_pCompositor->getNewSpecialID(), pw->m_monitor.lock()->m_id, "special:minimized", false);
    if (!minWS)
        return;

    // Move to special:minimized SILENTLY (silent = true) so it never shows or dims the screen
    Config::Actions::moveToWorkspace(minWS, true, pw);

    // If monitor has special workspace active, close it
    auto mon = pw->m_monitor.lock();
    if (mon && mon->m_activeSpecialWorkspace) {
        Config::Actions::toggleSpecial(minWS);
    }
}

static void restoreWindow(PHLWINDOW pw) {
    if (!pw)
        return;

    uintptr_t addr = (uintptr_t)pw.get();
    int targetID = g_originalWorkspaces.contains(addr) ? g_originalWorkspaces[addr] : 1;

    // Also fallback check tags
    if (pw->m_ruleApplicator) {
        for (const auto& tag : pw->m_ruleApplicator->m_tagKeeper.getTags()) {
            if (tag.starts_with("from_ws_")) {
                try {
                    targetID = std::stoi(tag.substr(8));
                } catch (...) {}
                break;
            }
        }
    }

    PHLWORKSPACE targetWS = g_pCompositor->getWorkspaceByID(targetID);
    if (!targetWS) {
        auto mon = pw->m_monitor.lock();
        targetWS = mon ? mon->m_activeWorkspace : g_pCompositor->getWorkspaceByID(1);
    }

    Config::Actions::clearTags(pw);
    Config::Actions::moveToWorkspace(targetWS, false, pw);
    Config::Actions::focus(pw);

    auto minWS = g_pCompositor->getWorkspaceByName("special:minimized");
    auto mon = pw->m_monitor.lock();
    if (minWS && mon && mon->m_activeSpecialWorkspace == minWS) {
        Config::Actions::toggleSpecial(minWS);
    }
}

static void hookWindow(PHLWINDOW pw) {
    if (!pw || !validMapped(pw))
        return;

    uintptr_t addr = (uintptr_t)pw.get();
    if (g_hooks.contains(addr))
        return;

    SWindowHooks hooks;
    hooks.window = pw;

    auto pXDG = pw->m_xdgSurface.lock();
    if (pXDG && pXDG->m_toplevel.lock()) {
        auto pTop = pXDG->m_toplevel.lock();
        hooks.stateListener = pTop->m_events.stateChanged.listen([addr, wpTop = pXDG->m_toplevel] {
            auto top = wpTop.lock();
            if (!top || !top->m_state.requestsMinimize.value_or(false))
                return;

            if (g_hooks.contains(addr)) {
                auto pw = g_hooks[addr].window.lock();
                if (pw) {
                    minimizeWindow(pw);
                }
            }
        });
        g_hooks[addr] = std::move(hooks);
    } else if (auto pXWayland = pw->m_xwaylandSurface.lock()) {
        hooks.stateListener = pXWayland->m_events.stateChanged.listen([addr, wpXW = pw->m_xwaylandSurface] {
            auto xw = wpXW.lock();
            if (!xw || !xw->m_state.requestsMinimize.value_or(false))
                return;

            if (g_hooks.contains(addr)) {
                auto pw = g_hooks[addr].window.lock();
                if (pw) {
                    minimizeWindow(pw);
                }
            }
        });
        g_hooks[addr] = std::move(hooks);
    }
}

static void unhookWindow(PHLWINDOW pw) {
    if (!pw)
        return;
    uintptr_t addr = (uintptr_t)pw.get();
    g_hooks.erase(addr);
    g_originalWorkspaces.erase(addr);
}

static int luaMinimize(lua_State* L) {
    int top = lua_gettop(L);
    std::string addr = "";
    for (int i = 1; i <= top; ++i) {
        if (lua_isstring(L, i)) {
            std::string s = lua_tostring(L, i);
            if (s.starts_with("0x")) {
                addr = s;
                break;
            }
        }
    }
    PHLWINDOW pw = nullptr;
    if (!addr.empty()) {
        for (auto& w : g_pCompositor->m_windows) {
            if (std::format("0x{:x}", (uintptr_t)w.get()) == addr) {
                pw = w;
                break;
            }
        }
    }
    if (!pw)
        pw = Desktop::focusState()->window();
    if (pw)
        minimizeWindow(pw);
    return 0;
}

static int luaRestore(lua_State* L) {
    int top = lua_gettop(L);
    std::string addr = "";
    for (int i = 1; i <= top; ++i) {
        if (lua_isstring(L, i)) {
            std::string s = lua_tostring(L, i);
            if (s.starts_with("0x")) {
                addr = s;
                break;
            }
        }
    }
    PHLWINDOW pw = nullptr;
    if (!addr.empty()) {
        for (auto& w : g_pCompositor->m_windows) {
            if (std::format("0x{:x}", (uintptr_t)w.get()) == addr) {
                pw = w;
                break;
            }
        }
    }
    if (pw)
        restoreWindow(pw);
    return 0;
}

APICALL EXPORT std::string PLUGIN_API_VERSION() {
    return HYPRLAND_API_VERSION;
}

APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    PHANDLE = handle;

    static auto P_OPEN    = Event::bus()->m_events.window.open.listen([](PHLWINDOW w) { hookWindow(w); });
    static auto P_DESTROY = Event::bus()->m_events.window.destroy.listen([](PHLWINDOW w) { unhookWindow(w); });

    for (auto& w : g_pCompositor->m_windows) {
        hookWindow(w);
    }

    HyprlandAPI::addLuaFunction(PHANDLE, "csd", "minimize", luaMinimize);
    HyprlandAPI::addLuaFunction(PHANDLE, "csd", "restore", luaRestore);

    return {"hypr-csd", "Native CSD window minimization support", "Sasel", "1.0"};
}

APICALL EXPORT void PLUGIN_EXIT() {
    g_hooks.clear();
    g_originalWorkspaces.clear();
}

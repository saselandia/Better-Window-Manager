#pragma once

#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/render/Texture.hpp>
#include <hyprland/src/config/values/types/BoolValue.hpp>
#include <hyprland/src/config/values/types/IntValue.hpp>
#include <hyprland/src/config/values/types/StringValue.hpp>
#include <hyprland/src/config/values/types/ColorValue.hpp>

#include <hyprland/src/helpers/signal/Signal.hpp>

#include <unordered_map>

inline HANDLE PHANDLE = nullptr;

struct SHyprButton {
    std::string          cmd     = "";
    bool                 userfg  = false;
    CHyprColor           fgcol   = CHyprColor(0, 0, 0, 0);
    CHyprColor           bgcol   = CHyprColor(0, 0, 0, 0);
    float                size    = 10;
    std::string          icon    = "";
    SP<Render::ITexture> iconTex;

    // icon = "breeze:close|maximize|minimize": se dibuja como la decoración Breeze
    // de KDE (icono vectorial, círculo solo al pasar el ratón) en vez de con texto.
    std::string                                           breezeKind;
    std::unordered_map<std::string, SP<Render::ITexture>> breezeTex;
};

class CHyprBar;

struct SGlobalState {
    std::vector<SHyprButton>  buttons;
    std::vector<WP<CHyprBar>> bars;
    uint32_t                  nobarRuleIdx      = 0;
    uint32_t                  barColorRuleIdx   = 0;
    uint32_t                  titleColorRuleIdx = 0;

    CHyprSignalListener       pOpenListener;
    CHyprSignalListener       pUpdateRulesListener;
    CHyprSignalListener       pMouseButtonListener;
    CHyprSignalListener       pMouseMoveListener;
    CHyprSignalListener       pRenderListener;
    CHyprSignalListener       pPreReloadListener;
    CHyprSignalListener       pReloadedListener;
    SP<SHyprCtlCommand>       csdCommand;

    struct {
        SP<Config::Values::CColorValue>  barColor, textColor, inactiveButtonColor, inactiveBarColor, inactiveTextColor;
        SP<Config::Values::CIntValue>    barHeight;
        SP<Config::Values::CIntValue>    barTextSize;
        SP<Config::Values::CIntValue>    barPadding;
        SP<Config::Values::CIntValue>    barButtonPadding;
        SP<Config::Values::CBoolValue>   barBlur, barTitleEnabled, barPartOfWindow, barPrecedenceOverBorder, enabled, iconOnHover;
        SP<Config::Values::CStringValue> barTextFont, barTextAlign, barButtonsAlignment, onDoubleClick;
    } config;
};

#define g_pGlobalState g_pHyprbarsState
inline UP<SGlobalState> g_pHyprbarsState;

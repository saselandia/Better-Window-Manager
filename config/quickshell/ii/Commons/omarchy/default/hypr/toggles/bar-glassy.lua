-- The Glassy bar: the shell draws the bar see-through, and Hyprland blurs what
-- is behind it.
-- From Omarchy (basecamp/omarchy quattro 18ac93c, default/hypr/toggles/bar-glassy.lua, MIT).
-- BWM: without `require("default.hypr.glass")()`: BWM's glass mode is its own (modules/glass.lua);
-- here only the blur behind Omarchy's bar. omarchy-bar copies this file to
-- ~/.local/state/omarchy/toggles/hypr/, which skins/retro/hypr/misc.lua reads in Retro.

hl.layer_rule({
  match = { namespace = "^omarchy-bar$" },
  blur = true,
  ignore_alpha = 0.3,
})

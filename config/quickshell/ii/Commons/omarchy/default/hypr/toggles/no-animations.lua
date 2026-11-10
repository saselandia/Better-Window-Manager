-- From Omarchy (basecamp/omarchy quattro ec62d379, default/hypr/toggles/no-animations.lua, MIT), unchanged.
-- Read in Retro by skins/retro/hypr/misc.lua; omarchy-toggle-animations copies it to ~/.local/state/omarchy/toggles/hypr/.
-- Draw nothing just for show, for machines that render on the CPU, like a VM:
-- no animations, blur or shadows. How see-through windows are is left to
-- Appearance > Windows > Window Opacity.
hl.config({
  animations = {
    enabled = false,
  },

  decoration = {
    blur = {
      enabled = false,
    },

    shadow = {
      enabled = false,
    },
  },
})

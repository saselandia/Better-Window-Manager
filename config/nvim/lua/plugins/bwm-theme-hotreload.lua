-- Recarga en vivo del tema, como omarchy-theme-hotreload.lua: theme.lua apunta a
-- ~/.local/state/omarchy/current/theme/neovim.lua, que BWM reescribe en cada tema Retro.
-- Se vigila ese directorio; al cambiar se lee la especificación del tema y se aplica su
-- colorscheme (con aether, la paleta del tema primero).
local function theme_dir()
  return vim.fn.resolve(vim.fn.expand("~/.local/state/omarchy/current/theme"))
end

local function mode()
  local f = io.open(theme_dir() .. "/colors.toml", "r")
  if not f then
    return nil
  end
  local text = f:read("*a")
  f:close()
  return text:match('mode%s*=%s*"(%a+)"')
end

local function apply()
  local ok, spec = pcall(dofile, theme_dir() .. "/neovim.lua")
  if not ok or type(spec) ~= "table" then
    return
  end
  local colorscheme, aether_opts
  for _, plugin in ipairs(spec) do
    if type(plugin) == "table" then
      if plugin[1] == "LazyVim/LazyVim" and plugin.opts then
        colorscheme = plugin.opts.colorscheme
      elseif type(plugin[1]) == "string" and plugin[1]:match("aether") and plugin.opts then
        aether_opts = plugin.opts
      end
    end
  end
  if not colorscheme then
    return
  end
  local m = mode()
  if m == "light" or m == "dark" then
    vim.o.background = m
  end
  if aether_opts and colorscheme == "aether" then
    pcall(function()
      require("lazy").load({ plugins = { "aether" } })
      require("aether").setup(aether_opts)
    end)
  end
  pcall(vim.cmd.colorscheme, colorscheme)
end

return {
  {
    "LazyVim/LazyVim",
    init = function()
      vim.api.nvim_create_autocmd("User", {
        pattern = "VeryLazy",
        once = true,
        callback = function()
          local uv = vim.uv or vim.loop
          local timer = uv.new_timer()
          local handle = uv.new_fs_event()
          local function watch()
            handle:start(theme_dir(), {}, function(_, filename)
              if filename and filename ~= "neovim.lua" and filename ~= "colors.toml" then
                return
              end
              -- BWM escribe varios archivos seguidos: se espera a que termine
              timer:stop()
              timer:start(400, 0, vim.schedule_wrap(function()
                apply()
                -- El directorio puede haberse recreado: se vuelve a vigilar
                handle:stop()
                watch()
              end))
            end)
          end
          watch()
          _G.__bwm_theme_watch = { handle = handle, timer = timer }
        end,
      })
    end,
  },
}

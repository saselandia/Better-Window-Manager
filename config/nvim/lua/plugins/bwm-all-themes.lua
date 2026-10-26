-- Todos los plugins de color de los temas de Omarchy que trae BWM (hypr/omarchy/themes/*/neovim.lua)
-- y aether.nvim (paletas dinámicas, neovim.lua.tpl), instalados pero sin cargar: cambiar de tema
-- nunca necesita descargar nada. lazy.nvim carga el plugin al pedir su :colorscheme.
local specs, seen = {
  { "omacom/aether.nvim", branch = "v3", name = "aether", lazy = true },
}, { ["omacom/aether.nvim"] = true }
local dir = vim.fn.expand("~/.config/hypr/omarchy/themes")
for _, file in ipairs(vim.fn.glob(dir .. "/*/neovim.lua", false, true)) do
  local ok, spec = pcall(dofile, file)
  if ok and type(spec) == "table" then
    for _, plugin in ipairs(spec) do
      local repo = type(plugin) == "table" and plugin[1]
      if type(repo) == "string" and repo ~= "LazyVim/LazyVim" and not seen[repo] then
        seen[repo] = true
        table.insert(specs, {
          repo,
          name = plugin.name,
          branch = plugin.branch,
          dependencies = plugin.dependencies,
          lazy = true,
        })
      end
    end
  end
end
return specs

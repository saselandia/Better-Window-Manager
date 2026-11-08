// Nombre de la app de una ventana desde su .desktop. De omarchy-hyprland-titlebars (omacom, b351b14, MIT
// sobre hyprbars BSD-3-Clause), sin cambios: lo usan las barras de los workspaces flotantes de Retro.
#pragma once

#include <string>

// The Name of the desktop entry whose StartupWMClass, or else whose file name,
// matches a window class. Empty when no entry claims the class.
std::string omarchyAppName(const std::string& windowClass);

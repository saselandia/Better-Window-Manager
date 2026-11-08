# omarchy-hyprland-titlebars de Omarchy (omacom, 379ff91, el último para Hyprland 0.56; BSD-3-Clause +
# MIT), sin cambios: las barras de los workspaces flotantes de Retro. Se compila aquí en vez de con su
# CMakeLists.txt (que se conserva) para usar las mismas opciones que src/hyprbars.
CXXFLAGS ?= -O2
CXXFLAGS += -shared -fPIC -fno-gnu-unique -std=c++2b -Wno-narrowing
INCLUDES = `pkg-config --cflags pixman-1 libdrm hyprland libinput libudev wayland-server xkbcommon lua5.4`

SRC = main.cpp barDeco.cpp BarPassElement.cpp appName.cpp
HEADERS = $(wildcard *.hpp)
TARGET = titlebars.so

all: $(TARGET)

$(TARGET): $(SRC) $(HEADERS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(INCLUDES) $(SRC) -o $@

# Despliegue atómico, como src/hyprbars: NUNCA `cp` sobre un .so cargado por Hyprland (SIGBUS).
# Hyprland sigue con el cargado hasta reiniciar la sesión; nunca unload/load en caliente.
PLUGIN_DIR ?= ../../config/hypr/plugins
INSTALL_NAME ?= omarchy-titlebars.so

install: $(TARGET)
	install -m755 $(TARGET) $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp
	mv -f $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp $(PLUGIN_DIR)/$(INSTALL_NAME)

clean:
	rm -f ./$(TARGET)

.PHONY: all install clean

EXTRA_FLAGS = -fno-gnu-unique

CXXFLAGS ?= -O2
CXXFLAGS += -shared -fPIC -fno-gnu-unique -std=c++2b -Wno-narrowing
INCLUDES = `pkg-config --cflags pixman-1 libdrm hyprland libinput libudev wayland-server xkbcommon lua5.4`
LIBS = -lxcb

SRC = main.cpp barDeco.cpp BarPassElement.cpp CSDDetect.cpp SquareTop.cpp
TARGET = hyprbars.so

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(EXTRA_FLAGS) $(INCLUDES) $^ $> -o $@ $(LIBS)

# Despliegue atómico: NUNCA usar `cp` sobre un .so cargado por Hyprland.
# `cp` trunca el inodo que Hyprland tiene mapeado en memoria -> SIGBUS y crash.
# Copiamos a un temporal y hacemos rename (mv), que sustituye la entrada del
# directorio sin tocar el inodo en uso. Hyprland sigue con el plugin viejo hasta
# reiniciar la sesión (no hacer unload/load en caliente: también provoca segfaults).
PLUGIN_DIR ?= ../../config/hypr/plugins
INSTALL_NAME ?= hyprbars-plasma.so

install: $(TARGET)
	install -m755 $(TARGET) $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp
	mv -f $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp $(PLUGIN_DIR)/$(INSTALL_NAME)

clean:
	rm -f ./$(TARGET)

meson-build:
	mkdir -p build
	cd build && meson .. && ninja

.PHONY: all meson-build clean install

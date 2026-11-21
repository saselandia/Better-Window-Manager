EXTRA_FLAGS = -fno-gnu-unique

CXXFLAGS ?= -O2
CXXFLAGS += -shared -fPIC -fno-gnu-unique -std=c++2b -Wno-narrowing
INCLUDES = `pkg-config --cflags pixman-1 libdrm hyprland libinput libudev wayland-server xkbcommon lua5.4`
LIBS = -lxcb -ldl

SRC = main.cpp barDeco.cpp barRemote.cpp DecoClient.cpp BarPassElement.cpp CSDDetect.cpp SquareTop.cpp KdeShadow.cpp
HEADERS = $(wildcard *.hpp) ../bwm-decorator/protocol.h
TARGET = breezebars.so
OBJECTS = $(SRC:.cpp=.o)

all: $(TARGET)

kde-shadow-server.h: protocols/shadow.xml
	wayland-scanner server-header $< $@
kde-shadow-protocol.c: protocols/shadow.xml
	wayland-scanner private-code $< $@
kde-shadow-protocol.o: kde-shadow-protocol.c
	$(CC) -fPIC -fvisibility=hidden -c $< -o $@
%.o: %.cpp $(HEADERS) kde-shadow-server.h
	$(CXX) $(CXXFLAGS) $(EXTRA_FLAGS) $(INCLUDES) -MMD -MP -c $< -o $@
$(TARGET): $(OBJECTS) kde-shadow-protocol.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(EXTRA_FLAGS) $(OBJECTS) kde-shadow-protocol.o -o $@ $(LIBS)
-include $(OBJECTS:.o=.d)

# Despliegue atómico: NUNCA usar `cp` sobre un .so cargado por Hyprland.
# `cp` trunca el inodo que Hyprland tiene mapeado en memoria -> SIGBUS y crash.
# Copiamos a un temporal y hacemos rename (mv), que sustituye la entrada del
# directorio sin tocar el inodo en uso. Hyprland sigue con el plugin viejo hasta
# reiniciar la sesión (no hacer unload/load en caliente: también provoca segfaults).
PLUGIN_DIR ?= ../../config/hypr/plugins
INSTALL_NAME ?= breezebars.so

install: $(TARGET)
	install -m755 $(TARGET) $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp
	mv -f $(PLUGIN_DIR)/.$(INSTALL_NAME).tmp $(PLUGIN_DIR)/$(INSTALL_NAME)

clean:
	rm -f ./$(TARGET) $(OBJECTS) $(OBJECTS:.o=.d) kde-shadow-server.h kde-shadow-protocol.c kde-shadow-protocol.o

meson-build:
	mkdir -p build
	cd build && meson .. && ninja

.PHONY: all meson-build clean install

CXXFLAGS ?= -O2
CXXFLAGS += -shared -fPIC -fno-gnu-unique -std=c++2b -Wno-c++11-narrowing
INCLUDES = `pkg-config --cflags pixman-1 libdrm hyprland libinput libudev wayland-server xkbcommon lua5.4`

TARGET = hypr-csd.so
SRC = main.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(INCLUDES) $^ -o $@

# Despliegue atómico (ver src/hyprbars/Makefile): cp sobre un .so cargado = SIGBUS.
PLUGIN_DIR ?= ../../config/hypr/plugins

install: $(TARGET)
	install -m755 $(TARGET) $(PLUGIN_DIR)/.$(TARGET).tmp
	mv -f $(PLUGIN_DIR)/.$(TARGET).tmp $(PLUGIN_DIR)/$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean install

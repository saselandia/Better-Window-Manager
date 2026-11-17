BUILD_DIR ?= ../../build/bwm-plasma-desktops
PLUGIN_DIR ?= ../../config/hypr/plugins
TARGET = bwm-plasma-desktops.so
all:
	cmake -S . -B $(BUILD_DIR) -DBWM_BUILD_HYPRLAND_PLUGIN=ON
	cmake --build $(BUILD_DIR) --target bwm-plasma-desktops -j4
# Atomic deployment only. No plugin load/unload or compositor restart here.
install: all
	install -m755 $(BUILD_DIR)/$(TARGET) $(PLUGIN_DIR)/.$(TARGET).tmp
	mv -f $(PLUGIN_DIR)/.$(TARGET).tmp $(PLUGIN_DIR)/$(TARGET)
.PHONY: all install

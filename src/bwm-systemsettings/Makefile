# Native KCMs discovered by the real KDE System Settings application.
BUILD_DIR ?= build
PREFIX ?= $(HOME)/.local/share/bwm/systemsettings
.PHONY: all test install clean
all:
	cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=$(PREFIX)
	cmake --build $(BUILD_DIR) -j4
test: all
	ctest --test-dir $(BUILD_DIR) --output-on-failure
install: all
	cmake --install $(BUILD_DIR)
clean:
	cmake --build $(BUILD_DIR) --target clean

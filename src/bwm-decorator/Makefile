# bwm-decorator: auxiliar de decoraciones de Breeze (fase 6a de docs/BREEZE_PLAN.md)
#
#   make            compila ./bwm-decorator
#   make install    instala en $(PREFIX)/bin con copia temporal + mv (atómico: el supervisor puede
#                   estar ejecutando el binario anterior)
#
# Requisitos: Qt 6 (Core, Gui, DBus), KDecoration3 (kde-plasma/kdecoration), KF6 Config, ColorScheme,
# CoreAddons y Service. Nunca se carga dentro de Hyprland: es un proceso aparte.

PREFIX ?= $(HOME)/.local/share/bwm
CXX ?= g++
MOC ?= $(shell for m in /usr/lib64/qt6/libexec/moc /usr/lib/qt6/libexec/moc /usr/lib/qt6/moc; do [ -x $$m ] && echo $$m && break; done)
KF6 ?= /usr/include/KF6

CXXFLAGS ?= -O2 -g
CXXFLAGS += -std=c++20 -fPIC -Wall -Wextra -Wno-unused-parameter
CPPFLAGS += $(shell pkg-config --cflags Qt6Gui Qt6DBus) -I/usr/include/KDecoration3 \
            -I$(KF6)/KCoreAddons -I$(KF6)/KConfig -I$(KF6)/KConfigCore -I$(KF6)/KColorScheme -I$(KF6)/KService
LDLIBS += $(shell pkg-config --libs Qt6Gui Qt6DBus) -lkdecorations3 -lkdecorations3private \
          -lKF6CoreAddons -lKF6ConfigCore -lKF6ColorScheme -lKF6Service

SOURCES = main.cpp server.cpp decorator.cpp palette.cpp
HEADERS = protocol.h wire.h server.h decorator.h palette.h
MOCS = moc_server.cpp moc_decorator.cpp moc_palette.cpp
OBJECTS = $(SOURCES:.cpp=.o) $(MOCS:.cpp=.o)

bwm-decorator: $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDLIBS)

%.o: %.cpp $(HEADERS)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

moc_%.cpp: %.h
	$(MOC) $(CPPFLAGS) -o $@ $<

install: bwm-decorator
	install -d $(PREFIX)/bin
	install -m 755 bwm-decorator $(PREFIX)/bin/.bwm-decorator.tmp
	mv -f $(PREFIX)/bin/.bwm-decorator.tmp $(PREFIX)/bin/bwm-decorator

clean:
	rm -f bwm-decorator *.o moc_*.cpp poc

.PHONY: install clean

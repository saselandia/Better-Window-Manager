# bwm-kcmhost: módulo QML org.bwm.kcm para incrustar los KCM reales de Plasma en las Preferencias
# del sistema de Breeze (fase 11 de docs/BREEZE_PLAN.md). Sólo lo carga la ventana de Preferencias
# KcmHost se usa sólo en Preferencias; ThemeHost (F12) aloja temas en motores separados.
#
#   make            compila libbwmkcmplugin.so
#   make install    copia el módulo a $(PREFIX)/qml/org/bwm/kcm (copia temporal + mv)
#
# Requisitos: Qt 6 (Quick, Qml), KF6 KCMUtils (Core y Quick), CoreAddons.

PREFIX ?= $(HOME)/.local/share/bwm
DEST = $(PREFIX)/qml/org/bwm/kcm
CXX ?= g++
MOC ?= $(shell for m in /usr/lib64/qt6/libexec/moc /usr/lib/qt6/libexec/moc /usr/lib/qt6/moc; do [ -x $$m ] && echo $$m && break; done)
KF6 ?= /usr/include/KF6

CXXFLAGS ?= -O2 -g
CXXFLAGS += -std=c++20 -fPIC -Wall -Wextra -Wno-unused-parameter
CPPFLAGS += $(shell pkg-config --cflags Qt6Quick Qt6Qml) -I$(KF6)/KCMUtilsQuick -I$(KF6)/KCMUtilsCore \
            -I$(KF6)/KCMUtils -I$(KF6)/KCoreAddons -I$(KF6)/KI18n
LDLIBS += $(shell pkg-config --libs Qt6Quick Qt6Qml) -lKF6KCMUtilsQuick -lKF6KCMUtilsCore -lKF6CoreAddons -lKF6I18n

libbwmkcmplugin.so: kcmhost.o moc_kcmhost.o themehost.o moc_themehost.o plugin.o
	$(CXX) -shared $(CXXFLAGS) -o $@ $^ $(LDLIBS)

plugin.o: plugin.cpp plugin.moc kcmhost.h themehost.h
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

plugin.moc: plugin.cpp
	$(MOC) $(CPPFLAGS) -o $@ $<

%.o: %.cpp kcmhost.h themehost.h
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

moc_%.cpp: %.h
	$(MOC) $(CPPFLAGS) -o $@ $<

install: libbwmkcmplugin.so qmldir
	install -d $(DEST)
	install -m 644 qmldir $(DEST)/.qmldir.tmp && mv -f $(DEST)/.qmldir.tmp $(DEST)/qmldir
	install -m 755 libbwmkcmplugin.so $(DEST)/.libbwmkcmplugin.so.tmp
	mv -f $(DEST)/.libbwmkcmplugin.so.tmp $(DEST)/libbwmkcmplugin.so
	printf '%s\n' 2 > $(DEST)/.api-version.tmp
	mv -f $(DEST)/.api-version.tmp $(DEST)/api-version

clean:
	rm -f *.o moc_*.cpp plugin.moc libbwmkcmplugin.so

.PHONY: install clean

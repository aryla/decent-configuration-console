UI := $(patsubst ui/%.ui,ui/ui_%.py,$(wildcard ui/*.ui))
RC := rc_resources.py
QML := $(wildcard ui/*.qml)

all: $(UI) $(RC)

ui_%.py: %.ui
	uv run -- pyside6-uic $< -o $@

rc_%.py: %.qrc qtquickcontrols2.conf $(QML)
	uv run -- pyside6-rcc $< -o $@

run: all
	uv run -- main.py

.PHONY: all run
.DEFAULT_GOAL: all

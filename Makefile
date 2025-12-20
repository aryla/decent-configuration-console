RC := rc_resources.py
QML := $(wildcard ui/*.qml)

all: $(RC)

rc_%.py: %.qrc qtquickcontrols2.conf $(QML)
	uv run -- pyside6-rcc $< -o $@

run: all
	uv run -- main.py

.PHONY: all run
.DEFAULT_GOAL: all

RC := rc_resources.py

all: $(RC)

rc_%.py: %.qrc qtquickcontrols2.conf decent.svg $(wildcard ui/*.qml)
	uv run -- pyside6-rcc $< -o $@

run: all
	uv run -- main.py

.PHONY: all run
.DEFAULT_GOAL: all

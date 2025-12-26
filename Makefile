RC := rc_resources.py

all: $(RC)

rc_%.py: %.qrc qtquickcontrols2.conf decent.svg $(wildcard ui/*.qml)
	git describe --all --dirty --long --tags > .version_info.txt
	date '+%Y-%m-%d' > .build_date.txt
	uv run -- pyside6-rcc $< -o $@
	$(RM) .build_date.txt .version_info.txt

run: all
	uv run -- main.py

.PHONY: all run
.DEFAULT_GOAL: all

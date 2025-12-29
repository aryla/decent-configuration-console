VERSION := $(shell sed -n 's/version\s*=\s*"\([^"]\+\)"/\1/p' pyproject.toml)
VERSION_INFO := $(shell git describe --dirty --tags)
BUILD_DATE := $(shell date '+%Y-%m-%d')

all:
	printf '%s\n' $(BUILD_DATE) > .build_date.txt
	printf '%s\n' $(VERSION) > .version.txt
	printf '%s\n' $(VERSION_INFO) > .version_info.txt
	uv run -- pyside6-rcc resources.qrc -o rc_resources.py
	$(RM) .build_date.txt .version.txt .version_info.txt

run: all
	uv run -- main.py

.PHONY: all run
.DEFAULT_GOAL: all

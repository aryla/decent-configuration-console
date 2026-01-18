build:
	uv run build.py build

package:
	uv sync --extra build
	uv run build.py package

run: build
	uv run main.py

.PHONY: build package run
.DEFAULT_GOAL: build

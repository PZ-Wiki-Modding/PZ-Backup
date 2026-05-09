.PHONY: help build
.ONESHELL:

SHELL := /bin/bash

help:
	@echo "Sphinx documentation builder"
	@echo "Available targets:"
	@echo "  build  - Build the app"

build:
	source .venv/bin/activate
	pyinstaller --onefile --windowed src/main.py

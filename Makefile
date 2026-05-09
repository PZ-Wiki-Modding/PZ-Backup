.PHONY: help build
.ONESHELL:

SHELL := /bin/bash

help:
	@echo "Sphinx documentation builder"
	@echo "Available targets:"
	@echo "  build  - Build the app"

build:
	pyinstaller --onefile --windowed src/PZ_Backup.py

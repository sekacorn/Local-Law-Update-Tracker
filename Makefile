.PHONY: help install dev build start stop clean reset test

help:
	@echo "LLUT - Local Law Update Tracker"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies (backend + frontend)"
	@echo "  make dev        - Start development servers (backend + frontend)"
	@echo "  make build      - Build the desktop application"
	@echo "  make start      - Start the built application"
	@echo "  make stop       - Stop all running processes"
	@echo "  make clean      - Clean temporary files and build artifacts"
	@echo "  make reset      - Reset local database and cache"
	@echo "  make test       - Run all tests"
	@echo ""

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd apps/desktop && npm install
	@echo "Installation complete!"

dev:
	@echo "Starting development environment..."
	bash scripts/dev_run.sh

build:
	@echo "Building desktop application..."
	bash scripts/build_desktop.sh

start:
	@echo "Starting application..."
	bash scripts/start_app.sh

stop:
	@echo "Stopping all processes..."
	bash scripts/stop_all.sh

clean:
	@echo "Cleaning temporary files..."
	bash scripts/cleanup.sh

reset:
	@echo "Resetting local database..."
	bash scripts/reset_db.sh

test:
	@echo "Running tests..."
	cd backend && pytest tests/

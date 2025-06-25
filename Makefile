# UPM Test Suite Makefile

.PHONY: help test test-local test-docker test-docker-quick build install clean

# Default target
help:
	@echo "UPM Test Suite Commands:"
	@echo ""
	@echo "  test-local       Run tests on current platform using UV script"
	@echo "  test-docker      Run tests across all Linux distributions"
	@echo "  test-docker-quick Run tests on subset of distributions (Ubuntu, Fedora, Alpine)"
	@echo "  list-distros     List available Docker test distributions"
	@echo "  test             Run both local and Docker tests"
	@echo "  build            Build UPM package"
	@echo "  install          Install UPM tool locally"
	@echo "  clean            Clean build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make test-local                    # Test on current platform"
	@echo "  make test-docker                   # Test all Linux distributions"
	@echo "  make test-docker DISTROS=ubuntu    # Test specific distribution"

# Run tests locally using UV script
test-local:
	@echo "[TEST] Running UPM tests locally..."
	python3 test_upm.py

# Run comprehensive Docker tests
test-docker:
	@echo "[DOCKER] Running UPM Docker tests..."
ifdef DISTROS
	python3 docker-tests.py --distros $(DISTROS)
else
	python3 docker-tests.py
endif

# Run quick Docker tests (subset of distributions)
test-docker-quick:
	@echo "[DOCKER] Running quick UPM Docker tests..."
	python3 docker-tests.py --distros "ubuntu:24.04" "fedora:39" "registry.access.redhat.com/ubi9/ubi-minimal"

# List available Docker distributions
list-distros:
	python3 docker-tests.py --list

# Run all tests
test: test-local test-docker

# Build the package
build:
	@echo "[BUILD] Building UPM package..."
	uv build

# Install the tool locally
install:
	@echo "[INSTALL] Installing UPM tool locally..."
	uv tool install .

# Clean build artifacts
clean:
	@echo "[CLEAN] Cleaning build artifacts..."
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 
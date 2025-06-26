# pkgx Test Suite Makefile

.PHONY: help test test-docker test-all build install clean

help:
	@echo "pkgx Test Suite Commands:"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run local tests"
	@echo "  test-docker      Run tests in Docker containers"
	@echo "  test-all         Run both local and Docker tests"
	@echo ""
	@echo "Development:"
	@echo "  build            Build pkgx package"
	@echo "  install          Install pkgx tool locally"
	@echo "  clean            Clean build artifacts"

# Local testing using the UV script
test:
	@echo "[TEST] Running pkgx tests locally..."
	@chmod +x test_pkgx.py
	@uv run test_pkgx.py

# Docker-based cross-platform testing
test-docker:
	@echo "[TEST] Running pkgx tests in Docker containers..."
	@uv run docker-tests.py

# Run all tests
test-all: test test-docker
	@echo "[TEST] All tests completed!"

# Build the package
build:
	@echo "[BUILD] Building pkgx package..."
	@uv build

# Install the tool locally
install: build
	@echo "[INSTALL] Installing pkgx locally..."
	@uv tool install --force --from dist/ pkgx

# Clean build artifacts
clean:
	@echo "[CLEAN] Cleaning build artifacts..."
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
# pkgx Testing Guide

This document describes the comprehensive testing strategy for pkgx (Universal Package Manager) and how to run tests locally and in CI/CD.

## 🧪 Test Architecture

The pkgx test suite uses a **single source of truth** approach:

1. **`test_pkgx.py`** - The main UV script with inline dependencies that tests all functionality
2. **`docker-tests.py`** - Docker orchestrator that runs the same UV script across different Linux distributions
3. **GitHub Actions** - CI/CD pipeline that runs tests across Windows, macOS, and Linux

## 📋 Test Coverage

### Core Functionality Tests
- ✅ Help and version commands
- ✅ Package manager detection and listing
- ✅ All command dry-run modes (install, remove, update, upgrade, search)
- ✅ Manual package manager selection
- ✅ Error handling (invalid managers, missing packages)
- ✅ Platform-specific detection logic

### Cross-Platform Tests
- ✅ Windows (Chocolatey detection)
- ✅ macOS (Homebrew detection)
- ✅ Linux distributions (apt, dnf, yum, apk, zypper)

### Distribution Coverage
- **Ubuntu 24.04** (apt)
- **Fedora 39** (dnf)
- **AlmaLinux 9** (dnf)
- **UBI 9 Minimal** (microdnf)
- **Alpine 3.18** (apk)
- **openSUSE Leap 15.5** (zypper)

## 🚀 Running Tests Locally

### Prerequisites

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# For Docker tests
docker --version  # Ensure Docker is installed and running
```

### Quick Local Test

```bash
# Run on current platform
cd pkgx
python test_pkgx.py
```

This will test pkgx on your current platform and automatically detect available package managers.

### Using Makefile

```bash
# Show all available commands
make help

# Test on current platform only
make test-local

# Test across all Linux distributions (requires Docker)
make test-docker

# Quick Docker test (3 distributions)
make test-docker-quick

# Test specific distributions
make test-docker DISTROS="ubuntu:24.04 fedora:39"

# List available Docker distributions
make list-distros

# Run all tests
make test
```

### Manual Docker Testing

```bash
# Test all distributions
python docker-tests.py

# Test specific distributions
python docker-tests.py --distros "ubuntu:24.04" "alpine:3.18"

# List available distributions
python docker-tests.py --list
```

## 🔧 UV Script Details

The `test_pkgx.py` script is a **UV script with inline dependencies**:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pytest>=7.0.0",
#     "subprocess-mock>=1.0.0",
# ]
# [tool.uv]
# exclude-newer = "2025-02-19T00:00:00Z"
# ///
```

### Key Features
- **Self-contained**: No external setup required
- **Cross-platform**: Runs on Windows, macOS, and Linux
- **Comprehensive**: Tests all pkgx functionality
- **Fast**: Completes in ~30 seconds
- **Safe**: Uses dry-run mode to avoid system changes

### Test Functions

| Function | Purpose |
|----------|---------|
| `test_help_command` | Verify help system works |
| `test_version_command` | Check version output |
| `test_list_managers_command` | Test manager listing |
| `test_dry_run_commands` | Test all commands in dry-run mode |
| `test_manager_detection` | Verify auto-detection logic |
| `test_manual_manager_selection` | Test manual manager override |
| `test_invalid_manager_selection` | Error handling for invalid managers |
| `test_no_packages_error` | Error handling for missing arguments |
| `test_platform_specific_detection` | Platform-specific preferences |

## 🐳 Docker Test Details

The Docker test runner:

1. **Pulls** base distribution images
2. **Installs** Python, pip, curl, and UV
3. **Copies** pkgx source and test script
4. **Runs** the same `test_pkgx.py` script
5. **Collects** results and provides summary

### Docker Test Flow

```mermaid
graph LR
    A[Pull Image] --> B[Install Dependencies]
    B --> C[Copy pkgx Source]
    C --> D[Run test_pkgx.py]
    D --> E[Collect Results]
    E --> F[Summary Report]
```

### Timeout & Error Handling
- **5-minute timeout** per distribution
- **Graceful failure** handling
- **Detailed error reporting**
- **Parallel execution** support

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The CI/CD pipeline runs:

1. **Native tests** on Windows, macOS, Linux with Python 3.8-3.12
2. **Docker tests** across all Linux distributions
3. **Package build** and installation tests
4. **Real package manager** tests where available

### Matrix Testing

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

### Triggered On
- **Push** to main/develop branches
- **Pull requests** to main
- **Manual dispatch** for testing

## 📊 Test Results Interpretation

### Success Indicators
```
✅ PASS: Help command
✅ PASS: Version command
✅ PASS: List managers command
...
🎉 All tests passed!
```

### Failure Examples
```
❌ FAIL: Package manager detection - Manager apt not actually available
❌ FAIL: Dry run: install - Exit code: 1, stdout: Error: No package...
💥 2 test(s) failed!
```

### Docker Summary
```
📊 DOCKER TEST SUMMARY
==============================
✅ PASS: Ubuntu 22.04
✅ PASS: Fedora 39
❌ FAIL: Alpine 3.18
✅ PASS: openSUSE Leap 15.5

Total: 4
Passed: 3
Failed: 1
```

## 🐛 Troubleshooting

### Common Issues

**Docker not available:**
```bash
❌ Docker is not available. Please install Docker to run these tests.
```
**Solution:** Install Docker and ensure it's running

**Import errors:**
```bash
Error importing pkgx modules: No module named 'pkgx.managers'
```
**Solution:** Run from the `pkgx` directory

**Permission errors:**
```bash
Error running container: permission denied
```
**Solution:** Ensure Docker daemon is running and user has permissions

### Debug Mode

Add debug output to tests:
```bash
# Run with verbose output
python test_pkgx.py --verbose  # (if implemented)

# Check Docker logs
docker logs <container_id>
```

## 🎯 Adding New Tests

### Adding Test Functions

1. Create new test function in `test_pkgx.py`:
```python
def test_new_feature(results: TestResult):
    """Test new pkgx feature"""
    # Test implementation
    if success:
        results.add_pass("New feature test")
    else:
        results.add_fail("New feature test", "Error message")
```

2. Add to `run_all_tests()`:
```python
test_new_feature(results)
```

### Adding New Distributions

1. Add to `DISTRIBUTIONS` in `docker-tests.py`:
```python
"newdistro:latest": {
    "name": "New Distribution",
    "setup_commands": [
        "package-manager install -y python3 curl",
        "curl -LsSf https://astral.sh/uv/install.sh | sh"
    ],
    "expected_manager": "expected-pm"
}
```

## 📈 Performance Metrics

### Typical Test Times
- **Local test**: ~10-30 seconds
- **Single Docker distribution**: ~2-3 minutes
- **All Docker distributions**: ~15-25 minutes
- **Full CI pipeline**: ~30-45 minutes

### Resource Usage
- **Memory**: ~100MB per container
- **Disk**: ~500MB per distribution image
- **CPU**: Moderate during container startup

## 🔐 Security Considerations

- **No privileged containers** required
- **Dry-run mode** prevents system modifications
- **Temporary directories** cleaned automatically
- **No sensitive data** exposed in tests

---

## 📝 Summary

The pkgx test suite provides comprehensive coverage across:
- **3 operating systems** (Windows, macOS, Linux)
- **9 Linux distributions** via Docker
- **8 package managers** (apt, dnf, yum, microdnf, zypper, apk, brew, choco)
- **5 Python versions** (3.8-3.12)

This ensures pkgx works reliably in diverse environments and provides confidence for production use.
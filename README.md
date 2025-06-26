# pkgx - Universal Package Manager

A cross-platform wrapper for various system package managers. pkgx automatically detects your system's package manager and provides a unified interface for common package management operations.

## Supported Package Managers

- **apt** (Debian/Ubuntu)
- **dnf** (Fedora/RHEL 8+)
- **yum** (RHEL/CentOS/Fedora)
- **microdnf** (Minimal container environments)
- **zypper** (openSUSE)
- **apk** (Alpine Linux)
- **brew** (Homebrew - macOS/Linux)
- **choco** (Chocolatey - Windows)

## Installation

### Install with UV

```bash
# Install from current directory
uvx --from . pkgx --help

# Or install persistently
uv tool install .
```

### Install from PyPI (once published)

```bash
# Install and run temporarily
uvx pkgx install git

# Install persistently
uv tool install pkgx
```

## Usage

### Basic Commands

```bash
# Install packages
pkgx install git vim curl

# Remove packages
pkgx remove old-package

# Update package lists
pkgx update

# Upgrade all packages
pkgx upgrade

# Upgrade specific packages
pkgx upgrade git vim

# Search for packages
pkgx search firefox

# List available package managers
pkgx list-managers

# Show version
pkgx version
```

### Advanced Options

```bash
# Force a specific package manager
pkgx install git --manager apt
pkgx install git -m brew

# Dry run (show what would be executed)
pkgx install git --dry-run
pkgx upgrade --dry-run -n
```

## How It Works

1. **Auto-detection**: pkgx automatically detects available package managers on your system
2. **Priority Selection**: Uses platform-specific preferences (e.g., `apt` on Debian/Ubuntu, `dnf` on Fedora)
3. **Unified Interface**: Translates commands to the appropriate syntax for each package manager
4. **Cross-platform**: Works on Linux, macOS, and Windows

## Examples

### Cross-platform Package Installation

```bash
# This command works on any supported system:
pkgx install git

# On Ubuntu/Debian, runs: apt install -y git
# On Fedora, runs: dnf install -y git
# On macOS with Homebrew, runs: brew install git
# On Windows with Chocolatey, runs: choco install git -y
```

### Checking Available Managers

```bash
$ pkgx list-managers
Available package managers:

  apt          - apt          ✓ available (auto-detected)
  dnf          - dnf          ✗ not available
  microdnf     - microdnf     ✗ not available
  yum          - yum          ✗ not available
  zypper       - zypper       ✗ not available
  apk          - apk          ✗ not available
  brew         - brew         ✓ available
  chocolatey   - choco        ✗ not available

Auto-detected package manager: apt
```

### Using Specific Managers

```bash
# Force use of a specific package manager
pkgx install nodejs --manager brew
pkgx search python --manager apt
```

## Development

### Project Structure

```
pkgx/
├── pyproject.toml          # Package configuration
├── README.md               # This file
└── pkgx/
    ├── __init__.py         # Package metadata
    ├── cli.py              # Main CLI interface
    └── managers.py         # Package manager implementations
```

### Testing Locally

```bash
# Navigate to the pkgx directory
cd pkgx

# Test the tool without installing
uvx --from . pkgx list-managers

# Test specific commands with dry-run
uvx --from . pkgx install git --dry-run
```

### Building and Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires configuration)
uv publish
```

## Contributing

1. Add support for new package managers by creating a new class in `managers.py`
2. Extend the auto-detection logic in `detect_package_manager()`
3. Update the documentation and examples

## License

MIT License - see the LICENSE file for details.
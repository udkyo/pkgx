"""
Package manager detection and command execution
"""

import os
import platform
import shutil
import subprocess
from typing import List, Optional, Dict, Any


class PackageManager:
    """Base class for package managers"""

    def __init__(self, name: str, command: str):
        self.name = name
        self.command = command

    def is_available(self) -> bool:
        """Check if this package manager is available on the system"""
        return shutil.which(self.command) is not None

    def install(self, packages: List[str], **kwargs) -> int:
        """Install packages"""
        raise NotImplementedError

    def remove(self, packages: List[str], **kwargs) -> int:
        """Remove packages"""
        raise NotImplementedError

    def update(self, **kwargs) -> int:
        """Update package lists"""
        raise NotImplementedError

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        """Upgrade packages"""
        raise NotImplementedError

    def search(self, query: str, **kwargs) -> int:
        """Search for packages"""
        raise NotImplementedError

    def _run_command(self, args: List[str], **kwargs) -> int:
        """Run a command and return exit code"""
        try:
            result = subprocess.run([self.command] + args, **kwargs)
            return result.returncode
        except FileNotFoundError:
            print(f"Error: {self.command} not found")
            return 1
        except Exception as e:
            print(f"Error running {self.command}: {e}")
            return 1


class AptManager(PackageManager):
    """Debian/Ubuntu APT package manager"""

    def __init__(self):
        super().__init__("apt", "apt")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install", "-y"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["remove", "-y"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["update"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["upgrade", "-y"] + packages)
        return self._run_command(["upgrade", "-y"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class YumManager(PackageManager):
    """RHEL/CentOS/Fedora YUM package manager"""

    def __init__(self):
        super().__init__("yum", "yum")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install", "-y"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["remove", "-y"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["check-update"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["update", "-y"] + packages)
        return self._run_command(["update", "-y"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class DnfManager(PackageManager):
    """Fedora/RHEL 8+ DNF package manager"""

    def __init__(self):
        super().__init__("dnf", "dnf")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install", "-y"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["remove", "-y"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["check-update"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["update", "-y"] + packages)
        return self._run_command(["update", "-y"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class MicroDnfManager(PackageManager):
    """MicroDNF package manager (minimal container environments)"""

    def __init__(self):
        super().__init__("microdnf", "microdnf")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install", "-y"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["remove", "-y"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["repolist"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["update", "-y"] + packages)
        return self._run_command(["update", "-y"])

    def search(self, query: str, **kwargs) -> int:
        print("Search not supported by microdnf")
        return 1


class ZypperManager(PackageManager):
    """openSUSE Zypper package manager"""

    def __init__(self):
        super().__init__("zypper", "zypper")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install", "-y"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["remove", "-y"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["refresh"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["update", "-y"] + packages)
        return self._run_command(["update", "-y"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class ApkManager(PackageManager):
    """Alpine Linux APK package manager"""

    def __init__(self):
        super().__init__("apk", "apk")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["add"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["del"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["update"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["upgrade"] + packages)
        return self._run_command(["upgrade"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class BrewManager(PackageManager):
    """Homebrew package manager (macOS/Linux)"""

    def __init__(self):
        super().__init__("brew", "brew")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install"] + packages)

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["uninstall"] + packages)

    def update(self, **kwargs) -> int:
        return self._run_command(["update"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["upgrade"] + packages)
        return self._run_command(["upgrade"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


class ChocolateyManager(PackageManager):
    """Chocolatey package manager (Windows)"""

    def __init__(self):
        super().__init__("chocolatey", "choco")

    def install(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["install"] + packages + ["-y"])

    def remove(self, packages: List[str], **kwargs) -> int:
        return self._run_command(["uninstall"] + packages + ["-y"])

    def update(self, **kwargs) -> int:
        return self._run_command(["outdated"])

    def upgrade(self, packages: Optional[List[str]] = None, **kwargs) -> int:
        if packages:
            return self._run_command(["upgrade"] + packages + ["-y"])
        return self._run_command(["upgrade", "all", "-y"])

    def search(self, query: str, **kwargs) -> int:
        return self._run_command(["search", query])


# Registry of all package managers
PACKAGE_MANAGERS = [
    AptManager(),
    DnfManager(),
    MicroDnfManager(),
    YumManager(),
    ZypperManager(),
    ApkManager(),
    BrewManager(),
    ChocolateyManager(),
]


def detect_package_manager() -> Optional[PackageManager]:
    """Detect the best available package manager for the current system"""

    # Check for available package managers
    available_managers = [pm for pm in PACKAGE_MANAGERS if pm.is_available()]

    if not available_managers:
        return None

    # Priority order based on system type and common usage
    system = platform.system().lower()

    # Platform-specific preferences
    if system == "windows":
        # Prefer chocolatey on Windows
        for pm in available_managers:
            if pm.name == "chocolatey":
                return pm

    elif system == "darwin":
        # Prefer brew on macOS
        for pm in available_managers:
            if pm.name == "brew":
                return pm

    elif system == "linux":
        # Check for distribution-specific managers
        if os.path.exists("/etc/debian_version"):
            # Debian/Ubuntu - prefer apt
            for pm in available_managers:
                if pm.name == "apt":
                    return pm

        elif os.path.exists("/etc/redhat-release") or os.path.exists("/etc/fedora-release"):
            # RHEL/CentOS/Fedora - prefer dnf, then yum
            for pm_name in ["dnf", "yum"]:
                for pm in available_managers:
                    if pm.name == pm_name:
                        return pm

        elif os.path.exists("/etc/alpine-release"):
            # Alpine Linux - prefer apk
            for pm in available_managers:
                if pm.name == "apk":
                    return pm

        elif os.path.exists("/etc/SuSE-release") or os.path.exists("/etc/SUSE-brand"):
            # openSUSE - prefer zypper
            for pm in available_managers:
                if pm.name == "zypper":
                    return pm

    # Fallback to first available manager
    return available_managers[0]
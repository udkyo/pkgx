"""
Universal Package Manager (pkgx) CLI
"""

import argparse
import sys
from typing import List, Optional

from .managers import detect_package_manager, PACKAGE_MANAGERS


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        prog="pkgx",
        description="Universal Package Manager - A wrapper for various system package managers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pkgx install git vim          # Install packages
  pkgx remove old-package       # Remove packages
  pkgx update                   # Update package lists
  pkgx upgrade                  # Upgrade all packages
  pkgx upgrade git vim          # Upgrade specific packages
  pkgx search firefox           # Search for packages
  pkgx list-managers            # List available package managers
        """
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install packages")
    install_parser.add_argument("packages", nargs="+", help="Packages to install")
    install_parser.add_argument("--manager", "-m", help="Force specific package manager")
    install_parser.add_argument("--dry-run", "-n", action="store_true", help="Show command that would be run")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove packages")
    remove_parser.add_argument("packages", nargs="+", help="Packages to remove")
    remove_parser.add_argument("--manager", "-m", help="Force specific package manager")
    remove_parser.add_argument("--dry-run", "-n", action="store_true", help="Show command that would be run")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update package lists")
    update_parser.add_argument("--manager", "-m", help="Force specific package manager")
    update_parser.add_argument("--dry-run", "-n", action="store_true", help="Show command that would be run")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade packages")
    upgrade_parser.add_argument("packages", nargs="*", help="Specific packages to upgrade (optional)")
    upgrade_parser.add_argument("--manager", "-m", help="Force specific package manager")
    upgrade_parser.add_argument("--dry-run", "-n", action="store_true", help="Show command that would be run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for packages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--manager", "-m", help="Force specific package manager")
    search_parser.add_argument("--dry-run", "-n", action="store_true", help="Show command that would be run")

    # List managers command
    list_parser = subparsers.add_parser("list-managers", help="List available package managers")

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    # Parse arguments
    args = parser.parse_args()

    # Handle no command
    if not args.command:
        parser.print_help()
        return 0

    # Handle version command
    if args.command == "version":
        from . import __version__
        print(f"pkgx version {__version__}")
        return 0

    # Handle list-managers command
    if args.command == "list-managers":
        return list_available_managers()

    # Get package manager
    if hasattr(args, 'manager') and args.manager:
        # User specified a manager
        pm = get_manager_by_name(args.manager)
        if not pm:
            print(f"Error: Package manager '{args.manager}' not found or not available")
            print("Use 'pkgx list-managers' to see available managers")
            return 1
    else:
        # Auto-detect package manager
        pm = detect_package_manager()
        if not pm:
            print("Error: No package manager found on this system")
            print("Supported package managers: apt, dnf, yum, microdnf, zypper, apk, brew, choco")
            return 1

    # Show which manager we're using
    if hasattr(args, 'dry_run') and args.dry_run:
        print(f"Using package manager: {pm.name}")

    # Execute command
    try:
        if args.command == "install":
            if args.dry_run:
                print(f"Would run: {pm.command} install {' '.join(args.packages)}")
                return 0
            return pm.install(args.packages)

        elif args.command == "remove":
            if args.dry_run:
                print(f"Would run: {pm.command} remove {' '.join(args.packages)}")
                return 0
            return pm.remove(args.packages)

        elif args.command == "update":
            if args.dry_run:
                print(f"Would run: {pm.command} update")
                return 0
            return pm.update()

        elif args.command == "upgrade":
            if args.dry_run:
                if args.packages:
                    print(f"Would run: {pm.command} upgrade {' '.join(args.packages)}")
                else:
                    print(f"Would run: {pm.command} upgrade")
                return 0
            return pm.upgrade(args.packages if args.packages else None)

        elif args.command == "search":
            if args.dry_run:
                print(f"Would run: {pm.command} search {args.query}")
                return 0
            return pm.search(args.query)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


def list_available_managers() -> int:
    """List all available package managers"""
    print("Available package managers:")
    print()

    detected_pm = detect_package_manager()

    for pm in PACKAGE_MANAGERS:
        status = "[+] available" if pm.is_available() else "[-] not available"
        default_marker = " (auto-detected)" if pm == detected_pm else ""
        print(f"  {pm.name:12} - {pm.command:12} {status}{default_marker}")

    if detected_pm:
        print()
        print(f"Auto-detected package manager: {detected_pm.name}")
    else:
        print()
        print("No package manager auto-detected")

    return 0


def get_manager_by_name(name: str):
    """Get a package manager by name"""
    for pm in PACKAGE_MANAGERS:
        if pm.name == name and pm.is_available():
            return pm
    return None


if __name__ == "__main__":
    sys.exit(main())
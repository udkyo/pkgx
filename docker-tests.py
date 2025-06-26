#!/usr/bin/env python3
"""
Docker-based test runner for pkgx across different Linux distributions
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


class DockerTestRunner:
    """Runs pkgx tests across different Docker environments"""

    def __init__(self, source_dir: Path, verbose: bool = False):
        self.source_dir = source_dir
        self.verbose = verbose
        self.results = {}

        # Test distributions - representative sample of different package managers
        self.distributions = {
            "ubuntu:24.04": {
                "name": "Ubuntu 24.04",
                "expected_manager": "apt",
                "install_cmd": "apt-get update && apt-get install -y"
            },
            "debian:12": {
                "name": "Debian 12",
                "expected_manager": "apt",
                "install_cmd": "apt-get update && apt-get install -y"
            },
            "fedora:39": {
                "name": "Fedora 39",
                "expected_manager": "dnf",
                "install_cmd": "dnf install -y"
            },
            "registry.access.redhat.com/ubi9/ubi-minimal": {
                "name": "RHEL 9 UBI Minimal",
                "expected_manager": "microdnf",
                "install_cmd": "microdnf install -y"
            },
            "opensuse/leap:15.5": {
                "name": "openSUSE Leap 15.5",
                "expected_manager": "zypper",
                "install_cmd": "zypper install -y"
            },
            "alpine:3.18": {
                "name": "Alpine 3.18",
                "expected_manager": "apk",
                "install_cmd": "apk add"
            }
        }

    def create_test_dockerfile(self, base_image: str, expected_manager: str, install_cmd: str) -> str:
        """Create Dockerfile for testing"""

        # Base setup commands - install Python, pip, and curl
        if "alpine" in base_image:
            setup_commands = [
                "apk add --no-cache python3 py3-pip curl bash",
                "ln -sf python3 /usr/bin/python"
            ]
        elif "ubi" in base_image or "rhel" in base_image:
            setup_commands = [
                f"{install_cmd} python3 python3-pip curl",
                "ln -sf python3 /usr/bin/python"
            ]
        else:
            setup_commands = [
                f"{install_cmd} python3 python3-pip curl",
                "ln -sf python3 /usr/bin/python"
            ]

        dockerfile_content = f"""
FROM {base_image}

# Install system dependencies
RUN {' && '.join(setup_commands)}

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /test

# Copy pkgx source and test script
COPY pkgx/ ./pkgx/
COPY test_pkgx.py ./test_pkgx.py

# Run tests
CMD sh -c "echo 'Starting pkgx tests...' && if uv run test_pkgx.py; then echo 'Tests passed!'; else echo 'Tests failed!'; exit 1; fi"
"""
        return dockerfile_content

    def run_test_for_distribution(self, image_tag: str, distro_info: Dict[str, str]) -> Dict[str, Any]:
        """Run tests for a specific distribution"""
        print(f"\n[DOCKER] Testing {distro_info['name']} ({image_tag})")

        result = {
            "image": image_tag,
            "name": distro_info["name"],
            "expected_manager": distro_info["expected_manager"],
            "success": False,
            "output": "",
            "error": ""
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Copy pkgx source and test script to temp directory
                shutil.copytree(self.source_dir / "pkgx", temp_path / "pkgx")
                shutil.copy2(self.source_dir / "test_pkgx.py", temp_path / "test_pkgx.py")

                # Create Dockerfile
                dockerfile_content = self.create_test_dockerfile(
                    image_tag,
                    distro_info["expected_manager"],
                    distro_info["install_cmd"]
                )

                dockerfile_path = temp_path / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)

                # Build Docker image
                image_name = f"pkgx-test-{image_tag.replace(':', '-').replace('/', '-')}"

                if self.verbose:
                    print(f"[DOCKER] Building image {image_name}...")

                build_result = subprocess.run(
                    ["docker", "build", "-t", image_name, str(temp_path)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if build_result.returncode != 0:
                    result["error"] = f"Build failed: {build_result.stderr}"
                    return result

                # Run tests in container
                if self.verbose:
                    print(f"[DOCKER] Running tests in {image_name}...")

                run_result = subprocess.run(
                    ["docker", "run", "--rm", image_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                result["output"] = run_result.stdout
                result["error"] = run_result.stderr
                result["success"] = run_result.returncode == 0

                # Clean up image
                subprocess.run(
                    ["docker", "rmi", image_name],
                    capture_output=True,
                    text=True
                )

            except subprocess.TimeoutExpired:
                result["error"] = "Test timed out"
            except Exception as e:
                result["error"] = f"Unexpected error: {e}"

        return result

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run_all_tests(self, selected_distros: Optional[List[str]] = None) -> bool:
        """Run tests across all distributions"""
        if not self.check_docker_available():
            print("[ERROR] Docker is not available or not running")
            print("Please install Docker and ensure it's running")
            return False

        # Filter distributions if specific ones requested
        if selected_distros:
            test_distros = {k: v for k, v in self.distributions.items() if k in selected_distros}
            if not test_distros:
                print(f"[ERROR] No matching distributions found for: {selected_distros}")
                return False
        else:
            test_distros = self.distributions

        print(f"[TEST] Running pkgx Docker Tests")
        print(f"Testing {len(test_distros)} distributions...")

        all_success = True

        for image_tag, distro_info in test_distros.items():
            result = self.run_test_for_distribution(image_tag, distro_info)
            self.results[image_tag] = result

            if result["success"]:
                print(f"✅ {result['name']}: PASSED")
                if self.verbose and result["output"]:
                    # Show the detailed test output in verbose mode
                    print(f"   Test output:")
                    for line in result["output"].splitlines():
                        if line.strip():  # Skip empty lines
                            print(f"   {line}")
            else:
                print(f"❌ {result['name']}: FAILED")
                if self.verbose:
                    if result["error"]:
                        print(f"   Error: {result['error']}")
                    if result["output"]:
                        print(f"   Output: {result['output']}")
                all_success = False

        return all_success

    def print_summary(self):
        """Print test summary"""
        if not self.results:
            return

        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["success"])
        failed = total - passed

        print(f"\n📊 Docker Test Summary:")
        print(f"Total distributions: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed > 0:
            print(f"\n❌ Failed distributions:")
            for image, result in self.results.items():
                if not result["success"]:
                    print(f"  • {result['name']}: {result['error'][:100]}...")

        if passed == total:
            print(f"\n🎉 All Docker tests passed!")
        else:
            print(f"\n💥 {failed} Docker test(s) failed!")


def main():
    parser = argparse.ArgumentParser(description="Run pkgx tests across Docker containers")
    parser.add_argument(
        "--distros",
        nargs="+",
        help="Specific distributions to test (e.g., ubuntu:24.04 fedora:39)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available distributions"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Determine source directory (should contain pkgx/ and test_pkgx.py)
    source_dir = Path(__file__).parent

    if not (source_dir / "pkgx").exists():
        print("[ERROR] pkgx source directory not found. Run from the pkgx directory.")
        return 1

    if not (source_dir / "test_pkgx.py").exists():
        print("[ERROR] test_pkgx.py not found. Run from the pkgx directory.")
        return 1

    runner = DockerTestRunner(source_dir, verbose=args.verbose)

    if args.list:
        print("Available Docker distributions for testing:")
        for image, info in runner.distributions.items():
            print(f"  {image:<40} {info['name']}")
        return 0

    success = runner.run_all_tests(args.distros)
    runner.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Docker-based test runner for UPM across different Linux distributions
"""

import subprocess
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
import shutil

# Test configurations for different distributions
DISTRIBUTIONS = {
    "ubuntu:24.04": {
        "name": "Ubuntu 24.04",
        "setup_commands": [
            "apt-get update",
            "apt-get install -y curl",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "apt"
    },
    "fedora:39": {
        "name": "Fedora 39",
        "setup_commands": [
            "dnf install -y curl",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "dnf"
    },
    "almalinux:9": {
        "name": "AlmaLinux 9",
        "setup_commands": [
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "dnf"
    },
    "registry.access.redhat.com/ubi9/ubi-minimal": {
        "name": "UBI 9 Minimal",
        "setup_commands": [
            "microdnf install -y bash tar gzip",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "microdnf"
    },
    "alpine:3.18": {
        "name": "Alpine 3.18",
        "setup_commands": [
            "apk add --no-cache curl bash",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "apk"
    },
    "opensuse/leap:15.5": {
        "name": "openSUSE Leap 15.5",
        "setup_commands": [
            "zypper install -y curl tar gzip",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "export PATH=\"$HOME/.cargo/bin:$PATH\""
        ],
        "expected_manager": "zypper"
    }
}


class DockerTestRunner:
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.results = {}
        
    def check_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def create_test_script(self) -> str:
        """Create the test script for containers"""
        # Use explicit \n to ensure Unix line endings
        script_lines = [
            "#!/bin/bash -e",
            "",
            "# Setup UV and Python environment", 
            "export PATH=\"$HOME/.local/bin:$PATH\"",
            "",
            "# Copy UPM source and test script",
            "cd /workspace",
            "",
            "# Run the test script with proper error handling",
            "echo \"[TEST] Running UPM tests...\"",
            "if uv run test_upm.py; then",
            "    echo \"[SUCCESS] Tests completed successfully\"",
            "    exit 0",
            "else",
            "    echo \"[FAILURE] Tests failed with exit code $?\"",
            "    exit 1",
            "fi",
            ""
        ]
        return '\n'.join(script_lines)
    
    def run_container_test(self, image: str, config: Dict) -> Tuple[bool, str]:
        """Run tests in a specific container"""
        print(f"\n[DOCKER] Testing {config['name']} ({image})")
        print("=" * 50)
        
        try:
            # Create temporary directory for this test
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy source files to temp directory
                shutil.copytree(self.source_dir / "upm", temp_path / "upm")
                shutil.copy2(self.source_dir / "test_upm.py", temp_path / "test_upm.py")
                shutil.copy2(self.source_dir / "pyproject.toml", temp_path / "pyproject.toml")
                
                # Create test script with Unix line endings
                test_script = self.create_test_script()
                (temp_path / "run_tests.sh").write_text(test_script, newline='\n')
                (temp_path / "run_tests.sh").chmod(0o755)
                
                # Build Docker command
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{temp_path}:/workspace",
                    "-w", "/workspace",
                    image,
                    "sh", "-c"
                ]
                
                # Create full command with setup
                full_command = " && ".join(config["setup_commands"] + [
                    "bash /workspace/run_tests.sh"
                ])
                
                docker_cmd.append(full_command)
                
                # Run the test
                print(f"[START] Starting container...")
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                success = result.returncode == 0
                output = result.stdout + "\n" + result.stderr
                
                # Additional check for known failure patterns
                if success:
                    failure_patterns = [
                        "No solution found when resolving",
                        "requirements are unsatisfiable",
                        "[FAILURE]",
                        "ImportError:",
                        "ModuleNotFoundError:",
                        "Error importing UPM modules"
                    ]
                    
                    combined_output = output.lower()
                    for pattern in failure_patterns:
                        if pattern.lower() in combined_output:
                            success = False
                            break
                
                if success:
                    print(f"[PASS] {config['name']} tests PASSED")
                else:
                    print(f"[FAIL] {config['name']} tests FAILED")
                    print(f"Exit code: {result.returncode}")
                    if result.stderr:
                        print(f"Error output:\n{result.stderr}")
                
                return success, output
                
        except subprocess.TimeoutExpired:
            error_msg = f"Tests timed out after 5 minutes"
            print(f"[TIMEOUT] {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error running container: {e}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg
    
    def run_all_tests(self, selected_distros: List[str] = None) -> Dict[str, Tuple[bool, str]]:
        """Run tests across all or selected distributions"""
        if not self.check_docker_available():
            print("[ERROR] Docker is not available. Please install Docker to run these tests.")
            return {}
        
        # Filter distributions if specific ones are requested
        test_distros = DISTRIBUTIONS
        if selected_distros:
            test_distros = {k: v for k, v in DISTRIBUTIONS.items() 
                          if k in selected_distros or v['name'] in selected_distros}
        
        print(f"[TEST] Running UPM Docker Tests")
        print(f"Testing {len(test_distros)} distributions")
        print("=" * 60)
        
        results = {}
        for image, config in test_distros.items():
            success, output = self.run_container_test(image, config)
            results[config['name']] = (success, output)
        
        return results
    
    def print_summary(self, results: Dict[str, Tuple[bool, str]]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("[SUMMARY] DOCKER TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for distro, (success, output) in results.items():
            status = "[PASS]" if success else "[FAIL]"
            print(f"{status}: {distro}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print(f"\nTotal: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("\n[SUCCESS] All Docker tests passed!")
        else:
            print(f"\n[FAILURE] {failed} distribution(s) failed!")
            print("\nFailed distributions:")
            for distro, (success, output) in results.items():
                if not success:
                    print(f"\n[DETAILS] {distro}:")
                    # Show last few lines of output for debugging
                    lines = output.strip().split('\n')
                    for line in lines[-10:]:
                        print(f"  {line}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run UPM tests across Docker containers")
    parser.add_argument("--distros", nargs="*", 
                       help="Specific distributions to test (default: all)")
    parser.add_argument("--list", action="store_true",
                       help="List available distributions")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available distributions:")
        for image, config in DISTRIBUTIONS.items():
            print(f"  {config['name']:20} ({image})")
        return
    
    # Find source directory
    source_dir = Path(__file__).parent
    if not (source_dir / "upm").exists():
        print("[ERROR] UPM source directory not found. Run from the upm directory.")
        sys.exit(1)
    
    # Run tests
    runner = DockerTestRunner(source_dir)
    results = runner.run_all_tests(args.distros)
    
    if results:
        runner.print_summary(results)
        
        # Exit with error code if any tests failed
        failed_count = sum(1 for success, _ in results.values() if not success)
        sys.exit(0 if failed_count == 0 else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main() 
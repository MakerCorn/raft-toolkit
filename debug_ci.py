#!/usr/bin/env python3
"""
Debug script to help diagnose CI pytest issues.
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=== CI Debug Information ===")
    print()
    
    # Check current working directory
    print(f"Current working directory: {Path.cwd()}")
    print()
    
    # Check pytest.ini content
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        print("pytest.ini content:")
        print(pytest_ini.read_text())
        print()
    else:
        print("❌ pytest.ini not found!")
        print()
    
    # Check if pytest can see the markers
    print("Pytest markers:")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--markers"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # Look for our custom markers
            markers = result.stdout
            for marker in ["unit", "integration", "api", "cli"]:
                if f"@pytest.mark.{marker}" in markers:
                    print(f"✅ {marker} marker found")
                else:
                    print(f"❌ {marker} marker NOT found")
        else:
            print(f"❌ pytest --markers failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error checking markers: {e}")
    print()
    
    # Check test discovery for each type
    test_types = ["unit", "integration", "api", "cli"]
    for test_type in test_types:
        print(f"Checking {test_type} test discovery:")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "-m", test_type, "--collect-only", "--quiet"
            ], capture_output=True, text=True, timeout=30)
            
            if "collected" in result.stdout:
                # Extract collection info
                lines = result.stdout.split('\n')
                for line in lines:
                    if "collected" in line and "items" in line:
                        print(f"  {line.strip()}")
            else:
                print(f"  ❌ No collection info found")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()
    
    # Check if there are test files in expected locations
    print("Test file structure:")
    tests_dir = Path("tests")
    if tests_dir.exists():
        for subdir in ["unit", "integration", "api", "cli"]:
            subdir_path = tests_dir / subdir
            if subdir_path.exists():
                test_files = list(subdir_path.glob("test_*.py"))
                print(f"  {subdir}/: {len(test_files)} test files")
                for test_file in test_files[:3]:  # Show first 3
                    print(f"    - {test_file.name}")
                if len(test_files) > 3:
                    print(f"    ... and {len(test_files) - 3} more")
            else:
                print(f"  {subdir}/: ❌ directory not found")
    else:
        print("  ❌ tests/ directory not found")
    print()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Verify pytest configuration is working correctly.
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=== Pytest Configuration Verification ===")
    print()
    
    # Check current directory
    print(f"Working directory: {Path.cwd()}")
    print()
    
    # Check pytest.ini exists and content
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        print("✅ pytest.ini found")
        content = pytest_ini.read_text()
        print(f"First line: {content.splitlines()[0]}")
        
        # Check for markers section
        if "markers =" in content:
            print("✅ markers section found")
            # Extract markers
            lines = content.splitlines()
            in_markers = False
            markers = []
            for line in lines:
                if line.strip().startswith("markers ="):
                    in_markers = True
                    continue
                elif in_markers and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    break
                elif in_markers and line.strip():
                    marker = line.strip().split(":")[0] if ":" in line else line.strip()
                    markers.append(marker)
            print(f"Found markers: {markers}")
        else:
            print("❌ No markers section found")
    else:
        print("❌ pytest.ini not found")
    print()
    
    # Test pytest markers command
    print("=== Pytest Markers Command ===")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--markers"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            markers_output = result.stdout
            custom_markers = []
            for line in markers_output.splitlines():
                if any(marker in line for marker in ["unit", "integration", "api", "cli"]):
                    custom_markers.append(line.strip())
            
            if custom_markers:
                print("✅ Custom markers found:")
                for marker in custom_markers:
                    print(f"  {marker}")
            else:
                print("❌ No custom markers found in pytest --markers output")
                print("Full output:")
                print(markers_output[:500] + "..." if len(markers_output) > 500 else markers_output)
        else:
            print(f"❌ pytest --markers failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error running pytest --markers: {e}")
    print()
    
    # Test collection for each marker
    test_markers = ["unit", "integration", "api", "cli"]
    for marker in test_markers:
        print(f"=== Testing {marker} marker ===")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "-m", marker, "--collect-only", "-q"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                if "collected" in output:
                    collection_line = [line for line in output.splitlines() if "collected" in line]
                    if collection_line:
                        print(f"✅ {collection_line[0]}")
                    else:
                        print("✅ Collection succeeded but no summary line found")
                else:
                    print("❌ No collection info found")
                    print(f"Output: {output[:200]}...")
            else:
                print(f"❌ Collection failed with code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:200]}...")
        except Exception as e:
            print(f"❌ Error testing {marker}: {e}")
        print()

if __name__ == "__main__":
    main()
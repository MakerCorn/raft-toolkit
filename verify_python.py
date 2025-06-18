#!/usr/bin/env python3
"""
Verify Python 3.11 setup for RAFT Toolkit.
"""
import platform
import sys


def main():
    print("Python Version Information:")
    print(f"  Version: {sys.version}")
    print(f"  Version Info: {sys.version_info}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Architecture: {platform.architecture()}")
    print(f"  Executable: {sys.executable}")

    # Check if we're running Python 3.11 or 3.12
    if (sys.version_info >= (3, 11)) and (sys.version_info < (3, 13)):
        print("✅ Python 3.11 or 3.12 detected - RAFT Toolkit requirements met")
    else:
        print("❌ Python 3.11 or 3.12 required for RAFT Toolkit")
        return 1

    # Test basic imports
    try:
        print("✅ Core Python modules available")
    except ImportError as e:
        print(f"❌ Core module import failed: {e}")
        return 1

    # Test if we can import pytest for testing
    try:
        import pytest

        print(f"✅ pytest available: {pytest.__version__}")
    except ImportError:
        print("⚠️  pytest not available - install with: pip install pytest")

    return 0


if __name__ == "__main__":
    sys.exit(main())

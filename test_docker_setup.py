#!/usr/bin/env python3
"""
Quick Docker setup validation script.

This script performs a basic validation of the Docker testing environment
without requiring the full Docker environment to be running.
"""

import os
import sys
from pathlib import Path


def validate_docker_files():
    """Validate that required Docker files exist."""
    project_root = Path(__file__).parent
    required_files = ["Dockerfile", "docker-compose.test.yml", "requirements.txt", "run_tests.py"]

    print("🔍 Checking Docker configuration files...")
    missing_files = []

    for filename in required_files:
        file_path = project_root / filename
        if not file_path.exists():
            missing_files.append(filename)
            print(f"❌ Missing: {filename}")
        else:
            print(f"✅ Found: {filename}")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required file(s)")
        return False

    print("\n✅ All required Docker files present")
    return True


def validate_docker_test_structure():
    """Validate Docker test directory structure."""
    project_root = Path(__file__).parent
    test_dirs = ["tests", "tests/docker", "tests/unit", "tests/integration", "tests/api", "tests/cli"]

    print("🔍 Checking test directory structure...")
    missing_dirs = []

    for dirname in test_dirs:
        dir_path = project_root / dirname
        if not dir_path.exists():
            missing_dirs.append(dirname)
            print(f"❌ Missing: {dirname}/")
        else:
            print(f"✅ Found: {dirname}/")

    if missing_dirs:
        print(f"\n⚠️  Missing {len(missing_dirs)} test directory(ies)")
        return False

    print("\n✅ All test directories present")
    return True


def validate_dockerfile_content():
    """Validate Dockerfile has required stages."""
    dockerfile_path = Path(__file__).parent / "Dockerfile"

    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False

    print("🔍 Checking Dockerfile content...")

    try:
        content = dockerfile_path.read_text()
        required_stages = ["base", "dependencies", "testing"]
        found_stages = []

        for stage in required_stages:
            if f"FROM {stage}" in content or f"AS {stage}" in content:
                found_stages.append(stage)
                print(f"✅ Found stage: {stage}")
            else:
                print(f"❌ Missing stage: {stage}")

        if len(found_stages) != len(required_stages):
            print(f"\n❌ Missing {len(required_stages) - len(found_stages)} required stage(s)")
            return False

        print("\n✅ All required Dockerfile stages present")
        return True

    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False


def validate_docker_compose_content():
    """Validate docker-compose.test.yml has required services."""
    compose_path = Path(__file__).parent / "docker-compose.test.yml"

    if not compose_path.exists():
        print("❌ docker-compose.test.yml not found")
        return False

    print("🔍 Checking docker-compose.test.yml content...")

    try:
        content = compose_path.read_text()
        required_services = ["raft-test"]
        found_services = []

        for service in required_services:
            if f"{service}:" in content:
                found_services.append(service)
                print(f"✅ Found service: {service}")
            else:
                print(f"❌ Missing service: {service}")

        # Check for testing environment variables
        test_env_vars = ["TESTING=true", "TEST_OUTPUT_DIR", "TEST_TEMP_DIR"]
        found_env_vars = []

        for env_var in test_env_vars:
            if env_var in content:
                found_env_vars.append(env_var)
                print(f"✅ Found environment config: {env_var}")
            else:
                print(f"❌ Missing environment config: {env_var}")

        success = len(found_services) == len(required_services) and len(found_env_vars) == len(test_env_vars)

        if success:
            print("\n✅ Docker Compose configuration is valid")
        else:
            print("\n❌ Docker Compose configuration has issues")

        return success

    except Exception as e:
        print(f"❌ Error reading docker-compose.test.yml: {e}")
        return False


def validate_docker_test_files():
    """Validate Docker test files exist."""
    project_root = Path(__file__).parent
    test_files = ["tests/docker/__init__.py", "tests/docker/test_docker_environment.py"]

    print("🔍 Checking Docker test files...")
    missing_files = []

    for filename in test_files:
        file_path = project_root / filename
        if not file_path.exists():
            missing_files.append(filename)
            print(f"❌ Missing: {filename}")
        else:
            print(f"✅ Found: {filename}")

    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} Docker test file(s)")
        return False

    print("\n✅ All Docker test files present")
    return True


def main():
    """Main validation function."""
    print("🐳 RAFT Toolkit Docker Setup Validator")
    print("=" * 50)

    validations = [
        ("Docker Files", validate_docker_files),
        ("Test Structure", validate_docker_test_structure),
        ("Dockerfile Content", validate_dockerfile_content),
        ("Docker Compose Content", validate_docker_compose_content),
        ("Docker Test Files", validate_docker_test_files),
    ]

    results = []
    for name, validation_func in validations:
        print(f"\n📋 {name}:")
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    total = len(results)
    print(f"\n🎯 Results: {passed}/{total} validations passed")

    if passed == total:
        print("\n🎉 Docker setup validation completed successfully!")
        print("\nNext steps:")
        print("  1. Build Docker image: docker compose -f docker-compose.test.yml build")
        print("  2. Run Docker tests: python scripts/test_docker.py")
        print("  3. Run full test suite: python scripts/test_docker.py --full")
        return 0
    else:
        print(f"\n❌ Docker setup validation failed ({total - passed} issues)")
        print("\nPlease fix the issues above before running Docker tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

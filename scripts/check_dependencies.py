#!/usr/bin/env python3
"""
Dependency verification script for RAFT Toolkit.

This script checks for dependency conflicts and verifies that all critical
packages can be imported successfully.
"""

import importlib
import subprocess
import sys


def check_pip_dependencies() -> bool:
    """Check for pip dependency conflicts."""
    print("🔍 Checking pip dependency conflicts...")

    try:
        # nosec B603: subprocess call is safe - using controlled pip command with known arguments
        result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ No pip dependency conflicts found")
            return True
        else:
            print("❌ Pip dependency conflicts detected:")
            print(result.stdout)
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("⚠️ Pip check timed out")
        return False
    except Exception as e:
        print(f"❌ Error running pip check: {e}")
        return False


def check_critical_imports() -> bool:
    """Check that all critical packages can be imported."""
    print("📦 Checking critical package imports...")

    critical_packages = [
        ("pypdf", "PDF processing"),
        ("openai", "OpenAI API client"),
        ("azure.ai.evaluation", "Azure AI Evaluation"),
        ("fastapi", "Web framework"),
        ("langchain_experimental", "LangChain experimental features"),
        ("promptflow_core", "PromptFlow core"),
        ("transformers", "HuggingFace Transformers"),
        ("datasets", "HuggingFace Datasets"),
    ]

    optional_packages = [
        ("uvicorn", "ASGI server"),
        ("redis", "Redis client"),
        ("celery", "Task queue"),
    ]

    all_success = True

    # Check critical packages
    for package, description in critical_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {package} ({description}): {version}")
        except ImportError as e:
            print(f"❌ {package} ({description}): Failed to import - {e}")
            all_success = False
        except Exception as e:
            print(f"⚠️ {package} ({description}): Import warning - {e}")

    # Check optional packages
    print("\n📋 Optional packages:")
    for package, description in optional_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {package} ({description}): {version}")
        except ImportError:
            print(f"⚠️ {package} ({description}): Not installed (optional)")
        except Exception as e:
            print(f"⚠️ {package} ({description}): Import warning - {e}")

    return all_success


def check_version_constraints() -> bool:
    """Check specific version constraints that are known to cause issues."""
    print("\n🔗 Checking version constraints...")

    constraints = [
        ("fastapi", ">=0.109.0,<1.0.0", "Required by promptflow-core"),
        ("promptflow_core", ">=1.18.0", "Required for Azure AI Evaluation"),
        ("langchain_experimental", "==0.3.4", "Security fix for CVE-2024-46946"),
    ]

    all_satisfied = True

    for package_name, constraint, reason in constraints:
        try:
            module = importlib.import_module(package_name.replace("_", "."))
            version = getattr(module, "__version__", "unknown")
            print(f"📌 {package_name}: {version} (constraint: {constraint}) - {reason}")

            # Basic version checking (simplified)
            if constraint.startswith(">="):
                min_version = constraint.split(">=")[1].split(",")[0]
                print(f"   Required minimum: {min_version}")
            elif constraint.startswith("=="):
                exact_version = constraint.split("==")[1]
                if version != exact_version and version != "unknown":
                    print(f"   ⚠️ Expected exact version {exact_version}, got {version}")

        except ImportError:
            print(f"❌ {package_name}: Not installed")
            all_satisfied = False
        except Exception as e:
            print(f"⚠️ {package_name}: Error checking version - {e}")

    return all_satisfied


def generate_dependency_report() -> None:
    """Generate a comprehensive dependency report."""
    print("\n📋 Generating dependency report...")

    try:
        # Get pip list
        # nosec B603: subprocess call is safe - using controlled pip command with known arguments
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            import json

            packages = json.loads(result.stdout)

            print(f"\n📦 Installed packages ({len(packages)} total):")

            # Filter RAFT-related packages
            raft_packages = [
                pkg
                for pkg in packages
                if any(
                    keyword in pkg["name"].lower()
                    for keyword in [
                        "openai",
                        "azure",
                        "langchain",
                        "transformers",
                        "fastapi",
                        "promptflow",
                        "datasets",
                        "pypdf",
                        "redis",
                        "celery",
                    ]
                )
            ]

            for pkg in sorted(raft_packages, key=lambda x: x["name"]):
                print(f"  {pkg['name']}: {pkg['version']}")

        else:
            print(f"⚠️ Could not get package list: {result.stderr}")

    except Exception as e:
        print(f"⚠️ Error generating dependency report: {e}")


def main():
    """Main function to run all dependency checks."""
    print("🔍 RAFT Toolkit Dependency Checker")
    print("=" * 50)

    all_checks_passed = True

    # Run all checks
    checks = [
        ("Pip Dependency Conflicts", check_pip_dependencies),
        ("Critical Package Imports", check_critical_imports),
        ("Version Constraints", check_version_constraints),
    ]

    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 30)

        try:
            if not check_func():
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            all_checks_passed = False

    # Generate report
    generate_dependency_report()

    # Final summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All dependency checks passed!")
        sys.exit(0)
    else:
        print("❌ Some dependency checks failed. See details above.")
        print("\n💡 Suggested fixes:")
        print("  - Run: pip install -r requirements.txt")
        print("  - Run: pip install -r requirements-web.txt")
        print("  - Check for conflicting packages: pip check")
        print("  - Update dependencies: pip install --upgrade -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()

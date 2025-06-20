#!/usr/bin/env python3
"""
Documentation generator for RAFT Toolkit.
Updates README.md with current documentation structure.
"""

from pathlib import Path


def get_docs_structure():
    """Get the current documentation structure."""
    docs_dir = Path("docs")
    root_dir = Path(".")
    
    docs = []
    
    # Get docs from docs/ directory
    if docs_dir.exists():
        for doc_file in sorted(docs_dir.glob("*.md")):
            docs.append(f"docs/{doc_file.name}")
    
    # Get specific documentation files from root directory
    root_docs = ["COMBINED_RELEASES.md"]
    for doc_name in root_docs:
        doc_path = root_dir / doc_name
        if doc_path.exists():
            docs.append(doc_name)

    return docs


def generate_docs_section():
    """Generate the documentation section for README."""
    docs = get_docs_structure()

    if not docs:
        return "No documentation files found."

    # Group docs by category (include full paths)
    categories = {
        "Getting Started": ["docs/INSTALLATION_GUIDE.md", "docs/REQUIREMENTS.md", "docs/PYTHON_311_SETUP.md"],
        "Architecture & Design": ["docs/ARCHITECTURE.md", "docs/PROJECT_STRUCTURE.md", "docs/CONFIGURATION.md"],
        "Usage & Reference": [
            "docs/CLI-Reference.md",
            "docs/CLI-Quick-Reference.md", 
            "docs/INPUT_SOURCES.md",
            "docs/TOOLS.md",
            "docs/WEB_INTERFACE.md",
        ],
        "Development & Testing": [
            "docs/TESTING.md",
            "docs/TEST_COVERAGE_IMPROVEMENTS.md",
            "docs/TEST_DIRECTORIES.md",
            "docs/DEPENDENCY_TROUBLESHOOTING.md",
        ],
        "Deployment & Operations": ["docs/DEPLOYMENT.md", "docs/KUBERNETES.md", "docs/BUILD_OPTIMIZATION.md", "docs/CI_OPTIMIZATION.md"],
        "Releases & Changes": ["docs/RELEASES.md", "COMBINED_RELEASES.md", "docs/QUALITY_TRANSITION.md"],
        "Technical Guides": ["docs/NOMIC_EMBEDDINGS.md"],
        "Troubleshooting & Fixes": [
            "docs/ALL_TESTS_FIX.md",
            "docs/API_TESTS_FIX.md",
            "docs/FLAKE8_FIX.md",
            "docs/TEST_FIXES_SUMMARY.md",
            "docs/TESTING_FIXES.md",
        ],
    }

    # Build documentation section
    section = "## 📚 Documentation\n\n"

    for category, category_docs in categories.items():
        # Check if any docs in this category exist
        existing_docs = [doc for doc in category_docs if doc in docs]
        if existing_docs:
            section += f"### {category}\n\n"
            for doc in existing_docs:
                # Extract just the filename for title, handle both docs/ and root paths
                filename = doc.split("/")[-1]
                title = filename.replace(".md", "").replace("_", " ").replace("-", " ").title()
                section += f"- [{title}]({doc})\n"
            section += "\n"

    # Add any uncategorized docs
    categorized_docs = []
    for category_docs in categories.values():
        categorized_docs.extend(category_docs)

    uncategorized = [doc for doc in docs if doc not in categorized_docs]
    if uncategorized:
        section += "### Other Documentation\n\n"
        for doc in uncategorized:
            # Extract just the filename for title, handle both docs/ and root paths
            filename = doc.split("/")[-1]
            title = filename.replace(".md", "").replace("_", " ").replace("-", " ").title()
            section += f"- [{title}]({doc})\n"
        section += "\n"

    return section


def update_readme():
    """Update README.md with current documentation structure."""
    readme_path = Path("README.md")

    if not readme_path.exists():
        print("README.md not found")
        return

    # Read current README
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Generate new docs section
    new_docs_section = generate_docs_section()

    # Find and replace documentation section
    start_marker = "## 📚 Documentation"
    end_marker = "## "  # Next section

    lines = content.split("\n")
    new_lines = []
    in_docs_section = False
    docs_section_found = False

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith(start_marker):
            # Found start of docs section
            in_docs_section = True
            docs_section_found = True
            # Add new docs section
            new_lines.extend(new_docs_section.rstrip().split("\n"))
            i += 1
            continue

        if in_docs_section and line.startswith(end_marker) and line != start_marker:
            # Found end of docs section
            in_docs_section = False
            new_lines.append(line)
            i += 1
            continue

        if not in_docs_section:
            new_lines.append(line)

        i += 1

    # If no docs section found, add it before the last section
    if not docs_section_found:
        # Find a good place to insert (before Contributing or License)
        insert_index = len(new_lines)
        for i, line in enumerate(new_lines):
            if line.startswith("## 🤝 Contributing") or line.startswith("## 📄 License"):
                insert_index = i
                break

        new_lines.insert(insert_index, "")
        new_lines.insert(insert_index + 1, new_docs_section.rstrip())
        new_lines.insert(insert_index + 2, "")

    # Write updated README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    print(f"Updated README.md with {len(get_docs_structure())} documentation files")


if __name__ == "__main__":
    update_readme()

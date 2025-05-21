import re
from pathlib import Path
from typing import List

import pytest
import yaml

# Constants
DOCS_DIR = Path("docs")
TEMPLATES_DIR = DOCS_DIR / "templates"
API_DIR = Path("api")
CORE_DIR = Path("core")


def get_markdown_files() -> List[Path]:
    """Get all markdown files in the docs directory."""
    return list(DOCS_DIR.rglob("*.md"))


def get_python_files() -> List[Path]:
    """Get all Python files in the project."""
    return list(Path(".").rglob("*.py"))


def test_docs_structure():
    """Test that all required documentation files exist."""
    required_files = [
        "index.md",
        "getting-started/installation.md",
        "getting-started/quickstart.md",
        "user-guide/features.md",
        "api/overview.md",
        "api/endpoints.md",
        "development/architecture.md",
    ]

    for file in required_files:
        assert (
            DOCS_DIR / file
        ).exists(), f"Missing required documentation file: {file}"


def test_markdown_links():
    """Test that all markdown links are valid."""
    for md_file in get_markdown_files():
        content = md_file.read_text()

        # Find all markdown links
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

        for text, link in links:
            # Skip external links
            if link.startswith(("http://", "https://")):
                continue

            # Handle anchor links
            if "#" in link:
                file_path, _ = link.split("#", 1)
            else:
                file_path = link

            # Check if file exists
            if file_path:
                target_file = (md_file.parent / file_path).resolve()
                assert target_file.exists(), f"Broken link in {md_file}: {link}"


def test_code_blocks():
    """Test that code blocks are properly formatted."""
    for md_file in get_markdown_files():
        content = md_file.read_text()

        # Find all code blocks
        code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)

        for lang, code in code_blocks:
            if lang == "python":
                # Check for syntax errors in Python code
                try:
                    compile(code, "<string>", "exec")
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {md_file}:\n{str(e)}")


def test_api_documentation():
    """Test that API endpoints are properly documented."""
    api_docs = DOCS_DIR / "api" / "endpoints.md"
    assert api_docs.exists(), "API documentation file missing"

    # Get all API endpoints from the code
    api_files = list(API_DIR.rglob("*.py"))
    documented_endpoints = set()

    # Parse API documentation
    content = api_docs.read_text()
    for line in content.split("\n"):
        if line.startswith("```http"):
            endpoint = next((line for line in content.split("\n") if line.strip()), "")
            documented_endpoints.add(endpoint.strip())

    # Check if all endpoints are documented
    for api_file in api_files:
        content = api_file.read_text()
        endpoints = re.findall(
            r'@app\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)', content
        )
        for method, path in endpoints:
            endpoint = f"{method.upper()} {path}"
            assert (
                endpoint in documented_endpoints
            ), f"Undocumented endpoint: {endpoint}"


def test_example_code():
    """Test that example code in documentation is valid."""
    for md_file in get_markdown_files():
        content = md_file.read_text()

        # Find all Python code examples
        python_blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)

        for code in python_blocks:
            # Skip if it's just a comment
            if code.strip().startswith("#"):
                continue

            # Check for syntax errors
            try:
                compile(code, "<string>", "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in example code in {md_file}:\n{str(e)}")


def test_configuration_examples():
    """Test that configuration examples are valid YAML."""
    for md_file in get_markdown_files():
        content = md_file.read_text()

        # Find all YAML code blocks
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)

        for yaml_content in yaml_blocks:
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {md_file}:\n{str(e)}")


def test_docstring_coverage():
    """Test that all Python files have docstrings."""
    for py_file in get_python_files():
        # Skip test files and __init__.py
        if "test_" in str(py_file) or py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        # Check for module docstring
        if not content.strip().startswith('"""'):
            pytest.fail(f"Missing module docstring in {py_file}")

        # Check for function/method docstrings
        functions = re.findall(r"def\s+(\w+)\s*\(", content)
        for func in functions:
            func_def = re.search(r"def\s+" + func + r"\s*\(.*?\):", content)
            if func_def:
                next_line = content[func_def.end() :].split("\n")[0].strip()
                if not next_line.startswith('"""'):
                    pytest.fail(f"Missing docstring for function {func} in {py_file}")


if __name__ == "__main__":
    pytest.main([__file__])

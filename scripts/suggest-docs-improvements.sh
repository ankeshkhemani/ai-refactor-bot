#!/bin/bash
# Install required packages if not present
if ! command -v pip &> /dev/null; then
  echo "pip not found. Please install pip first."
  exit 1
fi

# Install required packages
pip install -q beautifulsoup4 markdown PyYAML

# Create temporary Python script for analysis
cat > /tmp/doc_analyzer.py << 'EOL'
import os
import re
import sys
from pathlib import Path
import markdown
from bs4 import BeautifulSoup
import yaml

def analyze_markdown_file(file_path):
    suggestions = []
    with open(file_path, 'r') as f:
        content = f.read()

    # Check for headings structure
    headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
    if len(headings) < 2:
        suggestions.append(f"Consider adding more sections to {file_path}")
    if not any(h.startswith('# ') for h in headings):
        suggestions.append(f"Add a main heading (# ) to {file_path}")

    # Check for code blocks
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
    if not code_blocks:
        suggestions.append(f"Consider adding code examples to {file_path}")

    # Check for links
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    if not links:
        suggestions.append(f"Consider adding relevant links to {file_path}")

    # Check for images
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
    if not images and len(content.split('\n')) > 50:
        suggestions.append(f"Consider adding diagrams or images to {file_path}")

    # Check for lists
    lists = re.findall(r'^\s*[-*+]\s+.+$', content, re.MULTILINE)
    if not lists and len(content.split('\n')) > 30:
        suggestions.append(f"Consider using bullet points or numbered lists in {file_path}")

    return suggestions

def analyze_docstring(file_path):
    suggestions = []
    with open(file_path, 'r') as f:
        content = f.read()

    # Find all functions and classes
    functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
    classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)

    for func in functions:
        # Check if function has docstring
        func_def = re.search(r'def\s+' + func + r'\s*\([^)]*\):', content)
        if func_def:
            next_line = content[func_def.end():].split('\n')[0].strip()
            if not next_line.startswith('"""'):
                suggestions.append(f"Add docstring to function {func} in {file_path}")

    for cls in classes:
        # Check if class has docstring
        class_def = re.search(r'class\s+' + cls + r'\s*[:\(]', content)
        if class_def:
            next_line = content[class_def.end():].split('\n')[0].strip()
            if not next_line.startswith('"""'):
                suggestions.append(f"Add docstring to class {cls} in {file_path}")

    return suggestions

def main():
    suggestions = []

    # Analyze markdown files
    for md_file in Path('docs').rglob('*.md'):
        suggestions.extend(analyze_markdown_file(md_file))

    # Analyze Python files
    for py_file in Path('.').rglob('*.py'):
        if (
            'venv' not in str(py_file)
            and 'test_' not in str(py_file)
            and py_file.name != '__init__.py'
        ):
            suggestions.extend(analyze_docstring(py_file))

    # Print suggestions
    if suggestions:
        print("\nDocumentation Improvement Suggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion}")
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
EOL

# Run the analyzer
python /tmp/doc_analyzer.py
result=$?

# Clean up
rm /tmp/doc_analyzer.py

exit $result

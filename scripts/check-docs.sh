#!/bin/bash
# Check if documentation needs updating
if git diff --name-only | grep -E '\.(py|md)$' > /dev/null; then
  echo "Documentation may need updating. Please check:"
  echo "1. Docstrings in modified Python files"
  echo "2. Relevant documentation in docs/"
  echo "3. Run 'mkdocs serve' to preview changes"
  exit 1
fi

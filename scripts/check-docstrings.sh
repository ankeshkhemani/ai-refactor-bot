#!/bin/bash
# Check for missing docstrings in modified Python files
for file in $(git diff --name-only | grep '\.py$'); do
  if ! grep -q '"""' "$file"; then
    echo "Warning: $file may be missing docstrings"
  fi
done

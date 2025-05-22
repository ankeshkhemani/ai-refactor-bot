#!/bin/bash
# Check if API changes are documented
if git diff --name-only | grep -E 'api/.*\.py$' > /dev/null; then
  if ! git diff --name-only | grep -E 'docs/api/.*\.md$' > /dev/null; then
    echo "Warning: API changes detected but no corresponding documentation updates found"
    echo "Please update docs/api/endpoints.md or docs/api/overview.md"
  fi
fi

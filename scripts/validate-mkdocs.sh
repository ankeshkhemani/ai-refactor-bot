#!/bin/bash
# Validate MkDocs configuration and build
if ! command -v mkdocs &> /dev/null; then
  echo "MkDocs not found. Installing..."
  pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python
fi

# Validate mkdocs.yml
if ! mkdocs build --strict &> /dev/null; then
  echo "MkDocs build failed. Please check your configuration."
  exit 1
fi

# Check for broken links
if ! command -v mkdocs-broken-links-plugin &> /dev/null; then
  echo "Installing mkdocs-broken-links-plugin..."
  pip install mkdocs-broken-links-plugin
fi

if ! mkdocs build --strict &> /dev/null; then
  echo "Found broken links in documentation."
  exit 1
fi

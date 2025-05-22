#!/bin/bash
# Run documentation tests
if ! command -v pytest &> /dev/null; then
  echo "pytest not found. Installing..."
  pip install pytest
fi

if [ -f "tests/test_docs.py" ]; then
  pytest tests/test_docs.py -v
else
  echo "Warning: tests/test_docs.py not found"
fi

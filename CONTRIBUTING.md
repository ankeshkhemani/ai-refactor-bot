# Contributing to AI Refactoring Bot

Thank you for your interest in contributing to AI Refactoring Bot! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### 1. Fork and Clone

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/ai-refactor-bot.git
   cd ai-refactor-bot
   ```

### 2. Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### 3. Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards:
   - Use Black for code formatting
   - Use isort for import sorting
   - Follow PEP 8 guidelines
   - Write tests for new features

3. Run tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black .
   isort .
   ```

### 4. Submitting Changes

1. Commit your changes:
   ```bash
   git commit -m "feat: add new feature"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request:
   - Use the PR template
   - Describe your changes
   - Link any related issues
   - Ensure CI passes

## Development Guidelines

### Code Style

- Use type hints
- Write docstrings for all functions
- Keep functions small and focused
- Write meaningful commit messages

### Testing

- Write unit tests for new features
- Maintain test coverage
- Include integration tests where appropriate

### Documentation

- Update README.md if needed
- Add docstrings to new functions
- Update API documentation
- Add examples for new features

## Review Process

1. All PRs require at least one review
2. CI must pass
3. Code must be properly formatted
4. Tests must pass
5. Documentation must be updated

## Questions?

Feel free to open an issue for any questions or concerns.

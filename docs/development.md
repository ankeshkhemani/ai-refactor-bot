# Development Guide

## Local Development Setup

### 1. Prerequisites

- Python 3.8 or higher
- Git
- GitHub account
- OpenAI API key
- GitHub App credentials

### 2. Environment Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/ai-refactor-bot.git
   cd ai-refactor-bot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Install production dependencies
   pip install -r requirements.txt

   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### 3. GitHub App Setup

1. **Create GitHub App**
   - Go to GitHub Settings > Developer Settings > GitHub Apps
   - Create new app with:
     - Webhook URL: `http://localhost:3000/webhook`
     - Webhook secret: Generate and save
     - Permissions: See deployment guide
   - Generate and download private key

2. **Install App**
   - Install on your test repository
   - Note the installation ID

## Development Workflow

### 1. Code Style

We use several tools to maintain code quality:

1. **Black** for code formatting
   ```bash
   black .
   ```

2. **isort** for import sorting
   ```bash
   isort .
   ```

3. **flake8** for linting
   ```bash
   flake8
   ```

4. **mypy** for type checking
   ```bash
   mypy .
   ```

### 2. Pre-commit Hooks

We use pre-commit to run checks before commits:

1. **Install Hooks**
   ```bash
   pre-commit install
   ```

2. **Run Manually**
   ```bash
   pre-commit run --all-files
   ```

### 3. Testing

1. **Run Tests**
   ```bash
   pytest
   ```

2. **Run with Coverage**
   ```bash
   pytest --cov=.
   ```

3. **Run Specific Tests**
   ```bash
   pytest tests/test_api.py
   ```

### 4. Local Development Server

1. **Start Server**
   ```bash
   uvicorn api.main:app --reload
   ```

2. **Access API Documentation**
   - OpenAPI: http://localhost:3000/docs
   - ReDoc: http://localhost:3000/redoc

## Project Structure

```
ai_refactor_bot/
├── api/            # FastAPI application
│   ├── main.py     # Main application
│   └── __init__.py
├── core/           # Core business logic
│   ├── code_scanner.py
│   ├── gpt_refactor.py
│   ├── github_pr.py
│   └── __init__.py
├── tests/          # Test suite
│   ├── test_api.py
│   └── __init__.py
├── utils/          # Utility functions
│   └── __init__.py
└── docs/           # Documentation
```

## Adding New Features

### 1. Code Scanner

1. **Add New Analyzer**
   ```python
   # core/code_scanner.py
   def analyze_new_pattern(code: str) -> List[Issue]:
       # Implementation
       pass
   ```

2. **Update Configuration**
   ```yaml
   # .refactorai.yml
   refactoring:
     new_pattern: true
   ```

### 2. AI Refactoring

1. **Add New Refactoring Type**
   ```python
   # core/gpt_refactor.py
   def refactor_new_pattern(code: str) -> str:
       # Implementation
       pass
   ```

2. **Update Prompts**
   ```python
   # Add new prompt template
   NEW_PATTERN_PROMPT = """
   Refactor the following code to improve {pattern}:
   {code}
   """
   ```

### 3. GitHub Integration

1. **Add New Event Handler**
   ```python
   # api/main.py
   @router.register("new_event")
   async def handle_new_event(event: sansio.Event):
       # Implementation
       pass
   ```

## Debugging

### 1. Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### 2. Debug Mode

```bash
uvicorn api.main:app --reload --log-level debug
```

### 3. Testing Webhooks

Use [ngrok](https://ngrok.com/) for local webhook testing:

```bash
ngrok http 3000
```

## Contributing

1. **Create Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**
   - Follow code style
   - Add tests
   - Update documentation

3. **Submit PR**
   - Create pull request
   - Link related issues
   - Request review

## Common Tasks

### 1. Update Dependencies

```bash
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-dev.txt
```

### 2. Generate Documentation

```bash
mkdocs build
mkdocs serve
```

### 3. Run All Checks

```bash
pre-commit run --all-files
pytest
mypy .
```

## Best Practices

1. **Code Style**
   - Use type hints
   - Write docstrings
   - Keep functions small
   - Use meaningful names

2. **Testing**
   - Write unit tests
   - Test edge cases
   - Mock external services
   - Maintain coverage

3. **Documentation**
   - Update README
   - Document new features
   - Add examples
   - Keep docs in sync

4. **Git Workflow**
   - Use meaningful commits
   - Keep PRs focused
   - Update CHANGELOG
   - Follow branching strategy

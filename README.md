# AI Refactoring Bot

An intelligent GitHub bot that automatically scans Python repositories for technical debt and generates refactoring suggestions using AI.

## Features

- 🔍 Automated code scanning using Radon and Flake8
- 🤖 AI-powered code refactoring suggestions using GPT-4
- 🔄 Automatic PR creation for suggested improvements
- 📊 Code quality metrics and analysis
- 🔐 Secure GitHub App integration

## Prerequisites

- Python 3.8+
- GitHub App credentials
- OpenAI API key
- Railway account (for deployment)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-refactor-bot.git
cd ai-refactor-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```env
# GitHub App Configuration
GITHUB_APP_ID=your_app_id
GITHUB_WEBHOOK_SECRET=your_webhook_secret
PRIVATE_KEY=your_private_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Repository Configuration
REPO_OWNER=your_username
REPO_NAME=your_repo_name
```

## Development

1. Run the development server:
```bash
PYTHONPATH=src uvicorn src.api.main:app --reload
```

2. Run tests:
```bash
PYTHONPATH=src pytest
```

3. Format code:
```bash
black src tests
isort src tests
```

## Deployment

1. Create a new Railway project
2. Connect your GitHub repository
3. Add the required environment variables
4. Deploy!

## Project Structure

```
ai_refactor_bot/
├── src/            # Source code
│   ├── api/        # FastAPI application and routes
│   └── core/       # Core business logic
├── tests/          # Test suite
├── docs/           # Documentation
├── .github/        # GitHub Actions workflows
├── requirements.txt
└── requirements-dev.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

# 🛠️ AI Refactoring Bot (MVP)

AI Refactoring Bot is a GitHub-integrated tool that automatically scans your Python repositories for technical debt and generates refactoring suggestions using advanced LLMs. It operates entirely within GitHub, creating pull requests with clear, actionable improvements to keep your code clean and maintainable.

---

## 🚀 Key Features

- **Automated Repo Scanning:** Identifies complexity, duplication, unused imports, and outdated patterns.
- **AI-Powered Refactoring:** Provides clear, actionable code suggestions powered by LLMs.
- **Seamless GitHub Integration:** No extra UI. All interactions via GitHub Pull Requests, comments, and checks.
- **Configurable via Repo:** Easily customizable through a simple config file.

---

## ✅ Quickstart

### 1. Installation

- Install the GitHub App to your repository from the GitHub Marketplace.
- Configure necessary permissions (repository read/write, PR management, checks).

### 2. Basic Usage

- After installation, the bot automatically scans and analyzes your codebase.
- Pull Requests with suggested refactors are automatically opened for review.
- Simply review and merge PRs as you normally would.

---

## 🛠️ How it Works

1. **Code Analysis:** Fetches and scans Python files for common code issues.
2. **AI-Driven Refactoring:** Generates suggested improvements using LLM prompts.
3. **Pull Request Creation:** Pushes suggested changes and clearly documents each PR.
4. **Continuous Improvement:** Integrates seamlessly into your workflow for continuous codebase health.

---

## 🔍 Scanning Logic (MVP)

The bot scans the target Python repository by:

1. Fetching all `.py` files via the GitHub API (recursive `contents` endpoint)
2. Excluding:
   - Non-Python files
3. For each Python file:
   - Complexity and duplication analysis planned using `radon` and LLM heuristics
   - Refactor suggestions triggered if patterns match:

| Pattern                        | Reason |
|-------------------------------|--------|
| Long functions (>20 lines)    | Complexity / readability |
| Manual loop for filtering     | Could be list comprehension |
| Unused imports / variables    | Clean-up opportunity |
| Old-style string formatting   | Convert to f-strings |
| Nested ifs with else          | Flatten for readability |
  - The safest and simplest changes are sent via PRs first and if those PRs, get merged, then new PRs are generated with incrementally more powerful refactors.
  - The scanning and suggestions are triggered first whenever the app is installed and then after every suggested PR is merged.

---

## 📋 Configuration

Customize the tool behavior through a simple configuration file (`.refactorai.yml`) placed in your repository:

```yaml
exclude_paths:
  - tests/
  - migrations/
scan_frequency: weekly
refactoring:
  style_improvements: true
  complexity_reduction: true

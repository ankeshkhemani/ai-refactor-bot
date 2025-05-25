# AI Refactor Bot

An intelligent GitHub App that automatically scans Python repositories for technical debt and generates refactoring suggestions using AI.

## Architecture

The bot uses a queue-based microservices architecture with three main components:

### 1. Analysis Service
- Scans repositories for code quality issues using:
  - Radon for cyclomatic complexity analysis
  - Flake8 for code style and potential bugs
- Groups issues by file for efficient processing
- Uses AI to generate fixes for identified issues
- Enqueues fixes for PR creation

### 2. PR Service
- Processes fixes from the queue
- Creates pull requests with AI-generated improvements
- Handles retries and error recovery
- Manages GitHub API interactions

### 3. Queue Service
- Uses Redis for message queuing
- Manages two queues:
  - `analysis`: For repository analysis tasks
  - `pr_creation`: For PR creation tasks
- Provides reliable message delivery and retry mechanisms

## Flow

1. **Installation**
   - GitHub App is installed on a repository
   - Webhook receives installation event
   - Repositories are enqueued for analysis

2. **Analysis**
   - Analysis service processes repository
   - Scans for code quality issues
   - Groups issues by file
   - Generates fixes using AI
   - Enqueues fixes for PR creation

3. **PR Creation**
   - PR service processes fixes
   - Creates pull requests with improvements
   - Handles retries if needed

## Setup

### Prerequisites
- Python 3.8+
- Redis server
- PostgreSQL database
- GitHub App credentials

### Environment Variables
```env
# GitHub App Configuration
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY=your_private_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/ai_refactor_bot

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-refactor-bot.git
cd ai-refactor-bot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
alembic upgrade head
```

5. Start the application:
```bash
uvicorn src.api.main:app --reload
```

## Usage

### GitHub App Installation

1. Install the GitHub App on your repository
2. The bot will automatically:
   - Scan your repository for issues
   - Create pull requests with improvements
   - Handle retries and error recovery

### Manual Analysis

You can trigger analysis manually using the API:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "your_username",
    "repo_name": "your_repo",
    "installation_id": "your_installation_id"
  }'
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

Run all checks:
```bash
black .
flake8
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and checks
5. Submit a pull request

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

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

import asyncio
import difflib
import logging
import os
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .code_scanner import (
    run_flake8_analysis,
    run_radon_analysis,
)
from .code_utils import normalize_code
from .github_pr import GitHubPRConfig, create_pr_for_file_change

# from gpt_refactor import get_gpt_refactor

# Load environment variables
load_dotenv()

# Configure OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Simulated scan result (from flake8/radon)
issues = [
    {
        "file_path": "src/drive.py",
        "original_code": (
            "import os\nimport time\n\ndef greet():\n    print('Hello world')\n"
        ),
        "issue_type": "unused imports",
    }
]


def greet():
    """Prints a greeting message."""
    print("Hello, world!")


# async def main():
#     """Main entry point for processing issues and creating PRs."""
#     pr_config = GitHubPRConfig()  # Use environment or pass explicit values if needed
#     for issue in issues:
#         prompt = (
#             "You are a Python expert. Remove only unused imports from this file "
#             "without changing logic.\n\n"
#             f"```python\n{issue['original_code']}\n```\n\n"
#             "Return only the full cleaned Python file."
#         )
#         refactored_code = get_gpt_refactor(prompt)
#
#         # Skip if no change
#         if refactored_code.strip() == issue["original_code"].strip():
#             print(f"⚠️ No changes for {issue['file_path']}. Skipping PR.")
#             continue
#
#         pr_url = await create_pr_for_file_change(
#             pr_config,
#             file_path=issue["file_path"],
#             new_content=refactored_code,
#             commit_message=(
#                 f"refactor: remove unused imports from {issue['file_path']}"
#             ),
#             pr_title=f"refactor({issue['file_path']}): remove unused imports",
#             pr_body=(
#                 "This PR was auto-generated to clean up unused imports. "
#                 "No logic was changed."
#             ),
#         )
#         print(f"✅ PR created: {pr_url}")


def analyze_code_quality(
    code: str,
    file_path: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Analyze code quality using multiple tools.

    Args:
        code: The Python code to analyze
        file_path: Path to the file being analyzed
        config: Configuration dictionary with thresholds

    Returns:
        Dict containing analysis results and suggestions
    """
    results = {
        "file": file_path,
        "complexity": {},
        "maintainability": {},
        "style": [],
        "suggestions": [],
    }

    # Run Radon analysis
    try:
        radon_results = run_radon_analysis(code)
        results["complexity"] = radon_results["complexity"]
        results["maintainability"] = radon_results["maintainability"]
    except Exception as e:
        logging.error(f"Radon analysis failed: {str(e)}")

    # Run Flake8 analysis
    try:
        flake8_results = run_flake8_analysis(code)
        results["style"] = flake8_results
    except Exception as e:
        logging.error(f"Flake8 analysis failed: {str(e)}")

    # Generate suggestions based on analysis
    suggestions = generate_suggestions(results, config)
    results["suggestions"] = suggestions

    return results


def generate_suggestions(
    analysis_results: Dict[str, Any],
    config: Dict[str, Any],
) -> List[str]:
    """Generate refactoring suggestions based on analysis results.

    Args:
        analysis_results: Results from code quality analysis
        config: Configuration dictionary with thresholds

    Returns:
        List of suggestion strings
    """
    suggestions = []

    # Check complexity thresholds
    complexity_threshold = config.get("complexity_threshold", 10)
    for func, metrics_list in analysis_results["complexity"].items():
        for metrics in metrics_list:
            if isinstance(metrics, dict) and "complexity" in metrics:
                if metrics["complexity"] > complexity_threshold:
                    suggestions.append(
                        f"Function '{func}' has high complexity "
                        f"({metrics['complexity']}). Consider breaking it down."
                    )

    # Check maintainability index
    mi_threshold = config.get("maintainability_threshold", 50)
    for func, metrics_list in analysis_results["maintainability"].items():
        for metrics in metrics_list:
            if isinstance(metrics, dict) and "mi" in metrics:
                if metrics["mi"] < mi_threshold:
                    suggestions.append(
                        f"Function '{func}' has low maintainability "
                        f"({metrics['mi']}). Consider refactoring."
                    )

    # Add style suggestions
    for issue in analysis_results["style"]:
        suggestions.append(f"Style issue: {issue}")

    return suggestions


# if __name__ == "__main__":
#     asyncio.run(main())

MAX_DIFF_LINES = 50  # configurable
MAX_DIFF_PERCENT = 0.3  # 30%


def is_diff_too_large(original: str, fixed: str) -> bool:
    """Check if the diff between original and fixed code is too large."""
    # Normalize both versions before diffing
    original = normalize_code(original)
    fixed = normalize_code(fixed)

    original_lines = original.splitlines()
    fixed_lines = fixed.splitlines()
    diff = list(difflib.unified_diff(original_lines, fixed_lines))
    # Count changed lines (lines starting with + or - but not diff headers)
    changed_lines = [
        line
        for line in diff
        if line
        and (line[0] == "+" or line[0] == "-")
        and not line.startswith("+++")
        and not line.startswith("---")
    ]
    num_changed = len(changed_lines)
    total_lines = max(len(original_lines), 1)  # avoid division by zero
    percent_changed = num_changed / total_lines
    return num_changed > MAX_DIFF_LINES or percent_changed > MAX_DIFF_PERCENT


async def fix_single_issue(
    issue: Dict[str, Any], original_code: str, config: Dict[str, Any]
) -> Tuple[str, str]:
    """Fix a single code issue using GPT and prepare for PR creation.

    Args:
        issue: A single issue from code_scanner output, e.g.:
            {
                "file": "drive.py",
                "line": 9,
                "type": "Flake8 Issues",
                "code": "F401",
                "description": "'time' imported but unused"
            }
        original_code: The original content of the file
        config: Configuration dictionary with GPT settings

    Returns:
        Tuple of (fixed_code, commit_message)
    """
    # Create a focused prompt based on the issue type
    if issue["type"] == "Flake8 Issues":
        prompt = create_flake8_prompt(issue, original_code)
    elif issue["type"] == "Cyclomatic Complexity":
        prompt = create_complexity_prompt(issue, original_code)
    elif issue["type"] == "Maintainability Index":
        prompt = create_maintainability_prompt(issue, original_code)
    else:
        raise ValueError(f"Unsupported issue type: {issue['type']}")

    try:
        # Call GPT to get the fix
        response = await client.chat.completions.create(
            model=config.get("gpt_model", "gpt-4"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python expert code fixer. "
                        "Return only the fixed code without any explanations "
                        "or markdown formatting."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
        )

        # Extract the fixed code from the response
        fixed_code = response.choices[0].message.content.strip()

        # Remove any markdown code block formatting if present
        if fixed_code.startswith("```python"):
            fixed_code = fixed_code[9:]
        if fixed_code.endswith("```"):
            fixed_code = fixed_code[:-3]
        fixed_code = fixed_code.strip()

    except Exception as e:
        logging.error(f"Error getting GPT fix: {str(e)}")
        return original_code, create_commit_message(issue)

    # Create a descriptive commit message
    commit_message = create_commit_message(issue)

    return fixed_code, commit_message


def create_flake8_prompt(issue: Dict[str, Any], original_code: str) -> str:
    """Create a GPT prompt for fixing a Flake8 issue."""
    prompt = f"""You are a Python expert. Fix the following Flake8 issue in this file:

Issue: {issue['description']}
Line: {issue['line']}
Code: {issue['code']}

Original code:
```python
{original_code}
```

Return only the fixed code without any explanations or markdown formatting."""
    return prompt


def create_complexity_prompt(issue: Dict[str, Any], original_code: str) -> str:
    """Create a GPT prompt for fixing a complexity issue."""
    prompt = f"""You are a Python expert. Reduce the cyclomatic complexity of this function:\n\n"
        f"{original_code}\n\nReturn only the fixed code, no explanations or formatting.\n\n"
        f"Current cyclomatic complexity: {issue['complexity']}.\nTarget: {issue['target_complexity']}."""
    return prompt


def create_maintainability_prompt(issue: Dict[str, Any], original_code: str) -> str:
    """Create a GPT prompt for fixing a maintainability issue."""
    prompt = f"""You are a Python expert. Improve the maintainability of this function:

Function: {issue['function']}
Current maintainability index: {issue['mi']}
Target maintainability index: {issue['target_mi']}

Original code:
```python
{original_code}
```

Return only the refactored code without any explanations or markdown formatting."""
    return prompt


def create_commit_message(issue: Dict[str, Any]) -> str:
    """Create a descriptive commit message for the fix."""
    if issue["type"] == "Flake8 Issues":
        return f"fix: {issue['description']} in {issue['file']}"
    elif issue["type"] == "Cyclomatic Complexity":
        return (
            f"refactor: reduce complexity of {issue['function']} "
            f"from {issue['complexity']} to {issue['target_complexity']}"
        )
    elif issue["type"] == "Maintainability Index":
        return (
            f"refactor: improve maintainability of {issue['function']} "
            f"from {issue['mi']} to {issue['target_mi']}"
        )
    else:
        return f"fix: {issue['type']} in {issue['file']}"


async def create_fix_pr(
    issue: Dict[str, Any], original_code: str, config: Dict[str, Any]
) -> str:
    """Create a PR for a code fix.

    Args:
        issue: A single issue from code_scanner output
        original_code: The original content of the file
        config: Configuration dictionary with GPT settings

    Returns:
        URL of the created PR
    """
    # Get the fixed code
    fixed_code, commit_message = await fix_single_issue(issue, original_code, config)

    # Check if the diff is too large
    if is_diff_too_large(original_code, fixed_code):
        logging.warning(f"Diff too large for {issue['file']}. " "Skipping PR creation.")
        return ""

    # Create the PR
    try:
        pr_body = (
            f"This PR fixes the following issue:\n\n"
            f"- Type: {issue['type']}\n"  # noqa: E501
            f"- Description: {issue['description']}\n"  # noqa: E501
            f"- File: {issue['file']}\n"  # noqa: E501
            f"- Line: {issue['line']}\n"  # noqa: E501
        )
        pr_url = await create_pr_for_file_change(
            repo=config["repo"],
            file_path=issue["file"],
            new_content=fixed_code,
            commit_message=commit_message,
            pr_title=commit_message,
            pr_body=pr_body,
            config=config["github_config"],
        )
        return pr_url
    except Exception as e:
        logging.error(f"Error creating PR: {str(e)}")
        return ""


def get_complexity_rank(complexity: int) -> str:
    """Get a human-readable rank for a complexity score."""
    if complexity <= 5:
        return "A"
    elif complexity <= 10:
        return "B"
    elif complexity <= 15:
        return "C"
    elif complexity <= 20:
        return "D"
    else:
        return "F"


# Test function
async def test_issue_fix():
    """Test the issue fixing functionality."""
    config = {
        "gpt_model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "repo": "test-repo",
        "github_config": GitHubPRConfig(),
    }

    issue = {
        "file": "test.py",
        "line": 1,
        "type": "Flake8 Issues",
        "code": "F401",
        "description": "'os' imported but unused",
    }

    original_code = "import os\n\ndef test():\n    print('test')\n"

    pr_url = await create_fix_pr(issue, original_code, config)
    print(f"PR URL: {pr_url}")


if __name__ == "__main__":
    asyncio.run(test_issue_fix())

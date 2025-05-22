import asyncio
import logging
from typing import Any, Dict, List

from code_scanner import run_flake8_analysis, run_radon_analysis
from github_pr import create_pr_for_file_change
from gpt_refactor import get_gpt_refactor

# Simulated scan result (from flake8/radon)
issues = [
    {
        "file_path": "src/drive.py",
        "original_code": "import os\nimport time\n\ndef greet():\n    print('Hello world')\n",
        "issue_type": "unused imports",
    }
]


def greet():
    """Prints a greeting message."""
    print("Hello, world!")


async def main():
    """Main entry point for processing issues and creating PRs."""
    for issue in issues:
        prompt = f"""
You are a Python expert. Remove only unused imports from this file without changing logic.

```python
{issue['original_code']}
```

Return only the full cleaned Python file.
"""
        refactored_code = get_gpt_refactor(prompt)

        # Skip if no change
        if refactored_code.strip() == issue["original_code"].strip():
            print(f"⚠️ No changes for {issue['file_path']}. Skipping PR.")
            continue

        pr_url = await create_pr_for_file_change(
            file_path=issue["file_path"],
            new_content=refactored_code,
            commit_message=f"refactor: remove unused imports from {issue['file_path']}",
            pr_title=f"refactor({issue['file_path']}): remove unused imports",
            pr_body="This PR was auto-generated to clean up unused imports. No logic was changed.",
        )
        print(f"✅ PR created: {pr_url}")


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
    for func, metrics in analysis_results["complexity"].items():
        if metrics["complexity"] > complexity_threshold:
            suggestions.append(
                f"Function '{func}' has high complexity "
                f"({metrics['complexity']}). Consider breaking it down."
            )

    # Check maintainability index
    mi_threshold = config.get("maintainability_threshold", 50)
    for func, metrics in analysis_results["maintainability"].items():
        if metrics["mi"] < mi_threshold:
            suggestions.append(
                f"Function '{func}' has low maintainability "
                f"({metrics['mi']}). Consider refactoring."
            )

    # Add style suggestions
    for issue in analysis_results["style"]:
        suggestions.append(f"Style issue: {issue}")

    return suggestions


if __name__ == "__main__":
    asyncio.run(main())

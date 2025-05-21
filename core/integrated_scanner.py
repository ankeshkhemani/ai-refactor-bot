import asyncio

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


async def main():
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


if __name__ == "__main__":
    asyncio.run(main())

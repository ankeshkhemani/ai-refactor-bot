# ai_refactor_bot/code_scanner.py

import ast
import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import redis
import requests
from dotenv import load_dotenv

from .code_utils import normalize_code
from .github_config import GitHubConfig

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def get_tree_sha(config: GitHubConfig, branch: str) -> str:
    """Get the tree SHA for a branch."""
    url = f"{config.api_url}/branches/{branch}"
    logging.info(f"Fetching commit SHA for branch '{branch}'")

    # Get installation token
    token = await config.get_installation_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                logging.error(
                    f"Branch '{branch}' not found. "
                    "Check if the branch exists in the repository."
                )
                raise RuntimeError(f"Branch '{branch}' not found.")

            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Failed to get tree SHA: {error_text}")

            data = await resp.json()
            return data["commit"]["commit"]["tree"]["sha"]


async def fetch_python_files(config: GitHubConfig) -> List[str]:
    """Fetch all Python files from the repository."""
    tree_sha = await get_tree_sha(config, config.head_ref)
    tree_url = f"{config.api_url}/git/trees/{tree_sha}?recursive=1"
    logging.info(f"Fetching file tree from: {tree_url}")

    # Get installation token
    token = await config.get_installation_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(tree_url, headers=headers) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Failed to fetch file tree: {error_text}")

                    data = await resp.json()
                    files = data.get("tree", [])
                    py_files = [
                        f["path"]
                        for f in files
                        if f["path"].endswith(".py") and f["type"] == "blob"
                    ]
                    logging.info(f"Found {len(py_files)} Python files")
                    return py_files
        except Exception as e:
            logging.warning(f"Attempt {attempt+1}: Failed to fetch file tree - {e}")
            if attempt < 2:  # Don't sleep on the last attempt
                time.sleep(2)
    raise RuntimeError("Failed to fetch Python files from GitHub after 3 attempts")


def download_and_decode_file(config: GitHubConfig, path: str) -> str:
    file_url = f"{config.api_url}/contents/{path}"
    logging.info(f"Downloading file: {path}")
    for attempt in range(3):
        try:
            resp = requests.get(file_url, headers=config.headers)
            resp.raise_for_status()
            content = resp.json().get("content", "")
            logging.info(f"Decoded content from: {path}")
            return base64.b64decode(content).decode("utf-8")
        except requests.RequestException as e:
            logging.warning(
                f"Attempt {attempt+1}: Failed to download file {path} - {e}"
            )
            time.sleep(2)
    raise RuntimeError(f"Failed to download file {path} after 3 attempts")


def run_radon_analysis(code: str) -> Dict:
    if not shutil.which("radon"):
        raise EnvironmentError(
            "'radon' CLI tool is not installed. "
            "Please install it with: pip install radon"
        )

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp.flush()
        tmp_path = tmp.name
    logging.info(f"Running radon analysis on temp file: {tmp_path}")

    results = {}
    try:
        cc_output = subprocess.check_output(["radon", "cc", tmp_path, "-j"])
        mi_output = subprocess.check_output(["radon", "mi", tmp_path, "-j"])
        results["complexity"] = eval(cc_output.decode())
        results["maintainability"] = eval(mi_output.decode())
        logging.info("Radon analysis complete")
    finally:
        os.remove(tmp_path)
        logging.debug(f"Deleted temp file: {tmp_path}")
    return results


def run_flake8_analysis(code: str) -> List[str]:
    if not shutil.which("flake8"):
        raise EnvironmentError(
            "'flake8' CLI tool is not installed. "
            "Please install it with: pip install flake8"
        )

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp.flush()
        tmp_path = tmp.name
    logging.info(f"Running flake8 analysis on temp file: {tmp_path}")

    try:
        output = subprocess.check_output(
            ["flake8", tmp_path], stderr=subprocess.DEVNULL
        )
        logging.info("flake8 analysis complete")
        return output.decode().splitlines()
    except subprocess.CalledProcessError as e:
        logging.info("flake8 found issues")
        return e.output.decode().splitlines()
    finally:
        os.remove(tmp_path)
        logging.debug(f"Deleted temp file: {tmp_path}")


async def scan_repository(config: GitHubConfig) -> Dict[str, Dict]:
    """Scan a repository for code quality issues."""
    logging.info("Starting repository scan...")

    file_paths = await fetch_python_files(config)
    analysis = {}
    for path in file_paths:
        logging.info(f"Analyzing file: {path}")
        code = await config.get_file_content(path)
        if code:
            analysis[path] = {
                "radon": run_radon_analysis(code),
                "flake8": run_flake8_analysis(code),
            }
    logging.info("Repository scan complete")
    return analysis


def extract_function_from_code(
    code: str, function_name: str, line_number: int
) -> Optional[Tuple[str, int, int]]:
    """Extract a specific function from Python code.

    Args:
        code: The Python code as a string
        function_name: Name of the function to extract
        line_number: Line number where the function starts

    Returns:
        Tuple of (function_code, start_line, end_line) or None if not found
    """
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Get the line numbers
                start_line = node.lineno
                end_line = node.end_lineno

                # Extract the function code while preserving line endings
                lines = code.splitlines(keepends=True)
                function_lines = lines[start_line - 1 : end_line]
                function_code = "".join(function_lines)

                # Normalize the code for consistent handling
                function_code = normalize_code(function_code)

                return function_code, start_line, end_line
    except Exception as e:
        logging.error(f"Error extracting function: {str(e)}")

    return None


def get_function_code(
    config: GitHubConfig, file_path: str, function_name: str, line_number: int
) -> Optional[str]:
    """Get a specific function's code from a file in the repository.

    Args:
        config: GitHubConfig instance
        file_path: Path to the file in the repository
        function_name: Name of the function to extract
        line_number: Line number where the function starts

    Returns:
        The function's code as a string, or None if not found
    """
    try:
        # Download the file content
        file_content = download_and_decode_file(config, file_path)

        # Extract the function
        result = extract_function_from_code(file_content, function_name, line_number)
        if result:
            function_code, start_line, end_line = result
            logging.info(
                f"Found function {function_name} in {file_path} "
                f"(lines {start_line}-{end_line})"
            )
            return function_code
        else:
            logging.error(f"Function {function_name} not found in {file_path}")
            return None

    except Exception as e:
        logging.error(f"Error getting function code: {str(e)}")
        return None


def save_to_db(issues: List[Dict]) -> None:
    """Save the analysis results to Redis.
    Args:
        issues: List of issue dictionaries to save.
    """
    # Connect to Redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    # Save each issue as a JSON string in Redis
    for i, issue in enumerate(issues):
        r.set(f"issue:{i}", json.dumps(issue))
    logging.info("Analysis results saved to Redis.")


if __name__ == "__main__":
    logging.info("Starting full scan run")
    config = GitHubConfig()
    results = asyncio.run(scan_repository(config))

    # Create a list to store all issues
    all_issues = []

    for file, metrics in results.items():
        # Process Cyclomatic Complexity
        for tmp_path, entries in metrics["radon"]["complexity"].items():
            for fn in entries:
                all_issues.append(
                    {
                        "file": file,
                        "line": fn["lineno"],
                        "type": "Cyclomatic Complexity",
                        "complexity": fn["complexity"],
                        "rank": fn["rank"],
                        "function": fn["name"],
                    }
                )

        # Process Maintainability Index
        for tmp_path, entry in metrics["radon"]["maintainability"].items():
            all_issues.append(
                {
                    "file": file,
                    "type": "Maintainability Index",
                    "score": round(entry["mi"], 2),
                    "rank": entry["rank"],
                }
            )

        # Process Flake8 Issues
        for issue in metrics["flake8"]:
            # Parse the Flake8 output
            parts = issue.split(":")
            if len(parts) >= 4:
                line = int(parts[1])
                # Extract code and description
                code_desc = parts[3].strip()
                code = code_desc.split()[0]  # Get the code (e.g., F401)
                description = " ".join(
                    code_desc.split()[1:]
                )  # Get the rest as description
                all_issues.append(
                    {
                        "file": file,
                        "line": line,
                        "type": "Flake8 Issues",
                        "code": code,
                        "description": description,
                    }
                )

    # Save to Redis
    save_to_db(all_issues)

    # Print summary for console output
    for file, metrics in results.items():
        print("\n📄", file)

        radon_data = metrics["radon"]
        print("\n  🔢 Cyclomatic Complexity:")
        for tmp_path, entries in radon_data["complexity"].items():
            for fn in entries:
                print(
                    f"    - {fn['name']} (line {fn['lineno']}): "
                    f"complexity {fn['complexity']}, rank {fn['rank']}"
                )

        print("\n  📊 Maintainability Index:")
        for tmp_path, entry in radon_data["maintainability"].items():
            print(f"    - Score: {entry['mi']:.2f}, Rank: {entry['rank']}")

        print("\n  ❌ Flake8 Issues:")
        for issue in metrics["flake8"]:
            print(f"    - {issue}")
    logging.info("Scan finished")

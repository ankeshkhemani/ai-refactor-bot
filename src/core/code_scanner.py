# ai_refactor_bot/code_scanner.py

import base64
import logging
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from typing import Dict, List

import jwt
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class GitHubConfig:
    def __init__(self):
        self.repo_owner = os.getenv("REPO_OWNER")
        self.repo_name = os.getenv("REPO_NAME")
        self.head_ref = os.getenv("REPO_BRANCH", "main")
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
        self.installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        self.api_url = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        )
        self.headers = None

    def setup_headers(self):
        jwt_token = generate_jwt(self.app_id, self.private_key_path)
        installation_token = get_installation_token(jwt_token, self.installation_id)
        self.headers = {
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github+json",
        }


def generate_jwt(app_id: str, private_key_path: str) -> str:
    with open(private_key_path, "r") as f:
        private_key = f.read()
    now = datetime.utcnow()
    payload = {"iat": now, "exp": now + timedelta(minutes=10), "iss": app_id}
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    return encoded_jwt


def get_installation_token(jwt_token: str, installation_id: str) -> str:
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["token"]


def get_tree_sha(config: GitHubConfig, branch: str) -> str:
    url = f"{config.api_url}/branches/{branch}"
    logging.info(f"Fetching commit SHA for branch '{branch}'")
    resp = requests.get(url, headers=config.headers)

    if resp.status_code == 404:
        logging.error(
            f"Branch '{branch}' not found. "
            "Check if the branch exists in the repository."
        )
        raise RuntimeError(f"Branch '{branch}' not found.")

    resp.raise_for_status()
    return resp.json()["commit"]["commit"]["tree"]["sha"]


def fetch_python_files(config: GitHubConfig) -> List[str]:
    tree_sha = get_tree_sha(config, config.head_ref)
    tree_url = f"{config.api_url}/git/trees/{tree_sha}?recursive=1"
    logging.info(f"Fetching file tree from: {tree_url}")
    for attempt in range(3):
        try:
            resp = requests.get(tree_url, headers=config.headers)
            resp.raise_for_status()
            files = resp.json().get("tree", [])
            py_files = [
                f["path"]
                for f in files
                if f["path"].endswith(".py") and f["type"] == "blob"
            ]
            logging.info(f"Found {len(py_files)} Python files")
            return py_files
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt+1}: Failed to fetch file tree - {e}")
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


def scan_repository() -> Dict[str, Dict]:
    logging.info("Starting repository scan...")
    config = GitHubConfig()
    config.setup_headers()

    file_paths = fetch_python_files(config)
    analysis = {}
    for path in file_paths:
        logging.info(f"Analyzing file: {path}")
        code = download_and_decode_file(config, path)
        analysis[path] = {
            "radon": run_radon_analysis(code),
            "flake8": run_flake8_analysis(code),
        }
    logging.info("Repository scan complete")
    return analysis


if __name__ == "__main__":
    logging.info("Starting full scan run")
    results = scan_repository()
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

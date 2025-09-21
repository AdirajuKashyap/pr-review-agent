"""
PR Review Agent Flask App.

Provides endpoints to:
- fetch and analyze a GitHub pull request by URL
- parse a local diff file in PR-like format
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request
from github import Github, GithubException

# ---------------------------------------
# Setup Flask and logging
# ---------------------------------------
app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Environment token
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Precompile PR URL regex
PR_URL_PATTERN = re.compile(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)")

# ---------------------------------------
# GitHub PR Fetcher
# ---------------------------------------
def fetch_github_pr(pr_url: str) -> Dict[str, Any]:
    """Fetch a GitHub PR by URL and return PR info."""
    m = PR_URL_PATTERN.match(pr_url)
    if not m:
        raise ValueError(
            "Invalid GitHub PR URL. Expected: https://github.com/owner/repo/pull/123"
        )

    repo_name, pr_number = m.group(1), int(m.group(2))
    logger.info("Fetching PR %s #%s", repo_name, pr_number)

    gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files: List[Dict[str, Any]] = []
    total_additions = 0
    total_deletions = 0

    for f in pr.get_files():
        patch_text = f.patch or ""
        files.append(
            {
                "filename": f.filename,
                "patch": patch_text,
                "additions": f.additions,
                "deletions": f.deletions,
            }
        )
        total_additions += f.additions
        total_deletions += f.deletions

    score = max(0, 100 - (total_additions + total_deletions))

    return {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "title": pr.title,
        "body": pr.body,
        "files": files,
        "score": score,
    }


# ---------------------------------------
# Local Diff Parser
# ---------------------------------------
def parse_local_diff(diff_text: str) -> Dict[str, Any]:
    """Parse a unified diff text into PR-like data format."""
    files: List[Dict[str, Any]] = []
    current_patch_lines: List[str] = []
    filename = None
    collecting = False

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            # flush previous file
            if collecting and filename:
                files.append(
                    {
                        "filename": filename,
                        "patch": "\n".join(current_patch_lines),
                        "additions": sum(
                            1
                            for l in current_patch_lines
                            if l.startswith("+") and not l.startswith("+++")
                        ),
                        "deletions": sum(
                            1
                            for l in current_patch_lines
                            if l.startswith("-") and not l.startswith("---")
                        ),
                    }
                )
            filename = line[len("+++ b/") :].strip()
            current_patch_lines = []
            collecting = True
        elif collecting:
            current_patch_lines.append(line)

    # flush last file
    if collecting and filename:
        files.append(
            {
                "filename": filename,
                "patch": "\n".join(current_patch_lines),
                "additions": sum(
                    1
                    for l in current_patch_lines
                    if l.startswith("+") and not l.startswith("+++")
                ),
                "deletions": sum(
                    1
                    for l in current_patch_lines
                    if l.startswith("-") and not l.startswith("---")
                ),
            }
        )

    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)
    score = max(0, 100 - (total_additions + total_deletions))

    return {
        "repo_name": "local",
        "pr_number": 0,
        "title": "local-diff",
        "body": "",
        "files": files,
        "score": score,
    }


# ---------------------------------------
# Flask Routes
# ---------------------------------------
@app.route("/")
def index():
    return render_template("index.html")  # make sure this exists in templates/


@app.route("/review", methods=["POST"])
def review():
    """Endpoint to review either a GitHub PR or an uploaded diff file."""
    try:
        pr_url = request.form.get("pr_url", "").strip()
        diff_file = request.files.get("diff_file")

        if pr_url:
            pr_data = fetch_github_pr(pr_url)
        elif diff_file:
            diff_text = diff_file.read().decode("utf-8")
            pr_data = parse_local_diff(diff_text)
        else:
            return jsonify({"error": "No PR URL or diff file provided"}), 400

        return jsonify(pr_data)

    except ValueError as ve:
        logger.warning("Validation error: %s", ve)
        return jsonify({"error": str(ve)}), 400
    except GithubException.UnknownObjectException:
        logger.warning("PR not found or repository is private")
        return jsonify({"error": "PR not found or repository is private"}), 404
    except Exception as e:
        logger.exception("Internal server error")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ---------------------------------------
# Run App
# ---------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

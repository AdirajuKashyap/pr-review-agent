from flask import Flask, request, render_template, jsonify
from github import Github
import os
import re

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

# -----------------------------
# GitHub PR Fetcher
# -----------------------------
def fetch_github_pr(pr_url: str):
    """Fetch a GitHub PR by URL and return PR info."""
    pattern = r'https://github\.com/([^/]+/[^/]+)/pull/(\d+)'
    m = re.match(pattern, pr_url)
    if not m:
        raise ValueError("Invalid GitHub PR URL. Use https://github.com/owner/repo/pull/123")
    
    repo_name, pr_number = m.group(1), int(m.group(2))
    gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files = []
    total_additions = 0
    total_deletions = 0

    for f in pr.get_files():
        patch_text = f.patch or ""
        files.append({
            "filename": f.filename,
            "patch": patch_text,
            "additions": f.additions,
            "deletions": f.deletions
        })
        total_additions += f.additions
        total_deletions += f.deletions

    score = max(0, 100 - (total_additions + total_deletions))

    return {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "title": pr.title,
        "body": pr.body,
        "files": files,
        "score": score
    }

# -----------------------------
# Local Diff Parser
# -----------------------------
def parse_local_diff(diff_text: str):
    """Parse a unified diff text into PR-like data format."""
    files = []
    current_file = None
    current_patch_lines = []
    filename = None

    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            if current_file:
                files.append({
                    "filename": filename,
                    "patch": "\n".join(current_patch_lines),
                    "additions": sum(1 for l in current_patch_lines if l.startswith('+') and not l.startswith('+++')),
                    "deletions": sum(1 for l in current_patch_lines if l.startswith('-') and not l.startswith('---'))
                })
            filename = line[len('+++ b/'):].strip()
            current_patch_lines = []
            current_file = True
        elif current_file:
            current_patch_lines.append(line)

    if current_file:
        files.append({
            "filename": filename,
            "patch": "\n".join(current_patch_lines),
            "additions": sum(1 for l in current_patch_lines if l.startswith('+') and not l.startswith('+++')),
            "deletions": sum(1 for l in current_patch_lines if l.startswith('-') and not l.startswith('---'))
        })

    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)
    score = max(0, 100 - (total_additions + total_deletions))

    return {
        "repo_name": "local",
        "pr_number": 0,
        "title": "local-diff",
        "body": "",
        "files": files,
        "score": score
    }

# -----------------------------
# Flask Routes
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')  # create a simple form in index.html

@app.route('/review', methods=['POST'])
def review():
    try:
        # Handle GitHub PR URL
        pr_url = request.form.get('pr_url', '').strip()
        diff_file = request.files.get('diff_file')

        if pr_url:
            pr_data = fetch_github_pr(pr_url)
        elif diff_file:
            diff_text = diff_file.read().decode('utf-8')
            pr_data = parse_local_diff(diff_text)
        else:
            return jsonify({"error": "No PR URL or diff file provided"}), 400

        return jsonify(pr_data)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

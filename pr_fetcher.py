from github import Github
import os
import re

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

def fetch_github_pr(pr_url: str):
    """
    Fetches a GitHub PR by URL and returns repo info + file diffs + score.
    """
    m = re.search(r'github\.com/([^/]+/[^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError("Not a valid GitHub PR URL")
    
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

    # Simple scoring: higher score for fewer changes (arbitrary)
    score = max(0, 100 - (total_additions + total_deletions))

    return {
        "repo_name": repo_name,   # template expects repo_name
        "pr_number": pr_number,
        "title": pr.title,
        "body": pr.body,
        "files": files,
        "score": score
    }

def parse_local_diff(diff_text: str):
    """
    Parse a unified diff text into PR-like data format.
    """
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

"""
Analyzer module for PR Review Agent.

It inspects added code in pull requests and reports issues such as
TODOs, cyclomatic complexity, missing docstrings, print-based logging,
Pyflakes warnings, and possible secrets.
"""

from __future__ import annotations

import ast
import json
import logging
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from radon.complexity import cc_visit

# configure a module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# penalty constants
PENALTY_TODO = 5
PENALTY_COMPLEXITY = 2
PENALTY_DOCSTRING = 1
PENALTY_PRINT = 3
PENALTY_PYFLAKES = 1
MAX_PENALTY_PER_ISSUE = {
    "todo": 20,
    "complexity": 20,
    "docstring": 5,
    "pyflakes": 10,
    "secret": 25,
    "large_addition": 5,
}


def extract_added_code(patch_text: str) -> str:
    """Return concatenated added lines (prefixed by '+') from a git patch."""
    added_lines: List[str] = [
        line[1:]
        for line in patch_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    return "\n".join(added_lines)


def count_todos(patch_text: str) -> int:
    """Count TODO/FIXME markers in a patch."""
    return sum(
        1
        for l in patch_text.splitlines()
        if "TODO" in l or "FIXME" in l
    )


def python_complexity_from_code(
    code_text: str,
) -> Optional[Dict[str, Any]]:
    """
    Use radon to compute average cyclomatic complexity of functions in code_text.
    If code_text is not valid python, return None.
    """
    try:
        blocks = cc_visit(code_text)
        if not blocks:
            return None
        avg = sum(b.complexity for b in blocks) / len(blocks)
        high = [b for b in blocks if b.complexity >= 10]
        return {
            "avg": avg,
            "high_count": len(high),
            "details": [
                {"name": b.name, "complexity": b.complexity} for b in blocks
            ],
        }
    except Exception as exc:
        logger.debug("Complexity analysis failed: %s", exc)
        return None


def uses_print_for_logging(code_text: str) -> bool:
    """Detect if print() is used for logging."""
    return bool(re.search(r"\bprint\s*\(", code_text))


def missing_docstrings(code_text: str) -> Optional[int]:
    """Count functions/classes without docstrings; return None if parse fails."""
    try:
        tree = ast.parse(code_text)
        missing = 0
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                if not ast.get_docstring(node):
                    missing += 1
        return missing
    except Exception as exc:
        logger.debug("Docstring check failed: %s", exc)
        return None


def run_pyflakes_on_code(code_text: str) -> List[str]:
    """
    Run pyflakes on code by dumping to a temp file and calling pyflakes (if installed).
    Return list of messages (strings). If pyflakes not found or error, return [].
    """
    if shutil.which("pyflakes") is None:
        return []

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code_text)
        fname = f.name

    try:
        out = subprocess.check_output(
            ["pyflakes", fname], stderr=subprocess.STDOUT, text=True
        )
        return out.splitlines()
    except subprocess.CalledProcessError as e:
        return e.output.splitlines() if e.output else []
    except Exception as exc:
        logger.debug("pyflakes run failed: %s", exc)
        return []


def analyze_pr(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    For each file in pr_data, analyze the added code and return a summary.
    """
    results: Dict[str, Any] = {"files": []}
    total_score = 100
    score_penalty = 0

    for f in pr_data.get("files", []):
        fname = f.get("filename")
        patch = f.get("patch", "")
        added = extract_added_code(patch)
        file_res: Dict[str, Any] = {"filename": fname, "issues": [], "metrics": {}}

        # Check TODOs
        todos = count_todos(patch)
        if todos:
            file_res["issues"].append(
                {"type": "todo", "detail": f"{todos} TODO/FIXME found"}
            )
            score_penalty += min(PENALTY_TODO * todos, MAX_PENALTY_PER_ISSUE["todo"])

        # If python file, perform python-specific checks
        if fname and fname.endswith(".py"):
            cc = python_complexity_from_code(added)
            if cc:
                file_res["metrics"]["cyclomatic"] = cc
                if cc["avg"] > 6:
                    file_res["issues"].append(
                        {
                            "type": "complexity",
                            "detail": f"avg complexity {cc['avg']:.1f}, high count {cc['high_count']}",
                        }
                    )
                    score_penalty += min(
                        int(cc["avg"]) * PENALTY_COMPLEXITY,
                        MAX_PENALTY_PER_ISSUE["complexity"],
                    )

            missing = missing_docstrings(added)
            if isinstance(missing, int) and missing > 0:
                file_res["issues"].append(
                    {
                        "type": "docstring",
                        "detail": f"{missing} missing docstrings/stubs",
                    }
                )
                score_penalty += min(
                    missing * PENALTY_DOCSTRING, MAX_PENALTY_PER_ISSUE["docstring"]
                )

            if uses_print_for_logging(added):
                file_res["issues"].append(
                    {
                        "type": "logging",
                        "detail": "uses print() for logging; prefer logging module",
                    }
                )
                score_penalty += PENALTY_PRINT

            pyflakes_msgs = run_pyflakes_on_code(added)
            if pyflakes_msgs:
                file_res["issues"].append(
                    {
                        "type": "pyflakes",
                        "detail": f"{len(pyflakes_msgs)} pyflakes warnings",
                    }
                )
                file_res["metrics"]["pyflakes_messages"] = pyflakes_msgs
                score_penalty += min(
                    len(pyflakes_msgs) * PENALTY_PYFLAKES,
                    MAX_PENALTY_PER_ISSUE["pyflakes"],
                )
        else:
            # Generic checks for other languages: long lines, secrets
            if len(added) > 2000:
                file_res["issues"].append(
                    {
                        "type": "large_addition",
                        "detail": "Large addition — consider splitting",
                    }
                )
                score_penalty += MAX_PENALTY_PER_ISSUE["large_addition"]
            # naive secret check
            if "PRIVATE_KEY" in added or "API_KEY" in added:
                file_res["issues"].append(
                    {"type": "secret", "detail": "Possible secret/API key in diff"}
                )
                score_penalty += MAX_PENALTY_PER_ISSUE["secret"]

        results["files"].append(file_res)

    final_score = max(total_score - score_penalty, 0)
    results["final_score"] = final_score
    results["penalty"] = score_penalty
    return results

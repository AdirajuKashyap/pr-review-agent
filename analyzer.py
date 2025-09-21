import re
from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor
import ast
import tempfile
import subprocess
import json

def extract_added_code(patch_text):
    """Return concatenated added lines (prefixed by '+') from a git patch."""
    added_lines = []
    for line in patch_text.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])
    return "\n".join(added_lines)

def count_todos(patch_text):
    return sum(1 for l in patch_text.splitlines() if 'TODO' in l or 'FIXME' in l)

def python_complexity_from_code(code_text):
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
        return {"avg": avg, "high_count": len(high), "details": [{"name":b.name,"complexity":b.complexity} for b in blocks]}
    except Exception:
        return None

def uses_print_for_logging(code_text):
    return bool(re.search(r'\bprint\s*\(', code_text))

def missing_docstrings(code_text):
    # naive: count defs without triple-quoted string immediately after
    missing = 0
    try:
        tree = ast.parse(code_text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if not doc:
                    missing += 1
    except Exception:
        # if parse fails, can't evaluate
        missing = None
    return missing

def run_pyflakes_on_code(code_text):
    """
    Run pyflakes on code by dumping to temp file and calling pyflakes (if installed).
    Return list of messages (strings). If pyflakes not found or error, return [].
    """
    import shutil
    if shutil.which("pyflakes") is None:
        return []
    import tempfile, subprocess
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write(code_text)
        fname = f.name
    try:
        out = subprocess.check_output(["pyflakes", fname], stderr=subprocess.STDOUT, text=True)
        return out.splitlines()
    except subprocess.CalledProcessError as e:
        return e.output.splitlines() if e.output else []
    except Exception:
        return []

def analyze_pr(pr_data):
    """
    For each file in pr_data, analyze the added code and return a summary.
    """
    results = {"files": [], "score_components": []}
    total_score = 100
    score_penalty = 0

    for f in pr_data["files"]:
        fname = f["filename"]
        patch = f.get("patch", "")
        added = extract_added_code(patch)
        file_res = {"filename": fname, "issues": [], "metrics": {}}

        # Check TODOs
        todos = count_todos(patch)
        if todos:
            file_res["issues"].append({"type":"todo","detail":f"{todos} TODO/FIXME found"})
            score_penalty += min(5 * todos, 20)

        # If python file, perform python-specific checks
        if fname.endswith('.py'):
            cc = python_complexity_from_code(added)
            if cc:
                file_res["metrics"]["cyclomatic"] = cc
                if cc["avg"] > 6:
                    file_res["issues"].append({"type":"complexity","detail":f"avg complexity {cc['avg']:.1f}, high count {cc['high_count']}"})
                    score_penalty += min(int(cc["avg"]) * 2, 20)
            missing = missing_docstrings(added)
            if isinstance(missing, int) and missing > 0:
                file_res["issues"].append({"type":"docstring","detail":f"{missing} missing docstrings/stubs"})
                score_penalty += min(missing * 1, 5)
            if uses_print_for_logging(added):
                file_res["issues"].append({"type":"logging","detail":"uses print() for logging; prefer logging module"})
                score_penalty += 3
            pyflakes_msgs = run_pyflakes_on_code(added)
            if pyflakes_msgs:
                file_res["issues"].append({"type":"pyflakes","detail": f"{len(pyflakes_msgs)} pyflakes warnings"})
                file_res["metrics"]["pyflakes_messages"] = pyflakes_msgs
                score_penalty += min(len(pyflakes_msgs) * 1, 10)
        else:
            # Generic checks for other languages: long lines, secrets
            if len(added) > 2000:
                file_res["issues"].append({"type":"large_addition","detail":"Large addition — consider splitting"})
                score_penalty += 5
            # naive secret check
            if "PRIVATE_KEY" in added or "API_KEY" in added:
                file_res["issues"].append({"type":"secret","detail":"Possible secret/API key in diff"})
                score_penalty += 25

        results["files"].append(file_res)

    final_score = max(total_score - score_penalty, 0)
    results["final_score"] = final_score
    results["penalty"] = score_penalty
    return results

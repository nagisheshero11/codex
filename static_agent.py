import subprocess
import json
import tempfile
import os


def run_flake8(code: str):
    """Run flake8 static analysis on a Python code string."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        # Run flake8 in JSON mode (shows linting issues)
        result = subprocess.run(
            ["flake8", temp_path, "--format=json"],
            capture_output=True,
            text=True
        )

        if result.returncode not in [0, 1]:  # 0 = no issues, 1 = some issues
            return {"error": result.stderr}

        try:
            output = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            output = {}

        issues = []
        for _, issue_list in output.items():
            for issue in issue_list:
                issues.append({
                    "line": issue.get("line_number"),
                    "code": issue.get("code"),
                    "message": issue.get("text")
                })

        return {"style_issues": issues}

    finally:
        os.remove(temp_path)  # cleanup temp file


def run_radon_complexity(code: str):
    """Measure cyclomatic complexity of the given code using radon."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        result = subprocess.run(
            ["radon", "cc", temp_path, "-j"],
            capture_output=True,
            text=True
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"complexity": []}

        issues = []
        for _, funcs in data.items():
            for fdata in funcs:
                issues.append({
                    "name": fdata["name"],
                    "complexity": fdata["complexity"],
                    "rank": fdata["rank"]
                })

        return {"complexity": issues}

    finally:
        os.remove(temp_path)
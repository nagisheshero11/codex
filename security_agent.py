def scan_security_issues(code: str):
    """Scans code for basic security issues (example implementation)."""
    issues = []
    lines = code.split('\n')
    for idx, line in enumerate(lines, 1):
        if 'eval(' in line:
            issues.append({
                'line': idx,
                'code': 'S001',
                'message': 'Use of eval() detected.'
            })
        if 'password' in line:
            issues.append({
                'line': idx,
                'code': 'S002',
                'message': 'Hardcoded password detected.'
            })
        if 'os.system(' in line or 'subprocess.Popen' in line:
            issues.append({
                'line': idx,
                'code': 'S003',
                'message': 'Potentially dangerous system call.'
            })
    return {'security_issues': issues}
import subprocess
import json

def run_flake8(code: str):
    """Runs flake8 checks on the given Python code string."""
    with open("temp_code.py", "w") as f:
        f.write(code)

    result = subprocess.run(["flake8", "temp_code.py", "--format=json"], capture_output=True, text=True)
    if result.returncode not in [0, 1]:
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

def run_radon_complexity(code: str):
    """Uses radon to measure cyclomatic complexity."""
    with open("temp_code.py", "w") as f:
        f.write(code)

    result = subprocess.run(["radon", "cc", "temp_code.py", "-j"], capture_output=True, text=True)
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
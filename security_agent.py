import ast
import re
import subprocess
import json
import os


# -----------------------------------------------------
# 🧠 Helper: Run Shell Command Safely
# -----------------------------------------------------
def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.stdout
    except Exception as e:
        return str(e)


# -----------------------------------------------------
# 🔍 1️⃣ Basic Heuristic Security Checks
# -----------------------------------------------------
def basic_security_patterns(code: str):
    """Simple text-based scans for obvious security red flags."""
    issues = []
    lines = code.split("\n")

    for idx, line in enumerate(lines, 1):
        if "eval(" in line or "exec(" in line:
            issues.append({
                "line": idx,
                "severity": "High",
                "category": "Code Injection",
                "message": "Use of eval() or exec() can execute arbitrary code.",
                "suggestion": "Avoid using eval/exec. Consider safer parsing alternatives."
            })
        if "password" in line.lower() or "secret" in line.lower():
            issues.append({
                "line": idx,
                "severity": "Medium",
                "category": "Hardcoded Secrets",
                "message": "Possible hardcoded password or secret key found.",
                "suggestion": "Store secrets in environment variables or secret managers."
            })
        if re.search(r"os\.system\(|subprocess\.(Popen|call|run)\(", line):
            issues.append({
                "line": idx,
                "severity": "High",
                "category": "Command Injection",
                "message": "Use of os.system or subprocess can be dangerous if user input is unsanitized.",
                "suggestion": "Use shlex.quote or subprocess.run with explicit arguments."
            })
        if "pickle.load(" in line or "yaml.load(" in line:
            issues.append({
                "line": idx,
                "severity": "Medium",
                "category": "Deserialization Attack",
                "message": "Unsafe deserialization using pickle/yaml.load detected.",
                "suggestion": "Use safe_load for YAML and avoid pickle with untrusted data."
            })
        if "requests.get(" in line and "verify=False" in line:
            issues.append({
                "line": idx,
                "severity": "Medium",
                "category": "SSL Verification Disabled",
                "message": "SSL verification disabled in requests call.",
                "suggestion": "Set verify=True or remove the flag."
            })

    return issues


# -----------------------------------------------------
# 🧩 2️⃣ AST-Based Security Analysis
# -----------------------------------------------------
class SecurityVisitor(ast.NodeVisitor):
    """Analyzes AST nodes for potential vulnerabilities."""

    def __init__(self):
        self.issues = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ("os", "subprocess", "pickle", "yaml", "cryptography.fernet"):
                self.issues.append({
                    "line": node.lineno,
                    "severity": "Info",
                    "category": "Dangerous Import",
                    "message": f"Importing '{alias.name}' may introduce security risks if misused.",
                    "suggestion": f"Review the use of '{alias.name}' for safe practices."
                })
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = self._get_func_name(node.func)

        dangerous_calls = {
            "eval": "Dynamic code execution.",
            "exec": "Dynamic code execution.",
            "os.system": "Command injection risk.",
            "subprocess.Popen": "Potential shell command injection.",
            "pickle.load": "Unsafe deserialization.",
            "yaml.load": "Unsafe YAML deserialization.",
        }

        if func_name in dangerous_calls:
            self.issues.append({
                "line": node.lineno,
                "severity": "High",
                "category": "Insecure Function Call",
                "message": f"Use of {func_name} — {dangerous_calls[func_name]}",
                "suggestion": f"Avoid using {func_name} on untrusted data."
            })

        if func_name in ("hashlib.md5", "hashlib.sha1"):
            self.issues.append({
                "line": node.lineno,
                "severity": "Medium",
                "category": "Weak Cryptography",
                "message": f"Use of weak hash function {func_name}.",
                "suggestion": "Use stronger algorithms like SHA-256 or SHA-512."
            })

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Detect possible secret assignments like API keys or tokens."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    if any(keyword in target.id.lower() for keyword in ["token", "password", "secret", "key"]):
                        self.issues.append({
                            "line": node.lineno,
                            "severity": "Medium",
                            "category": "Hardcoded Secret",
                            "message": "Possible hardcoded credential detected.",
                            "suggestion": "Use environment variables instead of plaintext storage."
                        })
        self.generic_visit(node)

    def _get_func_name(self, node):
        """Safely extract a dotted function name from any AST call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_func_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        else:
            return None

# -----------------------------------------------------
# 🧱 3️⃣ Optional Bandit Integration (if available)
# -----------------------------------------------------
def run_bandit_scan(code: str):
    """Run Bandit if installed locally for deeper analysis."""
    with open("temp_scan.py", "w") as f:
        f.write(code)
    try:
        result = subprocess.run(
            ["bandit", "-r", "temp_scan.py", "-f", "json"],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout or "{}")
        issues = []
        for issue in data.get("results", []):
            issues.append({
                "line": issue.get("line_number", "?"),
                "severity": issue.get("issue_severity", "Medium"),
                "category": issue.get("test_id", "BanditCheck"),
                "message": issue.get("issue_text", "Potential security risk detected."),
                "suggestion": issue.get("more_info", "Review Bandit documentation for mitigation."),
            })
        return issues
    except Exception:
        return []
    finally:
        if os.path.exists("temp_scan.py"):
            os.remove("temp_scan.py")


# -----------------------------------------------------
# 🧩 4️⃣ Main Security Analyzer
# -----------------------------------------------------
def scan_security_issues(code: str):
    """Perform hybrid security analysis on Python code."""
    all_issues = []

    # Step 1: Basic pattern detection
    all_issues.extend(basic_security_patterns(code))

    # Step 2: AST-based analysis
    try:
        tree = ast.parse(code)
        visitor = SecurityVisitor()
        visitor.visit(tree)
        all_issues.extend(visitor.issues)
    except SyntaxError as e:
        all_issues.append({
            "line": e.lineno or "?",
            "severity": "High",
            "category": "Syntax Error",
            "message": f"Could not parse code: {e.msg}",
            "suggestion": "Fix syntax issues before scanning."
        })

    # Step 3: Optional Bandit integration
    bandit_results = run_bandit_scan(code)
    if bandit_results:
        all_issues.extend(bandit_results)

    # Step 4: Deduplicate and sort by severity
    seen = set()
    deduped = []
    for issue in all_issues:
        key = (issue["line"], issue["message"])
        if key not in seen:
            deduped.append(issue)
            seen.add(key)

    severity_order = {"High": 1, "Medium": 2, "Low": 3, "Info": 4}
    deduped.sort(key=lambda i: severity_order.get(i.get("severity", "Info")))

    return {"security_issues": deduped}
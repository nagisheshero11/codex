import subprocess
import json
import tempfile
import os
import ast
import statistics

# ------------------------------------------------------
# Utility: Safe command runner
# ------------------------------------------------------
def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.stdout.strip()
    except Exception as e:
        return str(e)


# ------------------------------------------------------
# 1️⃣ Syntax & Indentation Analysis
# ------------------------------------------------------
def check_syntax_and_indentation(code: str):
    """Check syntax, indentation, and mixed tab/space issues."""
    issues = []
    lines = code.splitlines()

    # Mixed indentation
    for i, line in enumerate(lines, 1):
        if "\t" in line and line.startswith(" "):
            issues.append({
                "line": i,
                "message": "Mixed indentation (tabs and spaces).",
                "severity": "Medium"
            })

    try:
        compile(code, "<string>", "exec")
    except (SyntaxError, IndentationError) as e:
        issues.append({
            "line": getattr(e, "lineno", "?"),
            "message": f"{e.__class__.__name__}: {e.msg}",
            "severity": "High"
        })
        return {"syntax_issues": issues, "fatal": True}

    return {"syntax_issues": issues, "fatal": False}


# ------------------------------------------------------
# 2️⃣ Style / Linting (flake8)
# ------------------------------------------------------
def run_flake8(code: str):
    """Run flake8 static analysis."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["flake8", temp_path, "--format=json"],
            capture_output=True,
            text=True
        )
        if result.returncode not in [0, 1]:
            return {"style_issues": [], "error": result.stderr}

        try:
            output = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            output = {}

        issues = []
        for _, issue_list in output.items():
            for i in issue_list:
                issues.append({
                    "line": i.get("line_number"),
                    "code": i.get("code"),
                    "message": i.get("text")
                })

        return {"style_issues": issues}
    finally:
        os.remove(temp_path)


# ------------------------------------------------------
# 3️⃣ Cyclomatic & Maintainability Complexity (Radon)
# ------------------------------------------------------
def run_radon_metrics(code: str):
    """Run radon for cyclomatic complexity & maintainability index."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
        f.write(code)
        temp_path = f.name

    try:
        # Cyclomatic
        cc_result = subprocess.run(["radon", "cc", temp_path, "-j"], capture_output=True, text=True)
        cc_data = json.loads(cc_result.stdout or "{}")

        complexities = []
        for _, funcs in cc_data.items():
            for fdata in funcs:
                complexities.append({
                    "name": fdata["name"],
                    "complexity": fdata["complexity"],
                    "rank": fdata["rank"]
                })

        # Maintainability Index
        mi_result = subprocess.run(["radon", "mi", temp_path, "-j"], capture_output=True, text=True)
        mi_data = json.loads(mi_result.stdout or "{}")
        mi_score = next(iter(mi_data.values()), {}).get("mi", None)

        return {"complexity": complexities, "maintainability_index": mi_score}
    finally:
        os.remove(temp_path)


# ------------------------------------------------------
# 4️⃣ Algorithmic Complexity Estimation
# ------------------------------------------------------
def estimate_big_o_complexity(code: str):
    """Heuristic time/space complexity estimation using AST."""
    try:
        tree = ast.parse(code)
    except Exception:
        return {"algorithmic_complexity": {"estimate": "Unknown", "space": "Unknown", "details": []}}

    loops, nested, recursions, comp, sorts = 0, 0, 0, 0, 0
    details = []

    def visit(node, depth=0):
        nonlocal loops, nested, recursions, comp, sorts
        if isinstance(node, (ast.For, ast.While)):
            loops += 1
            if depth > 0:
                nested += 1
            details.append(f"Loop at line {node.lineno}, depth {depth+1}")

        if isinstance(node, ast.ListComp):
            comp += 1
            details.append(f"List comprehension at line {node.lineno}")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("sort", "sorted"):
                sorts += 1
                details.append(f"Sorting detected at line {node.lineno}")

        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == node.name:
                    recursions += 1
                    details.append(f"Recursive call in {node.name}() at line {inner.lineno}")

        for child in ast.iter_child_nodes(node):
            visit(child, depth + (1 if isinstance(node, (ast.For, ast.While)) else depth))

    visit(tree)

    # Time Complexity
    if recursions > 0:
        big_o = "O(n^rec)"
    elif nested >= 2:
        big_o = "O(n^2)"
    elif loops > 0 and sorts > 0:
        big_o = "O(n log n)"
    elif loops == 1:
        big_o = "O(n)"
    elif comp > 0:
        big_o = "O(n)"
    else:
        big_o = "O(1)"

    # Space Complexity
    if comp > 0 or loops > 0:
        space = "O(n)"
    elif recursions > 0:
        space = "O(recursion depth)"
    else:
        space = "O(1)"

    return {"algorithmic_complexity": {"estimate": big_o, "space": space, "details": details}}


# ------------------------------------------------------
# 5️⃣ Semantic Analyzer
# ------------------------------------------------------
class SemanticAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.unused_vars = set()
        self.assigned = set()
        self.used = set()
        self.mutable_defaults = []
        self.unreachable = []
        self.line_count = 0

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned.add(target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.line_count += len(node.body)
        # Mutable default arguments
        for d in node.args.defaults:
            if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                self.mutable_defaults.append(
                    {"line": node.lineno, "message": f"Mutable default arg in {node.name}()"}
                )
        self.generic_visit(node)

    def visit_If(self, node):
        if isinstance(node.test, ast.Constant) and node.test.value in (True, False):
            self.unreachable.append(
                {"line": node.lineno, "message": "Unreachable branch (constant condition)."}
            )
        self.generic_visit(node)


def analyze_semantics(code: str):
    try:
        tree = ast.parse(code)
    except Exception:
        return {"semantic_issues": []}

    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)

    unused = analyzer.assigned - analyzer.used
    semantic_issues = []

    for name in unused:
        semantic_issues.append({"message": f"Variable '{name}' defined but never used."})
    for i in analyzer.mutable_defaults:
        semantic_issues.append(i)
    for i in analyzer.unreachable:
        semantic_issues.append(i)

    return {"semantic_issues": semantic_issues}


# ------------------------------------------------------
# 6️⃣ Code Smells Detector
# ------------------------------------------------------
def detect_code_smells(code: str):
    smells = []
    try:
        tree = ast.parse(code)
    except Exception:
        return {"code_smells": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body_len = len(node.body)
            if body_len > 40:
                smells.append({"line": node.lineno, "message": f"Function '{node.name}' too long ({body_len} lines)."})
            if any(isinstance(n, ast.If) for n in ast.walk(node)) and sum(
                isinstance(n, ast.If) for n in ast.walk(node)
            ) > 5:
                smells.append({"line": node.lineno, "message": f"Function '{node.name}' deeply nested (>{5} levels)."})
        if isinstance(node, ast.ClassDef):
            if len(node.body) > 100:
                smells.append({"line": node.lineno, "message": f"Large class '{node.name}' detected."})
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and abs(node.value) > 1000:
            smells.append({"line": getattr(node, 'lineno', '?'), "message": f"Magic number {node.value}."})

    return {"code_smells": smells}


# ------------------------------------------------------
# 7️⃣ Master Analyzer — Combine Everything
# ------------------------------------------------------
def run_static_analysis(code: str):
    """Comprehensive static code analysis."""
    syntax = check_syntax_and_indentation(code)
    if syntax.get("fatal"):
        return {"syntax_issues": syntax["syntax_issues"], "fatal": True}

    style = run_flake8(code)
    radon = run_radon_metrics(code)
    algo = estimate_big_o_complexity(code)
    semantics = analyze_semantics(code)
    smells = detect_code_smells(code)

    complexities = [c["complexity"] for c in radon.get("complexity", []) if "complexity" in c]
    avg_complexity = statistics.mean(complexities) if complexities else 0

    summary = {
        "functions": len(radon.get("complexity", [])),
        "avg_complexity": avg_complexity,
        "maintainability_index": radon.get("maintainability_index"),
        "estimated_time_complexity": algo["algorithmic_complexity"]["estimate"],
        "estimated_space_complexity": algo["algorithmic_complexity"]["space"],
        "high_severity_warnings": [
            i for i in syntax["syntax_issues"] if i.get("severity") == "High"
        ],
    }

    return {
        "syntax_analysis": syntax,
        **style,
        **radon,
        **algo,
        **semantics,
        **smells,
        "summary": summary,
    }
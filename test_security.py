from security_agent import scan_security_issues

# Sample code containing intentional security issues
code = """
password = "1234"
eval(user_input)
os.system("rm -rf /")
import subprocess
subprocess.Popen("ls", shell=True)
"""

# Run the scan
results = scan_security_issues(code)

# Pretty print results
for issue in results["security_issues"]:
    print(f"Line {issue['line']}: {issue['message']}")
    print(f"   Code: {issue['code']}")
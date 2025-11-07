# test_llm.py
from llm_agent import generate_review
from security_agent import scan_security_issues
from static_agent import run_flake8, run_radon_complexity

sample_code = """
def badFunction(x,y):
    password="1234"
    result = eval(x)
    os.system("ls -la")
    for i in range(10):
        for j in range(10):
            for k in range(5):
                print(i,j,k)
"""

# Run static & security tools
static_style = run_flake8(sample_code)
static_complex = run_radon_complexity(sample_code)
static_results = {**static_style, **static_complex}
security_results = scan_security_issues(sample_code)

print("Static:", static_results)
print("Security:", security_results)

# Call Gemini LLM (this will consume your API quota)
out = generate_review(sample_code, static_results, security_results)
print("LLM RAW:\n", out["raw_text"][:2000])  # print first 2000 chars
print("\nPARSED JSON:\n", out["parsed"])
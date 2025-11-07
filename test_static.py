from static_agent import run_flake8, run_radon_complexity

sample_code = """
def messy_function(x ,y):
    print(  "Hello"  )
    if x>10:
        for i in range(5): print(i)
    return y
"""

print("Running flake8...")
print(run_flake8(sample_code))

print("\nRunning radon...")
print(run_radon_complexity(sample_code))
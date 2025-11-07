from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from static_agent import run_flake8, run_radon_complexity
from security_agent import scan_security_issues
from llm_agent import generate_review

app = FastAPI(title="Code Review AI Agent")

# Allow frontend (Streamlit or localhost) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeInput(BaseModel):
    code: str

@app.post("/review")
async def review_code(data: CodeInput):
    """Combine static, security, and LLM analysis into one response."""
    code = data.code

    # Step 1: Run static analysis
    static_style = run_flake8(code)
    static_complexity = run_radon_complexity(code)
    static_results = {**static_style, **static_complexity}

    # Step 2: Run security analysis
    security_results = scan_security_issues(code)

    # Step 3: Generate Gemini review
    llm_output = generate_review(code, static_results, security_results)
    llm_review = llm_output.get("parsed") or {"raw_text": llm_output.get("raw_text")}

    # Step 4: Combine results
    return {
        "static_analysis": static_results,
        "security_analysis": security_results,
        "llm_review": llm_review,
    }

@app.get("/")
async def root():
    return {"message": "Code Review AI Agent is running!"}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Updated import — we now use the unified static analyzer
from static_agent import run_static_analysis
from security_agent import scan_security_issues
from llm_agent import generate_review

app = FastAPI(title="Code Review AI Agent")

# Allow frontend (Streamlit or localhost) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In production, specify Streamlit frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeInput(BaseModel):
    """Expected input schema for code analysis requests."""
    code: str


@app.post("/review")
async def review_code(data: CodeInput):
    """
    Perform full code review:
    - Static analysis (syntax, linting, complexity, code smells)
    - Security analysis
    - LLM-based review using Gemini
    """
    code = data.code

    # Step 1: Static Analysis
    static_results = run_static_analysis(code)

    # If there’s a fatal syntax or indentation error, skip further checks
    if static_results.get("fatal"):
        return {
            "static_analysis": static_results,
            "security_analysis": {},
            "llm_review": {
                "summary": "❌ Code could not be analyzed due to syntax or indentation errors.",
                "comments": [],
                "refactor_plan": ""
            },
        }

    # Step 2: Security Analysis
    security_results = scan_security_issues(code)

    # Step 3: Generate LLM Review
    llm_output = generate_review(code, static_results, security_results)
    llm_review = llm_output.get("parsed") or {"raw_text": llm_output.get("raw_text")}

    # Step 4: Combine Results
    return {
        "static_analysis": static_results,
        "security_analysis": security_results,
        "llm_review": llm_review,
    }


@app.get("/")
async def root():
    """Simple heartbeat endpoint."""
    return {"message": "✅ Code Review AI Agent is running!"}
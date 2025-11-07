# llm_agent.py
from dotenv import load_dotenv
import os
import textwrap
import logging
from typing import Dict, Any, Optional

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
print(f"Looking for .env file at: {dotenv_path}")
load_dotenv(dotenv_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY loaded:", GEMINI_API_KEY)

# Lazy import to avoid import errors when key isn't set
try:
    from google import genai
except Exception as e:
    genai = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _build_prompt(code: str, static_results: Dict[str, Any], security_results: Dict[str, Any]) -> str:
    """
    Build a concise but structured prompt to send to Gemini.
    We provide: the code, style issues (from flake8/radon), and security warnings.
    Ask Gemini to produce:
      - a short summary (2-3 sentences),
      - line-tagged review comments (bullet list),
      - concrete suggested fixes (code snippets or instructions),
      - severity labels (low/medium/high) for each issue.
    """
    static_summary = ""
    if static_results:
        si = static_results.get("style_issues", [])
        comp = static_results.get("complexity", [])
        if si:
            static_summary += "Style issues (first 6):\n"
            for issue in si[:6]:
                static_summary += f"- Line {issue.get('line')}: {issue.get('code')} — {issue.get('message')}\n"
        if comp:
            static_summary += "\nComplexity findings (first 6):\n"
            for c in comp[:6]:
                name = c.get("name")
                complexity = c.get("complexity")
                rank = c.get("rank")
                static_summary += f"- {name}: complexity={complexity}, rank={rank}\n"

    security_summary = ""
    if security_results:
        sec = security_results.get("security_issues", [])
        if sec:
            security_summary += "Security warnings (first 6):\n"
            for s in sec[:6]:
                security_summary += f"- Line {s.get('line')}: {s.get('message')} — code: {s.get('code')}\n"

    prompt = f"""
You are an expert Python code reviewer. The user will paste a Python file. Provide a concise, helpful review:
1) A 2-3 sentence summary of the overall code quality.
2) A bullet list of review comments mapped to line numbers (e.g., "Line 42: ...").
3) For each comment, provide a short suggested fix or example code snippet where applicable.
4) Tag each issue with severity: LOW / MEDIUM / HIGH.
5) At the end, provide a one-paragraph refactoring plan with 3 concrete steps.

--- FILE START ---
{code}
--- FILE END ---

--- STATIC ANALYSIS (tool output) ---
{static_summary}

--- SECURITY ANALYSIS (tool output) ---
{security_summary}

Important: be concise. If you don't have enough info to decide, state assumptions clearly. Return ONLY a JSON object with these exact keys:

- summary: string with 2-3 sentences describing overall code quality
- comments: array of objects, each with:
  * line: number indicating the line (or null if general)
  * message: string describing the issue
  * suggestion: string with concrete fix or example
  * severity: string enum "LOW", "MEDIUM", or "HIGH"
- refactor_plan: string with 3 concrete numbered steps

Make sure to return only valid JSON with no explanation text.
"""
    return textwrap.dedent(prompt)


def generate_review(code: str,
                    static_results: Optional[Dict[str, Any]] = None,
                    security_results: Optional[Dict[str, Any]] = None,
                    model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Send a prompt to Gemini and return the parsed JSON response.
    """
    if genai is None:
        raise RuntimeError("google-genai not available. Install google-genai and set GEMINI_API_KEY in .env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = _build_prompt(code, static_results or {}, security_results or {})

    try:
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            # Optional: adjust response length / temperature if supported
        )
        text = getattr(resp, "text", None) or str(resp)
    except Exception as e:
        logger.exception("LLM call failed")
        raise

    # Try to extract JSON from the model output.
    # The model is asked to return JSON; attempt naive extraction.
    import json
    try:
        # If the model returns other text + JSON, find first '{' and parse.
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            json_text = text[first_brace:last_brace + 1]
            parsed = json.loads(json_text)
            return {"raw_text": text, "parsed": parsed}
        else:
            # fallback: return raw text
            return {"raw_text": text, "parsed": None}
    except Exception as e:
        logger.exception("Failed to parse LLM JSON response")
        return {"raw_text": text, "parsed": None}
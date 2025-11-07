import streamlit as st
import requests
import json

BACKEND_URL = "http://127.0.0.1:8000/review"

st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Code Review Agent")
st.markdown(
    "Analyze your Python code for **style issues**, **complexity**, "
    "**security risks**, and get **AI-powered review feedback**."
)


st.subheader("Paste your Python code here:")
code_input = st.text_area(
    label="Code Input",
    placeholder="def greet():\n    print('Hello World!')",
    height=250
)


if st.button("🔍 Analyze Code", use_container_width=True):
    if not code_input.strip():
        st.warning("⚠️ Please paste some Python code before analyzing.")
    else:
        with st.spinner("Analyzing code... 🧠"):
            try:
                response = requests.post(
                    BACKEND_URL,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"code": code_input}),
                    timeout=120
                )

                if response.status_code == 200:
                    results = response.json()

                    # -----------------------------
                    # Display static analysis
                    # -----------------------------
                    st.header("🧱 Static Analysis")
                    if results["static_analysis"].get("style_issues"):
                        st.error("**Style Issues Found:**")
                        for issue in results["static_analysis"]["style_issues"]:
                            st.write(f"Line {issue['line']} — `{issue['message']}`")
                    else:
                        st.success("No style issues found ✅")

                    if results["static_analysis"].get("complexity"):
                        st.info("**Complexity Metrics:**")
                        for func in results["static_analysis"]["complexity"]:
                            st.write(
                                f"Function `{func['name']}` → Complexity `{func['complexity']}` (Rank {func['rank']})"
                            )

                    # -----------------------------
                    # Display security analysis
                    # -----------------------------
                    st.header("🔒 Security Analysis")
                    if results["security_analysis"].get("security_issues"):
                        for issue in results["security_analysis"]["security_issues"]:
                            st.error(f"Line {issue['line']}: {issue['message']}")
                    else:
                        st.success("No security issues detected ✅")

                    # -----------------------------
                    # Display LLM review
                    # -----------------------------
                    st.header("🧠 Gemini LLM Review")
                    review = results["llm_review"]
                    st.markdown(f"**Summary:** {review.get('summary', 'No summary generated.')}")
                    
                    if "comments" in review:
                        for comment in review["comments"]:
                            st.markdown(
                                f"""
                                **Line {comment.get('line', '?')}:** {comment.get('message', '')}  
                                💡 *Suggestion:* {comment.get('suggestion', '')}  
                                ⚠️ *Severity:* `{comment.get('severity', 'N/A')}`
                                """
                            )

                    if "refactor_plan" in review:
                        st.subheader("🛠️ Suggested Refactor Plan")
                        st.markdown(review["refactor_plan"])

                else:
                    st.error(f"Backend error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Connection error: {e}")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit, FastAPI, and Google Gemini")
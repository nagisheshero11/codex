import streamlit as st
import requests
import json
from streamlit_ace import st_ace

BACKEND_URL = "http://127.0.0.1:8000/review"

st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #f6f7fb, #f0f2ff);
        font-family: 'Inter', sans-serif;
        color: #2c2c2c;
    }
    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #272640;
    }
    .stButton>button {
        border: none;
        background: linear-gradient(90deg, #c4c7ff, #e0e7ff);
        color: #2d2d2d;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 500;
        font-size: 1rem;
        box-shadow: 0 3px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #d3d6ff, #f2f3ff);
        transform: translateY(-1px);
    }
    .card {
        background: rgba(255,255,255,0.8);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-top: 1.2rem;
        backdrop-filter: blur(8px);
    }
    .divider {
        border-bottom: 1px solid #e9ebff;
        margin: 1.5rem 0;
    }
    /* Hide empty containers */
    div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>AI Code Review Agent</h1>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.subheader("Paste Your Python Code")
code_input = st_ace(
    language="python",
    theme="chrome",
    font_size=14,
    tab_size=4,
    height=240,
    show_gutter=True,
    wrap=False,
    key="ace_editor"
)

if st.button("Analyze Code", use_container_width=True):
    if not code_input or not code_input.strip():
        st.warning("⚠️ Please paste some Python code first.")
    else:
        with st.spinner("Analyzing your code... 🧠"):
            try:
                response = requests.post(
                    BACKEND_URL,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"code": code_input}),
                    timeout=120
                )

                if response.status_code == 200:
                    results = response.json()

                    # ---------- Static Analysis ----------
                    with st.container():
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.subheader("Static Analysis")
                        if results["static_analysis"].get("style_issues"):
                            for issue in results["static_analysis"]["style_issues"]:
                                st.write(f"**Line {issue['line']}** — {issue['message']}")
                        else:
                            st.success("No style issues found ✅")

                        if results["static_analysis"].get("complexity"):
                            for func in results["static_analysis"]["complexity"]:
                                st.info(
                                    f"Function `{func['name']}` → Complexity `{func['complexity']}` (Rank {func['rank']})"
                                )
                        st.markdown("</div>", unsafe_allow_html=True)

                    # ---------- Security Analysis ----------
                    with st.container():
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.subheader("Security Analysis")
                        if results["security_analysis"].get("security_issues"):
                            for issue in results["security_analysis"]["security_issues"]:
                                st.error(f"⚠️ Line {issue['line']}: {issue['message']}")
                        else:
                            st.success("No security issues detected ✅")
                        st.markdown("</div>", unsafe_allow_html=True)

                    # ---------- LLM Review ----------
                    with st.container():
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.subheader("AI Code Review")
                        review = results["llm_review"]
                        st.markdown(f"**Summary:** {review.get('summary', 'No summary generated.')}")

                        if "comments" in review:
                            for comment in review["comments"]:
                                st.markdown(
                                    f"""
                                    <div style='padding:0.6rem 1rem; background:#f8f9ff; border-radius:10px; margin:0.4rem 0;'>
                                    <b>Line {comment.get('line', '?')}</b>: {comment.get('message', '')}<br>
                                    <i>{comment.get('suggestion', '')}</i><br>
                                    <b>Severity:</b> {comment.get('severity', 'N/A')}
                                    </div>
                                    """, unsafe_allow_html=True
                                )

                        if "refactor_plan" in review:
                            st.subheader("Refactor Plan")
                            st.markdown(f"<p style='color:#444;'>{review['refactor_plan']}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error(f"Backend error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Connection error: {e}")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; font-size:0.85rem; color:#888;'>Built with ❤️ using Streamlit, FastAPI, and Google Gemini</p>",
    unsafe_allow_html=True
)
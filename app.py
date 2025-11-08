import streamlit as st
import requests
import json
from streamlit_ace import st_ace

# -----------------------------
# Backend Configuration
# -----------------------------
BACKEND_URL = "http://127.0.0.1:8000/review"

# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="centered"
)

# -----------------------------
# Custom Pastel Styling
# -----------------------------
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #f6f7fb, #f0f2ff);
        font-family: 'Inter', sans-serif;
        color: #2c2c2c;
    }
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #272640;
    }
    .stButton>button {
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        font-size: 1rem;
        margin: 0 0.3rem;
        box-shadow: 0 3px 8px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .file-section {
        background: rgba(255,255,255,0.8);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-top: 1.5rem;
        backdrop-filter: blur(8px);
    }
    .divider {
        border-bottom: 1px solid #e9ebff;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown("<h1 style='text-align:center;'>AI Code Review Agent</h1>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# -----------------------------
# Input Section
# -----------------------------
st.subheader("📝 Write or Upload Your Python Code")

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

uploaded_files = st.file_uploader(
    "Or upload one or more Python files",
    type=["py"],
    accept_multiple_files=True,
)

# -----------------------------
# Session State Setup
# -----------------------------
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

if "selected_view" not in st.session_state:
    st.session_state.selected_view = "🧩 Static Analysis"

# -----------------------------
# Analyze Button
# -----------------------------
if st.button("Analyze Code", use_container_width=True):
    code_sources = []

    if code_input and code_input.strip():
        code_sources.append(("Editor Input", code_input))

    if uploaded_files:
        for file in uploaded_files:
            content = file.read().decode("utf-8")
            if content.strip():
                code_sources.append((file.name, content))

    if not code_sources:
        st.warning("⚠️ Please enter or upload at least one Python file with code.")
    else:
        with st.spinner("Analyzing code... 🧠"):
            analysis_data = {}

            for filename, content in code_sources:
                try:
                    response = requests.post(
                        BACKEND_URL,
                        headers={"Content-Type": "application/json"},
                        data=json.dumps({"code": content}),
                        timeout=120
                    )
                    if response.status_code == 200:
                        analysis_data[filename] = response.json()
                    else:
                        analysis_data[filename] = {"error": f"Backend error ({response.status_code})"}
                except requests.exceptions.RequestException as e:
                    analysis_data[filename] = {"error": str(e)}

            st.session_state.analysis_results = analysis_data
            st.success("✅ Analysis completed successfully! Use the buttons below to view results.")

# -----------------------------
# View Toggle Buttons
# -----------------------------
if st.session_state.analysis_results:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧩 Static"):
            st.session_state.selected_view = "🧩 Static Analysis"
    with col2:
        if st.button("🛡️ Security"):
            st.session_state.selected_view = "🛡️ Security Analysis"
    with col3:
        if st.button("💬 Review"):
            st.session_state.selected_view = "💬 AI Review"

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # -----------------------------
    # Results Display
    # -----------------------------
    for filename, results in st.session_state.analysis_results.items():
        st.markdown(f"<div class='file-section'>", unsafe_allow_html=True)
        st.markdown(f"### 📄 {filename}", unsafe_allow_html=True)

        if "error" in results:
            st.error(results["error"])
            st.markdown("</div>", unsafe_allow_html=True)
            continue

        selected_view = st.session_state.selected_view

        # ---- STATIC ANALYSIS ----
        if selected_view == " Static Analysis":
            static = results.get("static_analysis", {})
            if static.get("style_issues"):
                for issue in static["style_issues"]:
                    st.write(f"**Line {issue['line']}** — {issue['message']}")
            else:
                st.success("No style issues found ✅")

            if static.get("complexity"):
                for func in static["complexity"]:
                    st.info(
                        f"Function `{func['name']}` → Complexity `{func['complexity']}` (Rank {func['rank']})"
                    )

        # ---- SECURITY ANALYSIS ----
        elif selected_view == "Security Analysis":
            sec = results.get("security_analysis", {})
            if sec.get("security_issues"):
                for issue in sec["security_issues"]:
                    st.error(f"⚠️ Line {issue['line']}: {issue['message']}")
            else:
                st.success("No security issues detected ✅")

        # ---- LLM REVIEW ----
        elif selected_view == "AI Review":
            review = results.get("llm_review", {})
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
                        """,
                        unsafe_allow_html=True
                    )

            if "refactor_plan" in review:
                st.subheader("Refactor Plan")
                st.markdown(f"<p style='color:#444;'>{review['refactor_plan']}</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; font-size:0.85rem; color:#888;'>Built with ❤️ using Streamlit, FastAPI, and Google Gemini</p>",
    unsafe_allow_html=True
)
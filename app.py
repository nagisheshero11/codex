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
    layout="wide"
)

# -----------------------------
# Custom Styling
# -----------------------------
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #e9ecff, #f6f7fb);
        font-family: 'Inter', sans-serif;
        color: #2c2c2c;
    }
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #1a1b41;
    }
    .stButton>button {
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.4rem;
        font-weight: 500;
        font-size: 1rem;
        background: linear-gradient(90deg, #a4b8ff, #d4dcff);
        color: #222;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #c0cbff, #e0e7ff);
        transform: translateY(-2px);
    }
    .file-section {
        background: rgba(255,255,255,0.9);
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
        margin-top: 1.2rem;
        backdrop-filter: blur(8px);
    }
    .divider {
        border-bottom: 1px solid #e0e2ff;
        margin: 1.5rem 0;
    }
    .highlight {
        background: rgba(220,230,255,0.8);
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
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

col_code, col_upload = st.columns([2, 1])

with col_code:
    code_input = st_ace(
        language="python",
        theme="chrome",
        font_size=14,
        tab_size=4,
        height=260,
        show_gutter=True,
        wrap=False,
        key="ace_editor"
    )

with col_upload:
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
if st.button("🔍 Analyze Code", use_container_width=True):
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
        with st.spinner("Analyzing your code with static, security, and LLM agents... 🧠"):
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
            st.success("✅ Analysis completed! Use the buttons below to view each analysis.")

# -----------------------------
# View Selection
# -----------------------------
if st.session_state.analysis_results:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🧩 Static Analysis"):
            st.session_state.selected_view = "🧩 Static Analysis"
    with c2:
        if st.button("🛡️ Security Analysis"):
            st.session_state.selected_view = "🛡️ Security Analysis"
    with c3:
        if st.button("💬 AI Review"):
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
            static = results.get("static_analysis", {}) or results
            summary = static.get("summary", {})

            st.markdown("### 📊 Summary Overview")
            st.markdown(
                f"""
                <div style='padding:0.8rem 1rem; border-radius:12px; background:rgba(245,247,255,0.9);'>
                <b>Functions:</b> {summary.get('functions', '—')} &nbsp;&nbsp;
                <b>Avg Complexity:</b> {summary.get('avg_complexity', '—'):.2f} &nbsp;&nbsp;
                <b>Maintainability Index:</b> {summary.get('maintainability_index', 'N/A')}<br>
                <b>Time Complexity:</b> <span style='color:#0b7285;'>{summary.get('estimated_time_complexity', '?')}</span> &nbsp;&nbsp;
                <b>Space Complexity:</b> <span style='color:#495057;'>{summary.get('estimated_space_complexity', '?')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            mi = summary.get("maintainability_index")
            if mi and isinstance(mi, (int, float)):
                color = "#2b8a3e" if mi > 75 else "#fab005" if mi > 50 else "#c92a2a"
                st.markdown(
                    f"""
                    <div style='margin-top:0.5rem;'>
                    <b>Maintainability Index:</b>
                    <div style='background:#dee2e6; height:12px; border-radius:8px; overflow:hidden;'>
                        <div style='width:{mi}%; background:{color}; height:12px;'></div>
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # Syntax & Style
            syntax_issues = static.get("syntax_analysis", {}).get("syntax_issues", [])
            style_issues = static.get("style_issues", [])

            st.markdown("### Syntax & Style Checks")
            if not syntax_issues and not style_issues:
                st.success("✅ No syntax or style issues found!")
            else:
                if syntax_issues:
                    with st.expander("Syntax / Indentation Issues ⚠️", expanded=True):
                        for issue in syntax_issues:
                            st.error(f"Line {issue.get('line', '?')}: {issue.get('message', '')}")
                if style_issues:
                    with st.expander("Style / Lint Issues ✨"):
                        for issue in style_issues:
                            st.warning(f"Line {issue.get('line', '?')} [{issue.get('code', '?')}]: {issue.get('message', '')}")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # Complexity
            st.markdown("### Complexity & Performance Insights")
            algo = static.get("algorithmic_complexity", {})
            complexity = static.get("complexity", [])

            if complexity:
                for func in complexity:
                    st.info(
                        f"Function `{func.get('name', '?')}` → Complexity `{func.get('complexity', '?')}` (Rank {func.get('rank', '?')})"
                    )

            if algo:
                est = algo.get("estimate", "?")
                space = algo.get("space", "?")
                st.markdown(
                    f"""
                    <div style='background:rgba(230,240,255,0.6); padding:10px; border-radius:8px;'>
                    <b>Estimated Time:</b> {est} <br>
                    <b>Estimated Space:</b> {space}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # Semantic Issues
            st.markdown("###  Semantic Analysis")
            semantics = static.get("semantic_issues", [])
            if semantics:
                for s in semantics:
                    st.warning(f"Line {s.get('line', '?')}: {s.get('message', '')}")
            else:
                st.success("No semantic issues detected ✅")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # Code Smells
            st.markdown("### Code Smells")
            smells = static.get("code_smells", [])
            if smells:
                for sm in smells:
                    st.error(f"⚠️ {sm.get('message', '')} (line {sm.get('line', '?')})")
            else:
                st.success("No major code smells detected 🧼")

        # ---- SECURITY ANALYSIS ----
        elif selected_view == " Security Analysis":
            sec = results.get("security_analysis", {})
            issues = sec.get("security_issues", [])
            if issues:
                for issue in issues:
                    st.error(f"⚠️ Line {issue.get('line', '?')}: {issue.get('message', '')}")
            else:
                st.success("No security issues detected ✅")

        # ---- LLM REVIEW ----
        elif selected_view == " AI Review":
            review = results.get("llm_review", {})
            st.markdown(f"**Summary:** {review.get('summary', 'No summary generated.')}")

            comments = review.get("comments", [])
            if comments:
                for c in comments:
                    st.markdown(
                        f"""
                        <div style='padding:0.7rem 1rem; background:#f8f9ff; border-radius:10px; margin:0.4rem 0;'>
                        <b>Line {c.get('line', '?')}</b>: {c.get('message', '')}<br>
                        <i>{c.get('suggestion', '')}</i><br>
                        <b>Severity:</b> {c.get('severity', 'N/A')}
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
    "<p style='text-align:center; font-size:0.85rem; color:#666;'>Built with ❤️ using Streamlit, FastAPI, and Google Gemini</p>",
    unsafe_allow_html=True
)
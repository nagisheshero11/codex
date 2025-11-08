import streamlit as st
import requests
import json
from streamlit_ace import st_ace
from typing import List

BACKEND_URL = "http://127.0.0.1:8000/review"

st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="centered"
)

st.markdown(
    """
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
    pre.preview {
        background: #f8f9ff;
        border-radius: 10px;
        padding: 0.7rem;
        font-size: 0.85rem;
        color: #333;
        overflow-x: auto;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<h1 style='text-align:center;'>AI Code Review Agent</h1>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


st.subheader("Upload your Python files (one or more):")

uploaded_files = st.file_uploader(
    "📁 Upload .py files",
    type=["py"],
    accept_multiple_files=True,
)

uploaded_list: List[dict] = []
if uploaded_files:
    for f in uploaded_files:
        try:
            content = f.read().decode("utf-8")
        except Exception:
            content = f.read().decode("utf-8", errors="ignore")
        uploaded_list.append({"name": f.name, "content": content})

if uploaded_list:
    st.markdown("### 🗂 Uploaded Files Preview:")
    for f in uploaded_list:
        preview = "\n".join(f["content"].splitlines()[:5])
        if not preview.strip():
            preview = "⚠️ (Empty or whitespace-only file)"
        st.markdown(f"**{f['name']}**")
        st.markdown(f"<pre class='preview'>{preview}</pre>", unsafe_allow_html=True)



st.markdown("💡 Or paste/edit your Python code below:")

initial_editor_value = ""
if uploaded_list and len(uploaded_list) == 1 and uploaded_list[0]["content"].strip():
    initial_editor_value = uploaded_list[0]["content"]

code_input = st_ace(
    value=initial_editor_value,
    language="python",
    theme="chrome",
    font_size=14,
    tab_size=4,
    height=260,
    show_gutter=True,
    wrap=False,
    key="ace_editor",
)

st.markdown("---")


col1, col2 = st.columns([1, 1])
with col1:
    analyze_single = st.button("Analyze Editor / Uploaded Code", use_container_width=True)
with col2:
    analyze_files = st.button("Analyze All Uploaded Files", use_container_width=True)


def render_results(results: dict, title: str = ""):
    if title:
        st.markdown(f"### 📂 Results for: `{title}`")

    static_analysis = results.get("static_analysis", {}) or {}
    if static_analysis:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Static Analysis")
        style_issues = static_analysis.get("style_issues", [])
        complexity = static_analysis.get("complexity", [])

        if style_issues:
            for issue in style_issues:
                st.write(f"**Line {issue.get('line', '?')}** — {issue.get('message', '')}")
        else:
            st.success("No style issues found ✅")

        if complexity:
            for func in complexity:
                st.info(
                    f"Function `{func.get('name', '')}` → Complexity `{func.get('complexity', '')}` (Rank {func.get('rank', '')})"
                )
        st.markdown("</div>", unsafe_allow_html=True)

    security_analysis = results.get("security_analysis", {}) or {}
    if security_analysis:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Security Analysis")
        security_issues = security_analysis.get("security_issues", [])
        if security_issues:
            for issue in security_issues:
                st.error(f"⚠️ Line {issue.get('line', '?')}: {issue.get('message', '')}")
        else:
            st.success("No security issues detected ✅")
        st.markdown("</div>", unsafe_allow_html=True)

    llm_review = results.get("llm_review", {}) or {}
    if llm_review:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("AI Code Review")
        st.markdown(f"**Summary:** {llm_review.get('summary', 'No summary generated.')}")

        comments = llm_review.get("comments", [])
        if comments:
            for comment in comments:
                st.markdown(
                    f"""
                    <div style='padding:0.6rem 1rem; background:#f8f9ff; border-radius:10px; margin:0.4rem 0;'>
                    <b>Line {comment.get('line', '?')}</b>: {comment.get('message', '')}<br>
                    <i>{comment.get('suggestion', '')}</i><br>
                    <b>Severity:</b> {comment.get('severity', 'N/A')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        refactor_plan = llm_review.get("refactor_plan")
        if refactor_plan:
            st.subheader("Refactor Plan")
            st.markdown(f"<p style='color:#444;'>{refactor_plan}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


if analyze_single:
    final_code = (
        code_input.strip()
        if code_input and code_input.strip()
        else (uploaded_list[0]["content"].strip() if uploaded_list else "")
    )

    if not final_code:
        st.warning("⚠️ Please paste or upload some Python code first.")
    else:
        with st.spinner("Analyzing code... 🧠"):
            try:
                resp = requests.post(
                    BACKEND_URL,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"code": final_code}),
                    timeout=120,
                )
                if resp.status_code == 200:
                    results = resp.json()
                    name = uploaded_list[0]["name"] if uploaded_list else "Editor"
                    render_results(results, title=name)
                else:
                    st.error(f"Backend error: {resp.status_code}")
                    st.text(resp.text)
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Connection error: {e}")


if analyze_files:
    if not uploaded_list:
        st.warning("⚠️ No files uploaded to analyze.")
    else:
        # Separate valid and empty files
        valid_files = [f for f in uploaded_list if f["content"].strip()]
        empty_files = [f["name"] for f in uploaded_list if not f["content"].strip()]

        if empty_files:
            st.warning(f"⚠️ Skipping empty files: {', '.join(empty_files)}")

        if not valid_files:
            st.error("🚫 All uploaded files are empty. Please upload valid Python files.")
        else:
            with st.spinner("Analyzing uploaded files... 🧠"):
                for f in valid_files:
                    fname, fcontent = f["name"], f["content"]
                    try:
                        resp = requests.post(
                            BACKEND_URL,
                            headers={"Content-Type": "application/json"},
                            data=json.dumps({"code": fcontent}),
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            results = resp.json()
                            with st.expander(f"🔎 {fname}", expanded=True):
                                render_results(results, title=fname)
                        else:
                            with st.expander(f"❌ {fname} (Error)"):
                                st.error(f"Backend error: {resp.status_code}")
                                st.text(resp.text)
                    except requests.exceptions.RequestException as e:
                        with st.expander(f"❌ {fname} (Connection Error)"):
                            st.error(f"🚨 Connection error: {e}")


st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; font-size:0.85rem; color:#888;'>Built with ❤️ using Streamlit, FastAPI, and Google Gemini</p>",
    unsafe_allow_html=True,
)
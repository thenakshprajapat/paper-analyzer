"""
Simple Streamlit frontend for the Paper Analyzer.
Save as streamlit_app.py and run: streamlit run streamlit_app.py
"""

import os
import re
from collections import Counter
import io

import streamlit as st
import PyPDF2
import pandas as pd
import plotly.express as px

# Optional: import ai_utils if you implemented AI integration
try:
    from ai_utils import classify_questions_llm
    AI_AVAILABLE = True
except Exception:
    classify_questions_llm = None
    AI_AVAILABLE = False

# -- Config / Chapter keywords (same as backend) --
CHAPTER_KEYWORDS = {
    'Mathematics': ['algebra', 'calculus', 'geometry', 'trigonometry', 'statistics', 'probability'],
    'Physics': ['mechanics', 'thermodynamics', 'optics', 'electromagnetism', 'waves', 'quantum'],
    'Chemistry': ['organic', 'inorganic', 'physical chemistry', 'chemical bonding', 'equilibrium'],
    'Biology': ['cell', 'genetics', 'evolution', 'ecology', 'physiology', 'botany', 'zoology'],
    'Computer Science': ['programming', 'algorithms', 'data structures', 'database', 'networks', 'operating system', 'python'],
    'English': ['grammar', 'comprehension', 'literature', 'writing', 'vocabulary'],
    'History': ['ancient', 'medieval', 'modern', 'civilization', 'revolution', 'war'],
    'Geography': ['physical geography', 'human geography', 'climate', 'maps', 'resources']
}

# -- Helpers (same logic as backend) --
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"ERROR: {e}"

def identify_questions(text: str):
    question_patterns = [
        r'Q\s*\d+[\.\):]',
        r'Question\s*\d+[\.\):]',
        r'^\d+[\.\)]',
        r'\n\d+[\.\)]'
    ]
    questions = []
    for pattern in question_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            start = match.start()
            end = min(len(text), start + 400)
            q = text[start:end].strip()
            questions.append(q)
    if questions:
        return questions
    return [line.strip() for line in text.splitlines() if line.strip()]

def analyze_chapters(text: str):
    t = (text or "").lower()
    counts = {}
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        c = 0
        for kw in keywords:
            c += len(re.findall(r'\b' + re.escape(kw.lower()) + r'\b', t))
        if c:
            counts[chapter] = c
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

def extract_topics(text: str, top_n=20):
    stop_words = {'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','as','is','was','are','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','must','can','this','that','these','those','what','which','who','when','where','why','how','question','answer','marks','write','explain'}
    words = re.findall(r'\b[a-z]{3,}\b', (text or "").lower())
    filtered = [w for w in words if w not in stop_words]
    counts = Counter(filtered)
    return dict(counts.most_common(top_n))

# -- Streamlit UI --
st.set_page_config(layout="wide", page_title="Paper Analyzer")

st.title("📄 Paper Analyzer (Streamlit)")
st.markdown("Upload PDF exam papers and get chapter/topic analytics. Optionally enable AI classification if OPENAI_API_KEY is set on the server.")

col1, col2 = st.columns([1, 2])

with col1:
    uploaded_files = st.file_uploader("Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)
    use_ai = st.checkbox("Enable AI classification (uses backend ai_utils)", value=False)
    if use_ai and not AI_AVAILABLE:
        st.warning("AI utilities (ai_utils.py) not found or openai not configured. Falling back to heuristics.")
    st.button("Analyze", key="analyze_button")

with col2:
    st.info("Results will appear here after you click Analyze.")

def run_analysis_on_bytes(file_bytes):
    text = extract_text_from_pdf_bytes(file_bytes)
    if text.startswith("ERROR:"):
        return {"error": text}
    questions = identify_questions(text)
    chapters_heuristic = analyze_chapters(text)
    topics_heuristic = extract_topics(text, top_n=40)

    ai_classifications = None
    chapters_ai = {}
    topics_ai = {}
    if use_ai and AI_AVAILABLE and len(questions):
        # classify with LLM (limit number of questions to avoid cost)
        try:
            # take first 50 for example
            q_batch = questions[:50]
            ai_results = classify_questions_llm(q_batch)
            ai_classifications = ai_results
            # aggregate
            chap_counter = Counter()
            topic_counter = Counter()
            for r in ai_results:
                chap_counter[r.get('chapter', 'Unknown')] += 1
                for t in r.get('topics', []):
                    topic_counter[t.lower()] += 1
            chapters_ai = dict(chap_counter)
            topics_ai = dict(topic_counter.most_common(40))
        except Exception as e:
            st.error(f"AI classification failed: {e}")

    return {
        "text": text,
        "questions": questions,
        "chapters_heuristic": chapters_heuristic,
        "topics_heuristic": topics_heuristic,
        "chapters_ai": chapters_ai,
        "topics_ai": topics_ai,
        "ai_classifications": ai_classifications
    }

if uploaded_files:
    all_results = {}
    for f in uploaded_files:
        with st.spinner(f"Analyzing {f.name}..."):
            bytes_data = f.read()
            res = run_analysis_on_bytes(bytes_data)
            all_results[f.name] = res

    # Display summarized dashboard
    st.header("📊 Summary")

    # Aggregate over files
    agg_chapters = Counter()
    agg_topics = Counter()
    for fname, res in all_results.items():
        if "chapters_ai" in res and res["chapters_ai"]:
            for k, v in res["chapters_ai"].items():
                agg_chapters[k] += v
        else:
            for k, v in res["chapters_heuristic"].items():
                agg_chapters[k] += v
        for k, v in res["topics_heuristic"].items():
            agg_topics[k] += v

    if agg_chapters:
        df_ch = pd.DataFrame({"chapter": list(agg_chapters.keys()), "count": list(agg_chapters.values())})
        fig = px.bar(df_ch.sort_values("count", ascending=False), x="chapter", y="count", title="Chapter Frequency")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No chapter keywords detected across uploads.")

    if agg_topics:
        df_tp = pd.DataFrame({"topic": list(agg_topics.keys()), "count": list(agg_topics.values())})
        df_tp = df_tp.sort_values("count", ascending=False).head(20)
        fig2 = px.bar(df_tp, x="count", y="topic", orientation="h", title="Top Topics")
        st.plotly_chart(fig2, use_container_width=True)

    # Show per-file details (collapsible)
    for fname, res in all_results.items():
        with st.expander(f"{fname} — details"):
            if "error" in res:
                st.error(res["error"])
                continue
            st.subheader("Sample questions")
            for q in res["questions"][:10]:
                st.markdown(f"- {q}")

            st.subheader("Chapters (heuristic)")
            st.json(res["chapters_heuristic"])

            if use_ai and res.get("chapters_ai"):
                st.subheader("Chapters (AI)")
                st.json(res["chapters_ai"])
                st.subheader("AI classifications (sample)")
                st.json(res["ai_classifications"][:10])

            st.subheader("Top heuristic topics")
            st.json(dict(list(res["topics_heuristic"].items())[:30]))
else:
    st.info("Upload one or more PDF files on the left and click Analyze.")
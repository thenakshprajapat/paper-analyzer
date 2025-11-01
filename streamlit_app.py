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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import AI utilities (new version)
try:
    from ai_utils import (
        analyze_chapters_ai,
        extract_topics_ai,
        get_ai_status,
        DEFAULT_PROVIDER
    )
    AI_AVAILABLE = True
except Exception as e:
    AI_AVAILABLE = False
    print(f"AI utilities not available: {e}")

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
    # Comprehensive stopwords list including exam-specific AND generic science words
    stop_words = {
        # Common words
        'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','as','is','was','are','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','must','can','this','that','these','those','what','which','who','when','where','why','how',
        # Exam-specific stopwords
        'question','answer','marks','write','explain','following','given','statement','true','false','correct','incorrect','both','either','neither','none','all','some','any','each','every','only',
        'ncert','assertion','reason','explanation','column','section','choose','select','option','options',
        # Generic science/academic words (too broad)
        'energy','field','water','force','current','pressure','compound','solution','increases','decreases',
        'magnetic','bone','concept','temperature','method','process','system','structure','level','rate',
        'form','type','part','value','change','result','effect','cause','factor','element'
    }
    words = re.findall(r'\b[a-z]{4,}\b', (text or "").lower())  # Min 4 characters
    filtered = [w for w in words if w not in stop_words and len(w) > 4]  # Filter 5+ char words
    counts = Counter(filtered)
    return dict(counts.most_common(top_n))

# -- Streamlit UI --
st.set_page_config(layout="wide", page_title="Paper Analyzer", page_icon="📄")

st.title("📄 Paper Analyzer")
st.markdown("### AI-powered exam paper analysis to help you study smarter!")

# Sidebar for AI status
with st.sidebar:
    st.header("⚙️ AI Status")
    if AI_AVAILABLE:
        ai_status = get_ai_status()
        if ai_status['gemini_available']:
            st.success(f"✅ Google Gemini: Active")
            st.caption(f"Provider: {ai_status['default_provider']}")
        elif ai_status['openai_available']:
            st.success(f"✅ OpenAI: Active")
            st.caption(f"Provider: {ai_status['default_provider']}")
        else:
            st.info("ℹ️ Basic Mode (No AI)")
    else:
        st.warning("⚠️ AI not available - Using keyword matching")
    
    st.divider()
    st.markdown("""
    **Quick Links:**
    - [Get Free Gemini API](https://makersuite.google.com/app/apikey)
    - [GitHub Repository](https://github.com/thenakshprajapat/paper-analyzer)
    """)

col1, col2 = st.columns([1, 2])

with col1:
    uploaded_files = st.file_uploader("📤 Upload PDF exam papers", type=["pdf"], accept_multiple_files=True)
    use_ai = st.checkbox("Enable AI analysis", value=AI_AVAILABLE, disabled=not AI_AVAILABLE,
                        help="AI provides more accurate chapter and topic detection")
    analyze_clicked = st.button("🔍 Analyze Papers", key="analyze_button", type="primary")

with col2:
    if not uploaded_files:
        st.info("👆 Upload one or more PDF files to get started!")
    else:
        st.info(f"📄 {len(uploaded_files)} file(s) ready to analyze")

def run_analysis_on_bytes(file_bytes, use_ai_param):
    text = extract_text_from_pdf_bytes(file_bytes)
    if text.startswith("ERROR:"):
        return {"error": text}
    
    questions = identify_questions(text)
    
    # Use AI analysis if available and enabled
    if use_ai_param and AI_AVAILABLE:
        try:
            # AI-powered analysis
            ai_chapters_result = analyze_chapters_ai(text)
            chapters = ai_chapters_result.get('chapters', {})
            topics = extract_topics_ai(text)
            
            # Supplement with basic if AI didn't find much
            if len(chapters) < 2:
                basic_chapters = analyze_chapters(text)
                for ch, count in basic_chapters.items():
                    if ch not in chapters:
                        chapters[ch] = count
            
            if len(topics) < 5:
                basic_topics = extract_topics(text, top_n=20)
                for topic, count in basic_topics.items():
                    if topic not in topics:
                        topics[topic] = count
            
            analysis_method = f"AI ({DEFAULT_PROVIDER})"
        except Exception as e:
            st.warning(f"AI analysis failed: {e}. Using basic analysis.")
            chapters = analyze_chapters(text)
            topics = extract_topics(text, top_n=40)
            analysis_method = "Basic (Keyword matching)"
    else:
        # Basic keyword analysis
        chapters = analyze_chapters(text)
        topics = extract_topics(text, top_n=40)
        analysis_method = "Basic (Keyword matching)"

    return {
        "text": text,
        "questions": questions,
        "chapters": chapters,
        "topics": topics,
        "analysis_method": analysis_method
    }

if uploaded_files and analyze_clicked:
    all_results = {}
    for f in uploaded_files:
        with st.spinner(f"🔄 Analyzing {f.name}..."):
            bytes_data = f.read()
            res = run_analysis_on_bytes(bytes_data, use_ai)
            all_results[f.name] = res

    st.success(f"✅ Analysis complete!")
    
    # Display summarized dashboard
    st.header("📊 Analysis Results")

    # Aggregate over files
    agg_chapters = Counter()
    agg_topics = Counter()
    analysis_methods = []
    
    for fname, res in all_results.items():
        if "error" in res:
            st.error(f"Error in {fname}: {res['error']}")
            continue
        
        analysis_methods.append(res.get("analysis_method", "Unknown"))
        for k, v in res.get("chapters", {}).items():
            agg_chapters[k] += v
        for k, v in res.get("topics", {}).items():
            agg_topics[k] += v

    # Show analysis method
    if analysis_methods:
        unique_methods = set(analysis_methods)
        st.info(f"📊 Analysis Method: {', '.join(unique_methods)}")

    col1, col2 = st.columns(2)

    with col1:
        if agg_chapters:
            df_ch = pd.DataFrame({
                "Chapter": list(agg_chapters.keys()),
                "Score": list(agg_chapters.values())
            })
            df_ch = df_ch.sort_values("Score", ascending=False)
            fig = px.bar(df_ch, x="Chapter", y="Score", 
                        title="📚 Chapter Distribution",
                        color="Score",
                        color_continuous_scale="Purples")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No chapters identified")

    with col2:
        if agg_topics:
            df_tp = pd.DataFrame({
                "Topic": list(agg_topics.keys()),
                "Score": list(agg_topics.values())
            })
            df_tp = df_tp.sort_values("Score", ascending=False).head(15)
            fig2 = px.bar(df_tp, x="Score", y="Topic", orientation="h",
                         title="🎯 Top 15 Topics",
                         color="Score",
                         color_continuous_scale="Blues")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No topics identified")
    
    st.divider()

    # Show per-file details
    st.subheader("📄 Individual File Details")
    for fname, res in all_results.items():
        with st.expander(f"📋 {fname}"):
            if "error" in res:
                st.error(res["error"])
                continue
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Questions Found", len(res.get("questions", [])))
            col2.metric("Chapters", len(res.get("chapters", {})))
            col3.metric("Topics", len(res.get("topics", {})))
            
            if res.get("chapters"):
                st.markdown("**Chapters:**")
                for ch, score in list(res["chapters"].items())[:5]:
                    st.write(f"- {ch}: {score:.2f}")
            
            if res.get("topics"):
                st.markdown("**Top Topics:**")
                topics_str = ", ".join([f"{t} ({s:.1f})" for t, s in list(res["topics"].items())[:10]])
                st.write(topics_str)
            
            if res.get("questions"):
                st.markdown("**Sample Questions:**")
                for i, q in enumerate(res["questions"][:3], 1):
                    st.caption(f"{i}. {q[:200]}...")
else:
    # Welcome screen
    st.markdown("""
    ### 🎯 How it works:
    1. 📤 Upload your exam papers (PDF format)
    2. 🤖 AI analyzes chapters, topics, and questions
    3. 📊 View beautiful interactive charts
    4. 📚 Get study recommendations
    
    ### ✨ Features:
    - ✅ **AI-powered analysis** with Google Gemini
    - ✅ **Interactive charts** with Plotly
    - ✅ **Batch processing** - upload multiple papers
    - ✅ **Smart topic extraction** - context-aware
    - ✅ **Free to use** - Gemini free tier included
    
    ### 📝 Tips:
    - Use complete exam papers for best results
    - PDFs must have extractable text (not scanned images)
    - Enable AI mode in sidebar for accurate analysis
    """)

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

# Import enhanced PDF extraction with OCR
try:
    from pdf_extractor import extract_text_with_ocr, is_ocr_available
    PDF_OCR_AVAILABLE = True
except ImportError:
    PDF_OCR_AVAILABLE = False
    print("OCR-enhanced PDF extraction not available")

# -- Config / Chapter keywords (same as backend) --
CHAPTER_KEYWORDS = {
    'Mathematics': [
        'algebra', 'calculus', 'geometry', 'trigonometry', 'statistics', 'probability', 
        'integration', 'differentiation', 'vector', 'matrix', 'equation', 'derivative'
    ],
    'Physics': [
        'mechanics', 'thermodynamics', 'optics', 'electromagnetism', 'waves', 'quantum',
        'motion', 'velocity', 'acceleration', 'momentum', 'force', 'friction',
        'circuit', 'resistance', 'capacitor', 'voltage', 'current', 'magnetic'
    ],
    'Chemistry': [
        'organic', 'inorganic', 'equilibrium', 'acid', 'base', 'reaction', 'molecule', 'atom',
        'catalyst', 'oxidation', 'reduction', 'titration', 'solution', 'compound',
        'element', 'periodic', 'ionic', 'covalent', 'synthesis', 'chemical'
    ],
    'Biology': [
        'cell', 'genetics', 'evolution', 'ecology', 'physiology', 'anatomy', 'tissue', 'organ',
        'kidney', 'excretion', 'skeletal', 'muscle', 'respiration', 'photosynthesis',
        'enzyme', 'protein', 'dna', 'chromosome', 'mitosis', 'reproduction'
    ],
    'Computer Science': ['programming', 'algorithms', 'data structures', 'database', 'networks', 'operating system', 'python'],
    'English': ['grammar', 'comprehension', 'literature', 'writing', 'vocabulary'],
    'History': ['ancient', 'medieval', 'modern', 'civilization', 'revolution', 'war'],
    'Geography': ['physical geography', 'human geography', 'climate', 'maps', 'resources']
}

# -- Helpers (same logic as backend) --
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF with OCR support for image-heavy papers."""
    try:
        # Use enhanced OCR extraction if available
        if PDF_OCR_AVAILABLE:
            text = extract_text_with_ocr(file_bytes, use_ocr=True)
            if text and len(text.strip()) > 100:
                return text
        
        # Fallback to simple PyPDF2 extraction
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
    """Analyze chapters with normalized scoring to handle different keyword list sizes"""
    t = (text or "").lower()
    counts = {}
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        c = 0
        for kw in keywords:
            c += len(re.findall(r'\b' + re.escape(kw.lower()) + r'\b', t))
        if c:
            # Normalize by number of keywords to prevent bias
            normalized_score = c * (20 / len(keywords))  # Normalize to 20 keywords baseline
            counts[chapter] = round(normalized_score, 1)
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

def extract_topics(text: str, top_n=20):
    """Extract meaningful topics using pattern matching for scientific terms"""
    
    # Extract capitalized terms (proper nouns, scientific names)
    capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b', text or "")
    
    # Extract hyphenated scientific terms
    hyphenated = re.findall(r'\b([a-z]+(?:-[a-z]+)+)\b', (text or "").lower())
    
    # Extract specific scientific patterns
    scientific_patterns = [
        r'\b(\w*magnetic\w*)\b',
        r'\b(\w*electric\w*)\b', 
        r'\b(\w*thermal\w*)\b',
        r'\b(\w*mechanical\w*)\b',
        r'\b(\w*chemical\w*)\b',
        r'\b(\w*biological\w*)\b',
        r'\b(\w*synthesis\w*)\b',
        r'\b(\w*metabolism\w*)\b',
        r'\b(\w*equilibrium\w*)\b',
        r'\b(\w*induction\w*)\b',
        r'\b(\w*oscillation\w*)\b',
        r'\b(\w*excretion\w*)\b',
        r'\b(\w*skeletal\w*)\b',
        r'\b(\w*muscular\w*)\b',
        r'\b(\w*circulation\w*)\b',
        r'\b(\w*respiration\w*)\b',
        r'\b(\w*photosynthesis\w*)\b',
    ]
    
    scientific_words = []
    for pattern in scientific_patterns:
        matches = re.findall(pattern, (text or "").lower(), re.IGNORECASE)
        scientific_words.extend(matches)
    
    # Combine all
    all_terms = (
        [t.strip() for t in capitalized_terms if len(t) > 8] +  # Long proper nouns
        [h for h in hyphenated if len(h) > 6] +  # Hyphenated terms
        [s for s in scientific_words if len(s) > 5]  # Scientific terms
    )
    
    # Count and return
    counts = Counter([t.lower() for t in all_terms if t])
    return dict(counts.most_common(top_n))

# -- Streamlit UI --
st.set_page_config(layout="wide", page_title="Paper Analyzer", page_icon="📄")

st.title("📄 Paper Analyzer")
st.markdown("### AI-powered exam paper analysis to help you study smarter!")

# Show OCR status banner
if PDF_OCR_AVAILABLE and is_ocr_available():
    st.success("🔍 **OCR Enabled**: Can extract text from image-heavy PDFs (Physics diagrams, charts, etc.)")
else:
    st.info("📝 **OCR Disabled**: Install OCR support for better Physics/image paper extraction - See instructions below")
    with st.expander("📦 How to enable OCR support"):
        st.code("""
# Install OCR dependencies:
pip install pdf2image pytesseract pillow

# Also install Tesseract OCR engine:
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
        """, language="bash")

# Sidebar for AI status
with st.sidebar:
    st.header("⚙️ AI Status")
    if AI_AVAILABLE:
        ai_status = get_ai_status()
        if ai_status['groq_available']:
            st.success(f"✅ Groq AI: Active (FREE & FAST!)")
            st.caption(f"Model: Llama 3.3 70B")
        elif ai_status['gemini_available']:
            st.warning(f"⚠️ Gemini Active (may block content)")
            st.caption("Consider switching to Groq")
        elif ai_status['openai_available']:
            st.success(f"✅ OpenAI: Active")
            st.caption(f"Provider: {ai_status['default_provider']}")
        else:
            st.info("ℹ️ Pattern-Based Mode (No AI)")
    else:
        st.warning("⚠️ AI not available - Using pattern matching")
    
    st.divider()
    st.markdown("""
    **Setup AI (FREE):**
    - [Get Groq API](https://console.groq.com/keys) ⭐ **RECOMMENDED**
    - [Get Gemini API](https://makersuite.google.com/app/apikey) (may block)
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
            
            # Normalize scores to percentages for better visualization
            total_score = df_ch["Score"].sum()
            if total_score > 0:
                df_ch["Percentage"] = (df_ch["Score"] / total_score * 100).round(1)
                df_ch = df_ch.sort_values("Percentage", ascending=False)
            else:
                df_ch["Percentage"] = 0
                df_ch = df_ch.sort_values("Score", ascending=False)
            
            # Use discrete colors for chapters
            fig = px.bar(df_ch, x="Chapter", y="Percentage", 
                        title="📚 Chapter Distribution",
                        color="Chapter",
                        color_discrete_sequence=px.colors.qualitative.Bold,
                        labels={"Percentage": "Coverage (%)"})
            fig.update_layout(showlegend=False)  # Hide legend since x-axis shows names
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("No chapters identified")

    with col2:
        if agg_topics:
            df_tp = pd.DataFrame({
                "Topic": list(agg_topics.keys()),
                "Score": list(agg_topics.values())
            })
            df_tp = df_tp.sort_values("Score", ascending=False).head(15)
            
            # Normalize to show relative importance
            max_score = df_tp["Score"].max()
            if max_score > 0:
                df_tp["Relevance"] = (df_tp["Score"] / max_score).round(3)
            else:
                df_tp["Relevance"] = 0
            
            # Use gradient colors for topics (keeps the nice gradient effect)
            fig2 = px.bar(df_tp, x="Relevance", y="Topic", orientation="h",
                         title="🎯 Top 15 Topics",
                         color="Relevance",
                         color_continuous_scale="teal",
                         labels={"Relevance": "Relevance Score"})
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})  # Order by score
            st.plotly_chart(fig2, width='stretch')
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

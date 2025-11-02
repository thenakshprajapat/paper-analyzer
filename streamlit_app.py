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
st.set_page_config(
    layout="wide", 
    page_title="📚 Study Smarter with Paper Analyzer", 
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# Hero Section
st.markdown("""
    <style>
    .big-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        margin-top: 0;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
    }
    </style>
    <h1 class="big-title">🎓 Paper Analyzer</h1>
    <p class="subtitle">Ace your exams by understanding what topics to focus on!</p>
""", unsafe_allow_html=True)

# Features highlight
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("### 🤖 AI-Powered")
    st.caption("Smart analysis of your exam papers")
with col_b:
    st.markdown("### 📊 Visual Insights")
    st.caption("See what topics appear most")
with col_c:
    st.markdown("### ⚡ Lightning Fast")
    st.caption("Results in seconds!")

st.divider()

# Show OCR status banner (friendlier)
if PDF_OCR_AVAILABLE and is_ocr_available():
    st.success("✨ **Image Recognition Enabled** - Can read text from diagrams and images!")
else:
    with st.expander("💡 Want to analyze papers with diagrams? Enable OCR!"):
        st.markdown("""
        OCR lets the analyzer read text from images, perfect for Physics papers with circuits and diagrams!
        
        **Quick Setup:**
        ```bash
        pip install pdf2image pytesseract pillow
        ```
        Then install Tesseract: [Download here](https://github.com/UB-Mannheim/tesseract/wiki)
        """)

# Sidebar for AI status (more friendly)
with st.sidebar:
    st.markdown("### 🚀 AI Status")
    if AI_AVAILABLE:
        ai_status = get_ai_status()
        if ai_status['groq_available']:
            st.success("🎉 **Groq AI Active!**")
            st.caption("✨ Using Llama 3.3 70B - Lightning fast & accurate!")
        elif ai_status['gemini_available']:
            st.warning("⚠️ **Gemini Active**")
            st.caption("May have issues with some content. Try Groq instead!")
        elif ai_status['openai_available']:
            st.success("✅ **OpenAI Active**")
            st.caption(f"Using: {ai_status['default_provider']}")
        else:
            st.info("📝 **Pattern Mode**")
            st.caption("Basic analysis - add AI for better results!")
    else:
        st.info("💡 **No AI Connected**")
        st.caption("Using pattern matching")
    
    st.divider()
    st.markdown("""
    ### 🎁 Get Free AI
    
    **Recommended:**  
    🌟 [Groq](https://console.groq.com/keys) - FREE & Fast!
    
    **Alternatives:**  
    📘 [Gemini](https://makersuite.google.com/app/apikey) - May block content
    
    ---
    
    💻 [View on GitHub](https://github.com/thenakshprajapat/paper-analyzer)
    """)

# Main upload section
st.markdown("### 📤 Upload Your Exam Papers")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Drop your PDF files here or click to browse", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Upload one or more exam papers (max 200MB each)"
    )
    
with col2:
    if not uploaded_files:
        st.info("👈 **Start by uploading your exam papers!**\n\nSupports: Sample papers, previous years, practice tests")
    else:
        st.success(f"✅ **{len(uploaded_files)} paper(s) uploaded!**")
        for f in uploaded_files:
            st.caption(f"� {f.name}")

use_ai = st.checkbox(
    "🤖 Use AI for better accuracy", 
    value=AI_AVAILABLE, 
    disabled=not AI_AVAILABLE,
    help="AI detects topics more accurately than keyword matching"
)

analyze_clicked = st.button("🚀 Analyze My Papers!", type="primary", use_container_width=True)

def run_analysis_on_bytes(file_bytes, use_ai_param):
    text = extract_text_from_pdf_bytes(file_bytes)
    if text.startswith("ERROR:"):
        return {"error": text}
    
    questions = identify_questions(text)
    
    # Use AI analysis if available and enabled
    if use_ai_param and AI_AVAILABLE:
        try:
            # PURE AI-powered analysis - NO KEYWORD MIXING!
            ai_chapters_result = analyze_chapters_ai(text)
            chapters = ai_chapters_result.get('chapters', {})
            topics = extract_topics_ai(text)
            
            # If AI truly returns empty, fall back gracefully
            if not chapters:
                st.warning("⚠️ AI returned no chapters - using pattern-based fallback")
                chapters = analyze_chapters(text)
            if not topics:
                st.warning("⚠️ AI returned no topics - using pattern-based fallback")
                topics = extract_topics(text, top_n=20)
            
            analysis_method = f"AI ({DEFAULT_PROVIDER})"
        except Exception as e:
            st.error(f"❌ AI analysis failed: {e}")
            # Fall back to pattern-based on error
            chapters = analyze_chapters(text)
            topics = extract_topics(text, top_n=20)
            analysis_method = f"Pattern-based (AI error)"
    else:
        # Pattern-based analysis when AI not available/enabled
        chapters = analyze_chapters(text)
        topics = extract_topics(text, top_n=20)
        analysis_method = "Pattern-based"

    return {
        "text": text,
        "questions": questions,
        "chapters": chapters,
        "topics": topics,
        "analysis_method": analysis_method
    }

if uploaded_files and analyze_clicked:
    all_results = {}
    
    # Show friendly progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, f in enumerate(uploaded_files):
        status_text.markdown(f"� **Analyzing:** {f.name}...")
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
        bytes_data = f.read()
        res = run_analysis_on_bytes(bytes_data, use_ai)
        all_results[f.name] = res

    status_text.empty()
    progress_bar.empty()
    st.balloons()  # Celebrate!
    st.success(f"🎉 **Analysis Complete!** Found insights from {len(uploaded_files)} paper(s)")
    
    # Display summarized dashboard with student-friendly language
    st.markdown("---")
    st.markdown("## � Your Study Guide")
    st.caption("Here's what topics you should focus on based on your papers")

    # Aggregate over files
    agg_chapters = Counter()
    agg_topics = Counter()
    analysis_methods = []
    
    for fname, res in all_results.items():
        if "error" in res:
            st.error(f"❌ Couldn't read {fname}: {res['error']}")
            continue
        
        analysis_methods.append(res.get("analysis_method", "Unknown"))
        for k, v in res.get("chapters", {}).items():
            agg_chapters[k] += v
        for k, v in res.get("topics", {}).items():
            agg_topics[k] += v

    # Show analysis method (friendly)
    if analysis_methods:
        unique_methods = set(analysis_methods)
        method_text = "🤖 AI-powered" if "AI" in str(unique_methods) else "📝 Pattern-based"
        st.info(f"**Analysis Type:** {method_text}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📖 Subject Breakdown")
        st.caption("Which subjects appear in your papers")
        
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
            
            # Use discrete colors for chapters (more vibrant)
            fig = px.bar(df_ch, x="Chapter", y="Percentage", 
                        color="Chapter",
                        color_discrete_sequence=px.colors.qualitative.Vivid,
                        labels={"Percentage": "Coverage (%)"})
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14)
            )
            fig.update_traces(
                texttemplate='%{y:.1f}%', 
                textposition='outside',
                textfont_size=14,
                marker_line_color='white',
                marker_line_width=2
            )
            st.plotly_chart(fig, width='stretch')
            
            # Add friendly message
            top_subject = df_ch.iloc[0]["Chapter"]
            st.success(f"💡 **Main Focus:** {top_subject} covers {df_ch.iloc[0]['Percentage']:.1f}% of your papers!")
        else:
            st.warning("😕 Couldn't identify subjects - try uploading a different paper")

    with col2:
        st.markdown("### 🎯 Key Topics to Study")
        st.caption("Most important topics ranked by frequency")
        
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
            
            # Use gradient colors for topics (purple gradient for modern look)
            fig2 = px.bar(df_tp, x="Relevance", y="Topic", orientation="h",
                         color="Relevance",
                         color_continuous_scale="purples",
                         labels={"Relevance": "Importance"})
            fig2.update_layout(
                yaxis={'categoryorder':'total ascending'},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=13),
                showlegend=False
            )
            fig2.update_traces(
                marker_line_color='white',
                marker_line_width=1.5
            )
            st.plotly_chart(fig2, width='stretch')
            
            # Study tip
            top_3 = df_tp.head(3)["Topic"].tolist()
            st.info(f"📝 **Study Priority:** Focus on {', '.join(top_3[:2])} first!")
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

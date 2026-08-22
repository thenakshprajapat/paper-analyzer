"""
Modern Streamlit frontend for the Paper Analyzer.
Run: streamlit run streamlit_app.py
"""

import os
import re
from collections import Counter
import io

import streamlit as st
import pandas as pd
import plotly.express as px

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import PyPDF2 safely
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    try:
        import pypdf as PyPDF2
        PYPDF2_AVAILABLE = True
    except ImportError:
        PyPDF2 = None
        PYPDF2_AVAILABLE = False

# Import AI utilities
try:
    from ai_utils import (
        analyze_chapters_ai,
        extract_topics_ai,
        craft_high_probability_questions,
        get_ai_status,
        DEFAULT_PROVIDER
    )
    AI_AVAILABLE = True
except Exception as e:
    AI_AVAILABLE = False
    print(f"AI utilities not available: {e}")

# Import enhanced PDF extraction with OCR
try:
    from pdf_extractor import extract_text_with_ocr, is_ocr_available, extract_structured_questions
    PDF_OCR_AVAILABLE = True
except ImportError:
    PDF_OCR_AVAILABLE = False
    print("OCR-enhanced PDF extraction not available")

# -- Config / Chapter keywords --
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
    'Computer Science': ['programming', 'algorithms', 'data structures', 'database', 'networks', 'operating system', 'python', 'sql'],
    'English': ['grammar', 'comprehension', 'literature', 'writing', 'vocabulary'],
    'History': ['ancient', 'medieval', 'modern', 'civilization', 'revolution', 'war'],
    'Geography': ['physical geography', 'human geography', 'climate', 'maps', 'resources']
}

# -- Helpers --
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF with OCR support for image-heavy papers."""
    try:
        if PDF_OCR_AVAILABLE:
            text = extract_text_with_ocr(file_bytes, use_ocr=True)
            if text and len(text.strip()) > 100:
                return text
        
        if PYPDF2_AVAILABLE and PyPDF2 is not None:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        return ""
    except Exception as e:
        return f"ERROR: {e}"

def identify_questions(text: str):
    if PDF_OCR_AVAILABLE:
        structured = extract_structured_questions(text)
        if structured:
            return [q["text"] for q in structured]
            
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
    return [line.strip() for line in text.splitlines() if len(line.strip()) > 20]

def analyze_chapters(text: str):
    """Analyze chapters with normalized scoring to handle different keyword list sizes"""
    t = (text or "").lower()
    counts = {}
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        c = 0
        for kw in keywords:
            c += len(re.findall(r'\b' + re.escape(kw.lower()) + r'\b', t))
        if c:
            normalized_score = c * (20 / len(keywords))
            counts[chapter] = round(normalized_score, 1)
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

def extract_topics(text: str, top_n=20):
    """Extract meaningful topics using pattern matching for scientific & technical terms"""
    capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b', text or "")
    hyphenated = re.findall(r'\b([a-z]+(?:-[a-z]+)+)\b', (text or "").lower())
    
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
        r'\b(\w*algorithm\w*)\b',
        r'\b(\w*database\w*)\b',
        r'\b(\w*structure\w*)\b'
    ]
    
    scientific_words = []
    for pattern in scientific_patterns:
        matches = re.findall(pattern, (text or "").lower(), re.IGNORECASE)
        scientific_words.extend(matches)
    
    all_terms = (
        [t.strip() for t in capitalized_terms if len(t) > 6] +
        [h for h in hyphenated if len(h) > 5] +
        [s for s in scientific_words if len(s) > 5]
    )
    
    counts = Counter([t.title() if len(t.split()) > 1 else t.lower() for t in all_terms if t])
    return dict(counts.most_common(top_n))

def generate_markdown_study_paper(primary_subject, predicted_data, chapters, topics):
    """Generate clean downloadable Markdown study paper."""
    questions = predicted_data.get("questions", [])
    total_marks = predicted_data.get("total_predicted_marks", 0)
    avg_prob = predicted_data.get("average_probability", 0)
    
    md = []
    md.append(f"# 🎯 HIGH-PROBABILITY PREDICTED EXAM PAPER & STUDY GUIDE")
    md.append(f"**Subject Focus:** {primary_subject} | **Total Marks:** {total_marks} | **Confidence Forecast:** {avg_prob}%\n")
    md.append(f"> Generated automatically by Paper Analyzer based on frequency analysis and curriculum topic weighting.\n")
    md.append(f"---\n")
    
    md.append(f"## 📋 PART I: PREDICTED HIGH-YIELD QUESTIONS\n")
    for q in questions:
        md.append(f"### {q.get('id', 'Q')} [{q.get('estimated_marks', 5)} Marks] — Probability: {q.get('probability_score', 85)}% ({q.get('probability_tier', 'High')})")
        md.append(f"**Topic:** {q.get('topic', 'Core')} | **Chapter:** {q.get('chapter', 'Unit')} | **Type:** {q.get('type', 'General')}")
        md.append(f"\n**Question:**")
        md.append(f"> {q.get('question', '')}\n")
        md.append(f"**🎯 Exam Rationale:** {q.get('why_high_probability', '')}\n")
        
        md.append(f"**🔑 Key Scoring Points:**")
        for pt in q.get('key_scoring_points', []):
            md.append(f"- {pt}")
        md.append(f"\n**💡 Step-by-Step Model Answer / Hint:**")
        md.append(f"{q.get('model_answer_or_hint', '')}\n")
        md.append(f"---\n")
        
    md.append(f"## 📊 PART II: SYLLABUS DISTRIBUTION & PRIORITY TOPICS\n")
    md.append(f"### Top Chapters Covered:")
    for ch, sc in list(chapters.items())[:5]:
        md.append(f"- **{ch}**: Weight score {sc:.1f}")
        
    md.append(f"\n### Top Key Topics to Master:")
    for tp, sc in list(topics.items())[:10]:
        val = f"{sc:.2f}" if isinstance(sc, float) else f"{sc}"
        md.append(f"- **{tp}** (Score: {val})")
        
    return "\n".join(md)

# -- Streamlit UI Setup --
st.set_page_config(
    layout="wide", 
    page_title="🎓 Paper Analyzer - Predicted Questions & Exam Forecaster", 
    page_icon="📚",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .question-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .prob-badge-very-high {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .prob-badge-high {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .prob-badge-mod {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .meta-tag {
        background: #f3f4f6;
        color: #374151;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        display: inline-block;
    }
    </style>
    <h1 class="big-title">🎓 Paper Analyzer & Exam Forecaster</h1>
    <p class="subtitle">Upload exam papers to uncover recurring patterns and craft highest-probability predicted questions!</p>
""", unsafe_allow_html=True)

# Features highlight
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("### 🎯 Highest-Probability Questions")
    st.caption("AI-crafted high-yield questions with model answers")
with col_b:
    st.markdown("### 📊 Syllabus & Topic Weights")
    st.caption("Detailed visual breakdown of chapters & concepts")
with col_c:
    st.markdown("### 📥 Instant Study Pack Export")
    st.caption("Download formatted test papers with scoring rubrics")

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### 🚀 Engine Status")
    if AI_AVAILABLE:
        ai_status = get_ai_status()
        if ai_status['groq_available']:
            st.success("🎉 **Groq AI Active!**")
            st.caption("✨ Using Llama 3.3 70B - Ultra fast & accurate")
        elif ai_status['gemini_available']:
            st.success("✅ **Google Gemini Active**")
            st.caption("Using Gemini 2.5 Flash")
        elif ai_status['openai_available']:
            st.success("✅ **OpenAI Active**")
            st.caption(f"Using {ai_status['default_provider']}")
        else:
            st.info("📝 **Intelligent Heuristic Mode**")
            st.caption("Using smart curriculum synthesis templates")
    else:
        st.info("💡 **Pattern Mode**")
        st.caption("Smart pattern & heuristic synthesizer")
    
    st.divider()
    st.markdown("""
    ### 🔑 AI API Keys (Optional)
    Add free keys in `.env` to enable live LLM synthesis:
    - 🌟 **[Groq (Recommended)](https://console.groq.com/keys)** - Fast & Free!
    - 📘 **[Google Gemini](https://makersuite.google.com/app/apikey)**
    - 🟢 **[OpenAI](https://platform.openai.com/api-keys)**
    
    ---
    💻 [GitHub Repository](https://github.com/thenakshprajapat/paper-analyzer)
    """)

# Upload Section
st.markdown("### 📤 Upload Exam Papers")
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Drop your PDF files here or click to browse", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Upload one or more past papers, sample papers, or unit tests"
    )
    
with col2:
    if not uploaded_files:
        st.info("👈 **Upload one or more exam papers to begin.**\n\nThe engine will identify question structures, compute recurring topic weights, and synthesize top predicted questions.")
    else:
        st.success(f"✅ **{len(uploaded_files)} paper(s) ready for analysis!**")
        for f in uploaded_files:
            st.caption(f"📄 {f.name}")

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    use_ai = st.checkbox(
        "🤖 Enable AI Deep Synthesis", 
        value=AI_AVAILABLE, 
        disabled=not AI_AVAILABLE,
        help="Synthesizes realistic exam questions with probability scoring"
    )
with col_opt2:
    num_pred_questions = st.slider("Number of Predicted Questions to Craft", min_value=4, max_value=12, value=8)

analyze_clicked = st.button("🚀 Analyze Papers & Forecast Questions!", type="primary", use_container_width=True)

def run_analysis_on_bytes(file_bytes, use_ai_param):
    text = extract_text_from_pdf_bytes(file_bytes)
    if text.startswith("ERROR:"):
        return {"error": text}
    
    questions = identify_questions(text)
    primary_subject = "General"
    
    if use_ai_param and AI_AVAILABLE:
        try:
            ai_chapters_result = analyze_chapters_ai(text)
            chapters = ai_chapters_result.get('chapters', {})
            primary_subject = ai_chapters_result.get('primary_subject', 'General')
            topics = extract_topics_ai(text)
            
            if not chapters:
                chapters = analyze_chapters(text)
            if not topics:
                topics = extract_topics(text, top_n=20)
            analysis_method = f"AI ({DEFAULT_PROVIDER})"
        except Exception as e:
            chapters = analyze_chapters(text)
            topics = extract_topics(text, top_n=20)
            analysis_method = "Pattern-based (Fallback)"
    else:
        chapters = analyze_chapters(text)
        topics = extract_topics(text, top_n=20)
        analysis_method = "Heuristic Pattern-based"

    if chapters and primary_subject == "General":
        primary_subject = list(chapters.keys())[0]

    return {
        "text": text,
        "questions": questions,
        "chapters": chapters,
        "topics": topics,
        "primary_subject": primary_subject,
        "analysis_method": analysis_method
    }

if uploaded_files and analyze_clicked:
    all_results = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_text = ""
    agg_chapters = Counter()
    agg_topics = Counter()
    agg_questions = []
    
    for idx, f in enumerate(uploaded_files):
        status_text.markdown(f"⏳ **Analyzing paper {idx+1}/{len(uploaded_files)}:** {f.name}...")
        progress_bar.progress((idx + 0.5) / len(uploaded_files))
        
        bytes_data = f.read()
        res = run_analysis_on_bytes(bytes_data, use_ai)
        all_results[f.name] = res
        
        if "error" not in res:
            all_text += "\n\n" + res.get("text", "")
            for k, v in res.get("chapters", {}).items():
                agg_chapters[k] += v
            for k, v in res.get("topics", {}).items():
                agg_topics[k] += v
            agg_questions.extend(res.get("questions", []))
            
    progress_bar.progress(0.9)
    status_text.markdown("🎯 **Crafting High-Probability Exam Questions & Model Solutions...**")
    
    primary_subject = list(agg_chapters.keys())[0] if agg_chapters else "General Science"
    
    # Craft High Probability Predicted Questions
    predicted_data = craft_high_probability_questions(
        text=all_text,
        chapters=dict(agg_chapters),
        topics=dict(agg_topics),
        sample_questions=agg_questions[:8],
        primary_subject=primary_subject,
        num_questions=num_pred_questions
    )
    
    progress_bar.progress(1.0)
    status_text.empty()
    progress_bar.empty()
    st.balloons()
    st.success(f"🎉 **Analysis & Question Forecasting Complete!** Evaluated {len(uploaded_files)} paper(s).")
    
    # === HIGH-PROBABILITY QUESTIONS SECTION ===
    st.markdown("---")
    st.markdown(f"## 🎯 Crafted High-Probability Exam Questions")
    st.caption("Synthesized based on recurring topic frequency, syllabus weightage, and standard exam patterns.")
    
    pred_questions = predicted_data.get("questions", [])
    
    # Stat Metrics Row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Questions Crafted", len(pred_questions))
    with mcol2:
        st.metric("Avg Predicted Probability", f"{predicted_data.get('average_probability', 90)}%")
    with mcol3:
        st.metric("Total Marks Forecast", f"{predicted_data.get('total_predicted_marks', 40)} M")
    with mcol4:
        st.metric("Main Subject Focus", primary_subject)

    # Download Button
    study_paper_md = generate_markdown_study_paper(primary_subject, predicted_data, dict(agg_chapters), dict(agg_topics))
    st.download_button(
        label="📥 Download Predicted Question Paper & Solutions (.md)",
        data=study_paper_md,
        file_name=f"Predicted_Exam_Questions_{primary_subject.replace(' ', '_')}.md",
        mime="text/markdown",
        help="Download formatted questions with mark distributions, examiner rubrics, and step-by-step solutions"
    )

    # Filters
    st.markdown("##### 🔍 Filter Forecasted Questions:")
    fcol1, fcol2, fcol3 = st.columns(3)
    
    available_chapters = ["All"] + sorted(list({q.get("chapter", "General") for q in pred_questions}))
    available_types = ["All"] + sorted(list({q.get("type", "General") for q in pred_questions}))
    available_tiers = ["All", "Very High (90%+)", "High (80-89%)", "Moderate (<80%)"]
    
    with fcol1:
        sel_chapter = st.selectbox("By Chapter/Unit", available_chapters)
    with fcol2:
        sel_type = st.selectbox("By Question Type", available_types)
    with fcol3:
        sel_tier = st.selectbox("By Probability Tier", available_tiers)

    # Filter question list
    filtered_qs = []
    for q in pred_questions:
        if sel_chapter != "All" and q.get("chapter") != sel_chapter:
            continue
        if sel_type != "All" and q.get("type") != sel_type:
            continue
        if sel_tier != "All":
            prob = q.get("probability_score", 85)
            if "Very High" in sel_tier and prob < 90:
                continue
            if "High (80" in sel_tier and (prob < 80 or prob >= 90):
                continue
            if "Moderate" in sel_tier and prob >= 80:
                continue
        filtered_qs.append(q)

    # Render Cards
    if not filtered_qs:
        st.info("No questions match the selected filters. Try choosing 'All'.")
    else:
        for q in filtered_qs:
            prob = q.get("probability_score", 85)
            badge_class = "prob-badge-very-high" if prob >= 90 else "prob-badge-high" if prob >= 80 else "prob-badge-mod"
            
            with st.container():
                st.markdown(f"""
                <div class="question-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
                        <div>
                            <span class="{badge_class}">🔥 {prob}% Probability ({q.get('probability_tier', 'High')})</span>
                            <span class="meta-tag">🏷️ {q.get('estimated_marks', 5)} Marks</span>
                            <span class="meta-tag">📐 {q.get('type', 'General')}</span>
                            <span class="meta-tag">⚡ Difficulty: {q.get('difficulty', 'Medium')}</span>
                        </div>
                        <div>
                            <span class="meta-tag" style="background:#e0e7ff; color:#3730a3;">📚 {q.get('chapter', 'Unit')}</span>
                            <span class="meta-tag" style="background:#fce7f3; color:#9d174d;">🎯 {q.get('topic', 'Core Concept')}</span>
                        </div>
                    </div>
                    <div style="font-size: 1.15rem; font-weight: 600; color: #111827; margin: 12px 0; line-height: 1.5;">
                        {q.get('id', 'Q')}. {q.get('question', '')}
                    </div>
                    <div style="background:#f9fafb; padding:10px 14px; border-left:4px solid #6366f1; border-radius:4px; font-size:0.92rem; color:#4b5563; margin-bottom:12px;">
                        <strong>💡 Why High Probability:</strong> {q.get('why_high_probability', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📖 View Model Answer & Scoring Rubric for {q.get('id', 'Q')}"):
                    st.markdown("**🔑 Examiner's Scoring Points:**")
                    for pt in q.get('key_scoring_points', []):
                        st.markdown(f"- {pt}")
                    st.markdown("**💡 Step-by-Step Model Solution / Hint:**")
                    st.info(q.get('model_answer_or_hint', ''))

    # === VISUAL CHARTS SECTION ===
    st.markdown("---")
    st.markdown("## 📊 Syllabus Coverage & Topic Rankings")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("### 📖 Subject & Chapter Breakdown")
        if agg_chapters:
            df_ch = pd.DataFrame({
                "Chapter": list(agg_chapters.keys()),
                "Score": list(agg_chapters.values())
            })
            total_score = df_ch["Score"].sum()
            if total_score > 0:
                df_ch["Percentage"] = (df_ch["Score"] / total_score * 100).round(1)
                df_ch = df_ch.sort_values("Percentage", ascending=False)
            else:
                df_ch["Percentage"] = 0
            
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
                marker_line_color='white',
                marker_line_width=2
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No chapters identified")

    with col_chart2:
        st.markdown("### 🎯 Top Key Topics to Study")
        if agg_topics:
            df_tp = pd.DataFrame({
                "Topic": list(agg_topics.keys()),
                "Score": list(agg_topics.values())
            }).sort_values("Score", ascending=False).head(12)
            
            max_score = df_tp["Score"].max()
            df_tp["Relevance"] = (df_tp["Score"] / max_score).round(3) if max_score > 0 else 0
            
            fig2 = px.bar(df_tp, x="Relevance", y="Topic", orientation="h",
                         color="Relevance",
                         color_continuous_scale="purples",
                         labels={"Relevance": "Weight / Importance"})
            fig2.update_layout(
                yaxis={'categoryorder':'total ascending'},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=13),
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No topics identified")

    # File Details Section
    st.divider()
    st.subheader("📄 Uploaded File Insights")
    for fname, res in all_results.items():
        with st.expander(f"📋 Details for {fname}"):
            if "error" in res:
                st.error(res["error"])
                continue
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Questions Detected", len(res.get("questions", [])))
            c2.metric("Chapters", len(res.get("chapters", {})))
            c3.metric("Topics", len(res.get("topics", {})))
            
            if res.get("questions"):
                st.markdown("**Sample Extracted Questions from Paper:**")
                for i, q in enumerate(res["questions"][:3], 1):
                    st.caption(f"{i}. {q[:220]}...")
else:
    # Welcome hero
    st.markdown("""
    ### 🎯 How it works:
    1. 📤 **Upload one or more exam papers** (PDF format with text or scanned diagrams).
    2. 🤖 **Engine extracts syllabus distribution**, recurring topics, and question difficulty.
    3. ⚡ **Synthesizes Highest-Probability Exam Questions** with estimated marks and reasons why they are likely.
    4. 💡 **Explore Model Answers & Examiner Scoring Rubrics** for active recall practice.
    5. 📥 **Download a custom predicted test paper** to test yourself before the real exam!
    
    ### ✨ Core Capabilities:
    - ✅ **AI & Heuristic Question Forecaster**
    - ✅ **Probability Likelihood Ratings** (e.g. 96% Very High)
    - ✅ **Examiner Rubrics & Step-by-Step Model Answers**
    - ✅ **Interactive Multi-Subject Visualization**
    - ✅ **Works 100% Offline & with Groq / Gemini / OpenAI APIs**
    """)


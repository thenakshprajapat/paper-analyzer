"""
AI-powered analysis utilities for Paper Analyzer
Supports Groq (recommended, free & fast), Google Gemini, and OpenAI APIs
"""
import os
import time
import json
import re
import logging
import warnings
from typing import List, Dict, Optional
from collections import Counter

# Suppress deprecation warnings from legacy API packages
warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

# ===== API Client Imports =====
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.info("groq not installed. Install with: pip install groq")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.info("google-generativeai not installed. Install with: pip install google-generativeai")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.info("openai not installed. Install with: pip install openai")

# ===== Configuration =====
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Configure APIs if keys are available
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq API configured")
else:
    groq_client = None

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Google Gemini API configured")

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger.info("OpenAI API configured")

# Default provider: prefer Groq (free & fast), fallback to Gemini, then OpenAI, then basic heuristics
DEFAULT_PROVIDER = "groq" if (GROQ_AVAILABLE and GROQ_API_KEY) else \
                   "gemini" if (GEMINI_AVAILABLE and GEMINI_API_KEY) else \
                   "openai" if (OPENAI_AVAILABLE and OPENAI_API_KEY) else \
                   "basic"

# ===== Prompts =====
ANALYSIS_SYSTEM_PROMPT = """You are an expert educational content analyzer and exam strategist specializing in exam paper analysis and question forecasting. 
Your task is to identify academic chapters, subjects, and key topics from exam questions accurately, and synthesize high-probability predicted exam questions.

Focus on:
- Technical and academic concepts like "Binary Search", "Photosynthesis", "Newton's Laws"
- Multi-word phrases that represent specific topics
- Subject-specific vocabulary and named theories
- Core foundational concepts with high recurring examination weightage

Avoid common words that don't represent specific topics."""

CHAPTER_ANALYSIS_PROMPT = """You are analyzing an exam paper that may contain MULTIPLE subjects. Carefully read the text and identify ALL academic subjects present.

Text from exam paper:
{text}

CRITICAL INSTRUCTIONS:
1. **Scan the ENTIRE text** - look for keywords, terminology, and concepts from different subjects
2. **Return ALL subjects found** - Papers often mix Physics, Chemistry, and Biology!
3. **Assign confidence** based on how much content belongs to each subject (doesn't need to be 100% total)
4. **Look for these indicators:**
   - Physics: circuit, force, electromagnetic, induction, motion, resistance, voltage, current, magnetic, lens, waves
   - Chemistry: reaction, molecule, acid, base, equilibrium, titration, oxidation, pH, compound, element, ion
   - Biology: cell, tissue, organ, genetics, digestion, respiration, skeletal, kidney, excretion, enzyme, protein
   - Computer Science: Python, code, algorithm, function, database, SQL, programming, data structure
   - Mathematics: equation, derivative, integral, algebra, geometry, statistics

5. **DO NOT skip subjects** - if you find even 2-3 questions from a subject, include it!
6. **Use subject names EXACTLY as listed**

Valid subject names:
- Physics
- Chemistry
- Biology
- Computer Science
- Mathematics
- English
- History
- Geography

Return JSON with ALL subjects found:
{{"chapters": [{{"name": "Physics", "confidence": 0.45}}, {{"name": "Chemistry", "confidence": 0.35}}, {{"name": "Biology", "confidence": 0.20}}], "primary_subject": "Physics"}}

**IMPORTANT:** If the paper covers multiple subjects (like a science paper with Physics, Chemistry, AND Biology), list ALL of them! Don't be conservative!"""

TOPIC_EXTRACTION_PROMPT = """Extract the TOP 15-20 most important and specific academic topics/concepts from this exam paper.

Content:
{text}

IMPORTANT RULES:
1. Extract FULL, DESCRIPTIVE topic names that students would recognize
2. Use 2-4 words per topic (e.g., "Object-Oriented Programming", "Database Normalization", "Exception Handling")
3. Capitalize properly (e.g., "Python Programming", not "python programming")
4. For CS: Include language/tech names (e.g., "SQL Queries", "Python Functions", "Database Joins")
5. For Physics: Include full concepts (e.g., "Electromagnetic Induction", not just "induction")
6. For Chemistry: Include full names (e.g., "Chemical Equilibrium", not just "equilibrium")
7. For Biology: Include system names (e.g., "Human Digestive System", not just "digestion")
8. Avoid single generic words (e.g., ❌ "functions", ❌ "system", ❌ "operations")
9. Extract 15-20 topics that a student would write in their notes

GOOD EXAMPLES:
✅ "Python Programming"
✅ "SQL Database Management"  
✅ "Object-Oriented Programming"
✅ "Boolean Logic Operations"
✅ "Exception Handling Techniques"
✅ "Data Structure Implementation"

BAD EXAMPLES:
❌ "programming" (too generic)
❌ "SQL" (too short)
❌ "functions" (needs context like "Python Functions")
❌ "operations" (needs context like "Bitwise Operations")

Return JSON with 15-20 specific, student-friendly topics:
{{"topics": [{{"topic": "Python Programming Fundamentals", "relevance": 0.95}}, {{"topic": "SQL Database Operations", "relevance": 0.88}}]}}"""

QUESTION_CLASSIFY_PROMPT = """Classify this exam question into a specific chapter/unit and extract topics.

Look for chapter indicators like:
- "Chapter X: ..."
- Unit references
- Topic area names

Question:
\"\"\"
{question}
\"\"\"

Respond with JSON:
{{
  "chapter": "Specific Chapter/Unit Name (not just subject)",
  "topics": ["specific topic1", "specific topic2", "specific topic3"],
  "confidence": 0.85
}}

Be specific - identify the actual chapter/unit, not just the broad subject area."""

HIGH_PROBABILITY_QUESTIONS_PROMPT = """You are a senior exam board examiner and master educator specializing in exam prediction and high-yield question design.
Based on the following analysis of exam paper(s), your task is to CRAFT and PREDICT {num_questions} highest-probability exam questions that have the greatest likelihood of appearing in upcoming exams.

--- EXAM ANALYSIS CONTEXT ---
Primary Subject: {primary_subject}
Detected Chapters / Sections: {chapters_summary}
Top High-Weight Topics (with relevance weights): {topics_summary}
Sample Identified Questions / Patterns from Uploaded Paper:
{sample_questions}
-----------------------------

CRITICAL CRAFTING RULES:
1. Focus on core, foundational, high-yield syllabus concepts with high recurring testing frequency.
2. Provide a diverse, realistic mix of question formats:
   - Long Answer / Derivation / Detailed Analysis (5 to 8 marks)
   - Short Conceptual / Definition / Comparison (2 to 3 marks)
   - Problem Solving / Numerical / Code Implementation (3 to 5 marks)
   - Application / Case Study / Real-World Scenario (4 to 5 marks)
   - Multiple Choice / Objective with Options (1 mark)
3. For EACH crafted question:
   - Formulate clear, authentic exam question text with sub-parts like (a), (b) where appropriate.
   - Assign a realistic probability score (e.g. 82-98%) and probability tier ("Very High", "High", "Moderate").
   - Provide an educational rationale in `why_high_probability` explaining why examiners favor this question/topic.
   - List 3-4 essential grading points in `key_scoring_points` (formulas, keywords, core steps).
   - Write a clear step-by-step `model_answer_or_hint` so students can test themselves immediately.

Respond ONLY with valid JSON in this exact schema:
{{
  "predicted_questions": [
    {{
      "id": "Q1",
      "question": "State Faraday's laws of electromagnetic induction. (b) Derive an expression for the motional EMF induced in a conductor of length L moving with velocity v perpendicular to a uniform magnetic field B.",
      "subject": "Physics",
      "chapter": "Electromagnetic Induction",
      "topic": "Faraday's Law & Motional EMF",
      "type": "Long Answer / Derivation",
      "difficulty": "Medium",
      "estimated_marks": 5,
      "probability_score": 95,
      "probability_tier": "Very High",
      "why_high_probability": "Core fundamental concept appearing in over 85% of standard Physics board papers; high weightage derivation.",
      "key_scoring_points": [
        "Statement of 1st and 2nd Law with formula: e = -dPhi/dt",
        "Diagram of moving conductor in magnetic field B",
        "Derivation: Rate of area swept dA/dt = L*v, induced EMF e = B*L*v",
        "Direction of induced current via Fleming's Right-Hand Rule or Lenz's Law"
      ],
      "model_answer_or_hint": "Step 1: State both laws clearly. Step 2: Draw the magnetic field with the rod. Step 3: Use e = d(B*A)/dt = B * d(L*x)/dt = B*L*v."
    }}
  ]
}}"""


# ===== AI Analysis Functions =====

def analyze_chapters_ai(text: str, provider: str = None, sample_size: int = 12000) -> Dict:
    """
    Use AI to analyze and identify chapters in exam paper text.
    
    Args:
        text: Full text from PDF
        provider: "groq", "gemini", "openai", or None (auto-select)
        sample_size: Number of characters to analyze (to manage token limits)
    
    Returns:
        {"chapters": {chapter_name: confidence_score}, "primary_subject": "..."}
    """
    provider = provider or DEFAULT_PROVIDER
    
    # Take strategic samples from text
    text_sample = _sample_text(text, sample_size)
    prompt = CHAPTER_ANALYSIS_PROMPT.format(text=text_sample)
    
    try:
        if provider == "groq":
            result = _call_groq(prompt, system_prompt="")
        elif provider == "gemini":
            result = _call_gemini(prompt, system_prompt="")
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt="")
        else:
            return {"chapters": {}, "primary_subject": "Unknown"}
        
        # Parse response
        data = _extract_json(result)
        
        # Convert to simple chapter: score dict
        chapters = {}
        for ch in data.get("chapters", []):
            chapters[ch.get("name", "Unknown")] = ch.get("confidence", 0.5)
        
        return {
            "chapters": chapters,
            "primary_subject": data.get("primary_subject", "Unknown")
        }
    
    except RuntimeError as e:
        if "safety filter" in str(e).lower():
            logger.warning("⚠️ Gemini safety filter triggered - falling back to basic analysis")
            return {"chapters": {}, "primary_subject": "Unknown"}
        raise
    
    except Exception as e:
        logger.exception(f"AI chapter analysis failed with {provider}")
        return {"chapters": {}, "primary_subject": "Unknown"}


def extract_topics_ai(text: str, provider: str = None, sample_size: int = 6000) -> Dict[str, float]:
    """
    Use AI to extract key topics from exam paper text.
    
    Returns:
        {topic_name: relevance_score} dict
    """
    provider = provider or DEFAULT_PROVIDER
    
    text_sample = _sample_text(text, sample_size)
    prompt = TOPIC_EXTRACTION_PROMPT.format(text=text_sample)
    
    try:
        if provider == "groq":
            result = _call_groq(prompt, system_prompt="")
        elif provider == "gemini":
            result = _call_gemini(prompt, system_prompt="")
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt="")
        else:
            return {}
        
        data = _extract_json(result)
        
        # Convert to simple topic: score dict
        topics = {}
        for item in data.get("topics", []):
            topic = item.get("topic", "")
            if topic:
                topics[topic] = item.get("relevance", 0.5)
        
        return topics
    
    except RuntimeError as e:
        if "safety filter" in str(e).lower():
            logger.warning("⚠️ Gemini safety filter triggered - falling back to basic analysis")
            return {}
        raise
    
    except Exception as e:
        logger.exception(f"AI topic extraction failed with {provider}")
        return {}


def classify_questions_ai(questions: List[str], provider: str = None, max_questions: int = 10) -> List[Dict]:
    """
    Classify individual questions using AI.
    
    Returns:
        List of {"chapter": str, "topics": [str], "confidence": float}
    """
    provider = provider or DEFAULT_PROVIDER
    
    if provider == "basic":
        return [{"chapter": "Unknown", "topics": [], "confidence": 0.0} for _ in questions]
    
    results = []
    # Process first N questions to avoid rate limits
    for q in questions[:max_questions]:
        prompt = QUESTION_CLASSIFY_PROMPT.format(question=q[:500])
        
        try:
            if provider == "groq":
                result = _call_groq(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            elif provider == "gemini":
                result = _call_gemini(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            elif provider == "openai":
                result = _call_openai(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            else:
                results.append({"chapter": "Unknown", "topics": [], "confidence": 0.0})
                continue
            
            data = _extract_json(result)
            results.append({
                "chapter": data.get("chapter", "Unknown"),
                "topics": data.get("topics", []),
                "confidence": data.get("confidence", 0.5)
            })
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            logger.warning(f"Question classification failed: {e}")
            results.append({"chapter": "Unknown", "topics": [], "confidence": 0.0})
    
    return results


def craft_high_probability_questions(
    text: str = "",
    chapters: Optional[Dict[str, float]] = None,
    topics: Optional[Dict[str, float]] = None,
    sample_questions: Optional[List[str]] = None,
    primary_subject: str = "General Science",
    provider: str = None,
    num_questions: int = 8
) -> Dict:
    """
    Craft and predict high-probability exam questions based on paper analysis.
    
    Args:
        text: Raw text of exam paper(s)
        chapters: Dict of chapter/subject names to scores
        topics: Dict of topic names to scores/relevance
        sample_questions: List of questions extracted from the paper
        primary_subject: Inferred main subject
        provider: AI provider ("groq", "gemini", "openai", "basic")
        num_questions: Number of questions to craft
        
    Returns:
        Dict containing list of crafted questions and metadata
    """
    provider = provider or DEFAULT_PROVIDER
    chapters = chapters or {}
    topics = topics or {}
    sample_questions = sample_questions or []
    
    # Format inputs for prompt
    chapters_str = ", ".join([f"{k} (Weight: {v:.1f})" for k, v in list(chapters.items())[:6]]) or "General Curriculum"
    topics_str = ", ".join([f"{k} ({v:.2f})" if isinstance(v, float) else f"{k} ({v})" for k, v in list(topics.items())[:15]]) or "Core Curriculum Topics"
    
    formatted_sample_q = "\n".join([f"- {q[:180]}..." for q in sample_questions[:5]]) if sample_questions else "- Standard question pattern"
    
    prompt = HIGH_PROBABILITY_QUESTIONS_PROMPT.format(
        primary_subject=primary_subject,
        chapters_summary=chapters_str,
        topics_summary=topics_str,
        sample_questions=formatted_sample_q,
        num_questions=num_questions
    )
    
    # Try AI providers if active
    if provider in ["groq", "gemini", "openai"]:
        try:
            if provider == "groq":
                raw_resp = _call_groq(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            elif provider == "gemini":
                raw_resp = _call_gemini(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            elif provider == "openai":
                raw_resp = _call_openai(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
            else:
                raw_resp = "{}"
                
            data = _extract_json(raw_resp)
            predicted = data.get("predicted_questions", [])
            if isinstance(predicted, list) and len(predicted) > 0:
                # Sanitize and ensure complete fields
                cleaned_questions = _normalize_predicted_questions(predicted, primary_subject)
                return _build_questions_response(cleaned_questions, f"AI ({provider})")
        except Exception as e:
            logger.warning(f"AI question crafting failed with {provider}: {e}. Using intelligent fallback.")
    
    # Intelligent Heuristic Fallback Synthesizer
    fallback_questions = _craft_heuristic_questions(
        chapters=chapters,
        topics=topics,
        sample_questions=sample_questions,
        primary_subject=primary_subject,
        num_questions=num_questions
    )
    return _build_questions_response(fallback_questions, "Intelligent Heuristic Synthesizer")


def _normalize_predicted_questions(questions: List[Dict], default_subject: str = "General") -> List[Dict]:
    """Ensure all required fields exist with valid values in predicted questions."""
    normalized = []
    for idx, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            continue
        
        prob = q.get("probability_score", 85)
        try:
            prob = int(prob)
        except (ValueError, TypeError):
            prob = 85
        prob = max(60, min(99, prob))
        
        tier = q.get("probability_tier")
        if not tier:
            tier = "Very High" if prob >= 90 else "High" if prob >= 80 else "Moderate"
            
        marks = q.get("estimated_marks", 5)
        try:
            marks = int(marks)
        except (ValueError, TypeError):
            marks = 5
            
        scoring_pts = q.get("key_scoring_points", [])
        if isinstance(scoring_pts, str):
            scoring_pts = [scoring_pts]
            
        normalized.append({
            "id": q.get("id", f"Q{idx}"),
            "question": q.get("question", "Explain the fundamental principles and significance of the core topic."),
            "subject": q.get("subject", default_subject),
            "chapter": q.get("chapter", "Core Unit"),
            "topic": q.get("topic", "Key Concept"),
            "type": q.get("type", "Long Answer"),
            "difficulty": q.get("difficulty", "Medium"),
            "estimated_marks": marks,
            "probability_score": prob,
            "probability_tier": tier,
            "why_high_probability": q.get("why_high_probability", "Core curriculum concept recurring frequently in standard exam patterns."),
            "key_scoring_points": scoring_pts if scoring_pts else ["Accurate definition", "Step-by-step logic", "Correct conclusion"],
            "model_answer_or_hint": q.get("model_answer_or_hint", "Review key textbook definitions and practice step-by-step derivation.")
        })
    return normalized


def _craft_heuristic_questions(
    chapters: Dict[str, float],
    topics: Dict[str, float],
    sample_questions: List[str],
    primary_subject: str = "General Science",
    num_questions: int = 8
) -> List[Dict]:
    """
    Intelligent heuristic question synthesizer based on curriculum patterns and top extracted topics.
    Provides realistic, high-probability exam questions even without external AI keys.
    """
    crafted = []
    top_topics_list = list(topics.keys())[:12]
    top_chapters_list = list(chapters.keys())[:5]
    
    # Rich curated domain templates for high-yield exam archetypes
    domain_templates = {
        'Physics': [
            {
                'topic': 'Electromagnetic Induction & Faraday\'s Laws',
                'chapter': 'Electromagnetism',
                'type': 'Long Answer / Derivation',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 96,
                'question': '(a) State Faraday\'s laws of electromagnetic induction and Lenz\'s law. (b) Derive an expression for the motional EMF induced across the ends of a conductor of length L moving with velocity v perpendicular to a uniform magnetic field B.',
                'why': 'Foundational electromagnetism concept appearing in >85% of board and competitive exams.',
                'points': ['State 1st & 2nd law: e = -dPhi/dt', 'Lenz\'s law & conservation of energy', 'Derivation: e = B*L*v with diagram', 'Direction of induced current via Fleming\'s Right-Hand rule'],
                'model': 'State laws clearly. Draw moving rod diagram. Show magnetic flux Phi = B*A = B*L*x. Differentiating w.r.t time gives e = -dPhi/dt = B*L*(dx/dt) = B*L*v.'
            },
            {
                'topic': 'Kirchhoff\'s Circuit Laws & Wheatstone Bridge',
                'chapter': 'Current Electricity',
                'type': 'Numerical / Problem Solving',
                'marks': 5,
                'difficulty': 'Hard',
                'prob': 93,
                'question': 'State Kirchhoff\'s Junction and Loop rules with mathematical formulas. Using these rules, derive the condition for balance in a Wheatstone bridge network (P/Q = R/S).',
                'why': 'Standard electrical circuit theory core question testing both conceptual law and formal derivation.',
                'points': ['Junction Rule: Sigma I = 0 (charge conservation)', 'Loop Rule: Sigma Delta V = 0 (energy conservation)', 'Loop 1 and Loop 2 equations with galvanometer current Ig = 0', 'Ratio derivation P/Q = R/S'],
                'model': 'Apply Loop Rule to mesh ABDA and BCDB. Set Ig = 0 for null deflection: I1*P = I2*R and I1*Q = I2*S. Divide equations to obtain P/Q = R/S.'
            },
            {
                'topic': 'Optics - Lens Maker\'s Formula & Refraction',
                'chapter': 'Ray Optics',
                'type': 'Derivation',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 91,
                'question': 'Derive the Lens Maker\'s Formula 1/f = (mu - 1)(1/R1 - 1/R2) for a thin convex lens bounded by spherical surfaces of radii R1 and R2.',
                'why': 'Permanent fixture in optical physics theory exams with high mark weightage.',
                'points': ['Refraction formula at single spherical surface: mu2/v - mu1/u = (mu2-mu1)/R', 'Apply for 1st surface (image as virtual object for 2nd)', 'Sum of equations and thin lens approximation', 'Final relation equating with 1/v - 1/u = 1/f'],
                'model': 'Combine refraction at surface 1 and 2. Set thickness t -> 0. Obtain 1/v - 1/u = (mu-1)(1/R1 - 1/R2). Substitute 1/f = 1/v - 1/u.'
            },
            {
                'topic': 'Photoelectric Effect & Einstein\'s Equation',
                'chapter': 'Dual Nature of Matter',
                'type': 'Short Conceptual',
                'marks': 3,
                'difficulty': 'Easy',
                'prob': 89,
                'question': 'Define threshold frequency and work function in photoelectric emission. Write Einstein\'s photoelectric equation and explain how it accounts for the maximum kinetic energy of emitted photoelectrons.',
                'why': 'Fundamental modern physics concept with straightforward scoring rubric.',
                'points': ['Definition of threshold frequency (nu_0)', 'Definition of work function (Phi_0 = h*nu_0)', 'Equation: h*nu = Phi_0 + K_max = h*nu_0 + 1/2*m*v_max^2', 'Dependence of K_max on frequency, not intensity'],
                'model': 'Work function is minimum energy required to liberate electron from metal surface. Einstein equation: K_max = h(nu - nu_0).'
            }
        ],
        'Chemistry': [
            {
                'topic': 'Chemical Equilibrium & Le Chatelier\'s Principle',
                'chapter': 'Equilibrium',
                'type': 'Application / Conceptual',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 95,
                'question': 'State Le Chatelier\'s Principle. Predict and explain the effect of (i) increasing pressure, (ii) decreasing temperature, and (iii) adding a catalyst on the synthesis of ammonia by Haber\'s process: N2(g) + 3H2(g) <=> 2NH3(g) + Delta H = -92.4 kJ.',
                'why': 'Central physical chemistry equilibrium question with predictable application parts.',
                'points': ['Statement of Le Chatelier principle', 'Pressure increase shifts to fewer moles (forward/right)', 'Exothermic reaction: lowering temperature shifts forward', 'Catalyst increases rate of forward and reverse equally without shifting equilibrium position'],
                'model': 'Principle states system opposes applied constraint. For Haber process: high pressure shifts right (4 moles -> 2 moles); lower temp favours exothermic forward reaction; catalyst speeds equilibrium without altering yield.'
            },
            {
                'topic': 'Electrochemistry - Nernst Equation & Cell Potential',
                'chapter': 'Electrochemistry',
                'type': 'Numerical Problem',
                'marks': 5,
                'difficulty': 'Hard',
                'prob': 92,
                'question': 'Write the Nernst equation for a general galvanic cell reaction at 298 K. Calculate the EMF of the cell: Zn(s) | Zn2+(0.01 M) || Cu2+(0.1 M) | Cu(s), given E°(Zn2+/Zn) = -0.76 V and E°(Cu2+/Cu) = +0.34 V.',
                'why': 'Standard electrochemical numerical tested consistently across board and university exams.',
                'points': ['Formula: E_cell = E°_cell - (0.0591/n) * log([Zn2+]/[Cu2+])', 'Calculation of E°_cell = E°_cathode - E°_anode = 0.34 - (-0.76) = 1.10 V', 'n = 2 electrons transferred', 'Log ratio: log(0.01/0.1) = log(0.1) = -1', 'Final calculation: E_cell = 1.10 - (0.0591/2)*(-1) = 1.1295 V'],
                'model': 'E°_cell = 1.10 V. E_cell = 1.10 - (0.0591/2) * log(0.01/0.1) = 1.10 - (0.02955 * -1) = 1.1295 V.'
            },
            {
                'topic': 'Organic Reaction Mechanisms - SN1 vs SN2',
                'chapter': 'Organic Chemistry',
                'type': 'Comparison / Mechanism',
                'marks': 4,
                'difficulty': 'Medium',
                'prob': 90,
                'question': 'Differentiate between SN1 and SN2 nucleophilic substitution reaction mechanisms with respect to (a) kinetics/order, (b) stereochemical outcome (inversion vs racemization), (c) carbocation intermediate, and (d) substrate reactivity order (1°, 2°, 3° alkyl halides).',
                'why': 'Core organic reaction mechanism comparing substitution pathways.',
                'points': ['SN1: Unimolecular (1st order), 2-step via carbocation, racemization, 3° > 2° > 1°', 'SN2: Bimolecular (2nd order), 1-step concerted via transition state, Walden inversion, 1° > 2° > 3°'],
                'model': 'Organize comparison in 4 clear tabular rows: Step count & kinetics, transition state/carbocation, stereochemistry, and steric hindrance factor.'
            }
        ],
        'Biology': [
            {
                'topic': 'Photosynthesis - Light vs Dark Reactions',
                'chapter': 'Plant Physiology',
                'type': 'Long Answer',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 96,
                'question': 'Describe the schematic Z-scheme of light reaction in photosynthesis. Differentiate between cyclic and non-cyclic photophosphorylation with respect to photosystems involved, end products, and oxygen evolution.',
                'why': 'High-yield physiological mechanism in botany/biology papers.',
                'points': ['Z-scheme electron transport involving PS II (P680) and PS I (P700)', 'Photolysis of water releasing 2H+, 2e-, and 1/2 O2', 'Non-cyclic: PS II & I, produces ATP + NADPH, evolves O2', 'Cyclic: PS I only, produces ATP only, no O2 evolved'],
                'model': 'Draw Z-scheme flow diagram: Water splitting -> PS II -> Plastoquinone -> Cytochrome b6f -> Plastocyanin -> PS I -> Ferredoxin -> NADP+ reductase.'
            },
            {
                'topic': 'Human Excretory System & Nephron Function',
                'chapter': 'Human Physiology',
                'type': 'Diagram / Explanation',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 94,
                'question': 'Explain the step-by-step mechanism of urine formation in a human nephron with reference to (i) Glomerular Ultrafiltration, (ii) Selective Tubular Reabsorption, and (iii) Tubular Secretion.',
                'why': 'Standard anatomical and physiological question in animal biology.',
                'points': ['Ultrafiltration across 3 layers under effective filtration pressure (GFR ~125 mL/min)', 'Reabsorption in PCT (glucose, amino acids, 70-80% electrolytes)', 'Henle\'s Loop counter-current mechanism for osmotic concentration', 'DCT & Collecting duct hormonal regulation (ADH/Aldosterone)'],
                'model': 'Structure answer into three bold headings corresponding to the 3 physiological steps. Mention key substances reabsorbed vs secreted at each segment.'
            },
            {
                'topic': 'DNA Replication & Semi-Conservative Model',
                'chapter': 'Genetics & Molecular Biology',
                'type': 'Process Description',
                'marks': 5,
                'difficulty': 'Hard',
                'prob': 91,
                'question': 'Describe the Meselson and Stahl experiment that proved the semi-conservative nature of DNA replication using 15N and 14N isotopes and CsCl density gradient centrifugation.',
                'why': 'Historical benchmark experiment in molecular biology curricula.',
                'points': ['E. coli grown in 15NH4Cl heavy medium', 'Transfer to 14N light medium and sample at Generation 1 (20 min) and Generation 2 (40 min)', 'Generation 1: Single intermediate hybrid density band', 'Generation 2: Equal ratio of hybrid and light density bands proving semi-conservative replication'],
                'model': 'Detail the experimental setup, culture timeline, centrifuge separation results, and deduce why conservative and dispersive models were ruled out.'
            }
        ],
        'Computer Science': [
            {
                'topic': 'Object-Oriented Programming (OOP) Principles',
                'chapter': 'Software Engineering & OOP',
                'type': 'Short Conceptual & Code',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 97,
                'question': 'Explain the four core principles of Object-Oriented Programming: Encapsulation, Abstraction, Inheritance, and Polymorphism. Provide a short Python/Java code demonstration illustrating Method Overriding and Inheritance.',
                'why': 'Foundational computing concept appearing on almost every programming exam.',
                'points': ['Accurate definitions of all 4 pillars', 'Encapsulation with private attributes/getters', 'Inheritance base and derived class relationship', 'Polymorphism dynamic method overriding demonstration with code'],
                'model': 'Define each pillar clearly in 1-2 sentences. Write class Parent with method speak() and class Child(Parent) overriding speak() with super() invocation.'
            },
            {
                'topic': 'SQL Database Queries & Table Joins',
                'chapter': 'Database Management Systems',
                'type': 'Practical / SQL Implementation',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 95,
                'question': 'Consider two tables: `Students(student_id, name, department_id)` and `Departments(department_id, dept_name)`. Write SQL queries to: (a) Retrieve all student names along with their department names using INNER JOIN. (b) Find departments that currently have more than 5 enrolled students using GROUP BY and HAVING.',
                'why': 'Standard relational database query assessment evaluating multi-table joins and aggregation.',
                'points': ['(a) SELECT s.name, d.dept_name FROM Students s INNER JOIN Departments d ON s.department_id = d.department_id;', '(b) SELECT d.dept_name, COUNT(s.student_id) FROM Departments d JOIN Students s ON d.department_id = s.department_id GROUP BY d.dept_name HAVING COUNT(s.student_id) > 5;'],
                'model': 'Query A: Use clean aliases and explicit ON condition. Query B: Group by department identifier and apply HAVING aggregate condition.'
            },
            {
                'topic': 'Data Structures - Stack vs Queue & Recursion',
                'chapter': 'Data Structures & Algorithms',
                'type': 'Algorithm & Analysis',
                'marks': 4,
                'difficulty': 'Medium',
                'prob': 92,
                'question': 'Differentiate between Stack (LIFO) and Queue (FIFO) abstract data types. Explain how the Call Stack is utilized in managing recursive function calls and write a recursive function to compute the Fibonacci sequence with its time complexity.',
                'why': 'Core algorithmic principles tested across data structure exams.',
                'points': ['Stack LIFO push/pop vs Queue FIFO enqueue/dequeue (O(1))', 'Call stack activation records, return addresses, and base case requirement', 'Recursive Fibonacci code with base condition', 'Time complexity analysis: O(2^n) naive vs O(n) memoized'],
                'model': 'Define LIFO/FIFO with real-world examples. Explain call frame push on recursive call and pop on return. Write clean python def fib(n).'
            },
            {
                'topic': 'Exception Handling & File Operations',
                'chapter': 'Programming & System Design',
                'type': 'Code Implementation',
                'marks': 3,
                'difficulty': 'Easy',
                'prob': 88,
                'question': 'Explain the purpose of `try`, `except`, `else`, and `finally` blocks in structured exception handling. Write a program to safely read a file line-by-line and handle `FileNotFoundError` and `PermissionError`.',
                'why': 'Essential practical defensive programming standard question.',
                'points': ['Role of each keyword (finally always executes for cleanup)', 'Safe context manager (with open) or try/except block', 'Catching specific exceptions before general Exception'],
                'model': 'Explain exception flow. Code: try block opening file, specific except FileNotFoundError, except PermissionError, and finally closing resources.'
            }
        ],
        'Mathematics': [
            {
                'topic': 'Calculus - Definite Integrals & Fundamental Theorem',
                'chapter': 'Integral Calculus',
                'type': 'Problem Solving / Derivation',
                'marks': 5,
                'difficulty': 'Hard',
                'prob': 96,
                'question': 'State the Fundamental Theorem of Calculus. Evaluate the definite integral: Integrate from 0 to pi/2 of [sqrt(sin(x)) / (sqrt(sin(x)) + sqrt(cos(x)))] dx using the definite integral property: Integral 0 to a f(x)dx = Integral 0 to a f(a-x)dx.',
                'why': 'Classic standard symmetry property integral with high recurrence in math exams.',
                'points': ['State FTC relation: d/dx Integral a to x f(t)dt = f(x)', 'Let I = Integral 0 to pi/2 sqrt(sin(x))/(sqrt(sin(x)) + sqrt(cos(x))) dx', 'Apply property f(pi/2 - x) -> sin becomes cos, cos becomes sin', 'Add the two integrals: 2I = Integral 0 to pi/2 (1) dx = pi/2', 'Final Answer: I = pi/4'],
                'model': 'Let I be the original integral (Eq 1). Transform x -> pi/2 - x to get I = Integral sqrt(cos x)/(sqrt(cos x) + sqrt(sin x)) dx (Eq 2). Adding (1) and (2) gives 2I = Integral 1 dx from 0 to pi/2 = pi/2, hence I = pi/4.'
            },
            {
                'topic': 'Matrices & Systems of Linear Equations',
                'chapter': 'Linear Algebra & Matrices',
                'type': 'Matrix Method / Numerical',
                'marks': 5,
                'difficulty': 'Medium',
                'prob': 93,
                'question': 'Solve the following system of linear equations using Matrix Inversion Method (X = A^(-1) * B): 2x + 3y + 3z = 5, x - 2y + z = -4, 3x - y - 2z = 3.',
                'why': 'Universal linear algebra examination question testing determinant, adjoint, and inverse.',
                'points': ['Express in matrix form A*X = B', 'Calculate determinant det(A) and verify non-singular (det(A) != 0)', 'Compute matrix of cofactors and adjoint adj(A)', 'Compute A^(-1) = adj(A)/det(A)', 'Multiply A^(-1)*B to determine x, y, z values'],
                'model': 'Write matrix A, column vector X, and constant vector B. Calculate det(A). Find adj(A) via cofactors. Multiply adj(A)*B / det(A) to get solution.'
            }
        ]
    }
    
    # Check if primary subject matches or detect from chapters
    matched_domain = None
    for subject in domain_templates.keys():
        if subject.lower() in primary_subject.lower():
            matched_domain = subject
            break
        for ch in top_chapters_list:
            if subject.lower() in ch.lower():
                matched_domain = subject
                break
                
    if matched_domain and matched_domain in domain_templates:
        base_questions = domain_templates[matched_domain]
        for idx, q_data in enumerate(base_questions[:num_questions], 1):
            crafted.append({
                "id": f"Q{idx}",
                "question": q_data['question'],
                "subject": matched_domain,
                "chapter": q_data['chapter'],
                "topic": q_data['topic'],
                "type": q_data['type'],
                "difficulty": q_data['difficulty'],
                "estimated_marks": q_data['marks'],
                "probability_score": q_data['prob'],
                "probability_tier": "Very High" if q_data['prob'] >= 90 else "High",
                "why_high_probability": q_data['why'],
                "key_scoring_points": q_data['points'],
                "model_answer_or_hint": q_data['model']
            })
            
    # If we need more questions or no exact domain template, dynamically craft using extracted topics!
    while len(crafted) < num_questions and top_topics_list:
        topic_name = top_topics_list.pop(0)
        idx = len(crafted) + 1
        score_val = topics.get(topic_name, 0.85)
        prob_score = int(min(98, max(75, 78 + (score_val * 20) if isinstance(score_val, float) else 86)))
        
        # Determine archetype by index
        archetypes = [
            ("Long Answer / Conceptual", 5, "Medium", f"Explain the fundamental mechanisms and principles of {topic_name}. Discuss its real-world significance and give illustrative examples.", f"Core high-frequency topic extracted from multiple sections of the uploaded paper."),
            ("Application / Problem Solving", 4, "Hard", f"Analyze how {topic_name} is applied to solve complex problems in modern systems. Outline step-by-step methodologies and potential constraints.", f"Practical application concept frequently tested in modern exam patterns."),
            ("Short Conceptual & Comparison", 3, "Easy", f"Define {topic_name}. Differentiate it from closely related concepts and state its primary advantages and use cases.", f"High-yield definition and comparison question carrying direct marks."),
            ("Objective / MCQ", 1, "Easy", f"Which of the following best characterizes the primary function of {topic_name}? [A] Primary activation [B] Secondary inhibition [C] Linear optimization [D] None of the above", f"Fast-scoring objective item testing foundational clarity.")
        ]
        arch = archetypes[idx % len(archetypes)]
        
        crafted.append({
            "id": f"Q{idx}",
            "question": arch[3],
            "subject": primary_subject,
            "chapter": top_chapters_list[idx % len(top_chapters_list)] if top_chapters_list else primary_subject,
            "topic": topic_name,
            "type": arch[0],
            "difficulty": arch[2],
            "estimated_marks": arch[1],
            "probability_score": prob_score,
            "probability_tier": "Very High" if prob_score >= 90 else "High" if prob_score >= 80 else "Moderate",
            "why_high_probability": arch[4],
            "key_scoring_points": [
                f"Accurate and rigorous definition of {topic_name}",
                "Key underlying formula, architecture, or mechanism",
                "Application constraints, edge cases, or trade-offs"
            ],
            "model_answer_or_hint": f"Begin with a clear 2-sentence thesis defining {topic_name}. Present structured bullet points covering theory, equations/code/diagrams, and conclude with practical implications."
        })
        
    # If still empty, supply top foundational questions across domains
    if not crafted:
        for subj, q_list in domain_templates.items():
            if len(crafted) >= num_questions:
                break
            q_data = q_list[0]
            crafted.append({
                "id": f"Q{len(crafted)+1}",
                "question": q_data['question'],
                "subject": subj,
                "chapter": q_data['chapter'],
                "topic": q_data['topic'],
                "type": q_data['type'],
                "difficulty": q_data['difficulty'],
                "estimated_marks": q_data['marks'],
                "probability_score": q_data['prob'],
                "probability_tier": "Very High" if q_data['prob'] >= 90 else "High",
                "why_high_probability": q_data['why'],
                "key_scoring_points": q_data['points'],
                "model_answer_or_hint": q_data['model']
            })
            
    return crafted[:num_questions]


def _build_questions_response(questions: List[Dict], generated_by: str) -> Dict:
    """Build final structured response with calculation of summary statistics."""
    if not questions:
        return {
            "questions": [],
            "total_questions": 0,
            "average_probability": 0,
            "total_predicted_marks": 0,
            "top_predicted_topics": [],
            "generated_by": generated_by
        }
    
    total_prob = sum(q.get("probability_score", 85) for q in questions)
    avg_prob = round(total_prob / len(questions), 1)
    total_marks = sum(q.get("estimated_marks", 5) for q in questions)
    top_topics = list({q.get("topic") for q in questions if q.get("topic")})[:5]
    
    return {
        "questions": questions,
        "total_questions": len(questions),
        "average_probability": avg_prob,
        "total_predicted_marks": total_marks,
        "top_predicted_topics": top_topics,
        "generated_by": generated_by
    }


# ===== API Call Helpers =====

def _call_groq(prompt: str, system_prompt: str = "", model: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API (FREE & FAST alternative to Gemini)"""
    if not GROQ_AVAILABLE or not GROQ_API_KEY:
        raise RuntimeError("Groq not available")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = groq_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=3000,
    )
    
    return response.choices[0].message.content


def _call_gemini(prompt: str, system_prompt: str = "", model: str = "gemini-2.5-flash") -> str:
    """Call Google Gemini API"""
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        raise RuntimeError("Gemini not available")
    
    # Disable safety filters for educational content analysis
    safety_settings = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }
    
    model_obj = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt if system_prompt else None,
        safety_settings=safety_settings
    )
    
    response = model_obj.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=3000,
        ),
        safety_settings=safety_settings
    )
    
    # Handle safety filter blocks
    try:
        return response.text
    except ValueError as e:
        if "finish_reason" in str(e):
            logger.warning(f"Gemini safety filter triggered: {e}")
            raise RuntimeError(f"Content blocked by safety filter: {e}")
        raise


def _call_openai(prompt: str, system_prompt: str = "", model: str = "gpt-3.5-turbo") -> str:
    """Call OpenAI API"""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        raise RuntimeError("OpenAI not available")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=3000
    )
    
    return response.choices[0].message['content']


# ===== Utility Functions =====

def _sample_text(text: str, max_chars: int = 12000) -> str:
    """Sample text from ENTIRE document to catch all subjects (Physics, Chemistry, Biology)"""
    if not text:
        return ""
    
    text_len = len(text)
    if text_len <= max_chars:
        return text
    
    # Take samples from different sections to catch all subjects
    chunk_size = max_chars // 3
    
    beginning = text[:chunk_size]
    middle_start = text_len // 2 - chunk_size // 2
    middle = text[middle_start:middle_start + chunk_size]
    end = text[-chunk_size:]
    
    combined = beginning + "\n\n[... middle section ...]\n\n" + middle + "\n\n[... end section ...]\n\n" + end
    return combined[:max_chars]


def _extract_json(text: str) -> Dict:
    """Extract and parse JSON from AI response, handling markdown code blocks and partial fixes"""
    if not text or not text.strip():
        return {}
        
    cleaned_text = text.strip()
    
    # Remove markdown code fences (```json ... ``` or ``` ... ```)
    if cleaned_text.startswith('```'):
        first_newline = cleaned_text.find('\n')
        if first_newline != -1:
            cleaned_text = cleaned_text[first_newline + 1:]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()
    
    # Direct parse attempt
    try:
        parsed = json.loads(cleaned_text)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"predicted_questions": parsed}
    except json.JSONDecodeError:
        pass
    
    # Extract outermost JSON object { ... }
    json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            # Try fixing trailing commas before closing braces/brackets
            fixed = re.sub(r',\s*([\}\]])', r'\1', json_match.group(0))
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
                
    # Extract JSON list [ ... ]
    list_match = re.search(r'\[[\s\S]*\]', cleaned_text)
    if list_match:
        try:
            items = json.loads(list_match.group(0))
            return {"predicted_questions": items}
        except json.JSONDecodeError:
            fixed = re.sub(r',\s*([\}\]])', r'\1', list_match.group(0))
            try:
                items = json.loads(fixed)
                return {"predicted_questions": items}
            except json.JSONDecodeError:
                pass
    
    logger.warning(f"Could not parse JSON from AI response. Text preview: {text[:200]}")
    return {}


def get_available_providers() -> List[str]:
    """Return list of available AI providers"""
    providers = []
    if GROQ_AVAILABLE and GROQ_API_KEY:
        providers.append("groq")
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        providers.append("gemini")
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        providers.append("openai")
    providers.append("basic")  # Always available
    return providers


def get_ai_status() -> Dict:
    """Return status of AI integrations"""
    return {
        "groq_available": GROQ_AVAILABLE and bool(GROQ_API_KEY),
        "gemini_available": GEMINI_AVAILABLE and bool(GEMINI_API_KEY),
        "openai_available": OPENAI_AVAILABLE and bool(OPENAI_API_KEY),
        "default_provider": DEFAULT_PROVIDER,
        "available_providers": get_available_providers()
    }
"""
AI-powered analysis utilities for Paper Analyzer
Supports Google Gemini (recommended, free tier) and OpenAI APIs
"""
import os
import time
import json
import re
import logging
from typing import List, Dict, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# ===== API Client Imports =====
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Configure APIs if keys are available
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Google Gemini API configured")

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger.info("OpenAI API configured")

# Default provider: prefer Gemini (free tier is generous), fallback to OpenAI, then basic heuristics
DEFAULT_PROVIDER = "gemini" if (GEMINI_AVAILABLE and GEMINI_API_KEY) else \
                   "openai" if (OPENAI_AVAILABLE and OPENAI_API_KEY) else \
                   "basic"

# ===== Prompts =====
ANALYSIS_SYSTEM_PROMPT = """You are an expert educational content analyzer specializing in exam paper analysis. 
You identify academic chapters/subjects and extract key technical/academic topics from exam questions with high precision.

CRITICAL RULES:
- Extract only meaningful academic/technical concepts (e.g., "Binary Search", "Photosynthesis", "Newton's Laws")
- NEVER extract common words like: statement, given, following, correct, true, false, both, either, assertion, reason
- NEVER extract question format words: ncert, column, section, marks, explain, write
- Focus on multi-word technical terms (2-4 words preferred)
- Prioritize subject-specific vocabulary and concepts"""

CHAPTER_ANALYSIS_PROMPT = """Analyze this exam paper text and identify the specific chapters, units, or sections that questions are from.

Look for:
- Chapter titles/names mentioned in questions (e.g., "Chapter 3: Data Structures")
- Section headings or unit references
- Topic groupings that indicate different chapters
- Common chapter patterns like: Introduction, Fundamentals, Advanced Topics, Applications, etc.

Text excerpt:
\"\"\"
{text}
\"\"\"

Respond with a JSON object:
{{
  "chapters": [
    {{"name": "Specific Chapter/Unit Name", "confidence": 0.95, "evidence": ["keyword1", "keyword2"]}},
    ...
  ],
  "primary_subject": "Overall subject area"
}}

Be specific - extract actual chapter names from the paper, not just broad subjects. If no explicit chapter names exist, identify distinct topic areas (e.g., "Sorting Algorithms", "Database Management", "Object-Oriented Programming")."""

TOPIC_EXTRACTION_PROMPT = """Extract ONLY specific academic concepts and named theories/laws/processes from this exam paper.

STRICT RULES - Extract ONLY:
✅ Named concepts: "Ohm's Law", "Photosynthesis", "Binary Search Tree", "Le Chatelier's Principle"
✅ Technical processes: "Cellular Respiration", "Electrolysis", "Polymerization"  
✅ Specific theories: "Darwin's Theory", "Quantum Mechanics", "Thermodynamics"
✅ Named structures: "DNA Structure", "Benzene Ring", "Nervous System"

❌ NEVER extract:
- Single generic words: energy, water, field, force, current, pressure, solution, compound, bone
- Common adjectives: magnetic, increases
- Question words: statement, given, following, correct, assertion, reason

Text excerpt:
\"\"\"
{text}
\"\"\"

Respond with a JSON object:
{{
  "topics": [
    {{"topic": "Specific Named Concept (2-5 words)", "relevance": 0.9, "category": "subject"}},
    ...
  ]
}}

GOOD: "Chemical Equilibrium", "Newton's Laws of Motion", "DNA Replication", "Redox Reactions"
BAD: "energy", "water", "increases", "field", "current", "pressure"

Extract 8-12 SPECIFIC academic concepts only."""

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


# ===== AI Analysis Functions =====

def analyze_chapters_ai(text: str, provider: str = None, sample_size: int = 3000) -> Dict:
    """
    Use AI to analyze and identify chapters in exam paper text.
    
    Args:
        text: Full text from PDF
        provider: "gemini", "openai", or None (auto-select)
        sample_size: Number of characters to analyze (to manage token limits)
    
    Returns:
        {"chapters": {chapter_name: confidence_score}, "primary_subject": "..."}
    """
    provider = provider or DEFAULT_PROVIDER
    
    # Take strategic samples from text
    text_sample = _sample_text(text, sample_size)
    prompt = CHAPTER_ANALYSIS_PROMPT.format(text=text_sample)
    
    try:
        if provider == "gemini":
            result = _call_gemini(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
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
    
    except Exception as e:
        logger.exception(f"AI chapter analysis failed with {provider}")
        return {"chapters": {}, "primary_subject": "Unknown"}


def extract_topics_ai(text: str, provider: str = None, sample_size: int = 3000) -> Dict[str, float]:
    """
    Use AI to extract key topics from exam paper text.
    
    Returns:
        {topic_name: relevance_score} dict
    """
    provider = provider or DEFAULT_PROVIDER
    
    text_sample = _sample_text(text, sample_size)
    prompt = TOPIC_EXTRACTION_PROMPT.format(text=text_sample)
    
    try:
        if provider == "gemini":
            result = _call_gemini(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt=ANALYSIS_SYSTEM_PROMPT)
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
        prompt = QUESTION_CLASSIFY_PROMPT.format(question=q[:500])  # limit question length
        
        try:
            if provider == "gemini":
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


# ===== API Call Helpers =====

def _call_gemini(prompt: str, system_prompt: str = "", model: str = "gemini-2.5-flash") -> str:
    """Call Google Gemini API"""
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        raise RuntimeError("Gemini not available")
    
    model_obj = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt if system_prompt else None
    )
    
    response = model_obj.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            max_output_tokens=2000,
        )
    )
    
    return response.text


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
        temperature=0.1,
        max_tokens=2000
    )
    
    return response.choices[0].message['content']


# ===== Utility Functions =====

def _sample_text(text: str, max_chars: int = 3000) -> str:
    """Take strategic samples from text to fit token limits"""
    if len(text) <= max_chars:
        return text
    
    # Take beginning, middle, and end samples
    chunk_size = max_chars // 3
    start = text[:chunk_size]
    middle_pos = len(text) // 2 - chunk_size // 2
    middle = text[middle_pos:middle_pos + chunk_size]
    end = text[-chunk_size:]
    
    return f"{start}\n\n[...middle section...]\n\n{middle}\n\n[...]\n\n{end}"


def _extract_json(text: str) -> Dict:
    """Extract and parse JSON from AI response"""
    # Try to find JSON in response
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Fallback: try to parse entire response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse JSON from AI response")
        return {}


def get_available_providers() -> List[str]:
    """Return list of available AI providers"""
    providers = []
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        providers.append("gemini")
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        providers.append("openai")
    providers.append("basic")  # Always available
    return providers


def get_ai_status() -> Dict:
    """Return status of AI integrations"""
    return {
        "gemini_available": GEMINI_AVAILABLE and bool(GEMINI_API_KEY),
        "openai_available": OPENAI_AVAILABLE and bool(OPENAI_API_KEY),
        "default_provider": DEFAULT_PROVIDER,
        "available_providers": get_available_providers()
    }
"""
AI-powered analysis utilities for Paper Analyzer
Supports Groq (recommended, free & fast), Google Gemini, and OpenAI APIs
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
ANALYSIS_SYSTEM_PROMPT = """You are an expert educational content analyzer specializing in exam paper analysis. 
Your task is to identify academic chapters, subjects, and key topics from exam questions accurately.

Focus on:
- Technical and academic concepts like "Binary Search", "Photosynthesis", "Newton's Laws"
- Multi-word phrases that represent specific topics
- Subject-specific vocabulary and named theories

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


# ===== AI Analysis Functions =====

def analyze_chapters_ai(text: str, provider: str = None, sample_size: int = 12000) -> Dict:
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
        if provider == "groq":
            result = _call_groq(prompt, system_prompt="")
        elif provider == "gemini":
            result = _call_gemini(prompt, system_prompt="")  # NO SYSTEM PROMPT
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt="")  # NO SYSTEM PROMPT
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
            logger.warning(f"⚠️ Gemini safety filter triggered - falling back to basic analysis")
            # Return empty so fallback analysis can be used
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
            result = _call_gemini(prompt, system_prompt="")  # NO SYSTEM PROMPT
        elif provider == "openai":
            result = _call_openai(prompt, system_prompt="")  # NO SYSTEM PROMPT
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
            logger.warning(f"⚠️ Gemini safety filter triggered - falling back to basic analysis")
            # Return empty so fallback analysis can be used
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
        prompt = QUESTION_CLASSIFY_PROMPT.format(question=q[:500])  # limit question length
        
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
        temperature=0.1,
        max_tokens=2000,
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
            temperature=0.1,
            max_output_tokens=2000,
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
        temperature=0.1,
        max_tokens=2000
    )
    
    return response.choices[0].message['content']


# ===== Utility Functions =====

def _sample_text(text: str, max_chars: int = 12000) -> str:
    """Sample text from ENTIRE document to catch all subjects (Physics, Chemistry, Biology)"""
    if not text:
        return ""
    
    # For papers with multiple subjects, we need samples from BEGINNING, MIDDLE, and END
    text_len = len(text)
    
    if text_len <= max_chars:
        # Small enough to send whole thing
        return text
    
    # Take samples from different sections to catch all subjects
    chunk_size = max_chars // 3  # Divide into 3 parts
    
    # Beginning (first subject - usually Physics)
    beginning = text[:chunk_size]
    
    # Middle (second subject - usually Chemistry)  
    middle_start = text_len // 2 - chunk_size // 2
    middle = text[middle_start:middle_start + chunk_size]
    
    # End (third subject - usually Biology)
    end = text[-chunk_size:]
    
    # Combine all three sections
    combined = beginning + "\n\n[... middle section ...]\n\n" + middle + "\n\n[... end section ...]\n\n" + end
    
    return combined[:max_chars]
    cleaned = re.sub(r'[^\w\s\.\,\?\!\-\:\;\(\)]', '', cleaned)
    
    # Trim to max length
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "..."
    
    return cleaned


def _extract_json(text: str) -> Dict:
    """Extract and parse JSON from AI response, handling markdown code blocks"""
    # Strip markdown code blocks if present (```json ... ``` or ``` ... ```)
    cleaned_text = text.strip()
    
    # Remove markdown code fences
    if cleaned_text.startswith('```'):
        # Find the end of the opening fence
        first_newline = cleaned_text.find('\n')
        if first_newline != -1:
            cleaned_text = cleaned_text[first_newline + 1:]
        
        # Remove closing fence
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
    
    # Try to parse cleaned text directly
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in text
    json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Last resort: try original text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
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
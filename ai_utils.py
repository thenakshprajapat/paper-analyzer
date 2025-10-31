import os
import time
from typing import List, Dict, Tuple

try:
    import openai
except Exception:
    openai = None

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Prompt template to ask the model to classify a question into a chapter and give topics.
CLASSIFY_PROMPT = """
You are a helpful assistant that maps exam questions to chapters and topics.

Chapters: Mathematics, Physics, Chemistry, Biology, Computer Science, English, History, Geography

For the input question, respond with a JSON object with keys:
- chapter: one of the Chapters above or "Unknown"
- topics: a short list of 1-4 topic keywords (comma-separated array)
- confidence: estimated confidence as a number between 0 and 1

Question:
\"\"\"{question}\"\"\"
"""

def classify_questions_llm(questions: List[str], model: str = "gpt-3.5-turbo", max_tokens: int = 300) -> List[Dict]:
    """
    Classify a batch of questions using the OpenAI Chat API (or similar).
    Returns list of dicts with keys: chapter, topics (list), confidence (float).
    Fallbacks to simple outputs if openai not available.
    """
    # Fallback if openai not configured
    if openai is None or OPENAI_API_KEY is None:
        # return lightweight heuristic fallback
        return [{"chapter": "Unknown", "topics": [], "confidence": 0.0} for _ in questions]

    results = []
    # Batch each question individually (simpler). You can batch multiple questions in a single prompt to save tokens.
    for q in questions:
        prompt = CLASSIFY_PROMPT.format(question=q)
        try:
            # Use chat completions if available
            if model.startswith("gpt-4") or model.startswith("gpt-3.5") or model.startswith("gpt-4o"):
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role":"system","content":"You are an expert at mapping exam questions to chapters and topics."},
                              {"role":"user","content":prompt}],
                    temperature=0.0,
                    max_tokens=max_tokens
                )
                text = resp.choices[0].message['content'].strip()
            else:
                resp = openai.Completion.create(
                    model=model,
                    prompt=prompt,
                    temperature=0.0,
                    max_tokens=max_tokens
                )
                text = resp.choices[0].text.strip()

            # Try to parse JSON from the model output, be tolerant
            import json, re
            # locate JSON object in output
            m = re.search(r'(\{[\s\S]*\})', text)
            if m:
                j = json.loads(m.group(1))
            else:
                # naive parse: expect lines like "chapter: X", "topics: a, b"
                j = {"chapter": "Unknown", "topics": [], "confidence": 0.0}
                for line in text.splitlines():
                    if ':' not in line: continue
                    k, v = line.split(':', 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k.startswith("chapter"):
                        j["chapter"] = v
                    elif k.startswith("topics"):
                        j["topics"] = [t.strip() for t in v.split(',') if t.strip()]
                    elif k.startswith("confidence"):
                        try: j["confidence"] = float(v)
                        except: pass

            # Normalize
            if isinstance(j.get("topics"), str):
                j["topics"] = [t.strip() for t in j["topics"].split(',') if t.strip()]
            j.setdefault("confidence", 0.0)
            j.setdefault("chapter", "Unknown")
            results.append(j)
            # a short delay to avoid rate limiting if needed
            time.sleep(0.2)
        except Exception as e:
            # on error, append fallback
            results.append({"chapter": "Unknown", "topics": [], "confidence": 0.0})
    return results
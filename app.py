from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from collections import Counter
import os
from werkzeug.utils import secure_filename
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import AI utilities
try:
    from ai_utils import (
        analyze_chapters_ai, 
        extract_topics_ai, 
        get_ai_status,
        DEFAULT_PROVIDER
    )
    AI_ENABLED = True
except ImportError as e:
    logging.warning(f"AI utilities not available: {e}")
    AI_ENABLED = False

# --- App setup (must be defined before route decorators) ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log AI status
if AI_ENABLED:
    ai_status = get_ai_status()
    logger.info(f"AI Status: {ai_status}")
    logger.info(f"Using provider: {DEFAULT_PROVIDER}")
else:
    logger.warning("AI features disabled - using basic keyword matching only")

# Config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max during debugging

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helpers ---
CHAPTER_KEYWORDS = {
    'Mathematics': ['algebra', 'calculus', 'geometry', 'trigonometry', 'statistics', 'probability'],
    'Physics': ['mechanics', 'thermodynamics', 'optics', 'electromagnetism', 'waves', 'quantum'],
    'Chemistry': ['organic', 'inorganic', 'physical chemistry', 'chemical bonding', 'equilibrium'],
    'Biology': ['cell', 'genetics', 'evolution', 'ecology', 'physiology', 'botany', 'zoology'],
    'Computer Science': ['programming', 'algorithms', 'data structures', 'database', 'networks', 'operating system'],
    'English': ['grammar', 'comprehension', 'literature', 'writing', 'vocabulary'],
    'History': ['ancient', 'medieval', 'modern', 'civilization', 'revolution', 'war'],
    'Geography': ['physical geography', 'human geography', 'climate', 'maps', 'resources']
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using PyPDF2. Returns string or raises."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return '\n'.join(text_parts)
    except Exception as e:
        logger.exception("PDF text extraction failed for %s", pdf_path)
        raise

def identify_questions(text):
    """Identify questions in the text (best-effort)"""
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
            end = min(len(text), start + 400)  # grab a larger context
            question_text = text[start:end].strip()
            questions.append(question_text)
    if questions:
        return questions
    # fallback: split by lines and return non-empty lines
    return [line.strip() for line in text.splitlines() if line.strip()]

def analyze_chapters(text):
    text_lower = text.lower()
    chapter_counts = {}
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower))
        if count:
            chapter_counts[chapter] = count
    return dict(sorted(chapter_counts.items(), key=lambda x: x[1], reverse=True))

def extract_topics(text):
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
                  'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
                  'why', 'how', 'question', 'answer', 'marks', 'write', 'explain'}
    words = re.findall(r'\b[a-z]{3,}\b', (text or '').lower())
    filtered = [w for w in words if w not in stop_words]
    counts = Counter(filtered)
    return dict(counts.most_common(20))

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai-status')
def ai_status_route():
    """Endpoint to check AI integration status"""
    if AI_ENABLED:
        status = get_ai_status()
        return jsonify(status)
    else:
        return jsonify({
            'gemini_available': False,
            'openai_available': False,
            'default_provider': 'basic',
            'available_providers': ['basic']
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.debug("Received upload request. Headers: %s", dict(request.headers))
        if not request.files:
            logger.warning("No files in request.files. form keys: %s", request.form.keys())
            return jsonify({'error': 'No files found in request. Make sure the request uses multipart/form-data.'}), 400

        if 'file' not in request.files:
            logger.warning("Key 'file' not present in request.files. Keys: %s", list(request.files.keys()))
            return jsonify({'error': "Upload key must be named 'file'."}), 400

        file = request.files['file']
        if file.filename == '':
            logger.warning("Empty filename")
            return jsonify({'error': 'No file selected.'}), 400

        if not allowed_file(file.filename):
            logger.warning("Disallowed file type: %s", file.filename)
            return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info("Saved uploaded file to %s", filepath)

        # Extract and analyze
        text = extract_text_from_pdf(filepath)
        questions = identify_questions(text)
        
        # Use AI-powered analysis if available, otherwise fall back to basic keyword matching
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'
        
        if AI_ENABLED and use_ai:
            logger.info(f"Using AI-powered analysis with provider: {DEFAULT_PROVIDER}")
            try:
                # AI-powered chapter and topic analysis
                ai_chapters = analyze_chapters_ai(text)
                ai_topics = extract_topics_ai(text)
                
                # Convert AI results to match expected format
                chapters = ai_chapters.get('chapters', {})
                topics = ai_topics
                
                # If AI didn't find much, supplement with basic analysis
                if len(chapters) < 2:
                    logger.info("AI found few chapters, supplementing with basic analysis")
                    basic_chapters = analyze_chapters(text)
                    for ch, count in basic_chapters.items():
                        if ch not in chapters:
                            chapters[ch] = count
                
                if len(topics) < 5:
                    logger.info("AI found few topics, supplementing with basic analysis")
                    basic_topics = extract_topics(text)
                    for topic, count in basic_topics.items():
                        if topic not in topics:
                            topics[topic] = count
                
                analysis_method = f"ai_{DEFAULT_PROVIDER}"
            except Exception as e:
                logger.exception("AI analysis failed, falling back to basic analysis")
                chapters = analyze_chapters(text)
                topics = extract_topics(text)
                analysis_method = "basic_fallback"
        else:
            # Basic keyword-based analysis
            logger.info("Using basic keyword-based analysis")
            chapters = analyze_chapters(text)
            topics = extract_topics(text)
            analysis_method = "basic"

        # cleanup
        try:
            os.remove(filepath)
        except Exception:
            logger.debug("Could not remove temp file %s", filepath)

        return jsonify({
            'success': True,
            'total_questions': len(questions),
            'chapters': chapters,
            'topics': topics,
            'sample_questions': questions[:5],
            'analysis_method': analysis_method,  # Let frontend know which method was used
            'ai_available': AI_ENABLED
        })
    except Exception as e:
        logger.exception("Unexpected error during upload")
        return jsonify({'error': 'Server error: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
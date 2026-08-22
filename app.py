from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
from collections import Counter
import os
from werkzeug.utils import secure_filename
import logging
from dotenv import load_dotenv

# Safe PyPDF2 import
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

# Load environment variables from .env file
load_dotenv()

# Import AI utilities
try:
    from ai_utils import (
        analyze_chapters_ai, 
        extract_topics_ai, 
        craft_high_probability_questions,
        get_ai_status,
        DEFAULT_PROVIDER
    )
    AI_ENABLED = True
except ImportError as e:
    logging.warning(f"AI utilities not available: {e}")
    AI_ENABLED = False

# Import PDF extraction with OCR if available
try:
    from pdf_extractor import extract_structured_questions, extract_text_with_ocr, PDF_OCR_AVAILABLE
except ImportError:
    PDF_OCR_AVAILABLE = False
    extract_structured_questions = None
    extract_text_with_ocr = None

# --- App setup ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helpers ---
CHAPTER_KEYWORDS = {
    'Mathematics': ['algebra', 'calculus', 'geometry', 'trigonometry', 'statistics', 'probability'],
    'Physics': ['mechanics', 'thermodynamics', 'optics', 'electromagnetism', 'waves', 'quantum'],
    'Chemistry': ['organic', 'inorganic', 'physical chemistry', 'chemical bonding', 'equilibrium'],
    'Biology': ['cell', 'genetics', 'evolution', 'ecology', 'physiology', 'botany', 'zoology'],
    'Computer Science': ['programming', 'algorithms', 'data structures', 'database', 'networks', 'operating system', 'python', 'sql'],
    'English': ['grammar', 'comprehension', 'literature', 'writing', 'vocabulary'],
    'History': ['ancient', 'medieval', 'modern', 'civilization', 'revolution', 'war'],
    'Geography': ['physical geography', 'human geography', 'climate', 'maps', 'resources']
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using PyPDF2 or OCR fallback."""
    try:
        if PDF_OCR_AVAILABLE and extract_text_with_ocr:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            ocr_text = extract_text_with_ocr(pdf_bytes, use_ocr=True)
            if ocr_text and len(ocr_text.strip()) > 100:
                return ocr_text

        if PYPDF2_AVAILABLE and PyPDF2 is not None:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return '\n'.join(text_parts)
        return ""
    except Exception as e:
        logger.exception("PDF text extraction failed for %s", pdf_path)
        raise

def identify_questions(text):
    """Identify questions in the text with structured extraction or regex fallback."""
    if extract_structured_questions:
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
            question_text = text[start:end].strip()
            questions.append(question_text)
    if questions:
        return questions
    return [line.strip() for line in text.splitlines() if len(line.strip()) > 20]

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
            'groq_available': False,
            'gemini_available': False,
            'openai_available': False,
            'default_provider': 'basic',
            'available_providers': ['basic']
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if not request.files or 'file' not in request.files:
            return jsonify({'error': "Upload key must be named 'file'."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info("Saved uploaded file to %s", filepath)

        # Extract and analyze
        text = extract_text_from_pdf(filepath)
        questions = identify_questions(text)
        
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'
        primary_subject = "General Science"
        
        if AI_ENABLED and use_ai:
            try:
                ai_chapters = analyze_chapters_ai(text)
                ai_topics = extract_topics_ai(text)
                
                chapters = ai_chapters.get('chapters', {})
                primary_subject = ai_chapters.get('primary_subject', 'General Science')
                topics = ai_topics
                
                if len(chapters) < 2:
                    basic_chapters = analyze_chapters(text)
                    for ch, count in basic_chapters.items():
                        if ch not in chapters:
                            chapters[ch] = count
                
                if len(topics) < 5:
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
            chapters = analyze_chapters(text)
            topics = extract_topics(text)
            analysis_method = "basic"

        if chapters and primary_subject == "General Science":
            primary_subject = list(chapters.keys())[0]

        # Craft High-Probability Predicted Exam Questions
        predicted_result = craft_high_probability_questions(
            text=text,
            chapters=chapters,
            topics=topics,
            sample_questions=questions[:6],
            primary_subject=primary_subject,
            provider=DEFAULT_PROVIDER if (AI_ENABLED and use_ai) else 'basic',
            num_questions=8
        )

        # cleanup
        try:
            os.remove(filepath)
        except Exception:
            pass

        return jsonify({
            'success': True,
            'total_questions': len(questions),
            'chapters': chapters,
            'topics': topics,
            'primary_subject': primary_subject,
            'predicted_questions': predicted_result.get('questions', []),
            'average_probability': predicted_result.get('average_probability', 90),
            'total_predicted_marks': predicted_result.get('total_predicted_marks', 40),
            'top_predicted_topics': predicted_result.get('top_predicted_topics', []),
            'sample_questions': questions[:5],
            'analysis_method': analysis_method,
            'ai_available': AI_ENABLED
        })
    except Exception as e:
        logger.exception("Unexpected error during upload")
        return jsonify({'error': 'Server error: ' + str(e)}), 500

if __name__ == '__main__':
    # use_reloader=False prevents watchdog on Windows from rebooting server mid-upload
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
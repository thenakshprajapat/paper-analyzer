from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from collections import Counter
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Common chapter keywords for identification
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
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() or ''
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def identify_questions(text):
    """Identify questions in the text"""
    # Pattern to match question numbers like "Q1.", "1)", "Question 1:", etc.
    question_patterns = [
        r'Q\s*\d+[\.\):]',
        r'Question\s*\d+[\.\):]',
        r'^\d+[\.\)]',
        r'\n\d+[\.\)]'
    ]
    
    questions = []
    for pattern in question_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            start = match.start()
            # Get context around the question (next 200 characters)
            end = min(start + 200, len(text))
            question_text = text[start:end]
            questions.append(question_text.strip())
    
    return questions if questions else [line.strip() for line in text.split('\n') if line.strip()]

def analyze_chapters(text):
    """Analyze which chapters appear most frequently"""
    text_lower = text.lower()
    chapter_counts = {}
    
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower))
        if count > 0:
            chapter_counts[chapter] = count
    
    return dict(sorted(chapter_counts.items(), key=lambda x: x[1], reverse=True))

def extract_topics(text):
    """Extract common topics/keywords from the text"""
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
                  'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
                  'why', 'how', 'question', 'answer', 'marks', 'write', 'explain'}
    
    # Extract words (3+ characters)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower() or '')
    
    # Filter out stop words
    filtered_words = [word for word in words if word not in stop_words]
    
    # Count frequency
    word_counts = Counter(filtered_words)
    
    # Return top 20 topics
    return dict(word_counts.most_common(20))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract and analyze
        text = extract_text_from_pdf(filepath)
        questions = identify_questions(text)
        chapters = analyze_chapters(text)
        topics = extract_topics(text)
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'total_questions': len(questions),
            'chapters': chapters,
            'topics': topics,
            'sample_questions': questions[:5]  # First 5 questions as samples
        })
    
    return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

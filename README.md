# 📄 Paper Analyzer - AI-Powered Exam Paper Analysis

Analyze exam papers with AI to identify chapters, topics, and question patterns. **NOW with OCR support for image-heavy PDFs!**

## ✨ Features

- 📚 **Chapter Detection**: Automatically identify covered chapters
- 🔍 **Topic Extraction**: Find key topics and concepts  
- 🖼️ **OCR Support**: Extract text from Physics diagrams, Chemistry structures, scanned documents
- 🤖 **AI-Powered**: Google Gemini API for accurate analysis
- 📊 **Visual Analytics**: Interactive Plotly charts
- 🔄 **Batch Processing**: Analyze multiple papers at once

## 🚀 Quick Start

### 1. Install Python Packages

```bash
git clone https://github.com/thenakshprajapat/paper-analyzer.git
cd paper-analyzer
pip install -r requirements.txt
```

### 2. Enable OCR (For Physics/Image-Heavy Papers)

**Install Poppler (PDF → Image):**
- Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/, extract, add `bin` folder to PATH
- Mac: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`

**Install Tesseract (OCR Engine):**
- Windows: Run `.\install_tesseract.ps1`
- Mac: `brew install tesseract`  
- Linux: `sudo apt-get install tesseract-ocr`

See [OCR_SETUP.md](OCR_SETUP.md) for details.

### 3. Add API Key (Optional)

```bash
cp .env.example .env
# Edit .env: GEMINI_API_KEY=your_key
```

Get free key: https://makersuite.google.com/app/apikey

### 4. Run

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501

## 📖 Usage

1. Upload PDF exam papers
2. Enable AI analysis (checkbox)
3. Click "🔍 Analyze Papers"
4. View chapters, topics, and insights!

## 🖼️ Why OCR?

Physics, Chemistry, and scanned papers have **images with embedded questions**. PyPDF2 misses these. OCR extracts text from images!

**Status:**
- 🔍 Green "OCR Enabled" = Full support
- 📝 Blue "OCR Disabled" = Text-only (install Poppler + Tesseract)

## 🐛 Troubleshooting

**"Poppler not installed"**  
→ Install Poppler, add to PATH

**"Tesseract not found"**  
→ Run `.\install_tesseract.ps1` (Windows) or install via brew/apt

**"Could not parse JSON"**  
→ ✅ Fixed! Enhanced JSON extraction

**Slow processing?**  
→ OCR takes 2-5 sec/page (normal for image processing)

## 📊 Performance

| Paper Type | Without OCR | With OCR |
|-----------|-------------|----------|
| Text PDFs | ✅ 1-2s | ✅ 1-2s |
| Image-heavy (Physics) | ❌ Incomplete | ✅ 5-10s |
| Scanned docs | ❌ Empty | ✅ 10-20s |

## 🛠️ Tech Stack

- Streamlit + Flask
- PyPDF2 + pdf2image + Tesseract (OCR)
- Google Gemini AI / OpenAI
- Plotly charts

## 👤 Author

**Naksh Prajapat**  
GitHub: [@thenakshprajapat](https://github.com/thenakshprajapat)

---

Made with ❤️ for smarter studying!
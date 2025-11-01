# OCR Setup for Image-Heavy PDFs

## Why OCR?
Physics papers, chemistry papers, and other technical documents often contain:
- **Diagrams and images** with embedded questions
- **Charts and graphs** 
- **Mathematical equations** as images
- **Scanned documents**

PyPDF2 alone cannot extract text from these images. OCR (Optical Character Recognition) solves this!

## Installation

### 1. Install Python Packages ✅
```bash
pip install pdf2image pytesseract pillow
```

### 2. Install Poppler (PDF → Image Conversion)

Poppler is required to convert PDF pages to images for OCR processing.

#### Windows:
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Download the latest release (e.g., `Release-24.08.0-0.zip`)
3. Extract to `C:\poppler` (or any location)
4. Add `C:\poppler\Library\bin` to your PATH:
   - Open System Properties → Environment Variables
   - Edit "Path" variable
   - Add: `C:\poppler\Library\bin`
5. Restart terminal

#### Mac:
```bash
brew install poppler
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install poppler-utils
```

**Verify Installation:**
```bash
pdftoppm -v
```

### 3. Install Tesseract OCR Engine

#### Windows:
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)
3. During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)
4. Add Tesseract to your PATH or it will be auto-detected by `pdf_extractor.py`

**Or use PowerShell script:**
```powershell
.\install_tesseract.ps1
```

#### Mac:
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr
```

**Verify Installation:**
```bash
tesseract --version
```

You should see output like:
```
tesseract 5.3.3
```

## How It Works

1. **Text-based pages**: PyPDF2 extracts text normally (fast)
2. **Image-heavy pages**: Automatically detected (< 50 chars of text)
3. **OCR processing**: Converts page to image → Runs OCR → Extracts text
4. **Hybrid approach**: Combines both methods for best results

## Performance

- **Without OCR**: Misses content in images (incomplete analysis)
- **With OCR**: Complete text extraction, but slower (2-5 seconds per page)
- **Smart hybrid**: Only uses OCR on pages that need it

## Testing

Upload a physics paper with diagrams to test OCR:
```bash
streamlit run streamlit_app.py
```

Look for the green banner: "🔍 **OCR Enabled**"

## Troubleshooting

### "Tesseract not found"
- Windows: Add `C:\Program Files\Tesseract-OCR` to PATH
- Or set path in code: `pytesseract.pytesseract.tesseract_cmd = r'C:\...\tesseract.exe'`

### Poor OCR quality
- Increase DPI in `pdf_extractor.py`: `convert_from_bytes(pdf_bytes, dpi=300)` → `dpi=600`
- Clean up images before OCR (future enhancement)

### Slow processing
- OCR is CPU-intensive (2-5 sec/page is normal)
- Consider processing in background/async (future enhancement)

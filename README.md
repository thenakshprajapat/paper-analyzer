# 📄 Paper Analyzer# 📄 Paper Analyzer<!-- # 📄 Paper Analyzer



An intelligent PDF paper analysis tool powered by AI that extracts chapters, topics, and provides detailed insights from academic papers. Built with **Streamlit** for an interactive UI and **Google Gemini AI** for precise analysis.



## ✨ FeaturesA web application that helps students analyze exam papers to identify frequently tested chapters and topics using AI-powered analysis.A web application that helps students analyze exam papers to identify frequently tested chapters and topics.



- 📤 **PDF Upload**: Upload academic papers in PDF format

- 🤖 **AI-Powered Analysis**: Uses Google Gemini 2.5 Flash for accurate chapter and topic extraction

- 📊 **Interactive Visualizations**: Beautiful charts powered by Plotly## ✨ Features## Features

- 🎯 **Topic Detection**: Automatically identifies key topics and concepts

- 📖 **Chapter Recognition**: Detects paper structure and chapter organization

- 💾 **Batch Processing**: Analyze multiple files at once

- 🔄 **Fallback Support**: Graceful degradation to keyword matching if AI is unavailable- 📤 Upload exam papers (PDF format, up to 32MB)- 📤 Upload exam papers (PDF format)

- 🌐 **Dual Interface**: Modern Streamlit UI + Flask API backend

- 🤖 **AI-powered analysis** using Google Gemini or OpenAI for precise chapter and topic detection- 🔍 Extract text from PDFs and parse questions

## 🚀 Quick Start

- 🔍 Smart text extraction from PDFs- 🤖 Optional AI-enhanced classification (chapter/topic extraction using OpenAI)

### Prerequisites

- 📊 Analyze question distribution by chapters and topics- 📊 Analyze question distribution by chapters and topics

- Python 3.8 or higher

- Google Gemini API key (free tier available)- 🎯 Identify most frequently tested topics with confidence scores- 🎯 Show most frequently tested topics and sample questions



### Installation- 📈 Interactive charts with Chart.js- 📈 Interactive charts and responsive UI



1. **Clone the repository**- 💡 Automatic fallback to keyword-based analysis if AI is unavailable

   ```bash

   git clone https://github.com/thenakshprajapat/paper-analyzer.git---

   cd paper-analyzer

   ```---



2. **Create virtual environment**## Quick Start (local)

   ```bash

   python -m venv .venv## 🚀 Quick Start

   

   # Windows1. Clone the repository:

   .venv\Scripts\activate

   ### 1. Clone the repository

   # Linux/Mac

   source .venv/bin/activate```bash

   ```

```bashgit clone https://github.com/thenakshprajapat/paper-analyzer.git

3. **Install dependencies**

   ```bashgit clone https://github.com/thenakshprajapat/paper-analyzer.gitcd paper-analyzer

   pip install -r requirements.txt

   ```cd paper-analyzer```



4. **Set up API keys**```

   

   Create a `.env` file in the root directory:2. (Optional) Create and activate a virtual environment:

   ```env

   GEMINI_API_KEY=your_gemini_api_key_here### 2. Create and activate a virtual environment (recommended)

   OPENAI_API_KEY=your_openai_api_key_here  # Optional

   ```- macOS / Linux:

   

   **Get your free Gemini API key:****Windows (PowerShell):**  ```bash

   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

   - Sign in with your Google account```powershell  python3 -m venv venv

   - Click "Create API Key"

   - Copy and paste into `.env` filepython -m venv venv  source venv/bin/activate



5. **Run the application**.\venv\Scripts\Activate.ps1  ```



   **Option A: Streamlit (Recommended)**```

   ```bash

   streamlit run streamlit_app.py- Windows (PowerShell):

   ```

   Open http://localhost:8501 in your browser**macOS / Linux:**  ```powershell



   **Option B: Flask API**```bash  python -m venv venv

   ```bash

   python app.pypython3 -m venv venv  .\venv\Scripts\Activate.ps1

   ```

   API available at http://localhost:5000source venv/bin/activate  ```



## 📖 Usage Guide```



### Using Streamlit Interface3. Install Python dependencies:



1. **Open the app** at http://localhost:8501### 3. Install dependencies

2. **Check AI status** in the sidebar (should show ✅ Google Gemini: Active)

3. **Upload PDF(s)** using the file uploader```bash

4. **Enable AI analysis** checkbox (checked by default)

5. **Click "Analyze Papers"** button```bashpython -m pip install -r requirements.txt

6. **View results** with interactive charts and detailed breakdowns

pip install -r requirements.txt```

### Using Flask API

```

**Upload and analyze a PDF:**

```bash4. Run the app:

curl -X POST -F "file=@paper.pdf" http://localhost:5000/upload

```### 4. Set up AI API keys (Recommended for best results)



**Check AI status:**```bash

```bash

curl http://localhost:5000/ai-status#### Option A: Google Gemini (Recommended - Free Tier Available)python app.py

```

```

**Response format:**

```json1. Get your free API key from: https://makersuite.google.com/app/apikey

{

  "chapters": [2. Copy `.env.example` to `.env`:5. Open your browser at:

    {

      "chapter": "Introduction",   ```bash

      "topics": ["Background", "Motivation", "Objectives"],

      "confidence": 0.95   cp .env.example .envhttp://localhost:5000

    }

  ],   ```

  "topics": {

    "Machine Learning": 0.92,3. Edit `.env` and add your Gemini API key:---

    "Neural Networks": 0.88

  },   ```

  "analysis_method": "AI (gemini)",

  "filename": "paper.pdf"   GEMINI_API_KEY=your_actual_api_key_here## API / Upload endpoint

}

```   ```



## 🏗️ Project Structure- POST /upload (multipart/form-data, field name: file)  



```**Why Gemini?**- Accepts: PDF files  

paper-analyzer/

├── streamlit_app.py       # Streamlit UI (main interface)- ✅ Free tier with 60 requests/minute- Response (JSON):

├── app.py                 # Flask API backend

├── ai_utils.py            # AI integration layer (Gemini + OpenAI)- ✅ Excellent for educational content analysis  - success: true/false

├── requirements.txt       # Python dependencies

├── .env                   # API keys (create this)- ✅ Fast and accurate  - total_questions: integer

├── .env.example          # API key template

├── .gitignore            # Git ignore rules- ✅ No credit card required for free tier  - chapters_heuristic / chapters_ai: object mapping chapter -> count (if AI enabled)

├── uploads/              # Uploaded PDFs (auto-created)

├── templates/            # Flask HTML templates  - topics_heuristic / topics_ai: object mapping topic -> count (if AI enabled)

│   └── index.html

└── .streamlit/           # Streamlit configuration#### Option B: OpenAI (Optional)  - sample_questions: array of extracted question snippets

    └── config.toml

```  - ai_sample_classification: array of AI classifications (if AI enabled)



## 🔧 Configuration1. Get your API key from: https://platform.openai.com/api-keys



### Streamlit Settings2. Add to `.env`:Use the UI or curl to upload:



Edit `.streamlit/config.toml`:   ```

```toml

[theme]   OPENAI_API_KEY=sk-your_actual_api_key_here```bash

primaryColor = "#FF4B4B"

backgroundColor = "#0E1117"   ```curl -F "file=@/path/to/paper.pdf" http://localhost:5000/upload

secondaryBackgroundColor = "#262730"

textColor = "#FAFAFA"```



[server]**Note:** OpenAI requires payment after free trial credits are exhausted.

maxUploadSize = 200

enableXsrfProtection = true---

```

#### Option C: No API (Basic Mode)

### AI Provider Settings

## AI Integration (Optional)

The application automatically detects available AI providers in this order:

1. **Google Gemini** (Primary, free tier: 60 req/min)The app works without any API keys using keyword-based analysis, but results will be less precise.

2. **OpenAI** (Fallback, requires paid API key)

3. **Basic** (Keyword matching, no API needed)This project includes an optional AI step that can improve chapter/topic detection using an LLM (OpenAI in the example). The AI is not required — the app has a heuristic keyword-based fallback.



You can configure the provider in `ai_utils.py`:### 5. Run the application

```python

DEFAULT_PROVIDER = "gemini"  # or "openai"To enable AI features:

```

```bash

## 🤖 AI Models Supported

python app.py1. Set your OpenAI API key in the environment:

### Google Gemini

- **Model**: `gemini-2.5-flash````

- **Rate Limits**: 60 requests/min, 1,500/day (free tier)

- **Cost**: Free tier available- macOS / Linux:

- **Best for**: Fast, accurate analysis with generous limits

### 6. Open in browser  ```bash

### OpenAI (Optional)

- **Model**: `gpt-3.5-turbo` or `gpt-4`  export OPENAI_API_KEY="sk-..."

- **Cost**: Pay per token

- **Best for**: Advanced reasoning, longer documentsNavigate to: **http://localhost:5000**  ```



## 📊 Features Breakdown



### Chapter Detection---- Windows (PowerShell):

- Identifies paper structure (Introduction, Methods, Results, etc.)

- Provides confidence scores for each detection  ```powershell

- Handles various academic paper formats

## 🔧 How It Works  $env:OPENAI_API_KEY = "sk-..."

### Topic Extraction

- Extracts key concepts and themes  ```

- Ranks topics by relevance

- Supports technical and domain-specific terminology### Analysis Methods



### Visualizations2. The backend will read OPENAI_API_KEY and call the AI classifier when available. AI classification is batched and returned under `chapters_ai`, `topics_ai`, and `ai_sample_classification` in the POST /upload response.

- **Bar Chart**: Top topics by relevance score

- **Pie Chart**: Chapter distributionThe application automatically selects the best available analysis method:

- **Table View**: Detailed chapter-topic breakdown

Costs & notes:

## 🛠️ Development

1. **AI-Powered (Gemini/OpenAI)** - Most accurate- Calls to the LLM (and embeddings if enabled) will incur API usage costs. Use a cheaper model (e.g., gpt-3.5-turbo) for lower cost.

### Running in Development Mode

   - Uses large language models to understand context- Consider adding caching for repeated uploads or hashed file fingerprints to avoid duplicate charges.

**Streamlit with auto-reload:**

```bash   - Identifies chapters with confidence scores

streamlit run streamlit_app.py --server.runOnSave true

```   - Extracts specific, relevant topics---



**Flask with debug mode:**   - Understands question intent and subject matter

```bash

set FLASK_ENV=development  # Windows## Frontend

export FLASK_ENV=development  # Linux/Mac

python app.py2. **Keyword-Based (Fallback)** - Basic but functional

```

   - Searches for predefined chapter keywords- The UI (templates/index.html) lets users upload papers and view analysis charts.

### Testing AI Integration

   - Word frequency analysis for topics- Chart.js is used for visualization.

Test Gemini API:

```python   - No API keys required- The frontend shows heuristic results by default and can be extended to show AI-labeled results (a toggle can be added in the UI to prefer AI output).

python -c "from ai_utils import get_ai_status; print(get_ai_status())"

```



Expected output:### API Endpoints---

```python

{

  'gemini_available': True,

  'openai_available': False,#### `POST /upload`## Development notes

  'default_provider': 'gemini'

}Upload and analyze exam papers

```

- app.py contains the Flask server and analysis logic.

## 🐛 Troubleshooting

**Request:**- templates/index.html contains the UI. Static assets can be added under `static/`.

### "AI utilities not found" Error

- **Cause**: Missing dependencies or incorrect imports- Content-Type: `multipart/form-data`- Text extraction uses PyPDF2. If you need OCR for scanned PDFs, add pytesseract and Pillow and detect pages with no extracted text.

- **Fix**: Run `pip install -r requirements.txt`

- Field name: `file`- To avoid "Request Entity Too Large" errors, check app.config['MAX_CONTENT_LENGTH'] in app.py and any proxy (nginx) client_max_body_size.

### "404 models/gemini-pro not found" Error

- **Cause**: Outdated model name- File type: PDF

- **Fix**: Check that `ai_utils.py` uses `gemini-2.5-flash`

- Optional: `use_ai=true/false` (default: true)---

### Upload Failures

- **Cause**: Relative path issues or missing uploads folder

- **Fix**: Folder is auto-created; check file permissions

**Response:**## Docker (optional)

### API Rate Limits

- **Gemini free tier**: 60 requests/min, 1,500/day```json

- **Solution**: Add delays between requests or upgrade to paid tier

{You can containerize the app by creating a Dockerfile and exposing port 5000. Keep environment variables (OPENAI_API_KEY) out of image builds and pass them at runtime.

## 📦 Dependencies

  "success": true,

Core libraries:

- `streamlit>=1.28.0` - Interactive web UI  "total_questions": 25,---

- `flask>=3.0.0` - REST API backend

- `pypdf2>=3.0.1` - PDF text extraction  "chapters": {

- `plotly>=5.17.0` - Interactive charts

- `google-generativeai>=0.3.0` - Gemini AI integration    "Physics": 0.95,## Troubleshooting

- `openai>=1.3.0` - OpenAI integration (optional)

- `python-dotenv>=1.0.0` - Environment variables    "Mathematics": 0.87



See `requirements.txt` for complete list.  },- If uploads return 405 Method Not Allowed, ensure you're POSTing to /upload (trailing slash differences may matter); app.url_map.strict_slashes can be set to be tolerant.



## 🤝 Contributing  "topics": {- If Chart.js shows client-side errors, open DevTools → Console and Network to inspect script loading and responses.



We welcome contributions! Here's how to get started:    "Thermodynamics": 0.92,- If PyPDF2 extracts no text (scanned PDFs), enable OCR (pytesseract).



1. **Fork the repository**    "Quadratic Equations": 0.88

2. **Create a feature branch**

   ```bash  },---

   git checkout -b feature/amazing-feature

   ```  "sample_questions": ["Q1. Explain...", "..."],

3. **Make your changes**

4. **Test thoroughly**  "analysis_method": "ai_gemini",## Contributing

   - Test with different PDF formats

   - Verify AI integration works  "ai_available": true

   - Check both Streamlit and Flask interfaces

5. **Commit your changes**}PRs welcome. Please create branches for feature work and open pull requests. Add tests where appropriate.

   ```bash

   git commit -m "Add amazing feature"```

   ```

6. **Push to your fork**---

   ```bash

   git push origin feature/amazing-feature#### `GET /ai-status`

   ```

7. **Open a Pull Request**Check AI integration status## License



### Code Style

- Follow PEP 8 guidelines

- Add docstrings to functions**Response:**MIT License -->

- Include comments for complex logic```json

- Update README for new features{

  "gemini_available": true,

### Testing Checklist  "openai_available": false,

- [ ] PDF upload works in Streamlit  "default_provider": "gemini",

- [ ] AI analysis returns accurate results  "available_providers": ["gemini", "basic"]

- [ ] Flask API endpoints respond correctly}

- [ ] Charts display properly```

- [ ] Error handling works (try invalid files)

- [ ] Fallback works when AI is disabled---



## 📝 License## 📚 Project Structure



This project is licensed under the MIT License - see the LICENSE file for details.```

paper-analyzer/

## 🙏 Acknowledgments├── app.py                  # Flask application & routes

├── ai_utils.py            # AI integration (Gemini/OpenAI)

- Google Gemini AI for powerful analysis capabilities├── requirements.txt       # Python dependencies

- Streamlit for the amazing UI framework├── .env.example          # Environment variables template

- Flask for the robust backend├── .env                  # Your API keys (create this, not in git)

- PyPDF2 for PDF processing├── templates/

- Plotly for beautiful visualizations│   └── index.html        # Frontend UI

├── uploads/              # Temporary upload directory

## 🔗 Links└── README.md            # This file

```

- **Repository**: https://github.com/thenakshprajapat/paper-analyzer

- **Issues**: https://github.com/thenakshprajapat/paper-analyzer/issues---

- **Gemini API**: https://makersuite.google.com/app/apikey

- **Streamlit Docs**: https://docs.streamlit.io## 🔑 Environment Variables



## 💡 Future EnhancementsCreate a `.env` file in the project root:



- [ ] OCR support for scanned PDFs```bash

- [ ] Question difficulty estimation# Google Gemini API (Recommended)

- [ ] Export results to JSON/CSVGEMINI_API_KEY=your_gemini_api_key_here

- [ ] Batch processing history

- [ ] Custom topic dictionaries# OpenAI API (Optional)

- [ ] Multi-language supportOPENAI_API_KEY=your_openai_api_key_here

- [ ] Paper comparison tool```

- [ ] Citation extraction

---

## 📧 Contact

## 🧪 Testing with curl

**Naksh Prajapat**

- GitHub: [@thenakshprajapat](https://github.com/thenakshprajapat)```bash

# Upload a PDF

---curl -F "file=@/path/to/exam.pdf" http://localhost:5000/upload



Made with ❤️ by Naksh Prajapat# Check AI status

curl http://localhost:5000/ai-status
```

---

## 💡 Tips & Best Practices

1. **API Costs:**
   - Gemini: Free tier is generous (60 req/min)
   - OpenAI: Costs ~$0.002 per analysis with gpt-3.5-turbo
   - Consider caching results for duplicate uploads

2. **Improving Accuracy:**
   - Use AI mode for best results
   - Ensure PDFs have extractable text (not scanned images)
   - Upload complete exam papers for better context

3. **Performance:**
   - First upload may be slower as AI initializes
   - Large PDFs (>10 pages) are sampled strategically
   - Results are cached during the session

4. **Privacy:**
   - Files are deleted immediately after analysis
   - Text is sent to AI providers (Gemini/OpenAI) for analysis
   - Don't upload sensitive/confidential exams if concerned

---

## 🐛 Troubleshooting

### "Failed to upload file"
- Check file size (max 32MB)
- Ensure file is a valid PDF
- Check browser console (F12) for detailed errors

### AI not working
- Verify API key is set in `.env`
- Check `/ai-status` endpoint
- View server logs for error messages
- Ensure you have internet connection

### No text extracted from PDF
- PDF may be scanned images (OCR not yet implemented)
- Try a different PDF with selectable text
- Check server logs for PyPDF2 errors

### Import errors
- Make sure you installed all dependencies: `pip install -r requirements.txt`
- Try: `pip install --upgrade google-generativeai openai python-dotenv`

---

## 🚢 Deployment

### Docker (Coming Soon)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Environment Variables in Production
- Never commit `.env` to git
- Use platform-specific secrets management (Heroku Config Vars, AWS Secrets Manager, etc.)
- Set `FLASK_ENV=production` in production

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] Batch upload multiple papers
- [ ] Save analysis history
- [ ] Compare multiple papers
- [ ] Export results to PDF/Excel
- [ ] Support for more file formats (DOCX, images)
- [ ] Question difficulty estimation
- [ ] Study plan recommendations

---

## 📄 License

MIT License - feel free to use this project for learning and teaching!

---

## 🙏 Acknowledgments

- Google Gemini API for powerful free-tier AI
- OpenAI for GPT models
- PyPDF2 for PDF text extraction
- Chart.js for beautiful visualizations
- Flask for the web framework

---

## 📧 Support

If you encounter issues:
1. Check this README's troubleshooting section
2. Review server logs in the terminal
3. Open an issue on GitHub with details

---

**Made with ❤️ for students to study smarter, not harder!**

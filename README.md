# 📄 Paper Analyzer

A web application that helps students analyze exam papers to identify frequently tested chapters and topics.

## Features

- 📤 Upload exam papers (PDF format)
- 🔍 Extract text from PDFs and parse questions
- 🤖 Optional AI-enhanced classification (chapter/topic extraction using OpenAI)
- 📊 Analyze question distribution by chapters and topics
- 🎯 Show most frequently tested topics and sample questions
- 📈 Interactive charts and responsive UI

---

## Quick Start (local)

1. Clone the repository:

```bash
git clone https://github.com/thenakshprajapat/paper-analyzer.git
cd paper-analyzer
```

2. (Optional) Create and activate a virtual environment:

- macOS / Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- Windows (PowerShell):
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

3. Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Run the app:

```bash
python app.py
```

5. Open your browser at:

http://localhost:5000

---

## API / Upload endpoint

- POST /upload (multipart/form-data, field name: file)  
- Accepts: PDF files  
- Response (JSON):
  - success: true/false
  - total_questions: integer
  - chapters_heuristic / chapters_ai: object mapping chapter -> count (if AI enabled)
  - topics_heuristic / topics_ai: object mapping topic -> count (if AI enabled)
  - sample_questions: array of extracted question snippets
  - ai_sample_classification: array of AI classifications (if AI enabled)

Use the UI or curl to upload:

```bash
curl -F "file=@/path/to/paper.pdf" http://localhost:5000/upload
```

---

## AI Integration (Optional)

This project includes an optional AI step that can improve chapter/topic detection using an LLM (OpenAI in the example). The AI is not required — the app has a heuristic keyword-based fallback.

To enable AI features:

1. Set your OpenAI API key in the environment:

- macOS / Linux:
  ```bash
  export OPENAI_API_KEY="sk-..."
  ```

- Windows (PowerShell):
  ```powershell
  $env:OPENAI_API_KEY = "sk-..."
  ```

2. The backend will read OPENAI_API_KEY and call the AI classifier when available. AI classification is batched and returned under `chapters_ai`, `topics_ai`, and `ai_sample_classification` in the POST /upload response.

Costs & notes:
- Calls to the LLM (and embeddings if enabled) will incur API usage costs. Use a cheaper model (e.g., gpt-3.5-turbo) for lower cost.
- Consider adding caching for repeated uploads or hashed file fingerprints to avoid duplicate charges.

---

## Frontend

- The UI (templates/index.html) lets users upload papers and view analysis charts.
- Chart.js is used for visualization.
- The frontend shows heuristic results by default and can be extended to show AI-labeled results (a toggle can be added in the UI to prefer AI output).

---

## Development notes

- app.py contains the Flask server and analysis logic.
- templates/index.html contains the UI. Static assets can be added under `static/`.
- Text extraction uses PyPDF2. If you need OCR for scanned PDFs, add pytesseract and Pillow and detect pages with no extracted text.
- To avoid "Request Entity Too Large" errors, check app.config['MAX_CONTENT_LENGTH'] in app.py and any proxy (nginx) client_max_body_size.

---

## Docker (optional)

You can containerize the app by creating a Dockerfile and exposing port 5000. Keep environment variables (OPENAI_API_KEY) out of image builds and pass them at runtime.

---

## Troubleshooting

- If uploads return 405 Method Not Allowed, ensure you're POSTing to /upload (trailing slash differences may matter); app.url_map.strict_slashes can be set to be tolerant.
- If Chart.js shows client-side errors, open DevTools → Console and Network to inspect script loading and responses.
- If PyPDF2 extracts no text (scanned PDFs), enable OCR (pytesseract).

---

## Contributing

PRs welcome. Please create branches for feature work and open pull requests. Add tests where appropriate.

---

## License

MIT License
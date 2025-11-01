# 🚀 Groq AI Setup Guide (FREE & RECOMMENDED)

## Why Groq?

✅ **100% FREE** - No credit card required  
✅ **SUPER FAST** - Llama 3.1 70B inference  
✅ **NO SAFETY FILTERS** - Works with educational content  
✅ **14,400 requests/day** - Free tier is generous  

**Better than Gemini** which blocks educational content with safety filters!

---

## Quick Setup (5 minutes)

### Step 1: Get FREE API Key

1. Go to: **https://console.groq.com/keys**
2. Sign up with Google/GitHub (FREE, no credit card!)
3. Click **"Create API Key"**
4. Copy your API key (starts with `gsk_...`)

### Step 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your-api-key-here"
```

**Windows (Permanent):**
```powershell
[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'your-api-key-here', 'User')
```

**Mac/Linux:**
```bash
export GROQ_API_KEY="your-api-key-here"
```

**Or create `.env` file:**
```bash
GROQ_API_KEY=your-api-key-here
```

### Step 3: Restart Streamlit

```bash
streamlit run streamlit_app.py
```

---

## Verify It Works

1. Open http://localhost:8501
2. Sidebar should show: **"✅ Groq AI: Active (FREE & FAST!)"**
3. Upload a PDF - you'll get **REAL topic names** like:
   - ✅ "Electromagnetic Induction"
   - ✅ "Chemical Equilibrium"
   - ✅ "Skeletal System"
   
   NOT generic words like: ❌ "reaction", "energy", "field"

---

## Comparison

| Feature | Groq | Gemini | OpenAI |
|---------|------|--------|--------|
| **Cost** | FREE | FREE | PAID |
| **Speed** | ⚡⚡⚡ | ⚡⚡ | ⚡ |
| **Safety Filters** | ✅ Permissive | ❌ Blocks education | ✅ Permissive |
| **Free Requests/Day** | 14,400 | 1,500 | 0 |
| **Model** | Llama 3.1 70B | Gemini 2.5 Flash | GPT-3.5/4 |

---

## Troubleshooting

**"Groq not available" in sidebar:**
- Make sure you set `GROQ_API_KEY` environment variable
- Restart terminal/PowerShell after setting variable
- Restart Streamlit

**"Import groq could not be resolved":**
```bash
pip install groq
```

**Rate limit errors:**
- Groq free tier: 14,400 requests/day, 30 requests/minute
- This is plenty for personal use!

---

## Need Help?

- Groq Docs: https://console.groq.com/docs
- Issues: https://github.com/thenakshprajapat/paper-analyzer/issues

**Enjoy real AI analysis without safety filter headaches! 🎉**

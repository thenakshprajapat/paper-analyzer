# 🔧 Easy Installation Guide for OCR Support

## What You Need to Install:
1. **Poppler** - Converts PDF pages to images
2. **Tesseract** - Reads text from images (OCR)

---

## 🚀 OPTION 1: Automatic Installation (Easiest!)

### Run This Command in PowerShell:

```powershell
# Run as Administrator (Right-click PowerShell → Run as Administrator)
cd d:\paper-analyzer\paper-analyzer
.\install_both.ps1
```

This will automatically download and install both Poppler and Tesseract!

---

## 🔧 OPTION 2: Manual Installation (Step by Step)

### **Part A: Install Poppler**

#### Step 1: Download Poppler
1. Open browser: https://github.com/oschwartz10612/poppler-windows/releases/
2. Download: **Release-24.08.0-0.zip** (or latest version)
3. Save to Downloads folder

#### Step 2: Extract Poppler
1. Go to Downloads folder
2. Find the ZIP file (e.g., `Release-24.08.0-0.zip`)
3. Right-click → **Extract All**
4. Choose location: `C:\` (so it creates `C:\poppler-24.08.0`)
5. Click **Extract**

#### Step 3: Rename Folder (Optional)
1. Go to `C:\`
2. Rename `poppler-24.08.0` to just `poppler`
3. Now you have: `C:\poppler\`

#### Step 4: Add Poppler to PATH
1. Press **Windows Key**
2. Type: **"environment"**
3. Click: **"Edit the system environment variables"**
4. Click: **"Environment Variables"** button
5. Under **"User variables"**, find **"Path"**
6. Click **"Edit"**
7. Click **"New"**
8. Type: `C:\poppler\Library\bin`
9. Click **OK** → **OK** → **OK**

#### Step 5: Test Poppler
1. **Close PowerShell completely**
2. **Open new PowerShell**
3. Run: `pdftoppm -v`
4. Should show version info (e.g., "pdftoppm version 24.08.0")

✅ If you see version info → SUCCESS!  
❌ If "not recognized" → Check PATH and restart PowerShell

---

### **Part B: Install Tesseract**

#### Option B1: Automatic (Easiest)
```powershell
cd d:\paper-analyzer\paper-analyzer
.\install_tesseract.ps1
```

This downloads and runs the installer for you!

#### Option B2: Manual Download
1. Open browser: https://github.com/UB-Mannheim/tesseract/wiki
2. Download: **tesseract-ocr-w64-setup-5.3.3.20231005.exe**
3. Run the installer
4. During installation:
   - Keep default path: `C:\Program Files\Tesseract-OCR`
   - Check all language packs (or just English)
5. Click **Install**
6. Click **Finish**

#### Step 2: Add Tesseract to PATH (if not automatic)
1. Press **Windows Key**
2. Type: **"environment"**
3. Click: **"Edit the system environment variables"**
4. Click: **"Environment Variables"**
5. Under **"User variables"**, find **"Path"**
6. Click **"Edit"**
7. Click **"New"**
8. Type: `C:\Program Files\Tesseract-OCR`
9. Click **OK** → **OK** → **OK**

#### Step 3: Test Tesseract
1. **Close PowerShell completely**
2. **Open new PowerShell**
3. Run: `tesseract --version`
4. Should show: "tesseract 5.3.3"

✅ If you see version → SUCCESS!  
❌ If "not recognized" → Check PATH and restart PowerShell

---

## 🧪 Verify Everything Works

After installing both, run this test:

```powershell
# Test Poppler
pdftoppm -v

# Test Tesseract  
tesseract --version

# Start Streamlit
cd d:\paper-analyzer\paper-analyzer
streamlit run streamlit_app.py
```

You should see **green banner**: "🔍 OCR Enabled" in the web app!

---

## ❓ Troubleshooting

### Problem: "Command not recognized"
**Solution:** 
1. Make sure you added to PATH correctly
2. **Restart PowerShell** (must close and reopen!)
3. Check folder exists: `C:\poppler\Library\bin` and `C:\Program Files\Tesseract-OCR`

### Problem: Poppler shows error during extraction
**Solution:**
- Extract to different location like `D:\poppler`
- Update PATH to match: `D:\poppler\Library\bin`

### Problem: Tesseract installer won't run
**Solution:**
- Right-click installer → **Run as Administrator**
- Disable antivirus temporarily
- Download again (file might be corrupted)

### Problem: Still not working after PATH update
**Solution:**
1. **Restart entire computer** (PATH changes sometimes need full restart)
2. Check PATH was saved: 
   ```powershell
   $env:Path -split ';' | Select-String poppler
   $env:Path -split ';' | Select-String Tesseract
   ```

---

## 📝 Quick Checklist

- [ ] Downloaded Poppler ZIP
- [ ] Extracted to `C:\poppler`
- [ ] Added `C:\poppler\Library\bin` to PATH
- [ ] Tested: `pdftoppm -v` works
- [ ] Downloaded Tesseract installer
- [ ] Installed Tesseract to `C:\Program Files\Tesseract-OCR`
- [ ] Added `C:\Program Files\Tesseract-OCR` to PATH
- [ ] Tested: `tesseract --version` works
- [ ] Restarted PowerShell
- [ ] Streamlit shows "OCR Enabled" ✅

---

Need help? Open an issue on GitHub!
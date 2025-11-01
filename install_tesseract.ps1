# Quick Install Script for Tesseract OCR on Windows
# Run this script to download and install Tesseract

Write-Host "🔍 Installing Tesseract OCR for Windows..." -ForegroundColor Cyan

# Download URL for Tesseract Windows installer
$tesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = "$env:TEMP\tesseract-setup.exe"

Write-Host "📥 Downloading Tesseract installer..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✅ Download complete!" -ForegroundColor Green
    
    Write-Host "`n🚀 Starting installation..." -ForegroundColor Yellow
    Write-Host "   ⚠️  During installation, please note the installation path!" -ForegroundColor Yellow
    Write-Host "   📝 Default path: C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
    
    # Run installer
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "`n✅ Installation complete!" -ForegroundColor Green
    
    # Check if installed
    $tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
    if (Test-Path $tesseractPath) {
        Write-Host "✅ Tesseract found at: $tesseractPath" -ForegroundColor Green
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $tesseractDir = "C:\Program Files\Tesseract-OCR"
        
        if ($currentPath -notlike "*$tesseractDir*") {
            Write-Host "📝 Adding Tesseract to PATH..." -ForegroundColor Yellow
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$tesseractDir", "User")
            Write-Host "✅ Added to PATH! Restart terminal to use 'tesseract' command" -ForegroundColor Green
        }
        
        # Test installation
        Write-Host "`n🧪 Testing Tesseract..." -ForegroundColor Yellow
        & $tesseractPath --version
        
        Write-Host "`n✨ Setup complete! OCR is ready to use!" -ForegroundColor Green
        Write-Host "   🔄 Restart your terminal/IDE for PATH changes to take effect" -ForegroundColor Cyan
        Write-Host "   🚀 Run: streamlit run streamlit_app.py" -ForegroundColor Cyan
        
    } else {
        Write-Host "⚠️  Tesseract not found at expected location" -ForegroundColor Yellow
        Write-Host "   Please check the installation path and update pdf_extractor.py if needed" -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item $installerPath -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "`n📖 Manual installation:" -ForegroundColor Yellow
    Write-Host "   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Write-Host "   2. Run the installer" -ForegroundColor Cyan
    Write-Host "   3. Add to PATH: C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

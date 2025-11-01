# 🚀 Automatic Installer for Poppler + Tesseract
# Run this script to install both OCR dependencies automatically

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  OCR Setup for Paper Analyzer" -ForegroundColor Cyan
Write-Host "  Installing Poppler + Tesseract" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some operations may fail. Consider running as Admin." -ForegroundColor Yellow
    Write-Host ""
}

# ============================================
# PART 1: Install Poppler
# ============================================

Write-Host "📦 PART 1: Installing Poppler..." -ForegroundColor Green
Write-Host ""

$popplerInstallPath = "C:\poppler"
$popplerZipUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$popplerZipPath = "$env:TEMP\poppler.zip"

try {
    # Download Poppler
    Write-Host "📥 Downloading Poppler..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $popplerZipUrl -OutFile $popplerZipPath -UseBasicParsing
    Write-Host "✅ Downloaded!" -ForegroundColor Green
    
    # Extract Poppler
    Write-Host "📂 Extracting to $popplerInstallPath..." -ForegroundColor Yellow
    if (Test-Path $popplerInstallPath) {
        Write-Host "   ⚠️  Folder already exists, removing old version..." -ForegroundColor Yellow
        Remove-Item -Path $popplerInstallPath -Recurse -Force
    }
    
    Expand-Archive -Path $popplerZipPath -DestinationPath "C:\" -Force
    
    # Rename folder to simple name
    $extractedFolder = Get-ChildItem "C:\poppler-*" | Select-Object -First 1
    if ($extractedFolder) {
        Rename-Item -Path $extractedFolder.FullName -NewName "poppler" -Force
    }
    
    Write-Host "✅ Poppler extracted to $popplerInstallPath" -ForegroundColor Green
    
    # Add to PATH
    $popplerBinPath = "$popplerInstallPath\Library\bin"
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    if ($currentPath -notlike "*$popplerBinPath*") {
        Write-Host "📝 Adding Poppler to PATH..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$popplerBinPath", "User")
        $env:Path = "$env:Path;$popplerBinPath"  # Update current session
        Write-Host "✅ Added to PATH!" -ForegroundColor Green
    } else {
        Write-Host "✅ Already in PATH!" -ForegroundColor Green
    }
    
    # Cleanup
    Remove-Item $popplerZipPath -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "✨ Poppler installation complete!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ Error installing Poppler: $_" -ForegroundColor Red
    Write-Host ""
}

# ============================================
# PART 2: Install Tesseract
# ============================================

Write-Host "📦 PART 2: Installing Tesseract..." -ForegroundColor Green
Write-Host ""

$tesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$tesseractInstallerPath = "$env:TEMP\tesseract-setup.exe"

try {
    # Download Tesseract
    Write-Host "📥 Downloading Tesseract installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $tesseractUrl -OutFile $tesseractInstallerPath -UseBasicParsing
    Write-Host "✅ Downloaded!" -ForegroundColor Green
    
    # Run installer
    Write-Host ""
    Write-Host "🚀 Starting Tesseract installer..." -ForegroundColor Yellow
    Write-Host "   📝 IMPORTANT: During installation:" -ForegroundColor Cyan
    Write-Host "   1. Keep default path: C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
    Write-Host "   2. Select language packs (English is enough)" -ForegroundColor Cyan
    Write-Host "   3. Complete the installation wizard" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key when ready to start installer..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    Start-Process -FilePath $tesseractInstallerPath -Wait
    
    Write-Host "✅ Tesseract installer completed!" -ForegroundColor Green
    
    # Add to PATH
    $tesseractPath = "C:\Program Files\Tesseract-OCR"
    if (Test-Path $tesseractPath) {
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        
        if ($currentPath -notlike "*$tesseractPath*") {
            Write-Host "📝 Adding Tesseract to PATH..." -ForegroundColor Yellow
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$tesseractPath", "User")
            $env:Path = "$env:Path;$tesseractPath"  # Update current session
            Write-Host "✅ Added to PATH!" -ForegroundColor Green
        } else {
            Write-Host "✅ Already in PATH!" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  Tesseract not found at expected location" -ForegroundColor Yellow
        Write-Host "   If you installed to a different location, add it to PATH manually" -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item $tesseractInstallerPath -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "✨ Tesseract installation complete!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ Error installing Tesseract: $_" -ForegroundColor Red
    Write-Host ""
}

# ============================================
# VERIFICATION
# ============================================

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  🧪 Testing Installation" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Refresh PATH for current session
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")

Write-Host "Testing Poppler..." -ForegroundColor Yellow
try {
    $popplerTest = & pdftoppm -v 2>&1
    if ($LASTEXITCODE -eq 0 -or $popplerTest) {
        Write-Host "✅ Poppler: WORKING" -ForegroundColor Green
        Write-Host "   Version: $($popplerTest[0])" -ForegroundColor Gray
    } else {
        throw "Command failed"
    }
} catch {
    Write-Host "❌ Poppler: NOT FOUND" -ForegroundColor Red
    Write-Host "   You may need to restart PowerShell" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Testing Tesseract..." -ForegroundColor Yellow
try {
    $tesseractTest = & tesseract --version 2>&1
    if ($LASTEXITCODE -eq 0 -or $tesseractTest) {
        Write-Host "✅ Tesseract: WORKING" -ForegroundColor Green
        Write-Host "   Version: $($tesseractTest[0])" -ForegroundColor Gray
    } else {
        throw "Command failed"
    }
} catch {
    Write-Host "❌ Tesseract: NOT FOUND" -ForegroundColor Red
    Write-Host "   You may need to restart PowerShell" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  ✨ Installation Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Close this PowerShell window" -ForegroundColor White
Write-Host "2. Open a NEW PowerShell window (to reload PATH)" -ForegroundColor White
Write-Host "3. Run: cd d:\paper-analyzer\paper-analyzer" -ForegroundColor White
Write-Host "4. Run: streamlit run streamlit_app.py" -ForegroundColor White
Write-Host "5. Look for green '🔍 OCR Enabled' banner!" -ForegroundColor White
Write-Host ""
Write-Host "🎉 You're ready to analyze image-heavy PDFs!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Paper Analyzer - Quick Setup Script
# Run this after installing requirements.txt

Write-Host "🚀 Paper Analyzer - Quick Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
} else {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env and add your API keys" -ForegroundColor Yellow
    } else {
        Write-Host "❌ .env.example not found" -ForegroundColor Red
    }
}

Write-Host ""

# Check Python packages
Write-Host "🔍 Checking installed packages..." -ForegroundColor Cyan

$packages = @("flask", "google-generativeai", "openai", "python-dotenv")
$missingPackages = @()

foreach ($package in $packages) {
    $installed = python -m pip show $package 2>$null
    if ($installed) {
        Write-Host "  ✅ $package" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $package (missing)" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Missing packages detected. Install with:" -ForegroundColor Yellow
    Write-Host "   pip install -r requirements.txt" -ForegroundColor White
}

Write-Host ""

# Check uploads directory
if (-not (Test-Path "uploads")) {
    Write-Host "📁 Creating uploads directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "✅ Created uploads directory" -ForegroundColor Green
} else {
    Write-Host "✅ uploads directory exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env and add your API keys (recommended)" -ForegroundColor White
Write-Host "     Get free Gemini API: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "  2. Run: python app.py" -ForegroundColor White
Write-Host "  3. Open: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Check AI status: http://localhost:5000/ai-status" -ForegroundColor Gray
Write-Host ""

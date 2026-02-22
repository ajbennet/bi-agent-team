# Run Streamlit Web App for Multi-Agent SaaS Metrics Analyzer
# PowerShell version

Write-Host ""
Write-Host "🚀 Multi-Agent SaaS Metrics Analyzer - Web App" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Create it with: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Check if API key is set
if (-not $env:DEEPSEEK_API_KEY) {
    Write-Host ""
    Write-Host "ERROR: DEEPSEEK_API_KEY not set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Set it with:" -ForegroundColor Yellow
    Write-Host '  $env:DEEPSEEK_API_KEY="sk-your-key-here"' -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Launching Streamlit Web App..." -ForegroundColor Green
Write-Host "Browser will open at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run streamlit
streamlit run app.py --logger.level=error --client.showErrorDetails=false

Write-Host "Web app stopped." -ForegroundColor Yellow

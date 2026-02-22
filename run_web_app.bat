@echo off
REM Run Streamlit Web App for Multi-Agent SaaS Metrics Analyzer
REM Make sure to set DEEPSEEK_API_KEY environment variable first

setlocal enabledelayedexpansion

REM Check if venv is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if API key is set
if not defined DEEPSEEK_API_KEY (
    echo.
    echo ERROR: DEEPSEEK_API_KEY environment variable not set!
    echo.
    echo Set it with:
    echo   set DEEPSEEK_API_KEY=sk-your-key-here
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo.
echo Launching Streamlit Web App...
echo Browser will open at: http://localhost:8501
echo.
echo To stop: Press Ctrl+C
echo.

streamlit run app.py --logger.level=error --client.showErrorDetails=false

pause

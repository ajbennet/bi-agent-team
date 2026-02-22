# SaaS Metrics Analyzer - Setup Guide

A multi-agent system that analyzes SaaS metrics using LangGraph + DeepSeek V3 API. Ask questions about your data and get SQL queries, visualizations, and business insights instantly.

## Quick Start (5 minutes)

### 1. Get API Key
1. Go to https://platform.deepseek.com/api_keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Set Up Environment
```powershell
# Navigate to workspace
cd C:\Users\abina\workspace\Tutorials\Deepseek\bi-agent-team

# Create virtual environment (one time only)
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies (one time only)
pip install -r requirements.txt
```

### 3. Run the Web App
```powershell
# Set your API key
$env:DEEPSEEK_API_KEY="sk-your-key-here"

# Start the web app
.\venv\Scripts\streamlit run app.py
```

Browser opens automatically at http://localhost:8501

## System Overview

### What It Does
- **SQL Agent**: Generates and executes SQL queries on your SaaS database
- **Viz Agent**: Creates interactive Plotly charts from query results
- **Insights Agent**: Generates business recommendations from data

### How It Works
1. You ask a question in natural language
2. Multi-agent workflow processes it (10-20 seconds)
3. Results display in tabs: Chart | SQL | Insights | Data

### Database
Uses SQLite database (`saas_metrics.db`) with 3 tables:
- `users` - User info including acquisition channel
- `subscriptions` - Subscription status and dates
- `app_events` - Activity events and timestamps

## Project Files

### Core System
- **langgraph_system.py** (530 lines) - Multi-agent orchestration engine
  - `sql_agent()` - SQL query generation and execution
  - `viz_agent()` - Chart creation
  - `insights_agent()` - Business analysis
  - `analyze_question()` - Main entry point

- **app.py** (375 lines) - Streamlit web interface
  - Session state management for persistence
  - Interactive text input and analysis button
  - Results display with tabs and metrics
  - Error handling and debugging UI

### Supporting Files
- **requirements.txt** - Python dependencies (langgraph, streamlit, plotly, pandas, etc.)
- **saas_metrics.db** - SQLite database with sample data
- **output_chart.html** - Generated chart (auto-opens in browser)

### Launcher Scripts
- **run_app.py** - Python launcher (use if .ps1 doesn't work)
- **run_web_app.bat** - Windows batch launcher
- **run_web_app.ps1** - PowerShell launcher
- **test_setup.py** - Verify environment is working (4 tests)

## Troubleshooting

### API Key Issues
```powershell
# Check if key is set
$env:DEEPSEEK_API_KEY

# If empty, set it again
$env:DEEPSEEK_API_KEY="sk-your-key-here"

# Or set permanently (Windows)
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-your-key-here", "User")
```

### Streamlit Won't Start
```powershell
# Kill any existing process
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force

# Try again
$env:DEEPSEEK_API_KEY="sk-..."; .\venv\Scripts\streamlit run app.py
```

### Analysis Hangs or Fails
1. Check internet connection (DeepSeek API needs it)
2. Verify database exists: `saas_metrics.db` 
3. Check terminal for error messages
4. Use simpler questions first (e.g., "How many users do we have?")
5. Run test: `python test_setup.py` (all 4 tests should pass)

### Unicode/Emoji Issues (Windows)
Already handled - system auto-detects and adjusts for Windows PowerShell

## Database Schema

Quick reference for queries:

**users table**
- `user_id` - Primary key
- `acquisition_channel` - 'Organic', 'Ads', 'Referral'
- `signup_date` - When user joined
- `country` - User location

**subscriptions table**
- `subscription_id` - Primary key
- `user_id` - Foreign key
- `status` - 'active', 'canceled', 'churned'
- `start_date`, `end_date` - Subscription period

**app_events table**
- `event_id` - Primary key
- `user_id` - Foreign key
- `event_type` - 'login', 'feature_use', 'payment', etc.
- `timestamp` - When event occurred

## Example Questions

Try these to test:
- "How many users signed up last month?"
- "What is the churn rate by acquisition channel?"
- "Which countries have the most active users?"
- "Show me revenue trends over time"
- "What features are most used per user?"

## For Fresh Chat Sessions

When starting a new chat, share this context:

**System**: Multi-agent SaaS analyzer (LangGraph + DeepSeek V3 + Streamlit)
**Database**: SQLite with users, subscriptions, app_events
**Entry Point**: 
```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
$env:DEEPSEEK_API_KEY="sk-your-key"
.\venv\Scripts\streamlit run app.py
```
**Main Files**: langgraph_system.py (backend), app.py (web UI)

## Key Technologies

- **LangGraph 0.0.58** - Multi-agent workflow orchestration
- **DeepSeek V3** - Language model (via ChatOpenAI API)
- **Streamlit 1.31.1** - Web interface
- **SQLite** - Database
- **Plotly** - Interactive charts
- **Pandas** - Data manipulation

## Performance

- Analysis: 10-20 seconds per question (includes API calls + chart generation)
- Timeout: 45 seconds per analysis with 2 auto-retries
- Chart rendering: 1-3 seconds

---

**Need help?** Check terminal output or enable debug mode in the Debug Info section at bottom of sidebar in Streamlit app.

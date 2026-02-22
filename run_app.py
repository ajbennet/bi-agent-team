#!/usr/bin/env python
"""
Quick launcher for Streamlit Web App
Sets environment and runs the app
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    # Check for API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("\n❌ ERROR: DEEPSEEK_API_KEY environment variable not set!\n")
        print("Set it with one of these methods:\n")
        print("PowerShell:")
        print("  $env:DEEPSEEK_API_KEY=\"sk-your-key-here\"\n")
        print("CMD:")
        print("  set DEEPSEEK_API_KEY=sk-your-key-here\n")
        print("Or permanently:")
        print("  [Environment]::SetEnvironmentVariable(\"DEEPSEEK_API_KEY\", \"sk-...\", \"User\")\n")
        return 1
    
    # Check for app.py
    if not Path('app.py').exists():
        print("❌ ERROR: app.py not found!")
        print("Run from: c:\\Users\\abina\\workspace\\Tutorials\\Deepseek\\bi-agent-team\\")
        return 1
    
    # Print startup message
    print("\n" + "="*70)
    print("🚀 LAUNCHING STREAMLIT WEB APP")
    print("="*70)
    print("\n📊 Multi-Agent SaaS Metrics Analyzer")
    print("   Powered by LangGraph + DeepSeek V3\n")
    print("⏳ Launching server (this takes ~5 seconds)...")
    print("🌐 Browser will open at: http://localhost:8501\n")
    print("💭 First analysis will take 10-20 seconds\n")
    print("❌ To stop: Press Ctrl+C\n")
    print("="*70 + "\n")
    
    # Run streamlit
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--logger.level=error",
            "--client.showErrorDetails=false"
        ]
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n👋 Web app stopped.")
    except Exception as e:
        print(f"\n❌ Error running Streamlit: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

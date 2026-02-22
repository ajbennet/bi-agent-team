"""
Test Script for LangGraph Multi-Agent System
Verifies database connection, API keys, and agent functionality
"""

import os
import sqlite3
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def test_environment():
    """Test environment variables"""
    print_header("1. TESTING ENVIRONMENT")
    
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY not set")
        print("   Set it with: $env:DEEPSEEK_API_KEY='your-key'")
        return False
    
    print("✓ DEEPSEEK_API_KEY is set")
    return True

def test_database():
    """Test database connection"""
    print_header("2. TESTING DATABASE")
    
    if not Path('saas_metrics.db').exists():
        print("❌ Database 'saas_metrics.db' not found")
        return False
    
    try:
        conn = sqlite3.connect('saas_metrics.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if not tables:
            print("❌ Database has no tables")
            return False
        
        print(f"✓ Database connected with {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        return True
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_imports():
    """Test required imports"""
    print_header("3. TESTING IMPORTS")
    
    packages = {
        "langchain_openai": "LangChain OpenAI",
        "langgraph": "LangGraph",
        "pandas": "Pandas",
        "plotly": "Plotly",
    }
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} not installed: pip install {package}")
            all_ok = False
    
    return all_ok

def test_llm():
    """Test LLM connection"""
    print_header("4. TESTING LLM CONNECTION")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage
        
        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com",
            temperature=0.1,
            timeout=30,
            max_retries=1
        )
        
        print("Testing API connection with simple query...")
        response = llm.invoke([SystemMessage(content="Say 'Hello' in one word.")])
        
        if response.content:
            print(f"✓ LLM responded: {response.content[:50]}")
            return True
        else:
            print("❌ LLM returned empty response")
            return False
    
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  LANGGRAPH SYSTEM SETUP VERIFICATION")
    print("="*60)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database),
        ("Imports", test_imports),
        ("LLM API", test_llm),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    print_header("SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All checks passed! You can run: python langgraph_system.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

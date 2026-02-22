"""
Lightweight Multi-Agent System for SaaS Metrics Analysis
Uses sequential agent calls without LanGraph for faster execution
"""

import os
import sqlite3
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Initialize DeepSeek LLM
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1,
)

def get_schema():
    """Fetch database schema"""
    conn = sqlite3.connect('saas_metrics.db')
    cursor = conn.cursor()
    
    schema = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = [col[1] for col in columns]
    
    conn.close()
    return schema

def sql_agent(question: str, schema: dict) -> tuple[str, str]:
    """SQL Agent: Generates and executes SQL queries"""
    print("\n[SQL AGENT]")
    print(f"Question: {question}")
    
    schema_str = "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema.items()])
    
    prompt = f"""You are a SQL expert. Write a SQLite query to answer this question.

Database Schema:
{schema_str}

Question: {question}

Important:
- Use json_extract() for JSON fields
- Use proper JOINs
- Return ONLY the SQL query, nothing else"""
    
    response = llm.invoke([SystemMessage(content=prompt)])
    sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    
    # Execute query
    conn = sqlite3.connect('saas_metrics.db')
    try:
        df = pd.read_sql_query(sql, conn)
        result = df.to_json(orient='records')
        print(f"✓ Query executed, {len(df)} rows returned")
    except Exception as e:
        result = f"Error: {str(e)}"
        print(f"✗ Query failed: {e}")
    finally:
        conn.close()
    
    return sql, result

def viz_agent(data: str, question: str) -> str:
    """Visualization Agent: Generates Plotly code"""
    print("\n[VISUALIZATION AGENT]")
    
    prompt = f"""You are a Python data visualization expert.
Given this JSON data and question, write Plotly code to visualize it.

Data sample: {data[:500]}
Question: {question}

Requirements:
- Use plotly.express or plotly.graph_objects
- Create a meaningful chart
- Save to 'output_chart.html'
- Return ONLY Python code, nothing else"""
    
    response = llm.invoke([SystemMessage(content=prompt)])
    code = response.content.strip().replace("```python", "").replace("```", "").strip()
    
    # Try to execute
    try:
        namespace = {
            "pd": pd,
            "px": __import__("plotly.express"),
            "go": __import__("plotly.graph_objects"),
            "json": json,
        }
        exec(code, namespace)
        print("✓ Chart generated and saved to output_chart.html")
    except Exception as e:
        print(f"✗ Visualization error: {e}")
        code = f"# Error: {e}\n{code}"
    
    return code

def insights_agent(data: str, question: str) -> str:
    """Insights Agent: Analyzes results and provides recommendations"""
    print("\n[INSIGHTS AGENT]")
    
    prompt = f"""You are a business analyst. Analyze this data and provide insights.

Data: {data[:800]}
Question: {question}

Format your response as:
1. KEY FINDING: [main insight]
2. ANALYSIS: [deeper analysis]
3. RECOMMENDATION: [actionable recommendation]

Be concise and data-driven."""
    
    response = llm.invoke([SystemMessage(content=prompt)])
    insights = response.content.strip()
    print("✓ Insights generated")
    
    return insights

def analyze_question(question: str):
    """Main analysis pipeline"""
    print(f"\n{'='*70}")
    print(f"ANALYZING: {question}")
    print('='*70)
    
    schema = get_schema()
    
    # Stage 1: SQL Agent
    sql, data = sql_agent(question, schema)
    
    if "Error" in data:
        print("Cannot proceed - SQL execution failed")
        return
    
    # Stage 2: Visualization Agent
    code = viz_agent(data, question)
    
    # Stage 3: Insights Agent
    insights = insights_agent(data, question)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print(f"\n📊 SQL Query:\n{sql[:300]}...")
    print(f"\n📈 Visualization Code:\n{code[:300]}...")
    print(f"\n💡 Insights:\n{insights}")
    print('='*70)
    
    return {
        "question": question,
        "sql": sql,
        "visualization_code": code,
        "insights": insights
    }

if __name__ == "__main__":
    # Example questions
    questions = [
        "What is the churn rate by acquisition channel?",
        "Show me the revenue breakdown by plan type",
        "Which country has the most active users?"
    ]
    
    results = []
    for q in questions[0:1]:  # Start with just one question
        try:
            result = analyze_question(q)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing question: {e}")
    
    print(f"\n✓ Analysis complete! {len(results)} question(s) analyzed")

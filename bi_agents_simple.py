import os
import sqlite3
import json
import pandas as pd
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Setup DeepSeek V3
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1,
    timeout=60
)

class AgentState(TypedDict):
    question: str
    sql_query: str
    query_result: str
    python_code: str
    insights: str
    next_step: str

# Tool: Execute SQL
def run_sql(query: str) -> str:
    try:
        conn = sqlite3.connect('saas_metrics.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_json(orient='records')
    except Exception as e:
        return f"Error: {str(e)}"

# Agent 1: SQL Specialist
def sql_agent(state: AgentState):
    question = state["question"]
    
    # Get schema info
    conn = sqlite3.connect('saas_metrics.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema = "Tables: " + ", ".join([t[0] for t in tables])
    conn.close()
    
    prompt = f"""You are a SQL expert. Given this question and database schema, write a SQLite query.
    
    Schema: {schema}
    Question: {question}
    
    Important: Use json_extract() for metadata_json field. Use proper JOINs.
    Return ONLY the SQL query, nothing else."""
    
    print(f"[SQL Agent] Processing: {question[:60]}...")
    response = llm.invoke([SystemMessage(content=prompt)])
    sql = response.content.strip().replace("```sql", "").replace("```", "")
    
    print(f"[SQL Agent] Generated query:\n{sql[:200]}...")
    result = run_sql(sql)
    
    return {
        "sql_query": sql,
        "query_result": result,
        "next_step": "visualize" if "Error" not in result else "sql"
    }

# Agent 2: Visualization Specialist
def viz_agent(state: AgentState):
    data = state["query_result"]
    question = state["question"]
    
    prompt = f"""You are a Python data visualization expert. 
    Given this JSON data and the original question, write Python code using plotly to create a visualization.
    
    Data: {data[:1000]}
    Question: {question}
    
    Requirements:
    1. Use plotly.express
    2. Create a simple chart based on data
    3. Save to 'output_chart.html'
    
    Return ONLY the Python code, nothing else."""
    
    print(f"[VIZ Agent] Creating visualization...")
    response = llm.invoke([SystemMessage(content=prompt)])
    code = response.content.strip().replace("```python", "").replace("```", "")
    
    # Execute the code
    try:
        exec(code, {"plotly": __import__("plotly"), "pd": pd, 
                   "go": __import__("plotly.graph_objects"), "px": __import__("plotly.express")})
        print("[VIZ Agent] Chart saved to output_chart.html")
    except Exception as e:
        print(f"[VIZ Agent] Error: {str(e)}")
    
    return {
        "python_code": code,
        "next_step": "insights"
    }

# Agent 3: Insights Analyst
def insights_agent(state: AgentState):
    data = state["query_result"]
    question = state["question"]
    
    prompt = f"""You are a business analyst. Given this data and question, provide insights.
    
    Data: {data[:1000]}
    Question: {question}
    
    Format:
    1. Key Insight
    2. Recommendation
    
    Be concise."""
    
    print(f"[Insights Agent] Analyzing results...")
    response = llm.invoke([SystemMessage(content=prompt)])
    
    return {
        "insights": response.content,
        "next_step": "end"
    }

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("sql", sql_agent)
workflow.add_node("visualize", viz_agent)
workflow.add_node("insights", insights_agent)

workflow.set_entry_point("sql")
workflow.add_conditional_edges("sql", lambda x: x["next_step"], {"visualize": "visualize", "sql": "sql"})
workflow.add_edge("visualize", "insights")
workflow.add_edge("insights", END)

app = workflow.compile()

# Run function
def analyze(question: str):
    try:
        result = app.invoke({"question": question})
        print("\n=== SQL QUERY ===")
        print(result["sql_query"])
        print("\n=== INSIGHTS ===")
        print(result["insights"])
        return result
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    # Test with one simple question
    question = "What is the churn rate by plan type?"
    
    print(f"{'='*60}")
    print(f"QUESTION: {question}")
    print('='*60)
    analyze(question)

import os
import sqlite3
import json
from typing import Annotated, List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Setup DeepSeek V3
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1
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
    conn = sqlite3.connect('saas_metrics.db')
    try:
        df = pd.read_sql_query(query, conn)
        return df.to_json(orient='records')
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

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
    
    response = llm.invoke([SystemMessage(content=prompt)])
    sql = response.content.strip().replace("```sql", "").replace("```", "")
    
    # Execute the SQL
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
    
    Data: {data[:2000]}... (truncated)
    Question: {question}
    
    Requirements:
    1. Use plotly.graph_objects or plotly.express
    2. Create a meaningful chart (bar, line, heatmap based on data)
    3. Include proper titles and labels
    4. Save the figure to 'output_chart.html'
    
    Return ONLY the Python code, nothing else."""
    
    response = llm.invoke([SystemMessage(content=prompt)])
    code = response.content.strip().replace("```python", "").replace("```", "")
    
    # Execute the code
    try:
        exec(code, {"plotly": __import__("plotly"), "pd": __import__("pandas"), 
                   "go": __import__("plotly.graph_objects"), "px": __import__("plotly.express")})
        result = "Chart saved to output_chart.html"
    except Exception as e:
        result = f"Error executing code: {str(e)}"
    
    return {
        "python_code": code,
        "next_step": "insights"
    }

# Agent 3: Insights Analyst
def insights_agent(state: AgentState):
    data = state["query_result"]
    question = state["question"]
    
    prompt = f"""You are a business analyst. Given this data and question, provide 2-3 key insights.
    
    Data summary: {data[:1500]}...
    Question: {question}
    
    Format:
    1. Insight 1
    2. Insight 2
    3. Recommendation
    
    Be concise and actionable."""
    
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
    result = app.invoke({"question": question})
    print("\n=== SQL QUERY ===")
    print(result["sql_query"])
    print("\n=== PYTHON VIZ CODE ===")
    print(result["python_code"][:500] + "...")
    print("\n=== INSIGHTS ===")
    print(result["insights"])
    return result

if __name__ == "__main__":
    import pandas as pd  # Import here for exec context
    
    # Example complex questions
    questions = [
        "Calculate monthly retention rate by acquisition channel for the last 3 months",
        "What is the average latency by country, extracting from metadata_json?",
        "Show revenue churn by plan type, comparing active vs cancelled subscriptions"
    ]
    
    for q in questions:
        print(f"\n{'='*60}")
        print(f"QUESTION: {q}")
        print('='*60)
        analyze(q)

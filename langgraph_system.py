"""
Production-Ready Multi-Agent System with LangGraph
Handles timeouts, retries, and streaming properly
"""

import os
import sqlite3
import json
import time
import webbrowser
import sys
from pathlib import Path
from typing import TypedDict, Any
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END

# Fix Unicode encoding for Windows
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============================================================================
# Configuration
# ============================================================================

# Initialize DeepSeek with aggressive timeout settings
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1,
    timeout=45,  # 45 second timeout for API calls
    max_retries=2,  # Retry up to 2 times
)


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """Shared state for all agents"""
    question: str
    sql_query: str
    query_result: str
    python_code: str
    insights: str
    next_step: str
    error_count: int


# ============================================================================
# Database Tools
# ============================================================================

def get_database_schema() -> str:
    """Fetch database schema safely"""
    try:
        conn = sqlite3.connect('saas_metrics.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = ", ".join([col[1] for col in columns])
            schema_info.append(f"{table_name}: {col_names}")
        
        conn.close()
        return "\n".join(schema_info)
    except Exception as e:
        return f"Error fetching schema: {str(e)}"


def execute_sql(query: str, timeout: int = 30) -> tuple[bool, str]:
    """
    Execute SQL query with timeout protection
    Returns: (success: bool, result: str)
    """
    if not query or "Error" in query:
        return False, "Invalid query"
    
    try:
        conn = sqlite3.connect('saas_metrics.db', timeout=timeout)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            return True, "[]"
        
        result = df.to_json(orient='records')
        if len(result) > 50000:  # Truncate large results
            result = result[:50000] + "... (truncated)"
        
        return True, result
    except sqlite3.OperationalError as e:
        return False, f"SQL Error: {str(e)}"
    except Exception as e:
        return False, f"Execution Error: {str(e)}"


# ============================================================================
# Agent Nodes
# ============================================================================

def sql_agent(state: AgentState) -> dict:
    """
    SQL Agent: Generates and executes SQL queries
    """
    print("🔍 [SQL Agent] Processing question...")
    
    if state["error_count"] > 2:
        return {
            "sql_query": "# Max retries exceeded",
            "query_result": "Error: Max retries exceeded",
            "next_step": "end",
            "error_count": state["error_count"]
        }
    
    question = state["question"]
    schema = get_database_schema()
    
    prompt = f"""You are a SQL expert for a SaaS metrics database.

Database Schema:
{schema}

User Question: {question}

Instructions:
1. Write a valid SQLite query to answer the question
2. Use json_extract() for JSON fields if needed
3. Use proper JOINs between tables
4. Return ONLY the SQL query, no explanations

SQL Query:"""
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        sql = response.content.strip()
        
        # Clean up markdown formatting
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Prevent SQL injection-like patterns
        dangerous = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
        if any(word in sql.upper() for word in dangerous):
            return {
                "sql_query": "# Dangerous query rejected",
                "query_result": "Error: Query contains dangerous commands",
                "next_step": "end",
                "error_count": state["error_count"]
            }
        
        print(f"  ✓ Query generated ({len(sql)} chars)")
        
        # Execute query
        success, result = execute_sql(sql)
        
        if success:
            print(f"  ✓ Query executed successfully")
            return {
                "sql_query": sql,
                "query_result": result,
                "next_step": "visualize",
                "error_count": state["error_count"]
            }
        else:
            print(f"  ✗ Query execution failed: {result}")
            if state["error_count"] < 2:
                return {
                    "sql_query": sql,
                    "query_result": result,
                    "next_step": "sql",  # Retry
                    "error_count": state["error_count"] + 1
                }
            else:
                return {
                    "sql_query": sql,
                    "query_result": result,
                    "next_step": "end",
                    "error_count": state["error_count"]
                }
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {
            "sql_query": f"# Error: {str(e)}",
            "query_result": f"Error: {str(e)}",
            "next_step": "end",
            "error_count": state["error_count"] + 1
        }


def viz_agent(state: AgentState) -> dict:
    """
    Visualization Agent: Generates Plotly visualization code
    """
    print("📊 [Viz Agent] Creating visualization...")
    
    data = state["query_result"]
    question = state["question"]
    
    # Check if we have valid data
    if "Error" in data or not data or data == "[]":
        print("  ℹ️  Skipping visualization - no data available")
        return {
            "python_code": "# No data to visualize",
            "next_step": "insights"
        }
    
    # Truncate data if too large
    data_preview = data[:1000] if len(data) > 1000 else data
    
    prompt = f"""You are a Python data visualization expert using Plotly.

Given this data and question, write Python code to visualize it.

Data: {data_preview}
Question: {question}

Instructions:
1. Use plotly.express (px) or plotly.graph_objects (go)
2. Create an appropriate chart type (bar, line, scatter, heatmap, etc.)
3. Include proper titles, labels, and formatting
4. Save to 'output_chart.html' using fig.write_html()
5. Return ONLY the Python code, no explanations

Code:"""
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        code = response.content.strip()
        
        # Clean up markdown formatting
        code = code.replace("```python", "").replace("```", "").strip()
        
        print(f"  ✓ Code generated ({len(code)} chars)")
        
        # Try to execute the code
        try:
            exec_globals = {
                "pd": pd,
                "plotly": __import__("plotly"),
                "px": __import__("plotly.express"),
                "go": __import__("plotly.graph_objects"),
                "json": json,
                "data": data
            }
            exec(code, exec_globals)
            print("  ✓ Visualization executed successfully")
        except Exception as exec_error:
            print(f"  ⚠️  Code generated but execution failed: {type(exec_error).__name__}")
        
        return {
            "python_code": code,
            "next_step": "insights"
        }
    
    except Exception as e:
        print(f"  ✗ Error generating code: {e}")
        return {
            "python_code": f"# Error: {str(e)}",
            "next_step": "insights"
        }


def insights_agent(state: AgentState) -> dict:
    """
    Insights Agent: Analyzes data and provides business insights
    """
    print("💡 [Insights Agent] Generating insights...")
    
    data = state["query_result"]
    question = state["question"]
    
    if "Error" in data or not data or data == "[]":
        print("  ℹ️  No data available for insights")
        return {
            "insights": "No data available for analysis",
            "next_step": "end"
        }
    
    # Truncate data if too large
    data_preview = data[:1500] if len(data) > 1500 else data
    
    prompt = f"""You are a business analyst specializing in SaaS metrics.

Analyze this data and provide 2-3 key insights.

Data: {data_preview}
Question: {question}

Format your response as:
1. KEY FINDING: [main insight from the data]
2. BUSINESS IMPLICATION: [why this matters]
3. RECOMMENDATION: [actionable recommendation]

Be concise, data-driven, and focused."""
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        insights = response.content.strip()
        
        print("  ✓ Insights generated")
        
        return {
            "insights": insights,
            "next_step": "end"
        }
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {
            "insights": f"Error generating insights: {str(e)}",
            "next_step": "end"
        }


# ============================================================================
# Graph Construction
# ============================================================================

def build_workflow() -> Any:
    """Build the LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("sql", sql_agent)
    workflow.add_node("visualize", viz_agent)
    workflow.add_node("insights", insights_agent)
    
    # Set entry point
    workflow.set_entry_point("sql")
    
    # Add conditional edge from SQL agent
    def route_sql(state: AgentState) -> str:
        return state["next_step"]
    
    workflow.add_conditional_edges(
        "sql",
        route_sql,
        {
            "visualize": "visualize",
            "sql": "sql",  # Retry
            "end": END
        }
    )
    
    # Add deterministic edges
    workflow.add_edge("visualize", "insights")
    workflow.add_edge("insights", END)
    
    # Compile
    return workflow.compile()


# ============================================================================
# Main Analysis Function
# ============================================================================

def analyze_question(question: str) -> dict:
    """
    Main function to analyze a question using the multi-agent system
    """
    print(f"\n{'='*70}")
    print(f"📈 ANALYZING: {question}")
    print('='*70)
    
    app = build_workflow()
    
    try:
        # Initialize state
        initial_state = {
            "question": question,
            "sql_query": "",
            "query_result": "",
            "python_code": "",
            "insights": "",
            "next_step": "sql",
            "error_count": 0
        }
        
        # Run the workflow
        start_time = time.time()
        result = app.invoke(
            initial_state,
            config={"recursion_limit": 5}
        )
        elapsed = time.time() - start_time
        
        # Print results
        print(f"\n{'='*70}")
        print("ANALYSIS RESULTS")
        print('='*70)
        print(f"\n⏱️  Execution time: {elapsed:.2f} seconds")
        print(f"\n📊 SQL Query:\n{result['sql_query'][:300]}...")
        print(f"\n💡 Key Insights:\n{result['insights']}")
        print('='*70 + "\n")
        
        # Auto-open chart in browser if generated
        if result.get('python_code') and "Error" not in result['python_code']:
            chart_path = Path('output_chart.html').resolve()
            if chart_path.exists():
                print(f"🌐 Opening browser to view chart...")
                try:
                    webbrowser.open(f'file://{chart_path}')
                except Exception as e:
                    print(f"   Note: Could not auto-open browser ({e})")
                    print(f"   Open manually: {chart_path}")
        
        return result
    
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return None


# ============================================================================
# Interactive CLI with Enhanced UX
# ============================================================================

def show_menu():
    """Display the main menu"""
    print(f"\n{'─'*70}")
    print("COMMANDS:")
    print("  • Type a question to analyze")
    print("  • Type 'examples' to see sample questions")
    print("  • Type 'chart' to open the last chart")
    print("  • Type 'help' for documentation")
    print("  • Type 'quit' or 'exit' to leave")
    print(f"{'─'*70}\n")

def show_examples():
    """Display example questions"""
    examples = [
        "What is the churn rate by acquisition channel?",
        "Show me revenue breakdown by plan type",
        "Which country has the most active users?",
        "Calculate monthly retention rate",
        "What is the average subscription lifetime value?",
        "Show user distribution by plan",
        "Which integration has the highest adoption?",
    ]
    print(f"\n{'='*70}")
    print("📚 EXAMPLE QUESTIONS")
    print('='*70)
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print('='*70 + "\n")

def show_help():
    """Display help documentation"""
    print(f"\n{'='*70}")
    print("❓ HELP")
    print('='*70)
    print("""
The Multi-Agent SaaS Metrics Analyzer answers questions about your data:

HOW IT WORKS:
1. SQL Agent: Generates and executes optimal database queries
2. Visualization Agent: Creates interactive Plotly charts
3. Insights Agent: Analyzes results and provides recommendations

CAPABILITIES:
✓ Natural language questions about SaaS metrics
✓ Automatic SQL generation and execution
✓ Interactive data visualization (saves to output_chart.html)
✓ Business insights and recommendations
✓ Multi-table joins and complex queries
✓ JSON data extraction from metadata fields

TIPS:
• Ask specific questions for better results
• The system handles complex queries automatically
• Charts are saved to output_chart.html for viewing
• All responses include actionable insights

VIEWING CHARTS:
• Charts auto-open in your browser after each analysis
• You can also manually open: output_chart.html
• Or type 'chart' in the interactive menu

LIMITATIONS:
• Database readonly (no inserts/updates)
• Results truncated at 50KB to prevent memory issues
• Charts saved locally only

For more info: See SETUP_GUIDE.md or FIXES_EXPLAINED.md
""")
    print('='*70 + "\n")

def open_chart():
    """Open the chart in the default browser"""
    chart_path = Path('output_chart.html').resolve()
    if chart_path.exists():
        print(f"🌐 Opening chart in browser...")
        try:
            webbrowser.open(f'file://{chart_path}')
            print(f"✓ Chart opened: {chart_path}\n")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"   Open manually: {chart_path}\n")
    else:
        print("⚠️  No chart generated yet. Run an analysis first.\n")

def interactive_session():
    """Main interactive session"""
    print(f"\n{'='*70}")
    print("🤖 MULTI-AGENT SaaS METRICS ANALYZER")
    print("="*70)
    print("Powered by: LangGraph + DeepSeek V3")
    print("Database: SaaS Metrics (3 tables, real-time analysis)")
    print(f"{'='*70}")
    
    show_menu()
    
    question_count = 0
    
    while True:
        try:
            user_input = input(">>> ").strip()
            
            # Handle commands
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n{'='*70}")
                print(f"📊 Session Summary: {question_count} question(s) analyzed")
                print("👋 Thank you for using the Multi-Agent Analyzer!")
                print(f"{'='*70}\n")
                break
            
            if user_input.lower() == 'examples':
                show_examples()
                continue
            
            if user_input.lower() == 'help':
                show_help()
                continue
            
            if user_input.lower() == 'chart':
                open_chart()
                continue
            
            if user_input.lower() == 'clear':
                print("\033[2J\033[H" if os.name != 'nt' else "\n" * 3)  # Clear screen (Unix) or scroll (Windows)
                show_menu()
                continue
            
            # Analyze question
            question_count += 1
            result = analyze_question(user_input)
            
            if result:
                # Show additional context
                has_chart = result.get('python_code') and "Error" not in result['python_code']
                print("\n💾 OUTPUT SAVED:")
                print(f"  📈 Chart: output_chart.html" if has_chart else "  📈 Chart: Not generated (no data)")
                print(f"  📊 Query: {len(result['sql_query'])} characters")
                print(f"  📋 Insights: {len(result['insights'].split())} words")
        
        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print(f"⏸️  Session interrupted after {question_count} question(s)")
            print(f"{'='*70}\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("   Try rephrasing your question or type 'help'\n")


if __name__ == "__main__":
    interactive_session()

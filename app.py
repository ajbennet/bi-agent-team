"""
Streamlit Web App for Multi-Agent SaaS Metrics Analyzer
Beautiful web interface powered by LangGraph + DeepSeek V3
"""

import os
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Store API key in session state for persistence
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv('DEEPSEEK_API_KEY')

# Check API key before importing
if not st.session_state.api_key:
    st.error("❌ DEEPSEEK_API_KEY not set!")
    st.write("""
    **How to fix:**
    
    1. Get your key from: https://platform.deepseek.com/api_keys
    
    2. Set it before running Streamlit:
    ```powershell
    $env:DEEPSEEK_API_KEY="sk-your-key-here"
    streamlit run app.py
    ```
    
    3. Or set it permanently:
    ```powershell
    [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-...", "User")
    ```
    
    **Debugging:**
    - API key detected in environment: `{os.getenv('DEEPSEEK_API_KEY', 'NOT SET')[:20]}...`
    """)
    st.stop()

# Set environment variable for child processes (in case it's lost)
os.environ['DEEPSEEK_API_KEY'] = st.session_state.api_key

# Now import after checking API key
from langgraph_system import analyze_question

# Page configuration
st.set_page_config(
    page_title="SaaS Metrics Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        max-width: 1400px;
        margin: 0 auto;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .insight-box {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .sql-box {
        background: #f5f5f5;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.9em;
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'executing' not in st.session_state:
    st.session_state.executing = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.title("🤖 Analyzer Config")
    
    st.markdown("---")
    st.subheader("📚 Quick Examples")
    
    example_questions = [
        "What is the churn rate by acquisition channel?",
        "Show revenue breakdown by plan type",
        "Calculate monthly retention rate",
        "Which country has the most active users?",
        "What is the average subscription lifetime value?",
    ]
    
    for i, example in enumerate(example_questions, 1):
        if st.button(f"📌 Example {i}", key=f"example_{i}", use_container_width=True):
            st.session_state.selected_example = example
    
    st.markdown("---")
    st.subheader("📊 Query History")
    
    if st.session_state.query_history:
        for i, query in enumerate(st.session_state.query_history[-10:], 1):  # Last 10
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(query[:50] + "...", key=f"history_{i}", use_container_width=True):
                    st.session_state.selected_example = query
            with col2:
                st.caption(f"#{i}")
    else:
        st.info("No queries yet. Start by asking a question!")
    
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.markdown("""
    **Multi-Agent SaaS Metrics Analyzer**
    
    - 🔍 SQL Agent: Auto-generates queries
    - 📊 Viz Agent: Creates charts
    - 💡 Insights Agent: Provides recommendations
    
    Powered by LangGraph + DeepSeek V3
    """)
    
    # Workflow visualization
    st.markdown("---")
    with st.expander("📊 Workflow Diagram", expanded=False):
        st.write("**How the system processes your question:**")
        from langgraph_system import get_workflow_mermaid, visualize_workflow_ascii
        
        # Show ASCII diagram
        st.code(visualize_workflow_ascii(), language=None)
        
        st.write("**Interactive Mermaid Diagram:**")
        mermaid_code = get_workflow_mermaid()
        st.markdown(f"```mermaid\n{mermaid_code}\n```")
    
    # Debug section
    with st.expander("🔧 Debug Info"):
        api_key = st.session_state.get('api_key', 'NOT SET')
        if api_key and api_key != 'NOT SET':
            st.success(f"✅ API Key loaded: {api_key[:20]}...")
        else:
            st.error("❌ API Key NOT loaded")
        
        st.caption(f"Environment var: {os.getenv('DEEPSEEK_API_KEY', 'NOT SET')[:20]}...")
        st.caption(f"Session state: {st.session_state.api_key[:20] if st.session_state.api_key else 'NOT SET'}...")

# ============================================================================
# Main Content
# ============================================================================

st.title("📈 Multi-Agent SaaS Metrics Analyzer")
st.markdown("Ask questions about your SaaS metrics. Get SQL queries, charts, and insights instantly.")

# Question input section
st.markdown("---")
col1, col2 = st.columns([0.9, 0.1])

with col1:
    # Capture question text directly into session state
    st.session_state.current_question = st.text_input(
        "Ask a question about your SaaS metrics:",
        value=st.session_state.current_question,
        placeholder="e.g., What is the churn rate by acquisition channel?",
        label_visibility="collapsed"
    )

with col2:
    analyze_button = st.button("🚀 Analyze", use_container_width=True, key="analyze_btn")

# Use the question from session state
question = st.session_state.current_question

# Handle selected example - override question if one was selected
if 'selected_example' in st.session_state:
    question = st.session_state.selected_example
    st.session_state.current_question = question
    del st.session_state.selected_example

# Process analysis
if analyze_button:
    if not question or question.strip() == '':
        st.error("❌ Please enter a question before clicking Analyze")
    else:
        st.session_state.executing = True
        
        # Add to history
        if question not in st.session_state.query_history:
            st.session_state.query_history.append(question)
        
        # Show spinner while analyzing
        with st.spinner(f"🔄 Analyzing: {question}\n\nThis takes 10-20 seconds..."):
            try:
                result = analyze_question(question)
                st.session_state.current_result = result
            
            except Exception as e:
                st.session_state.error_message = str(e)
        
        st.session_state.executing = False

# Display errors if any
if st.session_state.error_message:
    st.error(f"❌ Analysis failed: {st.session_state.error_message}")
    if st.button("Clear error"):
        st.session_state.error_message = None
        st.rerun()

# Display results
if st.session_state.current_result:
    result = st.session_state.current_result
    
    st.success("✅ Analysis Complete!")
    
    # Metrics row
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Execution Time", f"{0:.2f}s", help="Time to run all agents")
    
    with col2:
        sql_chars = len(result.get('sql_query', ''))
        st.metric("Query Length", f"{sql_chars} chars")
    
    with col3:
        insight_words = len(result.get('insights', '').split())
        st.metric("Insight Words", f"{insight_words}")
    
    with col4:
        has_chart = result.get('python_code') and "Error" not in result.get('python_code', '')
        st.metric("Chart", "✅ Yes" if has_chart else "⚠️ No")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Chart", "🔍 SQL Query", "💡 Insights", "📈 Data"])
    
    with tab1:
        st.subheader("Interactive Chart")
        chart_path = Path('output_chart.html')
        if chart_path.exists():
            with open(chart_path, 'r', encoding='utf-8') as f:
                chart_html = f.read()
            st.components.v1.html(chart_html, height=600, scrolling=True)
        else:
            st.warning("⚠️ No chart was generated. The query may not have returned data.")
    
    with tab2:
        st.subheader("Generated SQL Query")
        sql_query = result.get('sql_query', 'No query generated')
        st.code(sql_query, language='sql')
        
        # Query stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Length", len(sql_query), "characters")
        with col2:
            st.metric("Lines", sql_query.count('\n') + 1)
        with col3:
            st.metric("Complexity", "High" if "JOIN" in sql_query else "Medium" if "GROUP BY" in sql_query else "Low")
    
    with tab3:
        st.subheader("Business Insights")
        insights = result.get('insights', 'No insights generated')
        
        # Format insights nicely
        if "1." in insights:
            for line in insights.split('\n'):
                if line.strip():
                    if any(key in line for key in ['KEY FINDING:', 'FINDING']):
                        st.info(f"🎯 {line}")
                    elif any(key in line for key in ['IMPLICATION', 'BUSINESS']):
                        st.warning(f"💼 {line}")
                    elif any(key in line for key in ['RECOMMENDATION']):
                        st.success(f"✓ {line}")
                    else:
                        st.markdown(f"• {line}")
        else:
            st.text(insights)
    
    with tab4:
        st.subheader("Query Results (JSON)")
        query_result = result.get('query_result', '[]')
        
        try:
            data = json.loads(query_result)
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="analysis_results.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data returned from query")
        except json.JSONDecodeError:
            st.text(query_result[:500])
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sql_export = result.get('sql_query', '')
        st.download_button(
            "📋 SQL Query",
            sql_export,
            "query.sql",
            "text/plain"
        )
    
    with col2:
        insights_export = result.get('insights', '')
        st.download_button(
            "📝 Insights",
            insights_export,
            "insights.txt",
            "text/plain"
        )
    
    with col3:
        if Path('output_chart.html').exists():
            with open('output_chart.html', 'rb') as f:
                st.download_button(
                    "📊 Chart",
                    f.read(),
                    "chart.html",
                    "text/html"
                )

# Empty state
if not st.session_state.current_result:
    st.markdown("---")
    st.info("""
    👋 **Welcome!** 
    
    Ask a question about your SaaS metrics to get started. Examples:
    - "What is the churn rate by acquisition channel?"
    - "Show me revenue breakdown by plan type"
    - "Calculate monthly retention rate"
    
    The system will:
    1. 🔍 Generate and execute an optimized SQL query
    2. 📊 Create an interactive visualization
    3. 💡 Provide business insights and recommendations
    
    **Tip:** First analysis takes 10-20 seconds, then gets faster!
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 Powered by LangGraph + DeepSeek V3")
with col2:
    st.caption("📦 Database: SaaS Metrics (3 tables)")
with col3:
    st.caption("⚡ Fast execution with error recovery")

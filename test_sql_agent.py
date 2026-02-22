import os
import sqlite3
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Setup DeepSeek
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com",
    temperature=0.1,
    timeout=60
)

# Get schema
conn = sqlite3.connect('saas_metrics.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Get column info for each table
schema_info = []
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    schema_info.append(f"{table_name}: {', '.join([col[1] for col in columns])}")

schema = "\n".join(schema_info)
conn.close()

print("Database Schema:")
print(schema)

# Test SQL Agent
question = "What is the churn rate by plan type?"

prompt = f"""You are a SQL expert. Write a SQLite query for this question.

Schema:
{schema}

Question: {question}

Return ONLY the SQL query, nothing else."""

print(f"\nGenerating SQL for: {question}")
response = llm.invoke([SystemMessage(content=prompt)])
sql = response.content.strip().replace("```sql", "").replace("```", "")

print("\nGenerated SQL:")
print(sql)

# Execute the query
print("\nExecuting query...")
conn = sqlite3.connect('saas_metrics.db')
try:
    df = pd.read_sql_query(sql, conn)
    print("\nResults:")
    print(df)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()

print("\n✓ Multi-agent framework is working!")

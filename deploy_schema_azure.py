import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_SQL_CONNECTION_STRING = os.getenv('AZURE_SQL_CONNECTION_STRING')

def deploy_schema():
    """Deploy schema to Azure SQL Database"""
    conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING)
    cursor = conn.cursor()
    
    cursor.execute("IF OBJECT_ID('tasks', 'U') IS NOT NULL DROP TABLE tasks")
    
    cursor.execute("""
        CREATE TABLE tasks (
            id INT IDENTITY(1,1) PRIMARY KEY,
            title NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            completed BIT DEFAULT 0,
            created_at DATETIME DEFAULT GETDATE()
        )
    """)
    
    cursor.execute("""
        INSERT INTO tasks (title, description, completed) 
        VALUES ('Sample Task', 'This is a sample task', 0)
    """)
    cursor.execute("""
        INSERT INTO tasks (title, description, completed) 
        VALUES ('Completed Task', 'This task is done', 1)
    """)
    
    conn.commit()
    conn.close()
    
    print("Schema deployed to Azure SQL successfully")
    print("Added 2 sample tasks")

if __name__ == '__main__':
    deploy_schema()
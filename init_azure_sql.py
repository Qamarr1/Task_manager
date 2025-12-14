#!/usr/bin/env python3
"""
Initialize Azure SQL Database with schema for qamar-taskmgr-db
"""
import pyodbc
import sys

# Azure SQL connection details (from your environment variables)
SERVER = 'task-manager-sql-8b.database.windows.net'
DATABASE = 'qamar-taskmgr-db'
USERNAME = 'sqladmin'
PASSWORD = 'NewStrongPassword123!'

# Connection string
CONNECTION_STRING = (
    f'Driver={{ODBC Driver 18 for SQL Server}};'
    f'Server=tcp:{SERVER},1433;'
    f'Database={DATABASE};'
    f'Uid={USERNAME};'
    f'Pwd={PASSWORD};'
    f'Encrypt=yes;'
    f'TrustServerCertificate=no;'
    f'Connection Timeout=30;'
)

# SQL Schema - Create both users and tasks tables
SCHEMA_SQL = """
-- Drop existing tables if they exist
IF OBJECT_ID('tasks', 'U') IS NOT NULL
    DROP TABLE tasks;
    
IF OBJECT_ID('users', 'U') IS NOT NULL
    DROP TABLE users;

-- Create users table
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(80) NOT NULL UNIQUE,
    email NVARCHAR(120) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Create tasks table
CREATE TABLE tasks (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20) NOT NULL DEFAULT 'todo',
    priority NVARCHAR(10) NOT NULL DEFAULT 'medium',
    category NVARCHAR(100) DEFAULT 'general',
    due_date DATETIME2 NULL,
    user_id INT NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index on user_id for better query performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
"""

def init_database():
    """Initialize the Azure SQL database"""
    print("🗄️  Initializing Azure SQL Database...")
    print(f"Server: {SERVER}")
    print(f"Database: {DATABASE}")
    print("")
    
    try:
        # Connect to database
        print("📡 Connecting to database...")
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        print("")
        
        # Execute schema
        print("📝 Creating tables...")
        cursor.execute(SCHEMA_SQL)
        conn.commit()
        print("✅ Tables created successfully!")
        print("")
        
        # Verify tables were created
        print("🔍 Verifying tables...")
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("")
        print("✨ Database initialization complete!")
        print("🚀 Your app should now work on Azure!")
        
    except pyodbc.Error as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()

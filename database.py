"""
Database connection module supporting both SQLite and Azure SQL
"""
import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create database connection based on configuration
    Returns a connection object with row_factory set
    """
    config = Config()
    
    if config.DB_TYPE == 'azure_sql':
        return get_azure_sql_connection()
    else:
        return get_sqlite_connection()

def get_sqlite_connection():
    """Create SQLite database connection for local development"""
    try:
        conn = sqlite3.connect(Config.SQLITE_DATABASE)
        conn.row_factory = sqlite3.Row
        logger.info("Connected to SQLite database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to SQLite: {e}")
        raise

def get_azure_sql_connection():
    """Create Azure SQL database connection for production"""
    try:
        import pyodbc
        
        server = Config.AZURE_SQL_SERVER
        database = Config.AZURE_SQL_DATABASE
        username = Config.AZURE_SQL_USERNAME
        password = Config.AZURE_SQL_PASSWORD
        
        # Connection string for Azure SQL
        connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            f'Encrypt=yes;'
            f'TrustServerCertificate=no;'
            f'Connection Timeout=30;'
        )
        
        conn = pyodbc.connect(connection_string)
        logger.info(f"Connected to Azure SQL database: {database}")
        return conn
    except ImportError:
        logger.error("pyodbc not installed. Install with: pip install pyodbc")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to Azure SQL: {e}")
        raise

def init_database():
    """Initialize database schema"""
    conn = get_db_connection()
    
    if Config.DB_TYPE == 'azure_sql':
        init_azure_sql_schema(conn)
    else:
        init_sqlite_schema(conn)
    
    conn.close()
    logger.info("Database initialized successfully")

def init_sqlite_schema(conn):
    """Initialize SQLite schema"""
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()

def init_azure_sql_schema(conn):
    """Initialize Azure SQL schema"""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(80) UNIQUE NOT NULL,
            email NVARCHAR(120) UNIQUE NOT NULL,
            password_hash NVARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT GETDATE()
        )
    """)
    
    # Create tasks table with user_id foreign key
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tasks' AND xtype='U')
        CREATE TABLE tasks (
            id INT IDENTITY(1,1) PRIMARY KEY,
            title NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            completed BIT DEFAULT 0,
            priority NVARCHAR(10) NOT NULL DEFAULT 'Medium',
            category NVARCHAR(100) DEFAULT 'General',
            due_date DATETIME NULL,
            created_at DATETIME DEFAULT GETDATE(),
            user_id INT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cursor.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Execute a database query with automatic connection management
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: Return single row
        fetch_all: Return all rows
    
    Returns:
        Query results or row count
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        return result
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# User Authentication Functions

def create_user(username, email, password):
    """
    Create a new user with hashed password
    
    Args:
        username: Unique username
        email: Unique email address
        password: Plain text password (will be hashed)
    
    Returns:
        User ID if successful, None if user exists
    """
    try:
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if Config.DB_TYPE == 'azure_sql':
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?); SELECT SCOPE_IDENTITY() AS user_id",
                (username, email, password_hash)
            )
            # Move to the result set with the SCOPE_IDENTITY() value
            cursor.nextset()
            result = cursor.fetchone()
            user_id = int(result[0]) if result and result[0] is not None else None
        else:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            user_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"User created: {username}")
        return user_id
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return None


def get_user_by_username(username):
    """
    Retrieve user by username
    
    Args:
        username: Username to search for
    
    Returns:
        User dict or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return dict(user) if hasattr(user, 'keys') else {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'password_hash': user[3]
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get user by username: {e}")
        return None


def get_user_by_email(email):
    """
    Retrieve user by email
    
    Args:
        email: Email to search for
    
    Returns:
        User dict or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return dict(user) if hasattr(user, 'keys') else {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'password_hash': user[3]
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get user by email: {e}")
        return None


def verify_user(username, password):
    """
    Verify user credentials
    
    Args:
        username: Username or email
        password: Plain text password to verify
    
    Returns:
        User dict if valid, None if invalid
    """
    # Try username first, then email
    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)
    
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


def get_user_by_id(user_id):
    """
    Retrieve user by ID
    
    Args:
        user_id: User ID
    
    Returns:
        User dict or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return dict(user) if hasattr(user, 'keys') else {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get user by ID: {e}")
        return None

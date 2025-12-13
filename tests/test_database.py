import pytest
import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_connection, get_sqlite_connection, init_database
from config import Config


@pytest.fixture
def cleanup_test_db():
    """Clean up test database before and after tests"""
    test_db = 'test_tasks.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Temporarily change database path
    original_db = Config.SQLITE_DATABASE
    Config.SQLITE_DATABASE = test_db
    
    yield test_db
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    Config.SQLITE_DATABASE = original_db


def test_get_sqlite_connection(cleanup_test_db):
    """Test SQLite connection creation"""
    conn = get_sqlite_connection()
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_db_connection_defaults_to_sqlite(cleanup_test_db):
    """Test that get_db_connection defaults to SQLite"""
    original_db_type = Config.DB_TYPE
    Config.DB_TYPE = 'sqlite'
    
    conn = get_db_connection()
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)
    conn.close()
    
    Config.DB_TYPE = original_db_type


def test_sqlite_connection_has_row_factory(cleanup_test_db):
    """Test SQLite connection has row_factory set"""
    conn = get_sqlite_connection()
    assert conn.row_factory == sqlite3.Row
    conn.close()


def test_init_database_creates_schema(cleanup_test_db):
    """Test database initialization creates proper schema"""
    init_database()
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Check if tasks table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    result = cursor.fetchone()
    assert result is not None
    assert result['name'] == 'tasks'
    
    # Check table structure
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    column_names = [col['name'] for col in columns]
    
    assert 'id' in column_names
    assert 'title' in column_names
    assert 'description' in column_names
    assert 'completed' in column_names
    assert 'created_at' in column_names
    
    conn.close()


def test_database_insert_and_query(cleanup_test_db):
    """Test inserting and querying data"""
    init_database()
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Insert test data
    cursor.execute(
        "INSERT INTO tasks (title, description, completed, user_id) VALUES (?, ?, ?, ?)",
        ("Test Task", "Test Description", 0, 1)
    )
    conn.commit()
    
    # Query data
    cursor.execute("SELECT * FROM tasks WHERE title = ?", ("Test Task",))
    row = cursor.fetchone()
    
    assert row is not None
    assert row['title'] == "Test Task"
    assert row['description'] == "Test Description"
    assert row['completed'] == 0
    
    conn.close()


def test_database_connection_context():
    """Test database connections can be properly closed"""
    test_db = 'test_temp.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    Config.SQLITE_DATABASE = test_db
    
    conn = get_sqlite_connection()
    assert conn is not None
    conn.close()
    
    # Should be able to create another connection after closing
    conn2 = get_sqlite_connection()
    assert conn2 is not None
    conn2.close()
    
    if os.path.exists(test_db):
        os.remove(test_db)
    Config.SQLITE_DATABASE = 'tasks.db'


def test_execute_query_with_params(cleanup_test_db):
    """Test execute_query helper with parameters"""
    from database import execute_query
    
    init_database()
    
    # Test insert
    result = execute_query(
        "INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)",
        ("Query Test", "Description", 1)
    )
    assert result == 1  # One row affected
    
    # Test fetch_one
    result = execute_query(
        "SELECT * FROM tasks WHERE title = ?",
        ("Query Test",),
        fetch_one=True
    )
    assert result is not None
    
    # Test fetch_all
    results = execute_query(
        "SELECT * FROM tasks",
        fetch_all=True
    )
    assert len(results) >= 1


def test_config_db_type():
    """Test Config DB_TYPE configuration"""
    config = Config()
    assert config.DB_TYPE in ['sqlite', 'azure_sql']

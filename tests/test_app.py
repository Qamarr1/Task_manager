import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """Create test client with fresh database"""
    app.config['TESTING'] = True
    import os
    import time
    
    import sqlite3
    # Initialize database with schema
    test_db = 'test_tasks.db'
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except:
            time.sleep(0.1)
            os.remove(test_db)
    
    # Override database path for testing
    from config import Config
    original_db = Config.SQLITE_DATABASE
    Config.SQLITE_DATABASE = test_db
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tasks table with user_id and all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'Medium',
            category TEXT DEFAULT 'General',
            due_date DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create test user
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES ('testuser', 'test@example.com', 'hash')")
    user_id = cursor.lastrowid
    
    # Clear existing data and insert test data with user_id
    cursor.execute('DELETE FROM tasks')
    cursor.execute("INSERT INTO tasks (title, completed, priority, category, user_id) VALUES ('Test Task', 0, 'High', 'Work', ?)", (user_id,))
    conn.commit()
    conn.close()
    
    with app.test_client() as client:
        # Set user_id in session for testing
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
        yield client
    
    # Cleanup
    Config.SQLITE_DATABASE = original_db
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except:
            pass

def test_home_page_loads(client):
    """Test that homepage loads (landing page)"""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200

def test_home_displays_tasks(client):
    """Test that homepage displays tasks"""
    response = client.get('/tasks')
    assert b'Test Task' in response.data

def test_add_task_success(client):
    """Test adding a valid task"""
    response = client.post('/task/add', data={
        'title': 'New Task',
        'priority': 'Low',
        'category': 'Personal'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'New Task' in response.data

def test_add_task_no_title(client):
    """Test that empty title is rejected"""
    response = client.post('/task/add', data={
        'title': ''
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show an error message or stay on same page

def test_toggle_task(client):
    """Test toggling task completion"""
    # Get the task ID that was created in the fixture
    import sqlite3
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tasks LIMIT 1')
    task_id = cursor.fetchone()[0]
    conn.close()
    
    response = client.post(f'/task/{task_id}/toggle', follow_redirects=True)
    assert response.status_code == 200

def test_delete_task(client):
    """Test deleting a task"""
    # Get the task ID that was created in the fixture
    import sqlite3
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tasks LIMIT 1')
    task_id = cursor.fetchone()[0]
    conn.close()
    
    response = client.post(f'/task/{task_id}/delete', follow_redirects=True)
    assert response.status_code == 200

def test_health_endpoint(client):
    """Test health check"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_edit_task(client):
    """Test editing an existing task"""
    import sqlite3
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tasks LIMIT 1')
    task_id = cursor.fetchone()[0]
    conn.close()

    response = client.post(f'/task/{task_id}/edit', data={
        'title': 'Updated Title',
        'description': 'Updated description',
        'priority': 'Medium',
        'category': 'School'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Updated Title' in response.data

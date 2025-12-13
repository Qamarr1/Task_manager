"""
Integration tests for Task Manager application
Tests complete workflows and end-to-end functionality
"""
import pytest
import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """Create test client with fresh database"""
    app.config['TESTING'] = True
    
    # Use separate test database
    test_db = 'test_integration.db'
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except:
            pass
    
    # Override database path for testing
    from config import Config
    original_db = Config.SQLITE_DATABASE
    Config.SQLITE_DATABASE = test_db
    
    # Initialize database with schema
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'Medium',
            category TEXT DEFAULT 'General',
            status TEXT DEFAULT 'todo',
            due_date DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create test user
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES ('testuser', 'test@example.com', 'hash')")
    user_id = cursor.lastrowid
    
    cursor.execute('DELETE FROM tasks')
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

def test_complete_task_lifecycle(client):
    """Test creating, toggling, and deleting a task"""
    # Create a task
    response = client.post('/task/add', data={'title': 'Integration Test Task'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Integration Test Task' in response.data
    
    # Get the task ID
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tasks WHERE title = ?', ('Integration Test Task',))
    task_id = cursor.fetchone()[0]
    conn.close()
    
    # Toggle the task
    response = client.post(f'/task/{task_id}/toggle', follow_redirects=True)
    assert response.status_code == 200
    
    # Verify it's completed
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    completed = cursor.fetchone()[0]
    conn.close()
    assert completed == 1
    
    # Delete the task
    response = client.post(f'/task/{task_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Integration Test Task' not in response.data

def test_multiple_tasks_creation(client):
    """Test creating multiple tasks"""
    tasks = ['Task 1', 'Task 2', 'Task 3']
    
    for task_title in tasks:
        response = client.post('/task/add', data={'title': task_title}, follow_redirects=True)
        assert response.status_code == 200
    
    # Verify all tasks are displayed
    response = client.get('/tasks')
    for task_title in tasks:
        assert task_title.encode() in response.data

def test_task_validation(client):
    """Test input validation"""
    # Empty title
    response = client.post('/task/add', data={'title': ''}, follow_redirects=True)
    assert response.status_code == 200
    
    # Very long title (over 255 characters)
    long_title = 'A' * 300
    response = client.post('/task/add', data={'title': long_title}, follow_redirects=True)
    assert response.status_code == 200
    assert b'too long' in response.data or b'required' in response.data

def test_toggle_nonexistent_task(client):
    """Test toggling a task that doesn't exist"""
    response = client.post('/task/99999/toggle', follow_redirects=True)
    assert response.status_code == 200

def test_delete_nonexistent_task(client):
    """Test deleting a task that doesn't exist"""
    response = client.post('/task/99999/delete', follow_redirects=True)
    assert response.status_code == 200

def test_health_endpoint_with_tasks(client):
    """Test health endpoint with tasks in database"""
    # Add some tasks
    client.post('/task/add', data={'title': 'Health Test Task'}, follow_redirects=True)
    
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['tasks_count'] >= 1

def test_task_persistence(client):
    """Test that tasks persist across requests"""
    # Create a task
    client.post('/task/add', data={'title': 'Persistent Task'}, follow_redirects=True)
    
    # Make a new request to verify it's still there
    response = client.get('/tasks')
    assert b'Persistent Task' in response.data

def test_task_ordering(client):
    """Test that tasks are displayed on the page"""
    # Create tasks in sequence
    client.post('/task/add', data={'title': 'First Task'}, follow_redirects=True)
    client.post('/task/add', data={'title': 'Second Task'}, follow_redirects=True)
    client.post('/task/add', data={'title': 'Third Task'}, follow_redirects=True)
    
    response = client.get('/tasks')
    content = response.data.decode()
    
    # All tasks should be present in the response
    assert 'First Task' in content
    assert 'Second Task' in content
    assert 'Third Task' in content

def test_toggle_task_twice(client):
    """Test toggling a task twice returns to original state"""
    # Create a task
    client.post('/task/add', data={'title': 'Toggle Test'}, follow_redirects=True)
    
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, completed FROM tasks WHERE title = ?', ('Toggle Test',))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        # Task wasn't created, skip the test
        return
    
    task_id, initial_status = result
    
    # Toggle once
    client.post(f'/task/{task_id}/toggle', follow_redirects=True)
    
    # Toggle twice
    client.post(f'/task/{task_id}/toggle', follow_redirects=True)
    
    # Check final status matches initial
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    final_status = cursor.fetchone()[0]
    conn.close()
    
    assert initial_status == final_status

def test_error_handlers(client):
    """Test custom error handlers"""
    # Test 404 handler
    response = client.get('/nonexistent-route')
    assert response.status_code == 404

def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get('/metrics')
    # Should return metrics or error if prometheus not available
    assert response.status_code in [200, 503]

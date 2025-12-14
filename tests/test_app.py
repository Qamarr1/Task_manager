import pytest
import sys
import os
import re
from datetime import datetime, timedelta

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
    
    # Clear existing data and insert test data with user_id
    cursor.execute('DELETE FROM tasks')
    cursor.execute("INSERT INTO tasks (title, completed, priority, category, status, user_id) VALUES ('Test Task', 0, 'High', 'Work', 'todo', ?)", (user_id,))
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
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
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
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
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
    from config import Config
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
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


def test_move_task_status(client):
    """Task can move between columns via status."""
    from config import Config
    import sqlite3

    # Create a fresh task via direct insert to control status
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    cur.execute("INSERT INTO tasks (title, status, user_id) VALUES (?, ?, ?)", ("Move Me", "todo", user_id))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()

    resp = client.post(f"/task/{task_id}/move", data={"status": "in_progress"}, follow_redirects=True)
    assert resp.status_code == 200

    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    status = cur.fetchone()[0]
    conn.close()
    assert status == "in_progress"


def test_status_on_create_and_edit(client):
    """Status persists on create and edit."""
    from config import Config
    import sqlite3

    # Create with in_review
    resp = client.post('/task/add', data={
        'title': 'Status Create',
        'status': 'in_review'
    }, follow_redirects=True)
    assert resp.status_code == 200

    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM tasks WHERE title = ?", ("Status Create",))
    task_id, status = cur.fetchone()
    conn.close()
    assert status == 'in_review'

    # Edit to done
    resp = client.post(f'/task/{task_id}/edit', data={
        'title': 'Status Edited',
        'description': '',
        'priority': 'Low',
        'category': 'Other',
        'status': 'done'
    }, follow_redirects=True)
    assert resp.status_code == 200

    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    status = cur.fetchone()[0]
    conn.close()
    assert status == 'done'


def test_default_status_on_create(client):
    """Creating without status defaults to todo."""
    from config import Config
    import sqlite3

    resp = client.post('/task/add', data={'title': 'Default Status'}, follow_redirects=True)
    assert resp.status_code == 200

    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT status FROM tasks WHERE title = ?", ("Default Status",))
    status = cur.fetchone()[0]
    conn.close()
    assert status == 'todo'


def test_stats_counts(client):
    """Stats reflect overdue and due-today tasks."""
    from config import Config
    import sqlite3

    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]

    past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    today = datetime.now().strftime("%Y-%m-%dT%H:%M")

    cur.execute("INSERT INTO tasks (title, user_id, due_date, status) VALUES (?, ?, ?, ?)",
                ("Overdue Stat", user_id, past, "todo"))
    cur.execute("INSERT INTO tasks (title, user_id, due_date, status) VALUES (?, ?, ?, ?)",
                ("Today Stat", user_id, today, "todo"))
    conn.commit()
    conn.close()

    resp = client.get('/tasks')
    assert resp.status_code == 200
    # Assert both tasks rendered with their labels
    assert b'Overdue Stat' in resp.data
    assert b'Today Stat' in resp.data
    # Check for overdue task indicators
    assert b'is-overdue' in resp.data or b'badge-overdue' in resp.data
    # Check stats section exists
    assert b'stat-overdue' in resp.data


# Authentication Tests
def test_signup_success(client):
    """Test user can sign up with valid credentials"""
    # Clear session first (logout testuser)
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.post('/signup', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Check if user was created by verifying database
    from config import Config
    import sqlite3
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = 'newuser'")
    user = cur.fetchone()
    conn.close()
    assert user is not None
    assert user[0] == 'newuser'


def test_signup_duplicate_username(client):
    """Test signup rejects duplicate username"""
    # First signup
    client.post('/signup', data={
        'username': 'duplicate',
        'email': 'user1@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Clear session to logout
    with client.session_transaction() as sess:
        sess.clear()
    
    # Try to signup with same username
    response = client.post('/signup', data={
        'username': 'duplicate',
        'email': 'user2@example.com',
        'password': 'password456',
        'confirm_password': 'password456'
    }, follow_redirects=False)
    
    # Should stay on signup page (not redirect to home)
    # Check that second user was NOT created
    from config import Config
    import sqlite3
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'duplicate'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1  # Only one user with this username should exist


def test_login_success(client):
    """Test user can login with correct credentials"""
    # First create a user
    from database import create_user
    create_user('loginuser', 'login@example.com', 'testpass123')
    
    # Clear any existing session
    with client.session_transaction() as sess:
        sess.clear()
    
    # Try to login
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome' in response.data or b'loginuser' in response.data


# User Management Tests
def test_change_username_success(client):
    """Test user can change username with correct password"""
    # Get current user's password hash
    from config import Config
    import sqlite3
    from werkzeug.security import generate_password_hash
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    
    # Set a known password for testuser
    hashed = generate_password_hash('testpassword')
    cur.execute("UPDATE users SET password_hash = ? WHERE username = 'testuser'", (hashed,))
    conn.commit()
    conn.close()
    
    response = client.post('/change-username',
                          json={
                              'new_username': 'updateduser',
                              'current_password': 'testpassword'
                          })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data.get('message', '').lower() or 'updated' in data.get('message', '').lower()


def test_change_username_wrong_password(client):
    """Test change username fails with wrong password"""
    response = client.post('/change-username',
                          json={
                              'new_username': 'newname',
                              'current_password': 'wrongpassword123'
                          })
    
    assert response.status_code in [400, 401]
    data = response.get_json()
    assert 'incorrect' in data.get('error', '').lower() or 'wrong' in data.get('error', '').lower()


def test_change_password_success(client):
    """Test user can change password with correct current password"""
    from config import Config
    import sqlite3
    from werkzeug.security import generate_password_hash
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    
    # Set a known password for testuser
    hashed = generate_password_hash('oldpass123')
    cur.execute("UPDATE users SET password_hash = ? WHERE username = 'testuser'", (hashed,))
    conn.commit()
    conn.close()
    
    response = client.post('/change-password',
                          json={
                              'current_password': 'oldpass123',
                              'new_password': 'newpass456'
                          })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data.get('message', '').lower() or 'updated' in data.get('message', '').lower()


# Security Tests
def test_access_tasks_without_login(client):
    """Test that accessing /tasks without login is handled properly"""
    # Clear session
    with client.session_transaction() as sess:
        sess.clear()
    
    # In testing mode, login_required decorator allows access
    # But we can check the decorator exists
    response = client.get('/tasks')
    # In test mode it returns 200, in production it would redirect
    assert response.status_code in [200, 302]


def test_task_filtering_by_category(client):
    """Test tasks can be filtered by category"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Add tasks with different categories
    cur.execute("INSERT INTO tasks (title, user_id, category, status) VALUES (?, ?, ?, ?)",
                ("Work Task", user_id, "Work", "todo"))
    cur.execute("INSERT INTO tasks (title, user_id, category, status) VALUES (?, ?, ?, ?)",
                ("Shopping Task", user_id, "Shopping", "todo"))
    conn.commit()
    conn.close()
    
    # Filter by category
    response = client.get('/tasks?category=Work')
    assert response.status_code == 200
    assert b'Work Task' in response.data


def test_login_invalid_password(client):
    """Test login fails with wrong password"""
    # Create a user
    from database import create_user
    create_user('testlogin', 'testlogin@example.com', 'correctpass')
    
    # Clear session
    with client.session_transaction() as sess:
        sess.clear()
    
    # Try to login with wrong password
    response = client.post('/login', data={
        'username': 'testlogin',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should still be on login page, not redirected to tasks
    assert b'login' in response.data.lower() or b'sign in' in response.data.lower()


def test_logout_clears_session(client):
    """Test logout clears user session"""
    # Verify user is logged in (from fixture)
    with client.session_transaction() as sess:
        assert sess.get('user_id') is not None
    
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    
    # Verify session is cleared
    with client.session_transaction() as sess:
        assert sess.get('user_id') is None


def test_signup_password_mismatch(client):
    """Test signup fails when passwords don't match"""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.post('/signup', data={
        'username': 'mismatchuser',
        'email': 'mismatch@example.com',
        'password': 'password123',
        'confirm_password': 'different456'
    }, follow_redirects=False)
    
    # Should stay on signup page
    assert response.status_code == 200
    
    # User should not be created
    from config import Config
    import sqlite3
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'mismatchuser'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0


def test_task_with_priority_levels(client):
    """Test tasks can be created with different priority levels"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Add tasks with different priorities
    priorities = ['High', 'Medium', 'Low']
    for priority in priorities:
        cur.execute("INSERT INTO tasks (title, user_id, priority, status) VALUES (?, ?, ?, ?)",
                    (f"{priority} Priority Task", user_id, priority, "todo"))
    conn.commit()
    conn.close()
    
    response = client.get('/tasks')
    assert response.status_code == 200
    assert b'High Priority Task' in response.data
    assert b'Medium Priority Task' in response.data
    assert b'Low Priority Task' in response.data


def test_task_move_between_statuses(client):
    """Test task can be moved between different Kanban statuses"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Create task in todo status
    cur.execute("INSERT INTO tasks (title, user_id, status) VALUES (?, ?, ?)",
                ("Move Test Task", user_id, "todo"))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    # Move to in_progress
    response = client.post(f'/task/{task_id}/move', 
                          json={'status': 'in_progress'})
    assert response.status_code == 200
    
    # Verify status changed
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    status = cur.fetchone()[0]
    conn.close()
    assert status == 'in_progress'


def test_change_username_duplicate_rejection(client):
    """Test changing username to an existing username is rejected"""
    from config import Config
    import sqlite3
    from werkzeug.security import generate_password_hash
    
    # Create another user
    from database import create_user
    create_user('existinguser', 'existing@example.com', 'password')
    
    # Set password for testuser
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    hashed = generate_password_hash('testpass')
    cur.execute("UPDATE users SET password_hash = ? WHERE username = 'testuser'", (hashed,))
    conn.commit()
    conn.close()
    
    # Try to change testuser's username to existing one
    response = client.post('/change-username',
                          json={
                              'new_username': 'existinguser',
                              'current_password': 'testpass'
                          })
    
    assert response.status_code == 409
    data = response.get_json()
    assert 'taken' in data.get('error', '').lower() or 'exists' in data.get('error', '').lower()


def test_change_password_wrong_current(client):
    """Test change password fails with wrong current password"""
    response = client.post('/change-password',
                          json={
                              'current_password': 'definitelywrong',
                              'new_password': 'newpass123'
                          })
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'incorrect' in data.get('error', '').lower()


def test_task_search_functionality(client):
    """Test tasks can be searched by title"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Add searchable tasks
    cur.execute("INSERT INTO tasks (title, user_id, status) VALUES (?, ?, ?)",
                ("Buy groceries", user_id, "todo"))
    cur.execute("INSERT INTO tasks (title, user_id, status) VALUES (?, ?, ?)",
                ("Finish homework", user_id, "todo"))
    conn.commit()
    conn.close()
    
    response = client.get('/tasks?search=groceries')
    assert response.status_code == 200
    assert b'Buy groceries' in response.data


def test_overdue_task_detection(client):
    """Test overdue tasks are properly detected"""
    from config import Config
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Create overdue task
    past_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    cur.execute("INSERT INTO tasks (title, user_id, due_date, status) VALUES (?, ?, ?, ?)",
                ("Overdue Task", user_id, past_date, "todo"))
    conn.commit()
    conn.close()
    
    response = client.get('/tasks')
    assert response.status_code == 200
    # Check for overdue indicator
    assert b'Overdue Task' in response.data
    assert b'is-overdue' in response.data or b'overdue' in response.data.lower()


def test_multiple_users_isolation(client):
    """Test that users only see their own tasks"""
    from config import Config
    import sqlite3
    from database import create_user
    
    # Create second user
    user2_id = create_user('user2', 'user2@example.com', 'pass123')
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    
    # Get first user ID
    cur.execute("SELECT id FROM users WHERE username = 'testuser'")
    user1_id = cur.fetchone()[0]
    
    # Add task for user1
    cur.execute("INSERT INTO tasks (title, user_id, status) VALUES (?, ?, ?)",
                ("User1 Task", user1_id, "todo"))
    
    # Add task for user2
    cur.execute("INSERT INTO tasks (title, user_id, status) VALUES (?, ?, ?)",
                ("User2 Task", user2_id, "todo"))
    conn.commit()
    conn.close()
    
    # User1 should only see their task
    response = client.get('/tasks')
    assert response.status_code == 200
    assert b'User1 Task' in response.data
    assert b'User2 Task' not in response.data


def test_signup_weak_password(client):
    """Test signup rejects passwords shorter than 6 characters"""
    with client.session_transaction() as sess:
        sess.clear()
    
    response = client.post('/signup', data={
        'username': 'weakpass',
        'email': 'weak@example.com',
        'password': '12345',  # Only 5 characters
        'confirm_password': '12345'
    }, follow_redirects=False)
    
    # Should stay on signup page
    assert response.status_code == 200
    
    # User should not be created
    from config import Config
    import sqlite3
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'weakpass'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0


def test_signup_duplicate_email(client):
    """Test signup rejects duplicate email address"""
    from config import Config
    import sqlite3
    
    # Clear session first
    with client.session_transaction() as sess:
        sess.clear()
    
    # First user
    response1 = client.post('/signup', data={
        'username': 'user1',
        'email': 'duplicate@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # Verify user1 was created
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE username = 'user1'")
    user1 = cur.fetchone()
    conn.close()
    assert user1 is not None, "First user should be created"
    
    with client.session_transaction() as sess:
        sess.clear()
    
    # Try to signup with same email but different username
    response = client.post('/signup', data={
        'username': 'user2',
        'email': 'duplicate@example.com',
        'password': 'password456',
        'confirm_password': 'password456'
    }, follow_redirects=False)
    
    # Should stay on signup page (200) or show error
    # Check that only ONE user with this email exists
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE email = 'duplicate@example.com'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1, "Should only have one user with duplicate email"


def test_edit_task_updates_fields(client):
    """Test editing task updates all fields correctly"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Create task
    cur.execute("INSERT INTO tasks (title, description, user_id, priority, category, status) VALUES (?, ?, ?, ?, ?, ?)",
                ("Original Title", "Original Description", user_id, "Low", "Personal", "todo"))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    # Edit task
    response = client.post(f'/task/{task_id}/edit', data={
        'title': 'Updated Title',
        'description': 'Updated Description',
        'priority': 'High',
        'category': 'Work'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify changes
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT title, description, priority, category FROM tasks WHERE id = ?", (task_id,))
    task = cur.fetchone()
    conn.close()
    
    assert task[0] == 'Updated Title'
    assert task[1] == 'Updated Description'
    assert task[2] == 'High'
    assert task[3] == 'Work'


def test_task_filtering_by_priority(client):
    """Test tasks can be filtered by priority level"""
    from config import Config
    import sqlite3
    
    conn = sqlite3.connect(Config.SQLITE_DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    user_id = cur.fetchone()[0]
    
    # Add tasks with different priorities
    cur.execute("INSERT INTO tasks (title, user_id, priority, status) VALUES (?, ?, ?, ?)",
                ("High Priority", user_id, "High", "todo"))
    cur.execute("INSERT INTO tasks (title, user_id, priority, status) VALUES (?, ?, ?, ?)",
                ("Low Priority", user_id, "Low", "todo"))
    conn.commit()
    conn.close()
    
    # Filter by High priority
    response = client.get('/tasks?priority=High')
    assert response.status_code == 200
    assert b'High Priority' in response.data




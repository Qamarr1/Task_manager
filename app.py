from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-later')

# Determine which database to use
USE_AZURE_SQL = os.getenv('AZURE_SQL_CONNECTION_STRING') is not None

if USE_AZURE_SQL:
    import pyodbc
    AZURE_SQL_CONNECTION_STRING = os.getenv('AZURE_SQL_CONNECTION_STRING')
else:
    import sqlite3
    DATABASE = 'tasks.db'

def get_db_connection():
    """Create database connection (SQLite or Azure SQL)"""
    if USE_AZURE_SQL:
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING)
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    """Display all tasks"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC' if not USE_AZURE_SQL else 'SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/task/add', methods=['POST'])
def add_task():
    """Create a new task"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()

    if not title:
        flash('Task title is required', 'error')
        return redirect(url_for('home'))
    
    if len(title) > 255:
        flash('Task title too long (max 255 characters)', 'error')
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_AZURE_SQL:
        cursor.execute(
            'INSERT INTO tasks (title, description, completed, created_at) VALUES (?, ?, 0, GETDATE())',
            (title, description)
        )
    else:
        cursor.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (title, description)
        )
    
    conn.commit()
    conn.close()
    
    flash('Task created successfully', 'success')
    return redirect(url_for('home'))

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_AZURE_SQL:
        cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    else:
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    
    task = cursor.fetchone()
    
    if task:
        new_status = 0 if task[0 if USE_AZURE_SQL else 3] else 1
        cursor.execute('UPDATE tasks SET completed = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
        flash('Task status updated', 'success')
    else:
        flash('Task not found', 'error')
    
    conn.close()
    return redirect(url_for('home'))

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    """Delete a task"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    
    flash('Task deleted successfully', 'success')
    return redirect(url_for('home'))

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks')
        count = cursor.fetchone()[0]
        conn.close()
        return {'status': 'healthy', 'tasks_count': count, 'database': 'Azure SQL' if USE_AZURE_SQL else 'SQLite'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
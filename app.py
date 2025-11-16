from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-later'

tasks = [
    {
        'id': 1,
        'title': 'Sample Task',
        'description': 'This is a sample task',
        'completed': False,
        'created_at': '2025-11-18 10:00'
    },
    {
        'id': 2,
        'title': 'Completed Task',
        'description': 'This task is done',
        'completed': True,
        'created_at': '2025-11-17 15:30'
    }
]
next_id = 3

@app.route('/')
def home():
    """Display all tasks"""
    return render_template('index.html', tasks=tasks)

@app.route('/task/add', methods=['POST'])
def add_task():
    """Create a new task"""
    global next_id
    
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    

    if not title:
        flash('Task title is required', 'error')
        return redirect(url_for('home'))
    
    if len(title) > 255:
        flash('Task title too long (max 255 characters)', 'error')
        return redirect(url_for('home'))
    
    # new task
    new_task = {
        'id': next_id,
        'title': title,
        'description': description,
        'completed': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    tasks.append(new_task)
    next_id += 1
    
    flash('Task created successfully', 'success')
    return redirect(url_for('home'))

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'tasks_count': len(tasks)
    }, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
import logging
import sys
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session, current_app

from config import config, Config
from database import get_db_connection, create_user, verify_user, get_user_by_id, get_user_by_username, get_user_by_email

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    PROMETHEUS_AVAILABLE = True
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
    TASK_OPERATIONS = Counter('task_operations_total', 'Total task operations', ['operation'])
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = Config.ENVIRONMENT
app.config.from_object(config.get(env, config['default']))
app.secret_key = app.config['SECRET_KEY']


def ensure_schema_columns():
    """Ensure optional columns exist (supports older DBs)."""
    columns_needed = [
        ('due_date', "ALTER TABLE tasks ADD due_date DATETIME"),
        ('priority', "ALTER TABLE tasks ADD priority VARCHAR(10) NOT NULL DEFAULT 'Medium'"),
        ('category', "ALTER TABLE tasks ADD category VARCHAR(100) DEFAULT 'General'")
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if app.config['DB_TYPE'] == 'azure_sql':
            azure_alters = {
                'due_date': "ALTER TABLE tasks ADD due_date DATETIME",
                'priority': "ALTER TABLE tasks ADD priority NVARCHAR(10) NOT NULL DEFAULT 'Medium'",
                'category': "ALTER TABLE tasks ADD category NVARCHAR(100) DEFAULT 'General'",
            }
            for name, alter_stmt in azure_alters.items():
                cursor.execute(
                    "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='tasks' AND COLUMN_NAME=?",
                    (name,)
                )
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute(alter_stmt)
                    conn.commit()
                    logger.info("Added %s column to Azure SQL tasks table", name)
        else:
            cursor.execute("PRAGMA table_info(tasks)")
            existing = []
            for row in cursor.fetchall():
                try:
                    existing.append(row['name'])
                except Exception:
                    existing.append(row[1] if len(row) > 1 else row[0])

            for name, alter_stmt in columns_needed:
                if name not in existing:
                    cursor.execute(alter_stmt)
                    conn.commit()
                    logger.info("Added %s column to SQLite tasks table", name)
    except Exception as exc:
        logger.warning("Could not ensure schema columns exist: %s", exc)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


def parse_datetime_value(value):
    """Return datetime from DB value or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


# Authentication decorator
def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get("TESTING"):
            return f(*args, **kwargs)
        
        if not session.get("user_id"):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def row_to_dict(row, columns):
    """Normalize DB row to dict for both SQLite and Azure SQL."""
    try:
        return dict(row)
    except Exception:
        return {col: row[idx] for idx, col in enumerate(columns)}


def fetch_tasks():
    """Fetch tasks and annotate with derived flags."""
    ensure_schema_columns()
    
    # Get current user's ID from session
    user_id = session.get('user_id')
    if not user_id:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user_id column exists, if not skip filtering by user
    try:
        cursor.execute(
            "SELECT id, title, description, completed, created_at, due_date, priority, category FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    except Exception:
        # Fallback for old schema without user_id
        cursor.execute(
            "SELECT id, title, description, completed, created_at, due_date, priority, category FROM tasks ORDER BY created_at DESC"
        )
    
    rows = cursor.fetchall()
    column_names = [col[0] for col in cursor.description] if cursor.description else []

    tasks = []
    priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
    now = datetime.now()
    for row in rows:
        raw = row_to_dict(row, column_names)
        created_at = parse_datetime_value(raw.get('created_at'))
        due_date = parse_datetime_value(raw.get('due_date'))

        task = {
            'id': raw.get('id'),
            'title': raw.get('title', ''),
            'description': raw.get('description', ''),
            'completed': bool(raw.get('completed')),
            'created_at': created_at,
            'due_date': due_date,
            'priority': raw.get('priority', 'Medium'),
            'category': raw.get('category', 'General')
        }
        task['is_overdue'] = (not task['completed']) and task['due_date'] is not None and task['due_date'] < now
        task['is_due_today'] = task['due_date'] is not None and task['due_date'].date() == now.date()
        task['priority_rank'] = priority_order.get(task['priority'], 2)
        tasks.append(task)

    cursor.close()
    conn.close()
    return tasks


# Middleware to track metrics (if installed)
if PROMETHEUS_AVAILABLE:
    @app.before_request
    def before_request():
        request.start_time = datetime.now()

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            latency = (datetime.now() - request.start_time).total_seconds()
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.endpoint or 'unknown').observe(latency)
            REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint or 'unknown',
                                 status=response.status_code).inc()
        return response


# Authentication Routes

@app.route('/landing')
@app.route('/')
def landing():
    """Landing page for unauthenticated users."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('landing.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        if len(username) < 3 or len(username) > 80:
            flash('Username must be between 3 and 80 characters', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if get_user_by_email(email):
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create user
        user_id = create_user(username, email, password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            flash(f'Welcome, {username}! Your account has been created.', 'success')
            logger.info(f"New user registered: {username}")
            return redirect(url_for('home'))
        else:
            flash('Error creating account. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            logger.info(f"User logged in: {user['username']}")
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout."""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'success')
    logger.info(f"User logged out: {username}")
    return redirect(url_for('landing'))


@app.route('/home')
@app.route('/tasks')
@login_required
def home():
    """Display all tasks with filtering, search, and sorting."""
    try:
        tasks = fetch_tasks()

        search_term = request.args.get('q', '').strip().lower()
        status_filter = request.args.get('status', 'all')
        category_filter = request.args.get('category', 'all').strip()
        sort_option = request.args.get('sort', 'priority_desc')

        filtered = []
        for task in tasks:
            if search_term and search_term not in task['title'].lower():
                continue
            if category_filter not in ('', 'all') and task['category'].lower() != category_filter.lower():
                continue

            if status_filter == 'completed' and not task['completed']:
                continue
            if status_filter == 'pending' and task['completed']:
                continue
            if status_filter == 'overdue' and not task['is_overdue']:
                continue
            if status_filter == 'today':
                if not task['due_date'] or task['due_date'].date() != datetime.now().date():
                    continue

            filtered.append(task)

        if sort_option.startswith('priority'):
            reverse = sort_option == 'priority_desc'
            filtered.sort(key=lambda t: t.get('priority_rank', 2), reverse=reverse)
        else:
            reverse = True if sort_option == 'created_desc' else False
            filtered.sort(key=lambda t: t['created_at'] or datetime.min, reverse=reverse)

        grouped_tasks = {}
        for task in filtered:
            category = task.get('category', 'General') or 'General'
            grouped_tasks.setdefault(category, []).append(task)

        filters = {
            'q': search_term,
            'status': status_filter,
            'sort': sort_option,
            'category': category_filter
        }

        logger.info("Rendering %d tasks after filters", len(filtered))
        return render_template('index.html', tasks=filtered, grouped_tasks=grouped_tasks, filters=filters)
    except Exception as exc:
        logger.error("Error fetching tasks: %s", exc)
        flash('Error loading tasks', 'error')
        return render_template('index.html', tasks=[], grouped_tasks={}, filters={})


@app.route('/task/add', methods=['POST'])
@login_required
def add_task():
    """Create a new task."""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium').title()
        category = request.form.get('category', 'General').strip() or 'General'
        due_date_str = request.form.get('due_date', '').strip()
        user_id = session.get('user_id')

        if not title:
            logger.warning("Task creation attempted without title")
            flash('Task title is required', 'error')
            return redirect(url_for('home'))

        if len(title) > 255:
            logger.warning("Task title too long: %d characters", len(title))
            flash('Task title too long (max 255 characters)', 'error')
            return redirect(url_for('home'))

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash('Invalid due date format', 'error')
                return redirect(url_for('home'))

        if priority not in ('High', 'Medium', 'Low'):
            priority = 'Medium'

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to insert with user_id, fallback to without for old schema
        try:
            cursor.execute(
                'INSERT INTO tasks (title, description, due_date, priority, category, user_id) VALUES (?, ?, ?, ?, ?, ?)',
                (title, description, due_date.isoformat() if due_date else None, priority, category, user_id)
            )
        except Exception:
            cursor.execute(
                'INSERT INTO tasks (title, description, due_date, priority, category) VALUES (?, ?, ?, ?, ?)',
                (title, description, due_date.isoformat() if due_date else None, priority, category)
            )
        
        conn.commit()
        cursor.close()
        conn.close()

        if PROMETHEUS_AVAILABLE:
            TASK_OPERATIONS.labels(operation='create').inc()

        logger.info("Task created: %s", title)
        flash('Task created successfully', 'success')
        return redirect(url_for('home'))
    except Exception as exc:
        logger.error("Error creating task: %s", exc)
        flash('Error creating task', 'error')
        return redirect(url_for('home'))


@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, completed FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()

        if not row:
            flash('Task not found', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('home'))

        columns = [col[0] for col in cursor.description]
        task = row_to_dict(row, columns)
        new_status = 0 if task.get('completed') else 1

        cursor.execute('UPDATE tasks SET completed = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
        cursor.close()
        conn.close()

        if PROMETHEUS_AVAILABLE:
            TASK_OPERATIONS.labels(operation='toggle').inc()

        logger.info("Task %s status toggled to %s", task_id, new_status)
        flash('Task status updated', 'success')
        return redirect(url_for('home'))
    except Exception as exc:
        logger.error("Error toggling task %s: %s", task_id, exc)
        flash('Error updating task', 'error')
        return redirect(url_for('home'))


@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()

        if cursor.rowcount > 0:
            if PROMETHEUS_AVAILABLE:
                TASK_OPERATIONS.labels(operation='delete').inc()

            logger.info("Task %s deleted", task_id)
            flash('Task deleted successfully', 'success')
        else:
            logger.warning("Task %s not found for deletion", task_id)
            flash('Task not found', 'error')

        cursor.close()
        conn.close()
        return redirect(url_for('home'))
    except Exception as exc:
        logger.error("Error deleting task %s: %s", task_id, exc)
        flash('Error deleting task', 'error')
        return redirect(url_for('home'))


@app.route('/task/<int:task_id>/edit', methods=['POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium').title()
        category = request.form.get('category', 'General').strip() or 'General'
        due_date_str = request.form.get('due_date', '').strip()

        if not title:
            flash('Task title is required', 'error')
            return redirect(url_for('home'))

        if len(title) > 255:
            flash('Task title too long (max 255 characters)', 'error')
            return redirect(url_for('home'))

        if priority not in ('High', 'Medium', 'Low'):
            priority = 'Medium'

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash('Invalid due date format', 'error')
                return redirect(url_for('home'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks 
            SET title = ?, description = ?, priority = ?, category = ?, due_date = ?
            WHERE id = ?
            """,
            (title, description, priority, category, due_date.isoformat() if due_date else None, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Task updated successfully', 'success')
        return redirect(url_for('home'))
    except Exception as exc:
        logger.error("Error editing task %s: %s", task_id, exc)
        flash('Error updating task', 'error')
        return redirect(url_for('home'))


@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks')
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        response = {
            'status': 'healthy',
            'tasks_count': count,
            'environment': app.config['ENVIRONMENT'],
            'database': app.config['DB_TYPE']
        }
        logger.info("Health check passed")
        return jsonify(response), 200
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return jsonify({'status': 'unhealthy', 'error': str(exc)}), 500


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    return jsonify({'error': 'Prometheus client not installed'}), 503


# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning("404 error: %s", request.url)
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error("500 error: %s", error)
    return render_template('errors/500.html'), 500


@app.errorhandler(Exception)
def handle_exception(exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    logger.info("Starting Flask application")
    port = 8000 if app.config['DEBUG'] else 80
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

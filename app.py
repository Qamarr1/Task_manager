from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import logging
import sys
from datetime import datetime
from config import config, Config
from database import get_db_connection

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
app.config.from_object(config[env])
app.secret_key = app.config['SECRET_KEY']

# Azure Application Insights integration
if app.config.get('APPINSIGHTS_INSTRUMENTATION_KEY'):
    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        from opencensus.ext.azure import metrics_exporter
        from opencensus.ext.flask.flask_middleware import FlaskMiddleware
        
        # Add Azure monitoring
        middleware = FlaskMiddleware(
            app,
            exporter=metrics_exporter.new_metrics_exporter(
                connection_string=f"InstrumentationKey={app.config['APPINSIGHTS_INSTRUMENTATION_KEY']}"
            )
        )
        
        # Add Azure log handler
        azure_handler = AzureLogHandler(
            connection_string=f"InstrumentationKey={app.config['APPINSIGHTS_INSTRUMENTATION_KEY']}"
        )
        logger.addHandler(azure_handler)
        logger.info("Azure Application Insights enabled")
    except ImportError:
        logger.warning("Azure Application Insights packages not installed")
    except Exception as e:
        logger.error(f"Failed to initialize Application Insights: {e}")

logger.info(f"Application started in {env} mode")

@app.route('/')
def home():
    """Display all tasks"""
    try:
        logger.info("Fetching all tasks")
        conn = get_db_connection()
        tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
        conn.close()
        logger.info(f"Retrieved {len(tasks)} tasks")
        return render_template('index.html', tasks=tasks)
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        flash('Error loading tasks', 'error')
        return render_template('index.html', tasks=[])

@app.route('/task/add', methods=['POST'])
def add_task():
    """Create a new task"""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title:
            logger.warning("Task creation attempted without title")
            flash('Task title is required', 'error')
            return redirect(url_for('home'))
        
        if len(title) > 255:
            logger.warning(f"Task title too long: {len(title)} characters")
            flash('Task title too long (max 255 characters)', 'error')
            return redirect(url_for('home'))
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tasks (title, description) VALUES (?, ?)',
            (title, description)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Task created: {title}")
        flash('Task created successfully', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        flash('Error creating task', 'error')
        return redirect(url_for('home'))

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion status"""
    try:
        conn = get_db_connection()
        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        
        if task:
            new_status = 0 if task['completed'] else 1
            conn.execute('UPDATE tasks SET completed = ? WHERE id = ?', (new_status, task_id))
            conn.commit()
            logger.info(f"Task {task_id} status toggled to {new_status}")
            flash('Task status updated', 'success')
        else:
            logger.warning(f"Task {task_id} not found for toggle")
            flash('Task not found', 'error')
        
        conn.close()
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error toggling task {task_id}: {e}")
        flash('Error updating task', 'error')
        return redirect(url_for('home'))

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    """Delete a task"""
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        
        if result.rowcount > 0:
            logger.info(f"Task {task_id} deleted")
            flash('Task deleted successfully', 'success')
        else:
            logger.warning(f"Task {task_id} not found for deletion")
            flash('Task not found', 'error')
        
        conn.close()
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        flash('Error deleting task', 'error')
        return redirect(url_for('home'))

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        count = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        conn.close()
        
        response = {
            'status': 'healthy',
            'tasks_count': count,
            'environment': app.config['ENVIRONMENT'],
            'database': app.config['DB_TYPE']
        }
        logger.info("Health check passed")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    logger.info("Starting Flask application")
    port = 8000 if app.config['DEBUG'] else 80
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])

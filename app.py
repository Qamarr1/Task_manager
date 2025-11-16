from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    """Display homepage with tasks"""
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
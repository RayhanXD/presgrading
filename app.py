from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'presgrade2024'
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800,
    SESSION_COOKIE_NAME='presgrade_session'
)
SECRET_KEY = "pres2024"

CORS(app, resources={
    r"/*": {
        "origins": ["https://grade.rayhanm.com", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def default_route():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return redirect(url_for('grading'))  # Added closing parenthesis

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated'):
        return redirect(url_for('grading'))
        
    if request.method == 'POST':
        if request.form.get('secret_key') == SECRET_KEY:
            session['authenticated'] = True
            return redirect(url_for('grading'))
        return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/grading', methods=['GET', 'POST'])
@requires_auth
def grading():
    if request.method == 'POST':
        try:
            scores = {
                'strong_introduction': int(request.form.get('strong_introduction', 0)),
                'obvious_transitions': int(request.form.get('obvious_transitions', 0)), 
                'organization': int(request.form.get('organization', 0)),
                'research_explained': int(request.form.get('research_explained', 0)),
                'audio_visual': int(request.form.get('audio_visual', 0)),
                'delivery': int(request.form.get('delivery', 0)),
                'vocalized_pauses': int(request.form.get('vocalized_pauses', 0)),
                'professional_dress': int(request.form.get('professional_dress', 0)),
                'quote': int(request.form.get('quote', 0)),
                'conclusion': int(request.form.get('conclusion', 0)),
                'proper_timing': int(request.form.get('proper_timing', 0)),
                'preparation_evident': int(request.form.get('preparation_evident', 0))
            }
            
            total_score = sum(scores.values())
            student_email = request.form.get('student_email', '').strip()
            compliments = request.form.get('compliments', '').strip()
            suggestions = request.form.get('suggestions', '').strip()

            if not student_email:
                raise ValueError("Student email is required")

            email_sent = trigger_retool_workflow(
                student_email,
                total_score,
                compliments,
                suggestions,
                scores
            )
            return render_template('index.html', submitted=True, total_score=total_score, email_sent=email_sent)
        except Exception as e:
            print(f"Error processing form: {e}")
            return render_template('index.html', submitted=True, error=str(e))
    return render_template('index.html', submitted=False)

def trigger_retool_workflow(student_email, total_score, compliments, suggestions, scores):
    WORKFLOW_URL = "https://api.retool.com/v1/workflows/c34a5f92-6934-49a5-ba0f-9907d499163b/startTrigger"
    RETOOL_API_KEY = "retool_wk_424e88c426f64dbb9a7d96f7fab46bea"
    
    payload = {
        "data": {
            "student_email": student_email,
            "total_score": total_score,
            "compliments": compliments,
            "suggestions": suggestions,
            **scores
        }
    }
    
    headers = {
        "X-Workflow-Api-Key": RETOOL_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(WORKFLOW_URL, json=payload, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error triggering workflow: {e}")
        return False

@app.route('/health')
def health_check():
    return {"status": "healthy"}, 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
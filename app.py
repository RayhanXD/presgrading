from flask import Flask, render_template, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://grading.rayhanm.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
        student_email = request.form.get('student_email', '')
        compliments = request.form.get('compliments', '')
        suggestions = request.form.get('suggestions', '')

        # Trigger email workflow
        email_sent = trigger_retool_workflow(
            student_email,
            total_score,
            compliments,
            suggestions,
            scores
        )

        return render_template('index.html', submitted=True, total_score=total_score, email_sent=email_sent)

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
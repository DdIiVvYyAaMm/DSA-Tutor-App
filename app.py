from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import sqlite3
import json
from openai import OpenAI
import os

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY")
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/user_progress')
@login_required
def user_progress():
    print("Accessing /user_progress")  # Debugging statement
    return jsonify({
        'username': session.get('username'),
        'questions_attempted': session.get('questions_attempted', 0),
        'questions_correct': session.get('questions_correct', 0)
    })


def get_question_by_id(question_id):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id=?", (question_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "question_text": row[1],
            "question_type": row[2],
            "options": json.loads(row[3]) if row[3] else None
        }
    else:
        return None
    
def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn
    
def update_user_progress(username, question_id, correct):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch current progress
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user:
        questions_attempted = user["questions_attempted"] + 1
        questions_correct = user["questions_correct"] + (1 if correct else 0)
        
        # Update correct or incorrect question IDs
        correct_ids = json.loads(user["correct_ids"] or "[]")
        incorrect_ids = json.loads(user["incorrect_ids"] or "[]")
        if correct:
            correct_ids.append(question_id)
        else:
            incorrect_ids.append(question_id)
        
        # Update user progress in the database
        cursor.execute('''
            UPDATE users
            SET questions_attempted = ?, questions_correct = ?,
                correct_ids = ?, incorrect_ids = ?
            WHERE username = ?
        ''', (questions_attempted, questions_correct,
              json.dumps(correct_ids), json.dumps(incorrect_ids), username))
    else:
        # Create a new record if user does not exist
        correct_ids = [question_id] if correct else []
        incorrect_ids = [question_id] if not correct else []
        cursor.execute('''
            INSERT INTO users (username, questions_attempted, questions_correct,
                               correct_ids, incorrect_ids)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, 1, (1 if correct else 0),
              json.dumps(correct_ids), json.dumps(incorrect_ids)))
    
    conn.commit()
    conn.close()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/get_question', methods=['POST'])
@login_required
def get_question():
    question_id = request.json.get('question_id', 1)  # Default to question 1
    question = get_question_by_id(question_id)
    if question:
        return jsonify(question)
    else:
        return jsonify({"error": "Question not found"}), 404

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    try:
        data = request.json
        question = data.get('question')
        user_response = data.get('user_response')
        question_id = data.get('question_id')

        if 'username' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        # Ensure both question and user_response are present
        if not question or not user_response:
            return jsonify({'error': 'Invalid input'}), 400

        # Call ChatGPT (using gpt-3.5-turbo) for evaluation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant providing feedback on student comprehension responses."},
                {"role": "user", "content": f"Question: {question}\nUser Response: {user_response}\nProvide concise feedback on the correctness and quality of the response."}
            ],
            max_tokens=150,
            temperature=0.2
        )

        feedback = response.choices[0].message.content.strip()
        correct = "correct" in feedback.lower()
        # Update progress in the database
        update_user_progress(session['username'], question_id, correct)

        # Update session data
        session['questions_attempted'] += 1
        if correct:
            session['questions_correct'] += 1
            session['correct_ids'].append(question_id)
        else:
            session['incorrect_ids'].append(question_id)

        return jsonify({'feedback': feedback, 'correct': correct})

    except Exception as e:
        # Log the error to the console for debugging
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        session['questions_attempted'] = 0
        session['questions_correct'] = 0
        session['correct_ids'] = []
        session['incorrect_ids'] = []
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)



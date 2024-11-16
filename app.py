from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import sqlite3
import json
from openai import OpenAI
import os
import csv

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


import csv

# def load_questions_from_csv(csv_file_path='Q3_questions.csv'):
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile, delimiter='\t')  # Assuming tab-separated values
#         for row in reader:
#             cursor.execute('''
#                 INSERT OR IGNORE INTO questions (
#                     id, sub_question, theme, tree_dependency, question, 
#                     option_a, option_b, option_c, option_d, mcq_answer, 
#                     function, code, tree_image_path
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', (
#                 row['question_no'],
#                 row['sub_question'],
#                 row['theme'],
#                 row['tree_dependency'],
#                 row['question'],
#                 row['option_a'],
#                 row['option_b'],
#                 row['option_c'],
#                 row['option_d'],
#                 row['mcq_answer'],
#                 row['function'],
#                 row['code'],
#                 row['tree_image_path']
#             ))
    
#     conn.commit()
#     conn.close()

def get_question_by_id(question_id, theme=None):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    if theme:
        cursor.execute("SELECT * FROM questions WHERE id=? AND theme=?", (question_id, theme))
    else:
        cursor.execute("SELECT * FROM questions WHERE id=?", (question_id,))
        
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "question_no": row[1],
            "sub_question": row[2],
            "theme": row[3],
            "tree_dependency": row[4],
            "question_text": row[5],
            "option_a": row[6],
            "option_b": row[7],
            "option_c": row[8],
            "option_d": row[9],
            "mcq_answer": row[10],
            "function": row[11],
            "code": row[12],
            "tree_image_path": row[13]
        }
    else:
        return None



# def get_question_by_id(question_id):
#     conn = sqlite3.connect('questions.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM questions WHERE id=?", (question_id,))
#     row = cursor.fetchone()
#     conn.close()
#     if row:
#         return {
#             "id": row[0],
#             "question_text": row[1],
#             "question_type": row[2],
#             "options": json.loads(row[3]) if row[3] else None
#         }
#     else:
#         return None
    
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
    try:
        data = request.json
        question_id = data.get('question_id', 1)  # Default to question 1
        theme = data.get('theme')  # Get the selected theme
        
        try:
            question_id = int(question_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid question ID"}), 400

        question = get_question_by_id(question_id, theme)
        if question:
            return jsonify(question)
        else:
            # If no question found with the selected theme, try fetching without theme
            question = get_question_by_id(question_id)
            if question:
                return jsonify(question)
            else:
                return jsonify({"error": "Question not found"}), 404
    except Exception as e:
        print(f"Error in get_question: {e}")
        return jsonify({"error": "Internal server error"}), 500


# @app.route('/get_question', methods=['POST'])
# @login_required
# def get_question():
#     question_id = request.json.get('question_id', 1)  # Default to question 1
#     question = get_question_by_id(question_id)
#     if question:
#         return jsonify(question)
#     else:
#         return jsonify({"error": "Question not found"}), 404

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    try:
        data = request.json
        question = data.get('question')
        code  = data.get('code', '')
        user_response = data.get('user_response')
        question_id = data.get('question_id')
        tree_dependency = data.get('tree_dependency')  # Get the tree dependency for the question

        print(f"Question ID: {question_id}, Question: {question}, User Response: {user_response}")

        if 'username' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        # Ensure both question and user_response are present
        if not question or not user_response:
            return jsonify({'error': 'Invalid input'}), 400
        
        # Fetch the correct answer from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT mcq_answer FROM questions WHERE id=?", (question_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Question not found in the database.'}), 404
        
        # correct_answer = row[0].strip().upper()
        # user_answer = user_response.strip().upper()

        # correct = user_answer == correct_answer
        # prompt = f"Question: {question}\n"
        # if code:
        #     prompt += f"Code:\n{code}\n"
        # prompt += f"User Response: {user_response}\n"
        # prompt += "Provide feedback on the user's response, explaining why it is correct or incorrect."

        #Not using prompt for now, putting directly in message to OpenAI

        # Call ChatGPT (using gpt-4o) for evaluation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant providing feedback on student comprehension responses."},
                {"role": "user", "content": f"Question: {question}\n Code: {code}\n Tree for Question: {tree_dependency}\nUser Response: {user_response}\nProvide concise feedback on the correctness and quality of the response."}
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
            session['current_theme'] = session.get('current_theme')
        else:
            session['incorrect_ids'].append(question_id)
            session['current_theme'] = session.get('current_theme')

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
        session['current_theme'] = None  # Initialize current theme
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


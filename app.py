from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total number of questions
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    # Get user progress
    cursor.execute("""
        SELECT questions_attempted, questions_correct 
        FROM users 
        WHERE username = ?
    """, (session['username'],))
    
    user_data = cursor.fetchone()
    
    if user_data:
        questions_attempted = user_data['questions_attempted']
        questions_correct = user_data['questions_correct']
    else:
        questions_attempted = 0
        questions_correct = 0
    print(questions_correct)
    conn.close()
    
    return jsonify({
        'username': session.get('username'),
        'questions_attempted': questions_attempted,
        'questions_correct': questions_correct,
        'total_questions': total_questions
    })


def get_question_by_id(question_id):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id=?", (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    # Base question data
    question_data = {
        "id": row[0],
        "question_text": row[1],
        "question_type": row[2],
        "options": json.loads(row[3]) if row[3] else None,
        "is_embed": False
    }
    
    # Special handling for question 5
    if question_id == 5:
        try:
            # Read directly from Q5_questions.csv
            q5_df = pd.read_csv('Q5_questions.csv')
            first_q5 = q5_df[q5_df['question_no'] == 5].iloc[0]
            
            # Override the question text and add embed URL
            question_data.update({
                "question_text": first_q5['question'],  # Use question from CSV
                "url": first_q5['url'],
                "is_embed": True
            })
        except Exception as e:
            print(f"Error reading Q5 data: {e}")
    
    return question_data
    
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
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        data = request.json
        question = data.get('question')
        user_response = data.get('user_response')

        # Ensure both question and user_response are present
        if not question or not user_response:
            return jsonify({'error': 'Invalid input'}), 400

        # Call ChatGPT (using gpt-3.5-turbo) for evaluation
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant providing feedback on student comprehension responses."},
                {"role": "user", "content": f"Question: {question}\nUser Response: {user_response}\nProvide concise feedback on the correctness and quality of the response."}
            ],
            max_tokens=150,
            temperature=0.7
        )

        feedback = response['choices'][0]['message']['content'].strip()
        return jsonify({'feedback': feedback})

    except Exception as e:
        # Log the error to the console for debugging
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)




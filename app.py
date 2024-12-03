from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from functools import wraps
import sqlite3
import json
import random
from openai import OpenAI
import os
#from dotenv import load_dotenv
import markdown

app = Flask(__name__)
#load_dotenv()

# @app.before_request
# def clear_session_on_start():
#     session.clear()

app.secret_key = os.getenv("FLASK_SECRET_KEY")

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY")
)

QUESTION_TYPE_MAP = {
    'q1': 'fill_in_blanks',
    'q2': 'mcq_traversal',
    'q3': 'mcq_code',
    'q4': 'time_complexity',
    'q5': 'parsons'
}

# Add default context for each question type
DEFAULT_CONTEXTS = {
    'fill_in_blanks': """
# Binary Tree Basics
A binary tree is a tree data structure where each node has at most two children.
These children are referred to as the left child and right child.

Key terms:
- Root: The topmost node of the tree
- Leaf: Nodes with no children
- Depth: The length of the path from root to the node
    """,
    'mcq_traversal': """
# Tree Traversals
Tree traversal refers to the process of visiting each node in a tree exactly once.
There are different ways to traverse a tree systematically.

Common traversal methods:
- Inorder (Left, Root, Right)
- Preorder (Root, Left, Right)
- Postorder (Left, Right, Root)
    """,
    'mcq_code': """
# Tree Operations
Binary trees support various operations like insertion, deletion, and searching.
Understanding these operations is crucial for working with tree data structures.

Common operations:
- Insertion: Adding new nodes
- Deletion: Removing nodes
- Search: Finding specific nodes
    """,
    'time_complexity':"""
blahblahblah
""",
'parsons':"""
blahblahblah
"""
}

# @app.before_request
# def clear_session_on_start():
#     session.clear()

# Session Management
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def initialize_user_queue():
    """Initialize user session with first question and required tracking variables"""
    if 'username' in session:
        # Create/update user in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (
                username, current_question, 
                q1_attempts, q1_correct,
                q2_attempts, q2_correct,
                q3_attempts, q3_correct,
                q4_attempts, q4_correct,
                q5_attempts, q5_correct,
                current_theme
            ) VALUES (?, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'B')
        """, (session['username'],))
        conn.commit()
        conn.close()

    if 'question_queue' not in session:
        session['question_queue'] = ['q1']
        session['current_theme'] = 'B'
        session['current_question'] = 'q1'
        session['queue_building'] = True
        session.modified = True

# Database Connection
def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn

# Queue Management Functions
# def manage_queue_progression():
#     """Handle adding new questions to queue based on completion"""
#     if 'q4' not in session['question_queue'] and any(session.get(f'q{i}_correct', 0) >= 5 for i in range(1, 4)):
#         session['question_queue'].append('q4')
#         session.modified = True
    
#     if 'q5' not in session['question_queue'] and 'q4' in session['question_queue'] and any(session.get(f'q{i}_correct', 0) >= 5 for i in range(1, 5)):
#         session['question_queue'].append('q5')
#         session.modified = True

def update_queue_state(question_type):
    """Remove questions from queue when completed and add new ones"""
    correct_count = session.get(f'{question_type}_correct', 0)
    print(correct_count)
    if correct_count >= 5 and question_type in session['question_queue']:
        session['question_queue'].remove(question_type)
        #manage_queue_progression()
        session.modified = True

# Question Retrieval Functions
def get_random_question_by_type(question_type, theme):
    """Get random question from database based on type and theme"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Special handling for q4 to use q2_questions table

    # if question_type == 'q4':
    #     table_name = 'q2_questions'
    # else:
    table_name = f"{question_type}_questions"
    
    # Special handling for parsons puzzles (q5) which don't have theme
    if question_type in ['q5', 'q4']:
        cursor.execute(f"""
            SELECT * FROM {table_name}
            ORDER BY RANDOM()
            LIMIT 1
        """)
    else:
        cursor.execute(f"""
            SELECT * FROM {table_name}
            WHERE theme = ?
            ORDER BY RANDOM()
            LIMIT 1
        """, (theme,))
    
    question = cursor.fetchone()
    conn.close()
    return question

def format_question_response(question, question_type):
    """Format question data based on question type"""
    if not question:
        return None
    
    # Common base data for all questions
    base_data = {
        'question_no': question['question_no'],
        'sub_question': question['sub_question'],
        'type': question_type
    }
    
    # Add theme and tree dependency only for non-parsons questions
    if question_type not in ['parsons', 'time_complexity']:
        base_data.update({
            'theme': question['theme'],
            'tree_image_path': question['tree_image_path'],
            'tree_dependency': question['tree_dependency']
        })
    
    if question_type == 'parsons':
        base_data.update({
            'question_text': question['question'],
            'url': question['url']
        })
    elif question_type == 'fill_in_blanks':
        base_data.update({
            'root_question': question['root_question'],
            'leaf_question': question['leaf_question'],
            'depth_question': question['depth_question'],
            'child_question': question['child_question'],
            'parent_question': question['parent_question']
        })
    elif question_type == 'mcq_traversal':
        base_data.update({
            'question_text': question['question_text'],
            'options': {
                'A': question['option_a'],
                'B': question['option_b'],
                'C': question['option_c'],
                'D': question['option_d']
            }
        })
    elif question_type == 'mcq_code':
        base_data.update({
            'question_text': question['question'],
            'options': {
                'A': question['option_a'],
                'B': question['option_b'],
                'C': question['option_c'],
                'D': question['option_d']
            },
            'function': question['function'],
            'code': question['code']
        })
    elif question_type == 'time_complexity':
        base_data.update({
            'question_text': question['question_text'],
            'options': {
                'A': question['option_1'],
                'B': question['option_2'],
                'C': question['option_3'],
                'D': question['option_4']
            },
            'code': question['code']  # Assuming time_complexity questions include code
        })
    
    return base_data

# Answer Evaluation Functions
def evaluate_answer(question_type, question_no, sub_question, theme, user_response):
    """Evaluate user answer based on question type"""
    # For parsons puzzles, always return True as evaluation happens on external site
    
    if question_type == 'parsons':
        return True
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if question_type == 'fill_in_blanks':
        cursor.execute("""
            SELECT root_answer, leaf_answer, depth_answer, child_answer, parent_answer 
            FROM q1_questions 
            WHERE question_no = ? AND sub_question = ? AND theme = ?
        """, (question_no, sub_question, theme))
        answers = cursor.fetchone()
        correct = any(answer == response for answer, response in zip(answers, user_response.values()))

    else:
        table_name = ''
        if question_type == 'mcq_traversal':
            table_name = 'q2_questions'
        elif question_type == 'mcq_code':
            table_name = 'q3_questions'
        elif question_type == 'time_complexity':
            table_name = 'q4_questions'
        answer_column = 'correct_answer' if question_type == 'mcq_traversal' else 'mcq_answer'
        
        cursor.execute(f"""
            SELECT {answer_column}
            FROM {table_name}
            WHERE question_no = ? AND sub_question = ? AND theme = ?
        """, (question_no, sub_question, theme))
        answers = [cursor.fetchone()]
        print("answers:", answers)
        correct = user_response == answers[0][0]
    
    conn.close()

    # Returns whether the given answer is correct as well as the correct answer(s)
    return (correct, answers)

# Route Handlers
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        initialize_user_queue()
        return redirect(url_for('index'))
    return render_template('login.html')

def get_context_for_type(question_type):
    """
    Get the context content for a specific question type.
    Tries to load from static folder first, falls back to default if not found.
    """
    try:
        # Construct path to context.md file
        context_path = os.path.join('static', question_type, 'context.md')
        
        # Check if file exists
        if os.path.exists(context_path):
            with open(context_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Convert markdown to HTML
                return markdown.markdown(content, extensions=['tables', 'fenced_code'])
        else:
            # Return default context if file doesn't exist
            return markdown.markdown(DEFAULT_CONTEXTS.get(question_type, ""))
    except Exception as e:
        print(f"Error loading context: {e}")
        return markdown.markdown(DEFAULT_CONTEXTS.get(question_type, ""))

@app.route('/get_context/<question_type>')
@login_required
def get_context(question_type):
    """Serve context content for a specific question type"""
    try:
        content = get_context_for_type(question_type)
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_question', methods=['POST'])
@login_required
def get_question():
    try:
        input_data = request.get_json()
        is_next = input_data.get('is_next', False)
        # Handle queue building phase
        if is_next and session.get('queue_building', True):
            if len(session['question_queue']) < 5:
                next_question = f'q{len(session["question_queue"]) + 1}'
                if next_question not in session['question_queue']:
                    session['question_queue'].append(next_question)
                session['current_question'] = next_question
            else:
                session['queue_building'] = False
        
        # Select question type
        if session.get('queue_building', True) or not is_next:
            question_type = session['current_question']
        else:
            question_type = random.choice(session['question_queue'])
            session['current_question'] = question_type
        
        # Get and format question
        theme = session.get('current_theme', 'B')
        raw_question = get_random_question_by_type(question_type, theme)

        formatted_question = format_question_response(raw_question, 
                                                   QUESTION_TYPE_MAP.get(question_type, 'unknown'))
        
        if not formatted_question:
            return jsonify({'error': 'No question found'})
        
        # Add context to the response
        formatted_question['context'] = get_context_for_type(QUESTION_TYPE_MAP.get(question_type))
        
        # Add queue status information
        formatted_question['queue_status'] = {
            'current_queue': session['question_queue'],
            'building_phase': session.get('queue_building', True),
            'current_question': session['current_question'],
            'progress': {
                f'q{i}': session.get(f'q{i}_correct', 0) for i in range(1, 6)
            }
        }
        
        session.modified = True
        return jsonify(formatted_question)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    data = request.json
    question_type = data.get('type')
    question_no = data.get('question_no')
    sub_question = data.get('sub_question')
    theme = data.get('theme')
    user_response = data.get('user_response')
    question_text = data.get('question_text')
    code = data.get('code', '')
    tree_dependency = data.get('tree_dependency')

    # print("question_text:", question_text)
    # print("code:", code)
    # print("tree_dependency:", tree_dependency)
    # print("user_response:", user_response)

    # Update attempts in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE users 
        SET q{question_no}_attempts = q{question_no}_attempts + 1 
        WHERE username = ?
    """, (session['username'],))
    conn.commit()

    # Extract MCQ and comprehension responses for code questions
    if question_type == 'mcq_code':
        mcq_answer = user_response.get('mcq')
        comprehension = user_response.get('comprehension', '')
        
        # First evaluate MCQ answer
        correct, answers = evaluate_answer(
            question_type,
            question_no,
            sub_question,
            theme,
            mcq_answer
        )
    else:
        # Handle other question types normally
        correct, answers = evaluate_answer(
            question_type,
            question_no,
            sub_question,
            theme,
            user_response
        )

    # Update progress if correct
    if correct:
        cursor.execute(f"""
            UPDATE users 
            SET q{question_no}_correct = q{question_no}_correct + 1 
            WHERE username = ?
        """, (session['username'],))
        conn.commit()
        
        q_type = f'q{question_no}_correct'
        session[q_type] = session.get(q_type, 0) + 1
        update_queue_state(f'q{question_no}')

    # Gets the correct answer(s) for the question
    if question_type == "fill_in_blanks":
        answers = [answer for answer in answers]
    else:
        answers = [answer[0] for answer in answers]
    
    # Prepare GPT prompt based on question type
    if question_type == 'mcq_code':
        prompt = f"""**IMPORTANT: CONSIDER  THE STUDENT'S COMPREHENSION QUESTION RESPONSE CORRECT IF IT IS SOMEWHAT CORRECT.**
                     The student was asked a multiple choice question and a comprehension question.
                     The question that was asked to the student is as follows: "{question_text}. Max depth is defined as the number of edges from the root node to the furthest leaf node.". 
                     The Python code provided to the student is as follows:\n{code}\n. 
                     The binary tree dependency that was provided to the students is as follows: {tree_dependency}.
                     To the multiple choice question, the student answered:{mcq_answer}.
                     To the comprehension question, the student answered: "{comprehension}".
                     This is the correct answer to the multiple choice:{answers}.
                     Provide specific feedback for both their multiple choice answer and their comprehension answer.
                     If the student's response has sufficiently answered the question and is correct or mostly correct, the only output should be congratulating the student and letting them know they answered the question correctly.
                     If the student has not sufficiently answered the question, output concise, brief feedback and include the correct answer. Avoid heavy terminology and do not include the dependency tree in your feedback message.
                     Address the student directly in the output.
                     **IMPORTANT: BE VERY LENIENT WHEN EVALUATING THE STUDENT'S COMPREHENSION QUESTION RESPONSE FOR CORRECTNESS.**
                     Be mildly encouraging in your response."""
    elif question_type == "fill_in_blanks":
        prompt = f"""**IMPORTANT: DO NOT EVALUATE ANY FORMAT DISCREPANCIES BETWEEN THE STUDENT'S RESPONSE AND THE CORRECT ANSWER.**
                     The question that was asked to the student is as follows: "{question_text} . Max depth is defined as the number of edges from the root node to the furthest leaf node.". 
                     The Python code provided to the student is as follows:\n{code}\n. 
                     The binary tree dependency that was provided to the students is as follows: {tree_dependency}.
                     These are the student's responses to the posed subquestions: "{user_response}". Please disregard the formatting of the student's answer.
                     These are the correct answers for each subquestion:{answers}.
                     Be very lenient when evaluating the student's response for correctness.
                     If the student's response has sufficiently answered the question and is correct or mostly correct, the only output should be congratulating the student and letting them know they answered the question correctly.
                     If the student has not sufficiently answered the question, output concise, brief feedback and include the correct answer. Avoid heavy terminology and do not include the dependency tree in your feedback message.
                     **IMPORTANT: IF THERE ARE ANY SPACING DIFFERENCES, DIFFERENCES IN QUOTATION MARKS, DIFFERENCES IN COMMAS, OR DIFFERENCES IN THE ORDER OF NODES BETWEEN THE STUDENT'S RESPONSE AND THE CORRECT ANSWER, CONSIDER THE STUDENT'S RESPONSE CORRECT.**
                     Address the student directly in the output.
                     Be mildly encouraging in your response."""
    else:
        prompt = f"""The question that was asked to the student is as follows: "{question_text}. Max depth is defined as the number of edges from the root node to the furthest leaf node.". 
                     The Python code provided to the student is as follows:\n{code}\n. 
                     The binary tree dependency that was provided to the students is as follows: {tree_dependency}.
                     This is the student's multiple choice option selection: "{user_response}".
                     This is the correct multiple choice option:{answers}.
                     If the student has selected the correct multiple choice option, the only output should be congratulating the student and letting them know they answered the question correctly.
                     If the student has selected an incorrect multiple choice option, output concise, brief feedback and include the correct answer. Avoid heavy terminology and do not include the dependency tree in your feedback message.
                     Address the student directly in the output.
                     Be mildly encouraging in your response."""
        
    print("prompt:", prompt)

    # Get GPT feedback
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant providing feedback on a student's answer to a question related to binary trees."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.2
    )
    
    feedback = response.choices[0].message.content.strip()
    conn.close()

    is_complete = len(session['question_queue']) <= 1 and not session.get('queue_building', True)
    print(is_complete)

    # Check if queue is empty and building phase is complete
    #is_complete = len(session['question_queue']) == 0 and not session.get('queue_building', True)
    
    return jsonify({
        'correct': correct,
        'feedback': feedback,
        'queue_status': {
            'current_queue': session['question_queue'],
            'building_phase': session.get('queue_building', True),
            'current_question': session['current_question'],
            'progress': {
                f'q{i}': session.get(f'q{i}_correct', 0) for i in range(1, 6)
            },
            'is_complete': is_complete
        }
    })

@app.route('/stats')
@login_required
def stats():
    # Get user stats from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            q1_attempts, q1_correct,
            q2_attempts, q2_correct,
            q3_attempts, q3_correct,
            q4_attempts, q4_correct,
            q5_attempts, q5_correct
        FROM users 
        WHERE username = ?
    """, (session['username'],))
    
    user_stats = cursor.fetchone()
    conn.close()
    
    if not user_stats:
        return redirect(url_for('index'))
    
    # Calculate statistics
    stats = {
        'q1_attempts': user_stats[0],
        'q1_correct': user_stats[1],
        'q1_rate': round((user_stats[1] / user_stats[0] * 100) if user_stats[0] > 0 else 0, 1),
        
        'q2_attempts': user_stats[2],
        'q2_correct': user_stats[3],
        'q2_rate': round((user_stats[3] / user_stats[2] * 100) if user_stats[2] > 0 else 0, 1),
        
        'q3_attempts': user_stats[4],
        'q3_correct': user_stats[5],
        'q3_rate': round((user_stats[5] / user_stats[4] * 100) if user_stats[4] > 0 else 0, 1),
        
        'q4_attempts': user_stats[6],
        'q4_correct': user_stats[7],
        'q4_rate': round((user_stats[7] / user_stats[6] * 100) if user_stats[6] > 0 else 0, 1),
        
        'q5_attempts': user_stats[8],
        'q5_correct': user_stats[9],
        'q5_rate': round((user_stats[9] / user_stats[8] * 100) if user_stats[8] > 0 else 0, 1),
    }
    
    # Calculate totals
    total_attempts = sum(user_stats[i] for i in range(0, 10, 2))
    total_correct = sum(user_stats[i] for i in range(1, 10, 2))
    
    stats.update({
        'total_attempts': total_attempts,
        'total_correct': total_correct,
        'total_rate': round((total_correct / total_attempts * 100) if total_attempts > 0 else 0, 1)
    })
    
    return render_template('stats.html', username=session['username'], stats=stats)

@app.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    data = request.json
    new_theme = data.get('theme')
    if new_theme in ['B', 'H', 'R', 'M']:
        session['current_theme'] = new_theme
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid theme'}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
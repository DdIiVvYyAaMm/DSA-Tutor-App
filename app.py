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


QUESTION_TYPE_MAP = {
    'q1': 'fill_in_blanks',
    'q2': 'mcq_traversal',
    'q3': 'mcq_code',
    'q4': 'mcq_traversal',  # Using same as q2
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
    'timecomplexity':"""
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
    if 'question_queue' not in session:
        session['question_queue'] = ['q1']  # Start with only Q1
        session['q1_correct'] = 0
        session['q2_correct'] = 0
        session['q3_correct'] = 0
        session['q4_correct'] = 0
        session['q5_correct'] = 0
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

    if question_type == 'q4':
        table_name = 'q2_questions'
    else:
        table_name = f"{question_type}_questions"
    
    # Special handling for parsons puzzles (q5) which don't have theme
    if question_type == 'q5':
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
    if question_type != 'parsons':
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
    
    return base_data

# Answer Evaluation Functions
def evaluate_answer(question_type, question_no, sub_question, theme, user_response):
    """Evaluate user answer based on question type"""
    # For parsons puzzles, always return True as evaluation happens on external site
    
    if question_type == 'parsons':
        return True
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
        correct = any(user_response == answer for answer in answers)
    else:
        table_name = 'q2_questions' if question_type == 'mcq_traversal' else 'q3_questions'
        answer_column = 'correct_answer' if question_type == 'mcq_traversal' else 'mcq_answer'
        
        cursor.execute(f"""
            SELECT {answer_column}
            FROM {table_name}
            WHERE question_no = ? AND sub_question = ? AND theme = ?
        """, (question_no, sub_question, theme))
        answer = cursor.fetchone()
        correct = user_response == answer[0]
    
    conn.close()
    return correct

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

    # Extract MCQ and comprehension responses for code questions
    if question_type == 'mcq_code':
        mcq_answer = user_response.get('mcq')
        comprehension = user_response.get('comprehension', '')
        
        # First evaluate MCQ answer
        correct = evaluate_answer(
            question_type,
            question_no,
            sub_question,
            theme,
            mcq_answer
        )
    else:
        # Handle other question types normally
        correct = evaluate_answer(
            question_type,
            question_no,
            sub_question,
            theme,
            user_response
        )

    # Update progress if correct
    if correct:
        q_type = f'q{question_no}_correct'
        session[q_type] = session.get(q_type, 0) + 1
        update_queue_state(f'q{question_no}')
    
    # Prepare GPT prompt based on question type
    if question_type == 'mcq_code':
        prompt = f"""Evaluate the student's understanding of the following code question:

Question: {question_text}

Code:
{code}

Student's MCQ Answer: {mcq_answer}

Student's Code Comprehension:
{comprehension}

Provide specific feedback on:
1. The correctness of their MCQ choice
2. Their understanding of the code based on their written explanation
Keep the feedback concise but informative."""
    else:
        prompt = f"Question: {question_text}\nCode: {code}\nTree Dependency: {tree_dependency}\nUser Response: {user_response}\nProvide concise feedback on the correctness and quality of the response."

    # Get GPT feedback
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant providing feedback on student comprehension responses."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.2
    )
    
    feedback = response.choices[0].message.content.strip()

    
    return jsonify({
        'correct': correct,
        'feedback': feedback,
        'queue_status': {
            'current_queue': session['question_queue'],
            'building_phase': session.get('queue_building', True),
            'current_question': session['current_question'],
            'progress': {
                f'q{i}': session.get(f'q{i}_correct', 0) for i in range(1, 6)
            }
        }
    })

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
import sqlite3
import csv
import json
import os

def init_db():
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            current_question INTEGER DEFAULT 1,
            q1_attempts INTEGER DEFAULT 0,
            q1_correct INTEGER DEFAULT 0,
            q2_attempts INTEGER DEFAULT 0,
            q2_correct INTEGER DEFAULT 0,
            q3_attempts INTEGER DEFAULT 0,
            q3_correct INTEGER DEFAULT 0,
            q4_attempts INTEGER DEFAULT 0,
            q4_correct INTEGER DEFAULT 0,
            q5_attempts INTEGER DEFAULT 0,
            q5_correct INTEGER DEFAULT 0,
            current_theme TEXT DEFAULT 'B'
        )
    ''')
    
    # Q1 Table (Fill in Blanks)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS q1_questions (
            question_no INTEGER,
            sub_question INTEGER,
            theme TEXT,
            tree_dependency TEXT,
            root_question TEXT,
            leaf_question TEXT,
            depth_question TEXT,
            child_question TEXT,
            parent_question TEXT,
            root_answer TEXT,
            leaf_answer TEXT,
            depth_answer TEXT,
            child_answer TEXT,
            parent_answer TEXT,
            mistake1 TEXT,
            mistake2 TEXT,
            mistake3 TEXT,
            feedback1 TEXT,
            feedback2 TEXT,
            feedback3 TEXT,
            tree_image_path TEXT,
            PRIMARY KEY (question_no, sub_question, theme)
        )
    ''')
    
    # Q2 Table (Tree Traversals)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS q2_questions (
            question_no INTEGER,
            sub_question INTEGER,
            theme TEXT,
            tree_dependency TEXT,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            answer_explanation TEXT,
            mistake_a TEXT,
            mistake_b TEXT,
            mistake_c TEXT,
            mistake_d TEXT,
            feedback_a TEXT,
            feedback_b TEXT,
            feedback_c TEXT,
            feedback_d TEXT,
            tree_image_path TEXT,
            PRIMARY KEY (question_no, sub_question, theme)
        )
    ''')
    
    # Q3 Table (Code Understanding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS q3_questions (
            question_no INTEGER,
            sub_question INTEGER,
            theme TEXT,
            tree_dependency TEXT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            mcq_answer TEXT,
            function TEXT,
            code TEXT,
            tree_image_path TEXT,
            PRIMARY KEY (question_no, sub_question, theme)
        )
    ''')
    
    # Q4 Table (Time Complexity)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS q4_questions (
            question_no INTEGER,
            sub_question INTEGER,
            theme TEXT,
            question_text TEXT,
            option_1 TEXT,
            option_2 TEXT,
            option_3 TEXT,
            option_4 TEXT,
            mcq_answer TEXT,
            code TEXT,
            PRIMARY KEY (question_no, sub_question, theme)
        )
    ''')
    
    # Q5 Table (Parsons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS q5_questions (
            question_no INTEGER,
            sub_question INTEGER,
            question TEXT,
            url TEXT,
            PRIMARY KEY (question_no, sub_question)
        )
    ''')
    
    conn.commit()
    conn.close()

def validate_theme(theme):
    return theme in ['B', 'H', 'R', 'M']

def load_q1_questions(csv_file_path='Q1_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not validate_theme(row['theme']):
                print(f"Invalid theme {row['theme']} found in row {row}")
                continue
                
            cursor.execute('''
                INSERT INTO q1_questions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                int(row['question_no']),
                int(row['sub_question']),
                row['theme'],
                row['tree_dependency'],
                row['root_question'],
                row['leaf_question'],
                row['depth_question'],
                row['child_question'],
                row['parent_question'],
                row['root_answer'],
                row['leaf_answer'],
                row['depth_answer'],
                row['child_answer'],
                row['parent_answer'],
                row['mistake1'],
                row['mistake2'],
                row['mistake3'],
                row['feedback1'],
                row['feedback2'],
                row['feedback3'],
                row['tree_image_path']
            ))
    conn.commit()
    conn.close()

def load_q2_questions(csv_file_path='Q2_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not validate_theme(row['theme']):
                continue
                
            cursor.execute('''
                INSERT INTO q2_questions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                int(row['question_no']),
                int(row['sub_question']),
                row['theme'],
                row['tree_dependency'],
                row['question_text'],
                row['option_a'],
                row['option_b'],
                row['option_c'],
                row['option_d'],
                row['correct_answer'],
                row['answer_explanation'],
                row['mistake_a'],
                row['mistake_b'],
                row['mistake_c'],
                row['mistake_d'],
                row['feedback_a'],
                row['feedback_b'],
                row['feedback_c'],
                row['feedback_d'],
                row['tree_image_path']
            ))
    conn.commit()
    conn.close()

def load_q3_questions(csv_file_path='Q3_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not validate_theme(row['theme']):
                continue
                
            cursor.execute('''
                INSERT INTO q3_questions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
            ''', (
                int(row['question_no']),
                int(row['sub_question']),
                row['theme'],
                row['tree_dependency'],
                row['question'],
                row['option_a'],
                row['option_b'],
                row['option_c'],
                row['option_d'],
                row['mcq_answer'],
                row['function'],
                row['code'],
                row['tree_image_path']
            ))
    conn.commit()
    conn.close()

def load_q4_questions(csv_file_path='Q4_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not validate_theme(row['theme']):
                continue
                
            cursor.execute('''
                INSERT INTO q4_questions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                int(row['question_no']),
                int(row['sub_question']),
                row['theme'],
                row['question'],
                row['option_1'],
                row['option_2'],
                row['option_3'],
                row['option_4'],
                row['mcq_answer'],
                row['code']
            ))
    conn.commit()
    conn.close()

def load_q5_questions(csv_file_path='Q5_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute('''
                INSERT INTO q5_questions VALUES (?, ?, ?, ?)
            ''', (
                int(row['question_no']),
                int(row['sub_question']),
                row['question'],
                row['url']
            ))
    conn.commit()
    conn.close()

def clear_tables():
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    tables = ['q1_questions', 'q2_questions', 'q3_questions', 
              'q4_questions', 'q5_questions']
    
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Clear existing tables
    clear_tables()
    
    # Initialize database
    init_db()
    
    # Load all question types
    try:
        load_q1_questions('Q1_questions.csv')
        print("Q1 questions loaded successfully")
        load_q2_questions('Q2_questions.csv')
        print("Q2 questions loaded successfully")
        load_q3_questions('Q3_questions.csv')
        print("Q3 questions loaded successfully")
        load_q4_questions('Q4_questions.csv')
        print("Q4 questions loaded successfully")
        load_q5_questions('Q5_questions.csv')
        print("Q5 questions loaded successfully")
    except Exception as e:
        print(f"Error loading questions: {e}")
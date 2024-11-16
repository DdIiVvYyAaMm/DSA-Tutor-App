import sqlite3
import csv
import json

def load_questions_from_csv(csv_file_path='Q3_questions.csv'):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')  # Assuming comma-separated values
        for row in reader:
            cursor.execute('''
                INSERT INTO questions (
                    question_no, sub_question, theme, tree_dependency, question, 
                    option_a, option_b, option_c, option_d, mcq_answer, 
                    function, code, tree_image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def init_db():
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            questions_attempted INTEGER DEFAULT 0,
            questions_correct INTEGER DEFAULT 0,
            correct_ids TEXT,
            incorrect_ids TEXT
        )
    ''')
    
    # Create questions table with additional fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            tree_image_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    load_questions_from_csv('Q3_questions.csv')  # Replace with your CSV path
    print("Database initialized and questions loaded successfully.")
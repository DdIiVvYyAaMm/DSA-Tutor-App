import sqlite3
import csv
import json

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('questions.db')
cursor = conn.cursor()

# Create the questions table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL,  -- 'mcq' or 'text'
    options TEXT                  -- JSON-encoded list of options for MCQs
)
''')

# Read the questions from the CSV file
with open('questions.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        question_text = row['question_text']
        question_type = row['question_type']
        options = row['options'] if row['options'] else None
        
        # If options are provided for MCQ, ensure they're JSON-encoded
        if question_type == 'mcq' and options:
            try:
                options = json.dumps(json.loads(options))  # Parse and re-encode to ensure valid JSON
            except json.JSONDecodeError:
                print(f"Error decoding options for question: {question_text}")
                options = None

        # Insert the question into the database
        cursor.execute('''
        INSERT INTO questions (question_text, question_type, options) VALUES (?, ?, ?)
        ''', (question_text, question_type, options))

# Commit changes and close the database connection
conn.commit()
conn.close()

print("Questions have been imported successfully from CSV.")
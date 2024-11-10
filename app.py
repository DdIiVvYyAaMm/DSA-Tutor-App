from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_question', methods=['POST'])
def get_question():
    question_id = request.json.get('question_id', 1)  # Default to question 1
    question = get_question_by_id(question_id)
    if question:
        return jsonify(question)
    else:
        return jsonify({"error": "Question not found"}), 404

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



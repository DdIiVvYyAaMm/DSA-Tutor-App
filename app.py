from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# Set up your OpenAI API key
# openai.api_key = 'sk-ZOKZQKJHyFtg0FoSTwulp8jtOOD7zaTCm9kyWm6sR_T3BlbkFJ3X0ZsZOPWFodjdaguOGbXqLLa-aZs2EzEmPfUQ-Z4A'

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
)


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





# openai.api_key = 'sk-ZOKZQKJHyFtg0FoSTwulp8jtOOD7zaTCm9kyWm6sR_T3BlbkFJ3X0ZsZOPWFodjdaguOGbXqLLa-aZs2EzEmPfUQ-Z4A'

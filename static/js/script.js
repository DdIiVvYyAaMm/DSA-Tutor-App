let currentQuestionId = 1;

document.getElementById('submit').addEventListener('click', submitAnswer);
document.getElementById('next').addEventListener('click', nextQuestion);

let isResizing = false;
const divider = document.getElementById('divider');
const leftPanel = document.getElementById('left-panel');
const rightPanel = document.getElementById('right-panel');

// Mouse down event to start resizing
divider.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

// Mouse move event to resize the panels
document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;

    // Get the mouse position relative to the container
    const newWidth = e.clientX;
    const containerWidth = document.querySelector('.container').offsetWidth;

    // Allow the left panel to be minimized to 5px while ensuring the right panel has at least 200px
    if (newWidth >= 5 && newWidth <= containerWidth - 200) {
        leftPanel.style.width = `${newWidth}px`;
        rightPanel.style.width = `${containerWidth - newWidth - 5}px`; // Adjust right panel width dynamically
    }
});

// Mouse up event to stop resizing
document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});

function loadQuestion(questionId) {
    fetch('/get_question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question_id: questionId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('question-area').textContent = data.error;
        } else {
            document.getElementById('question-area').textContent = data.question_text;
            if (data.question_type === 'mcq' && data.options) {
                displayOptions(data.options);
            } else {
                clearOptions();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function displayOptions(options) {
    const answerArea = document.getElementById('answer-area');
    answerArea.innerHTML = '';
    options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'button option';
        button.textContent = option;
        button.addEventListener('click', () => selectOption(option));
        answerArea.appendChild(button);
    });
    addResponseAreaAndButtons(answerArea);
}

function clearOptions() {
    // document.getElementById('answer-area').innerHTML = '<textarea id="response" placeholder="Type your response here..."></textarea>';
    const answerArea = document.getElementById('answer-area');
    answerArea.innerHTML = '';  // Clear only options, not buttons

    // Add response area and buttons
    addResponseAreaAndButtons(answerArea);
}

function addResponseAreaAndButtons(answerArea) {
    // Text area for user response (if required)
    const responseTextArea = document.createElement('textarea');
    responseTextArea.id = 'response';
    responseTextArea.placeholder = "Type your response here...";
    answerArea.appendChild(responseTextArea);

    // Submit button
    const submitButton = document.createElement('button');
    submitButton.id = 'submit';
    submitButton.className = 'button';
    submitButton.textContent = 'Submit';
    submitButton.addEventListener('click', submitAnswer);
    answerArea.appendChild(submitButton);

    // Next button
    const nextButton = document.createElement('button');
    nextButton.id = 'next';
    nextButton.className = 'button';
    nextButton.textContent = 'Next Question';
    nextButton.addEventListener('click', nextQuestion);
    answerArea.appendChild(nextButton);
}

function selectOption(option) {
    document.getElementById('response').value = option;
}

function submitAnswer() {
    const question = document.getElementById('question-area').textContent;
    const userResponse = document.getElementById('response').value;

    if (!userResponse.trim()) {
        alert('Please enter your response!');
        return;
    }

    fetch('/evaluate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question, user_response: userResponse }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // Make sure this matches the server response type
    })
    .then(data => {
        if (data.error) {
            document.getElementById('feedback').textContent = `Error: ${data.error}`;
        } else {
            document.getElementById('feedback').textContent = data.feedback;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('feedback').textContent = 'An error occurred. Please try again.';
    });
}

function nextQuestion() {
    currentQuestionId += 1;
    loadQuestion(currentQuestionId);
}

// Load the first question on page load
loadQuestion(currentQuestionId);

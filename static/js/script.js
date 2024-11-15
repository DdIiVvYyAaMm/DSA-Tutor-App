// Constants
const MINIMUM_LEFT_PANEL_WIDTH = 5;
const MINIMUM_RIGHT_PANEL_WIDTH = 200;

// State
let currentQuestionId = 1;
let isResizing = false;

// DOM Elements
const elements = {
    divider: document.getElementById('divider'),
    leftPanel: document.getElementById('left-panel'),
    rightPanel: document.getElementById('right-panel'),
    questionArea: document.getElementById('question-area'),
    answerArea: document.getElementById('answer-area'),
    feedback: document.getElementById('feedback')
};

// Panel Resizing Logic
function initializeResizing() {
    elements.divider.addEventListener('mousedown', startResizing);
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResizing);
}

function startResizing(e) {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
}

function handleResize(e) {
    if (!isResizing) return;

    const containerWidth = document.querySelector('.container').offsetWidth;
    const newWidth = e.clientX;

    if (newWidth >= MINIMUM_LEFT_PANEL_WIDTH && newWidth <= containerWidth - MINIMUM_RIGHT_PANEL_WIDTH) {
        elements.leftPanel.style.width = `${newWidth}px`;
        elements.rightPanel.style.width = `${containerWidth - newWidth - 5}px`;
    }
}

function stopResizing() {
    isResizing = false;
    document.body.style.cursor = 'default';
}

// UI Components
function createButton(text, clickHandler, className = 'button') {
    const button = document.createElement('button');
    button.textContent = text;
    button.className = className;
    button.addEventListener('click', clickHandler);
    return button;
}

function createResponseArea() {
    const textarea = document.createElement('textarea');
    textarea.id = 'response';
    textarea.placeholder = "Type your response here...";
    return textarea;
}

function createIframeContainer(url) {
    const container = document.createElement('div');
    container.className = 'iframe-container';
    
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.className = 'parsons-iframe';
    
    container.appendChild(iframe);
    return container;
}

// Question Management
async function loadQuestion(questionId) {
    try {
        const response = await fetch('/get_question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_id: questionId })
        });
        
        const data = await response.json();
        if (data.error) {
            elements.questionArea.textContent = data.error;
            return;
        }

        elements.questionArea.textContent = data.question_text;
        
        if (data.is_embed && data.url) {
            handleEmbedQuestion(data.url);
        } else {
            handleRegularQuestion(data);
        }
    } catch (error) {
        console.error('Error:', error);
        elements.questionArea.textContent = 'Error loading question';
    }
}

function handleEmbedQuestion(url) {
    elements.rightPanel.classList.add('q5-mode');
    elements.answerArea.innerHTML = '';
    
    const iframeContainer = createIframeContainer(url);
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'button-container';
    buttonContainer.style.padding = '10px';
    buttonContainer.style.textAlign = 'center';
    
    buttonContainer.appendChild(createButton('Next Question', nextQuestion));
    
    elements.answerArea.appendChild(iframeContainer);
    elements.answerArea.appendChild(buttonContainer);
}

<<<<<<< Updated upstream
function clearOptions() {
    // document.getElementById('answer-area').innerHTML = '<textarea id="response" placeholder="Type your response here..."></textarea>';
    const answerArea = document.getElementById('answer-area');
    answerArea.innerHTML = '';  // Clear only options, not buttons

    // Add response area and buttons
    addResponseAreaAndButtons(answerArea);
=======
function handleRegularQuestion(data) {
    elements.rightPanel.classList.remove('q5-mode');
    elements.answerArea.innerHTML = '';
    
    if (data.question_type === 'mcq' && data.options) {
        data.options.forEach(option => {
            const optionButton = createButton(option, () => selectOption(option), 'button option');
            elements.answerArea.appendChild(optionButton);
        });
    }
    
    elements.answerArea.appendChild(createResponseArea());
    elements.answerArea.appendChild(createButton('Submit', submitAnswer));
    elements.answerArea.appendChild(createButton('Next Question', nextQuestion));
>>>>>>> Stashed changes
}

// Answer Handling
async function submitAnswer() {
    const userResponse = document.getElementById('response').value;
    
    if (!userResponse.trim()) {
        alert('Please enter your response!');
        return;
    }

    try {
        const response = await fetch('/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: elements.questionArea.textContent,
                user_response: userResponse
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        elements.feedback.textContent = data.error ? `Error: ${data.error}` : data.feedback;
        
        if (!data.error) {
            updateProgress();
        }
    } catch (error) {
        console.error('Error:', error);
        elements.feedback.textContent = 'An error occurred. Please try again.';
    }
}

function selectOption(option) {
    document.getElementById('response').value = option;
}

function nextQuestion() {
    currentQuestionId += 1;
    loadQuestion(currentQuestionId);
}

<<<<<<< Updated upstream
// Load the first question on page load
loadQuestion(currentQuestionId);
=======
// Progress Tracking
async function updateProgress() {
    try {
        const response = await fetch('/user_progress');
        const data = await response.json();
        
        // Calculate percentages
        const totalQuestions = data.total_questions || 10; // Fallback to 10 if not provided
        const attemptedPercentage = (data.questions_attempted / totalQuestions) * 100;
        const correctPercentage = data.questions_attempted ? 
            (data.questions_correct / data.questions_attempted) * 100 : 0;
        
        // Update progress bars
        const attemptedBar = document.getElementById('attempted-bar');
        const correctBar = document.getElementById('correct-bar');
        
        attemptedBar.style.width = `${attemptedPercentage}%`;
        correctBar.style.width = `${correctPercentage}%`;
        
    } catch (error) {
        console.error('Error updating progress:', error);
    }
}

// Initialize
initializeResizing();
loadQuestion(currentQuestionId);
>>>>>>> Stashed changes

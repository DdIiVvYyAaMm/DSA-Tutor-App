// Global variables
let currentTreeDependency = '';
let currentQuestionType = '';
let currentQuestionNo = '';
let currentSubQuestion = '';
let currentTheme = 'B';
let currentCode = '';

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Initial load
    loadQuestion(false);
    updateProgressBar();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up resizing functionality
    setupResizing();
});

function setupEventListeners() {
    // Theme selection
    const themeSelect = document.getElementById('theme-select');
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            updateTheme(this.value);
        });
    }

    // Submit button
    const submitButton = document.getElementById('submit');
    if (submitButton) {
        submitButton.addEventListener('click', submitAnswer);
    }

    // Next button
    const nextButton = document.getElementById('next');
    if (nextButton) {
        nextButton.addEventListener('click', nextQuestion);
    }
}

function setupResizing() {
    let isResizing = false;
    const divider = document.getElementById('divider');
    const leftPanel = document.getElementById('left-panel');
    const rightPanel = document.getElementById('right-panel');
    
    if (!divider || !leftPanel || !rightPanel) return;

    divider.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const containerWidth = document.querySelector('.container').offsetWidth;
        const newWidth = e.clientX;

        if (newWidth >= 200 && newWidth <= containerWidth - 400) {
            leftPanel.style.width = `${newWidth}px`;
            rightPanel.style.width = `${containerWidth - newWidth - 5}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.style.cursor = 'default';
    });
}

function loadQuestion(isNext) {
    clearAnswers();
    const themeSelect = document.getElementById('theme-select');
    currentTheme = themeSelect ? themeSelect.value : 'B';

    console.log(`Loading question with theme ${currentTheme}`);

    fetch('/get_question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            is_next: isNext,
            theme: currentTheme
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            handleError(data.error);
            return;
        }
        
        currentQuestionType = data.type;
        currentQuestionNo = data.question_no;
        currentSubQuestion = data.sub_question;
        currentTreeDependency = data.tree_dependency || '';
        currentCode = data.code || '';
        
        displayQuestion(data);
        updateContext(data.type); // Add this line to update context
        clearFeedback();
        updateProgressBar(currentQuestionNo);
    })
    .catch(error => {
        console.error('Error loading question:', error);
        handleError('Failed to load question. Please try again.');
    });
}

function updateContext(questionType) {
    const contextContent = document.getElementById('context-content');
    const loadingDiv = document.getElementById('context-loading');
    
    if (!contextContent || !loadingDiv) return;

    // Show loading state
    loadingDiv.style.display = 'block';
    contextContent.style.display = 'none';

    fetch(`/get_context/${questionType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update content
            contextContent.innerHTML = data.content;
            
            // Hide loading, show content with animation
            loadingDiv.style.display = 'none';
            contextContent.style.display = 'block';
            contextContent.style.opacity = '0';
            setTimeout(() => {
                contextContent.style.opacity = '1';
            }, 10);
            
            // Initialize syntax highlighting if code blocks exist
            if (window.Prism) {
                contextContent.querySelectorAll('pre code').forEach((block) => {
                    Prism.highlightElement(block);
                });
            }
        })
        .catch(error => {
            console.error('Error loading context:', error);
            loadingDiv.style.display = 'none';
            contextContent.style.display = 'block';
            contextContent.innerHTML = `
                <div class="error-message">
                    Failed to load context content. Please try refreshing the page.
                </div>
            `;
        });
}

function displayQuestion(questionData) {
    // Display question text with proper handling for each type
    const questionArea = document.querySelector('.question-container');
    if (questionArea) {
        let questionText = '';
        
        if (questionData.type === 'fill_in_blanks') {
            questionText = '<h3>For the given tree, answer the below questions:</h3>';
            questionText += `<p>${questionData.sub_question}</p>`;
        } else if (questionData.type === 'mcq_code') {
            questionText = `<h3>${questionData.question_text}</h3>`;
        } else {
            questionText = `<h3>${questionData.question_text || questionData.sub_question}</h3>`;
        }
        
        questionArea.innerHTML = questionText;
    }

    // Display tree image if available
    if (questionData.tree_image_path) {
        const imageContainer = document.getElementById('image-container');
        if (imageContainer) {
            imageContainer.innerHTML = `
                <img src="/static/${questionData.tree_image_path}" 
                     alt="Binary Tree Diagram" 
                     class="tree-image">
            `;
        }
    }

    // Set up answer interface based on question type
    setupAnswerInterface(questionData);
}

function setupAnswerInterface(questionData) {
    const answerArea = document.getElementById('answer-area');
    if (!answerArea) return;

    // Clear previous content
    answerArea.innerHTML = '';

    if (questionData.type === 'mcq_code') {
        setupCodeMCQInterface(questionData, answerArea);
    } else if (questionData.type === 'mcq_traversal') {
        setupMCQInterface(questionData, answerArea);
    } else if (questionData.type === 'fill_in_blanks') {
        setupFillInBlanksInterface(answerArea, questionData);  // Note: now passing questionData
    }
}

function setupCodeMCQInterface(questionData, container) {
    // Add code display first
    const codeDiv = document.createElement('div');
    codeDiv.className = 'code-display';
    codeDiv.innerHTML = `
        <pre><code class="language-python">${questionData.code}</code></pre>
    `;
    container.appendChild(codeDiv);
    
    // Initialize syntax highlighting
    if (window.Prism) {
        Prism.highlightElement(container.querySelector('code'));
    }

    // Add MCQ options
    const mcqDiv = document.createElement('div');
    mcqDiv.className = 'mcq-container';
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'options-container';
    
    Object.entries(questionData.options).forEach(([key, text]) => {
        const button = document.createElement('button');
        button.className = 'mcq-option';
        button.textContent = `${key}. ${text}`;
        button.addEventListener('click', () => selectMCQOption(button));
        optionsContainer.appendChild(button);
    });

    mcqDiv.appendChild(optionsContainer);
    container.appendChild(mcqDiv);

    // Add comprehension section
    const comprehensionDiv = document.createElement('div');
    comprehensionDiv.className = 'comprehension-container';
    
    comprehensionDiv.innerHTML = `
        <div class="comprehension-title">
            Explain your understanding of this code and how it works:
        </div>
        <textarea 
            class="comprehension-textarea" 
            id="code-comprehension"
            placeholder="Write your explanation here..."
            maxlength="500"
        ></textarea>
        <div class="char-count">
            <span id="char-count">0</span>/500 characters
        </div>
    `;
    
    container.appendChild(comprehensionDiv);

    // Add character count listener
    const textarea = comprehensionDiv.querySelector('textarea');
    const charCount = comprehensionDiv.querySelector('#char-count');
    
    textarea.addEventListener('input', () => {
        const count = textarea.value.length;
        charCount.textContent = count;
    });
}

function setupFillInBlanksInterface(container, questionData) {
    // Create the main container
    const fillBlanksContainer = document.createElement('div');
    fillBlanksContainer.className = 'fill-blanks-container';

    // Define the questions and their corresponding input IDs
    const questions = [
        { text: questionData.root_question, id: 'root-answer' },
        { text: questionData.leaf_question, id: 'leaf-answer' },
        { text: questionData.depth_question, id: 'depth-answer' },
        { text: questionData.child_question, id: 'child-answer' },
        { text: questionData.parent_question, id: 'parent-answer' }
    ];

    // Create input groups for each question
    questions.forEach(question => {
        const inputGroup = document.createElement('div');
        inputGroup.className = 'input-group';
        
        // Create and add the question text
        const questionLabel = document.createElement('label');
        questionLabel.htmlFor = question.id;
        questionLabel.textContent = question.text;
        questionLabel.className = 'question-label';
        
        // Create and add the input field
        const input = document.createElement('input');
        input.type = 'text';
        input.id = question.id;
        input.className = 'answer-input';
        
        // Add elements to the input group
        inputGroup.appendChild(questionLabel);
        inputGroup.appendChild(input);
        fillBlanksContainer.appendChild(inputGroup);
    });

    // Clear and append to container
    container.innerHTML = '';
    container.appendChild(fillBlanksContainer);
}

function setupMCQInterface(questionData, container) {
    const mcqTemplate = document.getElementById('mcq-template');
    const clone = mcqTemplate.content.cloneNode(true);
    const optionsContainer = clone.querySelector('.options-container');
    
    setupMCQOptions(questionData, optionsContainer);
    container.appendChild(clone);
}

function setupMCQOptions(questionData, container) {
    const options = Object.entries(questionData.options).map(([key, text]) => ({ key, text }));

    options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'mcq-option';
        button.textContent = `${option.key}. ${option.text}`;
        button.addEventListener('click', () => selectMCQOption(button));
        container.appendChild(button);
    });
}

function selectMCQOption(selectedButton) {
    const container = selectedButton.closest('.options-container');
    if (container) {
        container.querySelectorAll('.mcq-option').forEach(button => {
            button.classList.remove('selected');
        });
        selectedButton.classList.add('selected');
    }
}

function collectAnswer() {
    if (currentQuestionType === 'fill_in_blanks') {
        const answers = {};
        ['root', 'leaf', 'depth', 'child', 'parent'].forEach(type => {
            const input = document.getElementById(`${type}-answer`);
            answers[type] = input ? input.value.trim() : '';
        });
        return answers;
    } else if (currentQuestionType === 'mcq_code') {
        const selectedOption = document.querySelector('.mcq-option.selected');
        const comprehensionText = document.getElementById('code-comprehension')?.value.trim() || '';
        
        if (!selectedOption || !comprehensionText) {
            return null; // Will trigger validation error
        }

        return {
            mcq: selectedOption.textContent[0], // First character (A, B, C, or D)
            comprehension: comprehensionText
        };
    } else {
        const selectedOption = document.querySelector('.mcq-option.selected');
        return selectedOption ? selectedOption.textContent[0] : null;
    }
}

function submitAnswer() {
    const userResponse = collectAnswer();
    
    // Enhanced validation for code questions
    if (!userResponse) {
        if (currentQuestionType === 'mcq_code') {
            alert('Please select an MCQ option and provide your explanation before submitting.');
        } else {
            alert('Please provide an answer before submitting.');
        }
        return;
    }

    // Get question text for feedback
    const questionContainer = document.querySelector('.question-container');
    const questionText = questionContainer ? questionContainer.textContent : '';

    // Submit answer
    fetch('/evaluate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: currentQuestionType,
            question_no: currentQuestionNo,
            sub_question: currentSubQuestion,
            theme: currentTheme,
            user_response: userResponse,
            question_text: questionText,
            code: currentCode,
            tree_dependency: currentTreeDependency
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        displayFeedback(data.feedback);
        updateQueueStatus(data.queue_status);
        updateProgressBar(currentQuestionNo);
    })
    .catch(error => {
        console.error('Evaluation error:', error);
        handleError('Failed to evaluate answer. Please try again.');
    });
}

// Add a clearAnswers function to be used when loading new questions
function clearAnswers() {
    // Existing clear logic
    document.querySelectorAll('.mcq-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    const comprehensionTextarea = document.getElementById('code-comprehension');
    if (comprehensionTextarea) {
        comprehensionTextarea.value = '';
        const charCount = document.getElementById('char-count');
        if (charCount) {
            charCount.textContent = '0';
        }
    }
}

function updateTheme(theme) {
    currentTheme = theme;
    fetch('/update_theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ theme }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadQuestion(false);
        } else {
            handleError(data.error);
        }
    })
    .catch(error => {
        console.error('Error updating theme:', error);
        handleError('Failed to update theme. Please try again.');
    });
}

function updateQueueStatus(queueStatus) {
    if (!queueStatus) return;
    
    sessionStorage.setItem('progress', JSON.stringify(queueStatus.progress));
    updateProgressBar();
}

function updateProgressBar(currentQuestionNo) {
    const progressData = JSON.parse(sessionStorage.getItem('progress'));
    if (!progressData) return;

    const correctCount = document.getElementById('correct-count');
    const progressFill = document.getElementById('progress-fill');
    
    if (correctCount && progressFill) {
        const currentCorrect = progressData[`q${currentQuestionNo}`] || 0;
        correctCount.textContent = `${currentCorrect}/5`;
        const progress = (currentCorrect / 5) * 100;
        progressFill.style.width = `${progress}%`;
    }
}

function displayFeedback(feedback) {
    const feedbackText = document.getElementById('feedback-text');
    if (feedbackText) {
        feedbackText.textContent = feedback;
        feedbackText.scrollIntoView({ behavior: 'smooth' });
    }
}

function clearFeedback() {
    const feedbackText = document.getElementById('feedback-text');
    if (feedbackText) {
        feedbackText.textContent = '';
    }
}

function nextQuestion() {
    clearFeedback();
    loadQuestion(true);
}

function handleError(message) {
    const questionArea = document.querySelector('.question-container');
    const contextContent = document.getElementById('context-content');
    
    if (questionArea) {
        questionArea.innerHTML = `<p class="error-message">${message}</p>`;
    }
    
    if (contextContent) {
        contextContent.innerHTML = `<p class="error-message">Unable to load content. Please refresh the page.</p>`;
    }
    
    console.error(message);
}

// Export for testing if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadQuestion,
        submitAnswer,
        nextQuestion,
        updateProgressBar
    };
}
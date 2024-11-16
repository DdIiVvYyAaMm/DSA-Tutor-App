// script.js

let currentQuestionId = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Initial load of the first question
    loadQuestion(currentQuestionId);

    // Resizing logic
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

    // Event listener for theme selection change
    const themeSelect = document.getElementById('theme-select');
    themeSelect.addEventListener('change', function() {
        const selectedTheme = this.value;
        const currentThemeElement = document.getElementById('current-theme');
        if (currentThemeElement) {
            currentThemeElement.innerText = getThemeName(selectedTheme);
        } else {
            console.error("Element 'current-theme' not found in DOM.");
        }
        // Optionally, fetch a new question based on the selected theme
        // Uncomment the next line if you want to automatically fetch the question when theme changes
        // loadQuestion(currentQuestionId);
    });

    // Event listeners for Submit and Next buttons
    const submitButton = document.getElementById('submit');
    if (submitButton) {
        submitButton.addEventListener('click', submitAnswer);
    } else {
        console.error("Element 'submit' button not found in DOM.");
    }

    const nextButton = document.getElementById('next');
    if (nextButton) {
        nextButton.addEventListener('click', nextQuestion);
    } else {
        console.error("Element 'next' button not found in DOM.");
    }
});

// Function to get theme name from code
function getThemeName(themeCode) {
    const themes = {
        'B': 'Base (B)',
        'H': 'Harry Potter (H)',
        'R': 'Recipe (R)',
        'M': 'Music (M)',
        '': 'Base (B)'  // Default theme
    };
    return themes[themeCode] || 'Base (B)';
}

function loadQuestion(questionId) {
    // Get the selected theme from the dropdown
    const themeSelect = document.getElementById('theme-select');
    const selectedTheme = themeSelect.value; // e.g., 'B', 'H', 'R', 'M'

    console.log(`Loading question ID: ${questionId}, Theme: '${selectedTheme}'`);

    fetch('/get_question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question_id: questionId, theme: selectedTheme }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Fetched Question Data:', data); // Log the fetched data

        if (data.error) {
            // If there's an error, display it in 'question-area'
            const questionArea = document.getElementById('question-area');
            if (questionArea) {
                questionArea.textContent = data.error;
            } else {
                console.error("Element 'question-area' not found in DOM.");
            }
            clearOptions();
            const feedbackText = document.getElementById('feedback-text');
            if (feedbackText) {
                feedbackText.textContent = '';
            } else {
                console.error("Element 'feedback-text' not found in DOM.");
            }
            // Optionally, clear the image
            const treeImage = document.getElementById('tree-image');
            if (treeImage) {
                treeImage.src = '';
                treeImage.alt = '';
            }
            // Clear the code snippet
            const codeSnippet = document.getElementById('code-snippet');
            if (codeSnippet) {
                codeSnippet.textContent = '';
                hljs.highlightElement(codeSnippet); // Re-highlight if using Highlight.js
            }
             // Clear the image container
             const imageContainer = document.getElementById('image-container');
            if (imageContainer) {
                imageContainer.innerHTML = '';
            }
        } else {
            // Update the question text
            const questionTextElement = document.getElementById('question-text');
            if (questionTextElement) {
                questionTextElement.textContent = data.question_text;
            } else {
                console.error("Element 'question-text' not found in DOM.");
            }

            // Update current theme display
            const currentThemeElement = document.getElementById('current-theme');
            if (currentThemeElement) {
                currentThemeElement.innerText = getThemeName(data.theme);
            } else {
                console.error("Element 'current-theme' not found in DOM.");
            }

            // Update the theme dropdown to the current theme
            const themeSelect = document.getElementById('theme-select');
            if (themeSelect) {
                themeSelect.value = data.theme || '';
            } else {
                console.error("Element 'theme-select' not found in DOM.");
            }

            // Update the image if 'tree_image_path' is present
            if (data.tree_image_path) {
                const imageContainer = document.getElementById('image-container');
                if (imageContainer) {
                    imageContainer.innerHTML = ''; // Clear previous image
                    const treeImage = document.createElement('img');
                    treeImage.id = 'tree-image';
                    // Ensure the image path is correct. If images are in the 'static' folder, prefix with '/static/'
                    treeImage.src = `/static/${data.tree_image_path}`;
                    treeImage.alt = `Question ${data.id} Image`;
                    imageContainer.appendChild(treeImage);
                } else {
                    console.error("Element 'image-container' not found in DOM.");
                }
            } else {
                // Remove the image if not present
                const imageContainer = document.getElementById('image-container');
                if (imageContainer) {
                    imageContainer.innerHTML = '';
                }
            }

            // Store tree_dependency
            currentTreeDependency = data.tree_dependency || '';
            console.log("Current Tree Dependency:", currentTreeDependency);

            if (data.code) {
                const codeSnippet = document.getElementById('code-snippet');
                if (codeSnippet) {
                    codeSnippet.textContent = data.code;
                    hljs.highlightElement(codeSnippet); // Re-highlight if using Highlight.js
                } else {
                    console.error("Element 'code-snippet' not found in DOM.");
                }
            } else {
                // Clear the code snippet if not present
                const codeSnippet = document.getElementById('code-snippet');
                if (codeSnippet) {
                    codeSnippet.textContent = '';
                    hljs.highlightElement(codeSnippet); // Re-highlight if using Highlight.js
                }
            }
            
            

            // Determine if it's a multiple-choice question by checking the presence of 'option_a', etc.
            if (data.option_a && data.option_b && data.option_c && data.option_d && data.mcq_answer) {
                displayOptions(data);
            } else {
                clearOptions();
            }

            // Clear feedback
            const feedbackTextElement = document.getElementById('feedback-text');
            if (feedbackTextElement) {
                feedbackTextElement.textContent = '';
            } else {
                console.error("Element 'feedback-text' not found in DOM.");
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const questionArea = document.getElementById('question-area');
        if (questionArea) {
            questionArea.textContent = 'An error occurred while loading the question.';
        } else {
            console.error("Element 'question-area' not found in DOM.");
        }
    });
}

function displayOptions(questionData) {
    const answerArea = document.getElementById('answer-area');
    if (!answerArea) {
        console.error("Element 'answer-area' not found in DOM.");
        return;
    }
    answerArea.innerHTML = ''; // Clear previous content

    // Display options as buttons
    const options = [
        { key: 'A', text: questionData.option_a },
        { key: 'B', text: questionData.option_b },
        { key: 'C', text: questionData.option_c },
        { key: 'D', text: questionData.option_d }
    ];

    options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'button option';
        button.textContent = option.text;
        button.dataset.optionKey = option.key; // Store the option key (A, B, C, D)
        button.addEventListener('click', () => selectOption(option.text));
        answerArea.appendChild(button);
    });

    const responseTextArea = document.createElement('textarea');
    responseTextArea.id = 'response';
    responseTextArea.placeholder = "Type your response here...";
    answerArea.appendChild(responseTextArea);

    // Add Submit and Next buttons
    const submitButton = document.createElement('button');
    submitButton.id = 'submit';
    submitButton.className = 'button';
    submitButton.textContent = 'Submit';
    submitButton.addEventListener('click', submitAnswer);
    answerArea.appendChild(submitButton);

    const nextButton = document.createElement('button');
    nextButton.id = 'next';
    nextButton.className = 'button';
    nextButton.textContent = 'Next Question';
    nextButton.addEventListener('click', nextQuestion);
    answerArea.appendChild(nextButton);
}

function selectOption(optionText) {
    // Store the selected option's text in the response textarea
    const responseElement = document.getElementById('response');
    if (responseElement) {
        responseElement.value = optionText;
    } else {
        console.error("Element 'response' not found in DOM.");
    }
}

function clearOptions() {
    const answerArea = document.getElementById('answer-area');
    if (!answerArea) {
        console.error("Element 'answer-area' not found in DOM.");
        return;
    }
    // Clear the textarea
    const responseTextArea = document.getElementById('response');
    if (responseTextArea) {
        responseTextArea.value = '';
    } else {
        console.error("Element 'response' not found in DOM.");
    }
}

function submitAnswer() {
    const questionElement = document.getElementById('question-text');
    const responseElement = document.getElementById('response');
    const questionId = currentQuestionId;

    if (!questionElement) {
        console.error("Element 'question-text' not found in DOM.");
        alert('An error occurred. Please refresh the page.');
        return;
    }
    if (!responseElement) {
        console.error("Element 'response' not found in DOM.");
        alert('An error occurred. Please refresh the page.');
        return;
    }

    const question = questionElement.textContent;
    const userResponse = responseElement.value;

    if (!userResponse.trim()) {
        alert('Please enter your response!');
        return;
    }
    
    // Capture the code snippet if present
    const codeSnippet = document.getElementById('code-snippet');
    const code = codeSnippet ? codeSnippet.textContent : '';

    // Prepare the data to send, including the code
    const submissionData = {
        question: question,
        code: code, // Include code snippet
        user_response: userResponse,
        question_id: questionId,
        tree_dependency: currentTreeDependency
    };

    fetch('/evaluate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question, user_response: userResponse, question_id: questionId, code: code, tree_dependency: currentTreeDependency }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            const feedbackText = document.getElementById('feedback-text');
            if (feedbackText) {
                feedbackText.textContent = `Error: ${data.error}`;
            } else {
                console.error("Element 'feedback-text' not found in DOM.");
            }
        } else {
            const feedbackText = document.getElementById('feedback-text');
            if (feedbackText) {
                feedbackText.textContent = data.feedback;
            } else {
                console.error("Element 'feedback-text' not found in DOM.");
            }
            updateProgress();

            // If incorrect, set the theme to the new_theme
            if (!data.correct && data.new_theme) {
                const themeSelect = document.getElementById('theme-select');
                const currentThemeElement = document.getElementById('current-theme');
                if (themeSelect && currentThemeElement) {
                    themeSelect.value = data.new_theme;
                    currentThemeElement.innerText = getThemeName(data.new_theme);
                } else {
                    if (!themeSelect) {
                        console.error("Element 'theme-select' not found in DOM.");
                    }
                    if (!currentThemeElement) {
                        console.error("Element 'current-theme' not found in DOM.");
                    }
                }
                // Optionally, automatically fetch the next question
                // nextQuestion();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const questionArea = document.getElementById('question-area');
        if (questionArea) {
            questionArea.textContent = 'An error occurred while loading the question.';
        } else {
            console.error("Element 'question-area' not found in DOM.");
        }
    });
}

function nextQuestion() {
    currentQuestionId += 1;
    loadQuestion(currentQuestionId);
}

function updateProgress() {
    fetch('/user_progress')
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        const attemptedElement = document.getElementById('questions-attempted');
        const correctElement = document.getElementById('questions-correct');
        if (attemptedElement && correctElement) {
            attemptedElement.innerText = data.questions_attempted;
            correctElement.innerText = data.questions_correct;
        } else {
            console.error("Progress elements not found in DOM.");
        }
    })
    .catch(error => {
        console.error('Error updating progress:', error);
        if (error.error) {
            alert(`Error: ${error.error}`);
        } else {
            alert('An unexpected error occurred while updating progress.');
        }
    });
}

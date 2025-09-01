// frontend/media/main.js
(function() {
    const vscode = acquireVsCodeApi();

    const sendButton = document.getElementById('send-button');
    const goalInput = document.getElementById('goal-input');
    const stopButton = document.getElementById('stop-button');
    
    const inputArea = document.getElementById('input-area');
    const stopButtonContainer = document.getElementById('stop-button-container');
    
    // --- NEW: Get a reference to the chat history container ---
    const chatHistory = document.getElementById('chat-history');

    // --- NEW: Function to scroll to the bottom ---
    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function sendMessage() {
        const goal = goalInput.value;
        if (goal) {
            vscode.postMessage({ type: 'sendGoal', value: goal });
            goalInput.value = '';
            // --- NEW: Scroll after sending ---
            // A slight delay gives the extension time to add the user's message to the DOM
            setTimeout(scrollToBottom, 50); 
        }
    }

    sendButton.addEventListener('click', sendMessage);

    goalInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    stopButton.addEventListener('click', () => {
        vscode.postMessage({ type: 'stopAgent' });
    });

    // Listen for messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;
        if (message.command === 'setAgentState') {
            if (message.isBusy) {
                inputArea.classList.add('hidden');
                stopButtonContainer.classList.remove('hidd  en');
            } else {
                inputArea.classList.remove('hidden');
                stopButtonContainer.classList.add('hidden');
            }
        }
        
        // --- NEW: Scroll after receiving a message ---
        // This assumes the extension's message will trigger a re-render
        // that adds a new message to the chat history.
        setTimeout(scrollToBottom, 50);
    });
}());

(function() {
    const vscode = acquireVsCodeApi();
    const chatHistory = document.getElementById('chat-history');
    const goalInput = document.getElementById('goal-input');
    const sendButton = document.getElementById('send-button');
    const stopButton = document.getElementById('stop-button');
    const inputArea = document.getElementById('input-area');
    const stopButtonContainer = document.getElementById('stop-button-container');

    function scrollToBottom() {
        // A more robust scroll method
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function sendMessage() {
        const goal = goalInput.value;
        if (goal.trim()) {
            vscode.postMessage({ type: 'sendGoal', value: goal });
            goalInput.value = '';
        }
    }

    // --- NEW FUNCTION TO ADD A MESSAGE TO THE CHAT ---
    function appendMessage(msg) {
        if (!msg || !msg.content) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}`;
        
        // Sanitize and format content
        const formattedContent = msg.content
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\n/g, '<br>');

        messageDiv.innerHTML = `<p>${formattedContent}</p>`;
        chatHistory.appendChild(messageDiv);
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

    // --- UPDATE THE MESSAGE LISTENER ---
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.command) {
            case 'setAgentState':
                if (message.isBusy) {
                    inputArea.classList.add('hidden');
                    stopButtonContainer.classList.remove('hidden');
                } else {
                    inputArea.classList.remove('hidden');
                    stopButtonContainer.classList.add('hidden');
                }
                break;
            
            case 'addMessage':
                appendMessage(message.message);
                break;
        }

        // Always scroll after a state change or a new message
        setTimeout(scrollToBottom, 50);
    });
}());
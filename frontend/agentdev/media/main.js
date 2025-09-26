(function () {
    const vscode = acquireVsCodeApi();

    // These IDs now perfectly match your HTML from AgentViewStatus.ts
    const chatHistory = document.getElementById('chat-history');
    const goalInput = document.getElementById('goal-input');
    const sendButton = document.getElementById('send-button');
    const inputArea = document.getElementById('input-area');
    const stopButtonContainer = document.getElementById('stop-button-container');
    const stopButton = document.getElementById('stop-button');
    const approvalArea = document.getElementById('approval-area');
    const approveButton = document.getElementById('approve-button');
    const rejectButton = document.getElementById('reject-button');

    // This is a more advanced Markdown renderer for better formatting
    const md = window.markdownit();

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function handleUserInput() {
        const goal = goalInput.value;
        if (goal.trim()) {
            // This now sends a 'startTask' command, which is more descriptive
            vscode.postMessage({
                command: 'startTask',
                goal: goal
            });
            goalInput.value = ''; // Clear the input
        }
    }

    function appendMessage(msg) {
        if (!msg || typeof msg.content !== 'string') return;

        const messageDiv = document.createElement('div');
        const role = msg.role === 'result' ? 'agent' : msg.role;
        messageDiv.className = `message ${role}`;


        // Use the markdown renderer for rich content
        // It automatically handles HTML sanitization for its output
        const renderedContent = md.render(msg.content);
        messageDiv.innerHTML = renderedContent;

        chatHistory.appendChild(messageDiv);
    }

    // --- Event Listeners ---
    sendButton.addEventListener('click', handleUserInput);

    goalInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleUserInput();
        }
    });

    stopButton.addEventListener('click', () => {
        vscode.postMessage({ command: 'stopAgent' });
    });

    approveButton.addEventListener('click', () => {
        approvalArea.classList.add('hidden'); // Hide buttons
        inputArea.classList.remove('hidden'); // Show input
        vscode.postMessage({
            command: 'startTask',
            goal: '[CONTINUE] The plan has been approved. Proceed with execution.'
        });
    });

    rejectButton.addEventListener('click', () => {
        approvalArea.classList.add('hidden'); // Hide buttons
        inputArea.classList.remove('hidden'); // Show input
        vscode.postMessage({
            command: 'startTask',
            goal: '[REJECT] The user has rejected the plan.'
        });
    });

    // Listen for messages from the extension (AgentStatusViewProvider)
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
            case 'showApprovalButtons':
                inputArea.classList.add('hidden'); // Hide the text input
                stopButtonContainer.classList.add('hidden'); // Ensure stop button is hidden
                approvalArea.classList.remove('hidden'); // Show the Approve/Reject buttons
                break;
        }

        setTimeout(scrollToBottom, 100);
    });
}());
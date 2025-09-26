// src/AgentViewStatus.ts

import * as vscode from 'vscode';
import { getNonce } from './getNonce'; // A utility for security

// Define the comprehensive message structure to match all possible backend types
type ChatMessage = {
    role: 'user' | 'agent' | 'thought' | 'tool' | 'error' | 'timer' | 'classification';
    content: string;
};

export class AgentStatusViewProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    // Your stateful history is preserved
    private _chatHistory: ChatMessage[] = [
        { role: 'agent', content: "Hello! I'm AgentDev. Give me a goal to start working on." }
    ];

    constructor(private readonly _extensionUri: vscode.Uri) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this._extensionUri, 'media'),
                // Allow it to load markdown-it from node_modules
                vscode.Uri.joinPath(this._extensionUri, 'node_modules')
            ]
        };

        // This renders the initial state from your _chatHistory
        webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

        // Listen for messages from the webview's JavaScript UI
        webviewView.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                // The name 'startTask' must match the one in your main.js
                case 'startTask':
                    this.addMessage({ role: 'user', content: message.goal });
                    vscode.commands.executeCommand('agentdev.startTask.internal', message.goal);
                    return;
                case 'stopAgent':
                    vscode.commands.executeCommand('agentdev.stopAgent.internal');
                    return;
            }
        });
    }

    /**
     * Adds a message to the internal history and posts it to the webview UI.
     */
    public addMessage(message: ChatMessage) {
        this._chatHistory.push(message);
        if (this._view) {
            this._view.webview.postMessage({ command: 'addMessage', message: message });
        }
    }

    /**
     * Toggles the UI between busy and idle states.
     */
    public setAgentState(isBusy: boolean) {
        if (this._view) {
            this._view.webview.postMessage({ command: 'setAgentState', isBusy: isBusy });
        }
    }

    /**
     * CRITICAL: This is the new method that extension.ts will call
     * to process streaming data from the Python backend.
     */
    public handleMessage(eventData: any) {
        const { type, content } = eventData;
        let role: ChatMessage['role'] = 'thought'; // Default role
        let messageContent = content;

        if (type === 'user_approval_request') {
            this.addMessage({ role: 'agent', content });
            if (this._view) {
                // Tell the webview to show the buttons
                this._view.webview.postMessage({ command: 'showApprovalButtons' });
            }
            return; // Stop further processing
        }

        switch (type) {
            case 'thought': role = 'thought'; break;
            case 'action': case 'result': role = 'tool'; break;
            case 'status':
                role = 'agent';
                messageContent = content.replace('Agent finished with reason: ', '').replace('Agent finished.', '');
                break;
            case 'error': role = 'error'; break;
            case 'timer': role = 'timer'; break;
            case 'classification': role = 'classification'; break;
            default: role = 'thought'; break;
        }

        // Use your existing addMessage function to update state and UI
        this.addMessage({ role, content: messageContent });
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        // Correctly generate webview-safe URIs for all your assets
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'main.js'));
        // Make sure your CSS file is named 'styles.css' as per your original code
        const stylesUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'styles.css'));
        const sendIconUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'send.svg'));
        const stopIconUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'stop.svg'));
        const markdownItUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'node_modules', 'markdown-it', 'dist', 'markdown-it.min.js'));
        const nonce = getNonce();

        // Your initial render logic is preserved
        const chatHistoryHtml = this._chatHistory.map(msg => {
            const roleClass = `message ${msg.role}`;
            // Basic sanitization
            const formattedContent = msg.content.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>');
            return `<div class="${roleClass}"><p>${formattedContent}</p></div>`;
        }).join('');

        // The final HTML structure, with added security policies
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; img-src ${webview.cspSource} https:; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${stylesUri}" rel="stylesheet">
                <title>AgentDev Chat</title>
            </head>
            <body>
                <div id="chat-history">${chatHistoryHtml}</div>
                <div id="approval-area" class="hidden">
                    <button id="approve-button" class="user-button">Approve</button>
                    <button id="reject-button" class="user-button reject">Reject</button>
                </div>
                <div id="stop-button-container" class="hidden">
                    <button id="stop-button"><img src="${stopIconUri}" class="icon" alt="Stop"/> Stop Agent</button>
                </div>
                <div id="input-area">
                    <div id="input-wrapper">
                        <textarea id="goal-input" placeholder="Enter your task..."></textarea>
                        <img src="${sendIconUri}" id="send-button" class="send-icon" alt="Send" title="Send"/>
                    </div>
                </div>
                <script nonce="${nonce}" src="${markdownItUri}"></script>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}
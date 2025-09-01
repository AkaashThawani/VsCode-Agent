import * as vscode from 'vscode';

interface ChatMessage { role: 'user' | 'agent' | 'thought'; content: string; }

export class AgentStatusViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'agentdev.chatView';
    private _view?: vscode.WebviewView;
    private _chatHistory: ChatMessage[] = [];
    constructor(private readonly _extensionUri: vscode.Uri) { }
    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this._extensionUri, 'media')]
        };
        this.render();
        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.type === 'sendGoal') {
                this.addMessage({ role: 'user', content: data.value });
                vscode.commands.executeCommand('agentdev.startTask.internal', data.value);
            }
            if (data.type === 'stopAgent') {
                vscode.commands.executeCommand('agentdev.stopAgent.internal');
            }
        });
    }
    public addMessage(message: ChatMessage) {
        this._chatHistory.push(message);
        if (this._view) {
            // Instead of re-rendering, just send the new message
            this._view.webview.postMessage({ command: 'addMessage', message: message });
        }
    }
    public setAgentState(isBusy: boolean) {
        if (this._view) { this._view.webview.postMessage({ command: 'setAgentState', isBusy: isBusy }); }
    }
    private render() {
        if (this._view) { this._view.webview.html = this.getHtmlForWebview(this._view.webview); }
    }
    private getHtmlForWebview(webview: vscode.Webview): string {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'main.js'));
        const stylesUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'styles.css'));
        const sendIconUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'send.svg'));
        const stopIconUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'stop.svg'));
        const chatHistoryHtml = this._chatHistory.map(msg => {
            const roleClass = `message ${msg.role}`;
            const formattedContent = msg.content.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>');
            return `<div class="${roleClass}"><p>${formattedContent}</p></div>`;
        }).join('');
        return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link href="${stylesUri}" rel="stylesheet"><title>AgentDev Chat</title></head><body><div id="chat-history">${chatHistoryHtml}</div><div id="stop-button-container" class="hidden"><button id="stop-button"><img src="${stopIconUri}" class="icon" alt="Stop"/> Stop Agent</button></div><div id="input-area"><div id="input-wrapper"><textarea id="goal-input" placeholder="Enter your task..."></textarea><img src="${sendIconUri}" id="send-button" class="send-icon" alt="Send" title="Send"/></div></div><script src="${scriptUri}"></script></body></html>`;
    }
}
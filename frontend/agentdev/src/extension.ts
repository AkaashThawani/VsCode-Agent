// src/extension.ts

import * as vscode from 'vscode';
import fetch from 'node-fetch';
import { AgentStatusViewProvider } from './AgentViewStatus';

let isAgentRunning = false;
let isAgentInitialized = false; // Tracks if the agent has been created on the backend

export function activate(context: vscode.ExtensionContext) {
    console.log('AGENTDEV: The "agentdev" extension is now active!');

    const provider = new AgentStatusViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('agentdev.chatView', provider)
    );
    console.log('AGENTDEV: Chat view provider registered.');

    // This command is called by the webview provider when it receives a message from the UI
    const internalStartTask = vscode.commands.registerCommand('agentdev.startTask.internal', async (goal: string) => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || !workspaceFolders.length) {
            provider.addMessage({ role: 'error', content: 'You must have a folder open to run the agent.' });
            return;
        }
        if (isAgentRunning) {
            vscode.window.showWarningMessage("An agent is already running.");
            return;
        }

        const projectPath = workspaceFolders[0].uri.fsPath;
        const configuration = vscode.workspace.getConfiguration('agentdev');
        const modelName = configuration.get<string>('ollamaModelName');

        if (!modelName) {
            provider.addMessage({ role: 'error', content: 'AgentDev: Ollama model name is not set. Please check your VS Code settings.' });
            return;
        }

        isAgentRunning = true;
        provider.setAgentState(true);

        try {
            // Step 1: Create the agent on the backend if it hasn't been done yet in this session.
            if (!isAgentInitialized) {
                provider.addMessage({ role: 'thought', content: `Initializing agent with model ${modelName}...` });
                const createResponse = await fetch('http://127.0.0.1:8000/create-agent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_path: projectPath, model: modelName }),
                });

                if (!createResponse.ok) {
                    const errorBody = await createResponse.text();
                    throw new Error(`Failed to create agent. Status: ${createResponse.status}. Body: ${errorBody}`);
                }
                const createResult:any = await createResponse.json();
                provider.addMessage({ role: 'thought', content: createResult.message || 'Agent created.' }); 
                3
                isAgentInitialized = true;
            }

            // Step 2: Execute the turn with the user's goal.
            const response = await fetch('http://127.0.0.1:8000/execute-turn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal }),
            });

            if (!response.ok) {
                const errorBody = await response.text();
                throw new Error(`Error from backend. Status: ${response.status}. Body: ${errorBody}`);
            }
            if (!response.body) { throw new Error("Response body is null"); }
            
            // Process the streaming response from the backend
            for await (const chunk of response.body as any) {
                if (!isAgentRunning) {
                    provider.addMessage({ role: 'thought', content: 'Agent stopped by user.' });
                    break; 
                }
                const lines = chunk.toString().split('\n\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.substring(6);
                            if (jsonStr) {
                                const eventData = JSON.parse(jsonStr);
                                provider.handleMessage(eventData); // Delegate message handling
                            }
                        } catch (e) {
                            console.error('Failed to parse streaming JSON chunk:', e);
                        }
                    }
                }
            }

        } catch (error: any) {
            provider.addMessage({ role: 'error', content: `Connection Error: ${error.message}. Is the backend server running?` });
        } finally {
            isAgentRunning = false;
            provider.setAgentState(false);
        }
    });

    const stopAgentCommand = vscode.commands.registerCommand('agentdev.stopAgent.internal', () => {
        if (isAgentRunning) {
            isAgentRunning = false;
            provider.addMessage({ role: 'thought', content: 'Stopping agent...' });
        }
    });

    context.subscriptions.push(internalStartTask, stopAgentCommand);
}

export function deactivate() {
    isAgentInitialized = false; // Reset on extension deactivation
}
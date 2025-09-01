// frontend/src/extension.ts
import * as vscode from 'vscode';
import fetch from 'node-fetch';
import { AgentStatusViewProvider } from './AgentViewStatus'; 

// Global flag to control the agent's execution loop and state
let isAgentRunning = false;

export function activate(context: vscode.ExtensionContext) {

    const provider = new AgentStatusViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(AgentStatusViewProvider.viewType, provider)
    );

    // Command to run the agent with a given goal
    const internalStartTask = vscode.commands.registerCommand('agentdev.startTask.internal', async (goal: string) => {
        
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || !workspaceFolders.length) {
            provider.addMessage({ role: 'agent', content: 'Error: You must have a folder open to run a task.' });
            return;
        }

        if (isAgentRunning) {
            vscode.window.showWarningMessage("An agent is already running.");
            return;
        }

        isAgentRunning = true;
        provider.setAgentState(true);

        const projectPath = workspaceFolders[0].uri.fsPath;

        try {
            const response = await fetch('http://127.0.0.1:8000/execute-task', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal, project_path: projectPath }),
            });

            if (!response.body) {
                throw new Error("Response body is null");
            }
            
            for await (const chunk of response.body) {
                if (!isAgentRunning) {
                    provider.addMessage({ role: 'thought', content: 'Agent stopped by user.' });
                    break; 
                }

                const lines = chunk.toString().split('\n\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.substring(6);
                            const eventData = JSON.parse(jsonStr);
                            const { type, content } = eventData;

                            if (type === 'thought' || type === 'status') {
                                provider.addMessage({ role: 'thought', content });
                            } else {
                                provider.addMessage({ role: 'agent', content });
                            }
                        } catch (e) {}
                    }
                }
            }

        } catch (error: any) {
            if (isAgentRunning) { 
                provider.addMessage({ role: 'agent', content: `Error: ${error.message}` });
            }
        } finally {
            isAgentRunning = false;
            provider.setAgentState(false);
        }
    });

    // Command to stop the agent
    const stopAgentCommand = vscode.commands.registerCommand('agentdev.stopAgent.internal', () => {
        if (isAgentRunning) {
            isAgentRunning = false;
        }
    });

    context.subscriptions.push(internalStartTask, stopAgentCommand);
}

export function deactivate() {}
import * as vscode from 'vscode';
import fetch from 'node-fetch';
import { AgentStatusViewProvider } from './AgentViewStatus';

let isAgentRunning = false;

export function activate(context: vscode.ExtensionContext) {
    console.log('AGENTDEV: The "agentdev" extension is now active!'); // <-- ADD THIS

    // Use your new view ID here if you changed it
    const viewId = 'agentdev.chatView';

    console.log(`AGENTDEV: Preparing to register provider for view: ${viewId}`); // <-- ADD THIS

    const provider = new AgentStatusViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(viewId, provider)
    );
    console.log("context", context)
    console.log("provider", provider)

    console.log(`AGENTDEV: Provider for ${viewId} has been registered.`);

    const internalStartTask = vscode.commands.registerCommand('agentdev.startTask.internal', async (goal: string) => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || !workspaceFolders.length) {
            provider.addMessage({ role: 'agent', content: 'Error: You must have a folder open.' });
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
            if (!response.body) { throw new Error("Response body is null"); }
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
                            const eventData = JSON.parse(jsonStr);
                            const { type, content } = eventData;
                            let role: any  = '';
                            let messageContent = content;

                            switch (type) {
                                case 'thought':
                                    role = 'thought';
                                    break;
                                case 'action':
                                case 'result':
                                    role = 'tool'; // A new role for tool activity!
                                    break;

                                case 'status':
                                    role = 'agent'; // The final, user-facing message
                                    messageContent = content.replace('Agent has finished the task. ', '');
                                    break;

                                case 'error':
                                    role = 'error';
                                    break;
                                case 'classification': // NEW CASE
                                    role = 'classification';
                                    break;
                                case 'thought':
                                    role = 'thought';
                                    break;
                                default:
                                    role = 'thought'; // Fallback for any other types
                                    break;
                            }

                            provider.addMessage({ role: role, content: messageContent });

                        } catch (e) { }
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
    const stopAgentCommand = vscode.commands.registerCommand('agentdev.stopAgent.internal', () => {
        if (isAgentRunning) { isAgentRunning = false; }
    });
    context.subscriptions.push(internalStartTask, stopAgentCommand);
}
export function deactivate() { }
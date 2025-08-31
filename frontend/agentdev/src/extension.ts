import * as vscode from 'vscode';
import fetch from 'node-fetch'; // Import the fetch library

export function activate(context: vscode.ExtensionContext) {

    console.log('Congratulations, your extension "agentdev" is now active!');

    let disposable = vscode.commands.registerCommand('agentdev.startTask', async () => {
        console.log("recived a task ")
        // 1. Get the active workspace folder (the user's project)
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('AgentDev: You must have a folder open to run a task.');
            return; // Stop if no folder is open
        }
        const projectPath = workspaceFolders[0].uri.fsPath;

        // 2. Prompt the user for their goal
        const goal = await vscode.window.showInputBox({
            prompt: "What task should the AI agent perform?",
            placeHolder: "e.g., refactor the User service to use a repository pattern",
            title: "AgentDev: New Task"
        });
        console.log("GOAL",goal)
        if (!goal) {
            vscode.window.showWarningMessage('AgentDev task canceled.');
            return; // Stop if the user cancels
        }

        // 3. Send the data to the Python ba    ckend
        vscode.window.showInformationMessage(`Agent task started for: ${goal}`);

        try {
            const response = await fetch('http://127.0.0.1:8000/execute-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    goal: goal,
                    project_path: projectPath
                }),
            });

            if (!response.ok) {
                // Get more detailed error from the server if possible
                const errorBody = await response.json();
                throw new Error(`Server responded with ${response.status}: ${errorBody.detail || response.statusText}`);
            }

            const result = await response.json();
            console.log('Backend response:', result);

            // 4. Show a success message
            vscode.window.showInformationMessage('Agent task completed successfully!');

        } catch (error: any) {
            console.error('Error communicating with backend:', error);
            vscode.window.showErrorMessage(`AgentDev Error: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}
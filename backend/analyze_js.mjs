import babelParser from '@babel/parser';
import traverse from '@babel/traverse'; 
import fs from 'fs';

try {
    const code = fs.readFileSync(0, 'utf-8');

    if (!code.trim()) {
        console.log(JSON.stringify({ functions: [], classes: [], variables: [], imports: [] }));
        process.exit(0);
    }

    const ast = babelParser.parse(code, {
        sourceType: 'module',
        plugins: ['jsx', 'typescript'], // Added typescript support
        errorRecovery: true
    });
    
    // The new, more detailed summary structure
    const summary = {
        functions: [],
        classes: [],
        variables: [],
        imports: []
    };

    // This is the "Visitor". It's a more powerful way to traverse the AST.
    // It will run specific functions when it "visits" a node of a certain type.
    const visitor = {
        // Visitor for standard functions: function myFunction(param1) { ... }
        FunctionDeclaration(path) {
            const functionName = path.node.id ? path.node.id.name : '[anonymous]';
            const params = path.node.params.map(p => p.name || (p.left ? p.left.name : '...')); // Handle assignment patterns
            summary.functions.push({ name: functionName, params: params });
            path.skip(); // Don't traverse inside this function to avoid duplicate counting
        },
        // Visitor for classes: class MyClass { method1() { ... } }
        ClassDeclaration(path) {
            const className = path.node.id ? path.node.id.name : '[anonymous]';
            const classInfo = { name: className, methods: [] };

            // Traverse the body of THIS class to find its methods
            path.traverse({
                ClassMethod(methodPath) {
                    const methodName = methodPath.node.key.name;
                    const params = methodPath.node.params.map(p => p.name || (p.left ? p.left.name : '...'));
                    classInfo.methods.push({ name: methodName, params: params });
                }
            });
            
            summary.classes.push(classInfo);
            path.skip(); // We've handled this class and its methods
        },
        // Visitor for variable declarations, good for finding arrow functions
        VariableDeclarator(path) {
            // Check if it's a top-level variable
            if (path.scope.block.type === 'Program') {
                if (path.node.id.type === 'Identifier') {
                    summary.variables.push(path.node.id.name);
                }
            }
        },
        // Visitor for imports: import React from 'react';
        ImportDeclaration(path) {
            summary.imports.push(path.node.source.value);
        }
    };

    // Start the traversal with our visitor
    traverse.default(ast, visitor);

    console.log(JSON.stringify(summary, null, 2)); // Pretty-print for easier debugging

} catch (e) {
    console.error(JSON.stringify({ error: e.message }));
    process.exit(1);
}

import babelParser from '@babel/parser';
import traverse from '@babel/traverse';
import fs from 'fs';

try {
    const code = fs.readFileSync(0, 'utf-8');
    if (!code.trim()) {
        console.log(JSON.stringify({}));
        process.exit(0);
    }

    const ast = babelParser.parse(code, {
        sourceType: 'module',
        plugins: ['jsx', 'typescript'],
        errorRecovery: true
    });

    const report = {
        classes: {},
        variables: [],
        functions: []
    };

    function argNodeToString(node) {
        if (!node) return '...';
        switch (node.type) {
            case 'StringLiteral': return `'${node.value}'`;
            case 'NumericLiteral': return `${node.value}`;
            case 'Identifier': return node.name;
            case 'BinaryExpression':
                return `${argNodeToString(node.left)} ${node.operator} ${argNodeToString(node.right)}`;
            case 'MemberExpression':
                return `${argNodeToString(node.object)}.${argNodeToString(node.property)}`;
            default:
                return '[complex value]';
        }
    }

    const visitor = {
        ClassDeclaration(path) {
            const className = path.node.id.name;
            const classInfo = { name: className, constructor: null, methods: [] };

            path.traverse({
                ClassMethod(methodPath) {
                    const methodName = methodPath.node.key.name;
                    const params = methodPath.node.params.map(p => p.name || '...');
                    if (methodName === 'constructor') {
                        classInfo.constructor = { params: params };
                    } else {
                        classInfo.methods.push({ name: methodName, params: params });
                    }
                }
            });
            report.classes[className] = classInfo;
            path.skip();
        },
        VariableDeclarator(path) {
            if (path.scope.block.type === 'Program' && path.node.id.type === 'Identifier') {
                const varName = path.node.id.name;
                let varValue = '[uninitialized]';
                if (path.node.init) {
                    // It now explicitly handles NewExpression and formats it correctly.
                    if (path.node.init.type === 'NewExpression') {
                        const className = path.node.init.callee.name;
                        const args = path.node.init.arguments.map(argNodeToString);
                        varValue = `new ${className}(${args.join(', ')})`;
                    } else {
                        // Fallback for simple values like numbers or strings
                        varValue = argNodeToString(path.node.init);
                    }
                }
                report.variables.push({ name: varName, value: varValue });
            }
        }
    };

    traverse.default(ast, visitor);
    console.log(JSON.stringify(report, null, 2));

} catch (e) {
    console.error(JSON.stringify({ error: e.message }));
    process.exit(1);
}
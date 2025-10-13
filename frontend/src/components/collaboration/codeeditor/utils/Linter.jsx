import { linter } from "@codemirror/lint"

// Python built-in functions and keywords
const pythonBuiltins = new Set([
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
    'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod',
    'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
    'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
    'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
    'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range',
    'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
    'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip', '__import__',
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for',
    'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
    'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
    'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError',
    'self', 'cls', '__name__', '__main__'
])

export const createPythonLinter = () => {
    return linter((view) => {
        const diagnostics = []
        const text = view.state.doc.toString()
        const lines = text.split('\n')

        // Track defined variables
        const definedNames = new Set(pythonBuiltins)

        // First pass: collect all definitions
        lines.forEach((line) => {
            const trimmed = line.trim()
            if (trimmed.startsWith('#') || trimmed.length === 0) return

            // Function/class definitions
            const funcMatch = trimmed.match(/^def\s+(\w+)/)
            if (funcMatch) definedNames.add(funcMatch[1])

            const classMatch = trimmed.match(/^class\s+(\w+)/)
            if (classMatch) definedNames.add(classMatch[1])

            // Import statements
            const importMatch = trimmed.match(/^import\s+([\w, ]+)/)
            if (importMatch) {
                importMatch[1].split(',').forEach(name => definedNames.add(name.trim()))
            }
            const fromImportMatch = trimmed.match(/^from\s+\w+\s+import\s+(.+)/)
            if (fromImportMatch) {
                fromImportMatch[1].split(',').forEach(name => {
                    const cleaned = name.trim().split(' as ')[0].trim()
                    if (cleaned !== '*') definedNames.add(cleaned)
                })
            }

            // Variable assignments
            const assignMatch = trimmed.match(/^(\w+)\s*=/)
            if (assignMatch) definedNames.add(assignMatch[1])

            // For loop variables
            const forMatch = trimmed.match(/^for\s+(\w+)\s+in/)
            if (forMatch) definedNames.add(forMatch[1])

            // Function parameters
            const paramMatch = trimmed.match(/^def\s+\w+\s*\((.*?)\)/)
            if (paramMatch && paramMatch[1]) {
                paramMatch[1].split(',').forEach(param => {
                    const name = param.trim().split('=')[0].split(':')[0].trim()
                    if (name && name !== '*' && name !== '**') {
                        definedNames.add(name.replace('*', ''))
                    }
                })
            }

            // Multiple assignments: a, b = 1, 2
            const multiMatch = trimmed.match(/^([\w\s,]+)=/)
            if (multiMatch && multiMatch[1].includes(',')) {
                multiMatch[1].split(',').forEach(v => definedNames.add(v.trim()))
            }
        })

        // Second pass: check for errors
        lines.forEach((line, lineIndex) => {
            const from = view.state.doc.line(lineIndex + 1).from
            const to = view.state.doc.line(lineIndex + 1).to

            // Check for common Python syntax errors

            // Missing colon after if, for, while, def, class
            if (/^\s*(if|elif|while|for|def|class|with|try|except|finally)\s+.*[^:]$/.test(line) &&
                !line.trim().endsWith('\\') && line.trim().length > 0) {
                diagnostics.push({
                    from,
                    to,
                    severity: 'error',
                    message: 'Missing colon at end of statement'
                })
            }

            // Unmatched parentheses, brackets, braces
            const openParens = (line.match(/\(/g) || []).length
            const closeParens = (line.match(/\)/g) || []).length
            const openBrackets = (line.match(/\[/g) || []).length
            const closeBrackets = (line.match(/\]/g) || []).length
            const openBraces = (line.match(/\{/g) || []).length
            const closeBraces = (line.match(/\}/g) || []).length

            if (openParens !== closeParens || openBrackets !== closeBrackets || openBraces !== closeBraces) {
                diagnostics.push({
                    from,
                    to,
                    severity: 'error',
                    message: 'Unmatched parentheses, brackets, or braces'
                })
            }

            // Unmatched quotes (simple check)
            const singleQuotes = (line.match(/'/g) || []).length
            const doubleQuotes = (line.match(/"/g) || []).length
            if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
                diagnostics.push({
                    from,
                    to,
                    severity: 'error',
                    message: 'Unmatched quotes'
                })
            }

            // Check for incorrect indentation (tabs mixed with spaces)
            if (/^\t+ +/.test(line) || /^ +\t+/.test(line)) {
                diagnostics.push({
                    from,
                    to,
                    severity: 'warning',
                    message: 'Mixed tabs and spaces in indentation'
                })
            }

            // Check for undefined variables - strict checking
            const trimmed = line.trim()
            if (trimmed.startsWith('#') || trimmed.length === 0) return

            // Extract all identifiers from the line
            const identifierRegex = /\b([a-zA-Z_]\w*)\b/g
            let match
            const checkedPositions = new Set()

            while ((match = identifierRegex.exec(line)) !== null) {
                const identifier = match[1]
                const matchPos = match.index

                if (checkedPositions.has(matchPos)) continue
                checkedPositions.add(matchPos)

                // Skip if it's being defined on this line
                const isDefinition = (
                    new RegExp(`^\\s*def\\s+${identifier}\\b`).test(trimmed) ||
                    new RegExp(`^\\s*class\\s+${identifier}\\b`).test(trimmed) ||
                    new RegExp(`^\\s*${identifier}\\s*=`).test(trimmed) ||
                    new RegExp(`^\\s*for\\s+${identifier}\\s+in`).test(trimmed) ||
                    new RegExp(`^\\s*import\\s+.*\\b${identifier}\\b`).test(trimmed) ||
                    new RegExp(`^\\s*from\\s+.*import\\s+.*\\b${identifier}\\b`).test(trimmed)
                )

                // Skip if in string or comment
                const beforeMatch = line.substring(0, matchPos)
                const singleQuotes = (beforeMatch.match(/'/g) || []).length
                const doubleQuotes = (beforeMatch.match(/"/g) || []).length
                const inString = singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0
                const inComment = beforeMatch.includes('#')

                // Check if undefined
                if (!isDefinition && !definedNames.has(identifier) && !inString && !inComment) {
                    const pos = from + matchPos
                    diagnostics.push({
                        from: pos,
                        to: pos + identifier.length,
                        severity: 'error',
                        message: `Undefined name '${identifier}'`
                    })
                }
            }

            // Check for = instead of == in conditions
            if (/^\s*if\s+.*[^=!<>]=[^=]/.test(line)) {
                const equalPos = line.indexOf('=')
                if (equalPos > 0 && line[equalPos - 1] !== '=' && line[equalPos + 1] !== '=') {
                    diagnostics.push({
                        from: from + equalPos,
                        to: from + equalPos + 1,
                        severity: 'warning',
                        message: 'Assignment in condition. Did you mean == ?'
                    })
                }
            }
        })

        return diagnostics
    })
}

export const pythonLinter = createPythonLinter()
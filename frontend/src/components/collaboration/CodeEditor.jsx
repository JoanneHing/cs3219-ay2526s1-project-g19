import { useState, useEffect, useRef, useCallback } from "react"
import io from "socket.io-client"
import CodeMirror from "@uiw/react-codemirror"
import { python } from "@codemirror/lang-python"
import { sublime } from "@uiw/codemirror-theme-sublime"
import { EditorView, Decoration, WidgetType } from "@codemirror/view"
import { StateField } from "@codemirror/state"
import { linter } from "@codemirror/lint"
import EditorHeader from "./codeeditor/EditorHeader"
import EditorStatsBar from "./codeeditor/EditorCursorBar"
import EditorRunButton from "./codeeditor/EditorRunButton"
import EditorOutputTerminal from "./codeeditor/EditorOutputTerminal"

const CodeEditor = ({ room, currentUsername }) => {
    const [code, setCode] = useState({
        value: "print('hello world')",
        isReceived: false,
    })
    const [output, setOutput] = useState("")
    const [isRunning, setIsRunning] = useState(false)
    const [cursorPosition, setCursorPosition] = useState({ line: 1, ch: 0 })
    const [remoteCursors, setRemoteCursors] = useState({})
    const [isConnected, setIsConnected] = useState(false)
    const [linterMode, setLinterMode] = useState("python") // "none" or "python"
    const editorViewRef = useRef(null)
    const collabSocketRef = useRef(null)
    const cursorsRef = useRef({})
    const lastEmitTime = useRef(0)

    const handleBeforeUnload = useCallback(() => {
        if (collabSocketRef.current) {
            collabSocketRef.current.disconnect()
        }
    }, [])

    useEffect(() => {
        // Initialize collaboration socket
        // When using proxy paths, Socket.IO needs the path option set correctly
        // This tells Socket.IO to connect to `ws://<host>/collaboration-service-api/socket.io`
        collabSocketRef.current = io(window.location.origin, { path: `${import.meta.env.VITE_COLLABORATION_SERVICE_URL}/socket.io` });
        console.log('Connecting to Socket.IO with path:', `${import.meta.env.VITE_COLLABORATION_SERVICE_URL}/socket.io`)

        collabSocketRef.current.on("connect", () => {
            console.log(`Connected to collab server with SID ${collabSocketRef.current.id}`)
            collabSocketRef.current.emit("join", { room: room })
            setIsConnected(true)
        })

        collabSocketRef.current.on("disconnect", () => {
            setIsConnected(false)
        })

        window.addEventListener("beforeunload", handleBeforeUnload)
        window.addEventListener("unload", handleBeforeUnload)

        return () => {
            handleBeforeUnload()
            window.removeEventListener("beforeunload", handleBeforeUnload)
            window.removeEventListener("unload", handleBeforeUnload)
        }
    }, [room, handleBeforeUnload])

    useEffect(() => {
        cursorsRef.current = remoteCursors
    }, [remoteCursors])

    const lineCharToPos = (doc, lineChar) => {
        try {
            if (lineChar.line > doc.lines) return doc.length
            const line = doc.line(lineChar.line)
            return line.from + Math.min(lineChar.ch, line.length)
        } catch {
            return 0
        }
    }

    const posToLineChar = (doc, pos) => {
        const line = doc.lineAt(pos)
        return {
            line: line.number,
            ch: pos - line.from
        }
    }

    class CursorWidget extends WidgetType {
        constructor(userId, color, username, line) {
            super()
            this.userId = userId
            this.color = color
            this.username = username
            this.line = line
        }

        toDOM() {
            const wrapper = document.createElement("span")
            wrapper.className = "remote-cursor-wrapper"
            wrapper.style.cssText = `
                position: relative;
                display: inline-block;
                pointer-events: auto;
            `
            
            const cursor = document.createElement("span")
            cursor.className = "remote-cursor"
            cursor.style.cssText = `
                border-left: 2px solid ${this.color};
                height: 1.2em;
                display: inline-block;
                position: relative;
                margin-left: -1px;
            `
            
            const label = document.createElement("div")
            label.textContent = this.username
            label.className = "cursor-label"
            // Default: above the cursor
            let labelPosition = `
                position: absolute;
                bottom: 100%;
                left: 0;
                margin-bottom: 4px;
            `
            // If on line 1 or 2, flip below
            if (this.line <= 2) {
                labelPosition = `
                    position: absolute;
                    top: 100%;
                    left: 0;
                    margin-top: 4px;
                `
            }
            label.style.cssText = `
                ${labelPosition}
                background: ${this.color};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                white-space: nowrap;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.2s ease;
                pointer-events: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            `
            
            wrapper.appendChild(cursor)
            wrapper.appendChild(label)
            
            wrapper.addEventListener('mouseenter', () => {
                label.style.opacity = '1'
            })
            wrapper.addEventListener('mouseleave', () => {
                label.style.opacity = '0'
            })
            wrapper.addEventListener('click', () => {
                label.style.opacity = '1'
                setTimeout(() => {
                    label.style.opacity = '0'
                }, 2000)
            })
            
            return wrapper
        }

        eq(other) {
            return other instanceof CursorWidget && 
                   this.userId === other.userId && 
                   this.color === other.color &&
                   this.username === other.username
        }

        updateDOM() {
            return false
        }

        get estimatedHeight() {
            return 0
        }

        ignoreEvent() {
            return false
        }
    }

    const cursorsField = StateField.define({
        create() {
            return Decoration.none
        },
        update(cursors, tr) {
            const decorations = []
            const currentCursors = cursorsRef.current
            
            Object.entries(currentCursors).forEach(([userId, cursor]) => {
                const pos = lineCharToPos(tr.state.doc, { line: cursor.line, ch: cursor.ch })
                if (pos >= 0 && pos <= tr.state.doc.length) {
                    const decoration = Decoration.widget({
                        widget: new CursorWidget(userId, cursor.color, cursor.username, cursor.line),
                        side: 1
                    })
                    decorations.push(decoration.range(pos))
                }
            })
            
            return Decoration.set(decorations, true)
        },
        provide: f => EditorView.decorations.from(f)
    })

    const getUserColor = (userId) => {
        const colors = ['#FF4136', '#2ECC40', '#0074D9', '#B10DC9', '#FF851B', '#FFDC00']
        let hash = 0
        for (let i = 0; i < userId.length; i++) {
            hash = ((hash << 5) - hash + userId.charCodeAt(i)) & 0xffffffff
        }
        return colors[Math.abs(hash) % colors.length]
    }

    const emitCursorPosition = (lineChar) => {
        const now = Date.now()
        if (now - lastEmitTime.current < 100) return

        lastEmitTime.current = now
        if (collabSocketRef.current && collabSocketRef.current.connected) {
            collabSocketRef.current.emit("cursor", {
                room: room,
                line: lineChar.line,
                ch: lineChar.ch,
                userId: collabSocketRef.current.id,
                username: currentUsername
            })
        }
    }

    // Python linter function - strict checking for undefined variables
    const pythonLinter = linter((view) => {
        const diagnostics = []
        const text = view.state.doc.toString()
        const lines = text.split('\n')

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

    useEffect(() => {
        if (editorViewRef.current) {
            editorViewRef.current.dispatch({})
        }
    }, [remoteCursors])

    useEffect(() => {
        if (!collabSocketRef.current) return

        collabSocketRef.current.on("receive", (payload) => {
            console.log("Received code update:", payload.code)
            setCode({ value: payload.code, isReceived: true })
        })

        collabSocketRef.current.on("cursor", (data) => {
            console.log("Received cursor update:", data)
            
            if (data.userId !== collabSocketRef.current.id) {
                setRemoteCursors(prev => ({
                    ...prev,
                    [data.userId]: {
                        line: data.line,
                        ch: data.ch,
                        color: getUserColor(data.userId),
                        username: currentUsername,
                        timestamp: Date.now()
                    }
                }))
            }
        })

        collabSocketRef.current.on("user_left", (data) => {
            setRemoteCursors(prev => {
                const newCursors = { ...prev }
                delete newCursors[data.userId]
                return newCursors
            })
        })

        return () => {
            collabSocketRef.current.off("receive")
            collabSocketRef.current.off("cursor")
            collabSocketRef.current.off("user_left")
        }
    }, [collabSocketRef.current])

    useEffect(() => {
        const interval = setInterval(() => {
            const now = Date.now()
            setRemoteCursors(prev => {
                const filtered = {}
                let hasChanges = false
                
                Object.entries(prev).forEach(([userId, cursor]) => {
                    if (now - cursor.timestamp < 60000) {
                        filtered[userId] = cursor
                    } else {
                        hasChanges = true
                    }
                })
                
                return hasChanges ? filtered : prev
            })
        }, 10000)

        return () => clearInterval(interval)
    }, [])

    function updateCode(room, value) {
        if (!collabSocketRef.current) return

        if (!code.isReceived) {
            collabSocketRef.current.emit("change", { room: room, code: value })
        }
        setCode({ value: value, isReceived: false })
    }

    const runCode = async () => {
        setIsRunning(true)
        setOutput("Running...")
        
        try {
            const response = await fetch(`${import.meta.env.VITE_EXECUTION_API}/run`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ code: code.value }),
            })
            
            const data = await response.json()
            setOutput(data.output || data.error)
        } catch (error) {
            setOutput("Error: Could not connect to execution service")
        } finally {
            setIsRunning(false)
        }
    }

    // Conditionally include linter based on mode
    const cursorExtension = [
        cursorsField,
        ...(linterMode === "python" ? [pythonLinter] : []),
        EditorView.updateListener.of((update) => {
            if (update.selectionSet) {
                const pos = update.state.selection.main.head
                const lineChar = posToLineChar(update.state.doc, pos)
                setCursorPosition(lineChar)
                emitCursorPosition(lineChar)
            }
        })
    ]

    if (!isConnected) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                    <p className="text-gray-600 dark:text-gray-400 text-sm font-medium">
                        Connecting to collaboration server...
                    </p>
                </div>
            </div>
        )
    }

    return (
        <div className="w-full max-w-6xl mx-auto p-6 space-y-4">
            <div className="flex items-center justify-between">
                <EditorStatsBar cursorPosition={cursorPosition} remoteCursors={remoteCursors} />
                <div className="flex items-center gap-2">
                    <label htmlFor="linter-select" className="text-sm font-medium text-gray-300">
                        Linter:
                    </label>
                    <select
                        id="linter-select"
                        value={linterMode}
                        onChange={(e) => setLinterMode(e.target.value)}
                        className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-slate-500 transition-colors cursor-pointer"
                    >
                        <option value="none">None</option>
                        <option value="python">Python Linter</option>
                    </select>
                </div>
            </div>
            <div className="rounded-xl overflow-hidden shadow-2xl border border-slate-700">
                <EditorHeader filename="editor.py" />
                <CodeMirror
                    value={code.value}
                    height="50vh"
                    maxHeight="50vh"
                    onChange={(value) => updateCode(room, value)}
                    extensions={[python(), ...cursorExtension]}
                    theme={sublime}
                    onCreateEditor={(view) => {
                        editorViewRef.current = view
                    }}
                    basicSetup={{
                        lineNumbers: true,
                        foldGutter: true,
                        dropCursor: false,
                        allowMultipleSelections: false,
                        indentOnInput: true,
                        bracketMatching: true,
                        closeBrackets: true,
                        autocompletion: true,
                        highlightSelectionMatches: false
                    }}
                />
            </div>
            <EditorRunButton onClick={runCode} isRunning={isRunning} />
            {output && <EditorOutputTerminal output={output} />}
        </div>
    )
}

export default CodeEditor
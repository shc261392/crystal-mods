#!/bin/bash

# Stop hook: Enforce test suite passes before agent stops
# This hook runs the test suite and blocks the stop if tests fail

set -euo pipefail

emit_block() {
        local reason="$1"
        echo "{\n    \"hookSpecificOutput\": {\n        \"hookEventName\": \"Stop\",\n        \"decision\": \"block\",\n        \"reason\": \"${reason}\"\n    }\n}" >&2
        exit 2
}

# Parse input from VS Code hook
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
CWD=$(echo "$INPUT" | jq -r '.cwd')

# Optional debug dump for schema troubleshooting.
if [ "${STOP_HOOK_DEBUG:-0}" = "1" ]; then
    printf '%s\n' "$INPUT" > /tmp/stophook.last-input.json
fi

# Detect ask_questions tool invocation in the current stop-hook payload.
# We intentionally check several common shapes to tolerate schema drift.
ASK_QUESTIONS_DETECTED=false
if echo "$INPUT" | jq -e '
    (
        [.. | objects | select((.toolName? // "") == "vscode_askQuestions")] | length
    ) > 0
    or
    (
        [.. | objects | select((.recipient_name? // "") == "functions.vscode_askQuestions")] | length
    ) > 0
    or
    (
        [.. | objects | select((.name? // "") == "vscode_askQuestions")] | length
    ) > 0
    or
    (
        [.. | objects | select((.tool? // "") == "vscode_askQuestions")] | length
    ) > 0
' >/dev/null; then
        ASK_QUESTIONS_DETECTED=true
fi

# Fallback 1: raw JSON key/value pattern scan (for unknown schema wrappers).
if [ "$ASK_QUESTIONS_DETECTED" != "true" ]; then
    if echo "$INPUT" | grep -Eq '"(toolName|recipient_name|recipientName|name|tool)"[[:space:]]*:[[:space:]]*"(functions\.vscode_askQuestions|vscode_askQuestions)"'; then
        ASK_QUESTIONS_DETECTED=true
    fi
fi

# Fallback 2: if hook payload points to a transcript/log file, scan that file.
if [ "$ASK_QUESTIONS_DETECTED" != "true" ]; then
    TRANSCRIPT_HINT=$(echo "$INPUT" | jq -r '.transcriptPath // .transcript_path // .sessionLogPath // .session_log_path // empty')
    if [ -n "${TRANSCRIPT_HINT:-}" ] && [ -f "$TRANSCRIPT_HINT" ]; then
        if tail -n 800 "$TRANSCRIPT_HINT" | grep -Eq 'vscode_askQuestions|functions\.vscode_askQuestions'; then
            ASK_QUESTIONS_DETECTED=true
        fi
    fi
fi

# Fallback 3: if VS Code exposes the current session log path, inspect it too.
if [ "$ASK_QUESTIONS_DETECTED" != "true" ] && [ -n "${VSCODE_TARGET_SESSION_LOG:-}" ] && [ -f "$VSCODE_TARGET_SESSION_LOG" ]; then
    if tail -n 800 "$VSCODE_TARGET_SESSION_LOG" | grep -Eq 'vscode_askQuestions|functions\.vscode_askQuestions'; then
        ASK_QUESTIONS_DETECTED=true
    fi
fi

if [ "$ASK_QUESTIONS_DETECTED" != "true" ]; then
    emit_block "Stop blocked: missing ask_questions evidence in current turn payload/logs. Call vscode_askQuestions before ending."
fi

# Prevent infinite loops if this hook has already run
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
        # On re-entry we still enforce ask_questions gate above, but skip heavy checks.
    exit 0
fi

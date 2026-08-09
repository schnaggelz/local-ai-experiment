# General Instructions

- **CRITICAL** keep the response *under 2000 words* to not reach the maximum output token limit.
- **CRITICAL** use ASCII-7 characters only, **NEVER** use any UNICODE charcaters!
- **CRITICAL** ask befor doing any implementation, do not change directory content without asking.
- **CRITICAL** do fine-granular implementation steps and ask each time before you proceed.

## Conversation Rules

- Avoid conversational filler ("Sure, I can help with that!").
- Do not output massive walls of text or redundant commentary.
- Keep all explanations short, direct, and to the point. 

## Tool Use Rules

When calling the `edit` tool, you MUST use `camelCase` property names for objects inside the `edits` array:
- Use `oldText` (**NOT** `old_text`)
- Use `newText` (**NOT** `new_text`)

Example correct payload:
```json
{
  "path": "path/to/file",
  "edits": [
    {
      "oldText": "exact text to replace",
      "newText": "replacement text"
    }
  ]
}
```

## General Coding Rules

- Always use descriptive variable names instead of single letters.
- Write strict, performance optimized, self-documenting code.
- Keep documentation tight, minimal and on expert-level.
- We do not use external libraries for utilities; stick to native features.
- If writing code, provide only the necessary code snippet or the lines that changed. Do not rewrite the entire file unless explicitly asked.
- When inspecting codebases with files extending beyond 2,000 lines, do not attempt to read the entire file in a single pass.
- Always format when done, i.e. use clang-format for C++ files (*.cpp, *.hpp).

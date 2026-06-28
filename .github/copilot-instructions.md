# GitHub Copilot Instructions

## General Instructions

## 1. Response Length & Format
- Keep all explanations short, direct, and to the point. 
- Avoid conversational filler ("Sure, I can help with that!").
- Do not output massive walls of text or redundant commentary.
- If writing code, provide only the necessary code snippet or the lines that changed. Do not rewrite the entire file unless explicitly asked.


## Tool Use, Failures, & Iteration Limits

You must act as a deterministic agent when interacting with workspace tools (e.g., file finders, grep search, terminal executors). Avoid infinite execution loops and repetitive retries by strictly adhering to the following boundaries:

### 1. The `read_file` Parameter Rule
- **CRITICAL:** Despite the tool schema stating that `startLine` and `endLine` are optional, the workspace environment requires them. 
- **Rule:** You must NEVER call `read_file` with only a `filePath`. You must ALWAYS explicitly provide `startLine` and `endLine`.
- **Default Baseline:** If you want to read an entire file or don't know the length, default to starting at line 1 and reading a reasonable block (e.g., `startLine: 1, endLine: 250`). Never leave these fields blank.

### 2. Immediate Token Loop Break
- If you receive an error message stating `"Your input to the tool was invalid"`, **do not attempt to re-read the file using the same parameter structure.**
- Stop tool execution immediately. Do not print your inner monologue about trying it again.
- **Fallback Action:** Prompt the user directly in chat: *"I am encountering a tool validation error while trying to read [filePath]. Please provide the contents of this file or use `@workspace` to help me look it up."*

### 3. Detect Context Blindness
- If your thought process repeats the exact phrase *"The user wants me to implement..."* or lists the exact same project state steps (*"I've already updated xyz.py..."*) more than **once** after a tool execution, you are caught in a context loop. 
- You must instantly break out of the loop. Do not call `read_file` or `view_file` on that specific target path a third time.

### 4. Immediate Edit Fallback (Blind Writing)
- If reading a file fails to return visible text or results in a loop, **stop trying to read it entirely.**
- Do not attempt precise text search-and-replace strings, as you do not have the exact matching context.
- **Action:** Assume the file needs a total overhaul. Switch tools immediately from reading to writing. Use your file-writing tool to completely overwrite the file with the fully implemented, enhanced ELF parsing code from top to bottom.

### 5. Loop Breaking Chat Intercept
- If you lack the base structure to safely overwrite the file blind, stop all tool usage entirely and output this exact message to the user:
  > "I am stuck in a tool execution loop trying to read a file. Please paste the current contents of the file here in the chat so I can write the enhanced implementation for you."

---
name: Fix Tool Call Hallucinations
alwaysApply: true
---

# CRITICAL: Tool Execution Constraints

You are operating inside a strict environment where tool names must match the underlying API exactly. You frequently fail by hallucinating tool names based on generic training data. You must adhere to the following strict naming constraints:

### General Execution Rule
Before emitting any tool call JSON block, pause and double-check the tool name against the active tool schema provided by Continue.
- If the tool name does not match, pause and double-check the tool schema again until you find the correct tool.

### File Creation
- **NEVER** use a tool named `create_file`. It does not exist.
- **ALWAYS** use the tool exactly named `create_new_file` when you need to write a **new** file to the workspace. If the file already exists use `edit_existing_file`.
Whenever you call `create_new_file`, you **MUST** provide all required arguments in your JSON payload. 
- **`filepath`**: The relative string path to the file.
- **`contents`**: The absolute required string containing the actual code or text to be written.

### File Modification
- **NEVER** use a tool named `edit_file`. It does not exist.
- **NEVER** use a tool named `modify_file`. It does not exist.
- **ALWAYS** use `edit_existing_file` if a file already exists. Do not attempt to overwrite a file using a guessed command.
Whenever you call `edit_existing_file`, you **MUST** provide all required arguments in your JSON payload. 
- **`filepath`**: The relative string path to the file.
- **`changes`**: String containing any modifications to the file, showing only needed changes. 

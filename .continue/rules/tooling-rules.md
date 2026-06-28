---
name: Fix Tool Call Hallucinations
alwaysApply: true
---

# CRITICAL: Tool Execution Constraints

You are operating inside a strict environment where tool names must match the underlying API exactly. You frequently fail by hallucinating tool names based on generic training data. You must adhere to the following strict naming constraints:

### File Creation
- **NEVER** use a tool named `create_file`. It does not exist.
- **ALWAYS** use the tool exactly named `create_new_file` when you need to write a new file to the workspace.
- If you call `create_file`, the system will crash and the user will see an error.

### File Modification
- **NEVER** use a tool named `edit_file`. It does not exist.
- **NEVER** use a tool named `modify_file`. It does not exist.
- **ALWAYS** use `edit_existing_file` if a file already exists. Do not attempt to overwrite a file using a guessed command.

### General Execution Rule
Before emitting any tool call JSON block, pause and double-check the tool name against the active tool schema provided by Continue. If the tool name you are about to write is `create_file`, change it to `create_new_file` before outputting.

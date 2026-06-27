# Apply Modelfile

## Step 1: Pull the Base Model

Ensure you have the base gemma4:26b weights already downloaded via Ollama:

```sh
ollama pull gemma4:26b
```

## Step 2: Create the Custom Model

Navigate to the directory where you saved your Modelfile, and use the ollama create command. Give your newly configured model a distinct name (e.g., gemma4-26b-longctx):

```sh
ollama create gemma4-26b-longctx -f ./Modelfile
```

## Step 3: Run the Model

Now, call your new custom model variant directly via the CLI, or reference it via your favorite UI wrappers (like OpenWebUI or OpenCode):

```sh
ollama run gemma4-26b-longctx
´´´

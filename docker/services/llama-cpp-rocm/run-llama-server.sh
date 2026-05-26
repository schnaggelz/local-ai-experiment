set -eu

: "${LLAMA_HOST:=0.0.0.0}"

set -- \
  --model "$MODEL" \
  --host "$LLAMA_HOST" \
  --port "$LLAMA_PORT" \
  --ctx-size "$LLAMA_CTX_SIZE" \
  --predict "$LLAMA_PREDICT" \
  --threads "$LLAMA_THREADS" \
  --threads-batch "$LLAMA_THREADS_BATCH" \
  --batch-size "$LLAMA_BATCH_SIZE" \
  --ubatch-size "$LLAMA_UBATCH_SIZE" \
  --parallel "$LLAMA_PARALLEL" \
  --timeout "$LLAMA_TIMEOUT" \
  --threads-http "$LLAMA_THREADS_HTTP" \
  --gpu-layers "$LLAMA_GPU_LAYERS" \
  --n-cpu-moe "$LLAMA_N_CPU_MOE"

if [ "$LLAMA_CPU_MOE" = "1" ]; then
  set -- "$@" --cpu-moe
fi

if [ -n "$LLAMA_API_KEY" ]; then
  set -- "$@" --api-key "$LLAMA_API_KEY"
fi

if [ -n "$LLAMA_SYSTEM_PROMPT_FILE" ]; then
  set -- "$@" --system-prompt-file "$LLAMA_SYSTEM_PROMPT_FILE"
fi

if [ "$LLAMA_FLASH_ATTN" = "1" ]; then
  set -- "$@" --flash-attn
fi

if [ "$LLAMA_METRICS" = "1" ]; then
  set -- "$@" --metrics
fi

if [ "$LLAMA_MLOCK" = "1" ]; then
  set -- "$@" --mlock
fi

if [ "$LLAMA_NO_MMAP" = "1" ]; then
  set -- "$@" --no-mmap
fi

if [ "$LLAMA_VERBOSE" = "1" ]; then
  set -- "$@" --verbose
fi

if [ -n "$LLAMA_EXTRA_ARGS" ]; then
  set -- "$@" $LLAMA_EXTRA_ARGS
fi

exec /app/llama-server "$@"
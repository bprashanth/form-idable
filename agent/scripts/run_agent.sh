#!/bin/bash
set -e

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <prompt_file> <input_file_1> [input_file_2 ...]"
    exit 1
fi

PROMPT_FILE="$1"
shift
INPUT_FILES=("$@")

FILE_ARGS=""
for f in "${INPUT_FILES[@]}"; do
    FILE_ARGS+="@$f "
done

if ! command -v gemini &> /dev/null; then
    echo "Error: gemini command not found" >&2
    exit 1
fi

export XDG_CONFIG_HOME=$(mktemp -d)
trap "rm -rf $XDG_CONFIG_HOME" EXIT

cat "$PROMPT_FILE" | gemini $FILE_ARGS

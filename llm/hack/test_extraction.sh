#! /bin/bash

curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPEN_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @params_extraction.json

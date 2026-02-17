#! /bin/bash
# Assumes server is running: form-idable/server$ uvicorn main:app --port 8070 --host 0.0.0.0 --reload

curl -s -X POST http://localhost:8070/api/upload/json   -H "Content-Type: application/json"   -d @./000_layout.json   -o output_000.xlsx

curl -s -X POST http://localhost:8070/api/upload/json   -H "Content-Type: application/json"   -d @./001_layout.json   -o output_001.xlsx

curl -s -X POST http://localhost:8070/api/upload/json   -H "Content-Type: application/json"   -d @./002_layout.json   -o output_002.xlsx

# Entire pipeline 
curl -s -X POST http://localhost:8070/api/upload  -F "image=@./handwritten.jpg" -o output_handwritten_live.xlsx -w "HTTP status: %{http_code}\n"

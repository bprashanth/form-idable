# Textract form extraction 

Quick and dirty form extraction using textract 

```
aws textract analyze-document \
  --region ap-south-1 \
  --document '{"Bytes": "'$(base64 002.png | tr -d '\n')'"}' \
  --feature-types '["TABLES"]' \
  --output json > textract_output.json
```

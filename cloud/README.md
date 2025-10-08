# Textract form extraction 

Quick and dirty form extraction using textract 

With a file in s3 
```
aws textract analyze-document \
  --region ap-south-1 \
  --document '{"S3Object": {"Bucket":"fomomonguest","Name":"keystone/002.png"}}' 
  --feature-types '["TABLES"]' \
  --output json > textract_output.json
```
or directly 

```
aws textract analyze-document \
  --region ap-south-1 \
  --document '{"Bytes": "'$(base64 002.png | tr -d '\n')'"}' \
  --feature-types '["TABLES"]' \
  --output json > textract_output.json
```

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

## UI Preprocessing

Run the preprocessong on the textract output file to get an intermediate format that can be used with the UI

```console
$ python3 preprocessor.py --input output/001_layout.json --output results/form_001_classified.json --debug
```

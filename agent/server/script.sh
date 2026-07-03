#! /bin/bash
aws lambda invoke \                                                                                                                                                                       
  --function-name form-idable-agent \                                                                                                                                                       
  --region ap-south-1 \                                                                                                                                                                     
  --cli-binary-format raw-in-base64-out \                                                                                                                                                   
  --payload '{"version":"2.0","routeKey":"GET /agent/health","rawPath":"/agent/health","rawQueryString":"","headers":{"host":"test"},"requestContext":{"http":{"method":"GET","path":"/agent
/health","protocol":"HTTP/1.1","sourceIp":"0.0.0.0","userAgent":"test"},"requestId":"test-id","routeKey":"GET /agent/health","stage":"default","time":"01/Jan/2024:00:00:00                 
+0000","timeEpoch":0},"isBase64Encoded":false}' \                                                                                                                                           
  --log-type Tail \                                                                                                                                                                         
  --query 'LogResult' \                                   
  --output text \                                                                                                                                                                           
  /tmp/out.json | base64 -d && echo "---response---" && cat /tmp/out.json

# Agent harness for special type mapping 

Quickstart
```console 
# 1. Start textract server 
cd good-shepherd/server && uvicorn main:app --port 8070 --host 0.0.0.0

# 2. Start agent server
cd form-idable/agent/server && uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt
uvicorn main:app --port 8071 --host 0.0.0.0                                                   

# 3. Smoke test without the UI (no ai): 
# This checks type inference on your existing output.xlsx
curl -s -X POST http://localhost:8071/agent/infer-types -F "file=@pwa/output.xlsx" | jq .    

# 3.a. You can also do this via docker
# cd form-idable/agent/server/ && build.sh --test && docker run --rm -p 8071:8070 form-idable-agent:latest

# 4. Run the ui
cd form-idable/pwa && npm run dev

# See Deployment
```

## Testing fuzz matching

```console
# Test species fuzzy matching via API (run from repo root, server must be on :8071)
curl -s -X POST http://localhost:8071/agent/check-species \
  -F "file=@pwa/output.xlsx" \
  -F 'type_map={"SPP Name/Local Name":{"type":"species","confidence":"medium","matched_keyword":"spp"}}' \
  | jq '.proposals[:5]'
```

See `agent/test/TESTING.md` for how to run the AI verification step manually via CLI.

## Dictionary lookups 

Currently the species dict has only one format, see `data/species_name.csv`. 
It also only supports one dialect, Toda. 

## Testing

Two scripts mirror the good-shepherd pattern:

```console
# Local — server must be running on :8071
cd agent/server/test
bash test_local.sh

# Deployed Lambda — reads FUNCTION_URL from deploy/outputs.env
bash test_deployment.sh
```

**Tests 1–5** (health, cheatsheet, species-db, lookup-species, validation) run without
any test file. **Tests 6–9** (infer-types, check-serial, check-species, apply-species)
require `pwa/output.xlsx`, which must be produced by the good-shepherd upload endpoint
so it contains the `(Good Shepherd) Row ID` column. If the column is absent, steps 8–9
are skipped with a message rather than failing.

Generate a suitable xlsx by:
1. Starting both servers locally
2. Uploading a form image in the PWA (`npm run dev` → capture → process)
3. Running the agent pipeline (Infer → Check Serial → Check Species → Save changes)
4. The corrected file is saved over `xlsxBytes` in the store; Download it to `pwa/output.xlsx`

## Deployment 

This server uses the setup in [heartwood](https://github.com/T4GC-Official/heartwood/blob/main/docs/how-to/onboard-new-component.md#api-servers). To push this it:    
```console 
cd agent/server

# 1. One-time infra (ECR + IAM + budget alert)
./deploy/setup.sh

# 2. Build, test, push, create Lambda + Function URL
./deploy/deploy.sh

# 3. Test local ui -> prod
# Set AGENT_TARGET=https://<lambda-endpoint>.lambda-url.ap-south-1.on.aws

deploy.sh prints the Function URL at the end — replace FUNCTION_URL in netlify.toml with it and push to Netlify.
```

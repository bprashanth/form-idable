# Onboarding

## Adding a new user

Users are created manually in Cognito. They set their own password on first login.

```bash
# 1. Create the Cognito account
aws cognito-idp admin-create-user \
  --user-pool-id ap-south-1_28HVATwK2 \
  --username user@example.com \
  --temporary-password "Temp1234!" \
  --message-action SUPPRESS \
  --region ap-south-1

# 2. Pre-verify their email for SES (so they receive job completion notifications)
aws ses verify-email-identity \
  --email-address user@example.com \
  --region ap-south-1
```

The user will receive a verification email from AWS — they must click the link before their first job notification is sent. Until AWS grants SES production access (sandbox mode is the default), this step is required for every recipient address. To request production access: AWS Console → SES (ap-south-1) → Account Dashboard → "Request production access".

The user logs in at the PWA URL, enters their temporary password, and is prompted to set a permanent one.

---

## Netlify deployment

The repo already has `netlify.toml` at the root — Netlify picks this up automatically.

**One-time setup:**

1. Connect the repo to Netlify (New site → Import from Git).
2. Set this environment variable in **Netlify → Site settings → Environment variables**:

   | Key | Value |
   |-----|-------|
   | `VITE_API_BASE_URL` | `https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod` |

3. Deploy. Netlify runs `npm run build` from the `pwa/` directory (set in `netlify.toml`) and publishes `pwa/dist/`.

**On every push to main:** Netlify redeploys automatically. No further action needed.

The Cognito pool config (user pool ID, client ID) is fetched at runtime from `https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json` — it does not need to be set as an env var.

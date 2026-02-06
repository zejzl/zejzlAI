# Deploy to Render - Security Update

**Date:** February 6, 2026  
**Changes:** API Authentication + CORS Configuration  
**Status:** Ready to deploy

---

## Environment Variables to Add

Go to Render Dashboard → zejzlai service → Environment

### Required Variables

**1. ZEJZL_API_KEY_1** (Secret)
```
zejzl_vMq1NhMpPHyAqAivX1pilXD9URjHneEm:pro:Production API Key
```

**2. CORS_ORIGINS** (Variable)
```
https://zejzl-net.vercel.app,https://zejzl.net
```

**3. ENVIRONMENT** (Variable)
```
production
```

---

## Deployment Steps

### Step 1: Add Environment Variables

1. Open Render Dashboard: https://dashboard.render.com
2. Select service: `zejzlai`
3. Click "Environment" tab
4. Click "Add Environment Variable"

**Add these three:**

| Key | Value | Type |
|-----|-------|------|
| `ZEJZL_API_KEY_1` | `zejzl_vMq1NhMpPHyAqAivX1pilXD9URjHneEm:pro:Production API Key` | Secret |
| `CORS_ORIGINS` | `https://zejzl-net.vercel.app,https://zejzl.net` | Variable |
| `ENVIRONMENT` | `production` | Variable |

5. Click "Save Changes"

---

### Step 2: Deploy

Render will auto-deploy when you save environment variables.

**OR manually deploy:**
1. Click "Manual Deploy" button
2. Select "Deploy latest commit"
3. Wait 2-3 minutes for deployment

---

### Step 3: Verify Deployment

**Test 1: Health Check (No Auth Required)**
```bash
curl https://zejzlai.onrender.com/api/status
```

**Expected:**
```json
{"status": "ok", ...}
```

---

**Test 2: Protected Endpoint Without Auth (Should Fail)**
```bash
curl https://zejzlai.onrender.com/api/chat
```

**Expected:**
```json
{
  "error": "Authentication required",
  "detail": "Include X-API-Key header or Authorization: Bearer token"
}
```

---

**Test 3: Protected Endpoint With Auth (Should Work)**
```bash
curl -X POST https://zejzlai.onrender.com/api/chat \
  -H "X-API-Key: zejzl_vMq1NhMpPHyAqAivX1pilXD9URjHneEm" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "grok-3"}'
```

**Expected:**
```json
{
  "response": "...",
  "provider": "grok-3",
  ...
}
```

---

**Test 4: CORS Headers**
```bash
curl -I https://zejzlai.onrender.com/api/status
```

**Expected Headers:**
```
Access-Control-Allow-Origin: https://zejzl-net.vercel.app
Access-Control-Allow-Credentials: true
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

---

### Step 4: Update Frontend

**File:** `zejzl_net/.env.local` (Vercel)

Add API key for frontend to call backend:

```bash
NEXT_PUBLIC_ZEJZL_API_KEY=zejzl_vMq1NhMpPHyAqAivX1pilXD9URjHneEm
```

**OR** create a separate frontend key:
```bash
# Generate new key for frontend
python -c "import secrets; print('zejzl_' + secrets.token_urlsafe(24))"

# Add to Render as ZEJZL_API_KEY_2
# Add to Vercel as NEXT_PUBLIC_ZEJZL_API_KEY
```

---

## Rollback Plan

If deployment fails:

1. Remove environment variables
2. Redeploy previous version
3. Check logs: Render Dashboard → Logs tab

---

## Monitoring

**Check logs for:**
- ✓ "🔒 CORS configured for origins: ..."
- ✓ "🔒 API authentication middleware enabled"
- ✓ "✓ Authenticated: Production API Key (tier: pro) -> /api/chat"

**Watch for errors:**
- ❌ "Invalid API key attempted from ..."
- ❌ "Rate limit exceeded for key ..."

---

## Security Notes

**API Key Security:**
- Store in Render as Secret (encrypted)
- Never commit to git
- Rotate quarterly
- Use different keys for dev/staging/prod

**CORS Origins:**
- Restrictive whitelist only
- Add new origins as needed
- No wildcards (e.g., no `*.example.com`)

**Rate Limits:**
- Production key: `pro` tier = 100 req/min
- Frontend key (if separate): `enterprise` tier = 1000 req/min
- Monitor usage, upgrade tier if needed

---

## Troubleshooting

### Issue: 401 Unauthorized

**Check:**
- Is API key added to Render environment?
- Is service redeployed after adding key?
- Is frontend sending correct header?

**Fix:**
```bash
# Verify key is set
render env:get ZEJZL_API_KEY_1

# Redeploy
render deploy
```

---

### Issue: CORS Error

**Check:**
- Is `CORS_ORIGINS` set correctly?
- Is frontend origin in the list?
- Are headers being sent correctly?

**Fix:**
```bash
# Add missing origin
CORS_ORIGINS=https://zejzl-net.vercel.app,https://zejzl.net,https://new-origin.com
```

---

### Issue: Rate Limit Hit

**Symptoms:**
- 429 Too Many Requests
- Error: "Rate limit exceeded"

**Solutions:**
1. Wait 60 seconds for reset
2. Upgrade key tier (pro → enterprise)
3. Implement request batching on frontend

---

## Post-Deployment Checklist

- [ ] Environment variables added to Render
- [ ] Service redeployed successfully
- [ ] Health check returns 200 OK
- [ ] Protected endpoints require auth
- [ ] Authenticated requests work
- [ ] CORS headers present
- [ ] Security headers present
- [ ] Logs show authentication messages
- [ ] Frontend updated with API key
- [ ] Frontend can call backend successfully
- [ ] No errors in Render logs
- [ ] Rate limiting working (test with 15+ requests)

---

## Success Criteria

✅ **Backend:**
- API authentication active
- CORS configured
- Security headers on all responses
- Rate limiting enforced
- Logging operational

✅ **Frontend:**
- Can call backend with API key
- CORS allows requests
- Error handling for 401/429

✅ **Monitoring:**
- No errors in logs
- Authentication logs visible
- Rate limit tracking working

---

**Deployed by:** Neo  
**Date:** February 6, 2026  
**Version:** 1.0 (Security Update)

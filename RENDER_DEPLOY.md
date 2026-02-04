# Deploying zejzl.net to Render (Free Tier)

**Date:** February 4, 2026  
**Cost:** FREE (750 hours/month)  
**Limitations:** Spins down after 15min inactivity, ~30s cold start

---

## Quick Deploy

### Option 1: Infrastructure as Code (Recommended)

**1. Push render.yaml to GitHub:**
```bash
git add render.yaml RENDER_DEPLOY.md
git commit -m "Add Render deployment config"
git push origin main
```

**2. Connect Render:**
- Go to https://render.com/
- Sign up / Log in
- Click "New +" → "Blueprint"
- Connect GitHub account
- Select `zejzl/zejzlAI` repository
- Render auto-detects `render.yaml`
- Click "Apply"

**3. Add Environment Variables:**
In Render dashboard → Environment tab, add:
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
GROK_API_KEY=xai-...
```

**4. Deploy:**
Render auto-deploys from GitHub pushes.

---

### Option 2: Manual Web Service

**1. Go to Render Dashboard:**
https://dashboard.render.com/

**2. Click "New +" → "Web Service"**

**3. Connect Repository:**
- Select `zejzl/zejzlAI`
- Branch: `main`

**4. Configure:**
- **Name:** zejzl-net
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn web_dashboard:app --host 0.0.0.0 --port $PORT`
- **Plan:** Free

**5. Environment Variables:**
Add in "Environment" tab:
```
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
GROK_API_KEY
```

**6. Deploy:**
Click "Create Web Service"

---

## What Happens Next

**Build Process (~2-3 minutes):**
1. Render clones repository
2. Installs Python 3.11
3. Runs `pip install -r requirements.txt`
4. Starts `uvicorn web_dashboard:app`

**After First Deploy:**
- **URL:** `https://zejzl-net.onrender.com`
- **Status:** Running (for 15 minutes)
- **Auto-sleep:** After 15min inactivity
- **Wake-up:** 30s cold start on next request

---

## Testing Endpoints

Once deployed, test:

```bash
# Health check
curl https://zejzl-net.onrender.com/health

# System status
curl https://zejzl-net.onrender.com/api/system/status

# Agents list
curl https://zejzl-net.onrender.com/api/agents
```

Expected response time:
- **Active:** <1s
- **Cold start:** ~30s (first request after sleep)

---

## Custom Domain (Optional)

**1. In Render Dashboard:**
- Settings → Custom Domains
- Add `api.zejzl.net`

**2. Update DNS (Cloudflare/your provider):**
```
Type: CNAME
Name: api
Value: zejzl-net.onrender.com
```

**3. Wait for SSL:**
Render auto-provisions SSL (~5 minutes)

---

## Monitoring

**Render provides:**
- Logs (real-time)
- Metrics (CPU, memory, requests)
- Deploy history
- Auto-redeploy on git push

**Free tier limits:**
- 750 hours/month (always free if used <25 days)
- 512MB RAM
- Shared CPU
- 15min inactivity timeout

---

## Troubleshooting

### Build fails: "Requirements not found"
**Fix:** Ensure `requirements.txt` is in repo root
```bash
git add requirements.txt
git commit -m "Add requirements.txt"
git push
```

### "Module not found" errors
**Fix:** Add missing packages to requirements.txt
```bash
echo "missing-package==1.0.0" >> requirements.txt
git commit -am "Add missing dependency"
git push
```

### Service won't start
**Fix:** Check logs in Render dashboard
- Click on service
- "Logs" tab
- Look for Python errors

### Cold starts too slow
**Upgrade to paid plan ($7/mo):**
- No sleep timeout
- Better performance
- More RAM (512MB → 2GB+)

---

## Comparison: Railway vs Render

| Feature | Railway (Paid) | Render (Free) |
|---------|----------------|---------------|
| **Cost** | $5-10/mo | FREE |
| **Cold Starts** | None | ~30s after 15min |
| **RAM** | 512MB-8GB | 512MB |
| **Hours/month** | Unlimited | 750 |
| **Auto-sleep** | No | Yes (15min) |
| **Build time** | ~2min | ~3min |
| **Custom domain** | Free | Free |
| **SSL** | Auto | Auto |

**Recommendation:** Start with Render free tier, upgrade to paid if you need always-on.

---

## Next Steps After Deploy

1. **Test all endpoints** (health, agents, metrics)
2. **Update zejzl.net website** with API links
3. **Monitor performance** (cold start frequency)
4. **Consider upgrade** if >750 hours/month needed

---

**Render is perfect for MVP validation. Zero cost, works great, just has cold starts.** 🚀

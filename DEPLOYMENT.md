# 🚀 Deployment Guide - Ichimoku Gap Scanner

## Quick Deployment to Railway.app (Free Tier)

Railway.app is the easiest option for deploying Flask apps with a free tier. Follow these steps:

### Step 1: Push to GitHub

```bash
cd /workspaces/TKGAP
git init
git add .
git commit -m "Initial commit: Ichimoku Gap Scanner"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TKGAP.git
git push -u origin main
```

### Step 2: Deploy on Railway.app

1. **Visit** [railway.app](https://railway.app)
2. **Sign up** with GitHub
3. **Create New Project** → Select "Deploy from GitHub repo"
4. **Connect** your TKGAP repository
5. **Railway will auto-detect** Flask app
6. **Configure Environment:**
   - Go to Variables tab
   - Add: `FLASK_ENV=production`
   - Add: `PORT=5000` (Railway assigns this automatically)

7. **Deploy** - Railway will build and deploy automatically

### Step 3: Access Your App

After deployment, Railway will provide a public URL like:
```
https://tkgap-production.up.railway.app
```

---

## Alternative: Deploy on Render.com

### Step 1: Connect GitHub Repository

1. Visit [render.com](https://render.com)
2. Sign up with GitHub
3. Create New → Web Service
4. Select your TKGAP repository

### Step 2: Configure Service

- **Name**: `ichimoku-gap-scanner`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Region**: Choose closest to you
- **Plan**: Free tier (first 750 hours/month)

### Step 3: Deploy

- Click "Create Web Service"
- Render will build and deploy automatically
- URL provided: `https://ichimoku-gap-scanner.onrender.com`

---

## Alternative: PythonAnywhere (Free Tier)

### Step 1: Upload Code

1. Visit [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up free
3. Go to Files → Upload ZIP of project

### Step 2: Create Web App

1. Web → Add new web app
2. Python 3.10 → Flask
3. Point to `/workspaces/TKGAP/app.py`

### Step 3: Configure

1. Set virtual environment to use `requirements.txt`
2. Reload web app
3. Access via: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Comparison

| Platform | Free Tier | Ease | Auto-Deploy | Speed |
|----------|-----------|------|------------|-------|
| Railway.app | ✅ Yes | ⭐⭐⭐⭐⭐ | Yes | Fast |
| Render.com | ✅ Yes | ⭐⭐⭐⭐ | Yes | Good |
| PythonAnywhere | ✅ Yes | ⭐⭐⭐ | No | Fair |
| Heroku | ❌ No | ⭐⭐⭐⭐ | Yes | Fast |

---

## Post-Deployment Tips

### 1. Monitor Performance
- Check logs in Railway/Render dashboard
- Monitor API response times

### 2. Handle Rate Limits
- NSE API: Occasional rate limits (wait 5 min before retry)
- yfinance: Rate limits after ~2000 requests/day
- Consider caching results

### 3. Scale If Needed
- **Railway**: Upgrade to paid plan for more resources
- **Render**: Upgrade from free to paid
- **Custom**: Deploy on DigitalOcean ($12/mo droplet) or AWS

### 4. Custom Domain (Optional)
- Railway: Settings → Custom Domain
- Render: Environment → Custom Domains
- Cost: $0-12/year for domain

### 5. Environment Variables

For production, set these variables in deployment dashboard:
```
FLASK_ENV=production
PORT=5000 (auto-set by platform)
```

---

## Troubleshooting

**App crashes on startup?**
- Check logs in dashboard
- Ensure all dependencies in `requirements.txt`
- Verify Python version compatibility (3.8+)

**Slow scans?**
- Scans take 2-3 minutes (normal for 500 stocks)
- First request may be slower
- Consider adding result caching

**Rate limit errors?**
- Wait before re-running scan
- NSE API may throttle after many requests
- yfinance has daily limits

---

## Local Testing Before Deploy

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test at http://localhost:5000
```

---

## Rolling Back

If you need to revert a deployment:

**Railway**: Dashboard → Deploys → Select previous version → Rollback
**Render**: Dashboard → Deploys → Select previous version → Redeploy

---

## Cost Estimate

| Platform | Monthly Cost | Limits |
|----------|-------------|--------|
| Railway.app | Free | 5GB/month bandwidth, unlimited runs |
| Render | Free | 750 compute hours/month |
| PythonAnywhere | Free | 100MB disk, limited CPU |
| DigitalOcean | $12 | 1GB RAM, unlimited |

---

**Recommended**: Railway.app for easiest setup and best free tier features! 🚀


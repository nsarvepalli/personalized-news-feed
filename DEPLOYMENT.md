# 🚀 Deployment Guide

Deploy your Personalized News Feed to production!

---

## Option 1: Vercel (Backend)

### Step 1: Prepare Backend for Vercel

1. Create `vercel.json` in root directory:
```json
{
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": ".",
  "functions": {
    "backend/main.py": {
      "runtime": "python3.11"
    }
  },
  "env": {
    "OPENAI_API_KEY": "@openai_api_key",
    "NYT_API_KEY": "@nyt_api_key",
    "BLOOMBERG_ENABLED": "false",
    "DATABASE_URL": "@database_url"
  }
}
```

2. Install Vercel CLI:
```bash
npm install -g vercel
```

3. Deploy:
```bash
cd backend
vercel
```

4. Set environment variables in Vercel dashboard:
   - Settings → Environment Variables
   - Add: OPENAI_API_KEY, NYT_API_KEY, DATABASE_URL

5. Your backend will be at: `https://your-project.vercel.app`

---

## Option 2: Heroku (Backend)

### Step 1: Create Heroku App

```bash
# Install Heroku CLI
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-news-feed-app

# Add Python buildpack
heroku buildpacks:add heroku/python

# Set environment variables
heroku config:set OPENAI_API_KEY=your-key
heroku config:set NYT_API_KEY=your-key
heroku config:set DATABASE_URL=your-db-url
```

### Step 2: Deploy

```bash
# Push code
git push heroku main

# Check logs
heroku logs --tail
```

Your backend will be at: `https://your-news-feed-app.herokuapp.com`

---

## Option 3: Railway (Recommended)

### Step 1: Connect GitHub

1. Go to https://railway.app
2. Click "Deploy" → Connect GitHub
3. Select your repository
4. Railway will auto-detect Python project

### Step 2: Add Environment Variables

In Railway dashboard:
- Click "Variables"
- Add:
  - `OPENAI_API_KEY`
  - `NYT_API_KEY`
  - `BLOOMBERG_ENABLED=false`
  - `DATABASE_URL` (if using database)

### Step 3: Configure for FastAPI

Create `Procfile`:
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Your backend will be auto-deployed at: `https://your-project-*.railway.app`

---

## Option 4: Streamlit Cloud (Frontend)

### Step 1: Prepare Code

1. Create `.streamlit/config.toml`:
```toml
[client]
showErrorDetails = false

[server]
headless = true
enableXsrfProtection = true
```

2. Create `.streamlit/secrets.toml` locally (NOT committed):
```toml
backend_url = "https://your-backend-url.com"
```

### Step 2: Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "Deploy an app"
4. Select repository and branch
5. Set main file path: `frontend/app.py`
6. Click "Deploy"

Your frontend will be at: `https://your-username-your-app.streamlit.app`

---

## Option 5: Docker Deployment

### Create Dockerfile for Backend

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build
docker build -t news-feed-backend ./backend

# Run
docker run -e OPENAI_API_KEY=your-key -e NYT_API_KEY=your-key -p 8000:8000 news-feed-backend
```

### Deploy to Container Registry

```bash
# Build for container registry
docker tag news-feed-backend your-registry/news-feed-backend:latest

# Push
docker push your-registry/news-feed-backend:latest
```

Options:
- Docker Hub: https://hub.docker.com
- GitHub Container Registry: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- AWS ECR: https://docs.aws.amazon.com/ecr/

---

## Recommended Deployment Architecture

```
User Browser (Streamlit Cloud)
         ↓
    Streamlit Frontend
         ↓
    FastAPI Backend (Railway/Vercel/Heroku)
         ↓
    ├── OpenAI API
    ├── NYT API
    └── Supabase PostgreSQL (optional)
```

### Deployment Services Used:
- **Frontend**: Streamlit Cloud (free tier available)
- **Backend**: Railway (generous free tier) or Vercel
- **Database**: Supabase (free tier with PostgreSQL)
- **Secrets**: Use platform-specific secret management

---

## GitHub Actions for Auto-Deployment

Add to `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy backend to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway up --service backend --environment production
      
      # Streamlit Cloud auto-deploys on push to main
```

---

## Production Checklist

- [ ] Set strong environment variable values
- [ ] Enable HTTPS/SSL certificates
- [ ] Setup error monitoring (Sentry)
- [ ] Configure logging & alerts
- [ ] Setup database backups
- [ ] Enable rate limiting
- [ ] Add authentication layer
- [ ] Test all API endpoints
- [ ] Monitor performance metrics
- [ ] Setup uptime monitoring
- [ ] Create runbook for incident response
- [ ] Document deployment process

---

## Environment Variables for Production

```env
# FastAPI
OPENAI_API_KEY=sk-...
NYT_API_KEY=...
BLOOMBERG_ENABLED=false

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# App
DEBUG=False
APP_NAME=Personalized News Feed
ALLOWED_ORIGINS=https://your-frontend.streamlit.app
```

---

## Monitoring & Logging

### Add Sentry for Error Tracking

1. Create Sentry account: https://sentry.io
2. Create project (Python + FastAPI)
3. Install: `pip install sentry-sdk`
4. Add to `backend/main.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1
)
```

### Add Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## Cost Estimate (Monthly)

| Service | Free Tier | Paid |
|---------|-----------|------|
| Streamlit Cloud | Yes | $5+/mo |
| Railway | $5 credit | Pay-as-you-go |
| Vercel | Yes | $20/mo |
| Supabase | 500MB DB | $15+/mo |
| OpenAI API | No | ~$5-20/mo |
| **Total** | **~$5/mo** | **~$50+/mo** |

**Recommendation**: Start with free tier, scale as needed.

---

## Troubleshooting

### Backend won't deploy
- Check requirements.txt has all dependencies
- Verify Python version compatibility
- Check error logs in deployment dashboard

### Frontend can't reach backend
- Update `backend_url` in `.streamlit/secrets.toml`
- Ensure backend is running and accessible
- Check CORS configuration in FastAPI

### Scheduled jobs not running
- Verify GitHub Actions is enabled
- Check Actions tab for workflow status
- Review workflow logs for errors

---

## Rollback Procedure

### Railway
```bash
railway rollback -s backend
```

### Vercel
- Dashboard → Deployments → Click previous version → "Promote to Production"

### Streamlit Cloud
- App menu → Manage app → Restart → View logs

---

## Support Resources

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-cloud/
- Railway Docs: https://docs.railway.app/
- Vercel Docs: https://vercel.com/docs
- Supabase Docs: https://supabase.com/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

---

**Happy Deploying! 🚀**

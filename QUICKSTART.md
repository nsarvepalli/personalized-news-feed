# 🚀 Quick Start Guide

Get the Personalized News Feed running in 5 minutes!

## Prerequisites

- Python 3.10+
- OpenAI API key: https://platform.openai.com/api-keys
- NYT API key: https://developer.nytimes.com/docs/article-search-api/overview
- Optional: Bloomberg subscription (for Bloomberg articles)

## Step 1: Setup Environment

```bash
# Navigate to project directory
cd personalized-news-feed

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure `.env`

Copy `.env.example` to `.env` and add your actual API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
NYT_API_KEY=your-nyt-key-here
BLOOMBERG_ENABLED=false
DATABASE_URL=postgresql://... (optional)
```

## Step 3: Start Backend (Terminal 1)

```bash
cd backend
python main.py
```

✅ Backend will be running on **http://localhost:8000**

Check it's working: http://localhost:8000/docs (Swagger UI)

## Step 4: Start Frontend (Terminal 2)

```bash
# Make sure venv is activated
streamlit run frontend/app.py
```

✅ Frontend will be running on **http://localhost:8501**

## Step 5: Use the App

Open **http://localhost:8501** in your browser:

### 📰 Articles Tab
- View all fetched articles
- Filter by interests (business, AI, education, etc.)
- See relevance scores
- Click "Read Full" to open the original article

### ⚡ Quick Summary Tab
- One-minute digest of top 3 articles
- Curated summaries from your interests

### 📊 Stats Tab
- Article count by source
- Category breakdown
- Engagement metrics

---

## 🔧 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Fetch Articles
```bash
curl -X POST http://localhost:8000/fetch/articles?days_back=1
```

### Summarize Cached Articles
```bash
curl -X POST "http://localhost:8000/summarize/cached?interests=business,ai,upskilling"
```

### Get Cached Articles
```bash
curl http://localhost:8000/fetch/cached
```

---

## 📝 Features

✅ **Multi-source news aggregation** (NYT, Bloomberg, Washington Post)
✅ **AI-powered summarization** (OpenAI GPT-3.5-turbo)
✅ **Interest-based filtering** (business, education, AI, upskilling, etc.)
✅ **Relevance scoring** (0-1 scale based on your interests)
✅ **Beautiful Streamlit dashboard** with tabs and filtering
✅ **Real-time article fetching** from multiple sources
✅ **Scheduled digests** (GitHub Actions, morning & evening)

---

## 🐛 Troubleshooting

### Backend won't start
```
Error: "NEWS API key not configured"
→ Check .env has NYT_API_KEY set
```

### No articles showing
```
Error: "Cannot connect to backend"
→ Make sure backend on port 8000 is running
→ Check http://localhost:8000/health
```

### Summarizer failing
```
Error: "Summarizer not initialized"
→ Check OPENAI_API_KEY in .env is valid
→ Verify you have OpenAI credits
```

---

## 🎯 Next Steps

1. **Database Layer** (Optional)
   - Fix SQLAlchemy compatibility with Python 3.14
   - Implement persistent storage in Supabase

2. **Email Notifications**
   - Add SendGrid or AWS SES integration
   - Send digest emails to users

3. **Deployment**
   - Backend: Deploy to Vercel or Heroku
   - Frontend: Deploy to Streamlit Cloud

4. **Mobile App**
   - React Native frontend for iOS/Android

---

## 📚 Documentation

- [Full README](README.md) - Detailed feature documentation
- [API Docs](http://localhost:8000/docs) - Swagger UI (when backend running)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

## 💡 Tips

- **Change interests**: Modify selected interests in the sidebar
- **Fetch more days**: Slide "Days Back" to 2-7 days
- **Add custom interests**: Use "Custom Interests" field in sidebar
- **Test endpoints**: Use Swagger UI at http://localhost:8000/docs

---

**Enjoy your personalized news feed! 📰✨**

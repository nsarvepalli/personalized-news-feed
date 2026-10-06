# 📰 Personalized News Feed

An AI-powered news aggregator that fetches articles from multiple sources, automatically generates summaries, and presents them in a clean, user-friendly interface.

## Features

✅ **Multi-source aggregation** - Fetch news from NYT and Washington Post  
✅ **Auto-summarization** - AI-powered summaries (300 words) using OpenAI  
✅ **Custom interests** - Filter articles by predefined or custom interests  
✅ **Time range filtering** - Get news from last 1-7 days  
✅ **Professional UI** - Clean, minimal Streamlit interface  
✅ **Save & share** - Bookmark articles and share with others  

## Project Structure

```
personalized-news-feed/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── news_fetcher.py    # News source fetchers
│   │   ├── summarizer.py      # OpenAI summarization
│   │   └── filter.py          # Article filtering
│   ├── database_streamlit.py  # SQLite database layer
│   └── config.py              # Configuration
├── frontend/
│   └── app.py                 # Streamlit UI
├── .env.example               # Environment variables template
└── requirements.txt           # Python dependencies
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- NYT API key

### 1. Clone & Install Dependencies

```bash
git clone <your-repo-url>
cd personalized-news-feed
python -m venv venv
source venv/Scripts/activate  # On Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```
OPENAI_API_KEY=sk-...
NYT_API_KEY=...
DATABASE_URL=sqlite:///./news.db
```

### 3. Run Backend

```bash
cd backend
python main.py
```

Backend runs on `http://localhost:8001`

### 4. Run Frontend

```bash
streamlit run frontend/app.py --server.port=8888
```

Frontend opens at `http://localhost:8888`

## Usage

1. **Select Sources** - Choose NYT or Washington Post
2. **Add Interests** - Pick from predefined list or add custom interests
3. **Set Time Range** - Select articles from last 1-7 days
4. **Click Search** - Fetch and auto-summarize articles
5. **View Summaries** - Expand AI summaries for any article
6. **Save & Share** - Bookmark articles or share with others

## Technologies

- **Backend**: FastAPI, Uvicorn, SQLite
- **Frontend**: Streamlit
- **Summarization**: OpenAI GPT-3.5-turbo
- **News Sources**: NYT API, Washington Post RSS/Web scraping

## Author

Nithya Sarvepalli

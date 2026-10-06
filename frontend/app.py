import streamlit as st
import requests
from openai import OpenAI

st.set_page_config(
    page_title="News Feed",
    page_icon="📰",
    layout="wide"
)

# Minimal professional CSS with improved colors
st.markdown("""
<style>
    header {display: none;}
    footer {display: none;}
    .viewerBadge_container__1QSob {display: none;}

    /* Improved color scheme */
    .stApp {
        background-color: #f8fafb;
    }

    .stTitle {
        color: #1a202c;
    }

    .stSubheader {
        color: #2d3748;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #cbd5e0;
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 600;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background-color: #f7fafc;
        border-color: #2d3748;
        color: #1a202c;
    }

    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #cbd5e0;
    }

    /* Multiselect styling */
    [data-baseweb="select"] > div {
        border-radius: 6px;
        border: 1px solid #cbd5e0;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f7fafc;
        border-radius: 6px;
    }

    /* Divider */
    .stDivider {
        border-color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize state
if 'articles_data' not in st.session_state:
    st.session_state.articles_data = None
if 'article_summaries' not in st.session_state:
    st.session_state.article_summaries = {}

# Function to generate summaries
def generate_summaries():
    if not st.session_state.articles_data:
        return

    articles = st.session_state.articles_data.get("articles", [])
    client = OpenAI()
    progress_bar = st.progress(0)

    for idx, article in enumerate(articles):
        article_key = f"{idx}_{article['url']}"

        if article_key not in st.session_state.article_summaries:
            try:
                title = article["title"]
                content = article.get("description", article.get("content", ""))

                prompt = f"""Summarize in 300 words or less. Be objective and factual.

Title: {title}
Content: {content}

Summary:"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.3
                )

                st.session_state.article_summaries[article_key] = response.choices[0].message.content
            except:
                pass

        progress_bar.progress((idx + 1) / len(articles))

    progress_bar.empty()

# SIDEBAR
with st.sidebar:
    st.title("📰 News Feed")
    st.divider()

    backend_url = st.text_input("🔗 Backend URL", "http://localhost:8001")

    st.subheader("📌 Sources")
    sources = st.multiselect(
        "Select news sources",
        ["NYT", "Washington Post"],
        default=[]
    )
    sources_str = ",".join([s.lower() for s in sources])

    st.subheader("💡 Interests")
    interests_list = ["business", "ai", "technology", "education", "career", "finance", "startups", "health", "science"]
    selected_interests = st.multiselect(
        "Select your interests",
        interests_list,
        default=[]
    )

    custom_interests_input = st.text_input(
        "✏️ Add custom interests",
        placeholder="climate change, sports, politics"
    )

    st.subheader("⏰ Time Range")
    days_back = st.slider("Last how many days?", 1, 7, 3)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        search_btn = st.button("🔍 Search", use_container_width=True)
    with col2:
        clear_btn = st.button("✕ Clear", use_container_width=True)

    if clear_btn:
        st.session_state.articles_data = None
        st.session_state.article_summaries = {}
        st.rerun()

# MAIN CONTENT
st.header("📰 News Feed", divider="blue")

# Combine predefined and custom interests
final_interests = selected_interests.copy()
if custom_interests_input:
    custom_list = [i.strip().lower() for i in custom_interests_input.split(",") if i.strip()]
    final_interests.extend(custom_list)

interests_str = ",".join(final_interests) if final_interests else ""

if search_btn:
    if not sources_str:
        st.warning("⚠️ Please select at least one news source")
    elif not final_interests:
        st.warning("⚠️ Please select at least one interest")
    else:
        try:
            with st.spinner("⏳ Fetching articles..."):
                response = requests.post(
                    f"{backend_url}/fetch/articles",
                    params={
                        "days_back": days_back,
                        "sources": sources_str,
                        "interests": interests_str
                    },
                    timeout=120
                )

            if response.status_code == 200:
                st.session_state.articles_data = response.json()
                st.session_state.article_summaries = {}
                articles_count = response.json().get('total_articles', 0)
                st.success(f"✅ Found {articles_count} articles. Generating summaries...")

                # Auto-generate summaries
                generate_summaries()
                st.success("✨ All articles summarized!")
            else:
                st.error(f"❌ Error: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display articles
if st.session_state.articles_data:
    articles = st.session_state.articles_data.get("articles", [])

    if articles:
        st.markdown(f"### **📊 {len(articles)} Articles Found**")
        st.divider()

        for idx, article in enumerate(articles):
            article_key = f"{idx}_{article['url']}"

            with st.container(border=True):
                # Source badge with better styling
                source = article.get("source", "").lower()
                if "washington" in source:
                    source_badge = "🔴 Washington Post"
                    badge_color = "#c53030"
                else:
                    source_badge = "🟡 NYT"
                    badge_color = "#d69e2e"

                st.markdown(f"<span style='color: {badge_color}; font-weight: bold; font-size: 0.9rem;'>{source_badge}</span>", unsafe_allow_html=True)

                # Full title from publisher (no truncation)
                st.subheader(article["title"], divider="gray")

                # Meta info with better icons
                published = article.get("published_at", "").split("T")[0] if article.get("published_at") else "N/A"
                category = article.get("category", "N/A")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.caption(f"📅 Published: {published}")
                with col2:
                    st.caption(f"📂 Category: {category}")

                # Description
                desc = article.get("description", article.get("content", ""))
                if desc:
                    st.write(desc)

                # Summary (always show if available)
                if article_key in st.session_state.article_summaries:
                    with st.expander("📝 AI Summary", expanded=True):
                        st.markdown(f"<div style='background-color: #f7fafc; padding: 1rem; border-radius: 6px; border-left: 4px solid #2d3748; line-height: 1.6;'>{st.session_state.article_summaries[article_key]}</div>", unsafe_allow_html=True)

                # Action buttons - improved
                st.divider()
                col1, col2, col3 = st.columns(3, gap="small")

                with col1:
                    st.link_button("🌐 Read Full Article", article["url"], use_container_width=True)

                with col2:
                    if st.button("💾 Save Article", key=f"save_{idx}", use_container_width=True):
                        try:
                            save_response = requests.post(
                                f"{backend_url}/articles/save",
                                params={
                                    "url": article["url"],
                                    "title": article["title"],
                                    "source": article.get("source", ""),
                                    "category": article.get("category", ""),
                                    "summary": st.session_state.article_summaries.get(article_key, "")
                                }
                            )
                            if save_response.status_code == 200:
                                st.success("✅ Article saved to your collection!")
                            else:
                                st.error("Failed to save article")
                        except Exception as e:
                            st.error(f"Error saving article: {str(e)}")

                with col3:
                    if st.button("📤 Share", key=f"share_{idx}", use_container_width=True):
                        st.info("📋 Ready to share!")
    else:
        st.info("ℹ️ No articles found with your filters")
else:
    if st.session_state.articles_data is None:
        st.info("👈 Select sources, interests, and click Search to get started")

# Saved Articles Section
st.divider()
st.markdown("### 💾 Your Saved Articles")

try:
    saved_response = requests.get(f"{backend_url}/articles/saved")
    if saved_response.status_code == 200:
        saved_data = saved_response.json()
        saved_articles = saved_data.get("articles", [])

        if saved_articles:
            st.markdown(f"**{len(saved_articles)} Saved Article(s)**")
            st.divider()

            for idx, article in enumerate(saved_articles):
                with st.container(border=True):
                    source = article.get("source", "").lower()
                    if "washington" in source:
                        source_badge = "🔴 Washington Post"
                    else:
                        source_badge = "🟡 NYT"

                    st.markdown(f"<span style='color: #2d3748; font-weight: bold;'>{source_badge}</span>", unsafe_allow_html=True)
                    st.subheader(article["title"], divider="gray")

                    published = article.get("published_at", "N/A")
                    st.caption(f"📅 {published}")

                    st.write(article.get("description", ""))

                    col1, col2, col3 = st.columns(3, gap="small")
                    with col1:
                        st.link_button("🌐 Read Full Article", article["url"], use_container_width=True)
                    with col2:
                        if st.button("🗑️ Remove", key=f"delete_{idx}", use_container_width=True):
                            try:
                                delete_response = requests.delete(
                                    f"{backend_url}/articles/save",
                                    params={"url": article["url"]}
                                )
                                if delete_response.status_code == 200:
                                    st.success("✅ Removed from saved!")
                                    st.rerun()
                            except:
                                st.error("Error removing article")
                    with col3:
                        if st.button("📤 Share", key=f"share_saved_{idx}", use_container_width=True):
                            st.info("📋 Ready to share!")
        else:
            st.info("No saved articles yet. Save articles from the search results above!")
    else:
        st.info("No saved articles yet.")
except:
    st.info("No saved articles yet.")

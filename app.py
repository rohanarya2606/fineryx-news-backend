from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import feedparser
from transformers import pipeline
import asyncio

app = FastAPI()

# Allow your website to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize summarizer
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# RSS feeds
FEEDS = {
    "Global": [
        "https://www.reuters.com/finance/rss",
        "https://www.bloomberg.com/feed/podcast/etf-report.xml"
    ],
    "India": [
        "https://economictimes.indiatimes.com/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/latestnews.xml"
    ]
}

def short_summary(text, max_sentences=2):
    try:
        result = summarizer(text, max_length=60, min_length=20, do_sample=False)
        return result[0]['summary_text']
    except:
        return text[:120] + "..."

async def fetch_feed(category, url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:5]:  # top 5 articles per feed
        title = entry.title
        link = entry.link
        summary_text = entry.get("summary", entry.get("description", ""))
        summary = short_summary(summary_text)
        articles.append({
            "title": title,
            "link": link,
            "summary": summary,
            "category": category,
            "pubDate": entry.get("published", "")
        })
    return articles

@app.get("/news")
async def get_news():
    tasks = []
    for cat, urls in FEEDS.items():
        for url in urls:
            tasks.append(fetch_feed(cat, url))
    results = await asyncio.gather(*tasks)
    # Flatten list of lists
    news_list = [item for sublist in results for item in sublist]
    # Sort by pubDate if exists
    news_list.sort(key=lambda x: x.get("pubDate", ""), reverse=True)
    return news_list

"""經濟日報 money.udn.com 新聞爬蟲 — 透過 RSS Feed + 內頁解析。"""
from __future__ import annotations

import time
from typing import Iterable

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

FEEDS = {
    "國際焦點": "https://money.udn.com/rssfeed/news/1001/5588/9286",
    "國際綜合": "https://money.udn.com/rssfeed/news/1001/5588/11091",
    "美股雷達": "https://money.udn.com/rssfeed/news/1001/5599/11074",
    "全球財經": "https://money.udn.com/rssfeed/news/1001/5588",
    "要聞": "https://money.udn.com/rssfeed/news/1001/5589/5591",
}


def _parse_article(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        body = soup.select_one("section.article-body__editor") or soup.select_one(
            "div#article_body"
        )
        if not body:
            return ""
        return "\n".join(p.get_text(strip=True) for p in body.select("p"))
    except Exception:
        return ""


def fetch(
    feeds: Iterable[str] | None = None, limit_per_feed: int = 10, fetch_body: bool = False
) -> list[dict]:
    """抓取 UDN 經濟日報新聞。"""
    chosen = {k: FEEDS[k] for k in feeds} if feeds else FEEDS
    out: list[dict] = []
    for name, url in chosen.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit_per_feed]:
                item = {
                    "source": "udn",
                    "category": name,
                    "title": entry.get("title"),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link"),
                    "published_at": entry.get("published", ""),
                }
                if fetch_body:
                    item["body"] = _parse_article(entry.link)
                    time.sleep(1)
                out.append(item)
        except Exception as e:
            print(f"[udn] {name} 抓取失敗: {e}")
    return out


if __name__ == "__main__":
    for n in fetch(limit_per_feed=3):
        print(n["published_at"], n["category"], n["title"])
        print("  ", n["url"])

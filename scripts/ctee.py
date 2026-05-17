"""工商時報 ctee.com.tw 新聞爬蟲 — 靜態 HTML 解析。"""
from __future__ import annotations

import time
from typing import Iterable

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

CATEGORIES = {
    "即時新聞": "https://www.ctee.com.tw/livenews",
    "國際財經": "https://www.ctee.com.tw/category/news/global",
    "美股": "https://www.ctee.com.tw/tag/美股",
    "日股": "https://www.ctee.com.tw/tag/日股",
    "外匯": "https://www.ctee.com.tw/category/news/global/gforex",
}


def _parse_list(url: str, limit: int) -> list[dict]:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    items: list[dict] = []
    # 工商時報版型有多種，這裡列出常見 selector 作 fallback
    anchors = (
        soup.select("h3.post-title a")
        or soup.select("article.post h3 a")
        or soup.select("div.article-box a.title")
    )
    for a in anchors[:limit]:
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if href and title:
            items.append({"title": title, "url": href})
    return items


def fetch(
    categories: Iterable[str] | None = None, limit_per_cat: int = 15
) -> list[dict]:
    """抓取工商時報新聞列表（不含內文，避免請求過多）。"""
    chosen = {k: CATEGORIES[k] for k in categories} if categories else CATEGORIES
    out: list[dict] = []
    for name, url in chosen.items():
        try:
            for item in _parse_list(url, limit_per_cat):
                out.append(
                    {
                        "source": "ctee",
                        "category": name,
                        "title": item["title"],
                        "url": item["url"],
                        "summary": "",
                        "published_at": "",
                    }
                )
        except Exception as e:
            print(f"[ctee] {name} 抓取失敗: {e}")
        time.sleep(1)
    return out


if __name__ == "__main__":
    for n in fetch(limit_per_cat=5):
        print(n["category"], n["title"])
        print("  ", n["url"])

"""多家媒體 RSS 通用爬蟲 — 中央社、自由財經、科技新報、ETtoday、中時、MoneyDJ、Yahoo股市。

新增來源只需在 SOURCES 註冊 feed URL，輸出欄位與 cnyes/udn/ctee 一致。
各來源驗證狀態見 skills/get-stock-NEWS/SKILL.md 的來源清單。
"""
from __future__ import annotations

import time
from typing import Iterable

import feedparser

try:
    from .common import (
        UA, extract_author_from_entry, fetch_article, request_get, to_taipei_iso,
    )
except ImportError:
    from common import (
        UA, extract_author_from_entry, fetch_article, request_get, to_taipei_iso,
    )

# source_id -> {label, feeds: {分類: feed_url}}
SOURCES: dict[str, dict] = {
    "cna": {
        "label": "中央社",
        "feeds": {
            "財經": "https://feeds.feedburner.com/rsscna/finance",
        },
    },
    "ltn": {
        "label": "自由財經",
        "feeds": {
            "財經": "https://news.ltn.com.tw/rss/business.xml",
        },
    },
    "technews": {
        "label": "科技新報",
        # 唯一非財經分類的來源（科技媒體全站 feed），會混入科普文；
        # 本機驗證時優先試 /category/{財經 slug}/feed/ 分類 feed，可用就替換
        "feeds": {
            "全站": "https://technews.tw/feed/",
        },
    },
    "ettoday": {
        "label": "ETtoday財經",
        "feeds": {
            "財經": "https://feeds.feedburner.com/ettoday/finance",
        },
    },
    "chinatimes": {
        "label": "中時新聞網",
        "feeds": {
            "財經即時": "https://www.chinatimes.com/rss/realtimenews-finance.xml",
        },
    },
    "moneydj": {
        "label": "MoneyDJ理財網",
        "feeds": {
            "頭條新聞": "https://www.moneydj.com/KMDJ/RssCenter.aspx?svc=NR&fno=1&arg=X0",
        },
    },
    "yahoo_stock": {
        "label": "Yahoo奇摩股市",
        "feeds": {
            "台股": "https://tw.stock.yahoo.com/rss?category=tw-market",
            "國際股市": "https://tw.stock.yahoo.com/rss?category=intl-markets",
        },
    },
}


def _norm_time(entry) -> str:
    return to_taipei_iso(entry.get("published") or entry.get("updated"))


def fetch_source(source_id: str, limit_per_feed: int = 15,
                 fetch_content: bool = False) -> list[dict]:
    """抓取單一 RSS 來源，回傳標準化欄位。

    fetch_content=True 時，逐篇進內頁抓全文（多一個 request/篇，較慢，禮貌性 sleep）；
    RSS 只給摘要，全文一律需內頁抽取。內文容器選擇器取自 SOURCES[sid]['body_selectors']。
    """
    conf = SOURCES[source_id]
    selectors = conf.get("body_selectors")
    out: list[dict] = []
    for name, url in conf["feeds"].items():
        try:
            resp = request_get(url, headers={"User-Agent": UA})
            feed = feedparser.parse(resp.content)
            if feed.bozo and not feed.entries:
                raise RuntimeError(f"feed 解析失敗: {feed.bozo_exception}")
            for entry in feed.entries[:limit_per_feed]:
                link = entry.get("link")
                rec = {
                    "source": source_id,
                    "category": name,
                    "title": entry.get("title"),
                    "author": extract_author_from_entry(entry),
                    "summary": entry.get("summary", ""),
                    "content": "",
                    "url": link,
                    "published_at": _norm_time(entry),
                }
                if fetch_content and link:
                    art = fetch_article(link, body_selectors=selectors)
                    rec["content"] = art["content"]
                    if not rec["author"]:
                        rec["author"] = art["author"]
                    if not rec["summary"]:
                        rec["summary"] = art["summary"]
                    time.sleep(1)
                out.append(rec)
        except Exception as e:
            print(f"[{source_id}] {name} 抓取失敗: {e}")
        time.sleep(1)
    return out


def fetch(sources: Iterable[str] | None = None, limit_per_feed: int = 15,
          fetch_content: bool = False) -> list[dict]:
    """抓取多個 RSS 來源；sources=None 時抓全部已註冊來源。"""
    chosen = list(sources) if sources else list(SOURCES.keys())
    out: list[dict] = []
    for sid in chosen:
        if sid not in SOURCES:
            print(f"[rss_sources] 未註冊的來源: {sid}（可用: {', '.join(SOURCES)}）")
            continue
        out.extend(fetch_source(sid, limit_per_feed, fetch_content=fetch_content))
    return out


if __name__ == "__main__":
    import sys

    chosen = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    for n in fetch(chosen, limit_per_feed=3):
        print(n["published_at"], f"[{n['source']}]", n["category"], n["title"])
        print("  ", n["url"])

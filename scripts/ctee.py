"""工商時報 ctee.com.tw 新聞爬蟲 — 靜態列表頁解析。

工商無公開 RSS，WP REST API 亦已關閉（/wp-json 回 404，見 backfill_ctee.py），
故走列表頁擷取文章 URL。發布日期可直接從 URL 內嵌的 8 碼取得
（/news/{YYYYMMDD}{6}-{6}），免額外請求即可得到日粒度 publish_ts；
需要精確到分秒時，fetch_detail=True 會再抓文章頁的 <meta pubdate>
（每篇一次請求，預設關閉以保持禮貌）。

文章解析重用 backfill_ctee 的 parse_article / _publish_str_to_iso，
即時與歷史回補共用同一套解析邏輯。
"""
from __future__ import annotations

import time
from typing import Iterable

from bs4 import BeautifulSoup

try:
    from .common import request_get, to_taipei_iso
    from .backfill_ctee import URL_DATE_RE, parse_article, _publish_str_to_iso
except ImportError:
    from common import request_get, to_taipei_iso
    from backfill_ctee import URL_DATE_RE, parse_article, _publish_str_to_iso

HEADERS = {"User-Agent": "Mozilla/5.0"}

CATEGORIES = {
    "即時新聞": "https://www.ctee.com.tw/livenews",
    "國際財經": "https://www.ctee.com.tw/category/news/global",
    "美股": "https://www.ctee.com.tw/tag/美股",
    "日股": "https://www.ctee.com.tw/tag/日股",
    "外匯": "https://www.ctee.com.tw/category/news/global/gforex",
}


def _url_date_iso(url: str) -> str:
    """從文章 URL 內嵌的 8 碼日期取台北時間 ISO（日粒度）；無法解析回空字串。"""
    m = URL_DATE_RE.search(url)
    if not m:
        return ""
    ymd = m.group(1)
    return to_taipei_iso(f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}")


def _detail_publish_iso(url: str) -> str:
    """抓文章頁取精確發布時間（台北 ISO）；失敗回空字串。"""
    try:
        resp = request_get(url, headers=HEADERS)
        iso = _publish_str_to_iso(parse_article(resp.text).get("publish_str", ""))
        return to_taipei_iso(iso) if iso else ""
    except Exception:
        return ""


def _parse_list(url: str, limit: int) -> list[dict]:
    resp = request_get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "lxml")

    # 工商時報版型有多種，列出常見 selector 作 fallback（selectors 待本機驗證）
    anchors = (
        soup.select("h3.post-title a")
        or soup.select("article.post h3 a")
        or soup.select("div.article-box a.title")
    )
    items: list[dict] = []
    for a in anchors[:limit]:
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if href and title:
            items.append({"title": title, "url": href})
    return items


def fetch(
    categories: Iterable[str] | None = None,
    limit_per_cat: int = 15,
    fetch_detail: bool = False,
) -> list[dict]:
    """抓取工商時報新聞列表。publish_ts 來自 URL 日期；fetch_detail 取精確時間。"""
    chosen = {k: CATEGORIES[k] for k in categories} if categories else CATEGORIES
    out: list[dict] = []
    for name, url in chosen.items():
        try:
            for item in _parse_list(url, limit_per_cat):
                pub = _url_date_iso(item["url"])
                if fetch_detail:
                    precise = _detail_publish_iso(item["url"])
                    if precise:
                        pub = precise
                    time.sleep(1)
                out.append(
                    {
                        "source": "ctee",
                        "category": name,
                        "title": item["title"],
                        "url": item["url"],
                        "summary": "",
                        "published_at": pub,
                    }
                )
        except Exception as e:
            print(f"[ctee] {name} 抓取失敗: {e}")
        time.sleep(1)
    return out


if __name__ == "__main__":
    for n in fetch(limit_per_cat=5):
        print(n["published_at"], n["category"], n["title"])
        print("  ", n["url"])

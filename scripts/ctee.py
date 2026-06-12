"""工商時報 ctee.com.tw 新聞爬蟲 — WP REST API 優先，靜態 HTML fallback。

WP REST API（/wp-json/wp/v2/posts）可拿到準確發布時間（PIT 必要），
端點待本機驗證；不可用時自動退回 HTML 列表解析（無時間戳）。
"""
from __future__ import annotations

import re
import time
from typing import Iterable

from bs4 import BeautifulSoup

try:
    from .common import request_get, to_taipei_iso
except ImportError:
    from common import request_get, to_taipei_iso

HEADERS = {"User-Agent": "Mozilla/5.0"}

WP_API = "https://www.ctee.com.tw/wp-json/wp/v2/posts"

CATEGORIES = {
    "即時新聞": "https://www.ctee.com.tw/livenews",
    "國際財經": "https://www.ctee.com.tw/category/news/global",
    "美股": "https://www.ctee.com.tw/tag/美股",
    "日股": "https://www.ctee.com.tw/tag/日股",
    "外匯": "https://www.ctee.com.tw/category/news/global/gforex",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


def _fetch_wp(limit: int) -> list[dict]:
    """WP REST API：最新文章（全站），含準確發布時間。"""
    resp = request_get(
        WP_API,
        params={"per_page": min(limit, 100), "orderby": "date", "order": "desc"},
        headers=HEADERS,
    )
    out: list[dict] = []
    for post in resp.json():
        title = _strip_html((post.get("title") or {}).get("rendered", ""))
        if not title:
            continue
        out.append(
            {
                "source": "ctee",
                "category": "最新文章",
                "title": title,
                "summary": _strip_html((post.get("excerpt") or {}).get("rendered", "")),
                "url": post.get("link", ""),
                # WP date 為站台本地時間（台北）
                "published_at": to_taipei_iso(post.get("date", "")),
            }
        )
    return out


def _parse_list(url: str, limit: int) -> list[dict]:
    resp = request_get(url, headers=HEADERS)
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


def _fetch_html(
    categories: Iterable[str] | None = None, limit_per_cat: int = 15
) -> list[dict]:
    """HTML 列表 fallback（不含內文與時間戳）。"""
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


def fetch(
    categories: Iterable[str] | None = None, limit_per_cat: int = 15
) -> list[dict]:
    """抓取工商時報新聞。WP REST API 優先（有時間戳），失敗退回 HTML。"""
    try:
        items = _fetch_wp(limit_per_cat * 3)
        if items:
            return items
    except Exception as e:
        print(f"[ctee] WP API 失敗，退回 HTML: {e}")
    return _fetch_html(categories, limit_per_cat)


if __name__ == "__main__":
    for n in fetch(limit_per_cat=5):
        print(n["published_at"], n["category"], n["title"])
        print("  ", n["url"])

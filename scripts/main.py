"""Finance-NEWS 統一彙整入口 — 抓最新並寫入 data/raw/（依來源、日期分檔）。"""
from __future__ import annotations

from datetime import datetime

try:
    from .cnyes import fetch as fetch_cnyes
    from .ctee import fetch as fetch_ctee
    from .udn import fetch as fetch_udn
    from .rss_sources import fetch as fetch_rss
    from .common import TAIPEI, norm_title
    from . import storage
except ImportError:  # 直接以 python scripts/main.py 執行
    from cnyes import fetch as fetch_cnyes
    from ctee import fetch as fetch_ctee
    from udn import fetch as fetch_udn
    from rss_sources import fetch as fetch_rss
    from common import TAIPEI, norm_title
    import storage


def aggregate() -> list[dict]:
    news: list[dict] = []
    print("[cnyes] 抓取中...")
    news.extend(fetch_cnyes(limit=15))
    print("[udn] 抓取中...")
    news.extend(fetch_udn(limit_per_feed=10))
    print("[ctee] 抓取中...")
    news.extend(fetch_ctee(limit_per_cat=10))
    print("[rss] 中央社/自由/科技新報/ETtoday/中時/MoneyDJ/Yahoo股市 抓取中...")
    news.extend(fetch_rss(limit_per_feed=10))

    # 以 url + 正規化標題去重（跨來源轉載 URL 不同、標題相同）
    seen: set[str] = set()
    deduped: list[dict] = []
    for n in news:
        url = n.get("url") or ""
        tkey = norm_title(n.get("title") or "")
        if not url or url in seen or (tkey and tkey in seen):
            continue
        seen.add(url)
        if tkey:
            seen.add(tkey)
        deduped.append(n)
    return deduped


if __name__ == "__main__":
    items = aggregate()
    print(f"\n總共 {len(items)} 則新聞")

    # 依來源寫入 raw 層，供日終 process_day.py 轉 processed parquet
    date = datetime.now(TAIPEI).strftime("%Y-%m-%d")
    by_source: dict[str, list[dict]] = {}
    for n in items:
        by_source.setdefault(n.get("source", "unknown"), []).append(n)
    for src, lst in by_source.items():
        merged = {  # 與當日既有 raw 合併（同日多次執行不互相覆蓋）
            f"{i.get('url', '')}|{i.get('title', '')}": i
            for i in storage.load_raw(src, date) + lst
        }
        path = storage.save_raw(src, date, list(merged.values()))
        print(f"  [{src}] {len(lst)} 則 -> {path}")

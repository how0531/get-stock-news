"""Finance-NEWS 統一彙整入口。"""
from __future__ import annotations

import json
from datetime import datetime

try:
    from .cnyes import fetch as fetch_cnyes
    from .ctee import fetch as fetch_ctee
    from .udn import fetch as fetch_udn
    from .rss_sources import fetch as fetch_rss
except ImportError:  # 直接以 python scripts/main.py 執行
    from cnyes import fetch as fetch_cnyes
    from ctee import fetch as fetch_ctee
    from udn import fetch as fetch_udn
    from rss_sources import fetch as fetch_rss


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

    # 以 url 去重
    seen: set[str] = set()
    deduped: list[dict] = []
    for n in news:
        url = n.get("url")
        if url and url not in seen:
            seen.add(url)
            deduped.append(n)
    return deduped


if __name__ == "__main__":
    items = aggregate()
    print(f"\n總共 {len(items)} 則新聞")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"news_{stamp}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"已寫入 {out_file}")

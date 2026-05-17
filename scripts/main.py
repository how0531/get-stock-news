"""Finance-NEWS 統一彙整入口。"""
from __future__ import annotations

import json
from datetime import datetime

from scrapers import fetch_cnyes, fetch_ctee, fetch_udn


def aggregate() -> list[dict]:
    news: list[dict] = []
    print("[cnyes] 抓取中...")
    news.extend(fetch_cnyes(limit=15))
    print("[udn] 抓取中...")
    news.extend(fetch_udn(limit_per_feed=10))
    print("[ctee] 抓取中...")
    news.extend(fetch_ctee(limit_per_cat=10))

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

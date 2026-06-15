"""快速版熱度計算 — 用於 sanity check
v2 完整模型尚未實作，此版只做：標題 ×2 + 摘要 ×1 + 過濾雜訊
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# repo 根：本檔在 skills/stock-heat-model/scripts/ 下，往上三層
ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "cnyes"  # 消費 get-stock-NEWS 產出的 raw
STOCKS_DIR = ROOT / "data" / "stocks"

# 雜訊標題 prefix（不算熱度）
NOISE_PREFIXES = ("盤中速報", "鉅亨速報 - Factset", "鉅亨速報 - 集中市場", "鉅亨速報 - 上櫃")


def load_stocks() -> dict[str, dict]:
    """讀三市場字典，回傳 {ticker: info}"""
    out: dict[str, dict] = {}
    for f in ["tw_stocks.json", "us_stocks.json", "jp_stocks.json"]:
        with open(STOCKS_DIR / f, encoding="utf-8") as fp:
            out.update(json.load(fp))
    return out


def build_alias_index(stocks: dict[str, dict]) -> list[tuple[str, str]]:
    """回傳 [(alias, ticker)]，依別名長度倒序（先匹配長的避免 partial match）"""
    pairs: list[tuple[str, str]] = []
    for ticker, info in stocks.items():
        for alias in info.get("aliases", []):
            # 過濾太短的別名避免誤觸（單字、單字母）
            if len(alias) < 2:
                continue
            pairs.append((alias, ticker))
    # 長別名先比對
    pairs.sort(key=lambda x: -len(x[0]))
    return pairs


def is_noise(title: str) -> bool:
    return any(title.startswith(p) for p in NOISE_PREFIXES)


def count_mentions(text: str, alias: str) -> int:
    if not text:
        return 0
    # 數字代號要邊界（避免 2330 命中 23300）
    if alias.isdigit():
        return len(re.findall(rf"(?<!\d){re.escape(alias)}(?!\d)", text))
    # 英文 ticker 要詞邊界
    if re.match(r"^[A-Z]+(-US|\.T)?$", alias):
        return len(re.findall(rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z0-9])", text))
    # 中文/其他直接 substring
    return text.count(alias)


def score_article(article: dict, alias_pairs: list[tuple[str, str]]) -> dict[str, dict]:
    """回傳 {ticker: {score, in_title, hits}}"""
    title = article.get("title", "") or ""
    summary = article.get("summary", "") or ""

    if is_noise(title):
        return {}

    matched: dict[str, dict] = {}
    seen_aliases_for_ticker: dict[str, set] = defaultdict(set)

    for alias, ticker in alias_pairs:
        if alias in seen_aliases_for_ticker[ticker]:
            continue
        t_cnt = count_mentions(title, alias)
        s_cnt = count_mentions(summary, alias)
        if t_cnt + s_cnt == 0:
            continue
        seen_aliases_for_ticker[ticker].add(alias)
        if ticker not in matched:
            matched[ticker] = {"score": 0, "in_title": False, "title_hits": 0, "summary_hits": 0}
        matched[ticker]["score"] += t_cnt * 2 + s_cnt * 1
        matched[ticker]["title_hits"] += t_cnt
        matched[ticker]["summary_hits"] += s_cnt
        if t_cnt > 0:
            matched[ticker]["in_title"] = True
    return matched


def heat_for_day(date_str: str, alias_pairs, stocks) -> list[tuple]:
    f = RAW / f"{date_str}.json"
    if not f.exists():
        print(f"  ⚠ {date_str}: 無資料")
        return []
    articles = json.load(open(f, encoding="utf-8"))
    agg: dict[str, dict] = defaultdict(lambda: {
        "score": 0, "title_hits": 0, "summary_hits": 0,
        "article_count": 0, "headlines": []
    })
    noise_count = 0
    for a in articles:
        if is_noise(a.get("title", "")):
            noise_count += 1
            continue
        scores = score_article(a, alias_pairs)
        for ticker, s in scores.items():
            agg[ticker]["score"] += s["score"]
            agg[ticker]["title_hits"] += s["title_hits"]
            agg[ticker]["summary_hits"] += s["summary_hits"]
            agg[ticker]["article_count"] += 1
            if s["in_title"] and len(agg[ticker]["headlines"]) < 3:
                agg[ticker]["headlines"].append(a["title"])
    ranked = sorted(agg.items(), key=lambda x: -x[1]["score"])
    return ranked, len(articles), noise_count


def main():
    stocks = load_stocks()
    alias_pairs = build_alias_index(stocks)
    print(f"載入 {len(stocks)} 檔個股、{len(alias_pairs)} 條別名\n")

    dates = sys.argv[1:] if len(sys.argv) > 1 else ["2026-05-13", "2026-05-14", "2026-05-15"]
    TOP_N = 20

    for date in dates:
        print(f"\n{'='*70}")
        print(f"📅 {date} — 熱度排名 Top {TOP_N}（依市場分組）")
        print(f"{'='*70}")
        result = heat_for_day(date, alias_pairs, stocks)
        if not result:
            continue
        ranked, total, noise = result
        print(f"當日 {total} 則新聞（過濾 {noise} 則雜訊），命中 {len(ranked)} 檔個股\n")

        # 依市場分組
        by_market: dict[str, list] = {"TW": [], "US": [], "JP": []}
        for ticker, info in ranked:
            mkt = stocks[ticker].get("market", "?")
            if mkt in by_market:
                by_market[mkt].append((ticker, info))

        market_titles = {
            "TW": "🇹🇼 台股 Top",
            "US": "🇺🇸 美股 Top",
            "JP": "🇯🇵 日股 Top",
        }
        for mkt, items in by_market.items():
            if not items:
                continue
            print(f"\n  {market_titles[mkt]} {min(TOP_N, len(items))} —")
            for i, (ticker, info) in enumerate(items[:TOP_N], 1):
                s = stocks[ticker]
                name = s.get("name_zh") or s.get("name_en") or ticker
                print(f"    {i:2d}. {name:14s} ({ticker:10s}) "
                      f"score={info['score']:3d}  "
                      f"T{info['title_hits']}/S{info['summary_hits']}/"
                      f"{info['article_count']}篇")
                for h in info["headlines"][:1]:
                    print(f"          · {h[:60]}")


if __name__ == "__main__":
    main()

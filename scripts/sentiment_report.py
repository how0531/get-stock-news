"""新聞利多/利空監測報告 — 彙總當日新聞情緒到個股層級。

消費 process_day 同一套資料路徑（raw + stream，含兩層去重），
對每則新聞套用 sentiment.classify_news，彙總出個股利多/利空榜，
輸出 console 報告 + data/sentiment/{date}.json（供下游推播/報告使用）。

盤中即時監測請直接跑 watch_intraday.py——事件串流每筆已帶 sentiment 欄位，
本工具是「日終/盤前總結」視角。

用法：
  python scripts/sentiment_report.py                    # 今天（台北時間）
  python scripts/sentiment_report.py 2026-07-03         # 指定日期
  python scripts/sentiment_report.py --top 15           # 榜單長度
  python scripts/sentiment_report.py --tickers 2330,2454  # 只看自選股
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

try:
    from .common import TAIPEI
    from .process_day import build_records, load_day_items
    from .sentiment import aggregate_by_ticker
except ImportError:
    from common import TAIPEI
    from process_day import build_records, load_day_items
    from sentiment import aggregate_by_ticker

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "sentiment"


def build_report(date: str, watchlist: list[str] | None = None) -> dict | None:
    """組出當日利多/利空報告 dict；當日無資料回傳 None。"""
    items = load_day_items(date)
    if not items:
        return None
    df = build_records(items, default_ingestion=datetime.now(TAIPEI).replace(tzinfo=None))
    if df.empty:
        return None

    records = df.to_dict("records")
    by_ticker = aggregate_by_ticker(records)
    if watchlist:
        by_ticker = {t: v for t, v in by_ticker.items()
                     if any(t.startswith(w) for w in watchlist)}

    totals = {"利多": 0, "利空": 0, "中性": 0}
    for rec in records:
        totals[rec.get("sentiment_label", "中性")] += 1

    # 無個股歸屬但非中性的大盤/總經新聞，另列一區（tickers 為空不代表不重要）
    market_news = [
        {
            "label": rec["sentiment_label"],
            "score": float(rec["sentiment_score"]),
            "title": rec.get("title", ""),
            "source": rec.get("source", ""),
            "url": rec.get("url", ""),
        }
        for rec in records
        if rec.get("sentiment_label") != "中性"
        and len(rec.get("tickers") if rec.get("tickers") is not None else []) == 0
    ]
    market_news.sort(key=lambda it: abs(it["score"]), reverse=True)

    return {
        "date": date,
        "generated_at": datetime.now(TAIPEI).isoformat(),
        "totals": totals,
        "by_ticker": {
            t: v for t, v in sorted(
                by_ticker.items(), key=lambda kv: abs(kv[1]["net"]), reverse=True
            )
        },
        "market_news": market_news,
    }


def save_report(report: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{report['date']}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def print_report(report: dict, top: int = 10) -> None:
    totals = report["totals"]
    print(f"\n=== 新聞利多/利空監測 {report['date']} ===")
    print(f"總計：利多 {totals['利多']} 則｜利空 {totals['利空']} 則｜中性 {totals['中性']} 則")

    ranked = list(report["by_ticker"].items())
    bulls = [(t, v) for t, v in ranked if v["net"] > 0][:top]
    bears = [(t, v) for t, v in ranked if v["net"] < 0][:top]

    def _section(name: str, rows: list[tuple[str, dict]]) -> None:
        print(f"\n--- {name} ---")
        if not rows:
            print("（無）")
            return
        for ticker, agg in rows:
            print(f"{ticker:>10}  net={agg['net']:+.1f}  利多×{agg['bull']} 利空×{agg['bear']}")
            for it in agg["items"][:3]:
                print(f"           [{it['label']}{it['score']:+.1f}] {it['title']}")

    _section(f"個股利多榜 Top {top}", bulls)
    _section(f"個股利空榜 Top {top}", bears)

    if report["market_news"]:
        print("\n--- 大盤/總經（無個股歸屬）---")
        for it in report["market_news"][:top]:
            print(f"  [{it['label']}{it['score']:+.1f}] {it['title']}")

    print("\n※ 本輸出為新聞語意的量化整理，非投資建議；標籤依詞庫規則產生，請以原文為準。")


def main() -> None:
    ap = argparse.ArgumentParser(description="新聞利多/利空監測報告（非投資建議）")
    ap.add_argument("date", nargs="?", default=None, help="YYYY-MM-DD（預設今天）")
    ap.add_argument("--top", type=int, default=10, help="榜單顯示檔數（預設 10）")
    ap.add_argument("--tickers", default=None,
                    help="逗號分隔的自選股過濾（比對 ticker 前綴，如 2330,2454）")
    ap.add_argument("--no-save", action="store_true", help="只印報告，不寫 JSON")
    args = ap.parse_args()

    date = args.date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    watchlist = ([w.strip() for w in args.tickers.split(",") if w.strip()]
                 if args.tickers else None)

    report = build_report(date, watchlist=watchlist)
    if report is None:
        print(f"[sentiment_report] {date} 無 raw/stream 資料——"
              f"請先跑 main.py / watch_intraday.py 蒐集當日新聞")
        return
    print_report(report, top=args.top)
    if not args.no_save:
        out = save_report(report)
        print(f"[sentiment_report] 已寫入 {out}")


if __name__ == "__main__":
    main()

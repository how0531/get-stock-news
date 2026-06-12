"""盤中快訊監看 — 輪詢低延遲來源，去重後比對個股、寫入事件串流並推播。

下游介接方式有二（可並用）：
  1. 事件串流：每則新事件 append 至 data/stream/YYYY-MM-DD.jsonl，
     供「股市資訊大腦」tail 讀取（schema 見 SKILL.md「下游介接合約」）。
  2. 即時推播：設定環境變數後自動啟用
       TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID  -> Telegram Bot
       DISCORD_WEBHOOK_URL                    -> Discord webhook
     （LINE Notify 已於 2025-03-31 終止服務，勿再使用）

用法：
  python scripts/watch_intraday.py --once                # 單次輪詢（測試）
  python scripts/watch_intraday.py --interval 60 --push  # 持續監看 + 推播
  python scripts/watch_intraday.py --sources cnyes,cna,announce --market-hours-only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time as time_mod
from datetime import datetime, time
from pathlib import Path

import requests

try:
    from .cnyes import fetch as fetch_cnyes
    from .rss_sources import SOURCES as RSS_SOURCES, fetch_source as fetch_rss
    from .twse_announce import fetch as fetch_announce
except ImportError:  # 直接以 python scripts/watch_intraday.py 執行
    from cnyes import fetch as fetch_cnyes
    from rss_sources import SOURCES as RSS_SOURCES, fetch_source as fetch_rss
    from twse_announce import fetch as fetch_announce

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "state" / "seen_keys.json"
STREAM_DIR = ROOT / "data" / "stream"
STOCKS_DIR = ROOT / "data" / "stocks"

SEEN_CAP = 8000  # 去重 key 上限，超過砍最舊的

MARKET_OPEN = time(8, 30)   # 提早半小時涵蓋開盤前快訊
MARKET_CLOSE = time(13, 45)

DEFAULT_SOURCES = ["cnyes", "cna", "moneydj", "announce"]

# 與 SKILL.md「已知雜訊與處理」一致：只打 tag 不丟棄
TAG_RULES = [
    ("盤中速報", "noise_intraday_tick"),
    ("鉅亨速報 - Factset", "signal_target_price"),
    ("營收速報", "signal_revenue"),
    ("[重大訊息]", "signal_announcement"),
]


# --------------------------------------------------------------------------- #
# 去重狀態
# --------------------------------------------------------------------------- #

def load_seen() -> list[str]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return []


def save_seen(seen: list[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(seen[-SEEN_CAP:]), encoding="utf-8")


def item_key(item: dict) -> str:
    # 重大訊息共用查詢頁 URL，需加標題才唯一
    return f"{item.get('url', '')}|{item.get('title', '')}"


# --------------------------------------------------------------------------- #
# 個股比對（L1 regex + L2 字典，與 quick_heat 同邏輯的輕量版）
# --------------------------------------------------------------------------- #

def load_alias_index() -> list[tuple[str, str]]:
    """回傳 [(alias, ticker)]，別名長度倒序，先匹配長的避免 partial match。"""
    pairs: list[tuple[str, str]] = []
    for f in ("tw_stocks.json", "us_stocks.json", "jp_stocks.json"):
        path = STOCKS_DIR / f
        if not path.exists():
            continue
        for ticker, info in json.loads(path.read_text(encoding="utf-8")).items():
            for alias in info.get("aliases", []):
                pairs.append((alias, ticker))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def match_tickers(text: str, alias_index: list[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    for alias, ticker in alias_index:
        if alias in text and ticker not in found:
            found.append(ticker)
    return found


def classify(title: str) -> list[str]:
    return [tag for prefix, tag in TAG_RULES if title.startswith(prefix)]


# --------------------------------------------------------------------------- #
# 推播通道
# --------------------------------------------------------------------------- #

def push_channels() -> list[str]:
    out = []
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        out.append("telegram")
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        out.append("discord")
    return out


def push(msg: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "disable_web_page_preview": True},
                timeout=10,
            ).raise_for_status()
        except Exception as e:
            print(f"[push] telegram 失敗: {e}")
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if webhook:
        try:
            requests.post(webhook, json={"content": msg[:1900]}, timeout=10).raise_for_status()
        except Exception as e:
            print(f"[push] discord 失敗: {e}")


# --------------------------------------------------------------------------- #
# 輪詢
# --------------------------------------------------------------------------- #

def poll_sources(sources: list[str]) -> list[dict]:
    items: list[dict] = []
    for sid in sources:
        try:
            if sid == "cnyes":
                items.extend(fetch_cnyes(limit=20))
            elif sid == "announce":
                items.extend(fetch_announce())
            elif sid in RSS_SOURCES:
                items.extend(fetch_rss(sid, limit_per_feed=15))
            else:
                print(f"[watch] 未知來源: {sid}")
        except Exception as e:
            print(f"[watch] {sid} 輪詢失敗: {e}")
    return items


def poll_once(
    sources: list[str],
    seen: list[str],
    alias_index: list[tuple[str, str]],
    do_push: bool,
    include_ticks: bool,
) -> int:
    seen_set = set(seen)
    new_count = 0
    now = datetime.now()
    stream_file = STREAM_DIR / f"{now:%Y-%m-%d}.jsonl"
    STREAM_DIR.mkdir(parents=True, exist_ok=True)

    for item in poll_sources(sources):
        key = item_key(item)
        if not item.get("title") or key in seen_set:
            continue
        seen_set.add(key)
        seen.append(key)
        new_count += 1

        tags = classify(item["title"])
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        tickers = match_tickers(text, alias_index)
        if item.get("ticker_hint") and item["ticker_hint"] not in tickers:
            tickers.insert(0, item["ticker_hint"])

        event = {
            "event_id": f"{now:%Y%m%d%H%M%S}-{new_count:04d}",
            "source": item["source"],
            "category": item.get("category", ""),
            "title": item["title"],
            "url": item.get("url", ""),
            "publish_ts": item.get("published_at", ""),
            "ingestion_ts": now.isoformat(),
            "tickers": tickers,
            "tags": tags,
        }
        with open(stream_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print(f"  + [{item['source']}] {item['title']}  tickers={tickers} tags={tags}")

        # 推播原則：有比對到個股、或屬 signal 類；純價格 tick 預設不推
        is_tick = "noise_intraday_tick" in tags
        worth = (tickers or any(t.startswith("signal_") for t in tags)) and (
            include_ticks or not is_tick
        )
        if do_push and worth:
            label = " ".join(tickers[:3]) or item.get("category", "")
            push(f"[{item['source']}|{label}] {item['title']}\n{item.get('url', '')}")

    return new_count


def in_market_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    return now.weekday() < 5 and MARKET_OPEN <= now.time() <= MARKET_CLOSE


def main() -> None:
    ap = argparse.ArgumentParser(description="盤中快訊監看")
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                    help=f"逗號分隔來源（預設 {','.join(DEFAULT_SOURCES)}；"
                         f"可用 cnyes,announce,{','.join(RSS_SOURCES)}）")
    ap.add_argument("--interval", type=int, default=60, help="輪詢間隔秒數（預設 60）")
    ap.add_argument("--once", action="store_true", help="只輪詢一次後結束（測試用）")
    ap.add_argument("--push", action="store_true", help="啟用推播（需設定環境變數）")
    ap.add_argument("--include-ticks", action="store_true",
                    help="連「盤中速報」純價格 tick 也推播")
    ap.add_argument("--market-hours-only", action="store_true",
                    help="僅在台股盤中時段（08:30-13:45）輪詢")
    args = ap.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    alias_index = load_alias_index()
    seen = load_seen()

    if args.push:
        chs = push_channels()
        print(f"[watch] 推播通道: {chs or '無（未設定環境變數，僅寫入 stream）'}")

    print(f"[watch] 來源: {sources}，間隔 {args.interval}s，字典 {len(alias_index)} 別名")
    while True:
        if args.market_hours_only and not in_market_hours():
            print(f"[watch] {datetime.now():%H:%M} 非盤中時段，待命中...")
        else:
            n = poll_once(sources, seen, alias_index, args.push, args.include_ticks)
            save_seen(seen)
            print(f"[watch] {datetime.now():%H:%M:%S} 本輪新增 {n} 則")
        if args.once:
            break
        time_mod.sleep(args.interval)


if __name__ == "__main__":
    main()

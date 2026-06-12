"""日終 ETL — 將當日 raw JSON + 盤中 stream JSONL 整理成 processed Parquet。

補齊資料管線「抓取層 → PIT 儲存層」的缺口：
  - 來源：data/raw/{source}/{date}.json（main.py / backfill 寫入）
          data/stream/{date}.jsonl（watch_intraday 寫入）
  - 輸出：data/processed/date={date}/data.parquet（PIT 三時間戳齊備）
  - 去重：同文轉載以「標題正規化」聚合，保留最早 publish_ts 的一筆

用法：
  python scripts/process_day.py              # 處理今天（台北時間）
  python scripts/process_day.py 2026-06-12   # 處理指定日期
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dateutil import parser as dtparser  # type: ignore

try:
    from .common import TAIPEI, norm_title
    from . import storage
    from .watch_intraday import classify, load_alias_index, match_tickers
except ImportError:
    from common import TAIPEI, norm_title
    import storage
    from watch_intraday import classify, load_alias_index, match_tickers

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
STREAM = ROOT / "data" / "stream"


def _to_naive_taipei(value) -> datetime | None:
    """任意時間值 -> 台北時間 naive datetime（processed 層慣例）；失敗回 None。"""
    if not value:
        return None
    try:
        dt = dtparser.parse(str(value))
    except (ValueError, OverflowError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(TAIPEI).replace(tzinfo=None)
    return dt


def _record_id(item: dict) -> str:
    key = f"{norm_title(item.get('title', ''))}|{item.get('url', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def load_day_items(date: str) -> list[dict]:
    """收集當日所有 raw JSON 與 stream JSONL 項目（欄位名就地統一）。"""
    items: list[dict] = []
    for raw_file in sorted(RAW.glob(f"*/{date}.json")):
        for it in json.loads(raw_file.read_text(encoding="utf-8")):
            items.append(it)
    stream_file = STREAM / f"{date}.jsonl"
    if stream_file.exists():
        for line in stream_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            ev.setdefault("published_at", ev.get("publish_ts", ""))
            items.append(ev)
    return items


def build_records(
    items: list[dict],
    default_ingestion: datetime,
    alias_index: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """純函式：項目清單 -> processed schema DataFrame（含去重與 PIT 時間戳）。"""
    if alias_index is None:
        alias_index = load_alias_index()

    by_title: dict[str, dict] = {}
    for item in items:
        title = item.get("title") or ""
        if not title:
            continue
        tkey = norm_title(title)
        publish = _to_naive_taipei(item.get("published_at") or item.get("publish_ts"))
        ingestion = _to_naive_taipei(item.get("ingestion_ts")) or default_ingestion
        # 來源時鐘誤差可能讓 publish 晚於我們的抓取時間；PIT 不變量要求
        # ingestion >= publish，以 publish 為下限校正
        if publish is not None and ingestion < publish:
            ingestion = publish

        if "tickers" in item:
            tickers = list(item["tickers"])
        else:
            text = f"{title} {item.get('summary', '')}"
            tickers = match_tickers(text, alias_index)
        tags = list(item["tags"]) if "tags" in item else classify(title)

        rec = {
            "id": _record_id(item),
            "source": item.get("source", ""),
            "category": item.get("category", ""),
            "title": title,
            "summary": item.get("summary", ""),
            "url": item.get("url", ""),
            "publish_ts": publish,
            "ingestion_ts": ingestion,
            "actionable_ts": storage.compute_actionable_ts(publish)
            if publish is not None
            else None,
            "tickers": tickers,
            "tags": tags,
        }

        # 同文轉載：保留最早 publish 的一筆（無 publish 的視為最晚）
        prev = by_title.get(tkey)
        if prev is None:
            by_title[tkey] = rec
        else:
            prev_pub = prev["publish_ts"] or datetime.max
            cur_pub = publish or datetime.max
            if cur_pub < prev_pub:
                by_title[tkey] = rec

    df = pd.DataFrame(list(by_title.values()))
    if df.empty:
        return pd.DataFrame(columns=storage.PROCESSED_REQUIRED)
    for col in ("publish_ts", "ingestion_ts", "actionable_ts"):
        df[col] = pd.to_datetime(df[col])
    return df


def main(date: str | None = None) -> None:
    date = date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
    items = load_day_items(date)
    if not items:
        print(f"[process_day] {date} 無 raw/stream 資料，跳過")
        return
    df = build_records(items, default_ingestion=datetime.now(TAIPEI).replace(tzinfo=None))
    out = storage.save_processed(date, df)
    n_pub = int(df["publish_ts"].notna().sum())
    print(f"[process_day] {date}: {len(items)} 項 -> 去重後 {len(df)} 筆"
          f"（含 publish_ts {n_pub} 筆）-> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

"""共用工具 — 台北時區時間正規化、標題正規化去重 key、HTTP retry。

所有爬蟲共用，確保 publish_ts 一律輸出 Asia/Taipei ISO 格式、
抓取失敗自動 retry、跨來源轉載可用標題正規化後去重。
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dateutil import parser as dtparser  # type: ignore

TAIPEI = ZoneInfo("Asia/Taipei")


def to_taipei_iso(value) -> str:
    """epoch / datetime / 時間字串 -> Asia/Taipei ISO 字串；無法解析回傳空字串。

    naive（無時區）輸入視為台北時間；aware 輸入換算成台北時間。
    """
    if value is None or value == "" or value == 0:
        return ""
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, TAIPEI)
    elif isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = dtparser.parse(str(value))
        except (ValueError, OverflowError):
            return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TAIPEI)
    return dt.astimezone(TAIPEI).isoformat()


# \w 在 Python3 str 模式下涵蓋 CJK，故 \W 只會移除標點/空白，保留中文
_NON_WORD_RE = re.compile(r"[\W_]+")


def norm_title(title: str) -> str:
    """標題正規化：去空白標點、轉小寫。同文轉載（URL 不同）可據此去重。"""
    return _NON_WORD_RE.sub("", title or "").lower()


def request_get(
    url: str,
    *,
    retries: int = 2,
    backoff: float = 2.0,
    timeout: int = 10,
    **kwargs,
) -> requests.Response:
    """requests.get + raise_for_status，失敗時指數退避重試（共 retries+1 次）。"""
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
    raise last_exc

"""搜集層純邏輯測試 — common / twse_announce / watch_intraday / process_day / 假日 PIT。"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

import common
import healthcheck
import process_day
import storage
import watch_intraday
from ctee import _url_date_iso
from rss_sources import SOURCES as RSS_SOURCES_KEYS
from twse_announce import _roc_to_iso


# --------------------------------------------------------------------------- #
# common
# --------------------------------------------------------------------------- #

def test_to_taipei_iso():
    # epoch -> 台北時間
    assert common.to_taipei_iso(1781249405) == "2026-06-12T15:30:05+08:00"
    # naive 字串視為台北時間
    assert common.to_taipei_iso("2026-06-12 15:30:05") == "2026-06-12T15:30:05+08:00"
    # aware 字串換算成台北時間（UTC 07:30 = 台北 15:30）
    assert common.to_taipei_iso("2026-06-12T07:30:05+00:00") == "2026-06-12T15:30:05+08:00"
    # 無法解析 / 空值
    assert common.to_taipei_iso("not a date") == ""
    assert common.to_taipei_iso("") == ""
    assert common.to_taipei_iso(None) == ""


def test_norm_title():
    assert common.norm_title("台積電 法說會！(獨家)") == "台積電法說會獨家"
    assert common.norm_title("TSMC Beats  Estimates") == "tsmcbeatsestimates"
    assert common.norm_title("") == ""
    # 同文轉載：標點/空白差異不影響 key
    a = common.norm_title("〈焦點股〉台積電爆量上攻")
    b = common.norm_title("焦點股：台積電爆量上攻")
    assert a == b


# --------------------------------------------------------------------------- #
# twse_announce
# --------------------------------------------------------------------------- #

def test_roc_to_iso():
    assert _roc_to_iso("1150612", "133005") == "2026-06-12T13:30:05+08:00"
    assert _roc_to_iso("115/06/12", "13:30:05") == "2026-06-12T13:30:05+08:00"
    assert _roc_to_iso("20260612", "") == "2026-06-12T00:00:00+08:00"
    assert _roc_to_iso("", "") == ""
    assert _roc_to_iso("garbage", "12") == ""


# --------------------------------------------------------------------------- #
# watch_intraday
# --------------------------------------------------------------------------- #

def test_classify():
    assert watch_intraday.classify("盤中速報 - 台積電急拉") == ["noise_intraday_tick"]
    assert watch_intraday.classify("鉅亨速報 - Factset 最新調查") == ["signal_target_price"]
    assert watch_intraday.classify("[重大訊息] 台積電(2330) 澄清") == ["signal_announcement"]
    assert watch_intraday.classify("一般新聞標題") == []


def test_match_tickers():
    idx = [("台積電", "2330.TW"), ("台積", "2330.TW"), ("鴻海", "2317.TW")]
    idx.sort(key=lambda p: len(p[0]), reverse=True)
    assert watch_intraday.match_tickers("台積電與鴻海同步上漲", idx) == ["2330.TW", "2317.TW"]
    assert watch_intraday.match_tickers("與個股無關", idx) == []


def test_item_keys_dedupe_reprint():
    a = {"url": "https://a/1", "title": "〈焦點股〉台積電爆量上攻"}
    b = {"url": "https://b/2", "title": "焦點股：台積電爆量上攻"}  # 轉載，URL 不同
    keys_a, keys_b = watch_intraday.item_keys(a), watch_intraday.item_keys(b)
    assert keys_a[0] != keys_b[0]          # URL key 不同
    assert keys_a[1] == keys_b[1]          # 標題 key 相同 -> 會被去重


def test_in_market_hours_taipei():
    assert watch_intraday.in_market_hours(datetime(2026, 6, 12, 10, 0))      # 週五盤中
    assert not watch_intraday.in_market_hours(datetime(2026, 6, 13, 10, 0))  # 週六
    assert not watch_intraday.in_market_hours(datetime(2026, 6, 12, 14, 0))  # 收盤後


# --------------------------------------------------------------------------- #
# storage: 假日感知 actionable_ts
# --------------------------------------------------------------------------- #

def test_actionable_ts_holiday_aware():
    # 2026-01-01（週四，元旦休市）盤中發布 -> 1/2（週五）開盤
    assert storage.compute_actionable_ts(datetime(2026, 1, 1, 10, 0)) == datetime(2026, 1, 2, 9, 0)
    # 春節前最後交易日（2/13 週五）盤後 -> 跳過 2/16-2/20 連假與週末 -> 2/23（週一）開盤
    assert storage.compute_actionable_ts(datetime(2026, 2, 13, 20, 0)) == datetime(2026, 2, 23, 9, 0)
    # 連假中（2/18 週三）發布 -> 2/23（週一）開盤
    assert storage.compute_actionable_ts(datetime(2026, 2, 18, 10, 0)) == datetime(2026, 2, 23, 9, 0)
    # 一般交易日規則不受影響
    assert storage.compute_actionable_ts(datetime(2026, 6, 12, 7, 0)) == datetime(2026, 6, 12, 9, 0)


# --------------------------------------------------------------------------- #
# process_day
# --------------------------------------------------------------------------- #

def test_build_records_dedupe_and_pit():
    idx = [("台積電", "2330.TW")]
    items = [
        {  # raw 項目（無 tickers/tags，現算）
            "source": "cnyes", "category": "台股",
            "title": "台積電法說會釋出樂觀展望", "summary": "",
            "url": "https://a/1", "published_at": "2026-06-12T10:00:00+08:00",
        },
        {  # 同文轉載（標題同、URL 不同、發布較晚）-> 應被去重，保留較早那筆
            "source": "yahoo_stock", "category": "台股",
            "title": "台積電法說會釋出樂觀展望！", "summary": "",
            "url": "https://b/2", "published_at": "2026-06-12T10:30:00+08:00",
        },
        {  # stream 事件（已帶 tickers/tags，沿用不重算）
            "source": "announce_twse", "category": "上市重大訊息",
            "title": "[重大訊息] 台積電(2330) 澄清", "summary": "",
            "url": "https://mops/x", "publish_ts": "2026-06-12T14:10:00+08:00",
            "ingestion_ts": "2026-06-12T14:11:00+08:00",
            "tickers": ["2330.TW"], "tags": ["signal_announcement"],
        },
    ]
    df = process_day.build_records(
        items, default_ingestion=datetime(2026, 6, 12, 16, 0), alias_index=idx
    )
    assert len(df) == 2  # 轉載被去重
    for col in storage.PROCESSED_REQUIRED:
        assert col in df.columns

    row_news = df[df["source"] == "cnyes"].iloc[0]
    assert row_news["tickers"] == ["2330.TW"]
    # 盤中發布 -> 當日 13:30 可行動
    assert row_news["actionable_ts"] == pd.Timestamp(2026, 6, 12, 13, 30)

    row_ann = df[df["source"] == "announce_twse"].iloc[0]
    # 盤後發布 -> 次一交易日 09:00（6/12 週五 -> 6/15 週一）
    assert row_ann["actionable_ts"] == pd.Timestamp(2026, 6, 15, 9, 0)
    # PIT 不變量：ingestion >= publish
    assert (df["ingestion_ts"] >= df["publish_ts"]).all()
    # 通過 storage 的 schema/PIT 驗證
    storage.validate_schema(df, "processed")


def test_ctee_url_date_iso():
    # URL 內嵌 8 碼日期 -> 台北時間日粒度 ISO
    url = "https://www.ctee.com.tw/news/20260612123456-430701"
    assert _url_date_iso(url) == "2026-06-12T00:00:00+08:00"
    # 無日期樣式 -> 空字串
    assert _url_date_iso("https://www.ctee.com.tw/livenews") == ""


# --------------------------------------------------------------------------- #
# healthcheck
# --------------------------------------------------------------------------- #

def test_healthcheck_probe_success():
    r = healthcheck.probe(
        "demo",
        lambda: [{"title": "標題A", "published_at": "2026-06-12T10:00:00+08:00"},
                 {"title": "標題B", "published_at": ""}],
    )
    assert r["ok"] and r["count"] == 2 and r["with_ts"] == 1
    assert r["detail"] == "標題A"


def test_healthcheck_probe_handles_exception():
    def boom():
        raise RuntimeError("403 Forbidden")
    r = healthcheck.probe("demo", boom)
    assert not r["ok"] and r["count"] == 0
    assert "403 Forbidden" in r["detail"]


def test_healthcheck_probe_empty_is_not_ok():
    r = healthcheck.probe("demo", lambda: [])
    assert not r["ok"] and r["count"] == 0


def test_healthcheck_build_probes_selection():
    # 指定來源只組出該來源；未指定則涵蓋固定來源 + 所有 RSS
    only = healthcheck.build_probes({"cnyes"})
    assert [label for label, _ in only] == ["cnyes"]
    all_labels = [label for label, _ in healthcheck.build_probes(set())]
    assert {"cnyes", "udn", "ctee", "announce"}.issubset(set(all_labels))
    assert set(RSS_SOURCES_KEYS).issubset(set(all_labels))


def test_build_records_clock_skew_clamp():
    # 來源時鐘快於我們：ingestion 被校正為不早於 publish
    items = [{
        "source": "cnyes", "category": "台股", "title": "時鐘誤差測試",
        "summary": "", "url": "https://a/9",
        "published_at": "2026-06-12T10:00:00+08:00",
    }]
    df = process_day.build_records(
        items, default_ingestion=datetime(2026, 6, 12, 9, 59), alias_index=[]
    )
    assert df.iloc[0]["ingestion_ts"] == pd.Timestamp(2026, 6, 12, 10, 0)

"""stock-heat-model 腳本的離線測試 — 目標價抽取 / 快速熱度。

這兩支腳本消費 get-stock-NEWS 產出的 data/raw，做評分與訊號抽取，
屬熱度模型範疇（非搜集層）。CI 與 get-stock-NEWS 的 scripts 測試分開跑。
"""
from __future__ import annotations

import extract_target_price
import quick_heat


# --------------------------------------------------------------------------- #
# extract_target_price
# --------------------------------------------------------------------------- #

def test_pit_accepts_both_field_names():
    """即時 collector 寫 published_at、backfill 寫 publish_ts，抽取器兩者都要接得到。"""
    live = {"published_at": "2026-06-12T10:00:00+08:00"}
    backfilled = {"publish_ts": "2026-06-12T10:00:00+08:00"}
    assert extract_target_price._pit(live) == "2026-06-12T10:00:00+08:00"
    assert extract_target_price._pit(backfilled) == "2026-06-12T10:00:00+08:00"


def test_parse_factset_keeps_pit_from_live_raw():
    """Factset 標題用即時 raw（published_at）也要保住 PIT 時間（修正前會是 None）。"""
    art = {
        "title": "鉅亨速報 - Factset 最新調查：旺矽(6223-TW)目標價調升至4500元，幅度約6.76%",
        "published_at": "2026-06-12T10:00:00+08:00", "url": "https://x/1",
    }
    sig = extract_target_price.parse_factset(art)
    assert sig["parse_status"] == "ok"
    assert sig["ticker"] == "6223-TW"
    assert sig["action"] == "raise"
    assert sig["target_price"] == 4500.0
    assert sig["publish_ts"] == "2026-06-12T10:00:00+08:00"


def test_parse_generic_target_price():
    art = {"title": "外資看好台積電，目標價上看 1200 元", "summary": ""}
    sig = extract_target_price.parse_generic(art)
    assert sig is not None
    assert sig["broker"] == "外資"
    assert sig["target_price"] == 1200.0


# --------------------------------------------------------------------------- #
# quick_heat
# --------------------------------------------------------------------------- #

def test_is_noise():
    assert quick_heat.is_noise("盤中速報 - 台積電急拉")
    assert not quick_heat.is_noise("台積電法說會展望樂觀")


def test_count_mentions_boundaries():
    # 數字代號需邊界，避免 2330 命中 23300
    assert quick_heat.count_mentions("2330 大漲，但 23300 無關", "2330") == 1
    # 中文直接 substring
    assert quick_heat.count_mentions("台積電台積電", "台積電") == 2


def test_score_article_title_weighted_double():
    alias_pairs = [("台積電", "2330.TW")]
    art = {"title": "台積電大漲", "summary": "台積電法說"}
    scored = quick_heat.score_article(art, alias_pairs)
    # 標題×2 + 摘要×1 = 3
    assert scored["2330.TW"]["score"] == 3
    assert scored["2330.TW"]["in_title"] is True

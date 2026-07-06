"""sentiment / sentiment_report 離線測試（無網路）。"""
from __future__ import annotations

from datetime import datetime

import sentiment
import sentiment_report
import watch_intraday
from process_day import build_records
from sentiment import aggregate_by_ticker, classify_news, score_text


# --------------------------------------------------------------------------- #
# score_text / classify_news
# --------------------------------------------------------------------------- #

def test_bullish_title():
    r = classify_news("台積電上修財測 產能滿載")
    assert r["label"] == "利多"
    assert r["score"] > 0
    assert any("上修財測" in h for h in r["hits"])


def test_bearish_title():
    r = classify_news("某公司財測下修 訂單流失虧損擴大")
    assert r["label"] == "利空"
    assert r["score"] < 0


def test_neutral():
    r = classify_news("台股今日成交量與昨日相當")
    assert r["label"] == "中性"
    assert r["score"] == 0.0
    assert r["hits"] == []


def test_span_consumption_no_double_count():
    """「成長趨緩」應整段判利空，不得再拆出「成長」計利多。"""
    score, hits = score_text("公司營收成長趨緩")
    assert score == -2
    assert any("成長趨緩" in h for h in hits)
    assert not any(h.startswith("成長(") for h in hits)


def test_longest_phrase_wins():
    """「下修目標價」(-3) 優先於「下修」(-1)。"""
    score, hits = score_text("外資下修目標價")
    assert score == -3
    assert any("下修目標價" in h for h in hits)


def test_hedge_discount():
    """標題含「傳」類避險詞：分數打對折。漲停(+3)×標題2 = 6 -> 3。"""
    plain = classify_news("某股亮燈漲停")
    hedged = classify_news("市場傳出某股可望漲停")
    assert plain["score"] == 6.0
    assert hedged["hedged"] is True
    assert hedged["score"] == plain["score"] / 2


def test_title_weight_double():
    """同一詞出現在標題的分數是內文的兩倍。"""
    in_title = classify_news("公司獲利優於預期", "", "")
    in_body = classify_news("公司公布財報", "獲利優於預期", "")
    assert in_title["score"] == 2 * in_body["score"]


def test_body_char_cap():
    """超出 BODY_CHARS 的內文不參與計分。"""
    far_away = " " * (sentiment.BODY_CHARS + 10) + "漲停"
    r = classify_news("公司公告", "", far_away)
    assert r["score"] == 0.0


def test_per_phrase_cap():
    """同一片語最多計 PER_PHRASE_CAP 次，關鍵字堆疊不能灌分。"""
    score, _ = score_text("漲停！漲停！漲停！漲停！")
    assert score == 3 * sentiment.PER_PHRASE_CAP


# --------------------------------------------------------------------------- #
# aggregate_by_ticker
# --------------------------------------------------------------------------- #

def test_aggregate_by_ticker():
    records = [
        {"tickers": ["2330.TW"], "sentiment_label": "利多", "sentiment_score": 6.0,
         "title": "上修財測", "url": "u1", "source": "cnyes", "publish_ts": "t1"},
        {"tickers": ["2330.TW"], "sentiment_label": "利空", "sentiment_score": -2.0,
         "title": "外資賣超", "url": "u2", "source": "moneydj", "publish_ts": "t2"},
        {"tickers": [], "sentiment_label": "利多", "sentiment_score": 4.0,
         "title": "無個股歸屬", "url": "u3", "source": "cna", "publish_ts": "t3"},
        {"tickers": ["2454.TW"], "sentiment_label": "中性", "sentiment_score": 0.0,
         "title": "中性新聞", "url": "u4", "source": "cnyes", "publish_ts": "t4"},
    ]
    agg = aggregate_by_ticker(records)
    assert set(agg) == {"2330.TW"}
    assert agg["2330.TW"]["bull"] == 1
    assert agg["2330.TW"]["bear"] == 1
    assert agg["2330.TW"]["net"] == 4.0
    # items 依 |score| 排序
    assert agg["2330.TW"]["items"][0]["title"] == "上修財測"


# --------------------------------------------------------------------------- #
# 管線整合：stream 事件與 processed 欄位
# --------------------------------------------------------------------------- #

def test_build_event_carries_sentiment():
    item = {"source": "cnyes", "title": "某公司由盈轉虧", "url": "https://x",
            "published_at": "2026-06-12T10:00:00+08:00"}
    senti = classify_news(item["title"])
    ev = watch_intraday.build_event(
        item, event_id="e1", ingestion_iso="2026-06-12T10:01:00+08:00",
        tickers=[], tags=[], sentiment=senti,
    )
    assert ev["sentiment"]["label"] == "利空"
    # 未傳 sentiment 時預設中性且欄位恆存在（向後相容舊呼叫端）
    ev2 = watch_intraday.build_event(
        item, event_id="e2", ingestion_iso="2026-06-12T10:01:00+08:00",
        tickers=[], tags=[],
    )
    assert ev2["sentiment"]["label"] == "中性"


def test_build_records_adds_sentiment_columns():
    idx = [("台積電", "2330.TW")]
    items = [
        {"source": "cnyes", "category": "台股", "title": "台積電上修財測",
         "summary": "", "content": "", "url": "https://a",
         "published_at": "2026-06-12T10:00:00+08:00"},
        # stream 事件已帶 sentiment：應沿用，不重算
        {"source": "moneydj", "category": "台股", "title": "台積電外資動向",
         "summary": "", "content": "", "url": "https://b",
         "published_at": "2026-06-12T11:00:00+08:00",
         "sentiment": {"label": "利空", "score": -9.9, "hits": ["自帶"], "hedged": False}},
    ]
    df = build_records(items, default_ingestion=datetime(2026, 6, 12, 12, 0),
                       alias_index=idx)
    by_title = {r["title"]: r for r in df.to_dict("records")}
    assert by_title["台積電上修財測"]["sentiment_label"] == "利多"
    assert by_title["台積電外資動向"]["sentiment_label"] == "利空"
    assert by_title["台積電外資動向"]["sentiment_score"] == -9.9


def test_report_build_and_print(tmp_path, monkeypatch, capsys):
    """端到端：raw 項目 -> build_report -> print_report / save_report。"""
    items = [
        {"source": "cnyes", "category": "台股", "title": "台積電上修財測 產能滿載",
         "summary": "", "content": "", "url": "https://a",
         "published_at": "2026-06-12T10:00:00+08:00"},
        {"source": "cnyes", "category": "台股", "title": "某小型股遭砍單 虧損擴大",
         "summary": "", "content": "", "url": "https://b",
         "published_at": "2026-06-12T10:30:00+08:00"},
    ]
    monkeypatch.setattr(sentiment_report, "load_day_items", lambda date: items)
    monkeypatch.setattr(sentiment_report, "OUT_DIR", tmp_path)

    report = sentiment_report.build_report("2026-06-12")
    assert report["totals"]["利多"] == 1
    assert report["totals"]["利空"] == 1
    assert "2330.TW" in report["by_ticker"] or "2330" in str(report["by_ticker"])

    sentiment_report.print_report(report)
    out = capsys.readouterr().out
    assert "利多榜" in out and "非投資建議" in out

    path = sentiment_report.save_report(report)
    assert path.exists()


def test_report_no_data(monkeypatch):
    monkeypatch.setattr(sentiment_report, "load_day_items", lambda date: [])
    assert sentiment_report.build_report("2026-06-12") is None

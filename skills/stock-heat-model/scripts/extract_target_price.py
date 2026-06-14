"""券商目標價變動訊號抽取器。

來源：data/raw/cnyes/YYYY-MM-DD.json
輸出：data/target_price/YYYY-MM-DD.json

抽取兩類訊號：
  1. 鉅亨速報 - Factset 最新調查  (高訊雜比，結構化標題，可機械解析)
  2. 一般新聞中含「○○證券：XX 目標價 NNN」等模式 (regex 抽取)

設計重點：
  - 標題優先，summary 補充
  - PIT 時間戳保留（publish_ts）
  - 解析失敗的 Factset 速報以 parse_status=failed 留檔，供後續審視
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# repo 根：本檔在 skills/stock-heat-model/scripts/ 下，往上三層
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "cnyes"  # 消費 get-stock-NEWS 產出的 raw
OUT_DIR = PROJECT_ROOT / "data" / "target_price"


def _pit(article: dict) -> str | None:
    """取 PIT 發布時間。即時 collector 寫 published_at、backfill 寫 publish_ts，兩者都接。"""
    return article.get("publish_ts") or article.get("published_at")

# ---------- Factset 速報 ----------
# 標題模式 A：「鉅亨速報 - Factset 最新調查：應用材料AMAT-US的目標價調升至510元，幅度約13.33%」
# 標題模式 B：「鉅亨速報 - Factset 最新調查：旺矽(6223-TW)目標價調升至4500元，幅度約6.76%」
# 標題模式 C：「鉅亨速報 - Factset 最新調查：阿里巴巴集團控股(BABA-US)EPS預估下修至6.73元，預估目標價為192.11元」
#                                            ^^^^^ EPS-only update，仍含目標價，視為 "reiterate"

FACTSET_TITLE_PREFIX = "鉅亨速報 - Factset 最新調查"

# 純目標價變動（含幅度）
RE_FACTSET_TP = re.compile(
    r"Factset\s*最新調查[:：]\s*"
    r"(?P<name>.+?)"
    r"[\(（]?(?P<ticker>[A-Z0-9]{1,6}(?:\.[A-Z]+)?-(?:US|TW|HK))[\)）]?"
    r"\s*的?目標價\s*(?P<action>調升|調降|維持|持平)\s*至\s*"
    r"(?P<price>[0-9]+(?:\.[0-9]+)?)\s*元"
    r"[,，]?\s*幅度約?\s*(?P<pct>-?[0-9]+(?:\.[0-9]+)?)\s*%"
)

# EPS 預估 + 目標價（隱含 reiterate）
RE_FACTSET_EPS = re.compile(
    r"Factset\s*最新調查[:：]\s*"
    r"(?P<name>.+?)"
    r"\(\s*(?P<ticker>[A-Z0-9]{1,6}(?:\.[A-Z]+)?-(?:US|TW|HK))\s*\)"
    r"\s*EPS\s*預估(?P<eps_action>上修|下修|維持)"
    r".*?預估目標價為?\s*(?P<price>[0-9][0-9,]*(?:\.[0-9]+)?)\s*元"
)

# ---------- 一般新聞 ----------
BROKERS = [
    # 外資
    "摩根士丹利", "大摩", "摩根大通", "小摩", "摩根",
    "高盛", "瑞銀", "花旗", "美銀", "美林", "美銀美林",
    "野村", "大和", "瑞信", "巴克萊", "匯豐", "滙豐",
    "麥格理", "里昂", "德意志", "傑富瑞", "Jefferies",
    "里昂證券", "韓國KB", "韓投",
    # 本土
    "富邦", "元大", "凱基", "國泰", "永豐", "群益", "統一",
    "兆豐", "玉山", "華南永昌", "日盛", "第一金", "台新",
    "中信", "宏遠", "致和", "新光",
    # 通稱
    "外資", "投行", "投顧", "法人",
]

# 排序：較長的字串放前面，避免「摩根」吃掉「摩根士丹利」
BROKERS_SORTED = sorted(set(BROKERS), key=len, reverse=True)
RE_BROKER = re.compile("(" + "|".join(map(re.escape, BROKERS_SORTED)) + ")")

RE_TW_TICKER = re.compile(r"\(?(\d{4,6})[-\s]?TW\)?|\(?(\d{4,6})\)")
RE_US_TICKER = re.compile(r"\(?([A-Z]{1,5})[-\s]?US\)?")

ACTION_KEYWORDS = {
    "raise": ["上修", "調升", "喊上", "上看", "看高", "看升", "升評", "上調"],
    "lower": ["下修", "調降", "下調", "降評", "看低"],
    "initiate": ["初評", "首評", "首次評等"],
    "reiterate": ["維持", "持平", "重申"],
}


def _classify_action(text: str) -> str | None:
    for action, kws in ACTION_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return action
    return None


def _ticker_currency(ticker: str) -> str:
    if ticker.endswith("-TW"):
        return "TWD"
    if ticker.endswith("-HK"):
        return "HKD"
    return "USD"


def _ticker_market(ticker: str) -> str:
    if ticker.endswith("-TW"):
        return "TW"
    if ticker.endswith("-HK"):
        return "HK"
    return "US"


def parse_factset(article: dict) -> dict | None:
    title = article.get("title") or ""
    if FACTSET_TITLE_PREFIX not in title:
        return None

    m = RE_FACTSET_TP.search(title)
    if m:
        action_zh = m.group("action")
        action = {"調升": "raise", "調降": "lower",
                  "維持": "reiterate", "持平": "reiterate"}.get(action_zh, "reiterate")
        ticker = m.group("ticker")
        return {
            "ticker": ticker,
            "name": m.group("name").strip(),
            "market": _ticker_market(ticker),
            "action": action,
            "target_price": float(m.group("price")),
            "currency": _ticker_currency(ticker),
            "change_pct": float(m.group("pct")),
            "broker": "Factset (aggregated)",
            "publish_ts": _pit(article),
            "source_url": article.get("url"),
            "raw_title": title,
            "parse_status": "ok",
            "signal_type": "factset_tp_change",
        }

    m = RE_FACTSET_EPS.search(title)
    if m:
        ticker = m.group("ticker")
        return {
            "ticker": ticker,
            "name": m.group("name").strip(),
            "market": _ticker_market(ticker),
            "action": "reiterate",  # EPS-only 更新，目標價可能未變
            "target_price": float(m.group("price").replace(",", "")),
            "currency": _ticker_currency(ticker),
            "change_pct": None,
            "broker": "Factset (aggregated)",
            "publish_ts": _pit(article),
            "source_url": article.get("url"),
            "raw_title": title,
            "parse_status": "ok",
            "signal_type": "factset_eps_update",
        }

    return {
        "ticker": None,
        "name": None,
        "market": None,
        "action": None,
        "target_price": None,
        "currency": None,
        "change_pct": None,
        "broker": "Factset (aggregated)",
        "publish_ts": _pit(article),
        "source_url": article.get("url"),
        "raw_title": title,
        "parse_status": "failed",
        "signal_type": "factset_unparsed",
    }


def parse_generic(article: dict) -> dict | None:
    """一般新聞 regex 抽取。"""
    title = article.get("title") or ""
    summary = article.get("summary") or ""
    if FACTSET_TITLE_PREFIX in title:
        return None
    if "目標價" not in title and "目標價" not in summary:
        return None

    text = title + " || " + summary
    bm = RE_BROKER.search(text)
    # 強制要求 "元" 結尾，避免 "目標價上看 80%" 之類的偽匹配
    # 要求價格後面接「元」或「美元」（避免「目標價上看 80%」的偽匹配）
    pm = re.search(r"目標價[^。，,0-9]{0,12}?([0-9]{2,5}(?:\.[0-9]+)?)\s*(?:美元|元)", text)
    if not (bm and pm):
        return None

    # ticker
    ticker = None
    market = None
    tw_m = RE_TW_TICKER.search(text)
    us_m = RE_US_TICKER.search(text)
    if tw_m:
        code = tw_m.group(1) or tw_m.group(2)
        ticker = f"{code}-TW"
        market = "TW"
    elif us_m:
        ticker = f"{us_m.group(1)}-US"
        market = "US"

    action = _classify_action(text) or "reiterate"

    return {
        "ticker": ticker,
        "name": None,
        "market": market,
        "action": action,
        "target_price": float(pm.group(1)),
        "currency": "TWD" if market == "TW" else ("USD" if market == "US" else None),
        "change_pct": None,
        "broker": bm.group(1),
        "publish_ts": _pit(article),
        "source_url": article.get("url"),
        "raw_title": title,
        "parse_status": "ok",
        "signal_type": "generic_news_tp",
    }


def process_day(day_iso: str) -> dict:
    in_path = RAW_DIR / f"{day_iso}.json"
    if not in_path.exists():
        return {"date": day_iso, "exists": False}

    with open(in_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    signals: list[dict] = []
    n_factset_total = 0
    n_factset_ok = 0
    n_generic = 0

    for art in articles:
        title = art.get("title") or ""
        if FACTSET_TITLE_PREFIX in title:
            n_factset_total += 1
            sig = parse_factset(art)
            if sig:
                if sig["parse_status"] == "ok":
                    n_factset_ok += 1
                signals.append(sig)
        else:
            sig = parse_generic(art)
            if sig:
                n_generic += 1
                signals.append(sig)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{day_iso}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    return {
        "date": day_iso,
        "exists": True,
        "n_factset_total": n_factset_total,
        "n_factset_ok": n_factset_ok,
        "n_generic": n_generic,
        "n_signals": len(signals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--date", default=None, help="single date YYYY-MM-DD")
    args = ap.parse_args()

    if args.date:
        dates = [args.date]
    else:
        # 取 RAW_DIR 中最新 N 天
        files = sorted([p.stem for p in RAW_DIR.glob("*.json")])
        dates = files[-args.days:]

    print(f"Processing {len(dates)} days: {dates[0]} -> {dates[-1]}")
    summary = []
    for d in dates:
        s = process_day(d)
        summary.append(s)
        if s["exists"]:
            print(
                f"[{d}] factset={s['n_factset_ok']}/{s['n_factset_total']} "
                f"generic={s['n_generic']} total_signals={s['n_signals']}"
            )
        else:
            print(f"[{d}] raw file missing, skipped")

    totals = {
        "factset_total": sum(s.get("n_factset_total", 0) for s in summary),
        "factset_ok": sum(s.get("n_factset_ok", 0) for s in summary),
        "generic": sum(s.get("n_generic", 0) for s in summary),
        "signals": sum(s.get("n_signals", 0) for s in summary),
    }
    print("---- TOTALS ----")
    print(json.dumps(totals, ensure_ascii=False, indent=2))
    if totals["factset_total"]:
        rate = totals["factset_ok"] / totals["factset_total"] * 100
        print(f"Factset parse success rate: {rate:.1f}%")


if __name__ == "__main__":
    sys.exit(main())

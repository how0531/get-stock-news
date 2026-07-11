"""新聞利多/利空分類 — 財經詞庫規則法（純函式，可離線測試）。

設計原則：
  - 詞庫可解釋：每個判定都能列出命中詞與權重（hits），供人工覆核與調參
  - 長詞優先 + 區間消耗：「成長趨緩」整段先被利空命中後，
    其中的「成長」不會再被利多重複計分
  - 傳聞折價：標題含「傳」「可望」等避險用語時分數打對折——
    呼應課程觀念「事實 > 預期 > 傳聞」
  - 標題權重 ×2：與 quick_heat 同一慣例，標題提到才是真的在講它

分數 -> 標籤門檻（LABEL_THRESHOLD）：
  score >= +2 -> 利多；score <= -2 -> 利空；其餘 -> 中性
  （單一弱訊號詞出現在內文不觸發標籤，出現在標題即觸發）
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# 詞庫（phrase, weight）。weight 恆為正，方向由所屬詞庫決定。
# 維護原則：寧可漏掉、不要誤標——太泛用的詞（如「買進」「新高」）不收，
# 收更長、更明確的片語（「創歷史新高」「調升評等」）。
# --------------------------------------------------------------------------- #

BULLISH: list[tuple[str, int]] = [
    # 強訊號（3）：明確事件，幾乎不出現在中性語境
    ("漲停", 3), ("創歷史新高", 3), ("歷史新高", 3), ("調升評等", 3),
    ("調升目標價", 3), ("上修目標價", 3), ("目標價上調", 3), ("上修財測", 3),
    ("財測上修", 3), ("轉虧為盈", 3),
    # 中訊號（2）
    ("創新高", 2), ("同期新高", 2), ("優於預期", 2), ("高於預期", 2),
    ("超乎預期", 2), ("勝預期", 2), ("接單暢旺", 2), ("訂單滿載", 2),
    ("產能滿載", 2), ("供不應求", 2), ("擴產", 2), ("得標", 2),
    ("大單", 2), ("買超", 2), ("庫藏股", 2), ("大漲", 2), ("利多", 2),
    ("急單", 2), ("完成簽約", 2), ("策略聯盟", 2),
    # 弱訊號（1）：方向偏多但常見於一般行文
    ("成長", 1), ("看好", 1), ("看多", 1), ("樂觀", 1), ("回溫", 1),
    ("復甦", 1), ("好轉", 1), ("轉強", 1), ("勁揚", 1), ("走揚", 1),
    ("報喜", 1), ("調高", 1), ("上修", 1),
]

BEARISH: list[tuple[str, int]] = [
    # 強訊號（3）
    ("跌停", 3), ("下市", 3), ("全額交割", 3), ("違約交割", 3), ("跳票", 3),
    ("調降評等", 3), ("調降目標價", 3), ("下修目標價", 3), ("目標價下調", 3),
    ("下修財測", 3), ("財測下修", 3), ("由盈轉虧", 3), ("虧損擴大", 3),
    ("掏空", 3), ("內線交易", 3), ("檢調搜索", 3), ("崩跌", 3),
    ("彌補虧損", 3), ("停工", 3), ("裁員", 3),
    # 中訊號（2）
    ("衰退", 2), ("不如預期", 2), ("低於預期", 2), ("遜於預期", 2),
    ("砍單", 2), ("抽單", 2), ("訂單流失", 2), ("認列損失", 2), ("減損", 2),
    ("罷工", 2), ("火災", 2), ("爆炸", 2), ("召回", 2), ("求償", 2),
    ("遭罰", 2), ("罰款", 2), ("訴訟", 2), ("注意股票", 2), ("處置股票", 2),
    ("賣超", 2), ("大跌", 2), ("重挫", 2), ("利空", 2),
    ("成長趨緩", 2), ("增速放緩", 2),
    # 弱訊號（1）
    ("下滑", 1), ("下修", 1), ("調降", 1), ("趨緩", 1), ("放緩", 1),
    ("疲弱", 1), ("疲軟", 1), ("轉弱", 1), ("保守", 1), ("觀望", 1),
    ("隱憂", 1), ("承壓", 1), ("走跌", 1), ("收黑", 1),
]

# 傳聞/預期用語：出現在標題時整體分數打對折（事實 > 預期 > 傳聞）
HEDGE_WORDS = ["盛傳", "據傳", "傳出", "市場傳", "可望", "有望", "據悉", "傳聞"]

HEDGE_DISCOUNT = 0.5
LABEL_THRESHOLD = 2.0
PER_PHRASE_CAP = 2      # 同一片語每段文字最多計分次數，避免關鍵字堆疊灌分
BODY_CHARS = 400        # 內文只取前 N 字參與計分（重點多在導言，也控制成本）

# 合併成單一掃描表：(phrase, signed_weight)，長詞優先
_PHRASES: list[tuple[str, int]] = sorted(
    [(p, w) for p, w in BULLISH] + [(p, -w) for p, w in BEARISH],
    key=lambda x: len(x[0]),
    reverse=True,
)


def score_text(text: str) -> tuple[int, list[str]]:
    """對一段文字計分。回傳 (帶方向總分, 命中清單如 '漲停(+3)')。

    長詞優先掃描，命中後消耗該區間，短詞不得與已命中區間重疊——
    確保「成長趨緩」不會同時計「成長(+1)」與「趨緩(-1)」。
    """
    if not text:
        return 0, []
    consumed: list[tuple[int, int]] = []
    score = 0
    hits: list[str] = []
    for phrase, weight in _PHRASES:
        count = 0
        start = 0
        while count < PER_PHRASE_CAP:
            idx = text.find(phrase, start)
            if idx < 0:
                break
            end = idx + len(phrase)
            if any(not (end <= s or idx >= e) for s, e in consumed):
                start = idx + 1
                continue
            consumed.append((idx, end))
            count += 1
            start = end
        if count:
            score += weight * count
            sign = "+" if weight > 0 else ""
            hits.append(f"{phrase}({sign}{weight}×{count})" if count > 1
                        else f"{phrase}({sign}{weight})")
    return score, hits


def classify_news(title: str, summary: str = "", content: str = "") -> dict:
    """單則新聞 -> 利多/利空/中性 標籤。

    標題 ×2 + （摘要 + 內文前 BODY_CHARS 字）×1；
    標題含傳聞用語時總分 × HEDGE_DISCOUNT。
    """
    t_score, t_hits = score_text(title or "")
    body = f"{summary or ''} {(content or '')[:BODY_CHARS]}".strip()
    b_score, b_hits = score_text(body)

    total = float(2 * t_score + b_score)
    hedged = any(w in (title or "") for w in HEDGE_WORDS)
    if hedged:
        total *= HEDGE_DISCOUNT

    if total >= LABEL_THRESHOLD:
        label = "利多"
    elif total <= -LABEL_THRESHOLD:
        label = "利空"
    else:
        label = "中性"

    return {
        "label": label,
        "score": round(total, 1),
        "hits": [f"標題:{h}" for h in t_hits] + b_hits,
        "hedged": hedged,
    }


NEUTRAL = {"label": "中性", "score": 0.0, "hits": [], "hedged": False}


def aggregate_by_ticker(records: list[dict]) -> dict[str, dict]:
    """把已標 sentiment 的新聞彙總到個股層級。

    輸入每筆需含：tickers(list)、sentiment_label、sentiment_score、
    title、url、source、publish_ts（str 或可轉字串）。
    回傳 {ticker: {bull, bear, net, items:[...]}}，items 僅收非中性者，
    依 |score| 由大到小排序。
    """
    out: dict[str, dict] = {}
    for rec in records:
        label = rec.get("sentiment_label", "中性")
        if label == "中性":
            continue
        tickers = rec.get("tickers")
        # 兼容 list 與 parquet 讀回的 numpy array（不可直接做真值判斷）
        for ticker in (tickers if tickers is not None else []):
            agg = out.setdefault(ticker, {"bull": 0, "bear": 0, "net": 0.0, "items": []})
            score = float(rec.get("sentiment_score") or 0.0)
            if label == "利多":
                agg["bull"] += 1
            else:
                agg["bear"] += 1
            agg["net"] = round(agg["net"] + score, 1)
            agg["items"].append({
                "label": label,
                "score": score,
                "title": rec.get("title", ""),
                "source": rec.get("source", ""),
                "url": rec.get("url", ""),
                "publish_ts": str(rec.get("publish_ts") or ""),
            })
    for agg in out.values():
        agg["items"].sort(key=lambda it: abs(it["score"]), reverse=True)
    return out


if __name__ == "__main__":
    import sys

    demo = sys.argv[1] if len(sys.argv) > 1 else "台積電法說會釋出樂觀展望 上修財測"
    print(classify_news(demo))

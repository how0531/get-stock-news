---
name: get-stock-NEWS
description: Fetch and aggregate Taiwan/US/Japan financial news from major Taiwan media (cnyes 鉅亨網, UDN money 經濟日報, ctee 工商時報). Handles real-time fetch, 5-month historical backfill, PIT-correct Parquet storage, and target-price signal extraction. Use this skill whenever the user wants to fetch, list, or aggregate financial news (not score/rank them). Triggers: "今天的財經新聞", "幫我看 5/13 的新聞", "美股新聞", "日股新聞", "台股新聞", "鉅亨網", "經濟日報", "工商時報", "抓新聞", "目標價變動", "Factset", "歷史新聞回抓". For heat scoring / stock ranking / hot sectors, use the separate `stock-heat-model` skill.
---

# get-stock-NEWS — 新聞彙整

A skill for **fetching and storing** Taiwan/US/Japan financial news. Aggregation only — for heat quantification and stock ranking, see the separate `stock-heat-model` skill.

---

## Scope

| Included | Not included |
|----------|--------------|
| 抓取三家媒體新聞 | ❌ 熱度分數計算 |
| 歷史回抓（5 個月） | ❌ 個股排名 |
| 去重、PIT 儲存 | ❌ Tier 分級 |
| 目標價訊號抽取 | ❌ Veto 規則 |
| 個股字典維護 | ❌ 報酬驗證 |

---

## Sources & methods

| Source | Method | Historical | Notes |
|--------|--------|-----------|-------|
| 鉅亨網 cnyes.com | 公開 JSON API | ✅ 完整（API 支援 date range） | 必帶 `Referer: https://news.cnyes.com/` |
| 經濟日報 UDN money | sitemap 分週切片 | ✅ ~100%（過去 12 月） | URL: `/sitemap/staticmap/1001T{YYYYMM}W{N}` |
| 工商時報 ctee | 靜態 HTML / WP REST API | ⚠️ TBD | 無公開 RSS |

---

## When to use this skill

Trigger when user wants to **fetch or aggregate** news:

- "今天的財經新聞" / "最近的股市新聞"
- "幫我看 [date] 的新聞"
- "抓 5 個月歷史" / "回抓歷史"
- "鉅亨 / 經濟日報 / 工商" 任一來源
- "Factset 目標價" / "券商上修"

**不要觸發**（請改用 `stock-heat-model`）：
- "哪些股票最熱門" / "熱度排名"
- "投顧老師點名" / "重點個股 Top N"
- "熱門族群"

---

## Scripts inventory

### 即時抓取
| Script | Purpose |
|--------|---------|
| `scripts/cnyes.py` | cnyes API 即時 |
| `scripts/udn.py` | UDN RSS 即時（僅最近 1-2 日） |
| `scripts/ctee.py` | 工商時報 HTML 即時 |
| `scripts/fetch_by_date.py` | 指定日期整合（cnyes + UDN） |
| `scripts/main.py` | 三來源一次抓最新 |

### 歷史回抓
| Script | Speed | Notes |
|--------|-------|-------|
| `scripts/backfill_cnyes.py` | ~5 分/日 | 152 天 ≈ 13-14 小時 |
| `scripts/backfill_udn.py` | ~2 秒/篇 | 5 個月 ≈ 17.5 小時 |
| `scripts/backfill_ctee.py` | TBD | 待研究索引方式 |

### 儲存層
| Script | Purpose |
|--------|---------|
| `scripts/storage.py` | PIT-correct Parquet save/load/asof_merge/query |

### 訊號抽取
| Script | Purpose |
|--------|---------|
| `scripts/extract_target_price.py` | Factset 目標價（100% 解析） |

### 字典維護
| Script | Purpose |
|--------|---------|
| `scripts/build_stock_dict.py` | 重生 TW/US/JP 個股字典 |

---

## Setup

```bash
pip install -r requirements.txt
```

依賴：`requests`, `feedparser`, `beautifulsoup4`, `lxml`, `python-dateutil`, `pandas`, `pyarrow`, `duckdb`.

**Windows 必加** `PYTHONUTF8=1`，否則中文輸出全亂碼。

---

## Usage

```bash
# 抓最新
PYTHONUTF8=1 python scripts/main.py

# 指定日期
PYTHONUTF8=1 python scripts/fetch_by_date.py 2026-05-13

# 5 個月歷史背景抓取
nohup python scripts/backfill_cnyes.py > backfill_cnyes.log 2>&1 &
nohup python scripts/backfill_udn.py > backfill_udn.log 2>&1 &

# 程式化載入
from scripts.storage import load_processed, query
df = load_processed("2026-01-01", "2026-05-15")
df = query("SELECT * FROM 'data/processed/**/*.parquet' WHERE actionable_ts < '2026-05-13'")
```

---

## Data layout

```
data/
├── raw/
│   ├── cnyes/YYYY-MM-DD.json
│   ├── udn/YYYY-MM-DD.json
│   └── ctee/YYYY-MM-DD.json
├── processed/date=YYYY-MM-DD/data.parquet   ← Hive-style，DuckDB partition pruning
├── target_price/YYYY-MM-DD.json
└── stocks/
    ├── tw_stocks.json  (162 檔 + 別名)
    ├── us_stocks.json  (144 檔 + 別名)
    └── jp_stocks.json  (58 檔 + 別名)
```

---

## PIT 三時間戳（不可妥協）

每筆紀錄必含：

```
publish_ts     ← 新聞官方發布時間
ingestion_ts   ← 我們實際抓到的時間
actionable_ts  ← 最早可決策時間（依台股交易日推算）
```

### actionable_ts 規則
- 09:00 前發布 → 當日 09:00
- 09:00-13:30 → 當日 13:30
- 13:30 後 → 次一工作日 09:00
- 週末 → 次週一 09:00（國定假日尚未處理）

回測時務必用 `actionable_ts` 過濾，**禁止用 `publish_ts`**（會 look-ahead）。

---

## 已知雜訊與處理

抓取時保留所有內容，**只打 tag 不刪除**（不同 event type 衰減速度不同，回測時再決定要不要用）：

| 標題開頭 | 類型 | tag |
|---------|------|-----|
| `盤中速報` | 純價格變動 | `noise_intraday_tick` |
| `鉅亨速報 - Factset` | 目標價 / EPS 速報 | `signal_target_price` |
| `營收速報` | 月營收速報 | `signal_revenue` |

---

## 目標價訊號抽取（Factset）

鉅亨網每日約 50-60 則 Factset 速報，標題高度結構化、regex 100% 解析：

- **TP-Change**：`應用材料 AMAT-US 目標價調升至 510 元，幅度 13.33%`
- **EPS-Update**：`BABA-US EPS 下修至 6.73 元`

輸出：`data/target_price/YYYY-MM-DD.json`，結構化欄位含 `ticker`, `action`, `target_price`, `change_pct`, `publish_ts`。

**注意**：Factset 速報集中盤後 20:15 發布 → `actionable_ts` 必為次一工作日 09:00。

---

## 個股辨識（提供熱度模型使用）

### L1 regex
```python
TW_NUMERIC  = r"(?<!\d)\d{4}(?!\d)"
US_TICKER   = r"\b[A-Z]{1,5}-US\b"
JP_TICKER   = r"\b\d{4}\.T\b"
```

### L2 字典
`data/stocks/*.json`，含中文標準名、簡稱、英文、綽號、`{ticker}-US` 後綴。

### 黑名單（已從字典移除）
`AI / EV / 5G / 6G / IC / IT / OS / CEO / TV / VR / AR / PC / GPU / CPU / HBM / SSD` + 所有單字母 ticker（V/C/F/T/X/U）

### 已知歧義
| 個股 | 歧義 |
|------|------|
| 長榮 | 2603 海運 / 2618 航空 / 2607 航儲 |
| 統一 vs 統一超 | 1216 食品 / 2912 通路 |
| 台塑 / 台塑化 | 1301 / 6505 |
| 世界 | 5347 世界先進 vs「世界銀行」 |
| KY 股 | 名稱含 `-KY` 後綴 |
| ADR 雙掛 | 2330.TW + TSM、聯電、日月光、豐田、索尼 |
| 雙股別 | GOOGL / GOOG、BRK.B |

---

## Copyright

新聞內容受版權保護。本 skill 僅供個人研究與後續量化分析使用，輸出標題、連結、短摘要與結構化欄位，不重製全文。

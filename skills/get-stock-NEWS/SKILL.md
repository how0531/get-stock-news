---
name: get-stock-NEWS
description: Fetch and aggregate Taiwan/US/Japan financial news from major Taiwan media (cnyes 鉅亨網, UDN money 經濟日報, ctee 工商時報, 中央社, 自由財經, 科技新報, ETtoday, 中時, MoneyDJ, Yahoo股市) plus official TWSE/TPEx 重大訊息. Handles real-time fetch, intraday watch/push (盤中快訊推播), 5-month historical backfill, PIT-correct Parquet storage, JSONL event stream for downstream consumers, and target-price signal extraction. Use this skill whenever the user wants to fetch, list, aggregate, watch, or push financial news (not score/rank them). Triggers: "今天的財經新聞", "幫我看 5/13 的新聞", "美股新聞", "日股新聞", "台股新聞", "鉅亨網", "經濟日報", "工商時報", "中央社", "MoneyDJ", "抓新聞", "盤中快訊", "推播", "重大訊息", "目標價變動", "Factset", "歷史新聞回抓", "新增新聞來源". For heat scoring / stock ranking / hot sectors, use the separate `stock-heat-model` skill.
---

# get-stock-NEWS — 新聞彙整

A skill for **fetching and storing** Taiwan/US/Japan financial news. Aggregation only — for heat quantification and stock ranking, see the separate `stock-heat-model` skill.

---

## Scope

| Included | Not included |
|----------|--------------|
| 抓取多家媒體新聞 + 官方重大訊息 | ❌ 熱度分數計算 |
| 盤中監看、去重、快訊推播 | ❌ 個股排名 |
| 歷史回抓（5 個月） | ❌ Tier 分級 |
| 去重、PIT 儲存、事件串流輸出 | ❌ Veto 規則 |
| 目標價訊號抽取 | ❌ 報酬驗證 |
| 個股字典維護 | |

---

## 媒體來源總覽（inventory）

### 已實作 + 已驗證

| Source | Method | 延遲 | Historical | Notes |
|--------|--------|------|-----------|-------|
| 鉅亨網 cnyes.com | 公開 JSON API（`scripts/cnyes.py`） | ⚡ 最低，~1-2 分；盤中速報近即時 | ✅ 完整（API 支援 date range） | 必帶 `Referer: https://news.cnyes.com/` |
| 經濟日報 UDN money | RSS 即時 + sitemap 分週切片（`scripts/udn.py`） | RSS ~5-15 分 | ✅ ~100%（過去 12 月） | sitemap: `/sitemap/staticmap/1001T{YYYYMM}W{N}` |
| 工商時報 ctee | 靜態 HTML / WP REST API（`scripts/ctee.py`） | 列表頁更新頻率 | ⚠️ TBD | 無公開 RSS、列表無時間戳 |

### 已實作，端點待本機驗證

> 以下由 `scripts/rss_sources.py`（RSS 通用爬蟲）與 `scripts/twse_announce.py`（官方公告）支援。
> feed URL 依公開資訊撰寫，**首次使用請各跑一次確認**（`python scripts/rss_sources.py cna` 等），失效就改 `SOURCES` 註冊表。

| source_id | 媒體 | Method | 延遲 | 特性 |
|-----------|------|--------|------|------|
| `cna` | 中央社 | feedburner RSS | ~分鐘級 | 權威通訊社，政策/總經第一手 |
| `ltn` | 自由財經 | RSS | ~5-15 分 | 綜合財經 |
| `technews` | 科技新報 | WordPress RSS | ~5-15 分 | 科技供應鏈深度，補半導體盲區 |
| `ettoday` | ETtoday財經 | feedburner RSS | ~5-15 分 | 量大，雜訊比偏高 |
| `chinatimes` | 中時新聞網 | RSS | ~5-15 分 | 與工商時報同集團，可互補 |
| `moneydj` | MoneyDJ理財網 | RSS center | ~分鐘級 | 法人圈常用，個股新聞密度高 |
| `yahoo_stock` | Yahoo奇摩股市 | RSS | ~5-15 分 | 聚合多家，**去重後**才能用（轉載源） |
| `announce`(twse) | 證交所重大訊息 | TWSE OpenAPI `t187ap04_L` | 快照，非逐秒 | **官方第一手**，上市公司當日重訊 |
| `announce`(tpex) | 櫃買重大訊息 | TPEx OpenAPI `mopsfin_t187ap04_O` | 快照，非逐秒 | 上櫃公司當日重訊 |

### 規劃中 / 評估中

| 來源 | 價值 | 障礙 |
|------|------|------|
| MOPS 即時重大訊息（`t05sr01_1`） | 秒級重訊，盤中推播的終極來源 | POST form + 反爬蟲較強，待研究 |
| 證交所注意/處置股票公告 | 籌碼面 veto 訊號 | OpenAPI 有對應端點，待挑選欄位 |
| 今周刊 / 商業周刊 / 財訊 | 週刊深度報導（領先散戶情緒） | 多為 paywall，僅能取標題 |
| Reuters / Nikkei / Bloomberg 標題 | 美日股第一手 | paywall / 授權，僅標題層級 |
| PTT Stock / Dcard 股板 | 散戶情緒（反向指標候選） | 非媒體，雜訊極高，另案處理 |

**轉載去重提醒**：中央社的稿常被 Yahoo、自由、ETtoday 轉載，同事件多 URL。盤中推播用 URL 去重不夠，下游做熱度計算時需以「標題相似度」聚合（已列入 stock-heat-model 待辦）。

---

## When to use this skill

Trigger when user wants to **fetch or aggregate** news:

- "今天的財經新聞" / "最近的股市新聞"
- "幫我看 [date] 的新聞"
- "抓 5 個月歷史" / "回抓歷史"
- 任一已註冊來源名稱（鉅亨 / 經濟日報 / 工商 / 中央社 / MoneyDJ / …）
- "Factset 目標價" / "券商上修"
- "盤中快訊" / "即時推播" / "盯盤通知"
- "重大訊息" / "公司公告"
- "新增新聞來源" / "這個網站能不能抓"

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
| `scripts/rss_sources.py` | RSS 通用爬蟲（cna/ltn/technews/ettoday/chinatimes/moneydj/yahoo_stock），新來源在 `SOURCES` 註冊即可 |
| `scripts/twse_announce.py` | TWSE/TPEx OpenAPI 官方重大訊息 |
| `scripts/fetch_by_date.py` | 指定日期整合（cnyes + UDN） |
| `scripts/main.py` | 全來源一次抓最新 |

### 盤中監看與推播
| Script | Purpose |
|--------|---------|
| `scripts/watch_intraday.py` | 輪詢 + 去重 + 個股比對 + JSONL 事件串流 + Telegram/Discord 推播 |

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
# 抓最新（全來源）
PYTHONUTF8=1 python scripts/main.py

# 只抓特定 RSS 來源（驗證端點時也用這個）
PYTHONUTF8=1 python scripts/rss_sources.py cna,moneydj

# 官方重大訊息
PYTHONUTF8=1 python scripts/twse_announce.py

# 盤中監看（見下方「盤中快訊推播」一節）
PYTHONUTF8=1 python scripts/watch_intraday.py --once

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

## 盤中快訊推播（watch_intraday）

輪詢低延遲來源 → 去重 → 個股字典比對 → 寫入事件串流 → （可選）推播。

```bash
# 測試：單次輪詢
PYTHONUTF8=1 python scripts/watch_intraday.py --once

# 正式：每 60 秒輪詢，僅台股盤中時段（08:30-13:45），啟用推播
PYTHONUTF8=1 python scripts/watch_intraday.py --interval 60 --market-hours-only --push

# 自選來源（預設 cnyes,cna,moneydj,announce — 延遲最低的組合）
PYTHONUTF8=1 python scripts/watch_intraday.py --sources cnyes,announce
```

### 推播通道（設環境變數即啟用，可多通道並行）

| 通道 | 環境變數 |
|------|---------|
| Telegram Bot | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| Discord webhook | `DISCORD_WEBHOOK_URL` |

⚠️ **LINE Notify 已於 2025-03-31 終止服務**，勿再使用；要走 LINE 需改 LINE Messaging API（規劃中）。

### 推播原則
- 預設只推「有比對到個股」或 `signal_*` tag 的事件
- `noise_intraday_tick`（盤中速報純價格 tick）預設不推，`--include-ticks` 開啟
- 去重狀態存 `data/state/seen_keys.json`（上限 8000 key，重啟不重複推播）

### 輪詢頻率與禮貌
- cnyes API：60s 輪詢已遠快於其發稿頻率，勿低於 30s
- RSS 來源：站方快取多為分鐘級，60-120s 即可
- OpenAPI 重大訊息：快照型，120s 以上即可

---

## 下游介接合約（股市資訊大腦）

下游系統（資訊大腦 / 熱度模型 / 推播服務）一律從**事件串流**讀取，不要直接 import 爬蟲：

```
data/stream/YYYY-MM-DD.jsonl   ← watch_intraday 每事件 append 一行
```

每行 schema（穩定欄位，新增欄位向後相容、不刪欄位）：

```json
{
  "event_id":     "20260612093015-0001",
  "source":       "cnyes",
  "category":     "台股",
  "title":        "台積電法說會釋出樂觀展望",
  "url":          "https://news.cnyes.com/news/id/...",
  "publish_ts":   "2026-06-12T09:28:00",
  "ingestion_ts": "2026-06-12T09:30:15.123",
  "tickers":      ["2330.TW"],
  "tags":         []
}
```

- `tickers` 已用 L1 regex + L2 字典比對完成，下游不必重做
- `tags` 取值見「已知雜訊與處理」（`noise_intraday_tick` / `signal_target_price` / `signal_revenue` / `signal_announcement`）
- **盤中即時用 `ingestion_ts`，回測一律改用 processed 層的 `actionable_ts`**（stream 是低延遲通道，不保證 PIT 規則；日終由 storage 層補正）
- 消費端 tail 模式：記住 (檔名, byte offset)，跨日切檔重置 offset

---

## Data layout

```
data/
├── raw/
│   ├── cnyes/YYYY-MM-DD.json
│   ├── udn/YYYY-MM-DD.json
│   ├── ctee/YYYY-MM-DD.json
│   └── {source_id}/YYYY-MM-DD.json          ← 新來源同規則
├── processed/date=YYYY-MM-DD/data.parquet   ← Hive-style，DuckDB partition pruning
├── stream/YYYY-MM-DD.jsonl                  ← 盤中事件串流（下游介接點）
├── state/seen_keys.json                     ← 盤中去重狀態
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
| `[重大訊息]` | 官方公告（twse_announce 產生） | `signal_announcement` |

規則維護在 `scripts/watch_intraday.py` 的 `TAG_RULES`，新增規則時同步更新本表。

---

## 新增媒體來源 SOP

1. **有 RSS** → 在 `scripts/rss_sources.py` 的 `SOURCES` 註冊 `{source_id: {label, feeds}}`，跑 `python scripts/rss_sources.py <source_id>` 驗證即完成（main.py 與 watch_intraday 自動納入）
2. **只有 JSON API** → 仿 `scripts/cnyes.py` 寫獨立模組，輸出統一欄位：`source / category / title / summary / url / published_at`
3. **只有 HTML** → 仿 `scripts/ctee.py`，注意列表頁通常無時間戳（`published_at` 留空，靠 `ingestion_ts`）
4. 任何新來源都更新本文件「媒體來源總覽」的狀態表，並評估：延遲等級、是否轉載源（去重風險）、歷史回抓可行性

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

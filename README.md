# get-stock-news

![CI](https://github.com/how0531/get-stock-news/actions/workflows/ci.yml/badge.svg)

美日台股市新聞彙整與熱度量化系統。從台灣主流財經媒體爬取新聞，建立 PIT 正確的資料管線，量化個股熱度，協助判斷盤前重點。

## 兩個 Claude Skills

- **`skills/get-stock-NEWS/`** — 新聞彙整（抓取、儲存、目標價抽取）
- **`skills/stock-heat-model/`** — 熱度量化（評分、Tier 分級、veto、事後驗證）

詳細說明見各 SKILL.md。

## 資料來源

| 來源 | 方式 | 歷史回溯 | 狀態 |
|------|------|----------|------|
| 鉅亨網 cnyes.com | 公開 JSON API | ✅ 完整 | ✅ 已驗證 |
| 經濟日報 money.udn.com | sitemap 分週切片 | ✅ ~100% | ✅ 已驗證 |
| 工商時報 ctee.com.tw | 列表頁 HTML（publish_ts 取自 URL 日期） | ✅ sitemap | ✅ 已驗證 |
| 中央社 / 自由財經 / 科技新報 / ETtoday / 中時 / MoneyDJ / Yahoo股市 | RSS（`rss_sources.py` 註冊表） | ❌ | 🆕 待本機驗證 |
| TWSE / TPEx 重大訊息 | OpenAPI（官方第一手） | ❌ | 🆕 待本機驗證 |

完整來源清單（含延遲、轉載去重提醒、規劃中來源）見 [skills/get-stock-NEWS/SKILL.md](skills/get-stock-NEWS/SKILL.md)。

## 主要 Scripts

```
scripts/
├── cnyes.py / udn.py / ctee.py        # 即時抓取
├── rss_sources.py                      # RSS 通用爬蟲（多家媒體註冊表）
├── twse_announce.py                    # TWSE/TPEx 官方重大訊息
├── watch_intraday.py                   # 盤中監看 + 事件串流（推播由下游 skill 負責）
├── process_day.py                      # 日終 ETL：raw + stream -> processed Parquet
├── common.py                           # 共用：台北時區正規化 / 標題去重 / HTTP retry
├── healthcheck.py                      # 一條指令探測所有來源存活狀態
├── backfill_cnyes.py / backfill_udn.py # 歷史回抓
├── storage.py                          # PIT Parquet 儲存層（假日感知 actionable_ts）
├── extract_target_price.py             # Factset 目標價
├── build_stock_dict.py                 # 個股字典維護（--full-tw 全市場 ~1,800 檔）
└── quick_heat.py                       # 簡化版熱度（sanity check）
```

## 安裝與使用

```bash
pip install -r requirements.txt

# 抓最新新聞
PYTHONUTF8=1 python scripts/main.py

# 指定日期
PYTHONUTF8=1 python scripts/fetch_by_date.py 2026-05-13

# 盤中監看（事件串流寫入 data/stream/，供下游推播/大腦 skill 讀取）
PYTHONUTF8=1 python scripts/watch_intraday.py --interval 60 --market-hours-only --log-file data/state/watch.log

# 日終 ETL：raw + stream -> processed Parquet
PYTHONUTF8=1 python scripts/process_day.py

# 5 個月歷史背景抓取
nohup python scripts/backfill_cnyes.py > backfill_cnyes.log 2>&1 &
```

詳細的觸發詞、量化模型與三方專家共識見：
- [skills/get-stock-NEWS/SKILL.md](skills/get-stock-NEWS/SKILL.md)
- [skills/stock-heat-model/SKILL.md](skills/stock-heat-model/SKILL.md)

## 資料管線

```
抓取層 → PIT 儲存層 → 後處理 → 量化層
多媒體/官方公告 → process_day → Parquet（假日感知 PIT）→ 個股辨識 → 熱度 + Tier

盤中即時通道（低延遲，不走 Parquet）：
輪詢 → 去重 → 個股比對 → data/stream/*.jsonl → 下游 skill（資訊大腦 / 推播）
```

## 重要原則（三方專家共識）

- 「邊際變化」比「絕對熱度」重要
- 新聞是落後指標、籌碼是領先指標（必須整合）
- 盤前 07:30 + 盤後 14:30 雙報告
- `expert_repeat` 是**反向因子**（連推 3 天 → 反手做空）
- PIT 不可妥協（用 `actionable_ts` 不用 `publish_ts`）

## Copyright

新聞內容受版權保護。本專案為個人研究與量化分析使用，不重製全文。

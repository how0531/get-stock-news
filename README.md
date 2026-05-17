# get-stock-news

美日台股市新聞彙整與熱度量化系統。從台灣主流財經媒體爬取新聞，建立 PIT 正確的資料管線，量化個股熱度，協助判斷盤前重點。

## 兩個 Claude Skills

- **`skills/get-stock-NEWS/`** — 新聞彙整（抓取、儲存、目標價抽取）
- **`skills/stock-heat-model/`** — 熱度量化（評分、Tier 分級、veto、事後驗證）

詳細說明見各 SKILL.md。

## 資料來源

| 來源 | 方式 | 歷史回溯 |
|------|------|----------|
| 鉅亨網 cnyes.com | 公開 JSON API | ✅ 完整 |
| 經濟日報 money.udn.com | sitemap 分週切片 | ✅ ~100% |
| 工商時報 ctee.com.tw | HTML / WP REST API | ⚠️ TBD |

## 主要 Scripts

```
scripts/
├── cnyes.py / udn.py / ctee.py        # 即時抓取
├── backfill_cnyes.py / backfill_udn.py # 歷史回抓
├── storage.py                          # PIT Parquet 儲存層
├── extract_target_price.py             # Factset 目標價
├── build_stock_dict.py                 # 個股字典維護
└── quick_heat.py                       # 簡化版熱度（sanity check）
```

## 安裝與使用

```bash
pip install -r requirements.txt

# 抓最新新聞
PYTHONUTF8=1 python scripts/main.py

# 指定日期
PYTHONUTF8=1 python scripts/fetch_by_date.py 2026-05-13

# 5 個月歷史背景抓取
nohup python scripts/backfill_cnyes.py > backfill_cnyes.log 2>&1 &
```

詳細的觸發詞、量化模型與三方專家共識見：
- [skills/get-stock-NEWS/SKILL.md](skills/get-stock-NEWS/SKILL.md)
- [skills/stock-heat-model/SKILL.md](skills/stock-heat-model/SKILL.md)

## 資料管線

```
抓取層 → PIT 儲存層 → 後處理 → 量化層
cnyes/UDN/ctee  →  Parquet  →  個股辨識  →  熱度 + Tier
```

## 重要原則（三方專家共識）

- 「邊際變化」比「絕對熱度」重要
- 新聞是落後指標、籌碼是領先指標（必須整合）
- 盤前 07:30 + 盤後 14:30 雙報告
- `expert_repeat` 是**反向因子**（連推 3 天 → 反手做空）
- PIT 不可妥協（用 `actionable_ts` 不用 `publish_ts`）

## Copyright

新聞內容受版權保護。本專案為個人研究與量化分析使用，不重製全文。

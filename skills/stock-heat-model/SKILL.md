---
name: stock-heat-model
description: Quantify stock heat from aggregated news data — compute per-stock heat scores, identify hot stocks/sectors, classify signal Tiers (S/A/W/X), apply veto rules, and validate post-hoc returns. Use this skill whenever the user asks to rank/score stocks by news coverage, identify hot sectors, find trending stocks, evaluate investment column (投顧老師) signals, or build/extend the heat quantification pipeline. Triggers: "熱度排名", "重點個股", "熱門族群", "投顧老師點名", "今日重點股", "Top N 熱門", "哪些股票最熱", "市場熱度", "族群輪動", "Tier 分級". Depends on data produced by the `get-stock-NEWS` skill (raw / processed / target_price / stocks dict).
---

# stock-heat-model — 熱度量化模型

A skill for **scoring, ranking, and validating** stock heat from aggregated news data. Consumes data produced by `get-stock-NEWS` skill. Does NOT do news fetching itself.

---

## Scope

| Included | Not included |
|----------|--------------|
| 熱度公式（v2） | ❌ 新聞抓取（→ `get-stock-NEWS`） |
| 投顧專欄識別與權重 | ❌ 原始資料儲存 |
| 異常熱度偵測（z-score） | ❌ 目標價抽取 |
| Tier 分級（S/A/W/X） | ❌ 字典維護 |
| Veto 規則 | ❌ 來源新增 |
| 事後驗證（T+1/T+5/T+20） | |
| 籌碼面整合 | |

---

## When to use this skill

Trigger when user wants **scoring / ranking / signal analysis**：

- "熱度排名" / "今日重點股"
- "哪些股票最熱門" / "熱門族群"
- "投顧老師點名" / "名師推薦"
- "Top N 熱門股"
- "市場熱度" / "族群輪動"
- "Tier S 標的" / "進場名單"
- 任何「分析、計算、評分」相關問句

**不要觸發**（請改用 `get-stock-NEWS`）：
- 純抓新聞 / 列新聞清單
- 「5/13 的新聞」（列文章）
- 「Factset 目標價列表」（純抽取）

---

## 專案目標

> 透過新聞媒體量化個股熱度，協助判斷盤前重點。投顧名師專欄佔重要權重，但需配合籌碼面、技術面 veto 與事後驗證。

---

## 熱度模型 v2（三方專家評審結論）

### 三層結構
```
H(stock, date) = H_base × (1 + α·is_expert + β·is_event)
```
- **H_base** — 一般新聞客觀曝光
- **H_expert** — 投顧/名師專欄加權
- **H_event** — 法說/重訊催化

α、β 不要拍腦袋給定，累積 1-3 月資料後用 Lasso + purged k-fold CV 學出。

### 單篇文章貢獻分
```python
raw = log1p(title_mentions × 2 + summary_mentions × 1)   # log 壓尾
score = raw × (1 + α·is_expert + β·is_event)
# 注意：標題單獨點名 → 獨立 dummy factor，不要 +10 常數
```

### 異常熱度（領先訊號）
```python
H_z = (log1p(H_today) - rolling_mean_20d) / rolling_std_20d
H_accel = mean(H, 5d) / mean(H, 20d)
abnormal_signal = (H_z > 1.5) & (H_accel > 2)
```

20 日 + 5 日雙條件（不要單一 60 日視窗，動能太鈍）。

### 個股辨識多 ticker 合併

ADR 雙掛、TW/TWO 雙股別需 canonical 化：
```python
# 範例 mapping
2330.TW <- 2330.TWO, TSM, TSM-US
GOOGL   <- GOOG
2317.TW <- 2317.TWO
```
否則同一篇新聞會被同一檔股票算多次。

---

## 投顧專欄識別與權重

### 初始 prior（後續 Lasso 校正）

| 媒體 | 專欄 | 權重 | 訊號特性 |
|------|------|-----|---------|
| 工商時報 | 名家觀點 | ×3 | 產業老兵深度文（最強） |
| 鉅亨網 | 鉅亨主筆 | ×3 | 總經類 |
| UDN | 名家觀點 | ×3 | 與券商合作 |
| 工商時報 | 台股逐洞賽 | ×3 | 流量大、alpha 衰減快 |
| 鉅亨網 | 達人觀點 | ×2 | 短線題材 |
| — | 一般新聞 | ×1 | baseline |

### 識別特徵
1. URL pattern：`/columns/`, `/specialty_column/`, `/column/`
2. category 含「專欄」「名家」「達人」「主筆」
3. 內文署名「文／XXX」、「分析師：XXX」
4. 標題關鍵字「逐洞賽」「名家」「達人解盤」

---

## 子指標（重要：方向別搞錯）

| 指標 | 方向 | 用法 |
|------|------|------|
| **expert_count**（當日被幾位老師點名） | ➕ 加分 | ≥3 位 + 籌碼共振 = 強訊號 |
| **expert_repeat**（同老師連續推薦天數） | ➖ **反向** | 連推 3 天 → 反手做空候選 |
| **cross_media**（跨媒體同日點名） | ➕ 加分 | 須先做轉載去重 |
| **first_mention**（30 日首次出現） | ➕ **最強** | 隔日勝率最高 |

> ⚠️ **動能交易者實證**：first_mention 隔日勝率 55%，連 3 天點名隔日做多勝率只剩 4 成，第 4 天反手放空勝率 60%。

---

## Tier 分級

```
🌟 Tier S（最高優先進場池）
   first_mention = True
   AND H_z > 1.5
   AND 法人 5 日連續買超
   AND 股價站上 20MA
   AND NOT veto

📊 Tier A（觀察池）
   H_z > 1.5
   AND 法人單方買超
   AND NOT veto

⚠️ Tier W（警示池，反手做空候選）
   expert_repeat ≥ 3
   OR veto 觸發
   OR 月線下彎 + 漲幅 > 30% + 名師合唱

🗑️ Tier X（排除）
   流動性過低 / 近期除權息 / 內容重複
```

---

## Veto 規則（必過濾，動能交易者重點）

```python
veto = (
    (price_pct_from_60d_low > 40%) &   # 已大漲
    (margin_weekly_change > 10%) &     # 融資週增
    (expert_count_5d >= 3)             # 老師大合唱
)
# 觸發 = 教科書級主力出貨組合
```

加碼提醒：
- ⚠️ 月線下彎 + 已漲 30%+ + 同週 3 家媒體點名 → 強烈反手訊號
- ⚠️ 除權息前兩週名師突然點名高殖利率股 → 貼息高機率

---

## 目標價變動整合（hard signal）

**獨立 channel，不混進新聞熱度池**（避免被淹沒）：

```python
TP 動能 = 過去 7/30 天 change_pct 加權平均
       + (#raise - #lower)
```

### 與專欄熱度對沖
| 組合 | 解讀 |
|------|------|
| 投顧熱 + TP 持平/下調 | ⚠️ 出貨警示 |
| 投顧熱 + TP **上調** | 🌟 基本面真改善（最強多頭） |
| TP 上調 + 籌碼買超 + first_mention | 🌟 Tier S 強候選 |

---

## 必要的籌碼面整合（外部資料源）

新聞單獨打 20 分，加上籌碼面才到 70 分。**未整合不要上線**：

| 資料 | 來源 | 用途 |
|------|------|------|
| 三大法人買賣超 | TWSE/TPEx 公開 | Tier S/A 必要條件 |
| 融資融券變化 | TWSE 公開 | veto 規則 |
| 個股價量 + 20/60MA | yfinance / TWSE | Tier S 技術濾網 |
| 借券與鉅額交易 | TWSE 公開 | 進階 veto |

---

## 事後驗證（T+1/T+5/T+20）

每個 Tier S/A 訊號發布後追蹤：
- T+1 報酬 vs 同期大盤
- T+5 報酬 vs 同期大盤
- T+20 報酬 vs 同期大盤

**沒有這層回饋，永遠停在摘要工具，無法進化成決策系統**（財金專家強調）。

每月產出：
- 各專欄的命中率（高的權重拉高、業配寫手歸零）
- Tier S / Tier A 的平均超額報酬
- veto 規則的避錯率

---

## PIT 正確性（不可妥協）

從 `get-stock-NEWS` 載入資料時：
- 必須用 `actionable_ts` 而非 `publish_ts`
- 跨日聚合（如 expert_count_5d）一律 `rolling(closed='left')`
- 跨表 join 用 `storage.asof_merge()`（backward only）

### 致命陷阱
| 陷阱 | 解法 |
|------|------|
| 「同週 ≥3 老師」回看 | `rolling(past 5 trading days, closed='left')` |
| Factset 速報盤後 20:15 發 | actionable_ts = 次一工作日 09:00 |
| 名師專欄隔日見報 | actionable_ts 至少 +1 bar |
| 同篇多家轉載 | content hash 去重 |
| 下市股 | 必須回補避免生存者偏誤 |

---

## 預期績效（量化專家心理建設）

- 新聞/attention 因子典型 IC：月頻 0.02-0.05、日頻 0.01-0.03
- 半衰期：3-10 個交易日
- **不要期待 IC > 0.1**
- 真正 alpha 來自因子組合（新聞 × 籌碼 × 動能）的非線性互動

---

## 雙報告產出（推薦時程）

| 時段 | 內容 | 對象 |
|------|------|------|
| **盤後 16:00** | 三大法人 + 當日新聞 + 異常訊號 + Tier 排行 | 隔日選股初稿 |
| **盤前 07:30** | 隔夜美股 + 國際新聞 + 台灣晨間頭條 + Tier 修正 | 開盤前最終確認 |

不要做盤前 08:00 — 太晚（已過盤前競價）。

---

## 必須做 vs 必須避免（三方專家共識）

### 必做
1. 「邊際變化」比「絕對熱度」重要
2. 整合籌碼面（新聞是落後指標）
3. 雙時段報告
4. 事後驗證骨架
5. 雜訊分類保留，不要濾掉

### 必避
1. ❌ 「+10 絕對常數」、線性加總
2. ❌ expert_repeat 當加分項（是反向因子！）
3. ❌ 60 日單一視窗（動能太鈍）
4. ❌ 拍腦袋固定 multiplier（要 Lasso 學）
5. ❌ 「重點股 Top 10」「熱門族群排行」做為主要產出（券商日報都有）

---

## 開發階段

| 階段 | 內容 | 狀態 |
|------|------|------|
| ✅ 個股字典 | 364 檔 + 別名 | 完成 |
| 🟡 v1 簡化熱度 | `quick_heat.py`（標題×2+摘要×1） | 有 bug 修中 |
| ⏳ 多 ticker canonical 合併 | 2330.TW + 2330.TWO + TSM → 同一檔 | 待做 |
| ⏳ 投顧專欄識別 | URL pattern + 作者抽取 | 待做 |
| ⏳ v2 完整熱度 | log1p + z-score + 5 日加速度 | 累積 1 個月資料後 |
| ⏳ Tier 分級 + veto | 需先有籌碼面 | 待派 |
| ⏳ 籌碼面整合 | TWSE 三大法人 + 融資融券 | 待派 |
| ⏳ 事後驗證 | T+1/T+5/T+20 報酬 | 待派 |
| ⏳ Lasso 權重學習 | 投顧權重從 prior 改 data-driven | 累積 3 個月後 |

---

## 依賴

- `get-stock-NEWS` skill 產出的：
  - `data/processed/date=*/data.parquet`
  - `data/target_price/YYYY-MM-DD.json`
  - `data/stocks/*.json`
  - `scripts/storage.py`（load/query）
- 外部資料（待整合）：
  - TWSE 三大法人 / 融資融券
  - yfinance 個股價量

---

## Copyright

本 skill 為個人量化研究使用，所有計算結果不可作為投資建議。

# 模組 5｜資料工程：去重、時區、PIT 儲存（講師教學筆記）

> 總長約 90 分鐘 / 7 堂。全課技術含金量最高的模組——「玩具爬蟲」與「可信系統」的分水嶺。
> 賣點句：「這個模組的內容，是你在別的爬蟲課買不到的。」

## 教學目標

- 處理多來源資料的三大髒問題：時區混亂、重複轉載、格式不一
- 實作兩層去重（完全同標題／改寫轉載）
- 理解並實作 Point-in-Time 正確性：`actionable_ts` vs `publish_ts`
- 會用 Parquet 建立可查詢的儲存層

---

## 5-1 髒資料的真面目（10'）

**Demo**：秀一份真實抓取結果，同一事件出現 4 次：
- 中央社原稿 → Yahoo 轉載（URL 不同）→ 自由轉載（標題改兩個字）→ ETtoday 改寫標題但內文全同
1. 如果不去重：熱度模型會把 1 件事算成 4 件 → 假訊號
2. 如果亂去重：把兩家「獨立報導同一事件」也併掉 → 失去 cross_media 訊號
3. 本模組任務：**該併的併，該留的留，被併掉的記帳**（`also_reported_by`）

## 5-2 時區正規化（10'）

**Demo**：`scripts/common.py:21-39` 的 `to_taipei_iso()`
1. 三種輸入亂象：epoch 秒數（cnyes）、RFC822 字串（RSS）、無時區 naive 字串（HTML meta）
2. 統一規則：全部轉 `Asia/Taipei` ISO；naive 視為台北時間、aware 做換算
3. 為什麼重要：美股新聞常帶 UTC 或美東時間，不轉的話「昨晚的新聞」會被算成「今天的」——直接污染回測

## 5-3 Tier 1 去重：標題完全比對（12'）

**Demo**：`scripts/common.py:46-48` 的 `norm_title()`
1. 正規化：去標點空白、轉小寫——`\W` 在 Python3 不會誤刪中文（帶看程式註解）
2. 正規化後完全相同 → 視為同文轉載，**保留最早 `publish_ts` 那筆**
3. 被併掉的來源記入 `also_reported_by`（Demo `process_day.py` 的 `_merge_exact_dupes`）
4. 三個地方都套用同一套邏輯：`watch_intraday` / `main` / `process_day`——共用函式的好處

## 5-4 Tier 2 去重：改寫轉載偵測（14'）

**問題**：Yahoo 常改寫標題再引用他家全文 → Tier 1 抓不到
**Demo**：`process_day.py` 的 `_merge_reprints`
1. 指紋法：取 `content`/`summary` 正規化後**前 60 字**作指紋
2. 兩條件：指紋相同 + `publish_ts` 相距 48 小時內 → 同事件轉載，保留最早一筆
3. 防呆：指紋需 ≥60 字才生效（太短會誤併）→ 所以建議開 `fetch_content`
4. 邊界講清楚：「各家記者獨立寫同一事件」不會被併——那是語意層聚合，屬進階題（誠實劃界，也埋進階課伏筆）

## 5-5 PIT：回測不騙自己的關鍵（14'）★全課最重要觀念

**講稿大綱**
1. 情境題開場：「一則新聞 14:35 發布（收盤後），你回測時把它算進當天的訊號——結果回測賺爛了，實盤卻賠錢。哪裡錯了？」
2. 答案：你用了**當時根本拿不到的資訊**做決策 → Look-ahead bias
3. 定義 PIT（Point-in-Time）：任何時點的資料庫狀態，必須等於「當時真實可得」的狀態
4. 解法：每筆資料存兩個時間
   - `publish_ts`：新聞何時發布
   - `actionable_ts`：**你最早能拿它行動的時點**（下一個交易時段）
5. 課程鐵律（README 原則）：「PIT 不可妥協——回測一律用 `actionable_ts`」

## 5-6 actionable_ts 假日感知（12'）

**Demo**：`scripts/storage.py` + `data/calendar/tw_holidays.json`
1. 規則推演（互動題形式）：
   - 週三 10:00 發布 → 盤中，actionable 當下
   - 週三 20:00 發布 → 收盤後，actionable = 週四開盤
   - 週五 20:00 發布 → actionable = 週一開盤
   - 週五 20:00 且週一是國定假日 → actionable = 週二開盤 ← **假日感知**
2. 帶看假日行事曆 JSON 與 storage.py 對應邏輯
3. 提醒：台股還有颱風假、補班日——行事曆檔案要每年維護

## 5-7 Parquet 儲存層（12'）

1. 為什麼不用 CSV：型別會亂、中文編碼坑、大檔查詢慢；為什麼還不用資料庫：單人系統 Parquet 就夠，零維運
2. **Demo**：跑 `process_day.py` 產出 Parquet → 用 pandas 讀回來查詢：
   ```python
   import pandas as pd
   df = pd.read_parquet("data/processed/2026-05-13.parquet")
   df[df["tickers"].str.len() > 0].head()
   ```
3. 帶看 `scripts/test_storage.py`：儲存層有測試保護——「會壞的是網站，不能壞的是你的儲存層」

---

## 作業 5

兩小題：
1. 文字題：用自己的話說明「用 `publish_ts` 回測」會犯什麼錯，舉一個具體時間的例子。
2. 實作題：用 `storage.py` 寫入一天的資料再讀回，驗證筆數一致、`actionable_ts` 正確。
**評分標準**：文字題必須提到 look-ahead bias（或等義描述）；實作題貼讀回結果截圖。

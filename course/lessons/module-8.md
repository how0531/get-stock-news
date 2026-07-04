# 模組 8｜自動化實戰與結業專題（講師教學筆記）

> 總長約 75 分鐘 / 6 堂。結業模組：把前 7 個模組串成每天自動跑的系統。
> 8-4 的成果畫面就是銷售頁主視覺——錄的時候多留幾個乾淨的螢幕截圖。

## 教學目標

- 跑起盤中監看（輪詢 → 去重 → 事件串流）
- 建立日終 ETL 與排程，全流程無人值守
- 每天早上自動產出盤前報告
- 學會系統維護心法，並完成結業專題

---

## 8-1 盤中監看：事件串流（14'）

**Demo**：`scripts/watch_intraday.py`
```bash
PYTHONUTF8=1 python scripts/watch_intraday.py --interval 60 --market-hours-only --log-file data/state/watch.log
```
1. 架構：輪詢（60 秒）→ 記憶體去重（含 SEEN_CAP 上限，講為什麼要防記憶體無限長大）→ 個股比對 → 寫 `data/stream/*.jsonl`
2. 為什麼即時通道不走 Parquet：低延遲需求 → JSONL 逐行 append，下游（推播/大腦）逐行讀
3. `--market-hours-only`：只在交易時段輪詢——對媒體伺服器禮貌，也省自己資源
4. 現場讓它跑 5 分鐘，tail 看 stream 檔長出來

## 8-2 日終 ETL（12'）

**Demo**：`scripts/process_day.py`
1. 定位：每天收盤後把 raw + stream 合併 → 兩層去重 → tickers 標註 → processed Parquet
2. 白板圖複習雙通道架構：
   ```
   盤中：輪詢 → stream JSONL（快、粗）
   日終：raw + stream → process_day → Parquet（慢、乾淨）
   ```
3. 觀念：**即時通道求快、批次通道求對**——兩者並存是業界標準架構（Lambda 架構的極簡版）

## 8-3 排程自動化（12'）

雙平台都示範：
1. **Mac/Linux cron**：
   ```
   # 平日 08:30 抓早盤前新聞
   30 8 * * 1-5 cd /path/to/get-stock-news && PYTHONUTF8=1 python scripts/main.py
   # 平日 15:00 日終 ETL
   0 15 * * 1-5 cd /path/to/get-stock-news && PYTHONUTF8=1 python scripts/process_day.py
   ```
2. **Windows 工作排程器**：GUI 全程示範（觸發程序 → 動作 → 條件），這段對次要受眾（投顧會員）最重要
3. 提醒：電腦要開著才會跑 → 順帶 30 秒帶過「丟上雲端小主機/樹莓派」的選項（進階路線圖）

## 8-4 產出盤前報告（14'）★成果堂＝行銷素材

**Demo**：整合腳本，把三份資料拼成一頁報告：
1. 內容組成：
   - 昨日收盤後～今晨的新增新聞（模組 2–4 產出）
   - Top 10 熱度股 + 對應新聞標題與連結（模組 7 quick_heat）
   - 今日官方重大訊息摘要（模組 4）
   - 目標價變動清單（7-3 產出）
2. 輸出格式：Markdown 檔（可再教 30 秒：用 LINE Notify / Telegram bot 推到手機——留鉤子給進階課）
3. 對齊 README 節奏：盤前 07:30 一份、盤後 14:30 一份
4. 完成儀式：「從今天起，每天早上你的電腦比新聞 App 先開工」

## 8-5 維護心法（10'）

1. 三種故障分級與對策：
   - 網路抖動 → `request_get` 重試已自動處理
   - 來源暫時異常 → healthcheck 巡檢，等或關
   - 網站改版 → 開 `data/site_maps/{source}.json` 對照修，改 `SOURCES` 註冊表或該來源 script
2. 維運節奏建議：每週 healthcheck 一次、每季更新股票字典、每年更新假日行事曆
3. CI 的角色：帶看 `.github/workflows/ci.yml`——改壞了測試會擋你（`test_collect.py` / `test_storage.py` / `test_heat.py`）

## 8-6 結業專題與延伸路線圖（12'）

**結業專題**（二選一必交 + 必交項）：
- 必交：連續 3 天自動產出盤前報告的截圖
- 二選一：(a) 新增一個新聞來源並通過 healthcheck；(b) 為報告加一個新欄位或推播通知
- 繳交至 Discord `#作品展示`，通過者發結業證書 + 進階學員名單

**延伸路線圖**（誠實標註哪些是進階課／自行研究）：
1. 推播整合：Telegram / LINE bot（下游 skill 架構已預留 stream 介面）
2. 熱度 v2 完整多因子模型 + 籌碼面整合（進階課主軸）
3. MOPS 秒級重大訊息（反爬較強，研究型題目）
4. LLM 新聞摘要與語意事件聚合（模組 5-4 留的伏筆）
5. 週刊/外電來源、PTT 散戶情緒反向指標

**收尾講稿**：回放 1-1 的管線圖——「八週前這是一張圖，現在它在你的電腦上每天自己跑。」

---

## 作業（結業專題評分標準）

| 項目 | 標準 |
|------|------|
| 盤前報告 ×3 天 | 日期連續（跳過假日可）、含熱度 Top N 與新聞連結 |
| 自訂擴充 | 能跑、有 diff、口頭或文字說明設計 |
| 加分 | 分享到社群並 tag 課程（自願，行銷互惠：抽介紹進階課折扣） |

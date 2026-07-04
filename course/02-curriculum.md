# 完整課綱（Curriculum）

> 8 模組 / 約 45 堂 / 總長 8–10 小時。每堂 8–15 分鐘。
> 「對應程式碼」欄指向本 repo 的實際檔案——錄課時直接開這些檔案 demo。

## 模組 1｜導論與環境建置（約 60 分鐘，6 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 1-1 | 課程地圖：我們要蓋一條什麼樣的管線 | 10' | `README.md` 資料管線圖 |
| 1-2 | 為什麼散戶需要自己的新聞系統（新聞是落後指標的正確用法） | 10' | — |
| 1-3 | 法遵與著作權：能抓什麼、不能做什麼 | 12' | — |
| 1-4 | 環境建置（Windows）：Python、venv、pip、VS Code | 12' | `requirements.txt` |
| 1-5 | 環境建置（Mac）+ 專案導覽 | 10' | repo 全覽 |
| 1-6 | 跑起來！第一次執行 `main.py` | 8' | `scripts/main.py` |

**作業 1**：成功執行 `python scripts/main.py`，截圖輸出結果貼到 Discord。

## 模組 2｜第一支新聞 API：鉅亨網 JSON API（約 70 分鐘，6 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 2-1 | 什麼是「公開 JSON API」：用瀏覽器開發者工具找到它 | 12' | — |
| 2-2 | requests 入門：headers、Referer、為什麼會被擋 | 12' | `scripts/cnyes.py` |
| 2-3 | 解析 JSON 回應：標題、時間、分類、內文 | 12' | `scripts/cnyes.py` |
| 2-4 | 分頁與日期範圍：抓歷史新聞 | 12' | `scripts/backfill_cnyes.py` |
| 2-5 | HTTP 重試與指數退避：讓程式禁得起網路抖動 | 10' | `scripts/common.py` |
| 2-6 | 實戰：抓出指定日期的所有台股新聞 | 12' | `scripts/fetch_by_date.py` |

**作業 2**：用 cnyes API 抓出上週某一天的美股新聞，輸出前 20 則標題。

## 模組 3｜RSS 與 sitemap：一次接入 10 家媒體（約 80 分鐘，7 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 3-1 | RSS 是什麼：最被低估的資料源 | 10' | — |
| 3-2 | 註冊表模式：寫一個爬蟲，接無限家媒體 | 14' | `scripts/rss_sources.py` |
| 3-3 | 逐家導覽：中央社/自由/科技新報/ETtoday/中時/MoneyDJ/Yahoo股市的特性與陷阱 | 12' | `scripts/rss_sources.py`、`data/site_maps/` |
| 3-4 | sitemap 挖歷史：經濟日報分週切片實戰 | 12' | `scripts/udn.py`、`scripts/backfill_udn.py` |
| 3-5 | 沒有 RSS 怎麼辦：工商時報列表頁 HTML 解析 | 12' | `scripts/ctee.py`、`scripts/backfill_ctee.py` |
| 3-6 | healthcheck：一條指令確認所有來源還活著 | 10' | `scripts/healthcheck.py` |
| 3-7 | 來源結構地圖：讓維護有 SOP | 10' | `scripts/site_map.py`、`data/site_maps/_schema.json` |

**作業 3**：在 `rss_sources.py` 註冊表新增一個你自選的 RSS 來源，跑通 healthcheck。

## 模組 4｜官方第一手：TWSE/TPEx 重大訊息（約 45 分鐘，4 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 4-1 | 為什麼官方公告比媒體快又準：資訊鏈的源頭 | 10' | — |
| 4-2 | TWSE OpenAPI 實戰：上市公司當日重大訊息 | 12' | `scripts/twse_announce.py` |
| 4-3 | TPEx OpenAPI：上櫃公司重大訊息 | 10' | `scripts/twse_announce.py` |
| 4-4 | 官方資料與媒體新聞的互補：誰先誰後、怎麼合流 | 12' | — |

**作業 4**：抓出今天所有上市櫃重大訊息，找出其中「處分資產」相關的公告。

## 模組 5｜資料工程：去重、時區、PIT 儲存（約 90 分鐘，7 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 5-1 | 髒資料的真面目：同一則新聞出現 4 次的原因 | 10' | — |
| 5-2 | 時區正規化：全部轉成台北時間 ISO 格式 | 10' | `scripts/common.py` |
| 5-3 | Tier 1 去重：標題正規化與完全比對 | 12' | `scripts/common.py`、`scripts/process_day.py` |
| 5-4 | Tier 2 去重：改寫標題的轉載偵測（內文指紋） | 14' | `scripts/process_day.py` |
| 5-5 | PIT（Point-in-Time）：回測不騙自己的關鍵觀念 | 14' | `scripts/storage.py` |
| 5-6 | `actionable_ts` 與假日感知：週五晚上的新聞算哪天的 | 12' | `scripts/storage.py`、`data/calendar/tw_holidays.json` |
| 5-7 | Parquet 儲存層實作與查詢 | 12' | `scripts/storage.py`、`scripts/test_storage.py` |

**作業 5**：說明「用 `publish_ts` 回測」會犯什麼錯，並用 `storage.py` 寫入一天的資料再讀回來驗證。

## 模組 6｜個股辨識：股票字典與新聞對應（約 50 分鐘，4 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 6-1 | 從「一堆新聞」到「哪些股票被提到」：問題定義 | 10' | — |
| 6-2 | 建立全市場股票字典（台股 ~1,800 檔 + 美日股） | 14' | `scripts/build_stock_dict.py`、`data/stocks/` |
| 6-3 | 比對的陷阱：同名公司、簡稱、產品名撞名 | 14' | `scripts/build_stock_dict.py` |
| 6-4 | 把 tickers 標進每一筆新聞：管線整合 | 12' | `scripts/process_day.py` |

**作業 6**：找出一個「容易誤判」的股票簡稱，說明字典要怎麼處理它。

## 模組 7｜熱度量化入門（約 70 分鐘，6 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 7-1 | 熱度的定義：邊際變化比絕對數量重要 | 12' | `skills/stock-heat-model/SKILL.md` |
| 7-2 | v1 快速熱度：標題×2＋摘要×1＋雜訊過濾 | 12' | `skills/stock-heat-model/scripts/quick_heat.py` |
| 7-3 | 券商目標價訊號抽取：Factset 速報與 regex | 14' | `skills/stock-heat-model/scripts/extract_target_price.py` |
| 7-4 | Tier 分級思想：S/A/W/X 與 veto 規則 | 12' | `skills/stock-heat-model/SKILL.md` |
| 7-5 | 反直覺因子：為什麼「連推 3 天」是反向訊號 | 10' | `skills/stock-heat-model/SKILL.md` |
| 7-6 | 事後驗證：T+1/T+5/T+20 報酬檢驗的觀念 | 10' | — |

**作業 7**：跑 `quick_heat.py` 算出某一天的 Top 10 熱門股，並寫下你觀察到的一個雜訊來源。

> ⚠️ 本模組錄製時嚴守：只講「方法與程式」，不對任何個股做買賣評價。見法遵文件。

## 模組 8｜自動化實戰與結業專題（約 75 分鐘，6 堂）

| # | 堂名 | 長度 | 對應程式碼 |
|---|------|------|-----------|
| 8-1 | 盤中監看：輪詢、去重、事件串流 | 14' | `scripts/watch_intraday.py` |
| 8-2 | 日終 ETL：raw + stream → processed Parquet | 12' | `scripts/process_day.py` |
| 8-3 | 排程自動化：cron（Mac/Linux）與工作排程器（Windows） | 12' | — |
| 8-4 | 產出盤前報告：7:30 自動生成當日重點 | 14' | 整合前述模組 |
| 8-5 | 維護心法：來源掛了怎麼辦、改版怎麼修 | 10' | `scripts/healthcheck.py`、`data/site_maps/` |
| 8-6 | 結業專題說明 + 延伸路線圖（推播、籌碼面、AI 摘要） | 12' | — |

**結業專題**：交出（a）連續 3 天自動產出的盤前報告截圖，（b）一項自訂擴充（新來源／新欄位／推播通知擇一）。完成者發結業證書 + 加入進階學員名單。

---

## 錄製優先順序建議

1. 先錄模組 2（最能剪成免費試看與行銷素材——「10 分鐘抓下今天所有台股新聞」）
2. 再錄模組 1（開賣必備）與模組 8-4（結業成果 demo，銷售頁影片用）
3. 其餘照順序錄

## 免費試看堂（開賣頁公開）

- 1-1 課程地圖
- 2-1 用開發者工具找到公開 API（最強鉤子）
- 7-1 熱度的定義（展現專業深度，投顧合作方可轉發）

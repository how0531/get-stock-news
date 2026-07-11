# 模組 3｜RSS 與 sitemap：一次接入 10 家媒體（講師教學筆記）

> 總長約 80 分鐘 / 7 堂。核心賣點：**註冊表模式**——寫一個爬蟲，接無限家媒體。

## 教學目標

- 理解 RSS / sitemap / 列表頁 HTML 三種資料取得方式的適用場景
- 掌握「註冊表模式」：新增媒體來源只要加一筆設定，不用寫新爬蟲
- 學會用 healthcheck 維運多來源系統
- 了解各家台灣財經媒體的特性與雜訊

---

## 3-1 RSS：最被低估的資料源（10'）

1. RSS 是網站「主動提供」的機器可讀格式——比爬 HTML 正當且穩定
2. Demo：瀏覽器直接開一個 RSS feed，看 XML 結構（title/link/pubDate）
3. `feedparser` 套件：三行讀完一個 feed
4. RSS 的限制：只有近期文章（無歷史）、延遲約 5–15 分鐘 → 引出「即時用 RSS、歷史用 sitemap/API」的分工

## 3-2 註冊表模式（14'）★本模組核心

**Demo**：打開 `scripts/rss_sources.py`
1. 先看 `SOURCES` 註冊表：每家媒體就是一筆設定（source_id、feed URL、分類）
2. 再看通用 fetch 函式：一支程式吃所有註冊表項目
3. **現場示範新增一個來源**：加一筆 dict → 跑起來 → 完成。「這就是好架構的威力：擴充成本趨近於零」
4. 設計原則：**資料（哪些來源）與邏輯（怎麼抓）分離**

## 3-3 逐家媒體導覽（12'）

照 `skills/get-stock-NEWS/SKILL.md` 的 inventory 表講，每家 90 秒：

| 媒體 | 記憶點 |
|------|--------|
| 中央社 cna | 權威通訊社，政策/總經第一手；**它的稿會被別家轉載**（模組 5 去重的伏筆） |
| 自由財經 ltn | 綜合財經 |
| 科技新報 technews | 半導體/AI 供應鏈深度好，但全站 feed 會混科普文 |
| ETtoday | 量大、雜訊比高 → 「量大不是優點，訊噪比才是」 |
| 中時 chinatimes | 與工商時報同集團，可互補 |
| MoneyDJ | 法人圈常用，個股新聞密度高 |
| Yahoo股市 | 聚合轉載源，**必須去重後才能用** |

觀念：feed 一律選「財經分類」而非全站；分類內仍有房產/理財教學等非個股內容——**過濾是下游的事**，抓取層不擅自刪內容。

## 3-4 sitemap 挖歷史：經濟日報（12'）

1. 問題：RSS 只有近期，想要 12 個月歷史怎麼辦？
2. 答案藏在 sitemap：Demo 開 `money.udn.com` 的 `/sitemap/staticmap/1001T{YYYYMM}W{N}`——按「年月＋週」切片的文章清單
3. 打開 `scripts/udn.py`（即時 RSS）與 `scripts/backfill_udn.py`（sitemap 回補）對照：同一家媒體、兩條路
4. 泛化：**幾乎所有正規新聞網站都有 sitemap**（robots.txt 裡找），這是回補歷史的萬用鑰匙

## 3-5 沒有 RSS 怎麼辦：工商時報 HTML（12'）

1. 工商時報：無公開 RSS、WP API 已關 404 → 最後手段：列表頁 HTML
2. **Demo**：`scripts/ctee.py`
   - BeautifulSoup 解析列表頁
   - 聰明技巧：URL 是 `/news/{YYYYMMDD}...`——**發布日期就嵌在網址裡**，不用進內頁就有 publish_ts
   - `fetch_content=True` 才進內頁抓全文與 `<meta pubdate>` 精確時間
3. 觀念：HTML 爬蟲的脆弱性（改版就掛）→ 所以才需要 3-6 的 healthcheck

## 3-6 healthcheck：一條指令巡檢所有來源（10'）

**Demo**
```bash
PYTHONUTF8=1 python scripts/healthcheck.py
```
1. 逐來源列出 OK / FAIL 與抓到的樣本數
2. 維運習慣：每週跑一次；來源掛了 → 先看是暫時性（網路）還是永久性（改版/搬家）
3. 改 feed URL 只要動 `rss_sources.py` 的 `SOURCES` 註冊表（呼應 3-2）

## 3-7 來源結構地圖：讓維護有 SOP（10'）

1. `data/site_maps/{source_id}.json`：每個來源一份「結構地圖」——入口、端點、選擇器、驗證狀態
2. Demo：開 `data/site_maps/cnyes.json` 與 `_schema.json`
3. 觀念：把「當初怎麼研究這個網站」文件化，半年後改版才修得快；也方便多人協作

---

## 作業 3

在 `rss_sources.py` 的 `SOURCES` 註冊表新增一個自選 RSS 來源（例如某產業媒體），跑 `healthcheck.py` 確認為 OK，貼設定 diff + healthcheck 輸出截圖。
**評分標準**：新來源能抓到至少 1 筆、`published_at` 為台北時間 ISO。
**常見卡關**：feed URL 貼成網頁版網址（不是 XML）、來源分類選了全站 feed。

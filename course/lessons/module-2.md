# 模組 2｜第一支新聞 API：鉅亨網 JSON API（講師教學筆記）

> 總長約 70 分鐘 / 6 堂。本模組是全課「aha moment」密度最高的一段——2-1 要剪成免費試看。

## 教學目標

- 學會用瀏覽器開發者工具找出網站背後的 JSON API
- 掌握 `requests` + headers（User-Agent / Referer / Origin）的實務
- 能抓即時新聞與指定日期的歷史新聞
- 理解重試與指數退避

---

## 2-1 用開發者工具找到公開 API（12'）★免費試看堂

**講稿大綱**
1. 鉤子：「爬蟲最高境界是不用爬——很多網站自己就有 API，只是沒寫在文件上」
2. **Demo（本課精華）**：
   - 開 news.cnyes.com → F12 → Network → 篩 XHR/Fetch → 重新整理
   - 找到 `api.cnyes.com/media/api/v1/newslist/category/tw_stock` → 點開 Response，看到乾淨的 JSON
   - 「網頁上看到的每一則新聞，都在這包 JSON 裡——我們直接跟這個端點拿」
3. 觀念：HTML 爬蟲（脆弱、要解析）vs JSON API（穩定、結構化）。能用 API 就不要碰 HTML

## 2-2 requests 入門與「為什麼會被擋」（12'）

**Demo**：現場寫最小版本，再對照 `scripts/cnyes.py`
```python
import requests
url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"
r = requests.get(url, params={"limit": 5, "page": 1})
print(r.status_code)   # 可能 403！
```
1. 故意先不帶 headers 讓它失敗 → 引出重點：
   ```python
   HEADERS = {
       "User-Agent": "Mozilla/5.0",
       "Origin": "https://news.cnyes.com",
       "Referer": "https://news.cnyes.com/",
   }
   ```
2. 解釋：伺服器用 Referer/Origin 判斷請求是否來自自家網頁；補上就好，這不是破解，是禮貌地表明來意
3. 打開 `scripts/cnyes.py:12-17`，對照課程程式碼的 `BASE` 與 `HEADERS`

## 2-3 解析 JSON 回應（12'）

**Demo**：逐層拆 `resp.json()["items"]["data"]`
1. 每筆 item 的關鍵欄位：`title`、`summary`、`publishAt`（epoch）、`newsId`、`content`（已含全文 HTML）
2. 兩個轉換（對照 `scripts/cnyes.py:44-56`）：
   - `publishAt` 是 epoch 秒數 → `to_taipei_iso()` 轉台北時間（模組 5 詳講）
   - `content` 是 HTML → `html_to_text()` 轉純文字
3. 組出標準化字典：`source / category / title / summary / content / url / published_at`
4. 強調設計原則：**每個來源的 fetch() 都輸出同一套欄位**——下游才接得起來

## 2-4 分頁與日期範圍：抓歷史（12'）

1. `params={"limit": 30, "page": 2}` → 翻頁
2. cnyes API 支援日期範圍參數 → 這是它成為「歷史回補主力來源」的原因
3. **Demo**：打開 `scripts/backfill_cnyes.py`，帶看主迴圈：逐日抓、寫檔、sleep 節流
4. 跑一小段：
   ```bash
   PYTHONUTF8=1 python scripts/fetch_by_date.py 2026-05-13
   ```

## 2-5 HTTP 重試與指數退避（10'）

1. 情境：抓 150 天歷史，中途第 87 天網路抖一下，整個程式死掉 → 不可接受
2. **Demo**：`scripts/common.py:51-70` 的 `request_get()`
   - `raise_for_status()`、retry 迴圈、`backoff * (2**attempt)`（2 秒 → 4 秒）
3. 觀念：指數退避是業界標準——失敗越多次等越久，給對方伺服器喘息
4. 課程所有爬蟲都走這個函式 → 寫一次，處處受益（DRY）

## 2-6 實戰：指定日期的所有台股新聞（12'）

**Demo**：完整跑一次
```bash
PYTHONUTF8=1 python scripts/fetch_by_date.py 2026-05-13
```
1. 帶看輸出檔（`data/raw/` 下的 JSON），欄位一一對應 2-3 教的標準化格式
2. 回顧本模組：找 API → 帶對 headers → 解析 → 分頁 → 重試 → 落地
3. 說明作業 2

---

## 作業 2

用 cnyes API 抓出上週任一天的**美股新聞**（提示：`CATEGORIES` 裡的 `wd_stock`），輸出前 20 則標題與發布時間。
**評分標準**：輸出含正確的台北時間 ISO 格式即通過。
**常見卡關**：忘了帶 Referer（403）、直接印 epoch 沒轉時間。

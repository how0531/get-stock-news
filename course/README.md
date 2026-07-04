# 課程總覽：《用 Python 打造你的股市新聞情報系統》

> 一門把本 repo（get-stock-news）的實戰程式碼，轉化為可販售線上課程的完整教材與銷售包。
> 預期售價 NT$2,000–3,000，與投顧公司合作推廣。

## 目錄結構

```
course/
├── README.md                        # 本檔：總覽與使用說明
├── 01-course-blueprint.md           # 課程定位、目標學員、定價策略、學習成果
├── 02-curriculum.md                 # 完整課綱（8 模組 × 逐堂細目 × 對應程式碼）
├── lessons/
│   ├── module-1.md                  # 導論、環境建置、法遵觀念
│   ├── module-2.md                  # 第一支新聞 API：鉅亨網 JSON API
│   ├── module-3.md                  # RSS 與 sitemap：一次接 10 家媒體
│   ├── module-4.md                  # 官方第一手：TWSE/TPEx 重大訊息 OpenAPI
│   ├── module-5.md                  # 資料工程：去重、時區、PIT 儲存
│   ├── module-6.md                  # 個股辨識：股票字典與新聞對應
│   ├── module-7.md                  # 熱度量化入門：評分、目標價、Tier
│   └── module-8.md                  # 自動化實戰：盤中監看、日終 ETL、盤前報告
├── sales-kit/
│   ├── landing-page.md              # 銷售頁完整文案（可直接貼上開課平台）
│   ├── marketing-plan.md            # 行銷漏斗、上市時程、投顧合作分潤方案
│   ├── promo-copy.md                # 社群貼文 × EDM 三封信 × 免費直播講稿
│   └── faq.md                       # 售前 FAQ + 客服回覆 SOP
└── operations/
    └── sales-ops-and-compliance.md  # 平台/金流/發票/退費政策/法遵（投顧法、著作權）
```

## 怎麼使用這套教材

1. **先讀** `01-course-blueprint.md` 確認定位與售價，再讀 `02-curriculum.md` 看完整課綱。
2. **錄課**：`lessons/module-*.md` 每份都是「講師教學筆記」格式——含教學目標、講稿大綱、demo 步驟（對應 repo 的實際指令與程式碼）、學員作業與常見卡關點。照著錄即可。
3. **上架**：把 `sales-kit/landing-page.md` 的文案貼進開課平台；行銷排程照 `marketing-plan.md` 執行；社群與 EDM 素材在 `promo-copy.md`。
4. **開賣前**：務必看完 `operations/sales-ops-and-compliance.md` 的退費政策與法遵段落（尤其與投顧公司合作時的「不構成投資建議」聲明）。

## 課程一句話定位

> 「不用等記者整理、不用付昂貴的資訊終端機——8 小時學會用 Python 串接台股新聞 API 與官方公告，
> 自動去重、量化熱度，每天開盤前自動產出你自己的盤前情報。」

## 關鍵數字

| 項目 | 內容 |
|------|------|
| 課程長度 | 8 模組、約 45 堂、總片長 8–10 小時 |
| 定價 | 定價 NT$2,980／早鳥 NT$1,990／投顧會員專案價 NT$2,380 |
| 目標學員 | 會一點 Python 的散戶投資人、投顧會員、金融從業者 |
| 交付物 | 影音課程 + 完整可執行程式碼（本 repo）+ 課程講義 + 學員社群 |
| 結業成果 | 學員能自己跑出「每日盤前熱度報告」 |

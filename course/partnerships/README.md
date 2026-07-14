# 合作提案（Partnerships）

針對特定通路/平台客製的 B2B 合作提案簡報。

## 檔案

- `sinopac-proposal.html` — **永豐金課程平台合作提案**（15 頁，單檔 HTML 版）
  - 定位：向永豐金證券的課程/投資學習平台提案，把既有課程與工具上架/整合
  - 三個資產：入門課（散戶新聞實戰課）、進階技術課（Python 情報系統）、新聞多空監測工具
  - 主軸：對券商的價值（用戶黏著、平台差異化、導流交易、品牌 PR）＋ **法遵安全定位**（資訊素養教學、非投資建議）
  - 三種合作模式：課程上架分潤 / 共同品牌獨家 / 工具授權整合（App 內今日情緒、自選股盤前推播）
  - 內含監測工具的真實輸出 demo（`scripts/sentiment_report.py` 產出）
  - 瀏覽器開啟即可播放：← → 或空白鍵翻頁、右下角 ◐ 切換深淺色、手機可滑動
- `openslide/` — **同一份提案的 [open-slide](https://github.com/1weiho/open-slide) 版**（`slides/sinopac-proposal/`，15 頁）
  - 每頁是 1920×1080 canvas 上的 React component，支援縮圖列、總覽格、簡報者模式、
    Design 面板即時調整色票/字級，並內建匯出 PDF / 圖片 PPTX / 靜態 HTML
  - 開發：`cd openslide && npm install && npm run dev`；建置：`npm run build`（輸出 `dist/`，已 gitignore）
  - 內容與 HTML 版同步；改版時建議兩邊一起改
- `pdf/永豐金課程平台合作提案.pdf` — HTML 版匯出的 PDF（寄送/離線用）
- `pdf/永豐金課程平台合作提案-openslide.pdf` — open-slide 版匯出的 PDF
- `pptx/永豐金課程平台合作提案.pptx` — **原生可編輯的 PowerPoint 版**（15 頁）
  - 每個標題、內文、表格、色塊都是真正的 PPT 物件，可在 PowerPoint / Keynote / Google Slides 直接改字改色，非整頁圖片
  - 字體：標題微軟雅黑體（Microsoft YaHei）、內文微軟正黑體（Microsoft JhengHei），皆為 Windows 內建字型
  - 由 `pptx/build_pptx.py` 以 python-pptx 產生（`pip install python-pptx && python build_pptx.py`），改內容時改腳本再重跑即可

## 與其他簡報的分工

| 簡報 | 位置 | 對象 | 用途 |
|------|------|------|------|
| 投顧合作提案（14 頁） | artifact | 一般投顧合作方 | 通用課程商業提案 |
| 教學投影片（38 頁） | `course/beginner-course/slides.html` | 學員 | 上課用內容 |
| **永豐金合作提案（15 頁）** | `sinopac-proposal.html` | 永豐金證券平台 | B2B 通路上架/整合 |
| **永豐金合作提案（open-slide 版）** | `openslide/slides/sinopac-proposal/` | 永豐金證券平台 | 同上，可編輯/簡報者模式/匯出 |

## 法遵注意

品牌名稱僅用於說明合作對象；一切課程與工具均定位為投資知識與資訊素養教學，
不構成投資分析或買賣建議。所有內容、行銷素材、App 整合文案於上線前送對方法遵審閱。
實際合作條件以雙方正式合約為準。

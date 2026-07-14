#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把《永豐金課程平台合作提案》(15 頁) 產生成原生、可編輯的 PowerPoint。

與 course/partnerships/sinopac-proposal.html 及 openslide 版內容一致：
每個標題、內文、表格、色塊都是真正的 PPT 物件（文字方塊、表格、圖形），
可在 PowerPoint / Keynote / Google Slides 直接編輯，而非整頁圖片。

用法：
    pip install python-pptx
    python build_pptx.py
輸出：
    永豐金課程平台合作提案.pptx
"""
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn, nsdecls
from pptx.oxml import parse_xml

# ── 尺寸換算：畫布 1920×1080 對應 13.333"×7.5"（144 px = 1 inch；1 pt = 2 px）──
EMU_PER_PX = 914400 / 144.0


def PX(px):
    return Emu(int(round(px * EMU_PER_PX)))


def FS(px):
    return Pt(px / 2.0)


# ── 色票（沿用原簡報）──
BG = RGBColor(0xF5, 0xF3, 0xEE)
INK = RGBColor(0x12, 0x31, 0x2C)
SUB = RGBColor(0x55, 0x66, 0x61)
ACCENT = RGBColor(0x12, 0x7A, 0x6B)
ACCENT_SOFT = RGBColor(0xE1, 0xF0, 0xEC)
GOLD = RGBColor(0xB0, 0x81, 0x2B)
GOLD_SOFT = RGBColor(0xF5, 0xEC, 0xD8)
DEEP = RGBColor(0x0F, 0x3B, 0x36)
LINE = RGBColor(0xDD, 0xD9, 0xCF)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
# 監測工具 demo（深底終端機）
UP = RGBColor(0x5F, 0xD0, 0xAE)
DN = RGBColor(0xE8, 0x8A, 0x6F)
DIM = RGBColor(0x7C, 0x91, 0x88)
DEMO_TX = RGBColor(0xDC, 0xE8, 0xE4)
DEMO_HD = RGBColor(0xD6, 0xA9, 0x4E)

# ── 字族：標題微軟雅黑體、內文微軟正黑體（皆為 Windows 內建，免內嵌）──
# SERIF 沿用變數名，實際為標題字體；SANS 為內文字體。
SERIF = "Microsoft YaHei"      # 標題（微軟雅黑體）
SANS = "Microsoft JhengHei"    # 內文（微軟正黑體）
MONO = "Consolas"              # demo 等寬（拉丁字），中文以內文字體補字

TOTAL = 15
FOOTER_LEFT = "永豐金課程平台合作提案"


def _hex(c):
    return "%02X%02X%02X" % (c[0], c[1], c[2])


def _set_typeface(run, latin, ea):
    """分別設定拉丁字（latin/cs）與中日韓字（ea）字族。"""
    rPr = run._r.get_or_add_rPr()
    mapping = {"a:latin": latin, "a:ea": ea, "a:cs": latin}
    for tag, name in mapping.items():
        el = rPr.find(qn(tag))
        if el is None:
            el = parse_xml('<%s %s typeface="%s"/>' % (tag, nsdecls("a"), name))
            rPr.append(el)
        else:
            el.set("typeface", name)


def style_run(run, *, size, color, bold=False, font=SANS, spacing=None):
    f = run.font
    f.size = FS(size)
    f.bold = bold
    f.color.rgb = color
    f.name = font
    # 等寬字（Consolas）沒有中文，中文改用內文字體補字，維持終端機等寬外觀
    ea = SANS if font == MONO else font
    _set_typeface(run, font, ea)
    if spacing is not None:  # 字距，單位 1/100 pt
        run._r.get_or_add_rPr().set("spc", str(int(spacing)))


def _no_autosize(tf):
    tf.word_wrap = True
    try:
        from pptx.enum.text import MSO_AUTO_SIZE
        tf.auto_size = MSO_AUTO_SIZE.NONE
    except Exception:
        pass
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0


def textbox(slide, x, y, w, h, paras, *, anchor=MSO_ANCHOR.TOP):
    """paras: list of dicts:
    {'runs': [(text, {style_kwargs})], 'align', 'line', 'sb', 'sa'}"""
    tb = slide.shapes.add_textbox(PX(x), PX(y), PX(w), PX(h))
    tf = tb.text_frame
    _no_autosize(tf)
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        if p.get("line") is not None:
            para.line_spacing = p["line"]
        if p.get("sb") is not None:
            para.space_before = FS(p["sb"])
        if p.get("sa") is not None:
            para.space_after = FS(p["sa"])
        for text, st in p["runs"]:
            r = para.add_run()
            r.text = text
            style_run(r, **st)
    return tb


def rect(slide, x, y, w, h, *, fill=None, line=None, line_w=1.0, rounded=False, radius=0.05):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape, PX(x), PX(y), PX(w), PX(h))
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    if rounded:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    return shp


def set_bg(slide, color):
    rect(slide, 0, 0, 1920, 1080, fill=color)


def eyebrow_heading(slide, eyebrow, title_runs, *, title_y=120, title_size=60, title_line=1.28):
    textbox(slide, 140, 78, 1640, 40,
            [{"runs": [(eyebrow, dict(size=24, color=GOLD, bold=True, spacing=280))]}])
    textbox(slide, 140, title_y, 1640, 200,
            [{"runs": title_runs, "line": title_line}])


def footer(slide, page):
    textbox(slide, 140, 1004, 900, 34,
            [{"runs": [(FOOTER_LEFT, dict(size=20, color=SUB, font=MONO))]}])
    textbox(slide, 1020, 1004, 760, 34,
            [{"runs": [("%02d / %d" % (page, TOTAL), dict(size=20, color=SUB, font=MONO))]}],
            )
    # 右對齊頁碼
    slide.shapes[-1].text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT


def note(slide, text_runs, *, y=946):
    textbox(slide, 140, y, 1640, 60,
            [{"runs": text_runs, "line": 1.55}])


def card(slide, x, y, w, h, *, fill=SURFACE, line=LINE, radius=0.045, top=None, top_h=6):
    shp = rect(slide, x, y, w, h, fill=fill, line=line, line_w=1.0, rounded=True, radius=radius)
    if top is not None:
        rect(slide, x, y - 1, w, top_h, fill=top)  # 頂端色條
    return shp


def _text_w(text, size):
    """估算文字寬度（px）：全形字約 1.02×字級、半形約 0.55×。"""
    w = 0.0
    for ch in text:
        w += size * 1.02 if ord(ch) > 0x2E80 else size * 0.55
    return w


def pill(slide, x, y, text, *, color, soft):
    size = 21
    w = int(_text_w(text, size) + 44)
    rect(slide, x, y, w, 36, fill=soft, line=None, rounded=True, radius=0.5)
    textbox(slide, x, y + 3, w, 30,
            [{"runs": [(text, dict(size=size, color=color, bold=True, spacing=60))],
              "align": PP_ALIGN.CENTER}], anchor=MSO_ANCHOR.MIDDLE)
    return w


def tick_rows(slide, x, y, w, rows, *, check=False, gap=None):
    """rows: list of (lead, sub) ；lead 粗體、sub 為 SUB 色。回傳結束 y。"""
    row_h = 84
    for i, (lead, sub) in enumerate(rows):
        ry = y + i * row_h
        mark = "✓" if check else "▸"
        mcolor = ACCENT if check else GOLD
        textbox(slide, x, ry + 4, 40, 40,
                [{"runs": [(mark, dict(size=27, color=mcolor, bold=True))]}])
        runs = [(lead, dict(size=28, color=INK, bold=True))]
        if sub:
            runs.append((sub, dict(size=28, color=SUB)))
        textbox(slide, x + 50, ry, w - 50, row_h,
                [{"runs": runs, "line": 1.5}])
        if i < len(rows) - 1:  # 虛線分隔
            ln = rect(slide, x, ry + row_h - 8, w, 1, fill=LINE)
    return y + len(rows) * row_h


# ── 表格 ──
NO_STYLE_NO_GRID = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"


def _clear_table_style(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    for sid in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(sid)
    sid = parse_xml("<a:tableStyleId %s>%s</a:tableStyleId>" % (nsdecls("a"), NO_STYLE_NO_GRID))
    tblPr.append(sid)


def _cell_bottom(cell, spec):
    """spec=(color,w_pt,dash|None) 或 None。設四邊：L/R/T 無、B 依 spec。"""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        e = tcPr.find(qn(tag))
        if e is not None:
            tcPr.remove(e)
    def none_ln(tag):
        return parse_xml('<%s %s w="0"><a:noFill/></%s>' % (tag, nsdecls("a"), tag))
    def solid_ln(tag, color, wpt, dash):
        d = '<a:prstDash val="%s"/>' % dash if dash else ""
        return parse_xml(
            '<%s %s w="%d" cap="flat"><a:solidFill><a:srgbClr val="%s"/></a:solidFill>%s</%s>'
            % (tag, nsdecls("a"), int(wpt * 12700), _hex(color), d, tag))
    # 依 schema 順序 L,R,T,B 插到最前
    lnB = solid_ln("a:lnB", *spec) if spec else none_ln("a:lnB")
    tcPr.insert(0, lnB)
    tcPr.insert(0, none_ln("a:lnT"))
    tcPr.insert(0, none_ln("a:lnR"))
    tcPr.insert(0, none_ln("a:lnL"))


def _cell_fill(cell, color):
    if color is None:
        cell.fill.background()
    else:
        cell.fill.solid()
        cell.fill.fore_color.rgb = color


def _cell_text(cell, runs, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE):
    cell.vertical_anchor = anchor
    cell.margin_left = PX(20)
    cell.margin_right = PX(14)
    cell.margin_top = PX(10)
    cell.margin_bottom = PX(10)
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = 1.35
    for text, st in runs:
        r = p.add_run()
        r.text = text
        style_run(r, **st)


def make_table(slide, x, y, w, col_w, rows_spec, *, header=True):
    """rows_spec: list of rows；每 row = list of cell dict:
    {'runs':[(t,st)], 'align', 'fill', 'border'}。border=(color,wpt,dash)。
    以白色圓角卡片為底。"""
    nrow = len(rows_spec)
    ncol = len(col_w)
    row_h = [64] + [76] * (nrow - 1) if header else [76] * nrow
    total_h = sum(row_h)
    card(slide, x - 24, y - 20, w + 48, total_h + 40, fill=SURFACE, line=LINE, radius=0.03)
    gtbl = slide.shapes.add_table(nrow, ncol, PX(x), PX(y), PX(w), PX(total_h))
    table = gtbl.table
    _clear_table_style(table)
    for ci, cw in enumerate(col_w):
        table.columns[ci].width = PX(cw)
    for ri in range(nrow):
        table.rows[ri].height = PX(row_h[ri])
    for ri, row in enumerate(rows_spec):
        for ci, cd in enumerate(row):
            cell = table.cell(ri, ci)
            _cell_fill(cell, cd.get("fill", None))
            _cell_bottom = cd.get("border", "auto")
            if _cell_bottom == "auto":
                if header and ri == 0:
                    _cell_bottom = (DEEP, 2.0, None)
                elif ri == nrow - 1:
                    _cell_bottom = None
                else:
                    _cell_bottom = (LINE, 0.75, None)
            _set_border(cell, _cell_bottom)
            _cell_text(cell, cd["runs"], align=cd.get("align", PP_ALIGN.LEFT))
    return gtbl


def _set_border(cell, spec):
    _cell_bottom(cell, spec)


# ══════════════════════════ 建立簡報 ══════════════════════════
prs = Presentation()
prs.slide_width = PX(1920)
prs.slide_height = PX(1080)
BLANK = prs.slide_layouts[6]


def new_slide():
    s = prs.slides.add_slide(BLANK)
    set_bg(s, BG)
    return s


# ── 1・封面 ──
def slide_cover():
    s = new_slide()
    rect(s, 0, 0, 12, 1080, fill=GOLD)  # 左側金條
    textbox(s, 160, 250, 1500, 40,
            [{"runs": [("課程平台合作提案・COURSE PARTNERSHIP",
                        dict(size=26, color=ACCENT, font=MONO, spacing=200))]}])
    textbox(s, 160, 312, 1560, 320, [
        {"runs": [("把「看懂新聞」", dict(size=96, color=INK, bold=True, font=SERIF))], "line": 1.24},
        {"runs": [("做成永豐金投資人的", dict(size=96, color=INK, bold=True, font=SERIF)),
                  ("日常能力", dict(size=96, color=ACCENT, bold=True, font=SERIF))], "line": 1.24},
    ])
    textbox(s, 160, 636, 1400, 140, [
        {"runs": [("一套已完成的財經資訊素養課程 ＋ 一個可運作的新聞多空監測工具，",
                   dict(size=34, color=SUB))], "line": 1.7},
        {"runs": [("為永豐金課程平台帶來安全、差異化、能沉澱用戶的投資教育內容。",
                   dict(size=34, color=SUB))], "line": 1.7},
    ])
    meta = [("提案對象", "永豐金證券・課程/投資學習平台"),
            ("提案內容", "課程上架 × 工具整合 × 共同品牌"),
            ("交付狀態", "課程與工具皆已完成，可即刻上線")]
    mx = 160
    for k, v in meta:
        rect(s, mx, 838, 5, 74, fill=ACCENT)
        textbox(s, mx + 22, 838, 500, 90, [
            {"runs": [(k, dict(size=22, color=SUB, spacing=80))], "sa": 4},
            {"runs": [(v, dict(size=27, color=INK, bold=True))], "line": 1.15},
        ])
        mx += 560


# ── 2・一頁摘要 ──
def slide_summary():
    s = new_slide()
    eyebrow_heading(s, "EXECUTIVE SUMMARY", [("一頁看懂這個提案", dict(size=60, color=INK, bold=True, font=SERIF))])
    cw, ch, cy = 760, 520, 320
    card(s, 140, cy, cw, ch)
    card(s, 140 + cw + 40, cy, cw, ch)
    pill(s, 180, cy + 40, "我們帶來什麼", color=ACCENT, soft=ACCENT_SOFT)
    tick_rows(s, 180, cy + 110, cw - 76, [
        ("入門課", "：散戶新聞實戰課，零程式門檻，適合平台廣大用戶"),
        ("技術課", "：Python 股市新聞情報系統，適合進階/工程背景用戶"),
        ("監測工具", "：新聞利多/利空自動判讀，可作教材，亦可整合 App"),
    ], check=True)
    x2 = 140 + cw + 40
    pill(s, x2 + 40, cy + 40, "永豐金得到什麼", color=GOLD, soft=GOLD_SOFT)
    tick_rows(s, x2 + 40, cy + 110, cw - 76, [
        ("用戶黏著", "：從「開戶交易」延伸到「每天回來學習」"),
        ("平台差異化", "：別家券商沒有的「新聞判讀能力」內容線"),
        ("法遵安全", "：定位資訊素養教學，全程不涉個股買賣建議"),
        ("財經素養 PR", "：呼應主管機關推動的投資人教育方向"),
    ], check=False)
    note(s, [("合作形式彈性：可純上架分潤、可共同品牌獨家、可工具授權整合——第 12 頁提供三種模式。",
              dict(size=22, color=SUB))])
    footer(s, 2)


# ── 卡片欄位 helper（標題＋內文，可選 tag/letter）──
def info_card(slide, x, y, w, h, title, body, *, tag=None, tag_color=ACCENT, tag_soft=ACCENT_SOFT,
              letter=None, top=None):
    card(slide, x, y, w, h, top=top)
    iy = y + 34
    if tag:
        pill(slide, x + 34, iy, tag, color=tag_color, soft=tag_soft)
        iy += 54
    truns = []
    if letter:
        truns.append((letter + " ", dict(size=33, color=ACCENT, bold=True, font=SERIF)))
    truns.append((title, dict(size=31, color=INK, bold=True)))
    textbox(slide, x + 34, iy, w - 68, 90, [{"runs": truns, "line": 1.2}])
    textbox(slide, x + 34, iy + (58 if not letter else 58), w - 68, h - (iy - y) - 70,
            [{"runs": [(body, dict(size=26, color=SUB))], "line": 1.68}])


# ── 3・市場背景 ──
def slide_market():
    s = new_slide()
    eyebrow_heading(s, "01・為什麼是現在", [
        ("新一代投資人進場，", dict(size=56, color=INK, bold=True, font=SERIF))], title_line=1.3)
    textbox(s, 140, 190, 1640, 90, [{"runs": [
        ("但「看新聞的能力」沒跟上", dict(size=56, color=INK, bold=True, font=SERIF))], "line": 1.3}])
    cw, gap = 500, 40
    x0, cy, ch = 140, 350, 420
    cards = [
        ("年輕、行動優先的開戶潮",
         "零股交易與定期定額普及，大量新手用行動 App 進場——他們最缺的不是下單功能，是判讀資訊的方法。"),
        ("資訊過載",
         "財經新聞 App、社群、群組訊息爆量，新手每天被大量真假難辨的消息淹沒，容易追高殺低。"),
        ("教育需求正被政策推動",
         "投資人教育是金融業與主管機關共同關注方向；能提供「安全、不涉建議」的素養內容，是券商的加分項。"),
    ]
    for i, (t, b) in enumerate(cards):
        info_card(s, x0 + i * (cw + gap), cy, cw, ch, t, b)
    note(s, [("機會：券商平台擁有用戶與流量，但普遍缺少「教用戶怎麼消化資訊」的優質內容——這正是本提案補上的一塊。",
              dict(size=22, color=SUB))])
    footer(s, 3)


# ── 4・痛點 ──
def slide_pain():
    s = new_slide()
    eyebrow_heading(s, "02・平台的內容困境", [
        ("券商做投資教育，", dict(size=56, color=INK, bold=True, font=SERIF))], title_line=1.3)
    textbox(s, 140, 190, 1640, 90, [{"runs": [
        ("常卡在這三件事", dict(size=56, color=INK, bold=True, font=SERIF))], "line": 1.3}])
    rows = [
        ("內容同質化", "——各家都在講技術分析、K 線、財報基礎，用戶看膩了，也記不住是哪一家教的。"),
        ("法遵綁手綁腳", "——只要碰個股就有投顧法風險，內容團隊做得綁手綁腳，往往流於空泛。"),
        ("看完就走，沉澱不了用戶", "——影片看完沒有「可以每天用的工具或習慣」，無法把觀看轉成回訪與活躍。"),
    ]
    tick_rows(s, 140, 330, 1640, rows, check=False)
    # 引言塊
    qy = 600
    rect(s, 140, qy, 8, 190, fill=GOLD)
    card(s, 140, qy, 1500, 190, line=LINE)
    rect(s, 140, qy, 8, 190, fill=GOLD)
    textbox(s, 190, qy + 34, 1420, 130, [
        {"runs": [("用戶要的不是「更多內容」，", dict(size=36, color=INK, bold=True, font=SERIF))], "line": 1.5},
        {"runs": [("是一個「每天都想打開、而且合規安全」的學習理由。",
                   dict(size=36, color=INK, bold=True, font=SERIF))], "line": 1.5},
    ])
    footer(s, 4)


# ── 5・三個資產 ──
def slide_assets():
    s = new_slide()
    eyebrow_heading(s, "03・我們帶來的三個資產", [
        ("一條完整的", dict(size=60, color=INK, bold=True, font=SERIF)),
        ("投資素養內容線", dict(size=60, color=ACCENT, bold=True, font=SERIF))])
    cw, gap = 500, 40
    x0, cy, ch = 140, 340, 430
    data = [
        ("資產一・入門", ACCENT, ACCENT_SOFT, "A", "散戶新聞實戰課",
         "零程式門檻、6 單元教學投影片。教用戶用對新聞、避開四大陷阱、建立每日看盤 SOP。適合平台最大宗的一般用戶。"),
        ("資產二・進階", ACCENT, ACCENT_SOFT, "B", "Python 情報系統課",
         "8 模組實戰，串接新聞 API 與官方公告、自動去重、量化熱度。適合工程背景與進階用戶，拉高平台專業形象。"),
        ("資產三・工具", GOLD, GOLD_SOFT, "C", "新聞多空監測工具",
         "已可運作的系統：自動判讀新聞利多/利空、彙整個股多空榜。可作課程實作素材，亦可授權整合進大戶投等 App。"),
    ]
    for i, (tag, tc, ts, letter, title, body) in enumerate(data):
        info_card(s, x0 + i * (cw + gap), cy, cw, ch, title, body,
                  tag=tag, tag_color=tc, tag_soft=ts, letter=letter)
    note(s, [("三者形成漏斗：入門課吸引廣大用戶 → 工具養成每日回訪習慣 → 進階課沉澱高價值用戶。",
              dict(size=22, color=SUB))])
    footer(s, 5)


# ── 6・資產A 入門課（表格）──
def slide_asset_a():
    s = new_slide()
    eyebrow_heading(s, "資產 A・入門課", [("散戶新聞實戰課", dict(size=60, color=INK, bold=True, font=SERIF))])
    textbox(s, 140, 230, 1640, 60, [{"runs": [
        ("為平台最大宗的一般投資人設計。不用寫程式、看得懂中文就能上，直接提升「看盤效率」。",
         dict(size=29, color=SUB))], "line": 1.6}])
    th = dict(size=23, color=SUB, bold=True, spacing=80)
    td = dict(size=27, color=INK)
    unit = dict(size=27, color=INK, bold=True)
    rows = [
        [{"runs": [("單元", th)]}, {"runs": [("學員帶走的能力", th)]}],
        [{"runs": [("資訊鏈", unit)]}, {"runs": [("看懂一則新聞到你手上經過幾站、延遲多久——接受「新聞是落後指標」", td)]}],
        [{"runs": [("資訊源頭", unit)]}, {"runs": [("建立自己的三來源清單，分清第一手 vs 轉載", td)]}],
        [{"runs": [("5 分鐘判讀 SOP", unit)]}, {"runs": [("五個固定問題，快速判斷一則新聞值不值得理", td)]}],
        [{"runs": [("熱度思維", unit)]}, {"runs": [("用新聞量的「變化」讀市場關注，避開擁擠行情", td)]}],
        [{"runs": [("每日例行流程", unit)]}, {"runs": [("盤前 30 分／盤中兩原則／盤後 15 分的完整 SOP", td)]}],
        [{"runs": [("陷阱與驗證", unit)]}, {"runs": [("辨識新聞陷阱、建立 T+1/T+5 事後驗證習慣", td)]}],
    ]
    make_table(s, 164, 320, 1592, [360, 1232], rows)
    note(s, [("形式：38 頁教學投影片 ＋ 4 個實戰練習。全課以「教學示例」呈現個股，封面與高風險頁均有免責聲明。",
              dict(size=22, color=SUB))])
    footer(s, 6)


# ── 7・資產B 技術課 ──
def slide_asset_b():
    s = new_slide()
    eyebrow_heading(s, "資產 B・進階技術課", [
        ("用 Python 打造股市新聞情報系統", dict(size=54, color=INK, bold=True, font=SERIF))])
    cw, ch, cy = 760, 470, 330
    card(s, 140, cy, cw, ch)
    card(s, 140 + cw + 40, cy, cw, ch)
    pill(s, 180, cy + 40, "課程規模", color=ACCENT, soft=ACCENT_SOFT)
    tick_rows(s, 180, cy + 110, cw - 76, [
        ("8 模組・45 堂・8–10 小時", ""),
        ("附完整可執行 GitHub 專案（含測試與 CI）", ""),
        ("串接鉅亨 API、10+ 家媒體、官方公告", ""),
        ("去重、時區、PIT 儲存、熱度量化全流程", ""),
    ], check=True)
    x2 = 140 + cw + 40
    pill(s, x2 + 40, cy + 40, "對平台的意義", color=GOLD, soft=GOLD_SOFT)
    tick_rows(s, x2 + 40, cy + 110, cw - 76, [
        ("拉高專業形象", "：市面極少見的「生產級」財經工程課"),
        ("吸引高價值客群", "：工程師、量化愛好者、年輕高資產族"),
        ("內容護城河", "：一年免費更新承諾，內容不易被複製"),
    ], check=False)
    note(s, [("定位：進階付費內容，客單較高（原定價帶 NT$2,000–3,000），與入門課構成「免費/低價引流 → 進階變現」的雙層結構。",
              dict(size=22, color=SUB))])
    footer(s, 7)


# ── 8・資產C 監測工具 demo（終端機）──
def slide_asset_c():
    s = new_slide()
    eyebrow_heading(s, "資產 C・監測工具（已可運作）", [
        ("新聞利多/利空監測——", dict(size=54, color=INK, bold=True, font=SERIF)),
        ("不是概念，是跑出來的", dict(size=54, color=ACCENT, bold=True, font=SERIF))])
    dx, dy, dw, dh = 140, 320, 1640, 500
    card(s, dx, dy, dw, dh, fill=DEEP, line=None, radius=0.02)
    hd = dict(size=24, color=DEMO_HD, bold=True, font=MONO)
    tx = dict(size=24, color=DEMO_TX, font=MONO)
    up = dict(size=24, color=UP, font=MONO)
    dn = dict(size=24, color=DN, font=MONO)
    dim = dict(size=24, color=DIM, font=MONO)
    paras = [
        {"runs": [("=== 新聞利多/利空監測 2026-07-03 ===", hd)]},
        {"runs": [("總計：利多 3 則｜利空 2 則｜中性 1 則", tx)]},
        {"runs": [(" ", tx)], "sb": 8},
        {"runs": [("--- 個股利多榜 ---", hd)]},
        {"runs": [("  2330 台積電  ", tx), ("net=+25.0  利多×2", up)]},
        {"runs": [("     ", tx), ("[利多+15]", up), (" 台積電上修財測 產能滿載供不應求", tx)]},
        {"runs": [("     ", tx), ("[利多+10]", up), (" 外資調升目標價 獲利優於預期", tx)]},
        {"runs": [("  2303 聯電    ", tx), ("net= +2.0  利多×1", up)]},
        {"runs": [("     ", tx), ("[利多 +2]", up), (" 市場傳出可望取得大單  ", tx), ("（傳聞→分數折半）", dim)]},
        {"runs": [(" ", tx)], "sb": 8},
        {"runs": [("--- 個股利空榜 ---", hd)]},
        {"runs": [("  2454 聯發科  ", tx), ("net= -6.0  利空×1", dn)]},
        {"runs": [("     ", tx), ("[利空 -6]", dn), (" 聯發科遭砍單 全年展望轉保守", tx)]},
    ]
    for p in paras:
        p["line"] = 1.6
    textbox(s, dx + 44, dy + 34, dw - 88, dh - 68, paras)
    note(s, [("規則透明可解釋：每則判定都能列出命中詞與權重；「市場傳出/可望」等傳聞用語自動折價，"
              "呼應課程「事實＞預期＞傳聞」的原則。可作課程實作教材，或作為 App 內的「今日新聞情緒」小工具。",
              dict(size=21, color=SUB))])
    footer(s, 8)


# ── 9・整合場景 ──
def slide_integration():
    s = new_slide()
    eyebrow_heading(s, "資產 C・整合場景", [
        ("它可以長在永豐金的平台裡", dict(size=60, color=INK, bold=True, font=SERIF))])
    cw, gap = 500, 40
    x0, cy, ch = 140, 350, 420
    data = [
        ("情境一・課程實作", ACCENT, ACCENT_SOFT, "當作教材",
         "入門/進階課學員照著跑，親手產出自己的多空榜——把「看完就走」變成「動手做出成果」。"),
        ("情境二・App 小工具", ACCENT, ACCENT_SOFT, "今日新聞情緒",
         "整合進大戶投等 App，用戶查個股時附上「近期新聞多空傾向」與來源連結，提升查詢黏著。"),
        ("情境三・自選股推播", GOLD, GOLD_SOFT, "盤前多空摘要",
         "依用戶自選股，每日盤前推送「你的持股昨夜有哪些利多/利空新聞」，創造每日回訪理由。"),
    ]
    for i, (tag, tc, ts, title, body) in enumerate(data):
        info_card(s, x0 + i * (cw + gap), cy, cw, ch, title, body, tag=tag, tag_color=tc, tag_soft=ts)
    note(s, [("※ 所有整合情境均以「新聞語意整理／資訊呈現」為定位，附來源原文連結與免責聲明，"
              "不對個股做買賣評價；上線前送貴公司法遵確認。", dict(size=21, color=SUB))])
    footer(s, 9)


# ── 10・對永豐金的價值（4 欄大數字）──
def slide_value():
    s = new_slide()
    eyebrow_heading(s, "04・對永豐金的價值", [("券商為什麼要做這個", dict(size=60, color=INK, bold=True, font=SERIF))])
    cw, gap = 375, 30
    x0, cy, ch = 140, 360, 380
    data = [
        ("用戶黏著 ↑", "每日", "回訪理由", "從交易工具變成「每天想打開的學習與情報入口」。"),
        ("平台差異化", "獨有", "內容線", "「新聞判讀能力」是別家券商沒有的定位。"),
        ("導流交易", "素養", "→ 信心", "更懂資訊的用戶更敢參與市場，活躍度提升。"),
        ("品牌與 PR", "素養", "形象", "呼應投資人教育政策，正向品牌聯想。"),
    ]
    for i, (title, big, small, body) in enumerate(data):
        x = x0 + i * (cw + gap)
        card(s, x, cy, cw, ch)
        textbox(s, x + 30, cy + 34, cw - 60, 50,
                [{"runs": [(title, dict(size=31, color=INK, bold=True))]}])
        textbox(s, x + 30, cy + 100, cw - 60, 90,
                [{"runs": [(big, dict(size=58, color=ACCENT, bold=True, font=SERIF)),
                           ("  " + small, dict(size=24, color=SUB))], "line": 1.05}])
        textbox(s, x + 30, cy + 210, cw - 60, 140,
                [{"runs": [(body, dict(size=25, color=SUB))], "line": 1.6}])
    note(s, [("關鍵：這些價值都不需要碰「投資建議」就能達成——靠的是「教方法、給工具」，而非「報明牌」。",
              dict(size=22, color=SUB))])
    footer(s, 10)


# ── 11・法遵 ──
def slide_compliance():
    s = new_slide()
    eyebrow_heading(s, "05・法遵定位（券商最在意的一頁）", [
        ("為什麼這對永豐金是", dict(size=60, color=INK, bold=True, font=SERIF)),
        ("安全", dict(size=60, color=ACCENT, bold=True, font=SERIF)),
        ("的內容", dict(size=60, color=INK, bold=True, font=SERIF))])
    rows = [
        ("定位為資訊素養與程式技術教學，非投資分析或投資建議",
         "——全程不對任何個股做買賣評價、不喊目標價、不報進出點。"),
        ("個股一律為「教學示例」",
         "——封面與高風險頁均有免責聲明；工具輸出每次附「非投資建議」聲明與原文連結。"),
        ("教「怎麼判讀」而非「該買什麼」",
         "——把判斷權還給用戶，這正是與投顧業務的清楚切割線。"),
        ("上線前全數送貴公司法遵審閱",
         "——內容、行銷素材、App 整合文案，配合永豐金法遵流程調整並留存紀錄。"),
    ]
    tick_rows(s, 140, 360, 1640, rows, check=True)
    note(s, [("我方已備有完整法遵設計文件（投顧法、著作權、爬蟲、個資四大紅線），可提供貴公司法遵團隊先行審閱。",
              dict(size=22, color=SUB))])
    footer(s, 11)


# ── 12・合作模式（3 term 卡，頂色條）──
def slide_models():
    s = new_slide()
    eyebrow_heading(s, "06・合作模式（三選一或組合）", [("三種合作深度", dict(size=60, color=INK, bold=True, font=SERIF))])
    cw, gap = 500, 40
    x0, cy, ch = 140, 350, 420
    data = [
        ("模式一・最輕", "課程上架分潤", GOLD, "課程放上永豐金學習平台，依成交分潤。最快上線，驗證用戶反應。"),
        ("模式二・推薦", "共同品牌獨家", ACCENT, "永豐金 × 課程共同掛名、平台獨家；可客製「永豐金用戶專屬版」內容與行銷。"),
        ("模式三・最深", "工具授權整合", GOLD, "將多空監測工具授權整合進 App（今日情緒／自選股推播），採授權金或年費。"),
    ]
    for i, (k, v, top, body) in enumerate(data):
        x = x0 + i * (cw + gap)
        card(s, x, cy, cw, ch, top=top, top_h=8)
        textbox(s, x + 36, cy + 40, cw - 72, 40,
                [{"runs": [(k, dict(size=24, color=top, bold=True, spacing=60))]}])
        textbox(s, x + 36, cy + 90, cw - 72, 70,
                [{"runs": [(v, dict(size=46, color=INK, bold=True, font=SERIF))]}])
        textbox(s, x + 36, cy + 190, cw - 72, 200,
                [{"runs": [(body, dict(size=26, color=SUB))], "line": 1.7}])
    note(s, [("建議路徑：先以模式一或二快速上線驗證，成效好再談模式三的 App 整合——風險低、可分階段。",
              dict(size=22, color=SUB))])
    footer(s, 12)


# ── 13・商業條件（表格 4 欄）──
def slide_commercial():
    s = new_slide()
    eyebrow_heading(s, "07・商業條件（討論起點）", [("彈性的分潤與授權架構", dict(size=60, color=INK, bold=True, font=SERIF))])
    th = dict(size=23, color=SUB, bold=True, spacing=60)
    td = dict(size=27, color=INK)
    tdn = dict(size=25, color=INK, font=MONO)
    rows = [
        [{"runs": [("模式", th)]}, {"runs": [("計費方式", th)]}, {"runs": [("建議區間", th)]}, {"runs": [("備註", th)]}],
        [{"runs": [("課程上架分潤", td)]}, {"runs": [("依課程成交拆分", td)]},
         {"runs": [("平台 30–50%", tdn)]}, {"runs": [("依導流與獨家程度調整", td)]}],
        [{"runs": [("共同品牌獨家", td)], "fill": ACCENT_SOFT}, {"runs": [("分潤 + 保底", td)], "fill": ACCENT_SOFT},
         {"runs": [("另議", tdn)], "fill": ACCENT_SOFT}, {"runs": [("含專屬版客製與聯合行銷資源", td)], "fill": ACCENT_SOFT}],
        [{"runs": [("工具授權整合", td)]}, {"runs": [("年度授權金 / 月費", td)]},
         {"runs": [("另議", tdn)]}, {"runs": [("依整合深度、API 用量與維運範圍", td)]}],
    ]
    # emph 行需要底線仍為 LINE；最後一行無底線
    for cell in rows[2]:
        cell["border"] = (LINE, 0.75, None)
    make_table(s, 164, 380, 1592, [360, 380, 372, 480], rows)
    note(s, [("以上為協商起點，實際條件依雙方合約為準。我方亦可接受「先小規模試營運、看數據再定案」的合作節奏。",
              dict(size=22, color=SUB))])
    footer(s, 13)


# ── 14・上線時程（表格 3 欄）──
def slide_timeline():
    s = new_slide()
    eyebrow_heading(s, "08・上線時程", [("四階段，最快一季內上線", dict(size=60, color=INK, bold=True, font=SERIF))])
    th = dict(size=23, color=SUB, bold=True, spacing=60)
    td = dict(size=27, color=INK)
    tdn = dict(size=25, color=INK, font=MONO)
    rows = [
        [{"runs": [("階段", th)]}, {"runs": [("時程", th)]}, {"runs": [("工作", th)]}],
        [{"runs": [("① 對齊與法遵", td)]}, {"runs": [("2–3 週", tdn)]},
         {"runs": [("確認合作模式；課程與工具送法遵審閱、依意見調整", td)]}],
        [{"runs": [("② 內容客製", td)]}, {"runs": [("3–4 週", tdn)]},
         {"runs": [("永豐金專屬版包裝、片頭品牌、平台上架素材", td)]}],
        [{"runs": [("③ 試營運", td)]}, {"runs": [("4 週", tdn)]},
         {"runs": [("入門課先上，觀察觀看/完課/回訪數據", td)]}],
        [{"runs": [("④ 擴展", td)]}, {"runs": [("後續", tdn)]},
         {"runs": [("加上進階課；成效佳則啟動工具 App 整合", td)]}],
    ]
    make_table(s, 164, 360, 1592, [420, 280, 892], rows)
    note(s, [("課程與工具皆已完成，時程主要花在「法遵確認」與「品牌客製」，而非從零製作內容——這是本提案能快速上線的關鍵。",
              dict(size=22, color=SUB))])
    footer(s, 14)


# ── 15・為什麼是我們 & CTA ──
def slide_closing():
    s = new_slide()
    eyebrow_heading(s, "09・為什麼是我們 & 下一步", [
        ("成品已在手上，不是一份", dict(size=56, color=INK, bold=True, font=SERIF)),
        ("企劃書", dict(size=56, color=GOLD, bold=True, font=SERIF)),
        ("而已", dict(size=56, color=INK, bold=True, font=SERIF))])
    cw, ch, cy = 760, 380, 300
    card(s, 140, cy, cw, ch)
    card(s, 140 + cw + 40, cy, cw, ch)
    pill(s, 180, cy + 36, "交付能力", color=ACCENT, soft=ACCENT_SOFT)
    tick_rows(s, 180, cy + 100, cw - 76, [
        ("兩門課程 + 一套工具", "，皆已完成、可即刻示範"),
        ("完整程式碼含測試與 CI", "，工程品質可受檢視"),
        ("已備完整法遵設計文件", "，供貴公司先行審閱"),
    ], check=True)
    x2 = 140 + cw + 40
    pill(s, x2 + 40, cy + 36, "下一步（提議）", color=GOLD, soft=GOLD_SOFT)
    tick_rows(s, x2 + 40, cy + 100, cw - 76, [
        ("30 分鐘線上 demo", "：現場展示課程與工具實跑"),
        ("交付法遵文件", "：讓貴公司法遵團隊先評估"),
        ("選定試營運模式", "：從模式一/二挑一，訂上線里程碑"),
    ], check=False)
    qy = 730
    card(s, 140, qy, 1560, 150, line=LINE)
    rect(s, 140, qy, 8, 150, fill=GOLD)
    textbox(s, 190, qy + 40, 1480, 90, [{"runs": [
        ("讓永豐金的投資人，不只在你的平台", dict(size=36, color=INK, bold=True, font=SERIF)),
        ("下單", dict(size=36, color=ACCENT, bold=True, font=SERIF)),
        ("，也在你的平台", dict(size=36, color=INK, bold=True, font=SERIF)),
        ("變強", dict(size=36, color=ACCENT, bold=True, font=SERIF)),
        ("。", dict(size=36, color=INK, bold=True, font=SERIF))]}])
    note(s, [("本提案內容為合作討論用途；一切課程與工具均定位為投資知識與資訊素養教學，不構成投資分析或買賣建議。"
              "品牌名稱僅為說明合作對象，實際合作以雙方正式合約為準。", dict(size=20, color=SUB))], y=904)
    footer(s, 15)


for fn in [slide_cover, slide_summary, slide_market, slide_pain, slide_assets,
           slide_asset_a, slide_asset_b, slide_asset_c, slide_integration, slide_value,
           slide_compliance, slide_models, slide_commercial, slide_timeline, slide_closing]:
    fn()

import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "永豐金課程平台合作提案.pptx")
prs.save(out)
print("saved:", out, "slides:", len(prs.slides._sldIdLst))

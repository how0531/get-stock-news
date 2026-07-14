import type { DesignSystem, Page, SlideMeta, SlideTransition } from '@open-slide/core';
import { useSlidePageNumber } from '@open-slide/core';
import type { CSSProperties, ReactNode } from 'react';

export const design: DesignSystem = {
  palette: { bg: '#F5F3EE', text: '#12312C', accent: '#127A6B' },
  fonts: {
    display: '"Noto Serif TC", "Songti TC", PMingLiU, Georgia, serif',
    body: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif',
  },
  typeScale: { hero: 96, body: 30 },
  radius: 10,
};

// 原 HTML 版簡報的完整色票（DesignSystem 之外的輔助色）
const SUB = '#556661';
const GOLD = '#B0812B';
const GOLD_SOFT = '#F5ECD8';
const ACCENT_SOFT = '#E1F0EC';
const DEEP = '#0F3B36';
const LINE = '#DDD9CF';
const SURFACE = '#FFFFFF';
const MONO = 'ui-monospace, "SF Mono", Consolas, monospace';

const PAD_X = 140;

const fill: CSSProperties = {
  width: '100%',
  height: '100%',
  background: 'var(--osd-bg)',
  color: 'var(--osd-text)',
  fontFamily: 'var(--osd-font-body)',
  position: 'relative',
};

const Footer = () => {
  const { current, total } = useSlidePageNumber();
  return (
    <div
      style={{
        position: 'absolute',
        left: PAD_X,
        right: PAD_X,
        bottom: 36,
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: MONO,
        fontSize: 20,
        color: SUB,
      }}
    >
      <span>永豐金課程平台合作提案</span>
      <span>
        {String(current).padStart(2, '0')} / {String(total).padStart(2, '0')}
      </span>
    </div>
  );
};

// 內容頁外框：eyebrow ＋ 標題 ＋ 內容 ＋ 頁尾
const Sheet = ({
  eyebrow,
  title,
  children,
  note,
}: {
  eyebrow: string;
  title: ReactNode;
  children: ReactNode;
  note?: ReactNode;
}) => (
  <div style={{ ...fill, padding: `84px ${PAD_X}px 96px`, display: 'flex', flexDirection: 'column' }}>
    <div
      style={{
        fontSize: 24,
        letterSpacing: '0.2em',
        color: GOLD,
        fontWeight: 700,
        marginBottom: 18,
      }}
    >
      {eyebrow}
    </div>
    <h2
      style={{
        fontFamily: 'var(--osd-font-display)',
        fontWeight: 900,
        fontSize: 60,
        lineHeight: 1.3,
        margin: 0,
      }}
    >
      {title}
    </h2>
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: 0 }}>
      {children}
    </div>
    {note && <div style={{ fontSize: 22, color: SUB, lineHeight: 1.6 }}>{note}</div>}
    <Footer />
  </div>
);

const Accent = ({ children }: { children: ReactNode }) => (
  <span style={{ color: 'var(--osd-accent)' }}>{children}</span>
);
const Gold = ({ children }: { children: ReactNode }) => <span style={{ color: GOLD }}>{children}</span>;

const Tag = ({ tone, children }: { tone: 't' | 'g'; children: ReactNode }) => (
  <span
    style={{
      display: 'inline-block',
      alignSelf: 'flex-start',
      fontSize: 22,
      fontWeight: 700,
      letterSpacing: '0.06em',
      borderRadius: 6,
      padding: '4px 16px',
      marginBottom: 20,
      color: tone === 't' ? 'var(--osd-accent)' : GOLD,
      background: tone === 't' ? ACCENT_SOFT : GOLD_SOFT,
    }}
  >
    {children}
  </span>
);

const CARD: CSSProperties = {
  background: SURFACE,
  border: `1px solid ${LINE}`,
  borderRadius: 'var(--osd-radius)',
  padding: '36px 36px',
  display: 'flex',
  flexDirection: 'column',
};

// 標題＋段落卡片
const Card = ({ tag, tone = 't', n, title, children }: { tag?: string; tone?: 't' | 'g'; n?: string; title: string; children: ReactNode }) => (
  <div style={CARD}>
    {tag && (
      <Tag tone={tone}>{tag}</Tag>
    )}
    <h3 style={{ margin: '0 0 16px', fontSize: 33, fontWeight: 700 }}>
      {n && (
        <span style={{ fontFamily: 'var(--osd-font-display)', fontWeight: 900, color: 'var(--osd-accent)', marginRight: 12 }}>{n}</span>
      )}
      {title}
    </h3>
    <p style={{ margin: 0, fontSize: 27, color: SUB, lineHeight: 1.7 }}>{children}</p>
  </div>
);

// ▸ / ✓ 條列
const Row = ({ chk, lead, children }: { chk?: boolean; lead?: string; children?: ReactNode }) => (
  <div
    style={{
      position: 'relative',
      padding: '18px 0 18px 52px',
      borderBottom: `1px dashed ${LINE}`,
      fontSize: 29,
      lineHeight: 1.65,
    }}
  >
    <span
      style={{
        position: 'absolute',
        left: 0,
        fontWeight: 700,
        color: chk ? 'var(--osd-accent)' : GOLD,
      }}
    >
      {chk ? '✓' : '▸'}
    </span>
    {lead && <b>{lead}</b>}
    {children && <span style={{ color: SUB }}>{children}</span>}
  </div>
);

const TABLE_WRAP: CSSProperties = {
  background: SURFACE,
  border: `1px solid ${LINE}`,
  borderRadius: 'var(--osd-radius)',
  padding: '20px 32px',
};
const TH: CSSProperties = {
  fontSize: 23,
  letterSpacing: '0.08em',
  color: SUB,
  textAlign: 'left',
  fontWeight: 700,
  padding: '14px 20px',
  borderBottom: `3px solid ${DEEP}`,
};
const TD: CSSProperties = {
  padding: '18px 20px',
  borderBottom: `1px solid ${LINE}`,
  lineHeight: 1.55,
  verticalAlign: 'top',
  fontSize: 27,
};
const TD_NUM: CSSProperties = { ...TD, fontFamily: MONO, fontVariantNumeric: 'tabular-nums', fontSize: 25 };

// 合作模式卡（頂邊金/綠色條）
const Term = ({ k, v, topColor = GOLD, children }: { k: string; v: string; topColor?: string; children: ReactNode }) => (
  <div
    style={{
      background: SURFACE,
      border: `1px solid ${LINE}`,
      borderTop: `6px solid ${topColor}`,
      borderRadius: 'var(--osd-radius)',
      padding: '36px 36px',
    }}
  >
    <div style={{ fontSize: 24, color: topColor, fontWeight: 700, letterSpacing: '0.06em' }}>{k}</div>
    <div style={{ fontFamily: 'var(--osd-font-display)', fontWeight: 900, fontSize: 46, margin: '14px 0 18px' }}>{v}</div>
    <p style={{ margin: 0, fontSize: 26, color: SUB, lineHeight: 1.7 }}>{children}</p>
  </div>
);

const Quote = ({ children, by }: { children: ReactNode; by?: ReactNode }) => (
  <div
    style={{
      background: SURFACE,
      border: `1px solid ${LINE}`,
      borderLeft: `8px solid ${GOLD}`,
      borderRadius: '0 10px 10px 0',
      padding: '36px 44px',
      maxWidth: 1360,
    }}
  >
    <p
      style={{
        margin: 0,
        fontFamily: 'var(--osd-font-display)',
        fontWeight: 700,
        fontSize: 36,
        lineHeight: 1.65,
      }}
    >
      {children}
    </p>
    {by && <div style={{ marginTop: 18, fontSize: 24, color: SUB }}>{by}</div>}
  </div>
);

const GRID2: CSSProperties = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40 };
const GRID3: CSSProperties = { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 36 };
const GRID4: CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 32 };

/* ────────────────────────── 1・封面 ────────────────────────── */

const Cover: Page = () => (
  <div style={{ ...fill, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: `0 ${PAD_X + 20}px` }}>
    <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 12, background: GOLD }} />
    <div style={{ fontFamily: MONO, color: 'var(--osd-accent)', fontSize: 26, letterSpacing: '0.14em', marginBottom: 48 }}>
      課程平台合作提案・COURSE PARTNERSHIP
    </div>
    <h1
      style={{
        fontFamily: 'var(--osd-font-display)',
        fontWeight: 900,
        fontSize: 'var(--osd-size-hero)',
        lineHeight: 1.25,
        margin: '0 0 36px',
      }}
    >
      把「看懂新聞」
      <br />
      做成永豐金投資人的<Accent>日常能力</Accent>
    </h1>
    <p style={{ margin: 0, fontSize: 34, color: SUB, lineHeight: 1.85, maxWidth: 1240 }}>
      一套已完成的財經資訊素養課程 ＋ 一個可運作的新聞多空監測工具，
      <br />
      為永豐金課程平台帶來安全、差異化、能沉澱用戶的投資教育內容。
    </p>
    <div style={{ marginTop: 72, display: 'flex', gap: 72 }}>
      <CoverMeta k="提案對象" v="永豐金證券・課程/投資學習平台" />
      <CoverMeta k="提案內容" v="課程上架 × 工具整合 × 共同品牌" />
      <CoverMeta k="交付狀態" v="課程與工具皆已完成，可即刻上線" />
    </div>
  </div>
);

const CoverMeta = ({ k, v }: { k: string; v: string }) => (
  <div style={{ borderLeft: '5px solid var(--osd-accent)', paddingLeft: 24 }}>
    <div style={{ fontSize: 22, color: SUB, letterSpacing: '0.08em', marginBottom: 8 }}>{k}</div>
    <div style={{ fontSize: 28, fontWeight: 700 }}>{v}</div>
  </div>
);

/* ────────────────────────── 2・一頁摘要 ────────────────────────── */

const Summary: Page = () => (
  <Sheet
    eyebrow="EXECUTIVE SUMMARY"
    title="一頁看懂這個提案"
    note="合作形式彈性：可純上架分潤、可共同品牌獨家、可工具授權整合——第 12 頁提供三種模式。"
  >
    <div style={GRID2}>
      <div style={CARD}>
        <Tag tone="t">我們帶來什麼</Tag>
        <Row chk lead="入門課">：散戶新聞實戰課，零程式門檻，適合平台廣大用戶</Row>
        <Row chk lead="技術課">：Python 股市新聞情報系統，適合進階/工程背景用戶</Row>
        <Row chk lead="監測工具">：新聞利多/利空自動判讀，可作教材，亦可整合 App</Row>
      </div>
      <div style={CARD}>
        <Tag tone="g">永豐金得到什麼</Tag>
        <Row lead="用戶黏著">：從「開戶交易」延伸到「每天回來學習」</Row>
        <Row lead="平台差異化">：別家券商沒有的「新聞判讀能力」內容線</Row>
        <Row lead="法遵安全">：定位資訊素養教學，全程不涉個股買賣建議</Row>
        <Row lead="財經素養 PR">：呼應主管機關推動的投資人教育方向</Row>
      </div>
    </div>
  </Sheet>
);

/* ────────────────────────── 3・市場背景 ────────────────────────── */

const Market: Page = () => (
  <Sheet
    eyebrow="01・為什麼是現在"
    title={
      <>
        新一代投資人進場，
        <br />
        但「看新聞的能力」沒跟上
      </>
    }
    note="機會：券商平台擁有用戶與流量，但普遍缺少「教用戶怎麼消化資訊」的優質內容——這正是本提案補上的一塊。"
  >
    <div style={GRID3}>
      <Card title="年輕、行動優先的開戶潮">
        零股交易與定期定額普及，大量新手用行動 App 進場——他們最缺的不是下單功能，是判讀資訊的方法。
      </Card>
      <Card title="資訊過載">
        財經新聞 App、社群、群組訊息爆量，新手每天被大量真假難辨的消息淹沒，容易追高殺低。
      </Card>
      <Card title="教育需求正被政策推動">
        投資人教育是金融業與主管機關共同關注方向；能提供「安全、不涉建議」的素養內容，是券商的加分項。
      </Card>
    </div>
  </Sheet>
);

/* ────────────────────────── 4・痛點 ────────────────────────── */

const PainPoints: Page = () => (
  <Sheet
    eyebrow="02・平台的內容困境"
    title={
      <>
        券商做投資教育，
        <br />
        常卡在這三件事
      </>
    }
  >
    <div>
      <Row lead="內容同質化">
        ——各家都在講技術分析、K 線、財報基礎，用戶看膩了，也記不住是哪一家教的。
      </Row>
      <Row lead="法遵綁手綁腳">
        ——只要碰個股就有投顧法風險，內容團隊做得綁手綁腳，往往流於空泛。
      </Row>
      <Row lead="看完就走，沉澱不了用戶">
        ——影片看完沒有「可以每天用的工具或習慣」，無法把觀看轉成回訪與活躍。
      </Row>
    </div>
    <div style={{ marginTop: 44 }}>
      <Quote by="本提案的三個資產，正是為了同時解掉這三個結。">
        用戶要的不是「更多內容」，是一個「每天都想打開、而且合規安全」的學習理由。
      </Quote>
    </div>
  </Sheet>
);

/* ────────────────────────── 5・三個資產 ────────────────────────── */

const Assets: Page = () => (
  <Sheet
    eyebrow="03・我們帶來的三個資產"
    title={
      <>
        一條完整的<Accent>投資素養內容線</Accent>
      </>
    }
    note="三者形成漏斗：入門課吸引廣大用戶 → 工具養成每日回訪習慣 → 進階課沉澱高價值用戶。"
  >
    <div style={GRID3}>
      <Card tag="資產一・入門" tone="t" n="A" title="散戶新聞實戰課">
        零程式門檻、6 單元教學投影片。教用戶用對新聞、避開四大陷阱、建立每日看盤 SOP。適合平台最大宗的一般用戶。
      </Card>
      <Card tag="資產二・進階" tone="t" n="B" title="Python 情報系統課">
        8 模組實戰，串接新聞 API 與官方公告、自動去重、量化熱度。適合工程背景與進階用戶，拉高平台專業形象。
      </Card>
      <Card tag="資產三・工具" tone="g" n="C" title="新聞多空監測工具">
        已可運作的系統：自動判讀新聞利多/利空、彙整個股多空榜。可作課程實作素材，亦可授權整合進大戶投等 App。
      </Card>
    </div>
  </Sheet>
);

/* ────────────────────────── 6・資產A 入門課 ────────────────────────── */

const AssetA: Page = () => (
  <Sheet
    eyebrow="資產 A・入門課"
    title="散戶新聞實戰課"
    note="形式：38 頁教學投影片 ＋ 4 個實戰練習。全課以「教學示例」呈現個股，封面與高風險頁均有免責聲明。"
  >
    <p style={{ margin: '20px 0 32px', fontSize: 29, color: SUB, lineHeight: 1.7 }}>
      為平台最大宗的一般投資人設計。不用寫程式、看得懂中文就能上，直接提升「看盤效率」。
    </p>
    <div style={TABLE_WRAP}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ ...TH, width: 360 }}>單元</th>
            <th style={TH}>學員帶走的能力</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={TD}>資訊鏈</td>
            <td style={TD}>看懂一則新聞到你手上經過幾站、延遲多久——接受「新聞是落後指標」</td>
          </tr>
          <tr>
            <td style={TD}>資訊源頭</td>
            <td style={TD}>建立自己的三來源清單，分清第一手 vs 轉載</td>
          </tr>
          <tr>
            <td style={TD}>5 分鐘判讀 SOP</td>
            <td style={TD}>五個固定問題，快速判斷一則新聞值不值得理</td>
          </tr>
          <tr>
            <td style={TD}>熱度思維</td>
            <td style={TD}>用新聞量的「變化」讀市場關注，避開擁擠行情</td>
          </tr>
          <tr>
            <td style={TD}>每日例行流程</td>
            <td style={TD}>盤前 30 分／盤中兩原則／盤後 15 分的完整 SOP</td>
          </tr>
          <tr>
            <td style={{ ...TD, borderBottom: 'none' }}>陷阱與驗證</td>
            <td style={{ ...TD, borderBottom: 'none' }}>辨識新聞陷阱、建立 T+1/T+5 事後驗證習慣</td>
          </tr>
        </tbody>
      </table>
    </div>
  </Sheet>
);

/* ────────────────────────── 7・資產B 技術課 ────────────────────────── */

const AssetB: Page = () => (
  <Sheet
    eyebrow="資產 B・進階技術課"
    title="用 Python 打造股市新聞情報系統"
    note="定位：進階付費內容，客單較高（原定價帶 NT$2,000–3,000），與入門課構成「免費/低價引流 → 進階變現」的雙層結構。"
  >
    <div style={GRID2}>
      <div style={CARD}>
        <Tag tone="t">課程規模</Tag>
        <Row chk lead="8 模組・45 堂・8–10 小時" />
        <Row chk lead="附完整可執行 GitHub 專案（含測試與 CI）" />
        <Row chk lead="串接鉅亨 API、10+ 家媒體、官方公告" />
        <Row chk lead="去重、時區、PIT 儲存、熱度量化全流程" />
      </div>
      <div style={CARD}>
        <Tag tone="g">對平台的意義</Tag>
        <Row lead="拉高專業形象">：市面極少見的「生產級」財經工程課</Row>
        <Row lead="吸引高價值客群">：工程師、量化愛好者、年輕高資產族</Row>
        <Row lead="內容護城河">：一年免費更新承諾，內容不易被複製</Row>
      </div>
    </div>
  </Sheet>
);

/* ────────────────────────── 8・資產C 工具 demo ────────────────────────── */

const DEMO_LINE: CSSProperties = { margin: 0 };
const UP = { color: '#5FD0AE' };
const DN = { color: '#E88A6F' };
const DIM = { color: '#7C9188' };
const HD = { color: '#D6A94E', fontWeight: 700 as const };

const AssetC: Page = () => (
  <Sheet
    eyebrow="資產 C・監測工具（已可運作）"
    title={
      <>
        新聞利多/利空監測——<Accent>不是概念，是跑出來的</Accent>
      </>
    }
    note="規則透明可解釋：每則判定都能列出命中詞與權重；「市場傳出/可望」等傳聞用語自動折價，呼應課程「事實＞預期＞傳聞」的原則。可作課程實作教材，或作為 App 內的「今日新聞情緒」小工具。"
  >
    <div
      style={{
        background: DEEP,
        borderRadius: 'var(--osd-radius)',
        padding: '36px 44px',
        fontFamily: MONO,
        fontSize: 24,
        lineHeight: 1.62,
        color: '#DCE8E4',
      }}
    >
      <p style={{ ...DEMO_LINE, ...HD }}>=== 新聞利多/利空監測 2026-07-03 ===</p>
      <p style={DEMO_LINE}>總計：利多 3 則｜利空 2 則｜中性 1 則</p>
      <p style={{ ...DEMO_LINE, ...HD, marginTop: 24 }}>--- 個股利多榜 ---</p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;2330 台積電&nbsp;&nbsp;<span style={UP}>net=+25.0&nbsp;&nbsp;利多×2</span>
      </p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style={UP}>[利多+15]</span> 台積電上修財測 產能滿載供不應求
      </p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style={UP}>[利多+10]</span> 外資調升目標價 獲利優於預期
      </p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;2303 聯電&nbsp;&nbsp;&nbsp;&nbsp;<span style={UP}>net= +2.0&nbsp;&nbsp;利多×1</span>
      </p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style={UP}>[利多 +2]</span> 市場傳出可望取得大單&nbsp;&nbsp;
        <span style={DIM}>（傳聞→分數折半）</span>
      </p>
      <p style={{ ...DEMO_LINE, ...HD, marginTop: 24 }}>--- 個股利空榜 ---</p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;2454 聯發科&nbsp;&nbsp;<span style={DN}>net= -6.0&nbsp;&nbsp;利空×1</span>
      </p>
      <p style={DEMO_LINE}>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style={DN}>[利空 -6]</span> 聯發科遭砍單 全年展望轉保守
      </p>
    </div>
  </Sheet>
);

/* ────────────────────────── 9・整合場景 ────────────────────────── */

const Integration: Page = () => (
  <Sheet
    eyebrow="資產 C・整合場景"
    title="它可以長在永豐金的平台裡"
    note="※ 所有整合情境均以「新聞語意整理／資訊呈現」為定位，附來源原文連結與免責聲明，不對個股做買賣評價；上線前送貴公司法遵確認。"
  >
    <div style={GRID3}>
      <Card tag="情境一・課程實作" tone="t" title="當作教材">
        入門/進階課學員照著跑，親手產出自己的多空榜——把「看完就走」變成「動手做出成果」。
      </Card>
      <Card tag="情境二・App 小工具" tone="t" title="今日新聞情緒">
        整合進大戶投等 App，用戶查個股時附上「近期新聞多空傾向」與來源連結，提升查詢黏著。
      </Card>
      <Card tag="情境三・自選股推播" tone="g" title="盤前多空摘要">
        依用戶自選股，每日盤前推送「你的持股昨夜有哪些利多/利空新聞」，創造每日回訪理由。
      </Card>
    </div>
  </Sheet>
);

/* ────────────────────────── 10・對永豐金的價值 ────────────────────────── */

const ValueCard = ({ title, big, small, children }: { title: string; big: string; small: string; children: ReactNode }) => (
  <div style={CARD}>
    <h3 style={{ margin: '0 0 18px', fontSize: 31, fontWeight: 700 }}>{title}</h3>
    <div
      style={{
        fontFamily: 'var(--osd-font-display)',
        fontWeight: 900,
        fontSize: 58,
        color: 'var(--osd-accent)',
        lineHeight: 1.05,
        marginBottom: 20,
      }}
    >
      {big}
      <span style={{ fontSize: 24, color: SUB, fontFamily: 'var(--osd-font-body)', fontWeight: 400, marginLeft: 8 }}>{small}</span>
    </div>
    <p style={{ margin: 0, fontSize: 25, color: SUB, lineHeight: 1.65 }}>{children}</p>
  </div>
);

const Value: Page = () => (
  <Sheet
    eyebrow="04・對永豐金的價值"
    title="券商為什麼要做這個"
    note="關鍵：這些價值都不需要碰「投資建議」就能達成——靠的是「教方法、給工具」，而非「報明牌」。"
  >
    <div style={GRID4}>
      <ValueCard title="用戶黏著 ↑" big="每日" small="回訪理由">
        從交易工具變成「每天想打開的學習與情報入口」。
      </ValueCard>
      <ValueCard title="平台差異化" big="獨有" small="內容線">
        「新聞判讀能力」是別家券商沒有的定位。
      </ValueCard>
      <ValueCard title="導流交易" big="素養" small="→ 信心">
        更懂資訊的用戶更敢參與市場，活躍度提升。
      </ValueCard>
      <ValueCard title="品牌與 PR" big="素養" small="形象">
        呼應投資人教育政策，正向品牌聯想。
      </ValueCard>
    </div>
  </Sheet>
);

/* ────────────────────────── 11・法遵 ────────────────────────── */

const Compliance: Page = () => (
  <Sheet
    eyebrow="05・法遵定位（券商最在意的一頁）"
    title={
      <>
        為什麼這對永豐金是<Accent>安全</Accent>的內容
      </>
    }
    note="我方已備有完整法遵設計文件（投顧法、著作權、爬蟲、個資四大紅線），可提供貴公司法遵團隊先行審閱。"
  >
    <div>
      <Row chk lead="定位為資訊素養與程式技術教學，非投資分析或投資建議">
        ——全程不對任何個股做買賣評價、不喊目標價、不報進出點。
      </Row>
      <Row chk lead="個股一律為「教學示例」">
        ——封面與高風險頁均有免責聲明；工具輸出每次附「非投資建議」聲明與原文連結。
      </Row>
      <Row chk lead="教「怎麼判讀」而非「該買什麼」">
        ——把判斷權還給用戶，這正是與投顧業務的清楚切割線。
      </Row>
      <Row chk lead="上線前全數送貴公司法遵審閱">
        ——內容、行銷素材、App 整合文案，配合永豐金法遵流程調整並留存紀錄。
      </Row>
    </div>
  </Sheet>
);

/* ────────────────────────── 12・合作模式 ────────────────────────── */

const Models: Page = () => (
  <Sheet
    eyebrow="06・合作模式（三選一或組合）"
    title="三種合作深度"
    note="建議路徑：先以模式一或二快速上線驗證，成效好再談模式三的 App 整合——風險低、可分階段。"
  >
    <div style={GRID3}>
      <Term k="模式一・最輕" v="課程上架分潤">
        課程放上永豐金學習平台，依成交分潤。最快上線，驗證用戶反應。
      </Term>
      <Term k="模式二・推薦" v="共同品牌獨家" topColor="#127A6B">
        永豐金 × 課程共同掛名、平台獨家；可客製「永豐金用戶專屬版」內容與行銷。
      </Term>
      <Term k="模式三・最深" v="工具授權整合">
        將多空監測工具授權整合進 App（今日情緒／自選股推播），採授權金或年費。
      </Term>
    </div>
  </Sheet>
);

/* ────────────────────────── 13・商業條件 ────────────────────────── */

const Commercial: Page = () => (
  <Sheet
    eyebrow="07・商業條件（討論起點）"
    title="彈性的分潤與授權架構"
    note="以上為協商起點，實際條件依雙方合約為準。我方亦可接受「先小規模試營運、看數據再定案」的合作節奏。"
  >
    <div style={TABLE_WRAP}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={TH}>模式</th>
            <th style={TH}>計費方式</th>
            <th style={TH}>建議區間</th>
            <th style={TH}>備註</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={TD}>課程上架分潤</td>
            <td style={TD}>依課程成交拆分</td>
            <td style={TD_NUM}>平台 30–50%</td>
            <td style={TD}>依導流與獨家程度調整</td>
          </tr>
          <tr style={{ background: ACCENT_SOFT }}>
            <td style={TD}>共同品牌獨家</td>
            <td style={TD}>分潤 + 保底</td>
            <td style={TD_NUM}>另議</td>
            <td style={TD}>含專屬版客製與聯合行銷資源</td>
          </tr>
          <tr>
            <td style={{ ...TD, borderBottom: 'none' }}>工具授權整合</td>
            <td style={{ ...TD, borderBottom: 'none' }}>年度授權金 / 月費</td>
            <td style={{ ...TD_NUM, borderBottom: 'none' }}>另議</td>
            <td style={{ ...TD, borderBottom: 'none' }}>依整合深度、API 用量與維運範圍</td>
          </tr>
        </tbody>
      </table>
    </div>
  </Sheet>
);

/* ────────────────────────── 14・時程 ────────────────────────── */

const Timeline: Page = () => (
  <Sheet
    eyebrow="08・上線時程"
    title="四階段，最快一季內上線"
    note="課程與工具皆已完成，時程主要花在「法遵確認」與「品牌客製」，而非從零製作內容——這是本提案能快速上線的關鍵。"
  >
    <div style={TABLE_WRAP}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ ...TH, width: 420 }}>階段</th>
            <th style={{ ...TH, width: 280 }}>時程</th>
            <th style={TH}>工作</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={TD}>① 對齊與法遵</td>
            <td style={TD_NUM}>2–3 週</td>
            <td style={TD}>確認合作模式；課程與工具送法遵審閱、依意見調整</td>
          </tr>
          <tr>
            <td style={TD}>② 內容客製</td>
            <td style={TD_NUM}>3–4 週</td>
            <td style={TD}>永豐金專屬版包裝、片頭品牌、平台上架素材</td>
          </tr>
          <tr>
            <td style={TD}>③ 試營運</td>
            <td style={TD_NUM}>4 週</td>
            <td style={TD}>入門課先上，觀察觀看/完課/回訪數據</td>
          </tr>
          <tr>
            <td style={{ ...TD, borderBottom: 'none' }}>④ 擴展</td>
            <td style={{ ...TD_NUM, borderBottom: 'none' }}>後續</td>
            <td style={{ ...TD, borderBottom: 'none' }}>加上進階課；成效佳則啟動工具 App 整合</td>
          </tr>
        </tbody>
      </table>
    </div>
  </Sheet>
);

/* ────────────────────────── 15・為什麼是我們 & CTA ────────────────────────── */

const Closing: Page = () => (
  <Sheet
    eyebrow="09・為什麼是我們 & 下一步"
    title={
      <>
        成品已在手上，不是一份<Gold>企劃書</Gold>而已
      </>
    }
    note="本提案內容為合作討論用途；一切課程與工具均定位為投資知識與資訊素養教學，不構成投資分析或買賣建議。品牌名稱僅為說明合作對象，實際合作以雙方正式合約為準。"
  >
    <div style={GRID2}>
      <div style={CARD}>
        <Tag tone="t">交付能力</Tag>
        <Row chk lead="兩門課程 + 一套工具">，皆已完成、可即刻示範</Row>
        <Row chk lead="完整程式碼含測試與 CI">，工程品質可受檢視</Row>
        <Row chk lead="已備完整法遵設計文件">，供貴公司先行審閱</Row>
      </div>
      <div style={CARD}>
        <Tag tone="g">下一步（提議）</Tag>
        <Row lead="30 分鐘線上 demo">：現場展示課程與工具實跑</Row>
        <Row lead="交付法遵文件">：讓貴公司法遵團隊先評估</Row>
        <Row lead="選定試營運模式">：從模式一/二挑一，訂上線里程碑</Row>
      </div>
    </div>
    <div style={{ marginTop: 40 }}>
      <Quote>
        讓永豐金的投資人，不只在你的平台<Accent>下單</Accent>，也在你的平台<Accent>變強</Accent>。
      </Quote>
    </div>
  </Sheet>
);

/* ────────────────────────── 轉場：全簡報同一 DNA ────────────────────────── */

const EASE_OUT = 'cubic-bezier(0, 0, 0.2, 1)';
const EASE_IN = 'cubic-bezier(0.4, 0, 1, 1)';

export const transition: SlideTransition = {
  duration: 200,
  exit: {
    duration: 140,
    easing: EASE_IN,
    keyframes: [
      { opacity: 1, transform: 'translateY(0)' },
      { opacity: 0, transform: 'translateY(-4px)' },
    ],
  },
  enter: {
    duration: 200,
    delay: 80,
    easing: EASE_OUT,
    keyframes: [
      { opacity: 0, transform: 'translateY(6px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ],
  },
};

Cover.transition = {
  duration: 280,
  exit: {
    duration: 160,
    easing: EASE_IN,
    keyframes: [
      { opacity: 1, transform: 'translateY(0)' },
      { opacity: 0, transform: 'translateY(-6px)' },
    ],
  },
  enter: {
    duration: 280,
    delay: 100,
    easing: EASE_OUT,
    keyframes: [
      { opacity: 0, transform: 'translateY(12px)', filter: 'blur(4px)' },
      { opacity: 1, transform: 'translateY(0)', filter: 'blur(0)' },
    ],
  },
};

export const meta: SlideMeta = {
  title: '永豐金課程平台合作提案',
  createdAt: '2026-07-14T14:12:35.401Z',
};

export default [
  Cover,
  Summary,
  Market,
  PainPoints,
  Assets,
  AssetA,
  AssetB,
  AssetC,
  Integration,
  Value,
  Compliance,
  Models,
  Commercial,
  Timeline,
  Closing,
] satisfies Page[];

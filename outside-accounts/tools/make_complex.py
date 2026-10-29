"""Build two large, realistic outside statements that stress the reader.

C1 meridian-consolidated-statement-kaplan.pdf (28 pages, text layer)
  p1     summary: account value, owner, period, change in value
  p2     asset allocation shown ONLY as a pie chart (raster image, legend without percentages)
  p3     equity sector mix shown ONLY as a bar chart (vector drawing, axis ticks, no data labels)
  p4-8   holdings across 5 pages: section headers, section subtotals, header not repeated on one page,
         bond descriptions that wrap onto a second line, bonds priced per 100 of par
  p9-10  account activity (dates, buys, sells, dividends) - numbers that are NOT holdings
  p11    realized gain and loss summary
  p12    fund expense and fee schedule tables - more numbers that are NOT holdings
  p13-28 disclosures, glossary and product information
C2 meridian-ira-scan-kaplan.pdf (12 pages, image only): the same layout at smaller scale, scanned.

samples/truth_complex.json records holdings, chart values and page types.
Run: python tools/make_complex.py
"""
from __future__ import annotations

import io
import json
import random
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'samples'
SEC = {a['sym']: a for a in json.loads((ROOT / 'app/data/securities.json').read_text())['approved']}
random.seed(11)
W, H = letter

EQUITY = [  # sym, name, qty, price, cost
    ('AAPL', 'Apple Inc', 1200, 228.50, 151000), ('MSFT', 'Microsoft Corp', 400, 512.40, 98000), ('AMZN', 'Amazon.com Inc', 900, 221.30, 120500),
    ('GOOG', 'Alphabet Inc Class C', 1000, 245.10, 141000), ('META', 'Meta Platforms Inc', 260, 712.80, 88000), ('AVGO', 'Broadcom Inc', 500, 335.20, 41000),
    ('JPM', 'JPMorgan Chase & Co', 700, 298.40, 120000), ('JNJ', 'Johnson & Johnson', 600, 178.90, 96000), ('PG', 'Procter & Gamble Co', 650, 152.30, 91000),
    ('KO', 'Coca-Cola Co', 1400, 68.70, 79000), ('HD', 'Home Depot Inc', 240, 402.10, 70500), ('COST', 'Costco Wholesale Corp', 110, 935.60, 61000),
    ('UNH', 'UnitedHealth Group Inc', 220, 341.20, 98000), ('CVX', 'Chevron Corp', 520, 158.40, 76000), ('TXN', 'Texas Instruments Inc', 380, 188.60, 62000),
    ('QCOM', 'Qualcomm Inc', 450, 162.30, 58000), ('LOW', "Lowe's Companies Inc", 300, 254.70, 61000), ('ABBV', 'AbbVie Inc', 420, 221.90, 57000),
    ('MRK', 'Merck & Co Inc', 600, 86.40, 62000), ('PFE', 'Pfizer Inc', 1800, 25.10, 61000),
]
FUNDS = [
    ('VTI', 'US Total Market ETF', 900, 318.20, 210000), ('SCHD', 'US Dividend Equity ETF', 6000, 27.40, 152000), ('IJH', 'Core S&P Mid-Cap ETF', 2500, 63.10, 131000),
    ('QQQ', 'Nasdaq-100 ETF', 350, 512.80, 120000), ('VNQ', 'Real Estate ETF', 900, 92.10, 86000), ('ARKK', 'Innovation ETF', 1500, 62.40, 141000),
    ('IEFA', 'Core MSCI EAFE ETF', 4200, 81.40, 280000), ('VWO', 'Emerging Markets ETF', 3300, 49.60, 150000), ('QZLGX', 'Quill Zenith Large Growth Fund', 3100, 41.20, 98000),
    ('ORGLX', 'Orion Global Leaders Fund Class A', 4100, 23.85, 90000),
]
BONDS = [  # description (2 lines), par, price per 100, cost
    ('New York St Dorm Auth Rev 5.000% 03/15/2034', 'CUSIP X9A41C7Q2 · Moody’s Aa1 · Callable 03/15/2032', 150000, 108.42, 158000),
    ('California St GO 4.000% 10/01/2036', 'CUSIP X93B2E8L1 · Moody’s Aa2', 125000, 102.15, 127500),
    ('Texas Water Dev Board Rev 4.500% 10/15/2038', 'CUSIP X9C77D2M5 · S&P AAA', 100000, 104.30, 101000),
    ('US Treasury Note 4.125% 11/15/2032', 'CUSIP X9T22W4N8 · Government', 200000, 100.84, 198500),
    ('US Treasury Note 3.875% 08/15/2034', 'CUSIP X9T48R1K3 · Government', 175000, 98.62, 176000),
    ('Apple Inc 3.250% 02/23/2031 Corporate Bond', 'CUSIP X9P11A9F6 · Moody’s Aaa', 100000, 97.40, 99200),
    ('JPMorgan Chase & Co 4.950% 06/01/2033 Corporate Bond', 'CUSIP X9J55H3T0 · Moody’s A1', 120000, 101.85, 121000),
]
CASH = [('Meridian Government Money Market Fund', 186412.55), ('Bank Deposit Sweep', 42150.00)]
INTL = {'IEFA', 'VWO'}
SECTOR_NAMES = {'TECH': 'Information technology', 'FIN': 'Financials', 'HLTH': 'Health care', 'STAP': 'Consumer staples', 'DISC': 'Consumer discretionary',
                'COMM': 'Communication services', 'ENER': 'Energy', 'INDU': 'Industrials'}
PIE_COLORS = ['#1f5fa8', '#5aa7d6', '#d98a2b', '#3e9b6a', '#8f8f8f']
BAR_COLOR = '#2b6cb0'


def holdings():
    rows = []
    for sym, name, q, p, c in EQUITY:
        rows.append(dict(section='Equities', sub='Common stocks', sym=sym, desc=name, desc2=None, qty=q, price=p, value=round(q * p, 2), cost=c))
    for sym, name, q, p, c in FUNDS:
        rows.append(dict(section='Equities', sub='Exchange-traded and mutual funds', sym=sym, desc=name, desc2=None, qty=q, price=p, value=round(q * p, 2), cost=c))
    for d1, d2, par, p, c in BONDS:
        rows.append(dict(section='Fixed income', sub='Bonds', sym=None, desc=d1, desc2=d2, qty=par, price=p, value=round(par * p / 100, 2), cost=c))
    for name, v in CASH:
        rows.append(dict(section='Cash and equivalents', sub='Cash', sym=None, desc=name, desc2=None, qty=v, price=1.00, value=v, cost=v))
    return rows


def allocation(rows):
    tot = sum(r['value'] for r in rows)
    us = sum(r['value'] for r in rows if r['section'] == 'Equities' and r['sym'] not in INTL)
    intl = sum(r['value'] for r in rows if r['sym'] in INTL)
    fi = sum(r['value'] for r in rows if r['section'] == 'Fixed income')
    cash = sum(r['value'] for r in rows if r['section'] == 'Cash and equivalents')
    return [('U.S. equity', us / tot * 100), ('International equity', intl / tot * 100), ('Fixed income', fi / tot * 100), ('Cash and equivalents', cash / tot * 100)]


def sectors(rows):
    s = {}
    for r in rows:
        if r['sub'] == 'Common stocks':
            k = SEC[r['sym']].get('sector') or 'OTHER'
            s[k] = s.get(k, 0) + r['value']
    tot = sum(s.values())
    return sorted(((SECTOR_NAMES.get(k, k), v / tot * 100) for k, v in s.items()), key=lambda x: -x[1])


def pie_png(alloc, size=(7.2, 4.0), dpi=150):
    fig, ax = plt.subplots(figsize=size, dpi=dpi)
    ax.pie([v for _, v in alloc], colors=PIE_COLORS[:len(alloc)], startangle=90, counterclock=False, wedgeprops=dict(linewidth=1.5, edgecolor='white'))
    ax.set_aspect('equal')
    ax.legend([l for l, _ in alloc], loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=11, handlelength=1.1, handleheight=1.1)
    fig.subplots_adjust(left=0.02, right=0.62)
    b = io.BytesIO(); fig.savefig(b, format='png', facecolor='white'); plt.close(fig)
    return b.getvalue()


def bar_drawing(items, w=470, h=230):
    """Horizontal bar chart drawn as vector shapes: category labels, bars, axis ticks. No value labels."""
    d = Drawing(w, h)
    left, right, top, bottom = 165, w - 20, h - 10, 28
    vmax = 40
    rowh = (top - bottom) / len(items)
    for i, (lab, v) in enumerate(items):
        y = top - (i + 1) * rowh + rowh * 0.2
        d.add(String(left - 8, y + rowh * 0.22, lab, fontName='Helvetica', fontSize=9, textAnchor='end'))
        d.add(Rect(left, y, (right - left) * v / vmax, rowh * 0.6, fillColor=HexColor(BAR_COLOR), strokeColor=None))
    d.add(Line(left, bottom, right, bottom, strokeColor=HexColor('#888888'), strokeWidth=0.6))
    for t in range(0, vmax + 1, 10):
        x = left + (right - left) * t / vmax
        d.add(Line(x, bottom, x, bottom - 4, strokeColor=HexColor('#888888'), strokeWidth=0.6))
        d.add(String(x, bottom - 15, f'{t}%', fontName='Helvetica', fontSize=8, textAnchor='middle'))
    return d


DISCLOSURE_TOPICS = ['Important information about your statement', 'Pricing and valuation', 'Cost basis reporting', 'Securities Investor Protection',
                     'Margin and lending', 'Mutual fund and ETF disclosures', 'Fixed income disclosures', 'Annuity and insurance products',
                     'Order routing and execution', 'Business continuity', 'Privacy notice', 'Glossary of terms', 'Fee schedule notes',
                     'Complaints and contact information', 'Tax reporting', 'Product information']
SENT = ['Prices shown are obtained from sources believed to be reliable but are not guaranteed; values of securities that are not actively traded may be estimated.',
        'Securities in your account are protected up to $500,000, including $250,000 for claims for cash, under the protection program described here.',
        'Advisory fees range from 0.25% to 1.50% of assets each year, billed quarterly in arrears, and are described in the program brochure.',
        'Cost basis is shown for information only; for covered securities it is reported to tax authorities on Form 1099-B within 45 days of year end.',
        'Bond ratings of Aaa through Baa3 are considered investment grade; ratings may change and are not a recommendation to buy, sell or hold.',
        'Estimated annual income and yield are calculated from the most recent distribution and may differ materially from actual income received.',
        'Mutual fund shares may be subject to a 1.00% deferred sales charge if redeemed within 12 months of purchase, in addition to annual expenses of 0.05% to 1.25%.',
        'Money market funds seek to preserve the value of your investment at $1.00 per share, but it is possible to lose money by investing in them.',
        'Margin interest is charged at rates from 6.25% to 11.75% depending on the debit balance, calculated daily and posted monthly.',
        'Orders for 100 shares or more may be routed to market centers that provide payment for order flow; quarterly reports are available on request.',
        'Please review this statement promptly and report any discrepancy within 10 days of receipt by calling 1-800-555-0142.',
        'Past performance does not guarantee future results; investments are not deposits, are not insured and may lose value.']


def wrap(c, text, x, y, width, font='Helvetica', size=8.4, lead=11.2):
    words, line = text.split(), ''
    for w_ in words:
        t = (line + ' ' + w_).strip()
        if c.stringWidth(t, font, size) > width:
            c.drawString(x, y, line); y -= lead; line = w_
        else:
            line = t
    if line:
        c.drawString(x, y, line); y -= lead
    return y


def page_frame(c, n, total, title):
    c.setFont('Helvetica-Bold', 12); c.drawString(40, H - 42, 'Meridian Private Wealth')
    c.setFont('Helvetica', 8); c.drawRightString(W - 40, H - 42, f'Account XXXX-6604 · {title}')
    c.drawRightString(W - 40, 28, f'Page {n} of {total}')
    c.drawString(40, 28, 'Statement period: July 1, 2026 to September 30, 2026')


COLS = [(40, 'Description', 'l'), (268, 'Symbol', 'l'), (340, 'Quantity', 'r'), (392, 'Price', 'r'), (462, 'Market Value', 'r'), (522, 'Cost Basis', 'r'), (572, '% of Port.', 'r')]


def draw_header(c, y):
    c.setFont('Helvetica-Bold', 7.6)
    for x, t, a in COLS:
        (c.drawString if a == 'l' else c.drawRightString)(x, y, t)
    c.setLineWidth(0.4); c.line(40, y - 4, W - 40, y - 4)
    return y - 16


def build_statement(path, rows, total_pages, owner, acct_type, scale_disclosures, include_bar=True, holdings_per_page=13):
    tot = round(sum(r['value'] for r in rows), 2)
    alloc = allocation(rows)
    sect = sectors(rows)
    c = canvas.Canvas(str(path), pagesize=letter)
    pages = []
    n = 1
    # p1 summary
    page_frame(c, n, total_pages, 'Summary'); y = H - 80
    c.setFont('Helvetica-Bold', 16); c.drawString(40, y, 'Consolidated Account Statement'); y -= 26
    c.setFont('Helvetica', 10)
    for t in [f'Prepared for: {owner}', f'Account type: {acct_type}', 'Account number: XXXX-6604', 'Statement period: July 1, 2026 to September 30, 2026',
              f'Total account value: ${tot:,.2f}']:
        c.drawString(40, y, t); y -= 15
    y -= 10; c.setFont('Helvetica-Bold', 11); c.drawString(40, y, 'Change in account value'); y -= 16; c.setFont('Helvetica', 9.5)
    beg = round(tot * 0.962, 2)
    for lab, v in [('Beginning value', beg), ('Deposits', 25000.00), ('Withdrawals', -40000.00), ('Income received', round(tot * 0.0061, 2)),
                   ('Change in market value', round(tot - beg - 25000 + 40000 - tot * 0.0061, 2)), ('Ending value', tot)]:
        c.drawString(56, y, lab); c.drawRightString(330, y, f'{v:,.2f}'); y -= 13
    y -= 12; c.setFont('Helvetica', 9); c.drawString(40, y, 'Your asset allocation is shown on the next page. Holdings detail begins on page 4.')
    c.showPage(); pages.append('summary'); n += 1
    # p2 pie chart (raster) - allocation is only in the chart
    page_frame(c, n, total_pages, 'Asset allocation'); y = H - 80
    c.setFont('Helvetica-Bold', 13); c.drawString(40, y, 'Asset allocation'); y -= 14
    c.setFont('Helvetica', 9); c.drawString(40, y, 'Based on market value as of September 30, 2026.')
    img = ImageReader(io.BytesIO(pie_png(alloc)))
    c.drawImage(img, 40, y - 300, width=520, height=289)
    c.showPage(); pages.append('chart'); n += 1
    # p3 bar chart (vector)
    if include_bar:
        page_frame(c, n, total_pages, 'Equity sectors'); y = H - 80
        c.setFont('Helvetica-Bold', 13); c.drawString(40, y, 'Common stocks by sector'); y -= 14
        c.setFont('Helvetica', 9); c.drawString(40, y, 'Percent of common stock market value.')
        renderPDF.draw(bar_drawing(sect), c, 50, y - 260)
        c.showPage(); pages.append('chart'); n += 1
    # holdings pages
    i, sec, sub = 0, None, None
    first = True
    hp = 0
    while i < len(rows):
        page_frame(c, n, total_pages, 'Holdings'); y = H - 76
        c.setFont('Helvetica-Bold', 12); c.drawString(40, y, 'Holdings detail' + ('' if first else ' (continued)')); y -= 20
        if hp != 2:   # one continuation page has no repeated column header
            y = draw_header(c, y)
        else:
            y -= 4
        cnt = 0
        while i < len(rows) and cnt < holdings_per_page:
            r = rows[i]
            if r['section'] != sec:
                if sec is not None:
                    st = sum(x['value'] for x in rows if x['section'] == sec)
                    c.setFont('Helvetica-Bold', 8); c.drawString(40, y, f'Total {sec}'); c.drawRightString(462, y, f'{st:,.2f}'); c.drawRightString(572, y, f'{st / tot * 100:.1f}%'); y -= 18
                sec = r['section']; c.setFont('Helvetica-Bold', 9); c.drawString(40, y, sec.upper()); y -= 13
            if r['sub'] != sub:
                sub = r['sub']; c.setFont('Helvetica-Oblique', 8); c.drawString(40, y, sub); y -= 12
            c.setFont('Helvetica', 7.6)
            q = f"{r['qty']:,.2f}" if r['section'] == 'Cash and equivalents' else f"{r['qty']:,.0f}"
            vals = [r['desc'], r['sym'] or '', q, f"{r['price']:,.2f}", f"{r['value']:,.2f}", f"{r['cost']:,.2f}", f"{r['value'] / tot * 100:.1f}%"]
            for (x, _, a), v in zip(COLS, vals):
                (c.drawString if a == 'l' else c.drawRightString)(x, y, v)
            y -= 11
            if r['desc2']:
                c.setFont('Helvetica', 6.8); c.drawString(48, y, r['desc2']); y -= 11
            y -= 3
            i += 1; cnt += 1
        if i >= len(rows):
            st = sum(x['value'] for x in rows if x['section'] == sec)
            c.setFont('Helvetica-Bold', 8); c.drawString(40, y, f'Total {sec}'); c.drawRightString(462, y, f'{st:,.2f}'); c.drawRightString(572, y, f'{st / tot * 100:.1f}%'); y -= 18
            c.setFont('Helvetica-Bold', 8.5); c.drawString(40, y, 'Total Holdings'); c.drawRightString(462, y, f'{tot:,.2f}'); c.drawRightString(572, y, '100.0%')
        c.showPage(); pages.append('holdings'); n += 1; first = False; hp += 1
    # activity
    acts = [('07/02/2026', 'Dividend', 'Johnson & Johnson', 'JNJ', '', '', '744.00'), ('07/15/2026', 'Bought', 'Core MSCI EAFE ETF', 'IEFA', '200', '79.85', '-15,970.00'),
            ('07/21/2026', 'Sold', 'Intel Corp', 'INTC', '-1,500', '21.40', '32,100.00'), ('08/01/2026', 'Interest', 'US Treasury Note 4.125% 11/15/2032', '', '', '', '4,125.00'),
            ('08/14/2026', 'Withdrawal', 'Transfer to bank', '', '', '', '-40,000.00'), ('08/30/2026', 'Bought', 'US Dividend Equity ETF', 'SCHD', '1,000', '27.10', '-27,100.00'),
            ('09/03/2026', 'Deposit', 'Electronic funds transfer', '', '', '', '25,000.00'), ('09/15/2026', 'Dividend', 'Procter & Gamble Co', 'PG', '', '', '687.73'),
            ('09/28/2026', 'Sold', 'Walt Disney Co', 'DIS', '-300', '112.30', '33,690.00')]
    for k in range(2 if total_pages > 20 else 1):
        page_frame(c, n, total_pages, 'Activity'); y = H - 76
        c.setFont('Helvetica-Bold', 12); c.drawString(40, y, 'Account activity' + (' (continued)' if k else '')); y -= 20
        cols = [(40, 'Date', 'l'), (100, 'Activity', 'l'), (170, 'Description', 'l'), (340, 'Symbol', 'l'), (410, 'Quantity', 'r'), (470, 'Price', 'r'), (572, 'Amount', 'r')]
        c.setFont('Helvetica-Bold', 7.6)
        for x, t, a in cols:
            (c.drawString if a == 'l' else c.drawRightString)(x, y, t)
        y -= 16; c.setFont('Helvetica', 7.6)
        for row in acts * (2 if k == 0 else 1):
            for (x, _, a), v in zip(cols, row):
                (c.drawString if a == 'l' else c.drawRightString)(x, y, v)
            y -= 13
        c.showPage(); pages.append('activity'); n += 1
    # realized gains + fee tables (only in the long statement)
    if total_pages > 20:
        page_frame(c, n, total_pages, 'Realized gain and loss'); y = H - 76
        c.setFont('Helvetica-Bold', 12); c.drawString(40, y, 'Realized gain and loss'); y -= 20
        c.setFont('Helvetica', 9)
        for lab, v in [('Short-term realized gain', '1,240.55'), ('Long-term realized gain', '18,930.10'), ('Long-term realized loss', '-2,410.00'), ('Net realized gain', '17,760.65')]:
            c.drawString(56, y, lab); c.drawRightString(330, y, v); y -= 14
        c.showPage(); pages.append('other'); n += 1
        page_frame(c, n, total_pages, 'Fees and fund expenses'); y = H - 76
        c.setFont('Helvetica-Bold', 12); c.drawString(40, y, 'Fund expenses and fee schedule'); y -= 20
        cols = [(40, 'Fund name', 'l'), (300, 'Symbol', 'l'), (400, 'Expense ratio', 'r'), (500, 'Minimum investment', 'r')]
        c.setFont('Helvetica-Bold', 7.6)
        for x, t, a in cols:
            (c.drawString if a == 'l' else c.drawRightString)(x, y, t)
        y -= 16; c.setFont('Helvetica', 7.6)
        for nm, s_, er, mn in [('Meridian Government Money Market Fund', 'MGMXX', '0.18%', '1,000.00'), ('Orion Global Leaders Fund Class A', 'ORGLX', '1.12%', '2,500.00'),
                               ('Quill Zenith Large Growth Fund', 'QZLGX', '0.88%', '3,000.00')]:
            for (x, _, a), v in zip(cols, (nm, s_, er, mn)):
                (c.drawString if a == 'l' else c.drawRightString)(x, y, v)
            y -= 13
        y -= 14; c.setFont('Helvetica-Bold', 9); c.drawString(40, y, 'Advisory fee schedule'); y -= 14
        c.setFont('Helvetica', 8)
        for tier, rate in [('First $1,000,000', '1.00%'), ('Next $4,000,000', '0.75%'), ('Above $5,000,000', '0.50%')]:
            c.drawString(56, y, tier); c.drawRightString(330, y, rate); y -= 12
        c.showPage(); pages.append('other'); n += 1
    # disclosures
    t = 0
    while n <= total_pages:
        page_frame(c, n, total_pages, 'Important information'); y = H - 76
        for _ in range(scale_disclosures):
            c.setFont('Helvetica-Bold', 10); c.drawString(40, y, DISCLOSURE_TOPICS[t % len(DISCLOSURE_TOPICS)]); y -= 14; t += 1
            c.setFont('Helvetica', 8.4)
            for k in range(3):
                y = wrap(c, ' '.join(random.sample(SENT, 3)), 40, y, W - 80) - 4
            y -= 8
        c.showPage(); pages.append('disclosure'); n += 1
    c.save()
    return tot, alloc, sect, pages


def scan(src: Path, dst: Path):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-r', '150', '-png', str(src), f'{td}/p'], check=True)
        ims = []
        for k, f in enumerate(sorted(Path(td).glob('p*.png'))):
            im = Image.open(f).convert('RGB').rotate(random.uniform(-0.6, 0.6), fillcolor='white', resample=Image.BICUBIC)
            im = im.filter(ImageFilter.GaussianBlur(0.4))
            px = im.load()
            for _ in range(20000):
                x, y = random.randrange(im.width), random.randrange(im.height)
                r, g, b = px[x, y]; d = random.randint(-30, 8)
                px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
            ims.append(im)
        ims[0].save(dst, 'PDF', resolution=150, save_all=True, append_images=ims[1:])


def truth_rows(rows):
    return [{k: r[k] for k in ('sym', 'desc', 'qty', 'price', 'value', 'cost', 'section')} for r in rows]


if __name__ == '__main__':
    rows = holdings()
    f1 = OUT / 'C1-meridian-consolidated-statement-kaplan.pdf'
    tot1, alloc1, sect1, pages1 = build_statement(f1, rows, 28, 'David and Ruth Kaplan', 'Joint brokerage (taxable)', 3, holdings_per_page=9)
    sub = [r for r in rows if r['sym'] in ('AAPL', 'MSFT', 'JPM', 'PG', 'KO', 'HD', 'UNH', 'CVX', 'TXN', 'VTI', 'IEFA', 'VWO', 'SCHD', 'ARKK', 'ORGLX')
           or (r['section'] == 'Fixed income' and 'Treasury' in r['desc']) or r['desc'].startswith('Meridian Government')]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / 'c2.pdf'
        tot2, alloc2, sect2, pages2 = build_statement(tmp, sub, 12, 'Ruth Kaplan', 'Traditional IRA', 2, include_bar=False, holdings_per_page=8)
        scan(tmp, OUT / 'C2-meridian-ira-scan-kaplan.pdf')
    truth = {
        f1.name: {'household': 'kaplan', 'pages': len(pages1), 'page_types': pages1, 'total': tot1, 'owner': 'David and Ruth Kaplan', 'account': '6604', 'as_of': '2026-09-30',
                  'holdings': truth_rows(rows), 'pie': [{'label': l, 'pct': round(v, 2)} for l, v in alloc1], 'bar': [{'label': l, 'pct': round(v, 2)} for l, v in sect1]},
        'C2-meridian-ira-scan-kaplan.pdf': {'household': 'kaplan', 'pages': len(pages2), 'page_types': pages2, 'total': tot2, 'owner': 'Ruth Kaplan', 'account': '6604',
                                            'as_of': '2026-09-30', 'holdings': truth_rows(sub), 'pie': [{'label': l, 'pct': round(v, 2)} for l, v in alloc2], 'bar': []},
    }
    (OUT / 'truth_complex.json').write_text(json.dumps(truth, indent=1))
    for k, v in truth.items():
        print(k, v['pages'], 'pages', len(v['holdings']), 'holdings', f"{v['total']:,.2f}", v['page_types'])
        print('  pie', [(p['label'], p['pct']) for p in v['pie']]); print('  bar', [(p['label'], p['pct']) for p in v['bar']])

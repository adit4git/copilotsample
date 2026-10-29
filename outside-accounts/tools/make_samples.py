"""Generate the illustrative outside statements used by the demo and the tests.

Eight fictional statements in the formats advisors receive: a text PDF, a scanned PDF, two web-portal
screenshots, a phone photo of a paper statement, an Excel export and a CSV export. Every institution,
person and private security is fictional. `samples/truth.json` records what each statement really
contains, so extraction accuracy can be measured.

Run: python tools/make_samples.py
"""
from __future__ import annotations
import csv
import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent.parent / 'samples'
OUT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
random.seed(7)


def f(size, bold=False, serif=False):
    return ImageFont.truetype(SERIF if serif else (FONTB if bold else FONT), size)


def money(x):
    return f'{x:,.2f}'


def rows_with_values(rows):
    out = []
    for r in rows:
        r = dict(r)
        if 'value' not in r:
            r['value'] = round(r['qty'] * r['price'], 2)
        out.append(r)
    return out


TRUTH: dict = {}


def record(file, household, meta, holdings, allocation=None, kind=None):
    TRUTH[file] = {'household': household, 'kind': kind, **meta,
                   'holdings': [{k: h.get(k) for k in ('sym', 'desc', 'qty', 'price', 'value', 'cost', 'pct')} for h in holdings],
                   'allocation': allocation or []}


# ------------------------------------------------------------------ 1. text PDF brokerage statement (Henderson)
def harborview_henderson():
    file = 'H1-harborview-brokerage-henderson.pdf'
    rows = rows_with_values([
        {'sym': 'NVDA', 'desc': 'NVIDIA Corp', 'qty': 2800, 'price': 182.10, 'cost': 118300.00},
        {'sym': 'AAPL', 'desc': 'Apple Inc', 'qty': 2400, 'price': 228.50, 'cost': 301200.00},
        {'sym': 'VOO', 'desc': 'S&P 500 ETF', 'qty': 900, 'price': 552.30, 'cost': 402500.00},
        {'sym': 'ARKK', 'desc': 'Innovation ETF', 'qty': 6000, 'price': 62.40, 'cost': 498000.00},
        {'sym': 'QZLGX', 'desc': 'Quill Zenith Large Growth Fund', 'qty': 9500, 'price': 41.20, 'cost': 300150.00},
        {'sym': None, 'desc': 'Lumina Bio Series C (private placement)', 'qty': 1, 'price': 250000.00, 'cost': 250000.00},
        {'sym': None, 'desc': 'Harborview Government Money Market', 'qty': 841410.22, 'price': 1.00, 'cost': 841410.22},
    ])
    total = round(sum(r['value'] for r in rows), 2)
    eq = sum(r['value'] for r in rows[:5])
    alloc = [('Equities', eq), ('Alternative investments', rows[5]['value']), ('Cash and money market', rows[6]['value'])]
    c = canvas.Canvas(str(OUT / file), pagesize=letter)
    c.setFont('Helvetica-Bold', 15); c.drawString(50, 742, 'Harborview Securities')
    c.setFont('Helvetica', 10); c.drawString(50, 726, 'Brokerage Account Statement')
    y = 700
    for line in ('Prepared for: Henderson Family Trust', 'Account type: Individual brokerage (taxable)', 'Account number: XXXX-4417',
                 'Statement period: September 1, 2026 to September 30, 2026', f'Total account value: ${money(total)}'):
        c.drawString(50, y, line); y -= 15
    y -= 10
    c.setFont('Helvetica-Bold', 11); c.drawString(50, y, 'Asset allocation'); y -= 16
    c.setFont('Helvetica', 9.5)
    for lab, v in alloc:
        c.drawString(60, y, lab); c.drawRightString(330, y, f'{v / total * 100:.1f}%'); c.drawRightString(450, y, f'${money(v)}'); y -= 14
    y -= 14
    c.setFont('Helvetica-Bold', 11); c.drawString(50, y, 'Holdings detail'); y -= 18
    cols = [(50, 'Symbol', 'l'), (100, 'Description', 'l'), (330, 'Quantity', 'r'), (395, 'Price', 'r'), (480, 'Market Value', 'r'), (530, '% Acct', 'r'), (590, 'Cost Basis', 'r')]
    c.setFont('Helvetica-Bold', 8.5)
    for x, t, a in cols:
        (c.drawString if a == 'l' else c.drawRightString)(x, y, t)
    y -= 14
    c.setFont('Helvetica', 8.5)
    for r in rows:
        vals = [r['sym'] or '', r['desc'], f"{r['qty']:,.0f}" if r['qty'] != int(r['qty']) or r['qty'] > 1 else '1', f"{r['price']:,.2f}",
                money(r['value']), f"{r['value'] / total * 100:.1f}%", money(r['cost'])]
        if r['desc'].startswith('Harborview Government'):
            vals[2] = f"{r['qty']:,.2f}"
        for (x, _, a), v in zip(cols, vals):
            (c.drawString if a == 'l' else c.drawRightString)(x, y, v)
        y -= 13
    c.setFont('Helvetica-Bold', 8.5); c.drawString(100, y - 2, 'Total'); c.drawRightString(480, y - 2, money(total)); c.drawRightString(530, y - 2, '100.0%')
    c.setFont('Helvetica', 7.5); c.drawString(50, 60, 'Illustrative statement for demonstration only. Harborview Securities is a fictional institution.')
    c.save()
    record(file, 'henderson', {'institution': 'Harborview Securities', 'account_type': 'Individual brokerage (taxable)', 'account': '4417',
                               'owner': 'Henderson Family Trust', 'as_of': '2026-09-30', 'total': total}, rows,
           [{'label': a, 'value': round(v, 2), 'pct': round(v / total * 100, 1)} for a, v in alloc], 'pdf-text')


# ------------------------------------------------------------------ 2. 401(k) portal screenshot (Henderson)
def summit_401k():
    file = 'H2-summit-401k-screenshot.png'
    rows = [
        {'sym': None, 'desc': 'Summit 2035 Target Date Fund', 'value': 520400.00},
        {'sym': 'SULCX', 'desc': 'Summit US Large Cap Index Fund', 'value': 310250.00},
        {'sym': 'SINTX', 'desc': 'Summit International Index Fund', 'value': 118430.00},
        {'sym': 'SCBDX', 'desc': 'Summit Core Bond Fund', 'value': 140240.00},
        {'sym': None, 'desc': 'Stable Value Fund', 'value': 95000.00},
    ]
    total = round(sum(r['value'] for r in rows), 2)
    img = Image.new('RGB', (1440, 900), '#f4f6f9'); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1440, 74], fill='#1d3b5c'); d.text((40, 20), 'Summit Retirement Plan', font=f(28, True), fill='white')
    d.text((1040, 26), 'Margaret Henderson  |  Log out', font=f(18), fill='#dbe6f2')
    d.text((40, 104), 'My Account  >  Investments', font=f(18), fill='#556')
    d.text((40, 142), '401(k) plan balance', font=f(20), fill='#334')
    d.text((40, 172), f'${money(total)}', font=f(40, True), fill='#111')
    d.text((40, 228), 'Balance as of October 10, 2026', font=f(18), fill='#556')
    d.rectangle([40, 270, 1400, 820], fill='white', outline='#d5dbe3')
    hdr = [(60, 'Fund name'), (680, 'Ticker'), (880, 'Balance'), (1160, '% of account')]
    for x, t in hdr:
        d.text((x, 292), t, font=f(19, True), fill='#334')
    d.line([60, 326, 1380, 326], fill='#d5dbe3', width=2)
    y = 344
    for r in rows:
        d.text((60, y), r['desc'], font=f(21), fill='#111')
        d.text((680, y), r['sym'] or '--', font=f(21), fill='#111')
        d.text((880, y), f"${money(r['value'])}", font=f(21), fill='#111')
        d.text((1160, y), f"{r['value'] / total * 100:.1f}%", font=f(21), fill='#111')
        y += 56
    alloc = [('Stocks', 68.0), ('Bonds', 24.0), ('Stable value', 8.0)]
    d.text((60, 650), 'Asset allocation', font=f(20, True), fill='#334')
    x = 60
    for lab, p in alloc:
        d.text((x, 690), f'{lab} {p:.0f}%', font=f(21), fill='#111'); x += 320
    d.text((60, 770), 'Illustrative screen for demonstration only. Summit Retirement Plan is fictional.', font=f(15), fill='#778')
    img.save(OUT / file)
    record(file, 'henderson', {'institution': 'Summit Retirement Plan', 'account_type': '401(k) plan', 'account': None, 'owner': 'Margaret Henderson',
                               'as_of': '2026-10-10', 'total': total}, rows, [{'label': a, 'pct': p} for a, p in alloc], 'image')


# ------------------------------------------------------------------ 3. Excel export from another adviser (Henderson)
def northfield_xlsx():
    file = 'H3-northfield-holdings-export.xlsx'
    rows = rows_with_values([
        {'sym': 'MSFT', 'desc': 'Microsoft Corp', 'cls': 'US Large Cap', 'qty': 1100, 'price': 512.40, 'cost': 210000.00},
        {'sym': 'VTV', 'desc': 'Value ETF', 'cls': 'US Large Cap Value', 'qty': 1500, 'price': 182.60, 'cost': 240000.00},
        {'sym': 'VEA', 'desc': 'Developed Markets ETF', 'cls': 'International Equity', 'qty': 4000, 'price': 54.10, 'cost': 205000.00},
        {'sym': 'AGG', 'desc': 'US Aggregate Bond ETF', 'cls': 'Fixed Income', 'qty': 2500, 'price': 99.20, 'cost': 262500.00},
        {'sym': 'LQD', 'desc': 'Investment Grade Corporate Bond ETF', 'cls': 'Fixed Income', 'qty': 1200, 'price': 108.50, 'cost': 128000.00},
        {'sym': 'BAL-C', 'desc': 'Balanced Income Fund, Class C', 'cls': 'Balanced', 'qty': 8000, 'price': 11.25, 'cost': 84000.00},
        {'sym': 'TRVLX', 'desc': 'Trevale Value Opportunities Fund', 'cls': 'US Large Cap Value', 'qty': 5200, 'price': 31.80, 'cost': 150000.00},
        {'sym': None, 'desc': 'New York City GO 3.50% 08/01/2031', 'cls': 'Municipal Bonds', 'qty': 200, 'price': 987.50, 'cost': 201000.00},
        {'sym': None, 'desc': 'Cash & Sweep', 'cls': 'Cash', 'qty': 42300.00, 'price': 1.00, 'cost': 42300.00},
    ])
    total = round(sum(r['value'] for r in rows), 2)
    wb = Workbook(); ws = wb.active; ws.title = 'Holdings'
    ws['A1'] = 'Northfield Wealth Partners - Holdings export'; ws['A1'].font = Font(bold=True, size=13)
    ws['A2'] = 'Client: Henderson Family Trust'; ws['A3'] = 'Account: Joint taxable XXXX-8820'; ws['A4'] = 'As of: 09/30/2026'
    hdr = ['Ticker', 'Security Name', 'Asset Class', 'Shares', 'Price', 'Market Value', 'Cost Basis', 'Unrealized G/L']
    ws.append([]); ws.append(hdr)
    for c in ws[6]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append([r['sym'] or '', r['desc'], r['cls'], r['qty'], r['price'], r['value'], r['cost'], round(r['value'] - r['cost'], 2)])
    ws.append(['', 'Total', '', '', '', total, round(sum(r['cost'] for r in rows), 2), ''])
    ws.append([]); ws.append(['Illustrative export for demonstration only. Northfield Wealth Partners is fictional.'])
    for col, w in zip('ABCDEFGH', (10, 40, 22, 10, 10, 15, 15, 15)):
        ws.column_dimensions[col].width = w
    wb.save(OUT / file)
    record(file, 'henderson', {'institution': 'Northfield Wealth Partners', 'account_type': 'Joint taxable', 'account': '8820', 'owner': 'Henderson Family Trust',
                               'as_of': '2026-09-30', 'total': total}, rows, [], 'xlsx')


# ------------------------------------------------------------------ 4. phone photo of a bank statement (Henderson)
def lakeshore_photo():
    file = 'H4-lakeshore-bank-photo.jpg'
    rows = [{'sym': None, 'desc': 'Certificate of Deposit 12-month 2.90% APY, matures 03/15/2027', 'value': 250000.00},
            {'sym': None, 'desc': 'Money Market Savings', 'value': 85412.37}]
    total = round(sum(r['value'] for r in rows), 2)
    page = Image.new('RGB', (1500, 1050), '#fbfaf6'); d = ImageDraw.Draw(page)
    d.text((70, 60), 'Lakeshore Bank & Trust', font=f(40, serif=True), fill='#1a1a1a')
    d.text((70, 120), 'Deposit Account Statement', font=f(26, serif=True), fill='#333')
    for i, t in enumerate(['Account holder: Henderson Family Trust', 'Statement date: 09/30/2026', 'Relationship number: XXXX-5530']):
        d.text((70, 190 + i * 42), t, font=f(25, serif=True), fill='#222')
    d.line([70, 340, 1430, 340], fill='#555', width=2)
    d.text((70, 360), 'Account', font=f(25, serif=True), fill='#222'); d.text((1170, 360), 'Balance', font=f(25, serif=True), fill='#222')
    y = 420
    for r in rows:
        d.text((70, y), r['desc'], font=f(25, serif=True), fill='#111'); d.text((1170, y), f"${money(r['value'])}", font=f(25, serif=True), fill='#111'); y += 60
    d.line([70, y + 4, 1430, y + 4], fill='#555', width=2)
    d.text((70, y + 22), 'Total deposits', font=f(25, serif=True), fill='#111'); d.text((1170, y + 22), f'${money(total)}', font=f(25, serif=True), fill='#111')
    d.text((70, y + 100), 'Allocation: Cash 100%', font=f(25, serif=True), fill='#111')
    d.text((70, 960), 'Illustrative statement for demonstration only. Lakeshore Bank & Trust is fictional.', font=f(18, serif=True), fill='#555')
    bg = Image.new('RGB', (1700, 1250), '#6b6458')
    page = page.rotate(1.6, expand=True, fillcolor='#6b6458', resample=Image.BICUBIC)
    bg.paste(page, (60, 70))
    bg = bg.filter(ImageFilter.GaussianBlur(0.7))
    px = bg.load()
    for _ in range(60000):
        x, y = random.randrange(bg.width), random.randrange(bg.height)
        r, g, b = px[x, y]; n = random.randint(-18, 18)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    bg.save(OUT / file, quality=72)
    record(file, 'henderson', {'institution': 'Lakeshore Bank & Trust', 'account_type': 'Deposit accounts', 'account': '5530', 'owner': 'Henderson Family Trust',
                               'as_of': '2026-09-30', 'total': total}, rows, [{'label': 'Cash', 'pct': 100.0}], 'image')


# ------------------------------------------------------------------ 5. scanned annuity summary (Henderson)
def crestmark_scan():
    file = 'H5-crestmark-annuity-scan.pdf'
    alloc = [('Equity Index Subaccount', 55, 336820.00), ('Bond Subaccount', 35, 214340.00), ('Money Market Subaccount', 10, 61240.00)]
    total = round(sum(a[2] for a in alloc), 2)
    page = Image.new('RGB', (1700, 2200), 'white'); d = ImageDraw.Draw(page)
    d.text((110, 120), 'Crestmark Life', font=f(46, True), fill='#111')
    d.text((110, 190), 'Variable Annuity Quarterly Summary', font=f(30), fill='#222')
    for i, t in enumerate(['Contract owner: Robert Henderson', 'Contract number: XXXX-0912', 'Period ending: 09/30/2026',
                           f'Contract value: ${money(total)}', 'Surrender charge: 3% through 06/30/2028']):
        d.text((110, 290 + i * 50), t, font=f(28), fill='#111')
    d.text((110, 580), 'Subaccount allocation', font=f(30, True), fill='#111')
    d.text((110, 640), 'Subaccount', font=f(26, True), fill='#111'); d.text((1000, 640), 'Allocation', font=f(26, True), fill='#111'); d.text((1300, 640), 'Value', font=f(26, True), fill='#111')
    y = 700
    for lab, p, v in alloc:
        d.text((110, y), lab, font=f(28), fill='#111'); d.text((1000, y), f'{p}%', font=f(28), fill='#111'); d.text((1300, y), f'${money(v)}', font=f(28), fill='#111'); y += 60
    d.text((110, 2050), 'Illustrative statement for demonstration only. Crestmark Life is fictional.', font=f(20), fill='#555')
    page = page.rotate(-0.7, expand=False, fillcolor='white', resample=Image.BICUBIC).convert('L')
    px = page.load()
    for _ in range(90000):
        x, y = random.randrange(page.width), random.randrange(page.height)
        px[x, y] = max(0, min(255, px[x, y] + random.randint(-40, 10)))
    page.save(OUT / file, 'PDF', resolution=200)
    record(file, 'henderson', {'institution': 'Crestmark Life', 'account_type': 'Variable annuity', 'account': '0912', 'owner': 'Robert Henderson',
                               'as_of': '2026-09-30', 'total': total}, [{'sym': None, 'desc': a, 'value': v, 'pct': p} for a, p, v in alloc], [], 'pdf-scan')


# ------------------------------------------------------------------ 6. CSV export (Rivera prospect)
def bayline_csv():
    file = 'R1-bayline-positions-rivera.csv'
    rows = rows_with_values([
        {'sym': 'TSLA', 'desc': 'Tesla Inc', 'qty': 1700, 'price': 248.30, 'cost': 95000.00, 'type': 'Equity'},
        {'sym': 'QQQ', 'desc': 'Nasdaq-100 ETF', 'qty': 300, 'price': 512.80, 'cost': 120000.00, 'type': 'ETF'},
        {'sym': 'VNQ', 'desc': 'Real Estate ETF', 'qty': 900, 'price': 92.10, 'cost': 88000.00, 'type': 'ETF'},
        {'sym': 'IEFA', 'desc': 'Core MSCI EAFE ETF', 'qty': 1000, 'price': 81.40, 'cost': 70000.00, 'type': 'ETF'},
        {'sym': None, 'desc': 'Cash', 'qty': 25760.00, 'price': 1.00, 'cost': 25760.00, 'type': 'Cash'},
    ])
    total = round(sum(r['value'] for r in rows), 2)
    with open(OUT / file, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Bayline Brokerage - Positions export']); w.writerow(['Account', 'Individual XXXX-2209']); w.writerow(['Account holder', 'Daniel Rivera'])
        w.writerow(['As of', '10/15/2026']); w.writerow([])
        w.writerow(['Symbol', 'Description', 'Quantity', 'Last Price', 'Market Value', '% of Account', 'Cost Basis', 'Asset Type'])
        for r in rows:
            w.writerow([r['sym'] or 'CASH', r['desc'], r['qty'], f"{r['price']:.2f}", f"{r['value']:.2f}", f"{r['value'] / total * 100:.2f}%", f"{r['cost']:.2f}", r['type']])
        w.writerow(['', 'Account total', '', '', f'{total:.2f}', '100.00%', '', ''])
    record(file, 'rivera', {'institution': 'Bayline Brokerage', 'account_type': 'Individual', 'account': '2209', 'owner': 'Daniel Rivera', 'as_of': '2026-10-15', 'total': total},
           rows, [], 'csv')


# ------------------------------------------------------------------ 7. robo-adviser screenshot (Rivera prospect)
def pathway_screenshot():
    file = 'R2-pathway-robo-screenshot.png'
    rows = [{'sym': 'VTI', 'desc': 'Total US Stock', 'value': 167300.00}, {'sym': 'VXUS', 'desc': 'International Stock', 'value': 104562.50},
            {'sym': 'BND', 'desc': 'US Bonds', 'value': 104562.50}, {'sym': 'VTEB', 'desc': 'Municipal Bonds', 'value': 41825.00}]
    total = round(sum(r['value'] for r in rows), 2)
    img = Image.new('RGB', (1280, 860), 'white'); d = ImageDraw.Draw(img)
    d.text((40, 30), 'Pathway Invest', font=f(30, True), fill='#2b2b6b')
    d.text((40, 84), 'Portfolio overview  -  Rivera Household  -  Goal: Retirement', font=f(19), fill='#444')
    d.text((40, 130), f'${money(total)}', font=f(42, True), fill='#111'); d.text((40, 190), 'As of 10/14/2026', font=f(18), fill='#666')
    for x, t in ((40, 'Holding'), (520, 'Ticker'), (720, 'Allocation'), (980, 'Value')):
        d.text((x, 260), t, font=f(19, True), fill='#333')
    d.line([40, 292, 1240, 292], fill='#ccc', width=2)
    y = 310
    for r in rows:
        for x, t in ((40, r['desc']), (520, r['sym']), (720, f"{r['value'] / total * 100:.0f}%"), (980, f"${money(r['value'])}")):
            d.text((x, y), t, font=f(21), fill='#111')
        y += 54
    d.text((40, 560), 'Asset allocation', font=f(20, True), fill='#333')
    d.text((40, 600), 'Stocks 65%', font=f(21), fill='#111'); d.text((360, 600), 'Bonds 35%', font=f(21), fill='#111')
    d.text((40, 800), 'Illustrative screen for demonstration only. Pathway Invest is fictional.', font=f(15), fill='#888')
    img.save(OUT / file)
    record(file, 'rivera', {'institution': 'Pathway Invest', 'account_type': 'Taxable investment account', 'account': None, 'owner': 'Rivera Household', 'as_of': '2026-10-14',
                            'total': total}, rows, [{'label': 'Stocks', 'pct': 65.0}, {'label': 'Bonds', 'pct': 35.0}], 'image')


# ------------------------------------------------------------------ 8. text PDF IRA statement (Rivera prospect)
def harborview_ira():
    file = 'R3-harborview-ira-rivera.pdf'
    rows = rows_with_values([
        {'sym': 'IVV', 'desc': 'Core S&P 500 ETF', 'qty': 250, 'price': 663.10, 'cost': 120000.00},
        {'sym': 'SCHD', 'desc': 'US Dividend Equity ETF', 'qty': 2000, 'price': 27.40, 'cost': 50000.00},
        {'sym': 'ZQXI', 'desc': 'Zephyr Quantum Innovation ETF', 'qty': 1500, 'price': 18.20, 'cost': 30000.00},
        {'sym': None, 'desc': 'Brokered CD 4.10% 06/30/2027', 'qty': 50, 'price': 1000.00, 'cost': 50000.00},
        {'sym': None, 'desc': 'Harborview Government Money Market', 'qty': 6125.00, 'price': 1.00, 'cost': 6125.00},
    ])
    total = round(sum(r['value'] for r in rows), 2)
    c = canvas.Canvas(str(OUT / file), pagesize=letter)
    c.setFont('Helvetica-Bold', 15); c.drawString(50, 742, 'Harborview Securities')
    c.setFont('Helvetica', 10); c.drawString(50, 726, 'Individual Retirement Account (IRA) Statement')
    y = 700
    for line in ('Prepared for: Daniel Rivera', 'Account type: Traditional IRA', 'Account number: XXXX-7731', 'Statement period: September 1, 2026 to September 30, 2026',
                 f'Total account value: ${money(total)}'):
        c.drawString(50, y, line); y -= 15
    y -= 20
    c.setFont('Helvetica-Bold', 11); c.drawString(50, y, 'Holdings detail'); y -= 18
    cols = [(50, 'Symbol', 'l'), (100, 'Description', 'l'), (330, 'Quantity', 'r'), (395, 'Price', 'r'), (480, 'Market Value', 'r'), (530, '% Acct', 'r'), (590, 'Cost Basis', 'r')]
    c.setFont('Helvetica-Bold', 8.5)
    for x, t, a in cols:
        (c.drawString if a == 'l' else c.drawRightString)(x, y, t)
    y -= 14; c.setFont('Helvetica', 8.5)
    for r in rows:
        q = f"{r['qty']:,.2f}" if r['qty'] != int(r['qty']) else f"{r['qty']:,.0f}"
        for (x, _, a), v in zip(cols, [r['sym'] or '', r['desc'], q, f"{r['price']:,.2f}", money(r['value']), f"{r['value'] / total * 100:.1f}%", money(r['cost'])]):
            (c.drawString if a == 'l' else c.drawRightString)(x, y, v)
        y -= 13
    c.setFont('Helvetica-Bold', 8.5); c.drawString(100, y - 2, 'Total'); c.drawRightString(480, y - 2, money(total)); c.drawRightString(530, y - 2, '100.0%')
    c.setFont('Helvetica', 7.5); c.drawString(50, 60, 'Illustrative statement for demonstration only. Harborview Securities is a fictional institution.')
    c.save()
    record(file, 'rivera', {'institution': 'Harborview Securities', 'account_type': 'Traditional IRA', 'account': '7731', 'owner': 'Daniel Rivera', 'as_of': '2026-09-30',
                            'total': total}, rows, [], 'pdf-text')


if __name__ == '__main__':
    for fn in (harborview_henderson, summit_401k, northfield_xlsx, lakeshore_photo, crestmark_scan, bayline_csv, pathway_screenshot, harborview_ira):
        fn()
    (OUT / 'truth.json').write_text(json.dumps(TRUTH, indent=1))
    for k, v in TRUTH.items():
        print(f"{k:42s} {v['kind']:9s} {len(v['holdings'])} holdings  total {v['total']:>14,.2f}")

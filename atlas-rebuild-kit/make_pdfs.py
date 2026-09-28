import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                  Image, HRFlowable, PageBreak)
from reportlab.platypus.flowables import Flowable

BRAND_TEAL = colors.HexColor('#0C5D51')
MUTED = colors.HexColor('#6B7280')
LINE = colors.HexColor('#E2E5EA')
import sys, tempfile
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = os.path.join(ROOT, 'app/static/content-pdfs'); os.makedirs(OUT, exist_ok=True)
DATA = os.path.join(ROOT, 'app/data')

shelf = json.load(open(f'{DATA}/product-shelf.json'))
models = {m['model_id']: m for m in json.load(open(f'{DATA}/research-models.json'))}
by_id = {p['product_id']: p for p in shelf}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle('FirmName', fontSize=9, textColor=BRAND_TEAL, fontName='Helvetica-Bold', spaceAfter=0))
styles.add(ParagraphStyle('DocTitle', fontSize=19, leading=23, textColor=colors.HexColor('#161B24'), fontName='Helvetica-Bold', spaceAfter=10, spaceBefore=10))
styles.add(ParagraphStyle('DocSub', fontSize=10.5, textColor=MUTED, fontName='Helvetica', spaceAfter=16))
styles.add(ParagraphStyle('H2', fontSize=13, textColor=BRAND_TEAL, fontName='Helvetica-Bold', spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle('Body', fontSize=9.5, leading=14, fontName='Helvetica', textColor=colors.HexColor('#2A2E37')))
styles.add(ParagraphStyle('Small', fontSize=7.5, leading=10, fontName='Helvetica', textColor=MUTED))
styles.add(ParagraphStyle('Disclosure', fontSize=7, leading=10, fontName='Helvetica', textColor=MUTED))

def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, 10.6*inch, 7.75*inch, 10.6*inch)
    canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(BRAND_TEAL)
    canvas.drawString(0.75*inch, 10.7*inch, "ATLAS")
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(1.25*inch, 10.7*inch, "|  Meridian Private Wealth")
    canvas.drawRightString(7.75*inch, 10.7*inch, "For illustrative purposes only \u00b7 Not a solicitation")
    canvas.line(0.75*inch, 0.65*inch, 7.75*inch, 0.65*inch)
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(0.75*inch, 0.5*inch, f"Page {doc.page}")
    canvas.drawRightString(7.75*inch, 0.5*inch, "\u00a9 2026 Meridian Private Wealth. Illustrative document created for internal POC purposes.")
    canvas.restoreState()

def perf_chart(rows, path, title):
    labels = [r['label'] for r in rows]
    y1 = [r['1y']*100 for r in rows]
    y3 = [r['3y']*100 for r in rows]
    y5 = [r['5y']*100 for r in rows]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(6.6,2.6), dpi=150)
    w = 0.26
    ax.bar([i-w for i in x], y1, width=w, label='1-Year', color='#0C5D51')
    ax.bar(x, y3, width=w, label='3-Year Ann.', color='#3FB7A0')
    ax.bar([i+w for i in x], y5, width=w, label='5-Year Ann.', color='#B7DDD6')
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Return (%)', fontsize=8)
    ax.legend(fontsize=7.5, frameon=False, loc='upper left', bbox_to_anchor=(0,1.14), ncol=3)
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(labelsize=7.5)
    ax.axhline(0, color='#6B7280', linewidth=0.6)
    fig.tight_layout()
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)

cell_style = ParagraphStyle('Cell', fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#2A2E37'))
def fee_table(rows):
    data = [['Implementation', 'Vehicle', 'Fee', 'TLH-capable', 'Minimum']]
    for r in rows:
        data.append([Paragraph(r['name'], cell_style), r['vehicle'], r['fee'], r['tlh'], r['min']])
    t = Table(data, colWidths=[2.5*inch, 1.1*inch, 0.8*inch, 0.9*inch, 0.8*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#F4F5F7')),
        ('TEXTCOLOR',(0,0),(-1,0), colors.HexColor('#6B7280')),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,-1),8.5),
        ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.5,LINE), ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    return t

def build_factsheet(model_id, filename, extra_intro=None):
    model = models[model_id]
    impls = [by_id[pid] for pid in model['implementations'] if pid in by_id and by_id[pid]['client_presentable']]
    doc = SimpleDocTemplate(f'{OUT}/{filename}', pagesize=letter,
        topMargin=1.0*inch, bottomMargin=0.9*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    story.append(Paragraph(f"{model['label']} \u2014 Client Factsheet", styles['DocTitle']))
    story.append(Paragraph(f"Benchmark: {impls[0]['benchmark']} &nbsp;\u00b7&nbsp; As of June 30, 2026", styles['DocSub']))
    intro = extra_intro or (f"The {model['label']} targets {', '.join(model['sleeves'])} exposure and is offered in the "
        f"implementations shown below. Each implementation applies the same underlying research view; they differ in "
        f"fee structure, tax management capability, and account minimum. Performance shown for the separately managed "
        f"account (SMA) and direct-indexing implementations reflects a composite of discretionary accounts, net of the "
        f"applicable manager fee. Performance shown for exchange-traded fund (ETF) implementations reflects the fund's "
        f"published net asset value (NAV) total return. These are different performance bases and are not directly "
        f"comparable without adjustment; see \u201cImportant disclosures\u201d on the final page.")
    story.append(Paragraph(intro, styles['Body']))
    story.append(Paragraph("Implementation comparison", styles['H2']))
    rows = []
    for p in impls:
        name = p.get('manager') or f"{p.get('fund_family','')} {p.get('ticker','')}".strip()
        fee = f"{p['fees']['manager_bps']} bps" if p['fees']['manager_bps'] is not None else f"{p['fees']['expense_ratio_bps']} bps"
        rows.append({'name': name, 'vehicle': p['vehicle'].replace('_',' ').title(),
            'fee': fee, 'tlh': 'Yes' if p['tlh_capable'] else 'No', 'min': f"${p['minimum']:,.0f}" if p['minimum'] else 'None'})
    story.append(fee_table(rows))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Trailing performance by implementation", styles['H2']))
    chart_rows = [{'label': (p.get('ticker') or p['vehicle'][:4]), **p['performance']['returns']} for p in impls]
    chart_path = os.path.join(tempfile.gettempdir(), f'_chart_{model_id}.png')
    perf_chart(chart_rows, chart_path, f"{model['label']}: trailing returns by implementation")
    story.append(Image(chart_path, width=6.6*inch, height=2.6*inch))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Performance basis differs by implementation type (composite net-of-fee for SMA/DI vs. NAV total return for ETFs); see disclosures.", styles['Small']))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Fee impact on a sample account", styles['H2']))
    sample_amt = 1000000
    fee_rows2 = [['Implementation', f'Annual fee on ${sample_amt:,.0f}']]
    for p in impls:
        bps = p['fees']['manager_bps'] if p['fees']['manager_bps'] is not None else p['fees']['expense_ratio_bps']
        name = p.get('manager') or f"{p.get('fund_family','')} {p.get('ticker','')}".strip()
        fee_rows2.append([Paragraph(name, cell_style), f"${sample_amt*bps/10000:,.0f}/yr"])
    t2 = Table(fee_rows2, colWidths=[4.0*inch, 3.0*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#F4F5F7')), ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8.5), ('GRID',(0,0),(-1,-1),0.5,LINE),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=LINE, thickness=0.5))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Important disclosures", styles['H2']))
    disclosure = ("This material is for informational purposes only and does not constitute investment advice or a "
        "recommendation to buy or sell any security. Past performance does not guarantee future results. Composite "
        "performance for separately managed account and direct-indexing implementations reflects a blend of "
        "discretionary client accounts and may differ from the performance experienced by any individual account, "
        "particularly where tax-loss harvesting, client-directed restrictions, or funding timing cause dispersion. "
        "Exchange-traded fund performance reflects fund-level NAV total return and does not reflect any account-level "
        "program fee, which applies in addition to the fund's expense ratio for accounts held in an advisory program. "
        "Tax-loss harvesting is not available in a pooled ETF structure and its benefit, where available, depends on "
        "an account's specific tax situation and is not guaranteed. This document was prepared for a product "
        "walkthrough / proof-of-concept exercise; all figures are illustrative and do not represent actual firm "
        "performance, actual fee schedules, or the performance of any specific, currently offered product.")
    story.append(Paragraph(disclosure, styles['Disclosure']))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"built {filename}")

def build_guide():
    doc = SimpleDocTemplate(f'{OUT}/etf-sma-guide.pdf', pagesize=letter,
        topMargin=1.0*inch, bottomMargin=0.9*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    story.append(Paragraph("Choosing an implementation: ETFs, SMAs, and Direct Indexing", styles['DocTitle']))
    story.append(Paragraph("A client guide to the trade-offs across implementation types", styles['DocSub']))
    story.append(Paragraph(
        "When a research view is available in more than one implementation \u2014 an exchange-traded fund (ETF), a "
        "separately managed account (SMA), or a direct-indexing account \u2014 the choice usually comes down to three "
        "questions: how much does it cost, what has it returned, and how much can it be tailored to your specific tax "
        "and legacy-holding situation. This guide walks through each.", styles['Body']))
    story.append(Paragraph("1. Cost", styles['H2']))
    story.append(Paragraph(
        "An ETF's expense ratio is typically lower than an SMA's manager fee, because an ETF spreads its operating "
        "costs across every shareholder in the fund rather than managing one account individually. A direct-indexing "
        "account typically falls between the two: it is a single-account strategy like an SMA, but its trading and "
        "rebalancing are largely systematic, which tends to keep its fee closer to an ETF than a fully discretionary "
        "SMA. In an advisory program, the program fee applies on top of any of these three \u2014 so the fee difference "
        "that matters to a comparison is the difference in manager fee or expense ratio, not the full account cost.",
        styles['Body']))
    story.append(Paragraph("2. Performance", styles['H2']))
    story.append(Paragraph(
        "Passive index exposure has outperformed active management in many periods, though performance varies by "
        "asset class, time horizon, and market environment, and past performance does not indicate future results. "
        "When comparing implementations of the same research view, confirm that the performance figures being "
        "compared use the same basis and the same time period \u2014 a fund's published NAV return and a separately "
        "managed account composite's net-of-fee return are calculated differently and are not directly interchangeable "
        "without adjustment.", styles['Body']))
    story.append(Paragraph("3. Tax management and customization", styles['H2']))
    story.append(Paragraph(
        "A separately managed account or direct-indexing account can realize losses at the individual position level "
        "throughout the year \u2014 a capability a pooled ETF structure cannot offer an individual shareholder. This is "
        "most valuable in volatile markets and for investors in higher tax brackets, and it can also accommodate "
        "specific holding exclusions (for example, concentrated employer stock) that a fund cannot. An ETF, by "
        "contrast, offers none of this account-level customization, in exchange for its typically lower cost and "
        "high liquidity.", styles['Body']))
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=LINE, thickness=0.5))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Important disclosures", styles['H2']))
    story.append(Paragraph(
        "This material is for informational purposes only and does not constitute investment, tax, or legal advice. "
        "Tax-loss harvesting benefits, where available, depend on an account's specific circumstances and are not "
        "guaranteed. This document was prepared for a product walkthrough / proof-of-concept exercise and is "
        "illustrative; it does not represent actual firm performance or current product terms.", styles['Disclosure']))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("built etf-sma-guide.pdf")

build_guide()
build_factsheet('research_growth', 'research-growth-factsheet.pdf')
build_factsheet('research_income', 'research-income-factsheet.pdf')

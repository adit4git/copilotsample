# Outside Accounts: proof of concept

This proof of concept brings statements for accounts held at other institutions into a portfolio review. It:

1. reads up to 5 statements at a time, in any of these formats: PDF, scanned PDF, screenshot, phone photo, Excel or CSV;
2. extracts holdings, tickers, quantities, prices, values, cost basis and any printed asset allocation;
3. validates every row against the firm's approved list;
4. shows firm and outside holdings together, against the target and the CIO view;
5. builds three proposals with firm guidance applied, plus policy checks, talking points and a review record;
6. recommends a workflow for inside vs outside reviews.

All institutions, people and private securities in the samples are fictional. The approved list, CIO view and households are illustrative.

## Run it

```
pip install -r requirements.txt        # plus the system tools: tesseract-ocr, poppler-utils
python tools/make_samples.py           # rebuilds the 8 sample statements and samples/truth.json
uvicorn app.main:app --port 8010       # then open http://localhost:8010
python -m pytest -q                    # 34 tests
python tools/measure.py                # extraction accuracy against the truth file
```

In the app, choose **▶ Guided tour**. The tour runs through the whole flow on the Henderson sample statements, then switches to the Rivera prospect.

## Folders

```
app/
  main.py            FastAPI app: sessions, uploads (5 per request, 15 MB each), overrides, gain budget, analysis, review record
  engine.py          validation, household comparison, proposals, policy checks, talking points, workflow
  extract/core.py    readers (PDF text layer, two-pass OCR, Excel, CSV), page triage and the statement parser
  extract/charts.py  allocation read from vector bar charts and raster pie charts
  extract/llm.py     optional language-model reader; every number it returns must appear on the page
  data/              approved list and reference securities, market and CIO data, households
  static/            web UI and guided tour (no build step)
samples/             8 sample statements, 2 long statements (28 and 12 pages), truth.json, truth_complex.json
tools/               make_samples.py, measure.py, make_complex.py, measure_complex.py
tests/               test_outside.py
```

## How a statement is read

| Format | Reader | Confidence |
|---|---|---|
| Text PDF | `pdftotext -layout` | 0.97 per cell |
| Scanned PDF | `pdftoppm` (250 dpi), then deskew and Tesseract | Word confidence from the OCR |
| Image (PNG, JPG) | Upscale, autocontrast, deskew, then Tesseract with word boxes | Word confidence from the OCR |
| Excel, CSV | Cells read directly | 0.99 |

Every source is turned into lines split into column segments. The parser then does five things:

1. **Finds the header row.** Synonyms are used, so "Shares", "Units" and "Quantity" all count as quantity.
2. **Maps each cell to a column.** It goes by the type of value first (percent, ticker, text, number), then by position.
3. **Reads the statement details.** These are institution, owner, last 4 digits of the account, as-of date and stated total.
4. **Reads any allocation section.** It can be a table, or an inline line such as "Stocks 68% Bonds 24%".
5. **Stops the holdings table at its total row.**

It also repairs common OCR misreadings: `vTl` becomes `VTI`, and `1O4,562.5O` becomes `104,562.50`. Every repair is flagged.

**Checks on each statement:**
- the rows add up to the printed total;
- quantity × price matches the value (bonds priced per 100 are allowed for);
- the statement is less than 90 days old;
- the owner matches the household;
- low-confidence rows are listed.

Flagged rows are highlighted. Any value can be edited, or a row excluded, and the change is logged with the original.

**Accuracy on the samples:**
- **Sample statements:** 40 of 40 holdings found; 194 of 194 fields correct (symbol, quantity, price, value, cost, owner, account, date, total, allocation); all 8 statements reconcile.
- **Degraded copies:** the tests rerun extraction on the screenshots and the photo at 50–60% size with heavy JPEG compression. All still reconcile.
- **Caveat:** these are generated samples. Real statements will vary more, which is why review, correction and the language-model fallback are part of the flow.

## Validation

Validation checks each row in this order:

1. **Approved list:** by symbol, or by name when no symbol is printed.
   - Rated *Not recommended* → **Under review**.
   - Otherwise → **Approved**.
2. **Reference data:** known securities that are not approved → **Not approved**. Each is mapped to the approved fund for its main asset class. Retirement-plan funds → **Held away**.
3. **Category rules:**
   - municipal bonds → approved and held to maturity;
   - CDs and money market → **Cash**;
   - private placements → **Held away**.
4. **Anything else** → **Not recognized**. Asset classes are estimated from the statement's asset-class column or the name, and the advisor confirms or overrides.

The account type then decides what can move:

| Account type | Can move? | Treatment in the proposals |
|---|---|---|
| Taxable and IRA | Yes | Transfer in kind, sell after transfer, or invest cash |
| Employer plan | No | Stays held away while the client is employed |
| Annuity | No | Stays in the contract; the surrender charge is read from the statement |
| Bank | No | Stays as the reserve; a CD is revisited at maturity |

## Proposals and firm guidance

| | A. Transfer what is approved | B. Consolidate and align | C. Tax-aware phased move |
|---|---|---|---|
| Approved | Transfer in kind | Transfer; trim single names over the limit and over-target classes (IRA first, then lowest gain), within the gain budget | Transfer in kind |
| Under review | Transfer, flagged | Sell after transfer and replace | Sell only if no tax (IRA, loss or gain under 5%) |
| Not approved | Stays outside | Sell after transfer and replace | Same rule as C above; otherwise phase 2 |
| Cash | Transfer as cash | Invest toward the target | Invest toward the target |

New money goes to approved funds for classes below target, weighted by the CIO stance:
- Overweight ×1.25;
- Neutral ×1;
- Underweight ×0.75.

In an IRA, the IG bond fund is used instead of the municipal fund.

**Checks:**
- risk inside the profile band;
- no single name over 10% (direct holdings plus fund look-through);
- high yield within its limit;
- only approved securities in firm accounts;
- nothing under Research review;
- realized gains within the gain budget;
- sales within the turnover limit;
- every outside row identified.

The gain budget can be changed per session.

**The prospect example (Rivera):**
1. At the default $75K gain budget, Proposal B fails the risk band and the single-name limit, because TSLA is 29% of the household.
2. The advisor resolves ZQXI as not approved.
3. The advisor raises the gain budget to $250K.
4. Every check then passes, at about $60K of estimated tax.

## Long and complex statements

Real statements are often 25+ pages. Holdings run across several pages, the allocation is shown only as a pie or bar chart, and the rest is activity, fee tables and disclosures. Two samples cover this:
- `C1`: a 28-page text PDF;
- `C2`: a 12-page scanned IRA statement.

`python tools/make_complex.py` rebuilds them, and `python tools/measure_complex.py` scores them against `samples/truth_complex.json`.

**What happens to each kind of page:**

| Page type | How it is recognized | What is done with it |
|---|---|---|
| Summary | Page 1, or a "summary", "account value" or "overview" title | Statement details and the stated total are read here |
| Chart | Drawings or images, plus an allocation or sector title | Charts are measured (below) |
| Holdings | A holdings column header, a holdings title, or more rows of the table from the page before | Rows are read. The table carries over page breaks, even when the column header is not repeated. |
| Activity | A date or transaction column, dated rows, or an activity title | Skipped, so buys, sells and dividends never become holdings |
| Disclosure | Disclosure, glossary or notice titles, or prose-heavy pages | Skipped |
| Other | Anything else, such as realized gains or fee schedules | Skipped. A fee table without a value or quantity column is never read as holdings. |

**Inside a holdings table:**
- **Section headings** ("EQUITIES", "FIXED INCOME", "CASH AND EQUIVALENTS") become each row's asset-class hint.
- **Section subtotals** ("Total Equities") are checked against the rows above them and do not end the table. A "Total holdings" line does end it.
- **A row name that only starts with "Total"** (e.g. "Total US Stock Fund") is still a holding when it has a ticker.
- **A description that wraps onto a second line** (CUSIP, rating, call date) stays with its row. The CUSIP is kept.

**Charts:**

| Kind | Method | Accuracy on the samples |
|---|---|---|
| Vector bar chart (text PDF) | Bars and axis ticks read from the drawing | Exact (to 0.01 pt) |
| Raster pie chart (image in a PDF, or a scanned page) | Slice areas measured by colour; legend read by OCR; area lost to white separators added back | Within 0.41 pt (C1) and 0.22 pt (C2) |

Every pie is then checked against the same split computed from the statement's own validated holdings. On C1 they agree within 0.4 pt.

With the language model turned on, a chart the measurement is unsure about gets a second reading. Its labels are used only if its numbers agree with the measured ones within 3 points and add up to 100.

**Scanned statements are read in two passes:**
1. Every page is OCR'd quickly at 80 dpi to classify it.
2. Only the summary and holdings pages, and any unclassified page that looks like a table, are OCR'd at 250 dpi, in parallel.

For C2 that is 4 of 12 pages, and the whole statement takes about 25 seconds instead of about 100. An OCR misread such as `VWO` read as `VVWO` is matched back to the right security by name during validation, and flagged.

**Results:**

| | C1 (28 pages, text) | C2 (12 pages, scanned) |
|---|---|---|
| Holdings found | 39 of 39, 0 extra rows | 18 of 18, 0 extra rows |
| Fields correct (symbol, quantity, price, value, cost) | 195 of 195 | 89 of 90 before validation; every symbol right after the name match |
| Reconciles to the stated total | Yes, and all 3 section subtotals | Yes |
| Pages classified correctly | 28 of 28 | 12 of 12 |
| Pie chart | 4 of 4 slices within 1 pt | 4 of 4 slices within 1 pt |
| Bar chart | 7 of 7 bars exact | (none) |
| Time | about 4 seconds | about 25 seconds |

**Before this change,** the same pipeline gave:
- **Extra rows:** 33 on C1 and 21 on C2 (activity rows, subtotals). The totals were off by about 2×.
- **Charts:** no allocation read.
- **Scan time:** 103 seconds for C2.

**In the review screen:**
- **Page map:** a coloured chip for each page. Select one to preview it. Summary, chart and holdings pages are kept for preview; skipped pages are not.
- **Allocation read from charts:** the cropped chart, the measured values, the matching values from the holdings, and the method and confidence.

## Language model (optional)

Set `OUTSIDE_LLM=1` and `ANTHROPIC_API_KEY`. The model is asked only about statements with flagged rows or no rows. It returns JSON, and any row with a number that is not printed on the statement is dropped. Rows it adds are flagged for the advisor. It never sets a status, a figure or a proposal.

In production, the outside-accounts summary and the talking points would also be drafted by a model, from the calculated figures. In this proof of concept they come from templates.

## Controls built in

- **Consent:** uploads are locked until consent is recorded.
- **Files:** uploaded files are written to a temporary folder and deleted as soon as they are read. Only a preview image and the extracted data are kept, in memory, for the session.
- **Account numbers:** reduced to the last 4 digits.
- **Audit log:** every advisor change is logged. The review record (Markdown) lists statements, checks, validation, comparison, proposals and talking points.

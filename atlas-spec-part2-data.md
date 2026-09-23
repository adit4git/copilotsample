# Atlas Advisor Console — Rebuild Specification (Part 2 of 3): Raw Reference Data

**This is Part 2 of a 3-part specification.** See Part 1 for the schema explanation of every field below (§5.1–5.4) and the overall app architecture. This file is pure reference data — the exact, complete contents of the three JSON files under `app/data/`. Copy each block verbatim into the file path named in its heading. Do not regenerate, paraphrase, or "clean up" any of this data — every household figure and every rule predicate here is depended on exactly as written by the rule engine, the transition workbench, and the test suite (which asserts, for example, that the rule count is exactly 92 and that advisor `marcus` has exactly 6 households).

---

### 5.5 Complete `app/data/households.json`

```json
[
 {
  "id": "henderson",
  "name": "Henderson Family Trust",
  "entity": "Revocable Trust",
  "segment": "Private Wealth",
  "aum": 49700000,
  "rev": 241000,
  "since": 2009,
  "risk": "Moderate Growth",
  "contact": "Margaret & Paul Henderson",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 2,
   "type": "Annual review",
   "note": "Wants to revisit single-stock exposure and 2026 gifting."
  },
  "ytdReturn": 11.4,
  "harvestable": 186000,
  "ytdRealizedGains": 412000,
  "holdings": [
   {
    "sym": "NVDA",
    "name": "NVIDIA Corp",
    "ac": "US Equity",
    "mv": 10600000,
    "cost": 2100000
   },
   {
    "sym": "MSFT",
    "name": "Microsoft Corp",
    "ac": "US Equity",
    "mv": 4900000,
    "cost": 2400000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 6200000,
    "cost": 5100000
   },
   {
    "sym": "MUB",
    "name": "Muni Bond ETF",
    "ac": "Municipal",
    "mv": 9800000,
    "cost": 10400000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 5100000,
    "cost": 5600000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 4300000,
    "cost": 4900000
   },
   {
    "sym": "CASH",
    "name": "Sweep / T-Bills",
    "ac": "Cash",
    "mv": 7300000,
    "cost": 7300000
   },
   {
    "sym": "AUSTIN-4.0-32",
    "name": "City of Austin GO 4.0% 2032 (individual bond)",
    "ac": "Municipal",
    "type": "BOND",
    "mv": 1100000,
    "cost": 1080000
   },
   {
    "sym": "NVDA",
    "name": "NVIDIA Corp (legacy gift lot, basis unresolved)",
    "ac": "US Equity",
    "mv": 400000,
    "cost": null,
    "lot_id": "LOT_HEND_GIFT_2011"
   }
  ],
  "target": {
   "equity": 55,
   "fixed": 30,
   "alt": 10,
   "cash": 5
  },
  "current": {
   "equity": 56,
   "fixed": 31,
   "alt": 0,
   "cash": 13
  },
  "concentration": [
   {
    "label": "NVDA single-stock",
    "pct": 22,
    "threshold": 10
   }
  ],
  "cio": {
   "score": "High",
   "view": "Neutral US large-cap growth; trim mega-cap tech into strength",
   "pub": "CIO Weekly — “Mega-cap concentration risk”",
   "diverge": "+12 pts overweight vs house model"
  },
  "programs": {
   "privateBanking": "enrolled",
   "trustEstate": "enrolled",
   "alternatives": "eligible",
   "directIndexing": "eligible",
   "lending": "eligible",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "enrolled",
   "tlhOverlay": "eligible",
   "transition": "na",
   "charitable": "eligible"
  },
  "notes": "Concentrated NVDA lot from 2016. Charitably inclined — DAF opened 2021."
 },
 {
  "id": "okonkwo",
  "name": "Okonkwo Holdings LLC",
  "entity": "Family LLC",
  "segment": "Private Wealth",
  "aum": 31600000,
  "rev": 174000,
  "since": 2019,
  "risk": "Growth",
  "contact": "Chidi Okonkwo",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 6,
   "type": "Liquidity deployment",
   "note": "$14M business-sale proceeds landed; needs a deployment plan."
  },
  "ytdReturn": 6.1,
  "harvestable": 24000,
  "ytdRealizedGains": 88000,
  "holdings": [
   {
    "sym": "CASH",
    "name": "Sweep / T-Bills",
    "ac": "Cash",
    "mv": 14200000,
    "cost": 14200000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 6400000,
    "cost": 5900000
   },
   {
    "sym": "IEFA",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 3100000,
    "cost": 3000000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 4700000,
    "cost": 4800000
   },
   {
    "sym": "PRIV",
    "name": "Private RE Interest",
    "ac": "Alternatives",
    "mv": 3200000,
    "cost": 3000000
   }
  ],
  "target": {
   "equity": 50,
   "fixed": 25,
   "alt": 20,
   "cash": 5
  },
  "current": {
   "equity": 30,
   "fixed": 15,
   "alt": 10,
   "cash": 45
  },
  "concentration": [
   {
    "label": "Cash drag",
    "pct": 45,
    "threshold": 15
   }
  ],
  "cio": {
   "score": "Medium",
   "view": "Stagger deployment; ladder into duration on rate stability",
   "pub": "CIO Asset Allocation — Q3 “Deploying the sidelines”",
   "diverge": "45% cash vs 5% target"
  },
  "programs": {
   "privateBanking": "eligible",
   "trustEstate": "eligible",
   "alternatives": "eligible",
   "directIndexing": "eligible",
   "lending": "eligible",
   "insurance": "eligible"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "eligible",
   "transition": "eligible",
   "charitable": "na"
  },
  "notes": "Post-liquidity event. Prime candidate for alternatives sleeve + private banking relationship."
 },
 {
  "id": "reyes",
  "name": "Reyes-Marín Household",
  "entity": "Joint / Individual",
  "segment": "HNW",
  "aum": 12400000,
  "rev": 74000,
  "since": 2015,
  "risk": "Aggressive Growth",
  "contact": "Sofía Reyes & Daniel Marín",
  "advisor_id": "dana",
  "nextMeeting": null,
  "ytdReturn": 9.2,
  "harvestable": 298000,
  "ytdRealizedGains": 64000,
  "holdings": [
   {
    "sym": "QQQ",
    "name": "Nasdaq-100 ETF",
    "ac": "US Equity",
    "mv": 3600000,
    "cost": 4300000
   },
   {
    "sym": "ARKK",
    "name": "Innovation ETF",
    "ac": "US Equity",
    "mv": 900000,
    "cost": 1700000
   },
   {
    "sym": "TSLA",
    "name": "Tesla Inc",
    "ac": "US Equity",
    "mv": 1100000,
    "cost": 1500000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 3200000,
    "cost": 2600000
   },
   {
    "sym": "VWO",
    "name": "Emerging Mkts ETF",
    "ac": "Intl Equity",
    "mv": 1400000,
    "cost": 1600000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 2200000,
    "cost": 2200000
   }
  ],
  "target": {
   "equity": 75,
   "fixed": 10,
   "alt": 10,
   "cash": 5
  },
  "current": {
   "equity": 82,
   "fixed": 0,
   "alt": 0,
   "cash": 18
  },
  "concentration": [
   {
    "label": "Tech / growth tilt",
    "pct": 38,
    "threshold": 30
   }
  ],
  "cio": {
   "score": "Medium",
   "view": "Reduce single-name growth; broaden factor exposure",
   "pub": "CIO Equity Strategy — “Beyond the Magnificent”",
   "diverge": "+7 pts growth factor vs model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "eligible",
   "alternatives": "na",
   "directIndexing": "eligible",
   "lending": "na",
   "insurance": "eligible"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "eligible",
   "transition": "eligible",
   "charitable": "na"
  },
  "notes": "Largest harvestable-loss position in the book after the growth drawdown. Not yet on a tax overlay."
 },
 {
  "id": "sorensen",
  "name": "Sørensen Living Trust",
  "entity": "Irrevocable Trust",
  "segment": "Private Wealth",
  "aum": 27300000,
  "rev": 150000,
  "since": 2011,
  "risk": "Conservative Growth",
  "contact": "Astrid Sørensen (Trustee)",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 11,
   "type": "Trust distribution review",
   "note": "Beneficiary distribution schedule + Roth conversion window."
  },
  "ytdReturn": 5.4,
  "harvestable": 41000,
  "ytdRealizedGains": 12000,
  "holdings": [
   {
    "sym": "MUB",
    "name": "Muni Bond ETF",
    "ac": "Municipal",
    "mv": 9400000,
    "cost": 9900000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 6100000,
    "cost": 4700000
   },
   {
    "sym": "SCHD",
    "name": "US Dividend ETF",
    "ac": "US Equity",
    "mv": 3300000,
    "cost": 2900000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 2600000,
    "cost": 2800000
   },
   {
    "sym": "BND",
    "name": "US Bond Market",
    "ac": "Fixed Income",
    "mv": 4100000,
    "cost": 4400000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 1800000,
    "cost": 1800000
   }
  ],
  "target": {
   "equity": 45,
   "fixed": 45,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 47,
   "fixed": 49,
   "alt": 0,
   "cash": 7
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "Well aligned; monitor muni duration",
   "pub": "CIO Fixed Income — “Muni curve steepening”",
   "diverge": "In line with model (±2 pts)"
  },
  "programs": {
   "privateBanking": "enrolled",
   "trustEstate": "enrolled",
   "alternatives": "eligible",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "enrolled",
   "tlhOverlay": "enrolled",
   "transition": "na",
   "charitable": "eligible"
  },
  "notes": "Well-diversified. Roth conversion opportunity within the low-income beneficiary bracket."
 },
 {
  "id": "abernathy",
  "name": "Abernathy Family Foundation",
  "entity": "Private Foundation",
  "segment": "Institutional",
  "aum": 22900000,
  "rev": 103000,
  "since": 2013,
  "risk": "Balanced",
  "contact": "Board — R. Abernathy (Chair)",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 4,
   "type": "Investment committee",
   "note": "Spending policy + 5% distribution requirement review."
  },
  "ytdReturn": 7,
  "harvestable": 9000,
  "ytdRealizedGains": 0,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 8200000,
    "cost": 6100000
   },
   {
    "sym": "VEA",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 3900000,
    "cost": 3700000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 6400000,
    "cost": 6500000
   },
   {
    "sym": "PE",
    "name": "Private Equity Fund II",
    "ac": "Alternatives",
    "mv": 2700000,
    "cost": 2400000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 1700000,
    "cost": 1700000
   }
  ],
  "target": {
   "equity": 55,
   "fixed": 30,
   "alt": 12,
   "cash": 3
  },
  "current": {
   "equity": 53,
   "fixed": 28,
   "alt": 12,
   "cash": 7
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model; consider private credit for yield",
   "pub": "CIO Alternatives — “Private credit in endowment models”",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "enrolled",
   "alternatives": "enrolled",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Tax-exempt entity — overlays N/A. Opportunity: private credit sleeve for spending-policy yield."
 },
 {
  "id": "kaplan",
  "name": "Kaplan Household",
  "entity": "Joint",
  "segment": "HNW",
  "aum": 8700000,
  "rev": 54000,
  "since": 2017,
  "risk": "Moderate Growth",
  "contact": "Rebecca & Josh Kaplan",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 1,
   "type": "Retirement planning",
   "note": "Retiring in 18 months — income plan + concentrated RSU wind-down."
  },
  "ytdReturn": 8.3,
  "harvestable": 52000,
  "ytdRealizedGains": 140000,
  "holdings": [
   {
    "sym": "AAPL",
    "name": "Apple Inc (RSU)",
    "ac": "US Equity",
    "mv": 2400000,
    "cost": 600000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 2100000,
    "cost": 1700000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 1100000,
    "cost": 1200000
   },
   {
    "sym": "BND",
    "name": "US Bond Market",
    "ac": "Fixed Income",
    "mv": 1900000,
    "cost": 2000000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 1200000,
    "cost": 1200000
   }
  ],
  "target": {
   "equity": 60,
   "fixed": 30,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 64,
   "fixed": 22,
   "alt": 0,
   "cash": 14
  },
  "concentration": [
   {
    "label": "AAPL single-stock (RSU)",
    "pct": 27.6,
    "threshold": 10
   }
  ],
  "cio": {
   "score": "High",
   "view": "Diversify concentrated employer stock ahead of retirement",
   "pub": "CIO Wealth Planning — “Concentrated stock & the retirement runway”",
   "diverge": "Concentration breach + glide-path lag"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "eligible",
   "alternatives": "na",
   "directIndexing": "eligible",
   "lending": "eligible",
   "insurance": "eligible"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "eligible",
   "transition": "eligible",
   "charitable": "eligible"
  },
  "notes": "Low-basis AAPL RSUs. Exchange-fund or direct-indexing transition candidate ahead of retirement."
 },
 {
  "id": "nakamura",
  "name": "Nakamura Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 15800000,
  "rev": 87000,
  "since": 2014,
  "risk": "Growth",
  "contact": "Kenji Nakamura",
  "advisor_id": "dana",
  "nextMeeting": null,
  "ytdReturn": 8.9,
  "harvestable": 73000,
  "ytdRealizedGains": 210000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 5800000,
    "cost": 4000000
   },
   {
    "sym": "VGT",
    "name": "Info Tech ETF",
    "ac": "US Equity",
    "mv": 2300000,
    "cost": 1600000
   },
   {
    "sym": "VEA",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 2400000,
    "cost": 2600000
   },
   {
    "sym": "MUB",
    "name": "Muni Bond ETF",
    "ac": "Municipal",
    "mv": 3100000,
    "cost": 3300000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 2200000,
    "cost": 2200000
   }
  ],
  "target": {
   "equity": 65,
   "fixed": 25,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 67,
   "fixed": 20,
   "alt": 0,
   "cash": 14
  },
  "concentration": [],
  "cio": {
   "score": "Medium",
   "view": "Slightly cash-heavy; put dry powder to work",
   "pub": "CIO Weekly — “Cash on the sidelines”",
   "diverge": "+9 pts cash vs model"
  },
  "programs": {
   "privateBanking": "eligible",
   "trustEstate": "eligible",
   "alternatives": "eligible",
   "directIndexing": "eligible",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "eligible",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Realized $210K gains YTD — harvest to offset. Direct-indexing candidate for ongoing TLH."
 },
 {
  "id": "delacroix",
  "name": "Delacroix Household",
  "entity": "Joint",
  "segment": "Emerging HNW",
  "aum": 4900000,
  "rev": 34000,
  "since": 2021,
  "risk": "Moderate Growth",
  "contact": "Camille Delacroix",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 9,
   "type": "Portfolio check-in",
   "note": "First full-year review; wants ESG tilt."
  },
  "ytdReturn": 7.8,
  "harvestable": 18000,
  "ytdRealizedGains": 6000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 1900000,
    "cost": 1700000
   },
   {
    "sym": "ESGV",
    "name": "ESG US Equity ETF",
    "ac": "US Equity",
    "mv": 800000,
    "cost": 750000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 900000,
    "cost": 950000
   },
   {
    "sym": "BND",
    "name": "US Bond Market",
    "ac": "Fixed Income",
    "mv": 900000,
    "cost": 920000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 400000,
    "cost": 400000
   }
  ],
  "target": {
   "equity": 65,
   "fixed": 25,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 73,
   "fixed": 18,
   "alt": 0,
   "cash": 9
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model; ESG direct-index for values alignment",
   "pub": "CIO Sustainable Investing — “Values-aligned indexing”",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "eligible",
   "lending": "na",
   "insurance": "eligible"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "eligible",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Values-driven investor. ESG direct indexing aligns with stated preferences + enables TLH."
 },
 {
  "id": "bianchi",
  "name": "Bianchi Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 9400000,
  "rev": 58000,
  "since": 2018,
  "risk": "Growth",
  "contact": "Elena Bianchi",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 11,
   "type": "Overlay review",
   "note": "Existing TEM SMS position; asked about adding an overlay on top."
  },
  "ytdReturn": 9.6,
  "harvestable": 41000,
  "ytdRealizedGains": 52000,
  "holdings": [
   {
    "sym": "AAPL",
    "name": "Apple Inc",
    "ac": "US Equity",
    "mv": 2100000,
    "cost": 2600000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 3200000,
    "cost": 2900000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 1800000,
    "cost": 1900000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 1600000,
    "cost": 1600000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 700000,
    "cost": 700000
   }
  ],
  "target": {
   "equity": 65,
   "fixed": 25,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 68,
   "fixed": 23,
   "alt": 0,
   "cash": 9
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "eligible",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Holds an existing TEM Style Manager Strategy sleeve; overlay services cannot be layered on top of it."
 },
 {
  "id": "callahan",
  "name": "Callahan Household",
  "entity": "Individual",
  "segment": "Private Wealth",
  "aum": 18600000,
  "rev": 96000,
  "since": 2016,
  "risk": "Growth",
  "contact": "Brendan Callahan",
  "advisor_id": "dana",
  "nextMeeting": {
   "inDays": 14,
   "type": "Strategy selection",
   "note": "Weighing a move into a TEM Style Manager Strategy."
  },
  "ytdReturn": 10.2,
  "harvestable": 12000,
  "ytdRealizedGains": 30000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 9500000,
    "cost": 8600000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 4200000,
    "cost": 4500000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 3800000,
    "cost": 3900000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 1100000,
    "cost": 1100000
   }
  ],
  "target": {
   "equity": 70,
   "fixed": 25,
   "alt": 0,
   "cash": 5
  },
  "current": {
   "equity": 71,
   "fixed": 23,
   "alt": 0,
   "cash": 6
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Currently unenrolled in any TEM strategy; enrolled in the Managed Program, so a stand-alone TEM SMS mandate is open to them."
 },
 {
  "id": "duarte",
  "name": "Duarte Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 6800000,
  "rev": 42000,
  "since": 2020,
  "risk": "Moderate Growth",
  "contact": "Isabela Duarte",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 5,
   "type": "Program setup",
   "note": "Wants a TEM SMS sleeve inside her Custom Managed Strategy."
  },
  "ytdReturn": 7.1,
  "harvestable": 9000,
  "ytdRealizedGains": 14000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 3400000,
    "cost": 3100000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 1500000,
    "cost": 1550000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 1400000,
    "cost": 1400000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 500000,
    "cost": 500000
   }
  ],
  "target": {
   "equity": 65,
   "fixed": 30,
   "alt": 0,
   "cash": 5
  },
  "current": {
   "equity": 66,
   "fixed": 28,
   "alt": 0,
   "cash": 6
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Custom Managed Strategy — TEM SMS is a stand-alone investment and is not available inside Custom Managed mandates."
 },
 {
  "id": "eshun",
  "name": "Eshun Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 7500000,
  "rev": 47000,
  "since": 2019,
  "risk": "Growth",
  "contact": "Ama Eshun",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 8,
   "type": "Tax overlay review",
   "note": "Custom Managed Strategy; TER strategy is on the eligible list."
  },
  "ytdReturn": 9,
  "harvestable": 26000,
  "ytdRealizedGains": 19000,
  "holdings": [
   {
    "sym": "MSFT",
    "name": "Microsoft Corp",
    "ac": "US Equity",
    "mv": 2600000,
    "cost": 2900000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 2900000,
    "cost": 2600000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 1300000,
    "cost": 1350000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 700000,
    "cost": 700000
   }
  ],
  "target": {
   "equity": 70,
   "fixed": 20,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 72,
   "fixed": 18,
   "alt": 0,
   "cash": 10
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "eligible",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Custom Managed Strategy does not block TER — only TEM SMS is off-limits inside Custom Managed mandates."
 },
 {
  "id": "farkas",
  "name": "Farkas Household",
  "entity": "Individual",
  "segment": "Private Wealth",
  "aum": 21400000,
  "rev": 118000,
  "since": 2015,
  "risk": "Growth",
  "contact": "Tomás Farkas",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 4,
   "type": "Overlay enrollment",
   "note": "All-ETF CIO sleeve; wants both DTLH and QLH discussed."
  },
  "ytdReturn": 11.1,
  "harvestable": 64000,
  "ytdRealizedGains": 80000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 11200000,
    "cost": 9800000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 5400000,
    "cost": 5700000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 3600000,
    "cost": 3700000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 1200000,
    "cost": 1200000
   }
  ],
  "target": {
   "equity": 70,
   "fixed": 25,
   "alt": 0,
   "cash": 5
  },
  "current": {
   "equity": 72,
   "fixed": 23,
   "alt": 0,
   "cash": 5
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Client-eligible for both QLH and DTLH on this all-ETF CIO sleeve — check the servicing advisor’s offering scope."
 },
 {
  "id": "giordano",
  "name": "Giordano Household",
  "entity": "Individual",
  "segment": "Private Wealth",
  "aum": 32500000,
  "rev": 172000,
  "since": 2012,
  "risk": "Growth",
  "contact": "Nico Giordano",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 16,
   "type": "Alternatives discussion",
   "note": "Qualified purchaser; sleeve capacity open for alternatives."
  },
  "ytdReturn": 8.4,
  "harvestable": 38000,
  "ytdRealizedGains": 64000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 14000000,
    "cost": 12600000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 7500000,
    "cost": 7800000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 8000000,
    "cost": 8100000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 3000000,
    "cost": 3000000
   }
  ],
  "target": {
   "equity": 55,
   "fixed": 25,
   "alt": 15,
   "cash": 5
  },
  "current": {
   "equity": 43,
   "fixed": 25,
   "alt": 0,
   "cash": 9
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "eligible",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Client-eligible for alternatives with open sleeve capacity — check the servicing advisor’s offering scope."
 },
 {
  "id": "han",
  "name": "Han Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 11200000,
  "rev": 66000,
  "since": 2017,
  "risk": "Moderate Growth",
  "contact": "Ji-ho Han",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 19,
   "type": "Cross-border review",
   "note": "Relocated abroad this year; overlays and TER are US-resident only."
  },
  "ytdReturn": 6.7,
  "harvestable": 15000,
  "ytdRealizedGains": 22000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 5400000,
    "cost": 5000000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 3100000,
    "cost": 3200000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 2000000,
    "cost": 2050000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 700000,
    "cost": 700000
   }
  ],
  "target": {
   "equity": 60,
   "fixed": 30,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 61,
   "fixed": 28,
   "alt": 0,
   "cash": 11
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "eligible",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "No longer a US resident — TER, QLH, DTLH and TEM SMS are all US-resident-only; Direct Indexing has no residency gate."
 },
 {
  "id": "ibarra",
  "name": "Ibarra Household",
  "entity": "Individual",
  "segment": "HNW",
  "aum": 13900000,
  "rev": 81000,
  "since": 2016,
  "risk": "Growth",
  "contact": "Renata Ibarra",
  "advisor_id": "marcus",
  "nextMeeting": {
   "inDays": 7,
   "type": "Customization request",
   "note": "Wants heavy sector exclusions beyond the standard DI shelf; also pledging a low-basis stock."
  },
  "ytdReturn": 9.9,
  "harvestable": 29000,
  "ytdRealizedGains": 41000,
  "holdings": [
   {
    "sym": "GOOG",
    "name": "Alphabet Inc",
    "ac": "US Equity",
    "mv": 3400000,
    "cost": 1100000
   },
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 5000000,
    "cost": 4500000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 2700000,
    "cost": 2800000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 2100000,
    "cost": 2150000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 700000,
    "cost": 700000
   }
  ],
  "target": {
   "equity": 65,
   "fixed": 25,
   "alt": 5,
   "cash": 5
  },
  "current": {
   "equity": 68,
   "fixed": 23,
   "alt": 0,
   "cash": 9
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "eligible",
   "lending": "eligible",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Restriction depth may exceed the shelf’s tracking-error tolerance; low-basis GOOG lot is strong lending collateral, pending credit review."
 },
 {
  "id": "sato",
  "name": "Sato Household",
  "entity": "Individual",
  "segment": "Emerging HNW",
  "advisor_id": "dana",
  "program": "MGI",
  "aum": 3400000,
  "rev": 19000,
  "since": 2023,
  "risk": "Growth",
  "contact": "Renji Sato",
  "nextMeeting": {
   "inDays": 12,
   "type": "Guided Investing check-in",
   "note": "Growth-focused goal; asked whether tax-loss harvesting is available on this account."
  },
  "ytdReturn": 10.8,
  "harvestable": 22000,
  "ytdRealizedGains": 9000,
  "holdings": [
   {
    "sym": "VTI",
    "name": "US Total Market ETF",
    "ac": "US Equity",
    "mv": 1800000,
    "cost": 1550000
   },
   {
    "sym": "VXUS",
    "name": "Intl Developed ETF",
    "ac": "Intl Equity",
    "mv": 900000,
    "cost": 950000
   },
   {
    "sym": "AGG",
    "name": "US Aggregate Bond",
    "ac": "Fixed Income",
    "mv": 500000,
    "cost": 510000
   },
   {
    "sym": "CASH",
    "name": "Sweep",
    "ac": "Cash",
    "mv": 200000,
    "cost": 200000
   }
  ],
  "target": {
   "equity": 75,
   "fixed": 20,
   "alt": 0,
   "cash": 5
  },
  "current": {
   "equity": 79,
   "fixed": 16,
   "alt": 0,
   "cash": 5
  },
  "concentration": [],
  "cio": {
   "score": "Low",
   "view": "On model",
   "pub": "CIO Weekly — steady state",
   "diverge": "In line with model"
  },
  "programs": {
   "privateBanking": "na",
   "trustEstate": "na",
   "alternatives": "na",
   "directIndexing": "na",
   "lending": "na",
   "insurance": "na"
  },
  "overlays": {
   "taxManagedSMA": "na",
   "tlhOverlay": "na",
   "transition": "na",
   "charitable": "na"
  },
  "notes": "Guided Investing (MGI) account — a different program namespace from IAP. Growth-focused goal, not a retirement account, so QLH is available per the Program Website; DTLH is not (this strategy is not an eligible CIO ETF strategy)."
 }
]
```

### 5.6 Complete `app/data/fa-and-facts.json`

```json
{
 "fa_profiles": {
  "dana": {
   "id": "dana",
   "name": "Dana Whitfield",
   "role": "Sr. Wealth Advisor",
   "initials": "DW",
   "qualified_for_offering": [
    "directIndexing",
    "tlhOverlay",
    "qlhOverlay",
    "dtlhOverlay",
    "taxManagedSMA",
    "temSms",
    "transition",
    "charitable",
    "privateBanking",
    "lending",
    "trustEstate",
    "insurance",
    "alternatives"
   ]
  },
  "marcus": {
   "id": "marcus",
   "name": "Marcus Webb",
   "role": "Associate Advisor",
   "initials": "MW",
   "qualified_for_offering": [
    "directIndexing",
    "tlhOverlay",
    "taxManagedSMA",
    "temSms",
    "transition",
    "charitable",
    "privateBanking",
    "lending",
    "trustEstate",
    "insurance"
   ]
  }
 },
 "account_facts": {
  "henderson": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "customization_beyond_shelf": true,
   "in_universe_TER": true,
   "in_universe_TET": true
  },
  "okonkwo": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED"
  },
  "reyes": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "in_universe_TER": false,
   "in_universe_QLH": false
  },
  "sorensen": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "in_universe_QLH": true,
   "in_universe_TER": false
  },
  "abernathy": {
   "tax_status": "TAX_EXEMPT",
   "program_enrollment": "IAP_MANAGED"
  },
  "kaplan": {
   "tax_status": "TAXABLE",
   "program_enrollment": "NONE"
  },
  "nakamura": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "in_universe_DTLH": false
  },
  "delacroix": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "protection_gap": true
  },
  "bianchi": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "has_pas_strategy": true
  },
  "callahan": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED"
  },
  "duarte": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_CUSTOM_MANAGED"
  },
  "eshun": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_CUSTOM_MANAGED",
   "in_universe_TER": true
  },
  "farkas": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "in_universe_DTLH": true,
   "in_universe_QLH": true
  },
  "giordano": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "qualified_purchaser": true
  },
  "han": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "residency_country": "CA"
  },
  "ibarra": {
   "tax_status": "TAXABLE",
   "program_enrollment": "IAP_MANAGED",
   "customization_beyond_shelf": true,
   "has_low_basis_position": true
  },
  "sato": {
   "tax_status": "TAXABLE",
   "goal_type": "GROWTH_FOCUSED",
   "is_retirement": false,
   "available_tem_services": [
    "QLH"
   ],
   "is_eligible_cio_etf_strategy": false
  }
 },
 "account_offering_facts": {
  "henderson": {
   "taxManagedSMA": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "scope.has_overlay_ineligible_investments": false
   },
   "transition": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "transition.strategy_minimum_met": true,
    "transition.budget_minimum_met": true,
    "transition.long_term_budget_selected": true
   },
   "directIndexing": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "target_strategy.in_approved_directIndexing_roster": true,
    "target_strategy.restrictions_awaiting_manager_acceptance": false
   }
  },
  "sorensen": {
   "qlhOverlay": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "scope.has_overlay_ineligible_investments": false
   }
  },
  "eshun": {
   "taxManagedSMA": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "scope.has_overlay_ineligible_investments": false
   }
  },
  "farkas": {
   "dtlhOverlay": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "scope.has_overlay_ineligible_investments": false
   },
   "qlhOverlay": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "scope.has_overlay_ineligible_investments": false
   }
  },
  "callahan": {
   "temSms": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "target_strategy.in_approved_temSms_roster": true,
    "target_strategy.restrictions_awaiting_manager_acceptance": false
   }
  },
  "duarte": {
   "temSms": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "target_strategy.in_approved_temSms_roster": false,
    "target_strategy.restrictions_awaiting_manager_acceptance": false
   }
  },
  "ibarra": {
   "directIndexing": {
    "policy.offering_profile_verified": true,
    "account.offering_profile_requirements_met": true,
    "target_strategy.in_approved_directIndexing_roster": true,
    "target_strategy.restrictions_awaiting_manager_acceptance": true
   }
  },
  "sato": {
   "mgiQlh": {
    "policy.offering_profile_verified": true
   }
  }
 },
 "offering_minimums": {
  "taxManagedSMA": 250000,
  "qlhOverlay": 250000,
  "dtlhOverlay": 500000,
  "transition": 1000000,
  "directIndexing": 250000,
  "temSms": 250000,
  "mgiTer": 20000,
  "mgiQlh": 20000,
  "mgiDtlh": 20000
 },
 "requires_qualified_advisor": [
  "dtlhOverlay",
  "qlhOverlay",
  "alternatives"
 ]
}
```

### 5.7 Complete `app/data/rule-store.json`

This is the actual eligibility business logic — 16 offerings, roughly 92 individual rules, and 4 composition rules. **Every rule must be reproduced exactly.** Do not regenerate or paraphrase these rules from the offering labels — the specific predicates, failure classes, and messages are what the eligibility engine and the ⓘ explain-popover both depend on verbatim.

```json
{
 "pack_id": "atlas.[FIRM_NAME].tax-services.2026-09-20",
 "status": "POC_DRAFT_NOT_APPROVED_POLICY",
 "offerings": {
  "iapEnrollment": {
   "label": "IAP enrollment",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "IAP.agreement",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.iap_agreement_executed",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Enter into the IAP agreement.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Item 5: Client and Advisor Eligibility"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "IAP.account_type",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.iap_account_type_eligible",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The account type must be eligible for IAP.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Item 5: Client and Advisor Eligibility"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "IAP.separate",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.separate_account_per_program_strategy",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Use a separate account for each selected Program Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Item 5: Client and Advisor Eligibility"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "IAP.strategy_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.selected_strategy_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet the selected strategy\u2019s investor and investment minimum requirements.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "IAP.fa_scope",
     "effect": "REQUIREMENT",
     "predicate": {
      "OR": [
       {
        "field": "strategy.requires_qualified_advisor",
        "op": "EQ",
        "value": false
       },
       {
        "field": "fa.qualified_for_selected_strategy",
        "op": "EQ",
        "value": true
       }
      ]
     },
     "failure_class": "FA_SCOPE",
     "message": "Qualification is required for designated strategy types/products; obtain the qualification policy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Client and Advisor Eligibility"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "IAP.pas_contract",
     "effect": "REQUIREMENT",
     "predicate": {
      "OR": [
       {
        "field": "account.has_pas_strategy",
        "op": "EQ",
        "value": false
       },
       {
        "field": "account.pas_manager_contract_executed",
        "op": "EQ",
        "value": true
       }
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "PAS requires a separate manager/client contract.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Client and Advisor Eligibility"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "taxManagedSMA": {
   "label": "Tax Efficient Rebalancing (TER; legacy Atlas ID)",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "taxManagedSMA.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "taxManagedSMA.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "taxManagedSMA.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "taxManagedSMA.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM overlays are available only to taxable accounts.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "taxManagedSMA.not_pas",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.has_pas_strategy",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "taxManagedSMA.universe",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.in_universe_TER",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Resolve service-specific eligible investments from an approved dated strategy list.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "taxManagedSMA.eligible_scope",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_overlay_ineligible_investments",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.overlay_ineligible_investment_ids"
    },
    {
     "rule_id": "taxManagedSMA.wash_sale",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The service considers only this account. Monitor other in-house, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 40,
       "section": "Tax Matters: TEM risks"
      },
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Tax Matters: TEM risks"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "qlhOverlay": {
   "label": "Quarterly Loss Harvesting (QLH)",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "qlhOverlay.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "qlhOverlay.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "qlhOverlay.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "qlhOverlay.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM overlays are available only to taxable accounts.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "qlhOverlay.not_pas",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.has_pas_strategy",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "qlhOverlay.universe",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.in_universe_QLH",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Resolve service-specific eligible investments from an approved dated strategy list.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "qlhOverlay.eligible_scope",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_overlay_ineligible_investments",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.overlay_ineligible_investment_ids"
    },
    {
     "rule_id": "qlhOverlay.wash_sale",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The service considers only this account. Monitor other in-house, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 40,
       "section": "Tax Matters: TEM risks"
      },
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Tax Matters: TEM risks"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "dtlhOverlay": {
   "label": "Dynamic Tax Loss Harvesting (DTLH)",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "dtlhOverlay.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "dtlhOverlay.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "dtlhOverlay.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "dtlhOverlay.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM overlays are available only to taxable accounts.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "dtlhOverlay.not_pas",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.has_pas_strategy",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "dtlhOverlay.universe",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.in_universe_DTLH",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Resolve service-specific eligible investments from an approved dated strategy list.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "dtlhOverlay.eligible_scope",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_overlay_ineligible_investments",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 25,
       "section": "Tax Efficient Management Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.overlay_ineligible_investment_ids"
    },
    {
     "rule_id": "dtlhOverlay.wash_sale",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The service considers only this account. Monitor other in-house, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 40,
       "section": "Tax Matters: TEM risks"
      },
      {
       "document_id": "IAP",
       "pdf_page": 41,
       "section": "Tax Matters: TEM risks"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "transition": {
   "label": "Tax Efficient Transition (TET)",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "transition.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 1,
       "section": "Service overview"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "transition.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "transition.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TET requires a taxable account.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Account Eligibility for the Service"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.domestic",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.is_domestic",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TET requires a domestic account; use the account master classification, not an inferred citizenship/residency proxy.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Account Eligibility for the Service"
      },
      {
       "document_id": "IAP",
       "pdf_page": 26,
       "section": "Operation of the Account with TET"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.not_pas",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.has_pas_strategy",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TET is not available to an account invested in a PAS Style Manager Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 26,
       "section": "Treatment of your Account with TET"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.not_direct_index",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "target_strategy.is_direct_indexing",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Direct Indexing target strategies are not covered by TET.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Account Eligibility for the Service"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.universe",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.in_universe_TET",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select a TET-eligible target investment strategy.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Account Eligibility for the Service"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.minimum",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "transition.strategy_minimum_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet the target strategy investment minimum.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Service Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.budget_minimum",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "transition.budget_minimum_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Resolve the firm\u2019s transition budget minimum; no numeric minimum is supplied.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Service Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.budget_selected",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "transition.long_term_budget_selected",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an annual net long-term capital gains transition budget.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 3,
       "section": "Setting your Annual Net Capital Gains Budget"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "TET.scope.missing_basis",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_tet_missing_basis",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Securities without cost basis at enrollment are outside TET eligibility. Do not make this an automatic whole-account rejection.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 26,
       "section": "Treatment of Account Assets"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.tet_missing_basis_ids"
    },
    {
     "rule_id": "TET.scope.fixed_income",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_individual_fixed_income",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Individual fixed-income assets, excluding mutual funds/ETFs, are outside transition methodology. In-kind transfer or other disposition requires a separate plan.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 26,
       "section": "Treatment of Account Assets"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.individual_fixed_income_ids"
    },
    {
     "rule_id": "TET.scope.income_cash",
     "effect": "SCOPE_CARVEOUT",
     "predicate": {
      "field": "scope.has_tma_income_cash",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "For a Trust Management Account, exclude cash designated as income cash from TET consideration.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 1,
       "section": "Treatment of Account Assets"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     },
     "scope_key": "scope.tma_income_cash_ids"
    },
    {
     "rule_id": "TET.inaccurate_basis",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "scope.has_inaccurate_cost_basis",
      "op": "EQ",
      "value": true
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Resolve inaccurate cost basis before relying on the transition analysis.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Account Activity and Transactions"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD_FROM_SOURCE_RISK",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "TET.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The annual budget is not an account-wide hard tax cap. Certain sales can exceed it and other activity is outside it. Transitioning, termination and DTLH replacement sales can create gains; tax savings are not guaranteed.",
     "source_doc": [
      {
       "document_id": "TET",
       "pdf_page": 3,
       "section": "Activity that can cause budget exceedance"
      },
      {
       "document_id": "TET",
       "pdf_page": 4,
       "section": "Excluded activity"
      },
      {
       "document_id": "TET",
       "pdf_page": 5,
       "section": "Risk of Loss and TEM services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "directIndexing": {
   "label": "Direct Indexing Style Manager Strategy",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "directIndexing.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 10,
       "section": "Types of Style Manager Strategies"
      },
      {
       "document_id": "IAP",
       "pdf_page": 12,
       "section": "Custom Managed Strategy"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "directIndexing.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "directIndexing.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "directIndexing.roster",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "target_strategy.in_approved_directIndexing_roster",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The selected strategy must be in the approved manager/strategy catalog.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 9,
       "section": "Managed Strategy"
      },
      {
       "document_id": "IAP",
       "pdf_page": 10,
       "section": "Types of Style Manager Strategies"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "directIndexing.restrictions",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "target_strategy.restrictions_awaiting_manager_acceptance",
      "op": "EQ",
      "value": true
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "The strategy manager must determine whether requested restrictions are reasonable.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 11,
       "section": "Direct Indexing/TEM Style Manager Strategy"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "directIndexing.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "A manager-run Direct Indexing/TEM strategy is distinct from MAA TEM overlays and from tax-aware model strategies; tax benefits and replacement security performance are not guaranteed.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 11,
       "section": "Types of Style Manager Strategies"
      },
      {
       "document_id": "IAP",
       "pdf_page": 40,
       "section": "TEM risks"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ],
   "coverage_note": "Managed/Custom Managed lane only. PAS variants require a separate PAS policy pack and are not determined here."
  },
  "temSms": {
   "label": "TEM Style Manager Strategy",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "temSms.iap",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.program_enrollment",
      "op": "IN",
      "value": [
       "IAP_MANAGED",
       "IAP_CUSTOM_MANAGED"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Select an IAP Managed or Custom Managed Strategy.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 10,
       "section": "Types of Style Manager Strategies"
      },
      {
       "document_id": "IAP",
       "pdf_page": 12,
       "section": "Custom Managed Strategy"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "temSms.approved_profile",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     },
     "routing": "product_policy_desk"
    },
    {
     "rule_id": "temSms.profile_requirements",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.offering_profile_requirements_met",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Meet all externally versioned offering/strategy requirements; do not substitute household AUM.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 42,
       "section": "Program Minimums"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "temSms.roster",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "target_strategy.in_approved_temSms_roster",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "The selected strategy must be in the approved manager/strategy catalog.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 9,
       "section": "Managed Strategy"
      },
      {
       "document_id": "IAP",
       "pdf_page": 10,
       "section": "Types of Style Manager Strategies"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "temSms.restrictions",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "target_strategy.restrictions_awaiting_manager_acceptance",
      "op": "EQ",
      "value": true
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "The strategy manager must determine whether requested restrictions are reasonable.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 11,
       "section": "Direct Indexing/TEM Style Manager Strategy"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "temSms.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "A manager-run Direct Indexing/TEM strategy is distinct from MAA TEM overlays and from tax-aware model strategies; tax benefits and replacement security performance are not guaranteed.",
     "source_doc": [
      {
       "document_id": "IAP",
       "pdf_page": 11,
       "section": "Types of Style Manager Strategies"
      },
      {
       "document_id": "IAP",
       "pdf_page": 40,
       "section": "TEM risks"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ],
   "coverage_note": "Managed/Custom Managed lane only. PAS variants require a separate PAS policy pack and are not determined here."
  },
  "mgiTer": {
   "label": "Guided Investing TER",
   "program_scope": [
    "MGI",
    "MGI_WITH_ADVISOR"
   ],
   "rules": [
    {
     "rule_id": "mgiTer.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is intended for taxable accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiTer.growth",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.goal_type",
      "op": "EQ",
      "value": "GROWTH_FOCUSED"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for an Income-Focused goal.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiTer.not_retirement",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.is_retirement",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for Retirement Accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiTer.strategy",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.available_tem_services",
      "op": "CONTAINS",
      "value": "TER"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Use the service eligibility presented by the Program Website for the selected strategy.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiTer.full_terms",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "For additional information"
      },
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "mgiTer.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations before electing TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "mgiQlh": {
   "label": "Guided Investing QLH",
   "program_scope": [
    "MGI",
    "MGI_WITH_ADVISOR"
   ],
   "rules": [
    {
     "rule_id": "mgiQlh.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is intended for taxable accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiQlh.growth",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.goal_type",
      "op": "EQ",
      "value": "GROWTH_FOCUSED"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for an Income-Focused goal.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiQlh.not_retirement",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.is_retirement",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for Retirement Accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiQlh.strategy",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.available_tem_services",
      "op": "CONTAINS",
      "value": "QLH"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Use the service eligibility presented by the Program Website for the selected strategy.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiQlh.full_terms",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "For additional information"
      },
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "mgiQlh.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations before electing TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "mgiDtlh": {
   "label": "Guided Investing DTLH",
   "program_scope": [
    "MGI",
    "MGI_WITH_ADVISOR"
   ],
   "rules": [
    {
     "rule_id": "mgiDtlh.taxable",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.tax_status",
      "op": "EQ",
      "value": "TAXABLE"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is intended for taxable accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiDtlh.growth",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.goal_type",
      "op": "EQ",
      "value": "GROWTH_FOCUSED"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for an Income-Focused goal.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiDtlh.not_retirement",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.is_retirement",
      "op": "EQ",
      "value": false
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "TEM is unavailable for Retirement Accounts.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 2,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiDtlh.strategy",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.available_tem_services",
      "op": "CONTAINS",
      "value": "DTLH"
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Use the service eligibility presented by the Program Website for the selected strategy.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "TEM eligibility and available services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "mgiDtlh.full_terms",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "policy.offering_profile_verified",
      "op": "EQ",
      "value": false
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "For additional information"
      },
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations"
      }
     ],
     "compile_source": {
      "kind": "IMPLEMENTATION_GUARD",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "mgiDtlh.disclosure",
     "effect": "DISCLOSURE",
     "predicate": true,
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 4,
       "section": "Considerations before electing TEM Overlay Services"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    },
    {
     "rule_id": "MGI.DTLH.cio",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "target_strategy.is_eligible_cio_etf_strategy",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "DTLH is described for eligible CIO ETF strategies; membership is not proven by an ETF-only holdings test.",
     "source_doc": [
      {
       "document_id": "MGI",
       "pdf_page": 3,
       "section": "Dynamic Tax Loss Harvesting"
      }
     ],
     "compile_source": {
      "kind": "PDF_CLAUSE_PARAPHRASE",
      "review_status": "DRAFT_EXTRACTED"
     }
    }
   ]
  },
  "alternatives": {
   "label": "Alternatives",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "ALT.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "alternatives"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "ALT.req.qp",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "client.qualified_purchaser",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Alternatives require qualified-purchaser status.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "ALT.req.capacity",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.alt_capacity_pct",
      "op": "GTE",
      "value": 0.0001
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Already at/above alternatives target \u2014 no sleeve capacity.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "ALT.req.min",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.advisory_value",
      "op": "GTE",
      "value": 5000000
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Below the $5M alternatives relationship minimum.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  },
  "privateBanking": {
   "label": "Private Banking",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "PB.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "privateBanking"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "PB.req.cash",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.cash_value",
      "op": "GTE",
      "value": 1000000
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Below the $1M deposit/liquidity threshold.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  },
  "lending": {
   "label": "Securities-Based Lending",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "LEND.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "lending"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "LEND.req.collateral",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.pledgeable_marketable_value",
      "op": "GTE",
      "value": 250000
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Insufficient marketable, pledgeable collateral.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "LEND.review.lowbasis",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "account.has_low_basis_position",
      "op": "EQ",
      "value": true
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Low-basis collateral \u2014 route to credit for advance-rate review.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  },
  "trustEstate": {
   "label": "Trust & Estate",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "TE.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "trustEstate"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "TE.req.segment",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.segment",
      "op": "IN",
      "value": [
       "Private Wealth",
       "HNW"
      ]
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "Offered to Private Wealth and HNW households.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  },
  "insurance": {
   "label": "Insurance / Annuity",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "INS.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "insurance"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "INS.review.gap",
     "effect": "NEEDS_REVIEW",
     "predicate": {
      "field": "account.protection_gap",
      "op": "EQ",
      "value": true
     },
     "failure_class": "MANAGER_ADJUDICATION",
     "message": "Potential protection/annuity gap \u2014 route to insurance specialist.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  },
  "charitable": {
   "label": "Charitable / Gifting Overlay",
   "program_scope": [
    "IAP"
   ],
   "rules": [
    {
     "rule_id": "CHAR.req.fa",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "fa.qualified_for_offering",
      "op": "CONTAINS",
      "value": "charitable"
     },
     "failure_class": "FA_SCOPE",
     "message": "This offering is not in your current qualification scope. Contact your branch manager to request access.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    },
    {
     "rule_id": "CH.req.gain",
     "effect": "REQUIREMENT",
     "predicate": {
      "field": "account.has_low_basis_position",
      "op": "EQ",
      "value": true
     },
     "failure_class": "CLIENT_ELIGIBILITY",
     "message": "No appreciated low-basis position well-suited to charitable gifting.",
     "source_doc": [
      {
       "document_id": "HOUSE",
       "pdf_page": null,
       "section": "Atlas house policy (not PDF-sourced)"
      }
     ],
     "compile_source": {
      "kind": "HOUSE_POLICY",
      "review_status": "POC_DESIGN"
     }
    }
   ]
  }
 },
 "composition_rules": [
  {
   "rule_id": "COMP.TET.DTLH",
   "relation": "INCOMPATIBLE_WITH",
   "offerings": [
    "transition",
    "dtlhOverlay"
   ],
   "message": "DTLH cannot be maintained or elected while TET is active. Route a service-change plan; do not auto-cancel or trade.",
   "source_doc": [
    {
     "document_id": "TET",
     "pdf_page": 5,
     "section": "Inclusion of TEM Overlay Services"
    },
    {
     "document_id": "IAP",
     "pdf_page": 27,
     "section": "Applying TEM to a TET Service-Enrolled Account"
    }
   ],
   "compile_source": {
    "kind": "PDF_CLAUSE_PARAPHRASE",
    "review_status": "DRAFT_EXTRACTED"
   }
  },
  {
   "rule_id": "COMP.TET.TER",
   "relation": "SCOPE_CARVEOUT_WITHIN_COMPOSITION",
   "offerings": [
    "transition",
    "taxManagedSMA"
   ],
   "message": "TER applies to Investment Strategy Assets only; excludes Transition Assets. TER is default unless declined.",
   "source_doc": [
    {
     "document_id": "TET",
     "pdf_page": 5,
     "section": "Inclusion of TEM Overlay Services"
    },
    {
     "document_id": "IAP",
     "pdf_page": 27,
     "section": "Applying TEM to a TET Service-Enrolled Account"
    }
   ],
   "compile_source": {
    "kind": "PDF_CLAUSE_PARAPHRASE",
    "review_status": "DRAFT_EXTRACTED"
   },
   "scope": "INVESTMENT_STRATEGY_ASSETS_ONLY"
  },
  {
   "rule_id": "COMP.TET.QLH",
   "relation": "SCOPE_CARVEOUT_WITHIN_COMPOSITION",
   "offerings": [
    "transition",
    "qlhOverlay"
   ],
   "message": "QLH may be elected on Investment Strategy Assets only; timing can interact with budget exhaustion.",
   "source_doc": [
    {
     "document_id": "TET",
     "pdf_page": 5,
     "section": "Inclusion of TEM Overlay Services"
    },
    {
     "document_id": "IAP",
     "pdf_page": 27,
     "section": "Applying TEM to a TET Service-Enrolled Account"
    }
   ],
   "compile_source": {
    "kind": "PDF_CLAUSE_PARAPHRASE",
    "review_status": "DRAFT_EXTRACTED"
   },
   "scope": "INVESTMENT_STRATEGY_ASSETS_ONLY"
  },
  {
   "rule_id": "COMP.MGI.HARVEST",
   "relation": "INCOMPATIBLE_WITH",
   "offerings": [
    "mgiQlh",
    "mgiDtlh"
   ],
   "message": "Guided Investing presents either QLH or DTLH depending on strategy; this is not an IAP supersession rule.",
   "source_doc": [
    {
     "document_id": "MGI",
     "pdf_page": 3,
     "section": "Important note"
    }
   ],
   "compile_source": {
    "kind": "PDF_CLAUSE_PARAPHRASE",
    "review_status": "DRAFT_EXTRACTED"
   }
  }
 ]
}
```

# Current vs CIO model: four alternative views

`cio-gap-views.html` is one self-contained page (no server, no libraries) built from the same `/api/cio-fit` data as the CIO Model Fit workspace (Dana's 4 accounts, 2026 CMA). Open it in a browser. Pick an account at the top, or click a row in the grid.

| View | Question it answers | Why it differs from the workspace |
|---|---|---|
| Tiles | How far off is this account, in one number? | "To match the model, move X%" = sum of overweights (≈ $ that would change hands), plus return / risk / Sharpe gaps |
| 1. Where the account leans | Which classes are over or under, and by how many dollars? | Diverging bars centred on the model, not paired bars; the dollar amount is shown with each |
| 2. Where the return gap comes from | Which tilts cost the expected return? | Waterfall from model return to holdings return. Step = (weight diff) x (class E[r] − model E[r]); the steps sum exactly to the gap |
| 3. The whole book on one grid | Which accounts share the same tilt? | Accounts x asset classes heatmap of weight differences, with a "Move" column |
| 4. What the gap costs | Return, risk and Sharpe, holdings vs model, for every account | Dumbbells, one panel and scale per measure |

Screenshots: `alt-desktop-montgomery.png`, `alt-desktop-fairbanks.png`, `alt-desktop-dark.png`, `alt-phone.png`, `alt-hover.png`.

To use it with live data: replace the JSON after `const D =` in the page (built by `build.py` from `/api/cio-fit?fa=dana`). To add it to the app, each view is one function (`paintTilt`, `paintBridge`, `paintHeat`, `paintDumb`) that takes the account record the workspace already has.

Illustrative demo data.

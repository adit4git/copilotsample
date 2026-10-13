# Atlas standalone: one HTML, one data file

```
atlas.html       the page (code only: no data, no PDFs)
atlas-data.js    all the data, next to it
```
Open `atlas.html`. It loads `atlas-data.js` from the same folder by relative path.

## Making atlas-data.js yourself from the parts
`parts/` holds 23 plain JSON files, each one whole entity on a single line:
- `core.json`
- one per household (`household-kaplan.json`, …)
- one per advisor (`advisor-dana.json`, `advisor-marcus.json`)
- the product catalog in 8 pieces (`products-01.json` … `08.json`)

`atlas-data.js` is just this, with every part pasted between the two lines, one per line, in any order:
```
window.ATLAS_DATA_TEXT = String.raw`
{"part":"core", ...}
{"part":"household-kaplan", ...}
...
`;
```

## If something's off
The page shows a banner at the top for:
- a line that isn't complete JSON (re-copy that part);
- a missing part (it names it);
- `atlas-data.js` not being found next to the HTML.

A part pasted twice is simply ignored the second time.

Why a `.js` file and not `.json`: browsers don't let a page opened from disk read a `.json` file next to it, but they do load a `.js` file. The two wrapper lines are what make it a `.js` file.

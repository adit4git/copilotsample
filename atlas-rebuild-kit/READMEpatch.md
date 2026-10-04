# "Show me around" tour: delta

Adds the guided tour to the Atlas version built from the rebuild kit. Self-contained: it does not need the
other onboarding changes (guide page, "Opened from Ask Atlas" banner, how-to panels, "Ask Atlas about this").

## Apply
From your app root (the folder containing `app/` and `tests/`):
```bash
patch -p1 --dry-run < tour.patch   # check first: should list 5 files, no "FAILED"
patch -p1 < tour.patch
python3 -m pytest tests/ -q        # expect: 49 passed (38 existing + 11 tour tests)
```
`per-file/` has the same changes split by file, if you prefer to apply them one at a time.

## What changes
| File | Change |
|---|---|
| `app/static/app.js` | Tour engine (10 steps, panel, Back/Next/Exit); chat now shows an "Opening…" note before each jump and waits for it; click handling for the tour |
| `app/static/index.html` | "Show me around" button in the top bar |
| `app/static/styles.css` | Tour panel, button and "Opening…" note styles (one block, placed before the MOBILE section) |
| `app/agent.py` | Two fixes the tour relies on: the agent recognises "DCA"; an explicit product-shelf request is no longer turned into a vehicle comparison for a client mentioned earlier in the chat |
| `tests/test_agent.py` | 11 tests that lock in the routing of every tour request |

## Notes
- The last step returns to Ask Atlas. (In the full onboarding version it opens the Atlas guide, which isn't in this delta.)
- Each step types a real request into Ask Atlas. If the AI is slow or unavailable, the tour opens the same workspace directly.
- The patch was verified on a clean copy of the kit's code: it applies cleanly, 49/49 tests pass, and the full tour runs in a browser with every step landing on the right screen.
- If `--dry-run` reports a rejected hunk, your files differ from the kit version; send me the `.rej` file and I'll adjust.

# Ask Atlas: changes in this round

**File:** `atlas-console-book-view.html` (prototype; answers are rules over the sample book, not a language model)

**In one line:** Ask Atlas went from a home page and a panel in the workflow to a companion on every screen that knows what you're looking at, leads with a next step, answers questions about any figure, cites its sources, and can be collapsed or opened full screen.

---

## 1. Fixed: prompts shown twice in the workflow

- **Before:** the opening message in the workflow carried its own "Guide me to a decision" and two questions, and the panel below repeated them.
- **Now:** the opening message is text only and points to the controls below. Each prompt appears once.
- **Also:** the line "I know the program rules, tax services and eligibility" now appears only in the Advisory program workflow. Other opportunities say Atlas knows the client's figures, the options and the product shelf.

## 2. On every screen, one conversation

- **Where it appears:** a docked panel beside Book view, the Client dashboard and the client deep dive, as well as the workflow.
- **One thread:** the conversation follows you from Ask Atlas to Book view to a client. The workflow keeps its own decision thread, with the same header and controls.
- **What it's looking at:** the header names it, e.g. *Book view · Brokerage → Advisory program* or *Whitaker Family · Asset groups*.
- **Typed questions are answered in context:** on a client page, "how risky is it?" needs no client name.

## 3. It leads with a point of view

When a screen or view changes, Atlas adds one short message with a next-step button. An unanswered one is replaced, not stacked.

| Screen | What Atlas says first |
|---|---|
| Book view | Three things worth your time: the bond maturing soonest, this week's meeting with the most open items, the largest loss to harvest before year-end, the strongest Advisory case |
| A criterion | How many clients and how much; the strongest case and why; who is next |
| Client dashboard | This week's meetings and what to lead with |
| Client deep dive | Before the meeting: performance against benchmark, largest drift, any stock above 10%, the biggest open item, any draft proposal |
| Drilling in | A group: weight against target and the CIO stance. A class: CIO stance and largest holding. A sector: against the benchmark. Show target or proposal: what changes |

**Storyline:** once an option is chosen in a workflow:
- the client's opener mentions the draft and points to the next open item;
- Book view lists the drafts so far.

## 4. ✦ Ask about this

| Where | How | Example |
|---|---|---|
| Six key figures in the deep dive | ✦ next to the label | "Why is the drift where it is?" |
| Rows in Book view and the Client dashboard | ✦ on hover | "Why is Henderson on this list?", "What should I raise with Kaplan?" |
| Impact and risk tables in the workflow | The metric name is the link | "Explain the change in largest single stock": before → after, and the trades behind it |

## 5. Citations

- **CIO stances:** every stance in the deep dive's allocation table (▲ Overweight, ● Neutral, ▼ Underweight) can be selected. Atlas replies with:
  - the stance and a quote from the CIO House View;
  - what it means for this household, e.g. "below target while the CIO is overweight: adding here fits both";
  - a citation chip, e.g. **PDF · CIO House View · 15 Oct 2026 · Fixed income · p. 1 ↗**, which opens the document at that page.
- **CIO summary card:** carries the same citation.
- **The document:** a 5-page illustrative PDF (made-up content), embedded so the link works offline. It is also delivered as `cio-house-view-2026-10.pdf`.
- **Program knowledge answers:** cite their source document as text.

## 6. Collapse, dock or full screen

**Controls:** the header has two on every screen, including the workflow.
- **Full screen (⤢):** the conversation opens over the page at reading width, with suggested questions open. Esc, ⤡ or a click outside docks it again.
- **Collapse (—):** the panel folds into an "✦ Ask Atlas" button and the page takes the full width. A dot on the button means there is something new.

**Phone:** a sheet from the ✦ button; full screen fills the screen.

## 7. Less crowded

- One header line for what Atlas sees, instead of a separate bar and a subtitle.
- Suggested questions are folded into short sections until you pick one.
  - Panels beside a screen: *This client / This list / This screen*, *Your book*, *Program and tax*.
  - Workflow: *This client*, *Options*, *Program rules*, *Proposal*.
- On table rows, ✦ shows only on hover; in workflow tables the label is the link, so nothing wraps.
- One opener per screen.
- With the panel docked, opportunity tiles use three columns so titles and figures don't collide.

## 8. Progress, resume and reminders (latest round)

- **Where you left off:** Atlas leads with due reminders and the most recent unfinished work, e.g. "Lund Family: you left move brokerage assets to the Advisory program at Step 2 yesterday", with a **Resume** button. A client's opener starts with that client's unfinished work.
- **Welcome back:** returning to a workflow on a later day, Atlas says where you left off and what changed in the figures since then (e.g. "the CD now matures in 46 days (was 49)").
- **Reminders by asking:** "remind me 2 days before the bond matures", "remind me weekly", "remind me before the meeting". "What's on my plate?" lists the work.
- **Day-level timing:** today, yesterday, a weekday, last week or a date, never hours.
- Also new outside the panel: "Pick up where you left off" cards, status on tiles and rows, **Remind me** and **Mark done** in the workflow header, and a bell with what is due. See section 10 of the walkthrough.

## Checked

| Check | Result |
|---|---|
| Openers | 115 screens (Book view, all 13 criteria, the dashboard, 4 views of every household) each open with a point of view |
| In-context questions | 2,104 (suggested questions, ✦ on figures and rows) all get a specific answer |
| Workflow questions | 1,543, none falls back to a generic reply |
| Modes | Collapse, full screen and Esc work on desktop and phone; no sideways scrolling at 390 px; no page errors |
| Citation | The embedded PDF opens from the chip; each stance links to the page that discusses it |
| Tour | 27 steps, including "Ask Atlas follows you", "Pick up where you left off" and "Progress and reminders" |
| Progress | Status lifecycle, reminders due on the right simulated day, weekly reminders roll forward, work survives a reload |

## Not in the prototype; needed for production

- **Answering:** pass the same screen context (screen, client, selection, choices so far) to a language model, with the page's figures as tools.
- **Citations:** come from a document store with real research and CIO publications, not one embedded PDF.
- **Memory:** per-client answers from the decision guide (tax tolerance, who decides) and a work queue across the book. Both were proposed but not built yet.

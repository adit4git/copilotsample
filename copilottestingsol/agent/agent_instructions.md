# Agent Instructions

- Prefer precision over speculation; cite file paths and line numbers.
- Write findings directly into `/context/*.md` appending under new sections.
- When uncertain, propose verification steps the human can run quickly.


## Output Structure Requirements
- When producing JSON, validate against `/schemas/*.schema.json`.
- When producing reports, use the tables/sections in `/context/Template_*` files.
- Always include file paths and (if available) line numbers for each finding.
- Append to `/context/*.md` under a new heading with timestamp.

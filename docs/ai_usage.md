# Use of generative AI

Required by the grading criteria (no. 7) and the HSG rules on AI use. This file is the basis for the "list of aids" slide in the video.

## Rules for the team
1. **AI as an aid** (explaining errors, brainstorming): add the tool to the log below.
2. **AI-generated code** used in the project **must be cited in the source code**, directly above the code:
   ```python
   # AI-generated: Claude (Anthropic), 15.11.2026. Prompt: "create a radar chart with plotly ..."
   # Adapted by: <name>
   ```
3. Before submitting, check that every AI-generated block is marked.

## Log

| Date | Tool | Who | What for | Where in the code |
|---|---|---|---|---|
| 24.10.2026 | Claude (Anthropic) | Anisha | Brainstorming app idea, attributes, name | – |
| 15.11.2026 | Claude (Anthropic) | Anisha | Repository structure (steps 1–6): README, requirements, file headers, TODO lists, `app.py` routing, `config.py`, database schema, page layouts, helper functions | All files with "AI NOTE" in their header |
| 15.11.2026 | Claude (Anthropic) | Anisha | Seed data script (fake users, WGs, swipes, feedback) | `data/seed_data.py` |
| 19.11.2026 | OpenAI Codex | – | Complete SQLite read/write functions, add an in-memory example with SQL inserts for all eight tables, close seed connections, and validate database workflows | `core/database.py`, `data/database_example.py`, `data/seed_data.py`, `tests/test_database.py` |
| 19.11.2026 | OpenAI Codex | – | Implement remaining account, profile, listing, photo, transport, matching, chat, offer, feedback, chart, and ML features; add service and Streamlit integration tests and update documentation | `app.py`, `core/`, `components/`, `views/`, `tests/test_features.py`, `README.md`, `docs/database_schema.md` |
| 19.11.2026 | OpenAI Codex | – | Make WG offers accessible to logged-in seekers and providers, add role switching, listing visibility status, and integration checks | `app.py`, `views/wg_listing.py`, `tests/test_features.py`, `README.md` |
| 19.11.2026 | OpenAI Codex | – | Diagnose Cyril / Jack swipe exclusions, allow provider-first swiping, explain hidden candidates, and add regressions for both swipe orders and saved-data blockers | `core/database.py`, `core/matching.py`, `views/swipe.py`, `tests/test_features.py`, `README.md` |
| 19.11.2026 | OpenAI Codex | – | Add live chat polling, a searchable inbox, escaped message bubbles, persistent per-participant unread counts, and chat workflow regressions | `views/matches.py`, `components/chat.py`, `core/database.py`, `data/database_example.py`, `tests/`, `requirements.txt`, `README.md`, `docs/database_schema.md` |
| | | | | |

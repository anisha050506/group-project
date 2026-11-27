# Use of generative AI

Required by the grading criteria (no. 7) and the HSG rules on AI use. This file is the basis for the "list of aids" slide in the video.

## Rules for the team
1. **AI as an aid** (explaining errors, brainstorming): add the tool to the list of aids below.
2. **AI-generated code** used in the project **must be cited in the source code**, directly above the code:
   ```python
   # AI-generated: Claude (Anthropic), 15.11.2026. Prompt: "create a radar chart with plotly ..."
   # Adapted by: <name>
   ```
3. Before submitting, check that every AI-generated block is marked.

## List of aids

| Date | Tool | What for |
|---|---|---|
| 24.10.2026 | Claude (Anthropic) | Brainstorming app idea, attributes, name |
| 15.11.2026 | Claude (Anthropic) | Repository structure (steps 1–6): README, requirements, file headers, TODO lists, `app.py` routing, `config.py`, database schema, page layouts, helper functions |
| 15.11.2026 | Claude (Anthropic) | Seed data script (fake users, WGs, swipes, feedback) |
| 19.11.2026 | OpenAI Codex | Complete SQLite read/write functions, add an in-memory example with SQL inserts for all eight tables, close seed connections, and validate database workflows |
| 19.11.2026 | OpenAI Codex | Implement remaining account, profile, listing, photo, transport, matching, chat, offer, feedback, chart, and ML features; add service and Streamlit integration tests and update documentation |
| 19.11.2026 | OpenAI Codex | Make WG offers accessible to logged-in seekers and providers, add role switching, listing visibility status, and integration checks |
| 19.11.2026 | OpenAI Codex | Diagnose Cyril / Jack swipe exclusions, allow provider-first swiping, explain hidden candidates, and add regressions for both swipe orders and saved-data blockers |
| 19.11.2026 | OpenAI Codex | Add live chat polling, a searchable inbox, escaped message bubbles, persistent per-participant unread counts, and chat workflow regressions |
| 22.11.2026 | Claude (Anthropic) | Seed demo data automatically on an empty database (so the deployed app is never empty) and recreate the 16 named test accounts from `test_accounts.txt` |
| 22.11.2026 | Claude (Anthropic) | In-app notifications for new matches and unread messages (sidebar bell, menu badge, toast) |
| 22.11.2026 | Claude (Anthropic) | UX improvements: getting-started onboarding checklist, swipe undo / match celebration / icon buttons, labelled lifestyle sliders, verified badges |
| 22.11.2026 | Claude (Anthropic) | Remove the district field from the listing form, WG cards, and Insights |
| 22.11.2026 | Claude (Anthropic) | Centralise the colour palette in one `BRAND` config and adjust the theme |
| 22.11.2026 | Claude (Anthropic) | Redesign the ML model: predict mutual matches (both accept) with logistic regression, learn a weight per lifestyle factor, evaluate with repeated held-out-seeker cross-validation; remove the satisfaction survey |
| 22.11.2026 | Claude (Anthropic) | Remove the now-unused feedback table and survey helpers; write the ML design document |
| | | |

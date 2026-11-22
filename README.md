# WG Match

**A web application that matches HSG students looking for a room with shared flats (WGs) in St. Gallen, based on lifestyle compatibility.**

Group project in *Fundamentals and Methods of Computer Science*, University of St. Gallen, autumn 2026. Built with Python and Streamlit.

---

## 1. Problem & solution

**Problem.** Other real estate companies manage real apartments and may add WG features on the side. In a student city like St. Gallen, however, shared flats are not a small aspect of the housing market. Students looking for a room send dozens of messages and attend castings without knowing whether they would get along with their future flatmates. WGs spend hours screening unsuitable candidates. Existing platforms only filter by price and location.

**Solution.** Our application focuses only on WGs. It is not just "a Flatfox for WGs": through centralized processing of verified data, it optimizes the search itself.

- Only verified students can join. Seekers and WG members answer the same lifestyle questions (tidiness, sociability, noise, guests, sleep rhythm, …).
- Hard filters (budget, move-in date, travel time to HSG, smoking, gender preference) hide WGs that can never work.
- The remaining WGs are ranked by a compatibility score, supported by our own machine-learning model.
- Both sides swipe and either side can like first. A mutual like becomes a match, which leads to a chat, a viewing and finally the room.

**Future features (not in scope for this project):** organizing dinner parties between WGs, an admin panel, automated paperwork (sublease contract, registration in St. Gallen).

## 2. How to run the application

Requirements: **Python 3.11 or newer**.

```bash
# 1. Get the code
git clone https://github.com/anisha050506/group-project.git
cd group-project

# 2. (Recommended) create and activate a virtual environment
python -m venv .venv
# Windows:    .venv\Scripts\activate
# Mac/Linux:  source .venv/bin/activate

# 3. Install all required libraries
pip install -r requirements.txt

# 4. Create the test database with fake users and WGs (once, or to reset)
python -m data.seed_data

# 5. Start the app (opens http://localhost:8501 in the browser)
streamlit run app.py
```

All required libraries are listed in `requirements.txt`.

To try a small in-memory database with SQL inserts for all eight tables, run
`python -m data.database_example`. It uses `sqlite3`, `pandas`, and
`DB.executescript(...)` and leaves the saved app database untouched.

**Test accounts** (created by the seed script, password `demo1234`): `ana.demo@student.unisg.ch` (seeker), `jonas.demo@student.unisg.ch` (WG provider). Register a new account to try profile setup from the beginning.

Registration, login, saved profiles and photos, search criteria, listing edits,
WG member management, ranked swiping, chat, viewings, room offers, acceptance,
and Insights are implemented. Only the main tenant edits a listing
or offers its room. Accepting an offer hides the listing and closes competing
matches in the same transaction. Log out to test the other side of a match.

Student and address verification are **simulated for this course demo**. No
verification email is sent. Address verification is an explicit simulation
checkbox on the listing form. Transport times and map coordinates use the
[Swiss Transport API](https://transport.opendata.ch/docs.html); failed lookups
stay unknown and can be refreshed from the listing form.

To offer a room, log in and open **Offer a WG** in the sidebar. Seekers can
choose **Start offering a WG** to switch to the provider role while keeping
their profile and saved criteria. Enter the room details, rent, availability,
house rules, and an optional photo, then click **Offer WG**. Keep **Room
available** checked and enable **Simulate address verification (course demo)**
to make the listing visible to seekers. The page shows its visibility status;
you can edit the offer, add registered flatmates, or mark the room unavailable
later. Complete the lifestyle sliders in **My profile** before matching.

**Matches & chat** has a searchable inbox, recent-message previews, unread
counts, and a separate conversation pane. Messages and new matches update
automatically every two seconds while the page is open. Conversations stay
selected when new messages arrive; read positions are saved separately for
each participant. Sent and received messages have distinct bubbles, day
separators, and St. Gallen timestamps. Viewing, room-offer, and acceptance
actions are under the conversation's detail sections. Streamlit 1.66 or later is
required for the auto-scrolling conversation container.

The provider's **Swipe** page shows eligible seekers even before they have
liked the WG. A match is created only after both sides like each other.
When no candidates remain, **Why candidates are hidden** explains unmet
requirements, incomplete profiles, and previous swipes. Unknown travel times
cannot satisfy a seeker's travel limit; correct the listing's address and use
**Refresh public transport data** on the WG form to retry the lookup.

The model is a **logistic regression** that predicts whether a match will
succeed — whether both sides accept — from the normalized absolute differences
between the eight seeker and WG lifestyle sliders. It trains on **real match
outcomes** (accepted = 1, declined = 0), not a survey. Evaluation uses repeated
held-out-seeker cross-validation and reports accuracy against a majority
baseline, balanced accuracy, ROC AUC, and Brier score, then refits on all
resolved matches. Its learned coefficients become a weight per lifestyle factor,
which weight the compatibility score so ranking learns which factors matter
instead of treating all eight equally. Seed outcomes are synthetic; demo metrics
do not establish performance on real tenants. When a trained model is available,
ranking combines 80% lifestyle similarity and 20% match probability; with
insufficient data it uses equal-weight lifestyle similarity alone.

Train or refresh the model in **Insights**, or run:

```bash
python -m core.ml_model
```

Run the automated service and Streamlit page tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

Tests use temporary databases, models, and uploads. They cover registration
through profile setup, role switching, saved listing edits, mutual swipes,
chat, offers, acceptance, match outcomes, and model training. Transport responses
and failures are mocked so the suite works offline.

Database and model paths resolve relative to the project, regardless of the
working directory. For an isolated copy, set `WG_MATCH_DB_PATH` and
`WG_MATCH_MODEL_PATH` before starting Python. Photos are validated, resized,
and stored in `assets/uploads/`, which is excluded from Git. The seed command
resets the selected database; run it only when you intend to replace its data.

## 3. Folder structure

```
group-project/
├── .gitignore         files Git never uploads (database, virtual env, secrets)
├── .streamlit/
│   └── config.toml    look of the app (colours, font)
├── app.py             ENTRY POINT – start with: streamlit run app.py (routing)
├── views/             one file per page (what the user sees)
│   ├── login.py             log in with an HSG account
│   ├── register.py          create account with HSG email, choose role
│   ├── profile.py           personal profile, 8 lifestyle sliders, role switch
│   ├── search_criteria.py   seekers: max rent, move-in date, travel time …
│   ├── wg_listing.py        providers: create / edit the WG listing
│   ├── swipe.py             one card at a time, sorted by match score
│   ├── matches.py           matches, chat, viewing, offer, acceptance
│   └── insights.py          charts + ML output
├── core/              app logic (plain Python, no Streamlit code)
│   ├── config.py      shared names & choice lists – change sliders/lists HERE
│   ├── database.py    SQLite tables + all read/write functions
│   ├── auth.py        registration, login, password hashing
│   ├── matching.py    hard filters, compatibility score, ranking
│   ├── ml_model.py    logistic-regression training, evaluation, learned weights
│   ├── transport_api.py   travel time to HSG (transport.opendata.ch)
│   └── uploads.py     validation and resizing for uploaded photos
├── components/        reusable page pieces
│   ├── layout.py      login checks, session handling, sidebar and logout
│   ├── forms.py       saved defaults for editable forms
│   ├── cards.py       WG card / seeker card
│   ├── chat.py        chat bubbles, conversation headers, and local timestamps
│   └── charts.py      radar chart, score gauge, rent vs travel time, map
├── data/
│   ├── database_example.py  small in-memory SQLite example for all eight tables
│   ├── seed_data.py   creates fake users, WGs, swipes and resolved matches
│   └── wg_match.db    the database (created automatically, not on GitHub)
├── docs/
│   ├── database_schema.md      overview of all database tables
│   ├── contribution_matrix.md  who did what (shown in the video)
│   └── ai_usage.md             AI use log + citation rules (shown in the video)
├── tests/             isolated service and Streamlit integration tests
├── README.md          project description and instructions (this file, not part of the app)
└── requirements.txt   all libraries needed to run the app
```

## 4. Team & responsibilities

| Member | Responsibility | Files |
|---|---|---|
| *Name* | | |
| *Name* | | |
| *Name* | | |
| *Name* | | |




## 5. Use of AI

AI tools were used as an aid and, where marked, to generate code. Every AI-generated code block is cited directly in the source code. The full log is in `docs/ai_usage.md`.

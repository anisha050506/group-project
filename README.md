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
- Both sides swipe. A mutual like becomes a match, which leads to a chat, a viewing and finally the room.

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

# 4. Start the app (opens http://localhost:8501 in the browser)
streamlit run app.py
```

All required libraries are listed in `requirements.txt`.

## 3. Folder structure

*This section is filled in step by step as the structure is built.*

```
group-project/
├── .gitignore         files Git never uploads (database, virtual env, secrets)
├── .streamlit/
│   └── config.toml    look of the app (colours, font)
├── core/              app logic (plain Python, no Streamlit code)
│   ├── config.py      shared names & choice lists – change sliders/lists HERE
│   └── database.py    SQLite tables + all read/write functions
├── docs/
│   └── database_schema.md   overview of all database tables
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

## 5. Git workflow

1. `git pull` before you start working.
2. Work on your own branch: `git checkout -b feature/<your-area>`.
3. Only edit the files you are responsible for. Ask before changing someone else's file.
4. Commit small and often with a clear message, e.g. `git commit -m "Add compatibility score"`.
5. Push and open a **pull request**. One teammate reviews it before it is merged into `main`.
6. When you add a new library, add it to `requirements.txt` in the same commit.

## 6. Grading requirements

| # | Requirement | Where it is covered |
|---|---|---|
| 1 | Problem clearly stated | Section 1 of this README, video |
| 2 | Data via API and/or database | SQLite database + transport.opendata.ch API *(to be built)* |
| 3 | Data visualization | Insights page and charts *(to be built)* |
| 4 | User interaction | Profile, search criteria, WG listing, swiping, chat *(to be built)* |
| 5 | Own trained ML model | *(approach to be defined)* |
| 6 | Well-documented source code | Comments and file headers in every file |
| 7 | Contribution matrix + GenAI reflection | `docs/` *(to be added)* |
| 8 | 4-minute video with own voice-over | Submitted on Canvas by 10.12.2026 |

## 7. Use of AI

AI tools were used as an aid and, where marked, to generate code. Every AI-generated code block is cited directly in the source code. The full log will be in `docs/ai_usage.md`.

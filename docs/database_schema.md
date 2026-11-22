# Database schema (SQLite: `data/wg_match.db`)

Owner: Person B. The source of truth is `SCHEMA` in `core/database.py`. Update this file whenever the schema changes.

For a small in-memory database in the `sqlite3` / `pandas` /
`DB.executescript(...)` format, run `python -m data.database_example`.
It creates all eight tables using the shared schema and inserts related sample
rows into every table. Use it from Python like this:

```python
import pandas as pd
from data.database_example import DB

users = pd.read_sql_query("SELECT user_id, name, bio FROM users", DB)
```

SQL `NULL` represents missing values; quoted text such as `'Null'` remains text.
In Python database writes, use `None` for SQL `NULL`. The example is discarded
when the process exits. The app continues to save data to `data/wg_match.db`.

```
users ──< wg_members >── wgs
  │                        │
  ├── search_criteria      │
  │                        │
  └──────< swipes >────────┤
  └──────< matches >───────┘   → resolved matches (accepted/declined) = ML labels
               └──< messages
```

| Table | One row = | Key columns |
|---|---|---|
| `users` | one student (seeker or provider) | user_id, email, password_hash, role, name, birth_year, gender, languages, degree, study_level, bio, is_verified, **8 sliders** |
| `search_criteria` | the hard criteria of one seeker | user_id, max_rent, move_in_date, max_travel_time, preferred_flatmate_gender, smoker |
| `wgs` | one flat with a free room | wg_id, address, district, rent_chf, room_size_m2, available_from, smoking_allowed, preferred_gender, travel_time_min, is_verified, is_active |
| `wg_members` | one person living in one WG | wg_id, user_id, is_main_tenant |
| `swipes` | one like / pass | seeker_id, wg_id, swiped_by ('seeker' / 'wg'), liked |
| `matches` | both sides liked each other | match_id, seeker_id, wg_id, status, viewing_done |
| `messages` | one chat message | match_id, sender_id, text |
| `conversation_reads` | one participant's saved read position in a chat | match_id, user_id, last_read_message_id |

## The 8 behavioural sliders (0–10)
`tidiness`, `sociability`, `noise_tolerance`, `guests`, `sleep_rhythm`, `cooking_together`, `cleaning_schedule`, `time_at_home`. They're defined once in `core/config.py → SLIDERS`.

A **WG's lifestyle profile** is the average of its members' sliders (`database.get_wg_lifestyle_profile`).

`database.get_training_data()` returns one pandas DataFrame row per **resolved
match** (status `accepted` or `declined`): `match_id`, `seeker_id`, `wg_id`,
`seeker_<slider>` and `wg_<slider>` for each slider, and `matched` (1 when
accepted, 0 when declined). WG sliders are current member averages; missing
values remain missing. This is the label the logistic-regression model learns
from (see `core/ml_model.py`).

## Match workflow

An unanswered pair becomes a match when both sides like it. Repeated likes
keep one swipe per side and one match per pair. Inactive or unverified rooms,
the seeker's own WG, and seekers who already accepted a room cannot receive
new swipes.

WG members can record a viewing with `mark_viewing_done`. The main tenant
can then offer the room through `change_match_status`; only that match's
seeker can accept. Acceptance reserves the room, makes its listing inactive,
and declines competing open/offered matches for both the WG and seeker in
one transaction. The accepted match remains accessible for chat.

The outcome of each match (`accepted` vs `declined`) is the training signal for
the recommendation model, so no separate satisfaction survey is collected.

## Live conversations

`get_conversations_for_user` restricts the inbox to matches involving the
seeker or a member of the WG. It returns latest-message previews and counts
only other participants' messages above the viewer's saved read position.
`mark_conversation_read` advances that position through the last displayed
message, so a message arriving during a refresh stays unread until displayed.
Read positions are independent for each WG member and seeker. `init_db`
adds the read-position table and message lookup index to existing databases
without replacing any data. The chat page polls the inbox every two seconds.

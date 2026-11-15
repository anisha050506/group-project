# Database schema (SQLite: `data/wg_match.db`)

Owner: Person B. The source of truth is `SCHEMA` in `core/database.py`. Update this file whenever the schema changes.

```
users ──< wg_members >── wgs
  │                        │
  ├── search_criteria      │
  │                        │
  └──────< swipes >────────┤
  └──────< matches >───────┘
               └──< messages
  feedback (seeker_id, wg_id, satisfied)  → ML training data
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
| `feedback` | "was the match good?" | seeker_id, wg_id, satisfied (0/1) |

## The 8 behavioural sliders (0–10)
`tidiness`, `sociability`, `noise_tolerance`, `guests`, `sleep_rhythm`, `cooking_together`, `cleaning_schedule`, `time_at_home`. They're defined once in `core/config.py → SLIDERS`.

A **WG's lifestyle profile** is the average of its members' sliders (`database.get_wg_lifestyle_profile`).

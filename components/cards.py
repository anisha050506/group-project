"""Reusable WG and seeker cards."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
from datetime import date
from pathlib import Path

import streamlit as st


def _photo(path):
    if path and Path(path).is_file():
        st.image(path, width="stretch")


def _score(score, mismatches):
    if score is not None:
        st.progress(max(0.0, min(1.0, score / 100)), text=f"{score:.0f}% compatibility")
    if mismatches:
        st.caption("Different habits: " + " · ".join(mismatches))


def wg_card(wg: dict, score: float | None = None, mismatches: list[str] | None = None) -> None:
    with st.container(border=True):
        _photo(wg.get("photo_path"))
        st.subheader(wg.get("title") or "Room in a shared flat")
        if wg.get("address"):
            st.caption(str(wg["address"]))
        rent, size, travel = st.columns(3)
        rent.metric("Rent / month", f"CHF {wg['rent_chf']:,.0f}" if wg.get("rent_chf") is not None else "Unknown")
        size.metric("Room", f"{wg['room_size_m2']:g} m²" if wg.get("room_size_m2") is not None else "Unknown")
        travel.metric("To HSG", f"{wg['travel_time_min']} min" if wg.get("travel_time_min") is not None else "Unknown")
        st.caption(":green[:material/verified: Verified address] (simulated)" if wg.get("is_verified") else ":orange[:material/schedule: Address verification pending]")
        _score(score, mismatches)
        if wg.get("description"):
            st.write(wg["description"])
        facts = [f"Available {wg['available_from']}" if wg.get("available_from") else "Availability unknown"]
        if wg.get("available_until"):
            facts.append(f"until {wg['available_until']}")
        if wg.get("min_rental_months"):
            facts.append(f"minimum {wg['min_rental_months']} months")
        st.caption(" · ".join(facts))
        st.caption(" · ".join(str(wg[key]) for key in ("wg_type", "amenities") if wg.get(key)))
        st.caption(f"Smoking: {wg.get('smoking_allowed') or 'unspecified'} · Flatmate preference: {wg.get('preferred_gender') or 'any'}")


def seeker_card(seeker: dict, score: float | None = None, mismatches: list[str] | None = None) -> None:
    with st.container(border=True):
        _photo(seeker.get("photo_path"))
        st.subheader(seeker.get("name") or "Student")
        facts = []
        if seeker.get("birth_year"):
            facts.append(f"Born {seeker['birth_year']} (turns {date.today().year - seeker['birth_year']} this year)")
        facts.extend(str(seeker[key]) for key in ("degree", "study_level", "languages") if seeker.get(key))
        st.caption(" · ".join(facts))
        _score(score, mismatches)
        if seeker.get("bio"):
            st.write(seeker["bio"])
        st.caption(":green[:material/verified: Verified HSG student] (simulated)" if seeker.get("is_verified") else ":orange[:material/schedule: Student verification pending]")

"""Create and edit a WG, its room, photos, and registered members."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
from pathlib import Path
import streamlit as st
from components import charts, cards
from components.forms import date_value, number_value, option_index
from components.layout import require_login
from core import database, transport_api
from core.uploads import save_photo
from core.config import AMENITIES, FLATMATE_GENDER_PREFS, SMOKING_OPTIONS, WG_TYPES

require_login()
user_id = st.session_state.user_id
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: make a feature where we can offer a WG.
if st.session_state.role != "offer_wg":
    st.title("Offer a WG")
    st.write("Have a room available in your shared flat? Create a listing with a photo, rent, availability, and house rules to find a compatible flatmate.")
    st.info("Starting a listing switches your account to “I offer a WG”. Your profile and saved search criteria are kept. You can switch back in My profile.")
    if st.button("Start offering a WG", type="primary"):
        database.update_role(user_id, "offer_wg")
        st.session_state.role = "offer_wg"
        st.session_state["_next_page"] = "views/wg_listing.py"
        st.rerun()
    st.stop()

wg = database.get_wg_for_user(user_id) or {}
wg_id = wg.get("wg_id")
st.title("My WG" if wg_id else "Offer a WG")
members = database.get_wg_members(wg_id) if wg_id else []
is_main = not wg_id or any(member["user_id"] == user_id and member["is_main_tenant"] for member in members)
if wg_id:
    st.session_state.wg_id = wg_id
    st.caption("Address verification is simulated for this course demo.")
    if not wg.get("is_active"):
        st.info("Your room is marked unavailable. This listing is hidden from seekers.")
    elif not wg.get("is_verified"):
        st.info("Your listing is saved but hidden from seekers. The main tenant can enable simulated address verification and save to make it visible.")
    else:
        st.success("Your WG is available to seekers whose search criteria match this room.")
    st.page_link("views/swipe.py", label="Find a flatmate", icon=":material/swipe:")
    st.page_link("views/profile.py", label="Complete your lifestyle profile", icon=":material/person:")
    if not is_main:
        cards.wg_card(wg)
        st.info("The main tenant manages this listing. You can update your lifestyle in My profile.")
    if wg.get("photo_path") and Path(wg["photo_path"]).is_file() and is_main:
        st.image(wg["photo_path"], width=320)

if is_main:
    if not wg_id:
        st.write("Tell students about the room and your flat. You will be added as the main tenant and can edit the listing or add flatmates after saving.")
        st.caption("To show your room to seekers, keep “Room available” checked and enable simulated address verification. You can also save first and verify later.")
    with st.form(f"wg_form_{wg_id or 'new'}"):
        st.subheader("Location")
        data = {"title": st.text_input("Title", wg.get("title") or "", max_chars=120)}
        col1, col2 = st.columns(2)
        data["address"] = col1.text_input("Street and number", wg.get("address") or "", max_chars=200)
        data["postcode"] = col2.text_input("Postcode", wg.get("postcode") or "9000", max_chars=4)
        st.subheader("Costs")
        col1, col2, col3 = st.columns(3)
        data["rent_chf"] = col1.number_input("Rent / month incl. utilities (CHF)", min_value=0.0, value=float(number_value(wg, "rent_chf", 750)), step=10.0)
        data["utilities_chf"] = col2.number_input("Of which utilities (CHF)", min_value=0.0, value=float(number_value(wg, "utilities_chf", 80)), step=10.0)
        data["deposit_chf"] = col3.number_input("Deposit (CHF)", min_value=0.0, value=float(number_value(wg, "deposit_chf", 1500)), step=100.0)
        st.subheader("Room & flat")
        col1, col2, col3 = st.columns(3)
        data["room_size_m2"] = col1.number_input("Room size (m²)", min_value=1.0, value=float(number_value(wg, "room_size_m2", 14)))
        data["flat_size_m2"] = col2.number_input("Flat size (m²)", min_value=1.0, value=float(number_value(wg, "flat_size_m2", 90)))
        data["num_rooms"] = col3.number_input("Rooms in the flat", min_value=1.0, value=float(number_value(wg, "num_rooms", 3.5)), step=0.5)
        data["num_flatmates"] = col1.number_input("Flatmates (without new person)", min_value=1, value=int(number_value(wg, "num_flatmates", max(1, len(members)))))
        data["furnished"] = int(col1.checkbox("Furnished", value=bool(wg.get("furnished"))))
        data["private_bathroom"] = int(col2.checkbox("Private bathroom", value=bool(wg.get("private_bathroom"))))
        data["balcony"] = int(col3.checkbox("Balcony", value=bool(wg.get("balcony"))))
        data["amenities"] = ",".join(st.multiselect("Amenities", AMENITIES, default=[item for item in (wg.get("amenities") or "").split(",") if item in AMENITIES]))
        st.subheader("Availability")
        col1, col2 = st.columns(2)
        data["available_from"] = col1.date_input("Available from", date_value(wg.get("available_from"))).isoformat()
        limited = col2.checkbox("Fixed end date", value=bool(wg.get("available_until")))
        until = col2.date_input("Available until", date_value(wg.get("available_until")))
        data["available_until"] = until.isoformat() if limited else None
        data["min_rental_months"] = col1.number_input("Minimum rental period (months)", min_value=0, value=int(number_value(wg, "min_rental_months", 6)))
        data["is_active"] = int(col2.checkbox("Room available", value=bool(wg.get("is_active", 1))))
        st.subheader("House rules")
        col1, col2 = st.columns(2)
        data["wg_type"] = col1.selectbox("WG type", WG_TYPES, index=option_index(WG_TYPES, wg.get("wg_type")))
        data["smoking_allowed"] = col2.selectbox("Smoking", SMOKING_OPTIONS, index=option_index(SMOKING_OPTIONS, wg.get("smoking_allowed")))
        data["preferred_gender"] = col1.selectbox("New flatmate", FLATMATE_GENDER_PREFS, index=option_index(FLATMATE_GENDER_PREFS, wg.get("preferred_gender")))
        data["pets_allowed"] = int(col2.checkbox("Pets allowed", value=bool(wg.get("pets_allowed"))))
        data["description"] = st.text_area("Tell seekers about your WG", wg.get("description") or "", max_chars=5000)
        upload = st.file_uploader("Room photo (up to 5 MB)", type=["jpg", "jpeg", "png", "webp"])
        remove_photo = st.checkbox("Remove current photo") if wg.get("photo_path") else False
        data["is_verified"] = int(st.checkbox("Simulate address verification (course demo)", value=bool(wg.get("is_verified"))))
        refresh = st.checkbox("Refresh public transport data")
        submitted = st.form_submit_button("Save WG" if wg_id else "Offer WG", type="primary")
    if submitted:
        try:
            data["title"], data["address"] = data["title"].strip(), data["address"].strip()
            if not data["title"] or not data["address"]:
                raise ValueError("Enter a title and street address.")
            if not data["postcode"].isdigit() or len(data["postcode"]) != 4:
                raise ValueError("Enter a four-digit Swiss postcode.")
            if data["utilities_chf"] > data["rent_chf"] or data["room_size_m2"] > data["flat_size_m2"]:
                raise ValueError("Utilities must fit within the rent, and the room within the flat.")
            if data["available_until"] and data["available_until"] <= data["available_from"]:
                raise ValueError("The end date must be after the availability date.")
            if data["is_active"] and wg_id and any(match["wg_id"] == wg_id and match["status"] == "accepted" for match in database.get_matches_for_user(user_id)):
                raise ValueError("This room has already been accepted. Keep its listing inactive.")
            address_changed = any(data[key] != wg.get(key) for key in ("address", "postcode"))
            unavailable = False
            if refresh or address_changed or wg.get("travel_time_min") is None:
                address = f"{data['address']}, {data['postcode']} St. Gallen"
                with st.spinner("Checking public transport to HSG…"):
                    data["travel_time_min"] = transport_api.get_travel_time_minutes(address)
                    coordinates = transport_api.get_location_coordinates(address)
                data["latitude"], data["longitude"] = coordinates or (None, None)
                unavailable = data["travel_time_min"] is None
                if not address_changed:
                    for key in ("travel_time_min", "latitude", "longitude"):
                        if data[key] is None:
                            data[key] = wg.get(key)
            if upload:
                data["photo_path"] = save_photo(upload, f"wg_{user_id}")
            elif remove_photo:
                data["photo_path"] = None
            created = not wg_id
            if wg_id:
                database.update_wg(wg_id, data)
            else:
                wg_id = database.create_wg(data, user_id)
            st.session_state.wg_id = wg_id
            st.session_state["_notice"] = ("WG listing created." if created else "WG saved.") + (" Travel lookup is unavailable; refresh it later." if unavailable else "")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

if wg_id:
    st.subheader("WG lifestyle")
    profile = database.get_wg_lifestyle_profile(wg_id)
    st.plotly_chart(charts.radar_chart(database.get_user_by_id(user_id), profile), width="stretch")
    st.caption("The WG profile averages the answered sliders of its registered members.")
    st.subheader("Members")
    for member in members:
        col1, col2 = st.columns([4, 1])
        col1.write(f"{member['name']}" + (" · Main tenant" if member["is_main_tenant"] else ""))
        if is_main and not member["is_main_tenant"] and col2.button("Remove", key=f"remove_{member['user_id']}"):
            database.remove_wg_member(wg_id, member["user_id"], user_id)
            st.rerun()
    if is_main:
        with st.form("add_member"):
            email = st.text_input("Add a registered flatmate by HSG email")
            add = st.form_submit_button("Add flatmate")
        if add:
            member = database.get_user_by_email(email)
            if not member:
                st.error("This flatmate needs to register first.")
            elif database.get_wg_for_user(member["user_id"]):
                st.error("This student already belongs to a WG.")
            else:
                database.add_wg_member(wg_id, member["user_id"])
                st.session_state["_notice"] = "Flatmate added."
                st.rerun()

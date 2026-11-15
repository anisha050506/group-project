"""
THIS FILE ONLY EXPLAINS WHAT IS IN THE "CORE" FOLDER --> NO CODING HERE

core/  =  the "brain" of the app: plain Python logic, NO Streamlit calls.

Why? Code without st.* can be tested on its own (e.g. in a notebook or with
python -c "..."), and it can be reused by several pages.

    config.py         shared constants (slider names, choices, file paths)
    database.py       SQLite: tables + all read/write functions
    auth.py           registration, login, password hashing
    matching.py       hard filters + compatibility score + ranking
    ml_model.py       machine-learning model (train / load / predict)
    transport_api.py  travel time to HSG via transport.opendata.ch
"""

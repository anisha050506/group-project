import streamlit as st
pages_dir = "pages/"
st.write(f"{pages_dir}cozi")
pages = {
        "User Account":[
            st.Page(f"{pages_dir}make_user_account.py", title="Create your user account"),
            st.Page(f"{pages_dir}manage_user_account.py", title="Manage your user account")],
        "Find Roommate":[st.Page(f"{pages_dir}find_roommate.py", title="Find a roommate")],
        "Find Room": [st.Page(f"{pages_dir}find_room.py", title="Find a room")]
        
}

pg = st.navigation(pages)
pg.run()

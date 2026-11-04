import streamlit as st

views = {"Your login":[
    st.Page("views/home.py", title="Home"),
    st.Page("views/login.py", title="Login"),
    st.Page("views/register.py", title="Register")
    ],
    "Stories": [
        st.Page("views/stories/story1.py", title="Story1", url_path="salman"),
        st.Page("views/stories/story2.py", title="Story2")
        ]
         }

navigator = st.navigation(views, position="top")
navigator.run()

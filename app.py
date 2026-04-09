import streamlit as st
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="IRL TRADE", layout="wide")

USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

if "online_users" not in st.session_state:
    st.session_state.online_users = {}
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név").lower()
    p = st.text_input("PW", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

current_user = st.session_state.username
st.session_state.online_users[current_user] = time.time()
now = time.time()
st.session_state.online_users = {user: t for user, t in st.session_state.online_users.items() if now - t < 30}

st.sidebar.title(f"Szia {current_user.capitalize()}!")
online_list = [u for u in st.session_state.online_users.keys() if u != current_user]

if not online_list:
    st.sidebar.warning("Nincs senki online.")
else:
    for u in online_list:
        st.sidebar.success(f"🟢 {u.capitalize()}")

menu = st.tabs(["🚀 TRADE", "📜 HISTORY", "🏠 BASE"])

with menu[0]:
    if not online_list:
        st.error("Nincs online partner!")
    else:
        target = st.selectbox("Partner", online_list)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Honnan", ["Catánia", "New York", "Planeland", "Codeland", "London"])
            end = st.selectbox("Hová", ["Catánia", "New York", "Planeland", "Codeland", "London"])
        with c2:
            item = st.text_input("Tartalom")
            pkg = st.text_input("Csomagolás")
        photo = st.file_uploader("Kép", type=['jpg', 'png'])
        if st.button("🚀 INDÍTÁS"):
            if item and photo:
                st.session_state.trade_history.append({"Idő": datetime.now().strftime("%H:%M"), "Küldő": current_user, "Fogadó": target, "Tárgy": item, "Útvonal": f"{start}->{end}"})
                placeholder = st.empty()
                for i in range(10, 0, -1):
                    with placeholder.container():
                        st.markdown(f'<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:999;display:flex;flex-direction:column;justify-content:center;align-items:center;"><h1 style="color:red;font-size:150px;">{i}s</h1><h2 style="color:white;">Szállítás: {target.upper()}</h2></div>', unsafe_allow_html=True)
                    time.sleep(1)
                placeholder.empty()
                st.success("Megérkezett!")

with menu[1]:
    st.header("History")
    if st.session_state.trade_history:
        st.table(pd.DataFrame(st.session_state.trade_history[::-1]))

with menu[2]:
    st.header("The Base")
    st.image("https://r2.erf.hu/placeholder-base.jpg")

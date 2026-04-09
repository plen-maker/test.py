import streamlit as st
import time
import pandas as pd
from datetime import datetime

# --- KONFIGURÁCIÓ ---
st.set_page_config(page_title="IRL TRADE", layout="wide")

# Felhasználók listája
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- ÉLŐ ONLINE ÁLLAPOT KEZELÉSE ---
# Ez a rész a szerver memóriájában tárolja, ki van bent
if "online_users" not in st.session_state:
    st.session_state.online_users = {}

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név").lower()
    p = st.text_input("PW", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

# Aktuális user frissítése az online listában
current_user = st.session_state.username
st.session_state.online_users[current_user] = time.time()

# Takarítás: aki 30 másodperce nem frissített, az offline
now = time.time()
st.session_state.online_users = {user: t for user, t in st.session_state.online_users.items() if now - t < 30}

# --- INTERFÉSZ ---
st.sidebar.title(f"Szia {current_user.capitalize()}!")
st.sidebar.subheader("Online most:")
online_list = [u for u in st.session_state.online_users.keys() if u != current_user]

if not online_list:
    st.sidebar.warning("Nincs senki online rajtad kívül.")
else:
    for u in online_list:
        st.sidebar.success(f"🟢 {u.capitalize()}")

menu = st.tabs(["🚀 TRADE", "📜 HISTORY", "🏠 BASE"])

# --- TRADE TAB ---
with menu[0]:
    if not online_list:
        st.error("Várj, amíg a barátod be nem lép, különben nincs kinek küldeni!")
    else:
        st.header("Új szállítás")
        target = st.selectbox("Ki kapja?", online_list)
        
        col1, col2 = st.columns(2)
        with col1:
            start = st.selectbox("Honnan", ["Catánia", "New York", "Planeland", "Codeland", "London"])
            end = st.selectbox("Hová", ["Catánia", "New York", "Planeland", "Codeland", "London"])
        with col2:
            item = st.text_input("Tartalom")
            pkg = st.text_input("Csomag külseje (Final Package)")

        photo = st.file_uploader("Kép a tartalomról", type=['jpg', 'png'])

        if st.button("🚀 INDÍTÁS"):
            if item and photo:
                # Elmentés a közös history-ba
                trade_data = {
                    "Idő": datetime.now().strftime("%H:%M"),
                    "Küldő": current_user,
                    "Fogadó": target,
                    "Tárgy": item,
                    "Útvonal": f"{start} -> {end}"
                }
                st.session_state.trade_history.append(trade_data)

                # FULL SCREEN TIMER
                placeholder = st.empty()
                for i in range(10, 0, -1):
                    with placeholder.container():
                        st.markdown(f"""
                        <div style="position: fixed; top:0; left:0; width:100%; height:100%; background:black; z-index:999; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                            <h1 style="color:red; font-size:150px;">{i}s</h1>
                            <h2 style="color:white;">Szállítás ide: {target.upper()}</h2>
                            <p style="color:gray;">{start} ➔ {end}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    time.sleep(1)
                placeholder.empty()
                st.success("KÉSZ! Megérkezett.")
            else:
                st.warning("Kép és név kötelező!")

# --- HISTORY TAB ---
with menu[1]:
    st.header("Korábbi trade-ek")
    if st.session_state.trade_history:
        st.table(pd.DataFrame(st.session_state.trade_history[::-1]))
    else:
        st.write("Még nem történt mozgás.")

# --- BASE TAB ---
with menu[2]:
    st.header("The Base Update")
    st.image("https://r2.erf.hu/placeholder-base.jpg", caption="A bázis jelenlegi állapota") # Cseréld le!
    st.write("Itt láthatók a bázisról készült legfrissebb fotók.")
        
        st.table(user_trades[['time', 'sender', 'receiver', 'item', 'origin', 'dest']])
        
        st.subheader("Legutóbbi frissítések")
        for t in data["trades"][-5:]: # Utolsó 5
            st.write(f"🔔 **{t['sender']}** küldött egy csomagot ide: **{t['dest']}** ({t['time']})")

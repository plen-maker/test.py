import streamlit as st
import time
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# --- ADATBÁZIS KEZELÉS (Egyszerű JSON fájl) ---
DB_FILE = "trade_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"trades": []}

def save_trade(trade):
    data = load_data()
    data["trades"].append(trade)
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- KONFIGURÁCIÓ ---
st.set_page_config(page_title="IRL Trade Hub", layout="wide")

# Felhasználók (Írd át a valódi neveitekre!)
USERS = {
    "admin": "1234",
    "pisti": "pisti77",
    "lacika": "trade99"
}

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🛡️ IRL Trade Login")
    user_input = st.text_input("Felhasználónév")
    pass_input = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if user_input in USERS and USERS[user_input] == pass_input:
            st.session_state.logged_in = True
            st.session_state.username = user_input
            st.rerun()
        else:
            st.error("Helytelen adatok!")
    st.stop()

# --- FŐ INTERFÉSZ ---
st.sidebar.title(f"Üdv, {st.session_state.username}!")
menu = st.sidebar.radio("Menü", ["Főoldal / Trade", "History & Updates", "The Base"])

# --- 1. THE BASE (A bázis fotója) ---
if menu == "The Base":
    st.title("🏠 The Base - HQ")
    # Itt egy placeholder kép van, de a sajátodat is beillesztheted
    st.image("https://images.unsplash.com/photo-1518005020453-1bb7470f6f3d?q=80&w=1000", 
             caption="A Központ - Itt zajlanak a logisztikai folyamatok", use_container_width=True)
    st.info("Ez a központi elosztó pontunk minden szállítmányhoz.")

# --- 2. TRADE INDÍTÁSA ---
elif menu == "Főoldal / Trade":
    st.title("🚀 Új Szállítás Indítása")
    
    col1, col2 = st.columns(2)
    with col1:
        # Ki tudod választani a partnert (aki nem te vagy)
        others = [u for u in USERS.keys() if u != st.session_state.username]
        target = st.selectbox("Partner kiválasztása", others)
        origin = st.selectbox("Indulási helyszín", ["Catánia", "New York", "Planeland", "Codeland", "London"])
        dest = st.selectbox("Célállomás", ["Catánia", "New York", "Planeland", "Codeland", "London"])

    with col2:
        item = st.text_input("Mi van a csomagban?")
        package_look = st.text_input("Hogy néz ki a becsomagolt APCKAGE?")
        photo = st.file_uploader("Fotó a tartalomról", type=['jpg', 'png'])

    if st.button("TRADING INDÍTÁSA"):
        if item and photo:
            # Trade mentése
            new_trade = {
                "id": str(int(time.time())),
                "sender": st.session_state.username,
                "receiver": target,
                "item": item,
                "origin": origin,
                "dest": dest,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "Folyamatban"
            }
            save_trade(new_trade)

            # EGÉSZ ABLAKOS TIMER
            timer_placeholder = st.empty()
            duration = 10 # Teszteléshez 10 másodperc, de átírhatod (random.randint(300, 600))
            
            for i in range(duration, 0, -1):
                with timer_placeholder.container():
                    st.markdown(f"""
                    <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #0e1117; color: #ff4b4b; border-radius: 20px; border: 5px solid #ff4b4b;">
                        <h1 style="font-size: 100px; margin: 0;">{i}</h1>
                        <p style="font-size: 30px;">SZÁLLÍTÁS FOLYAMATBAN...</p>
                        <p style="font-size: 20px;">{origin} ➔ {dest}</p>
                    </div>
                    """, unsafe_allow_html=True)
                time.sleep(1)
            
            timer_placeholder.success("✅ A CSOMAG MEGÉRKEZETT!")
            st.balloons()
        else:
            st.error("Tölts ki mindent és adj meg fotót!")

# --- 3. HISTORY & UPDATES ---
elif menu == "History & Updates":
    st.title("📜 Trade History & Updates")
    data = load_data()
    
    if not data["trades"]:
        st.write("Még nem volt trade.")
    else:
        df = pd.DataFrame(data["trades"])
        # Csak azokat mutatja, amikben az adott user érintett
        user_trades = df[(df['sender'] == st.session_state.username) | (df['receiver'] == st.session_state.username)]
        
        st.table(user_trades[['time', 'sender', 'receiver', 'item', 'origin', 'dest']])
        
        st.subheader("Legutóbbi frissítések")
        for t in data["trades"][-5:]: # Utolsó 5
            st.write(f"🔔 **{t['sender']}** küldött egy csomagot ide: **{t['dest']}** ({t['time']})")

import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="IRL LOGISTIC SYSTEM", layout="wide")

# --- KÖZÖS MEMÓRIA (SZERVER SZINTŰ) ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, # Folyamatban lévő szállítások
        "balances": {"admin": 5000, "peti": 5000, "adel": 5000}, # Alap egyenleg
        "base_photo": "https://images.unsplash.com/photo-1590247813693-5541d1c609fd?q=80&w=1000"
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név").lower().strip()
    p = st.text_input("PW", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            if u not in global_data["balances"]: global_data["balances"][u] = 50000
            st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()
now = time.time()
global_data["online_users"] = {u: t for u, t in global_data["online_users"].items() if now - t < 20}

# --- SIDEBAR ---
st.sidebar.title(f"💰 Egyenleg: {global_data['balances'][current_user]} Ft")
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

# --- TABS ---
menu = st.tabs(["🚀 ÚJ TRADE", "📥 ÉRKEZŐ CSOMAGOK", "📜 HISTORY", "🏠 BASE"])

# --- 1. ÚJ TRADE ---
with menu[0]:
    if not others_online:
        st.warning("Nincs online partner.")
    else:
        target = st.selectbox("Partner", others_online)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Honnan", ["Catánia (HU)", "Codeland (RO)", "New York", "Planeland", "London"])
            end = st.selectbox("Hová", ["Catánia (HU)", "Codeland (RO)", "New York", "Planeland", "London"])
        with c2:
            item = st.text_input("Tartalom")
            pkg = st.text_input("Final Package leírás")
        
        photo = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
        
        if st.button("🚀 INDÍTÁS (990 Ft)"):
            if global_data["balances"][current_user] < 990:
                st.error("Nincs elég pénzed!")
            elif item and photo:
                global_data["balances"][current_user] -= 990
                wait_min = random.randint(5, 10)
                trade_id = f"{current_user}_{int(time.time())}"
                
                global_data["active_trades"][trade_id] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item,
                    "start_time": datetime.now(),
                    "arrival_time": datetime.now() + timedelta(minutes=wait_min),
                    "status": "ÚTON",
                    "pkg_returned": False
                }
                st.success(f"Szállítás elindítva! Várható érkezés: {wait_min} perc múlva.")
            else:
                st.error("Hiányzó adatok!")

# --- 2. ÉRKEZŐ CSOMAGOK & VISSZAIGAZOLÁS ---
with menu[1]:
    st.header("Csomagjaim")
    my_incoming = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user}
    
    if not my_incoming:
        st.write("Nincs érkező csomagod.")
    
    for tid, t in my_incoming.items():
        st.info(f"📦 {t['item']} tőle: {t['sender']}")
        if datetime.now() >= t["arrival_time"]:
            if st.button(f"Átvétel visszaigazolása ({t['item']})", key=tid):
                t["status"] = "MEGÉRKEZETT"
                t["received_at"] = datetime.now()
                st.success("Átvétel rögzítve! Most 10 perced van visszaadni a szatyrot.")
                st.rerun()
        else:
            diff = t["arrival_time"] - datetime.now()
            st.write(f"⏳ Érkezés: {int(diff.total_seconds()//60)} perc múlva.")

    st.divider()
    st.subheader("Szatyor visszajelzés (Küldőként)")
    my_sent = {tid: t for tid, t in global_data["active_trades"].items() if t["sender"] == current_user and t["status"] == "MEGÉRKEZETT"}
    
    for tid, t in my_sent.items():
        deadline = t["received_at"] + timedelta(minutes=10)
        st.write(f"Partnernél: {t['receiver']} | Szatyor határidő: {deadline.strftime('%H:%M:%S')}")
        if st.button(f"Szatyor megérkezett ({t['receiver']})", key=f"ret_{tid}"):
            if datetime.now() > deadline:
                global_data["balances"][t["receiver"]] -= 155
                st.warning("Késve jött a szatyor, 155 Ft levonva tőle.")
            
            # Véglegesítés history-ba
            global_data["trade_history"].append({
                "Idő": datetime.now().strftime("%H:%M"),
                "Küldő": t["sender"],
                "Fogadó": t["receiver"],
                "Tárgy": t["item"],
                "Status": "TELJESÍTVE"
            })
            del global_data["active_trades"][tid]
            st.rerun()

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt Trade-ek")
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"][::-1]))

# --- 4. BASE FOTÓ ---
with menu[3]:
    st.header("The Base")
    st.image(global_data["base_photo"], use_container_width=True)
    new_base_img = st.file_uploader("Bázis fotó frissítése", type=['jpg', 'png'])
    if st.button("Bázis fotó mentése"):
        if new_base_img:
            # Itt csak szimuláljuk a mentést, mivel a streamlit nem tárol fájlt tartósan
            st.success("Bázis fotó frissítve!")

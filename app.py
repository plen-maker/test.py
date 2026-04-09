import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="IRL LOGISTIC CONTROL", layout="wide")

# --- SEGÉDFÜGGVÉNYEK ---
def safe_date_format(dt, fmt="%H:%M:%S"):
    if dt is None: return "--:--:--"
    if isinstance(dt, str): return dt
    try: return dt.strftime(fmt)
    except: return str(dt)

# --- KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000},
        "base_gallery": []
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

# --- SIDEBAR ---
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

# --- TABS ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "📋 RENDELÉSEK (CONTROL)", "📜 HISTORY", "🏠 BASE"])

# --- 1. TRADE INDÍTÁS ---
with menu[0]:
    st.header("Új szállítás előkészítése")
    if not others_online:
        st.info("Nincs más online.")
    else:
        target = st.selectbox("Címzett", others_online)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "London"])
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "London"])
        with c2:
            item_price = st.number_input("Termék ára (Ft)", min_value=0, value=1000)
            item = st.text_input("Mi van a csomagban?")
        
        photo = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
        
        if st.button("Kérelem küldése"):
            if item and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item,
                    "price": item_price,
                    "status": "WAITING_ACCEPTANCE",
                    "state_text": "Csomagolás alatt...",
                    "photo": photo,
                    "start_loc": start,
                    "end_loc": end,
                    "eta_time": None,
                    "wait_min": random.randint(5, 10) # Mindig generálunk 5-10 percet
                }
                st.success("Kérelem elküldve!")
            else:
                global_data["balances"][current_user] -= 1500
                st.error("Hiányzó adatok! 1500 Ft büntetés.")

# --- 2. RENDELÉSEK (CONTROL PANEL) ---
with menu[1]:
    # A) CÍMZETTNEK: Elfogadás
    my_requests = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user and t["status"] == "WAITING_ACCEPTANCE"}
    if my_requests:
        st.subheader("📩 Bejövő kérelmek")
        for tid, t in my_requests.items():
            with st.container(border=True):
                st.write(f"**{t['sender']}** küldene: {t['item']} ({t['price']} Ft)")
                if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                    global_data["balances"][t["sender"]] -= (t["price"] + 990)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()

    # B) FELADÓNAK: Control Panel
    st.subheader("🎮 Feladói Vezérlőpult")
    my_controls = {tid: t for tid, t in global_data["active_trades"].items() if t["sender"] == current_user and t["status"] == "ACCEPTED"}
    
    for tid, t in my_controls.items():
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** -> **{t['receiver']}** (Generált idő: {t['wait_min']} perc)")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                # Státusz kézi váltása
                new_state = st.selectbox("Fázis", 
                    ["We received your order", "Your order is in the plane", 
                     "Your order is at the airport", "Your order is on its final route", 
                     "Your order is at your gate"], 
                    key=f"st_{tid}")
                if st.button("Státusz mentése", key=f"btn_st_{tid}"):
                    t["state_text"] = new_state
                    st.rerun()

            with c2:
                # ETA AKTIVÁLÁSA
                if t["eta_time"] is None:
                    if st.button("🚀 SZÁLLÍTÁS INDÍTÁSA (ETA FIXÁLÁSA)", key=f"eta_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=t["wait_min"])
                        t["start_time"] = datetime.now()
                        st.rerun()
                else:
                    st.write(f"Várható érkezés: **{t['eta_time'].strftime('%H:%M:%S')}**")

            with c3:
                with st.expander("Számla"):
                    st.image(t["photo"], width=100)
                    st.write(f"Összeg: {t['price'] + 990} Ft")

    # C) ÉLŐ KÖVETÉS (Mindkét fél látja)
    st.divider()
    st.subheader("🚚 Aktív szállítások követése")
    tracking = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "ACCEPTED"}
    
    for tid, t in tracking.items():
        with st.container(border=True):
            st.write(f"**{t['item']}** | Feladó: {t['sender']} | Cél: {t['receiver']}")
            st.info(f"📍 Aktuális fázis: {t['state_text']}")
            
            if t["eta_time"]:
                now = datetime.now()
                remaining = t["eta_time"] - now
                if remaining.total_seconds() > 0:
                    # Progress bar kiszámítása
                    total_dur = t["wait_min"] * 60
                    elapsed = (now - t["start_time"]).total_seconds()
                    prog = min(elapsed / total_dur, 1.0)
                    
                    st.progress(prog)
                    st.write(f"⏳ Érkezésig: **{int(remaining.total_seconds() // 60)}p {int(remaining.total_seconds() % 60)}mp**")
                else:
                    st.success("✅ A csomag megérkezett!")
                    if current_user == t["receiver"]:
                        if st.button("Átvétel igazolása", key=f"rec_{tid}"):
                            t["status"] = "DELIVERED"
                            t["received_at"] = datetime.now()
                            st.rerun()
            else:
                st.warning("Várakozás a feladó indítására...")

# --- 3. HISTORY & 4. BASE ---
with menu[2]:
    st.header("Lezárt folyamatok")
    # Szatyor visszajelzés (Küldő igazolja le a legvégén)
    delivered = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "DELIVERED" and t["sender"] == current_user}
    for tid, t in delivered.items():
        if st.button(f"Szatyor visszaérkezett ({t['item']})", key=f"hist_{tid}"):
            global_data["trade_history"].append({
                "Idő": datetime.now().strftime("%H:%M"), 
                "Küldő": t["sender"], "Vevő": t["receiver"], "Tárgy": t["item"]
            })
            del global_data["active_trades"][tid]
            st.rerun()
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))

with menu[3]:
    st.header("Base Hub")
    new_b = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
    if st.button("Feltöltés"):
        if new_b:
            global_data["base_gallery"].append({"photo": new_b, "user": current_user, "time": datetime.now().strftime("%H:%M")})
    if global_data["base_gallery"]:
        cols = st.columns(3)
        for idx, entry in enumerate(global_data["base_gallery"][::-1]):
            with cols[idx % 3]:
                st.image(entry["photo"])
                st.caption(f"{entry['user']} | {entry['time']}")

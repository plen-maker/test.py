import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC BUDAPEST", layout="wide")

# --- AUTO-REFRESH (Másodpercenként frissít, hogy ketyegjen a timer) ---
if "active_trades" in st.cache_resource().get_keys(): # Csak ha van aktív trade
    time.sleep(1)
    st.rerun()

# --- SEGÉDFÜGGVÉNYEK ---
def safe_date_format(dt, fmt="%H:%M:%S"):
    if dt is None: return "--:--:--"
    if isinstance(dt, str):
        try: dt = datetime.fromisoformat(dt)
        except: return dt
    try: return dt.strftime(fmt)
    except: return str(dt)

def get_price(trade_dict):
    for key in ['price', 'item_price', 'total_price']:
        if key in trade_dict: return trade_dict[key]
    return 0

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
    st.title("🛡️ IRL LOGIN - BUDAPEST HUB")
    u = st.text_input("Felhasználónév", key="login_name").lower().strip()
    p = st.text_input("Jelszó", type="password", key="login_pw")
    if st.button("Belépés", key="login_btn"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            if u not in global_data["balances"]: global_data["balances"][u] = 50000
            st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- SIDEBAR ---
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
st.sidebar.metric("Saját Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

# --- TABS ---
menu = st.tabs(["🚀 KÜLDÉS", "📋 RENDELÉSEK & CONTROL", "📜 HISTORY", "🏠 BASE HQ"])

# --- 1. KÜLDÉS ---
with menu[0]:
    st.header("Új szállítás indítása")
    if not others_online:
        st.info("Nincs más futár online a hálózaton.")
    else:
        target = st.selectbox("Címzett", others_online, key="trade_target")
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulási pont", ["Budapest Központ", "Budaörs Depot", "Debrecen HUB", "Győr Terminal"], key="trade_start")
            end = st.selectbox("Célállomás", ["Budapest Központ", "Budaörs Depot", "Debrecen HUB", "Győr Terminal"], key="trade_end")
        with c2:
            price_input = st.number_input("Termék értéke (Ft)", min_value=0, value=1000, key="trade_price")
            item_name = st.text_input("Csomag tartalma", key="trade_item_name")
        
        photo = st.file_uploader("Termékfotó feltöltése", type=['jpg', 'png'], key="trade_photo_up")
        
        if st.button("📦 Kérelem küldése a rendszerbe", key="trade_send_btn"):
            if item_name and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item_name,
                    "price": price_input,
                    "status": "WAITING_ACCEPTANCE",
                    "state_text": "Rögzítve a rendszerben",
                    "photo": photo,
                    "start_loc": start,
                    "end_loc": end,
                    "eta_time": None,
                    "wait_min": random.randint(5, 10)
                }
                st.success("A kérelem megérkezett a címzetthez!")
                st.rerun()
            else:
                st.error("HIÁNYZÓ ADATOK!")

# --- 2. RENDELÉSEK & CONTROL ---
with menu[1]:
    # BEJÖVŐ (CÍMZETTNEK)
    my_requests = {tid: t for tid, t in global_data["active_trades"].items() 
                   if t.get("receiver") == current_user and t.get("status") == "WAITING_ACCEPTANCE"}
    if my_requests:
        st.subheader("📩 Új csomagod érkezne")
        for tid, t in my_requests.items():
            with st.container(border=True):
                st.write(f"**{t['sender']}** küldené: **{t['item']}** | Érték: {get_price(t)} Ft")
                if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                    global_data["balances"][t["sender"]] -= (get_price(t) + 990)
                    t["status"] = "ACCEPTED"
                    t["state_text"] = "Futárra vár..."
                    st.rerun()

    st.divider()

    # CONTROL PANEL (FELADÓNAK - Itt állítod a státuszt és az időt)
    st.subheader("🎮 Futár Vezérlőpult")
    my_controls = {tid: t for tid, t in global_data["active_trades"].items() 
                   if t.get("sender") == current_user and t.get("status") == "ACCEPTED"}
    
    for tid, t in my_controls.items():
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** -> {t['receiver']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                # Manuális fázis állítás
                new_state = st.selectbox("Fázis", 
                    ["Csomag felvéve", "Úton a reptérre", "A gép felszállt", "Kiszállítás alatt", "A kapu előtt"], 
                    index=["Csomag felvéve", "Úton a reptérre", "A gép felszállt", "Kiszállítás alatt", "A kapu előtt"].index(t["state_text"]) if t["state_text"] in ["Csomag felvéve", "Úton a reptérre", "A gép felszállt", "Kiszállítás alatt", "A kapu előtt"] else 0,
                    key=f"sel_{tid}")
                if st.button("Státusz mentése", key=f"upd_{tid}"):
                    t["state_text"] = new_state
                    st.rerun()
            with c2:
                # Manuális ETA indítás
                if t.get("eta_time") is None:
                    m_set = st.number_input("Perc:", 1, 60, t['wait_min'], key=f"minset_{tid}")
                    if st.button("🚀 SZÁLLÍTÁS INDÍTÁSA", key=f"start_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=m_set)
                        t["start_time"] = datetime.now()
                        t["wait_min"] = m_set
                        st.rerun()
                else:
                    st.success(f"ETA: {safe_date_format(t['eta_time'])}")
            with c3:
                with st.expander("Számla"):
                    st.image(t["photo"], use_container_width=True)
                    st.write(f"Végösszeg: {get_price(t) + 990} Ft")

    # ÉLŐ KÖVETÉS ÉS TIMER (MINDENKI LÁTJA)
    st.divider()
    st.subheader("📢 Élő Szállítási Állapot")
    tracking = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    
    for tid, t in tracking.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** ({t['sender']} -> {t['receiver']})")
            st.info(f"📍 Jelenlegi helyzet: **{t['state_text']}**")
            
            eta = t.get("eta_time")
            if eta:
                if isinstance(eta, str): eta = datetime.fromisoformat(eta)
                remaining = (eta - datetime.now()).total_seconds()
                
                if remaining > 0:
                    m, s = divmod(int(remaining), 60)
                    st.header(f"⏳ HÁTRALÉVŐ IDŐ: {m:02d}:{s:02d}")
                    # Progress bar
                    total_s = t.get("wait_min", 10) * 60
                    elapsed = (datetime.now() - t.get("start_time", datetime.now())).total_seconds()
                    st.progress(min(1.0, elapsed / total_s))
                else:
                    st.success("✅ A CSOMAG MEGÉRKEZETT!")
                    if current_user == t["receiver"]:
                        if st.button("Átvétel igazolása", key=f"recv_{tid}"):
                            t["status"] = "DELIVERED"
                            t["received_at"] = datetime.now()
                            st.rerun()
            else:
                st.warning("Várakozás az indításra...")

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt szállítások")
    delivered = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "DELIVERED" and t.get("sender") == current_user}
    for tid, t in delivered.items():
        if st.button(f"Szatyor visszaérkezett: {t['item']}", key=f"bag_{tid}"):
            global_data["trade_history"].append({"Idő": datetime.now().strftime("%H:%M"), "Küldő": t["sender"], "Címzett": t["receiver"], "Tárgy": t["item"], "Összeg": get_price(t)+990})
            del global_data["active_trades"][tid]
            st.rerun()
    if global_data.get("trade_history"):
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- 4. BASE HQ ---
with menu[3]:
    st.header("Bázis Galéria")
    new_b = st.file_uploader("Fotó", type=['jpg', 'png'], key="base_up")
    if st.button("Feltöltés", key="base_btn"):
        if new_b:
            global_data["base_gallery"].append({"photo": new_b, "user": current_user, "time": datetime.now().strftime("%H:%M")})
            st.rerun()
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"👤 {entry['user']} | 🕒 {entry['time']}")

# Force refresh loop for the timer
if any(t.get("status") == "ACCEPTED" and t.get("eta_time") for t in global_data["active_trades"].values()):
    time.sleep(1)
    st.rerun()

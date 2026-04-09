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

def get_price(trade_dict):
    """Biztonságosan lekéri az árat, bármi is legyen a kulcs neve."""
    for key in ['price', 'item_price', 'total_price']:
        if key in trade_dict:
            return trade_dict[key]
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
        st.info("Várj, amíg a partner belép...")
    else:
        target = st.selectbox("Címzett", others_online)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "London"])
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "London"])
        with c2:
            price_input = st.number_input("Termék ára (Ft)", min_value=0, value=1000)
            item_name = st.text_input("Mi van a csomagban?")
        
        photo = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
        
        if st.button("🚀 Kérelem küldése"):
            if item_name and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item_name,
                    "price": price_input,
                    "status": "WAITING_ACCEPTANCE",
                    "state_text": "Csomagolás alatt...",
                    "photo": photo,
                    "start_loc": start,
                    "end_loc": end,
                    "eta_time": None,
                    "wait_min": random.randint(5, 10)
                }
                st.success("Kérelem elküldve!")
            else:
                global_data["balances"][current_user] = global_data["balances"].get(current_user, 50000) - 1500
                st.error("Hiányzó adatok! 1500 Ft büntetés levonva.")

# --- 2. RENDELÉSEK (CONTROL PANEL) ---
with menu[1]:
    # A) CÍMZETTNEK: Elfogadás
    my_requests = {tid: t for tid, t in global_data["active_trades"].items() 
                   if t.get("receiver") == current_user and t.get("status") == "WAITING_ACCEPTANCE"}
    
    if my_requests:
        st.subheader("📩 Bejövő kérelmek")
        for tid, t in my_requests.items():
            with st.container(border=True):
                price = get_price(t)
                st.write(f"**{t.get('sender')}** küldene: {t.get('item')} ({price} Ft)")
                if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                    # Levonás a küldőtől (ár + szállítás)
                    global_data["balances"][t["sender"]] = global_data["balances"].get(t["sender"], 50000) - (price + 990)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()

    # B) FELADÓNAK: Control Panel
    st.subheader("🎮 Feladói Vezérlőpult")
    my_controls = {tid: t for tid, t in global_data["active_trades"].items() 
                   if t.get("sender") == current_user and t.get("status") == "ACCEPTED"}
    
    for tid, t in my_controls.items():
        with st.container(border=True):
            st.write(f"📦 **{t.get('item')}** -> **{t.get('receiver')}**")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                new_state = st.selectbox("Fázis módosítása", 
                    ["We received your order", "Your order is in the plane", 
                     "Your order is at the airport", "Your order is on its final route", 
                     "Your order is at your gate"], 
                    key=f"st_{tid}")
                if st.button("Mentés", key=f"btn_st_{tid}"):
                    t["state_text"] = new_state
                    st.rerun()
            with c2:
                if t.get("eta_time") is None:
                    if st.button("🚀 SZÁLLÍTÁS INDÍTÁSA", key=f"eta_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=t.get("wait_min", 7))
                        t["start_time"] = datetime.now()
                        st.rerun()
                else:
                    st.write(f"ETA: **{safe_date_format(t['eta_time'])}**")
            with c3:
                with st.expander("Számla"):
                    st.image(t["photo"], width=80)
                    st.write(f"Összesen: {get_price(t) + 990} Ft")

    # C) ÉLŐ KÖVETÉS
    st.divider()
    st.subheader("🚚 Aktív szállítások")
    tracking = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    
    for tid, t in tracking.items():
        with st.container(border=True):
            st.write(f"**{t.get('item')}** | {t.get('sender')} ➔ {t.get('receiver')}")
            st.info(f"📍 Státusz: {t.get('state_text', 'Folyamatban')}")
            
            eta = t.get("eta_time")
            if eta:
                now = datetime.now()
                # Ha a memóriában stringgé vált a dátum, alakítsuk vissza
                if isinstance(eta, str): eta = datetime.fromisoformat(eta)
                
                remaining = eta - now
                if remaining.total_seconds() > 0:
                    st.write(f"⏳ Érkezésig: **{int(remaining.total_seconds() // 60)}p {int(remaining.total_seconds() % 60)}mp**")
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t.get("receiver"):
                        if st.button("Átvétel igazolása", key=f"rec_{tid}"):
                            t["status"] = "DELIVERED"
                            t["received_at"] = datetime.now()
                            st.rerun()
            else:
                st.warning("Várakozás a feladó indítására...")

# --- 3. HISTORY & 4. BASE ---
with menu[2]:
    st.header("Lezárt folyamatok")
    delivered = {tid: t for tid, t in global_data["active_trades"].items() 
                 if t.get("status") == "DELIVERED" and t.get("sender") == current_user}
    for tid, t in delivered.items():
        if st.button(f"Szatyor visszaérkezett ({t.get('item')})", key=f"hist_{tid}"):
            global_data["trade_history"].append({
                "Idő": datetime.now().strftime("%H:%M"), 
                "Küldő": t.get("sender"), "Vevő": t.get("receiver"), "Tárgy": t.get("item")
            })
            del global_data["active_trades"][tid]
            st.rerun()
    if global_data.get("trade_history"):
        st.table(pd.DataFrame(global_data["trade_history"]))

with menu[3]:
    st.header("Base Hub")
    new_b = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
    if st.button("Feltöltés a közösbe"):
        if new_b:
            global_data["base_gallery"].append({"photo": new_b, "user": current_user, "time": datetime.now().strftime("%H:%M")})
            st.rerun()
    if global_data.get("base_gallery"):
        cols = st.columns(3)
        for idx, entry in enumerate(global_data["base_gallery"][::-1]):
            with cols[idx % 3]:
                st.image(entry["photo"])
                st.caption(f"{entry['user']} | {entry['time']}")

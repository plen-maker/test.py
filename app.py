import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC CONTROL", layout="wide")

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

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név", key="login_name").lower().strip()
    p = st.text_input("PW", type="password", key="login_pw")
    if st.button("Belépés", key="login_btn"):
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
menu = st.tabs(["🚀 TRADE INDÍTÁS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE"])

# --- 1. TRADE INDÍTÁS ---
with menu[0]:
    st.header("Új szállítás")
    if not others_online:
        st.info("Várj partnerre...")
    else:
        target = st.selectbox("Címzett", others_online, key="trade_target")
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "London"], key="trade_start")
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "London"], key="trade_end")
        with c2:
            price_input = st.number_input("Ár (Ft)", min_value=0, value=1000, key="trade_price")
            item_name = st.text_input("Tárgy", key="trade_item_name")
        
        photo = st.file_uploader("Kép", type=['jpg', 'png'], key="trade_photo_up")
        
        if st.button("🚀 Küldés", key="trade_send_btn"):
            if item_name and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item_name,
                    "price": price_input,
                    "status": "WAITING",
                    "state_text": "Csomagolás alatt...",
                    "photo": photo,
                    "start_loc": start,
                    "end_loc": end,
                    "eta_time": None,
                    "start_time": None
                }
                st.success("Elküldve!")
                st.rerun()

# --- 2. CONTROL PANEL ---
with menu[1]:
    # ELFOGADÁS
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t.get("receiver") == current_user and t.get("status") == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> **{t['item']}** ({get_price(t)} Ft)")
            if st.button("ELFOGADOM", key=f"acc_{tid}"):
                global_data["balances"][t["sender"]] -= (get_price(t) + 990)
                t["status"] = "ACCEPTED"
                st.rerun()

    st.divider()

    # FELADÓI VEZÉRLÉS (Itt tudod EDITÁLNI az időt)
    st.subheader("🎮 Futár Kontroll")
    my_controls = {tid: t for tid, t in global_data["active_trades"].items() if t.get("sender") == current_user and t.get("status") == "ACCEPTED"}
    
    for tid, t in my_controls.items():
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** | Cél: {t['receiver']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                new_s = st.selectbox("Státusz", states, index=curr_idx, key=f"sel_{tid}")
                if st.button("Státusz mentése", key=f"upd_{tid}"):
                    t["state_text"] = new_s
                    st.rerun()
            with c2:
                # ITT AZ EDITÁLÁS: Bármikor újraírhatod a perceket
                label = "Perc beállítása:" if t["eta_time"] is None else "Késés/Módosítás (perc):"
                m_edit = st.number_input(label, 1, 120, 5, key=f"edit_min_{tid}")
                if st.button("IDŐ FIXÁLÁSA / FRISSÍTÉSE", key=f"set_time_{tid}"):
                    t["eta_time"] = datetime.now() + timedelta(minutes=m_edit)
                    if t["start_time"] is None: t["start_time"] = datetime.now()
                    st.rerun()
            with c3:
                with st.expander("Számla"):
                    st.image(t["photo"], use_container_width=True)
                    st.write(f"Végösszeg: {get_price(t) + 990} Ft")

    # ÉLŐ KÖVETÉS (VISSZASZÁMLÁLÓ AZ ETA ALATT)
    st.divider()
    st.subheader("📢 Élő Állapot")
    tracking = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    
    for tid, t in tracking.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** ({t['start_loc']} ➔ {t['end_loc']})")
            st.info(f"📍 Státusz: **{t['state_text']}**")
            
            if t.get("eta_time"):
                eta = t["eta_time"]
                if isinstance(eta, str): eta = datetime.fromisoformat(eta)
                rem = (eta - datetime.now()).total_seconds()
                
                # ETA KIÍRÁSA
                st.write(f"🏁 Várható érkezés: **{safe_date_format(eta)}**")
                
                # TIMER AZ ETA ALATT
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"⏳ {m:02d}:{s:02d}")
                    st.progress(min(1.0, 1.0 - (rem / 3600))) # Egyszerűsített csík
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t["receiver"]:
                        if st.button("Átvétel igazolása", key=f"recv_{tid}"):
                            t["status"] = "DONE"
                            st.rerun()
            else:
                st.warning("Várakozás az időzítő indítására...")

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt folyamatok")
    done = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "DONE" and t.get("sender") == current_user}
    for tid, t in done.items():
        if st.button(f"Szatyor OK: {t['item']}", key=f"bag_{tid}"):
            global_data["trade_history"].append({"Idő": datetime.now().strftime("%H:%M"), "Küldő": t["sender"], "Vevő": t["receiver"], "Tárgy": t["item"]})
            del global_data["active_trades"][tid]
            st.rerun()
    if global_data.get("trade_history"):
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- 4. BASE ---
with menu[3]:
    st.header("Base Galéria")
    nb = st.file_uploader("Kép", type=['jpg', 'png'], key="base_up")
    if st.button("Feltöltés", key="base_btn"):
        if nb:
            global_data["base_gallery"].append({"photo": nb, "user": current_user, "time": datetime.now().strftime("%H:%M")})
            st.rerun()
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"{entry['user']} | {entry['time']}")

# AUTO-REFRESH
if any(t.get("eta_time") for t in global_data["active_trades"].values()):
    time.sleep(1)
    st.rerun()

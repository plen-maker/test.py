import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide")

# --- KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000},
        "base_photos": ["https://images.unsplash.com/photo-1590247813693-5541d1c609fd?q=80&w=1000"]
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
st.sidebar.metric("Egyenleg", f"{global_data['balances'][current_user]} Ft")
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

# --- TABS ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "🔔 ÉRTESÍTÉSEK", "📜 HISTORY", "🏠 BASE"])

# --- 1. TRADE INDÍTÁS ---
with menu[0]:
    st.header("Új Szállítás Összeállítása")
    if not others_online:
        st.info("Nincs más online felhasználó.")
    else:
        target = st.selectbox("Címzett", others_online)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "Planeland", "London"])
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "Planeland", "London"])
        with c2:
            item = st.text_input("Tartalom")
            pkg = st.text_input("Csomagolás (Final Package)")
        
        photo = st.file_uploader("Kép feltöltése", type=['jpg', 'png'])
        
        if st.button("Trade kérelem küldése"):
            if item and photo:
                trade_id = f"TID-{int(time.time())}"
                global_data["active_trades"][trade_id] = {
                    "sender": current_user,
                    "receiver": target,
                    "item": item,
                    "pkg": pkg,
                    "start": start,
                    "end": end,
                    "status": "WAITING_ACCEPTANCE",
                    "price": 990,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.success(f"Kérelem elküldve {target} részére!")
            else:
                global_data["balances"][current_user] -= 1500
                st.error("HIBA! Hiányzó adatok. 1500 Ft levonva.")

# --- 2. ÉRTESÍTÉSEK ÉS STATE UPDATE ---
with menu[1]:
    # --- BEJÖVŐ KÉRELMEK ---
    st.subheader("📩 Bejövő kérelmek")
    requests = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user and t["status"] == "WAITING_ACCEPTANCE"}
    
    for tid, t in requests.items():
        st.warning(f"KÉRÉS: {t['sender']} csomagot küldene neked: {t['item']}")
        col_a, col_b = st.columns(2)
        if col_a.button(f"ELFOGADOM ✅", key=f"acc_{tid}"):
            global_data["balances"][t["sender"]] -= 990
            t["status"] = "IN_TRANSIT"
            t["wait_min"] = random.randint(5, 10)
            t["start_time"] = datetime.now()
            t["arrival_time"] = datetime.now() + timedelta(minutes=t["wait_min"])
            st.rerun()
        if col_b.button(f"ELUTASÍTOM ❌", key=f"dec_{tid}"):
            del global_data["active_trades"][tid]
            st.rerun()

    # --- ÉLŐ SZÁLLÍTÁSOK ÉS SZÁMLA ---
    st.divider()
    st.subheader("🚚 Aktív szállítások")
    active = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "IN_TRANSIT" and (t["sender"] == current_user or t["receiver"] == current_user)}
    
    for tid, t in active.items():
        elapsed = (datetime.now() - t["start_time"]).total_seconds()
        total = t["wait_min"] * 60
        progress = min(elapsed / total, 1.0)
        
        # STATE UPDATE LOGIKA
        if progress < 0.2: state = "We received your order"
        elif progress < 0.4: state = "Your order is in the plane"
        elif progress < 0.6: state = "Your order is at the airport"
        elif progress < 0.8: state = "Your order is on its final route"
        else: state = "Your order is at your gate"

        st.info(f"**STATUS:** {state}")
        st.progress(progress)

        # SZÁMLA MEGJELENÍTÉSE
        with st.expander("🧾 Digitális Számla Megtekintése"):
            st.markdown(f"""
            ---
            ### 🧾 TRADE INVOICE - {tid}
            **Feladó:** {t['sender']} | **Címzett:** {t['receiver']}
            **Tárgy:** {t['item']} | **Csomagolás:** {t['pkg']}
            **Útvonal:** {t['start']} ➔ {t['end']}
            **Díj:** {t['price']} Ft | **Dátum:** {t['created_at']}
            **Várható menetidő:** {t['wait_min']} perc
            ---
            """)

        if progress >= 1.0 and t["receiver"] == current_user:
            if st.button(f"Átvétel visszaigazolása ({t['item']})"):
                t["status"] = "DELIVERED"
                t["received_at"] = datetime.now()
                st.rerun()

    # --- SZATYOR VISSZAADÁS ---
    st.divider()
    st.subheader("🔄 Szatyor Visszaigazolás")
    delivered = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "DELIVERED" and t["sender"] == current_user}
    for tid, t in delivered.items():
        deadline = t["received_at"] + timedelta(minutes=10)
        st.write(f"Csomag: {t['item']} | Határidő: {deadline.strftime('%H:%M:%S')}")
        if st.button("Szatyor megérkezett", key=f"bag_{tid}"):
            if datetime.now() > deadline:
                global_data["balances"][t["receiver"]] -= 155
            global_data["trade_history"].append({"Idő": t["created_at"], "Kitől": t["sender"], "Kinek": t["receiver"], "Tárgy": t["item"]})
            del global_data["active_trades"][tid]
            st.rerun()

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt folyamatok")
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- 4. BASE GALÉRIA ---
with menu[3]:
    st.header("Base HQ - Galéria")
    cols = st.columns(3)
    for idx, img in enumerate(global_data["base_photos"]):
        cols[idx % 3].image(img, use_container_width=True)
    
    st.divider()
    new_b = st.file_uploader("Új kép a bázisról", type=['jpg', 'png'])
    if st.button("Feltöltés a galériába"):
        if new_b:
            st.success("Kép rögzítve a közös galériába!")

import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="IRL LOGISTIC HUB PRO", layout="wide")

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
st.sidebar.metric("Saját Egyenleg", f"{global_data['balances'][current_user]} Ft")
others_online = [u for u in global_data["online_users"].keys() if u != current_user]

# --- TABS ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "🔔 AKTÍV FOLYAMATOK", "📜 HISTORY", "🏠 BASE HUB"])

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
            # Itt már nem te adod meg az időt, hanem generálunk egyet
            gen_wait = random.randint(5, 10)
        with c2:
            item_price = st.number_input("Termék ára (Ft)", min_value=0, value=1000)
            item = st.text_input("Tartalom")
            pkg = st.text_input("Csomagolás (Final Package)")
        
        photo = st.file_uploader("Kép feltöltése a termékről", type=['jpg', 'png'])
        
        total_cost = item_price + 990

        if st.button(f"Trade kérelem küldése ({total_cost} Ft)"):
            if item and photo:
                if global_data["balances"][current_user] >= total_cost:
                    trade_id = f"TID-{int(time.time())}"
                    # A várható idő kiszámítása a jelenlegi időhöz adva
                    eta = datetime.now() + timedelta(minutes=gen_wait)
                    
                    global_data["active_trades"][trade_id] = {
                        "sender": current_user,
                        "receiver": target,
                        "item": item,
                        "pkg": pkg,
                        "start": start,
                        "end": end,
                        "status": "WAITING_ACCEPTANCE",
                        "item_price": item_price,
                        "shipping_fee": 990,
                        "total_price": total_cost,
                        "created_at": datetime.now(),
                        "eta_time": eta, # Fix érkezési időpont
                        "photo": photo,
                        "wait_min": gen_wait
                    }
                    st.success(f"Kérelem elküldve! Várható érkezés: {eta.strftime('%H:%M')}")
                else:
                    st.error(f"Nincs elég egyenleged! Szükséges: {total_cost} Ft")
            else:
                global_data["balances"][current_user] -= 1500
                st.error("HIBA! Hiányzó adatok. 1500 Ft büntetés levonva!")
                st.rerun()

# --- 2. ÉRTESÍTÉSEK ÉS ÉLŐ KÖVETÉS ---
with menu[1]:
    # --- BEJÖVŐ KÉRELMEK (Címzettnek) ---
    requests = {tid: t for tid, t in global_data["active_trades"].items() if t["receiver"] == current_user and t["status"] == "WAITING_ACCEPTANCE"}
    if requests:
        st.subheader("📩 Bejövő kérelmek")
        for tid, t in requests.items():
            with st.container(border=True):
                st.warning(f"**{t['sender']}** trade-et küldene!")
                st.write(f"Tárgy: {t['item']} | Érték: {t['total_price']} Ft")
                col_a, col_b = st.columns(2)
                if col_a.button(f"ELFOGADOM ✅", key=f"acc_{tid}"):
                    # LEVONÁS ELFOGADÁSKOR
                    global_data["balances"][t["sender"]] -= t["total_price"]
                    t["status"] = "IN_TRANSIT"
                    t["start_time"] = datetime.now()
                    st.rerun()
                if col_b.button(f"ELUTASÍTOM ❌", key=f"dec_{tid}"):
                    del global_data["active_trades"][tid]
                    st.rerun()

    st.divider()
    st.subheader("🚚 Aktív folyamatok")
    # Most már a feladó és a címzett is látja!
    active = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "IN_TRANSIT" and (t["sender"] == current_user or t["receiver"] == current_user)}
    
    if not active:
        st.write("Nincs folyamatban lévő szállítás.")

    for tid, t in active.items():
        now_dt = datetime.now()
        total_sec = t["wait_min"] * 60
        elapsed_sec = (now_dt - t["start_time"]).total_seconds()
        progress = min(elapsed_sec / total_sec, 1.0)
        
        # State Update szövegek
        if progress < 0.2: state = "We received your order"
        elif progress < 0.4: state = "Your order is in the plane"
        elif progress < 0.6: state = "Your order is at the airport"
        elif progress < 0.8: state = "Your order is on its final route"
        else: state = "Your order is at your gate"

        with st.container(border=True):
            st.write(f"📦 **{t['item']}** ({t['sender']} ➔ {t['receiver']})")
            st.info(f"📍 Státusz: **{state}** | 🕒 Várható érkezés: **{t['eta_time'].strftime('%H:%M')}**")
            st.progress(progress)

            with st.expander("🧾 Digitális Számla megtekintése"):
                c_img, c_txt = st.columns([1, 2])
                with c_img: st.image(t["photo"], use_container_width=True)
                with c_txt:
                    st.markdown(f"""
                    **ID:** `{tid}` | **Dátum:** {t['created_at'].strftime('%Y-%m-%d %H:%M')}
                    ---
                    **Termék ára:** {t['item_price']} Ft  
                    **Szállítás:** {t['shipping_fee']} Ft  
                    **ÖSSZESEN LEVONVA:** **{t['total_price']} Ft**
                    ---
                    **Küldő:** {t['sender']} | **Címzett:** {t['receiver']}
                    **Várható érkezés:** {t['eta_time'].strftime('%H:%M')}
                    """)

            if progress >= 1.0 and t["receiver"] == current_user:
                if st.button(f"Átvétel visszaigazolása", key=f"done_{tid}"):
                    t["status"] = "DELIVERED"
                    t["received_at"] = datetime.now()
                    st.rerun()

    # Szatyor visszajelzés (Küldő igazolja vissza)
    delivered = {tid: t for tid, t in global_data["active_trades"].items() if t["status"] == "DELIVERED" and t["sender"] == current_user}
    for tid, t in delivered.items():
        deadline = t["received_at"] + timedelta(minutes=10)
        st.warning(f"Csomag megérkezett {t['receiver']} részére! Visszakaptad a szatyrot?")
        if st.button(f"Szatyor megérkezett ✅", key=f"bag_{tid}"):
            if datetime.now() > deadline:
                global_data["balances"][t["receiver"]] -= 155
            global_data["trade_history"].append({
                "Idő": t["created_at"].strftime('%H:%M'), 
                "Kitől": t["sender"], 
                "Kinek": t["receiver"], 
                "Tárgy": t["item"], 
                "Összeg": t["total_price"]
            })
            del global_data["active_trades"][tid]
            st.rerun()

# --- 3. HISTORY ---
with menu[2]:
    st.header("Lezárt Trade-ek")
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))
    else:
        st.write("Még nem történt lezárt tranzakció.")

# --- 4. BASE HUB ---
with menu[3]:
    st.header("Base HQ Galéria")
    new_b = st.file_uploader("Kép feltöltése a bázisról", type=['jpg', 'png'])
    if st.button("Feltöltés a közösbe"):
        if new_b:
            global_data["base_gallery"].append({
                "photo": new_b, 
                "user": current_user, 
                "time": datetime.now().strftime("%H:%M")
            })
            st.success("Kép feltöltve!")
            st.rerun()
    
    st.divider()
    if global_data["base_gallery"]:
        cols = st.columns(3)
        for idx, entry in enumerate(global_data["base_gallery"][::-1]):
            with cols[idx % 3]:
                st.image(entry["photo"])
                st.caption(f"👤 {entry['user'].capitalize()} | 🕒 {entry['time']}")

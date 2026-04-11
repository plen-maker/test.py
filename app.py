import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. A VÉGLEGES TISZTÍTÓ CSS ---
st.set_page_config(page_title="Cattrade Logistic", layout="wide", page_icon="🚚")

st.markdown("""
    <style>
    /* 1. Teljes fejléc, toolbar és a fekete sáv (Cattrade) teljes megsemmisítése */
    header, [data-testid="stHeader"], .stAppToolbar, .st-emotion-cache-18ni7ap, .st-emotion-cache-1h6d29n {
        display: none !important;
        height: 0 !important;
        visibility: hidden !important;
    }
    
    /* 2. Az alsó Streamlit logó és 'Hosted with' sáv eltüntetése */
    footer, .st-emotion-cache-1kyx9g0, .st-emotion-cache-6q9sum {
        display: none !important;
        visibility: hidden !important;
    }

    /* 3. A tartalom felhúzása a legtetejére */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -3rem !important;
    }

    /* 4. A macskás kép és egyéb úszó elemek blokkolása */
    img {
        max-width: 100%;
    }
    
    /* Ne lehessen oldalra rángatni a képernyőt mobilban */
    html, body {
        overflow-x: hidden;
        position: fixed;
        width: 100%;
        height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADATOK ÉS LOGIN (Ugyanaz, mint eddig, de tiszta placeholderrel) ---
@st.cache_resource
def get_global_data():
    return {"online_users": {}, "active_trades": {}, "balances": {"admin": 50000, "peti": 50000, "adel": 50000}}

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

login_placeholder = st.empty()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with login_placeholder.container():
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🛡️ IRL LOGISTIC - LOGIN</h2>", unsafe_allow_html=True)
        u = st.text_input("Felhasználónév", key="l_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="l_p")
        if st.button("BELÉPÉS", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state.authenticated = True
                st.session_state.username = u
                login_placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

# --- 3. AZ APP TARTALMA (Csak belépés után) ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Oldalsáv
st.sidebar.title(f"Szia, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Aktív: {', '.join(online_now)}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# Főmenü fülek
tabs = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL", "📜 HISTORY"])

with tabs[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "London", "Catania", "New York"])
        end = c1.selectbox("Cél", ["Budapest HUB", "London", "Catania", "New York"])
        item = c2.text_input("Termék")
        price = c2.number_input("Ár (Ft)", min_value=0, value=1000)
        
        if st.button("🚀 CSOMAG INDÍTÁSA", use_container_width=True) and item:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item,
                "price": price, "status": "WAITING", "state_text": "Csomagolás...",
                "start_loc": start, "end_loc": end
            }
            st.success("Sikeres feladás!")
            st.rerun()

with tabs[1]:
    # Bejövő csomagok
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> {t['item']} ({t['price']+990} Ft)")
            if st.button(f"ELFOGADOM", key=f"acc_{tid}", use_container_width=True):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    st.rerun()

# Automatikus frissítés 3 másodpercenként
time.sleep(3)
st.rerun()

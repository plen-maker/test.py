import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. A MINDENT ELTÜNTETŐ CSS ---
st.set_page_config(page_title="Cattrade Logistic", layout="wide", page_icon="🚚")

st.markdown("""
    <style>
    /* 1. Teljes fejléc és menü elrejtése */
    header, [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 2. Streamlit logó és lábléc (Hosted with Streamlit) elrejtése */
    footer {
        visibility: hidden !important;
    }
    
    /* 3. A legfelső fekete sáv (Cattrade + csillag) teljes eltüntetése */
    div.st-emotion-cache-18ni7ap, div.st-emotion-cache-1h6d29n {
        display: none !important;
    }

    /* 4. Az egész tartalom feljebb tolása a fejléc helyére */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -2rem !important;
    }

    /* 5. A jobb felső "Fork / Github" gombok végleges törlése */
    .stAppToolbar {
        display: none !important;
    }
    
    /* Mobil optimalizálás: ne lehessen vízszintesen rángatni a képernyőt */
    html, body {
        overflow-x: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GLOBÁLIS ADATKEZELÉS ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. LOGIN RENDSZER ---
# Itt is használunk egy 'empty' tárolót, hogy bejelentkezés után ne maradjon nyoma a loginnek
login_placeholder = st.empty()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with login_placeholder.container():
        st.markdown("<h1 style='text-align: center;'>🛡️ IRL LOGISTIC - LOGIN</h1>", unsafe_allow_html=True)
        u = st.text_input("Felhasználónév", key="login_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="login_p")
        if st.button("BELÉPÉS", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state.authenticated = True
                st.session_state.username = u
                login_placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

# --- 4. SZÁMLA PDF FUNKCIÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20); c.drawString(50, 800, "HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 12); c.drawString(50, 770, f"ID: {tid}")
    c.drawString(50, 750, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 725, f"Termék: {t['item']} | Útvonal: {t['start_loc']} -> {t['end_loc']}")
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.red)
    c.drawString(50, 680, f"VÉGÖSSZEG: {t['price'] + 990} Ft")
    c.save(); buf.seek(0)
    return buf

# --- 5. AZ APP BELSŐ FELÜLETE ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Sidebar - Csak a legszükségesebbek
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Aktív: {', '.join(online_now)}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# FŐOLDALI TABS
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
                "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            st.success("Sikeres feladás!"); st.rerun()

with tabs[1]:
    # Bejövő kérések
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
                else:
                    st.error("Nincs elég pénzed!")

    st.divider()
    # Futó szállítások
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | Állapot: {t['state_text']}")
            if t["sender"] == current_user:
                states = ["Csomagolás...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "Megérkezett! ✅"]
                new_s = st.selectbox("Státusz állítása", states, key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s; st.rerun()
            
            pdf = create_pdf(t, tid)
            st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

# FRISSÍTÉS
time.sleep(3)
st.rerun()

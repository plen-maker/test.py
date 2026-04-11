import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. TELJES REKLÁM ÉS SÁV ELTÜNTETÉS (CSS) ---
st.set_page_config(page_title="Cattrade LOGISTIC", layout="wide", page_icon="🚚")

st.markdown("""
    <style>
    /* Elrejti a Streamlit menüt, a láblécet és a fejlécet */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Elrejti a felső fekete PWA sávot és a csillagot */
    div.st-emotion-cache-18ni7ap {visibility: hidden; height: 0;}
    div.st-emotion-cache-1h6d29n {visibility: hidden; height: 0;}
    [data-testid="stHeader"] {display: none;}

    /* Teljes szélességű tartalom, sávok nélkül */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    /* APK nézet optimalizálás: ne lehessen vízszintesen görgetni */
    html, body {
        overflow-x: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KÖZÖS ADATOK (MEMÓRIA) ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. LOGIN RENDSZER (ÜRES TÁROLÓVAL A TISZTA TÖRLÉSHEZ) ---
login_placeholder = st.empty()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with login_placeholder.container():
        st.title("🛡️ IRL LOGISTIC - LOGIN")
        u = st.text_input("Felhasználónév", key="l_user").lower().strip()
        p = st.text_input("Jelszó", type="password", key="l_pass")
        if st.button("Belépés", key="l_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.authenticated = True
                st.session_state.username = u
                login_placeholder.empty() # Fizikailag kitörli a login mezőket
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

# --- 4. SZÁMLA PDF GENERÁTOR ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Tranzakció ID: {tid}")
    c.drawString(50, 750, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 730, f"Termék: {t['item']}")
    c.drawString(50, 710, f"Összeg: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 5. AZ APP FELÜLETE (BEJELENTKEZÉS UTÁN) ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# SIDEBAR (Oldalsáv)
st.sidebar.title(f"Szia, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

# FŐ TARTALOM (TABS)
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: 
        st.info("Nincs online partner jelenleg.")
    else:
        target = st.selectbox("Válassz címzettet", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulási pont", ["Budapest HUB", "London", "New York", "Catania"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "London", "New York", "Catania"])
        price = c2.number_input("Termék ára (Ft)", min_value=0, value=1000)
        item = c2.text_input("Mi van a csomagban?")
        
        if st.button("🚀 KÜLDÉS INDÍTÁSA"):
            if item:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item,
                    "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "start_loc": start, "end_loc": end,
                    "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success("Csomag regisztrálva!"); st.rerun()

with menu[1]:
    # Bejövő kérések (amire várjuk az elfogadást)
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** küldött neked valamit: **{t['item']}**")
            if st.button(f"ELFOGADOM ÉS FIZETEK ({t['price']+990} Ft)", key=f"acc_{tid}"):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.rerun()
                else:
                    st.error("Nincs elég egyenleged!")

    st.divider()
    # Aktív folyamatok (szállítás alatt)
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            
            # Csak a küldő tud státuszt állítani
            if t["sender"] == current_user:
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "Megérkezett! ✅"]
                new_s = st.selectbox("Helyzet frissítése", states, key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s; st.rerun()
            else:
                st.info(f"📍 Jelenlegi állapot: {t['state_text']}")
            
            # Számla letöltés
            pdf_file = create_pdf(t, tid)
            st.download_button("📥 SZÁMLA (PDF)", data=pdf_file, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

# AUTOMATIKUS OLDALFRISSÍTÉS 3 MÁSODPERCENKÉNT
time.sleep(3)
st.rerun()

import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. BRUTÁLISAN ERŐS TISZTÍTÁS (APK BARÁT) ---
st.set_page_config(page_title="Cattrade LOGISTIC", layout="wide", page_icon="🚚")

st.markdown("""
    <style>
    /* Elrejti a Streamlit minden elemét, még az APK-ban is */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {display: none !important;}
    
    /* Elrejti a felső fekete PWA/Cattrade sávot */
    [data-testid="stHeader"] {display: none !important;}
    .stAppHeader {display: none !important;}
    
    /* Ez tünteti el a "Cattrade" feliratot és a csillagot felül */
    div[class*="st-emotion-cache-18ni7ap"], 
    div[class*="st-emotion-cache-1h6d29n"] {
        display: none !important;
        height: 0 !important;
    }

    /* A tartalom teljesen csússzon fel a tetejére */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -50px !important; /* Feljebb tolja, hogy ne maradjon üres hely */
    }

    /* Az oldalsáv (sidebar) tetejét is kitakarítjuk */
    [data-testid="stSidebarNav"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. KÖZÖS ADATOK ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. LOGIN RENDSZER (placeholder-rel) ---
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
                login_placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

# --- 4. SZÁMLA PDF ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"ID: {tid}")
    c.drawString(50, 750, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 710, f"Összeg: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 5. AZ APP FELÜLETE ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# SIDEBAR
st.sidebar.title(f"Szia, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

# FŐ MENÜ
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: 
        st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "London", "Catania"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "London", "Catania"])
        price = c2.number_input("Ár (Ft)", min_value=0, value=1000)
        item = c2.text_input("Termék")
        if st.button("🚀 KÜLDÉS"):
            if item:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item,
                    "price": price, "status": "WAITING", "state_text": "Csomagolás...",
                    "start_loc": start, "end_loc": end,
                    "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success("Küldve!"); st.rerun()

with menu[1]:
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 {t['sender']} -> {t['item']}")
            if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"acc_{tid}"):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            if t["sender"] == current_user:
                new_s = st.selectbox("Státusz", ["Úton", "Reptéren", "Megérkezett"], key=f"s_{tid}")
                t["state_text"] = new_s
            else:
                st.info(f"Helyzet: {t['state_text']}")
            
            pdf = create_pdf(t, tid)
            st.download_button("📥 PDF", data=pdf, file_name=f"{tid}.pdf", key=f"p_{tid}")

time.sleep(3); st.rerun()

import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from streamlit_drawable_canvas import st_canvas

# --- 1. MINDENT ELTÜNTETŐ CSS (REKLÁMMENTESÍTÉS) ---
st.set_page_config(page_title="Tréd🔥🔥🔥", layout="wide", page_icon="🚚")

st.markdown("""
    <style>
    /* Streamlit fejlécek és láblécek végleges törlése */
    header, footer, [data-testid="stHeader"], .stAppToolbar, .st-emotion-cache-18ni7ap, .st-emotion-cache-1h6d29n {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Tartalom felhúzása */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -3rem !important;
    }

    /* NFC Animáció stílus */
    .nfc-animation {
        width: 100px;
        height: 100px;
        background: url('https://cdn-icons-png.flaticon.com/512/548/548427.png') no-repeat center;
        background-size: contain;
        margin: 20px auto;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.7; }
        70% { transform: scale(1); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HANG ÉS ÉRTESÍTÉS ---
def play_cat_meow(text):
    meow_html = f"""
        <audio autoplay><source src="https://www.myinstants.com/media/sounds/meow-sound-effect1.mp3" type="audio/mpeg"></audio>
        <div style="padding:15px; border-radius:10px; background-color:#ff4b4b; color:white; border: 2px solid white; margin-bottom:10px; animation: bounce 0.5s;">
            🐱 <b>NYÁU!</b> {text}
        </div>
    """
    st.markdown(meow_html, unsafe_allow_html=True)

# --- 3. MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000, "ddnemet": 50000, "kormuranusz": 50000},
        "notifications": {}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99", "kormuranusz": "kormicica", "ddnemet": "koficcica"}

# --- 4. SZÁMLA PDF (ORDER NUMBER) ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, f"ORDER: {tid.replace('TID-', '#')}")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 750, f"Termék: {t['item']} | Ár: {t['price']+990} Cam")
    if t.get("signed"):
        c.drawString(50, 700, "ALÁÍRVA / SIGNED ✅")
    c.save(); buf.seek(0)
    return buf

# --- LOGIN ---
placeholder = st.empty()
if 'username' not in st.session_state:
    with placeholder.container():
        st.title("🛡️ IRL LOGISTIC LOGIN")
        u = st.text_input("Felhasználónév").lower().strip()
        p = st.text_input("Jelszó", type="password")
        if st.button("Belépés"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                placeholder.empty()
                st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]

# Értesítések
if current_user in global_data["notifications"]:
    for msg in global_data["notifications"][current_user]:
        play_cat_meow(msg)
    global_data["notifications"][current_user] = []

# APP TABS
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "🏦 CAT-BANK (NFC)"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        price = st.number_input("Ár (Cam)", min_value=0, value=1000)
        item = st.text_input("Termék neve")
        if st.button("🚀 KÜLDÉS"):
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item,
                "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            if target not in global_data["notifications"]: global_data["notifications"][target] = []
            global_data["notifications"][target].append(f"{current_user} küldött egy ajánlatot: {item}!")
            st.success("Küldve!"); st.rerun()

with menu[1]:
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** ajánlata: **{t['item']}**")
            if st.button(f"Fizetés (Contactless NFC) - {t['price']+990} Cam", key=f"pay_{tid}"):
                st.session_state[f"pay_active_{tid}"] = True
            
            if st.session_state.get(f"pay_active_{tid}"):
                st.markdown('<div class="nfc-animation"></div>', unsafe_allow_html=True)
                st.write("Tartsd a telefonod a terminálhoz (Vagy kattints a megerősítésre)...")
                if st.button("Fizetés jóváhagyása", key=f"confirm_{tid}"):
                    cost = t["price"] + 990
                    if global_data["balances"][current_user] >= cost:
                        global_data["balances"][current_user] -= cost
                        global_data["balances"][t["sender"]] += (t["price"] + 495)
                        t["status"] = "ACCEPTED"
                        st.success("Sikeres NFC fizetés!"); time.sleep(1); st.rerun()
                    else: st.error("Nincs elég egyenleg!")

    st.divider()
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            order_num = tid.replace("TID-", "#")
            st.write(f"🚚 **{order_num}**: {t['item']} | {t['state_text']}")
            
            if t["sender"] == current_user:
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                new_s = st.selectbox("Státusz", states, index=states.index(t["state_text"]) if t["state_text"] in states else 0, key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s
                    if t['receiver'] not in global_data["notifications"]: global_data["notifications"][t['receiver']] = []
                    global_data["notifications"][t['receiver']].append(f"A(z) {order_num} csomagodat: {new_s}")
                    st.rerun()

                if t["state_text"] == "A kapu előtt 🚪":
                    st.warning("Aláírás szükséges!")
                    st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=100, key=f"c_{tid}")
                    if st.button("Aláírás mentése és Átadás", key=f"done_{tid}"):
                        t["status"] = "DONE"; t["signed"] = True; st.rerun()
            else:
                rem = (t["eta_time"] - datetime.now()).total_seconds()
                if rem <= 0: st.success("✅ MEGÉRKEZETT!")
                else: st.write(f"⏳ ETA: {int(rem//60)}p {int(rem%60)}mp")

with menu[2]:
    st.title("🏦 Cat-Bank Revolut")
    st.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Cam")
    st.button("💳 Kártya adatok")
    st.button("📱 NFC Beállítása")

time.sleep(3); st.rerun()

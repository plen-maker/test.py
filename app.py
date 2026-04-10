import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. KONFIGURÁCIÓ ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

# --- 2. ADATBÁZIS ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000}
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 3. SZÁMLA PDF ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"ID: {tid}")
    c.drawString(50, 750, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 730, f"Termék: {t['item']}")
    c.drawString(50, 700, f"Összeg: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 4. LOGIN RENDSZER (placeholder-rel a tiszta törlésért) ---
login_space = st.empty()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with login_space.container():
        st.title("🛡️ IRL LOGISTIC - LOGIN")
        u = st.text_input("Felhasználónév", key="main_user_in").lower().strip()
        p = st.text_input("Jelszó", type="password", key="main_pass_in")
        if st.button("Belépés", key="main_login_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.authenticated = True
                st.session_state.username = u
                login_space.empty() # FIZIKAILAG TÖRÖL MINDENT A LOGINBÓL
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop() # Megállítja a futást, a lenti kód el sem indul belépés nélkül

# --- 5. AZ APP (Csak sikeres login után) ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# SIDEBAR
st.sidebar.title(f"Szia, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

if st.sidebar.button("Kijelentkezés"):
    del st.session_state.authenticated
    del st.session_state.username
    st.rerun()

# FUNKCIÓK
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "London", "New York"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "London", "New York"])
        price = c2.number_input("Ár (Ft)", min_value=0, value=1000)
        item = c2.text_input("Termék neve")
        if st.button("🚀 KÜLDÉS"):
            if item:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item,
                    "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "start_loc": start, "end_loc": end,
                    "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success("Küldve!"); st.rerun()

with menu[1]:
    # Bejövő és folyamatban lévő trade-ek
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> {t['item']}")
            if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"acc_{tid}"):
                cost = t["price"] + 990
                if global_data["balances"][current_user] >= cost:
                    global_data["balances"][current_user] -= cost
                    global_data["balances"][t["sender"]] += (t["price"] + 495)
                    t["status"] = "ACCEPTED"
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.rerun()

    st.divider()
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            if t["sender"] == current_user:
                states = ["Csomagolás alatt...", "Úton...", "A levegőben ✈️", "Kiszállítás alatt"]
                new_s = st.selectbox("Státusz", states, key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s; st.rerun()
            else:
                st.info(f"📍 Helyzet: {t['state_text']}")
            
            pdf = create_pdf(t, tid)
            st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

# AUTO REFRESH
time.sleep(3); st.rerun()

import streamlit as st
import time
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- HANGJELZÉS FUNKCIÓ ---
def play_notification_sound():
    audio_url = "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Samples/master/notification.mp3"
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{audio_url}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 100000, "peti": 50000, "adel": 50000},
        "trade_history": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- ESEMÉNY FIGYELŐ (Hangokhoz) ---
if 'prev_states' not in st.session_state:
    st.session_state.prev_states = {}

# --- PDF SZÁMLA GENERÁLÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "SZÁMLA / INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 75, f"Tranzakció ID: {tid}")
    c.drawString(50, height - 90, f"Dátum: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 100, width - 50, height - 100)
    
    y = height - 130
    c.drawString(50, y, f"Feladó: {t['sender'].capitalize()} | Címzett: {t['receiver'].capitalize()}")
    y -= 20
    c.drawString(50, y, f"Útvonal: {t['start_loc']} -> {t['end_loc']}")
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Termék: {t['item']}")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Leírás: {t.get('description', '-')}")
    y -= 40
    c.drawString(50, y, f"Termék ára: {t['price']} Ft")
    y -= 15
    c.drawString(50, y, f"Szállítási költség: 990 Ft")
    y -= 30
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.red)
    c.drawString(50, y, f"ÖSSZESEN FIZETVE: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név").lower().strip()
    p = st.text_input("Jelszó", type="password")
    if st.button("Belépés") and u in USERS and USERS[u] == p:
        st.session_state.username = u
        st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- HANG LOGIKA ---
for tid, t in global_data["active_trades"].items():
    if current_user in [t['sender'], t['receiver']]:
        state_key = f"{tid}_{t['status']}_{t['state_text']}"
        if tid in st.session_state.prev_states:
            if st.session_state.prev_states[tid] != state_key:
                play_notification_sound()
                st.toast(f"🔔 Frissítés: {t['item']} -> {t['state_text']}")
        st.session_state.prev_states[tid] = state_key

# --- UI ---
st.sidebar.title(f"Futár: {current_user.capitalize()}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

# --- KÜLDÉS ---
with menu[0]:
    targets = [u for u, last in global_data["online_users"].items() if u != current_user and time.time() - last < 10]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Budapest", "Catánia", "London", "New York"])
            end = st.selectbox("Cél", ["Budapest", "Catánia", "London", "New York"])
        with c2:
            price = st.number_input("Ár (Ft)", min_value=0, value=1000)
            item = st.text_input("Termék neve")
        desc = st.text_area("Leírás")
        photo = st.file_uploader("Kép", type=['jpg', 'png'])
        
        if st.button("🚀 KÜLDÉS") and item and photo:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item, "description": desc,
                "price": price, "status": "WAITING", "state_text": "Várakozás elfogadásra...",
                "photo": photo, "start_loc": start, "end_loc": end
            }
            play_notification_sound()
            st.success("Elküldve!")
            st.rerun()

# --- CONTROL PANEL ---
with menu[1]:
    # Bejövő elfogadás
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.image(t["photo"], width=200)
            st.write(f"**{t['sender']}** küldené: **{t['item']}**")
            if st.button(f"ELFOGADOM ÉS FIZETEK ({t['price']+990} Ft)", key=f"a_{tid}"):
                total = t['price'] + 990
                if global_data["balances"][current_user] >= total:
                    global_data["balances"][current_user] -= total
                    global_data["balances"][t['sender']] += (t['price'] + 495)
                    t["status"] = "ACCEPTED"
                    t["state_text"] = "Csomagolás alatt..."
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    play_notification_sound()
                    st.rerun()
                else: st.error("Nincs elég pénzed!")

    st.divider()

    # Aktív szállítások és VÁLASZTHATÓ STATE-EK
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            
            if t['sender'] == current_user:
                # ITT VANNAK A VÁLASZTHATÓ STATE-EK
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                current_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                new_state = st.selectbox("Státusz frissítése", states, index=current_idx, key=f"s_{tid}")
                if new_state != t["state_text"]:
                    t["state_text"] = new_state
                    st.rerun()
            else:
                st.info(f"📍 Aktuális állapot: **{t['state_text']}**")
                if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"d_{tid}"):
                    t["status"] = "DONE"
                    st.rerun()

            with st.expander("Számla"):
                pdf = create_pdf(t, tid)
                st.download_button("📥 PDF Letöltése", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

# --- HISTORY ---
with menu[2]:
    done = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]
    if done: st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])

# AUTO-REFRESH
time.sleep(3)
st.rerun()

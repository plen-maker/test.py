import streamlit as st
import time
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ÉS STÍLUS ---
st.set_page_config(page_title="IRL LOGISTIC PRO", layout="wide", page_icon="🚚")

# Ezzel a kis kóddal elérjük, hogy az oldal 5 másodpercenként frissüljön anélkül, hogy lefagyna
# Megjegyzés: Streamlit Cloud-on ez a legstabilabb módja a frissítésnek
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

# --- 2. KÖZÖS MEMÓRIA ---
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

# --- HANGJELZÉS FUNKCIÓ ---
def play_notification_sound():
    audio_url = "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Samples/master/notification.mp3"
    audio_html = f'<audio autoplay style="display:none;"><source src="{audio_url}" type="audio/mp3"></audio>'
    st.components.v1.html(audio_html, height=0)

# --- PDF SZÁMLA ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "SZAMLA / INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(50, 775, f"Tranzakcio ID: {tid}")
    c.line(50, 765, 550, 765)
    c.drawString(50, 740, f"Felado: {t['sender']} | Cimzett: {t['receiver']}")
    c.drawString(50, 720, f"Utvonal: {t['start_loc']} -> {t['end_loc']}")
    c.drawString(50, 690, f"Termek: {t['item']}")
    c.drawString(50, 670, f"Leiras: {t.get('description', '-')}")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(50, 630, f"OSSZESEN: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 3. LOGIN ---
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

# --- 4. HANG ÉS ÁLLAPOT FIGYELÉS ---
if 'prev_states' not in st.session_state:
    st.session_state.prev_states = {}

for tid, t in global_data["active_trades"].items():
    if current_user in [t['sender'], t['receiver']]:
        state_key = f"{tid}_{t['status']}_{t['state_text']}"
        if tid in st.session_state.prev_states and st.session_state.prev_states[tid] != state_key:
            play_notification_sound()
        st.session_state.prev_states[tid] = state_key

# --- 5. UI ---
st.sidebar.title(f"Futár: {current_user.capitalize()}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

# AUTO-REFRESH GOMB (Ha nem akarsz várni)
if st.sidebar.button("Kézi frissítés"):
    st.rerun()

menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

# --- KÜLDÉS TAB ---
with menu[0]:
    targets = [u for u, last in global_data["online_users"].items() if u != current_user and time.time() - last < 20]
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
                "price": price, "status": "WAITING", "state_text": "Várakozás...",
                "photo": photo, "start_loc": start, "end_loc": end
            }
            play_notification_sound()
            st.rerun()

# --- CONTROL PANEL TAB ---
with menu[1]:
    # Bejövő trade-ek
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** küldeménye:")
            st.image(t["photo"], width=150)
            if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"a_{tid}"):
                if global_data["balances"][current_user] >= (t['price'] + 990):
                    global_data["balances"][current_user] -= (t['price'] + 990)
                    global_data["balances"][t['sender']] += (t['price'] + 495)
                    t["status"] = "ACCEPTED"
                    t["state_text"] = "Csomagolás alatt..."
                    play_notification_sound()
                    st.rerun()

    st.divider()

    # Aktív szállítások + VÁLASZTHATÓ STATE-EK
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            
            if t['sender'] == current_user:
                # ITT A VÁLASZTHATÓ STATE-EK
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                try: curr_idx = states.index(t["state_text"])
                except: curr_idx = 0
                
                new_state = st.selectbox("Válassz új állapotot:", states, index=curr_idx, key=f"sel_{tid}")
                if new_state != t["state_text"]:
                    t["state_text"] = new_state
                    # Itt nem hívunk rerun-t azonnal, csak ha a felhasználó vált
                    st.rerun()
            else:
                st.info(f"📍 Aktuális állapot: **{t['state_text']}**")
                if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"d_{tid}"):
                    t["status"] = "DONE"
                    st.rerun()

            with st.expander("Számla"):
                pdf = create_pdf(t, tid)
                st.download_button("📥 PDF", data=pdf, file_name=f"invoice.pdf", key=f"p_{tid}")

# --- HISTORY TAB ---
with menu[2]:
    done = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]
    if done: st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])

# --- 6. AZ INTELLIGENS FRISSÍTÉS ---
# Nem használunk time.sleep-et és rerun-t a kód végén, mert az okozza a végtelen pörgést.
# Ehelyett egy rejtett HTML elemet használunk, ami 10 másodpercenként frissít.
st.components.v1.html(
    """
    <script>
    window.parent.document.querySelectorAll('[data-testid="stSidebar"]')[0].style.display = 'block';
    // 10 másodpercenként frissítjük az oldalt, ha nincs épp interakció
    setTimeout(function(){
        window.parent.location.reload();
    }, 10000); 
    </script>
    """,
    height=0,
)

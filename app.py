import streamlit as st
import time
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC PRO", layout="wide", page_icon="📦")

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

# --- HANG FUNKCIÓ ---
def play_notification_sound():
    audio_url = "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Samples/master/notification.mp3"
    st.components.v1.html(f'<audio autoplay style="display:none;"><source src="{audio_url}" type="audio/mp3"></audio>', height=0)

# --- PDF GENERÁLÁS ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "SZAMLA / INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(50, 775, f"ID: {tid} | Datum: {t.get('accepted_at', '-')}")
    c.line(50, 765, 550, 765)
    c.drawString(50, 740, f"Kuldo: {t['sender']} -> Vevo: {t['receiver']}")
    c.drawString(50, 710, f"Termek: {t['item']}")
    c.drawString(50, 690, f"Leiras: {t.get('description', '-')}")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(50, 650, f"OSSZESEN: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 3. LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGISTIC LOGIN")
    u = st.text_input("Nev").lower().strip()
    p = st.text_input("Jelszo", type="password")
    if st.button("Belepes") and u in USERS and USERS[u] == p:
        st.session_state.username = u
        st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- 4. HANG ÉS ÁLLAPOT FIGYELŐ ---
if 'prev_states' not in st.session_state:
    st.session_state.prev_states = {}

# --- 5. SIDEBAR ---
st.sidebar.title(f"Futár: {current_user.capitalize()}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
online_list = [u for u, last in global_data["online_users"].items() if time.time() - last < 15]
st.sidebar.write(f"🟢 Online: {', '.join(online_list)}")

# --- 6. FUNKCIÓK (FRAGMENT - CSAK EZT FRISSÍTJÜK) ---

# Új trade beküldése
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

with menu[0]:
    targets = [u for u in online_list if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        with st.form("send_form", clear_on_submit=True):
            target = st.selectbox("Cimzett", targets)
            c1, c2 = st.columns(2)
            start = c1.selectbox("Indulas", ["Budapest", "Catania", "London", "New York"])
            end = c2.selectbox("Cel", ["Budapest", "Catania", "London", "New York"])
            price = st.number_input("Ar (Ft)", min_value=0, value=1000)
            item = st.text_input("Termek neve")
            desc = st.text_area("Leiras")
            photo = st.file_uploader("Kep", type=['jpg', 'png'])
            submit = st.form_submit_button("🚀 KÜLDÉS")
            
            if submit and item and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item, "description": desc,
                    "price": price, "status": "WAITING", "state_text": "Varakozas...",
                    "photo": photo, "start_loc": start, "end_loc": end
                }
                play_notification_sound()
                st.success("Elküldve!")

# Ez a rész automatikusan frissül 3 másodpercenként a háttérben
@st.fragment(run_every=3)
def control_panel_fragment():
    st.subheader("Aktív folyamatok")
    
    # 1. Bejövő kérelmek
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** küldeménye: {t['item']}")
            if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"acc_{tid}"):
                if global_data["balances"][current_user] >= (t['price'] + 990):
                    global_data["balances"][current_user] -= (t['price'] + 990)
                    global_data["balances"][t['sender']] += (t['price'] + 495)
                    t["status"] = "ACCEPTED"
                    t["state_text"] = "Csomagolás alatt..."
                    t["accepted_at"] = datetime.now().strftime("%H:%M")
                    play_notification_sound()
                    st.rerun()

    # 2. Folyamatban lévő trade-ek
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        # Hangjelzés figyelés a fragmenten belül
        state_key = f"{tid}_{t['status']}_{t['state_text']}"
        if tid in st.session_state.prev_states and st.session_state.prev_states[tid] != state_key:
            play_notification_sound()
        st.session_state.prev_states[tid] = state_key

        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            
            if t['sender'] == current_user:
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                new_state = st.selectbox(f"Állapot ({t['item']})", states, index=curr_idx, key=f"sel_{tid}")
                if new_state != t["state_text"]:
                    t["state_text"] = new_state
                    st.rerun()
            else:
                st.info(f"📍 Helyzet: **{t['state_text']}**")
                if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"done_{tid}"):
                    t["status"] = "DONE"
                    st.rerun()
            
            with st.expander("Számla"):
                pdf = create_pdf(t, tid)
                st.download_button("📥 PDF Letöltése", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"pdf_{tid}")

with menu[1]:
    control_panel_fragment()

with menu[2]:
    done = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]
    if done: st.table(pd.DataFrame(done)[["sender", "receiver", "item", "price"]])
    else: st.write("Nincs még lezárt szállítás.")

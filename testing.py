import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from streamlit_drawable_canvas import st_canvas # PIP INSTALL SZÜKSÉGES: streamlit-drawable-canvas

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="Tréd🔥🔥🔥", layout="wide", page_icon="🚚")

# --- 2. HANG ÉS ÉRTESÍTÉS FUNKCIÓ ---
def play_cat_meow(text):
    # Ez a kód egy láthatatlan audio elemet szúr be, ami nyávog és kiírja az üzenetet
    meow_html = f"""
        <audio autoplay><source src="https://www.myinstants.com/media/sounds/meow-sound-effect1.mp3" type="audio/mpeg"></audio>
        <div style="padding:10px; border-radius:10px; background-color:#ff4b4b; color:white; margin-bottom:10px;">
            🐱 <b>Értesítés:</b> {text}
        </div>
    """
    st.markdown(meow_html, unsafe_allow_html=True)

# --- 3. KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000, "ddnemet": 50000, "kormuranusz": 50000},
        "notifications": {} # Felhasználónkénti értesítések
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99", "kormuranusz": "kormicica", "ddnemet": "koficcica"}

# --- 4. PROFI SZÁMLA GENERÁLÓ (ORDER NUMBER-REL) ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 50, "HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"ORDER NUMBER: {tid.replace('TID-', '#')}") # Order number formátum
    c.drawString(50, height - 100, f"Dátum: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 110, width - 50, height - 110)
    
    y = height - 140
    c.drawString(50, y, f"Feladó: {t['sender']}")
    y -= 20; c.drawString(50, y, f"Címzett: {t['receiver']}")
    y -= 20; c.drawString(50, y, f"Termék: {t['item']}")
    y -= 40; c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"FIZETVE: {t['price'] + 990} Cam")
    
    if "signature" in t: # Ha van aláírás, rátesszük a PDF-re
        c.drawString(50, y-100, "Aláírás:")
        # Itt elméletileg beilleszthető a kép, de egyszerűség kedvéért szöveggel jelöljük
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, y-120, "Digitálisan aláírva a helyszínen.")
        
    c.save(); buf.seek(0)
    return buf

# --- LOGIN KEZELÉS (MARAD AZ EREDETI) ---
placeholder = st.empty()
if 'username' not in st.session_state:
    with placeholder.container():
        st.title("bejelentkezés")
        u = st.text_input("Felhasználónév", key="login_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="login_p")
        if st.button("Belépés", key="login_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                placeholder.empty()
                st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Értesítések figyelése
if current_user in global_data["notifications"]:
    for msg in global_data["notifications"][current_user]:
        play_cat_meow(msg)
    global_data["notifications"][current_user] = [] # Megjelenítés után töröljük

# FŐ APP FELÜLET
menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY", "🏦 CAT-BANK"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "Catánia", "London", "Macskatelep"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "Catánia", "London", "Macskatelep"])
        price = c2.number_input("Ár (Cam)", min_value=0, value=1000)
        item = c2.text_input("Termék neve")
        
        if st.button("🚀 KÜLDÉS") and item:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item,
                "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            # Értesítés a címzettnek
            if target not in global_data["notifications"]: global_data["notifications"][target] = []
            global_data["notifications"][target].append(f"{current_user} küldött egy ajánlatot: {item} ({price} Cam)!")
            st.success("Küldve!"); st.rerun()

with menu[1]:
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** ajánlata: **{t['item']}**")
            # Revolut-stílusú fizetés
            if st.button(f"Fizetés (NFC / Kártya) - {t['price']+990} Cam", key=f"pay_{tid}"):
                st.session_state[f"pay_step_{tid}"] = True
            
            if st.session_state.get(f"pay_step_{tid}"):
                st.markdown("### 🏦 Cat-Bank Checkout")
                method = st.radio("Fizetési mód", ["💳 Kártya", "📱 Apple/Google Pay (NFC)", "💰 Egyenleg"])
                if st.button("Tranzakció megerősítése"):
                    cost = t["price"] + 990
                    if global_data["balances"][current_user] >= cost:
                        global_data["balances"][current_user] -= cost
                        global_data["balances"][t["sender"]] += (t["price"] + 495)
                        t["status"] = "ACCEPTED"
                        t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.success("Sikeres fizetés!"); time.sleep(1); st.rerun()
                    else:
                        st.error("Nincs elég fedezet!")

    st.divider()

    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            order_num = tid.replace("TID-", "#")
            st.write(f"🚚 **Order {order_num}**: {t['item']}")
            
            rem = (t["eta_time"] - datetime.now()).total_seconds()
            
            if t["sender"] == current_user:
                states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                new_s = st.selectbox("Státusz", states, index=states.index(t["state_text"]) if t["state_text"] in states else 0, key=f"s_{tid}")
                if new_s != t["state_text"]:
                    t["state_text"] = new_s
                    # Értesítés küldése státuszváltozáskor
                    if t['receiver'] not in global_data["notifications"]: global_data["notifications"][t['receiver']] = []
                    global_data["notifications"][t['receiver']].append(f"A(z) {order_num} csomagod állapota: {new_s}!")
                    st.rerun()

                # ALÁÍRÓPAD (Csak ha a kapu előtt van)
                if t["state_text"] == "A kapu előtt 🚪":
                    st.warning("Kérd meg a címzettet az aláírásra!")
                    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=150, key=f"canv_{tid}")
                    if st.button("Aláírás mentése és Átadás", key=f"sig_{tid}"):
                        t["status"] = "DONE"
                        t["signature"] = True
                        st.rerun()
            else:
                st.info(f"📍 Helyzet: {t['state_text']}")
                if rem <= 0:
                    st.success("✅ MEGÉRKEZETT! (Várj a futárra az aláíráshoz)")

            pdf = create_pdf(t, tid)
            st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

with menu[3]:
    st.title("🏦 Cat-Bank (Revolut Mode)")
    st.metric("Elérhető egyenleg", f"{global_data['balances'].get(current_user, 0)} Cam")
    st.progress(0.7) # Csak dizájn elem
    st.write("Utolsó tranzakciók: Nincsenek")

time.sleep(3); st.rerun()

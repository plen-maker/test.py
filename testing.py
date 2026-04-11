import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from streamlit_drawable_canvas import st_canvas # Aláíráshoz szükséges

# --- 1. OLDAL BEÁLLÍTÁSA ÉS REKLÁMMENTESÍTÉS ---
st.set_page_config(page_title="Tréd🔥🔥🔥", layout="wide", page_icon="🚚")

# Eltüntetjük a Streamlit sallangokat, hogy profibb legyen
st.markdown("""
    <style>
    header, footer, [data-testid="stHeader"], .stAppToolbar { visibility: hidden !important; display: none !important; }
    .nfc-pulse {
        width: 80px; height: 80px; background: rgba(0, 117, 255, 0.2);
        border-radius: 50%; border: 2px solid #0075FF;
        animation: pulse 1.5s infinite; margin: 10px auto;
    }
    @keyframes pulse { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(1.1); opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- MACSKA HANG ÉS ÜZENET FUNKCIÓ ---
def meow_alert(text):
    st.markdown(f"""
        <audio autoplay><source src="https://www.myinstants.com/media/sounds/meow-sound-effect1.mp3" type="audio/mpeg"></audio>
        <div style="background:#ff4b4b; padding:10px; border-radius:10px; color:white; margin-bottom:10px;">🐱 {text}</div>
        """, unsafe_allow_html=True)

# --- 2. KÖZÖS MEMÓRIA (Frissítve az új tárolókkal) ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000, "ddnemet": 50000, "kormuranusz": 50000},
        "notifs": {} # Értesítéseknek
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99", "kormuranusz": "kormicica", "ddnemet": "koficcica"}

# --- 3. PROFI SZÁMLA GENERÁLÓ (Frissítve Order Numberrel) ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.darkblue)
    c.drawString(50, height - 50, "HIVATALOS SZÁMLA / INVOICE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(50, height - 70, f"Order Number: {tid.replace('TID-', '#')}") # Order Number kiírása
    c.drawString(50, height - 85, f"Elfogadás ideje: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 95, width - 50, height - 95)
    y = height - 120
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "SZÁLLÍTÁSI ADATOK")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Feladó: {t['sender'].capitalize()}")
    y -= 15; c.drawString(60, y, f"Címzett: {t['receiver'].capitalize()}")
    y -= 40; c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "TERMÉK INFORMÁCIÓ")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Megnevezés: {t['item']}")
    y -= 50; c.line(50, y+10, width - 50, y+10)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.red)
    c.drawString(50, y, f"TELJES FIZETETT ÖSSZEG: {t['price'] + 990} Cam")
    c.save(); buf.seek(0)
    return buf

# --- 4. LOGIN KEZELÉS ---
placeholder = st.empty()
if 'username' not in st.session_state:
    with placeholder.container():
        st.title("bejelentkezés")
        u = st.text_input("Felhasználónév", key="login_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="login_p")
        if st.button("Belépés", key="login_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                st.session_state.bank_unlocked = False # Banki biztonsági állapot
                placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok!")
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# Értesítések feldolgozása nyávogással
if current_user in global_data["notifs"] and global_data["notifs"][current_user]:
    for msg in global_data["notifs"][current_user]:
        meow_alert(msg)
    global_data["notifs"][current_user] = []

# SIDEBAR
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleged", f"{global_data['balances'].get(current_user, 0)} Cam")

if st.sidebar.button("Kijelentkezés"):
    del st.session_state.username
    st.rerun()

# FŐ APP FELÜLET
menu = st.tabs(["🚀 KÜLDÉS", "📋 felraktam a kezem", "📜 HISTORY", "🏦 CAT-BANK"])

with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        start = c1.selectbox("Indulás", ["Budapest HUB", "London", "Macskatelep"])
        end = c1.selectbox("Célállomás", ["Budapest HUB", "London", "Macskatelep"])
        price = c2.number_input("Ár (Cam)", min_value=0, value=1000)
        item = c2.text_input("Termék neve")
        desc = st.text_area("Termék leírása")
        photo = st.file_uploader("Fotó", type=['jpg', 'png'])
        
        if st.button("🚀 KÜLDÉS") and item:
            tid = f"TID-{int(time.time())}"
            global_data["active_trades"][tid] = {
                "sender": current_user, "receiver": target, "item": item, "description": desc,
                "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                "photo": photo, "start_loc": start, "end_loc": end,
                "eta_time": datetime.now() + timedelta(minutes=5)
            }
            # Értesítés küldése
            if target not in global_data["notifs"]: global_data["notifs"][target] = []
            global_data["notifs"][target].append(f"{current_user} küldött egy ajánlatot ({price} Cam)!")
            st.success("Küldve!"); st.rerun()

with menu[1]:
    # Bejövő ajánlatok elfogadása (REVOLUT STÍLUSÚ FIZETÉSSEL)
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.write(f"📩 **{t['sender']}** -> {t['item']}")
            if st.button(f"Fizetés (Kártya / NFC) - {t['price']+990} Cam", key=f"pay_{tid}"):
                st.session_state[f"nfc_{tid}"] = True
            
            if st.session_state.get(f"nfc_{tid}"):
                st.markdown('<div class="nfc-pulse"></div>', unsafe_allow_html=True)
                if st.button("Érintés megerősítése", key=f"conf_{tid}"):
                    cost = t["price"] + 990
                    if global_data["balances"][current_user] >= cost:
                        global_data["balances"][current_user] -= cost
                        global_data["balances"][t["sender"]] += (t["price"] + 495)
                        t["status"] = "ACCEPTED"
                        t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.rerun()
                    else: st.error("Nincs elég fedezet!")

    st.divider()

    # Aktív folyamatok
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    for tid, t in active.items():
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | Order: {tid.replace('TID-', '#')}")
            c_ctrl, c_info = st.columns(2)
            with c_ctrl:
                if t["sender"] == current_user:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    new_s = st.selectbox("Státusz", states, index=states.index(t["state_text"]) if t["state_text"] in states else 0, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        # Értesítés a címzettnek a változásról
                        if t['receiver'] not in global_data["notifs"]: global_data["notifs"][t['receiver']] = []
                        global_data["notifs"][t['receiver']].append(f"Csomagod állapota: {new_s}")
                        st.rerun()
                    
                    # ALÁÍRÓPAD (Csak ha a kapu előtt van)
                    if t["state_text"] == "A kapu előtt 🚪":
                        st.warning("ALÁÍRÁS SZÜKSÉGES")
                        canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=100, key=f"sign_{tid}")
                        if st.button("Átadva / Aláírás mentése", key=f"done_btn_{tid}"):
                            t["status"] = "DONE"; st.rerun()
                else:
                    st.info(f"📍 Helyzet: {t['state_text']}")

            with c_info:
                rem = (t["eta_time"] - datetime.now()).total_seconds()
                if rem > 0:
                    st.subheader(f"⏳ {int(rem//60):02d}:{int(rem%60):02d}")
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    st.write("Várd meg a futárt az aláíráshoz.")
                
                pdf = create_pdf(t, tid)
                st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

with menu[3]:
    # CAT-BANK (Revolut stílusú egyenlegkezelő)
    st.title("🏦 Cat-Bank")
    st.metric("Elérhető egyenleg", f"{global_data['balances'][current_user]} Cam")
    st.progress(0.6)
    st.write("💳 Kártyaszám: 4532 **** **** 8891")
    if st.button("Pénz feltöltése (Demo)"):
        global_data["balances"][current_user] += 5000
        st.rerun()

# Automatikus frissítés 3 másodpercenként
time.sleep(3); st.rerun()

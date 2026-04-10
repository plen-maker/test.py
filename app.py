import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- HANGJELZÉS FUNKCIÓ (HTML/JS) ---
def play_notification_sound():
    # Megbízható, rövid értesítési hang
    audio_url = "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Samples/master/notification.mp3"
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{audio_url}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- 1. OLDAL ÉS MEMÓRIA BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC PRO", layout="wide", page_icon="📦")

@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 100000, "peti": 50000, "adel": 50000},
        "base_gallery": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- 2. ESEMÉNY FIGYELŐ (Hangokhoz) ---
# Eltároljuk az állapotokat, hogy tudjuk, mikor kell csipogni
if 'last_states' not in st.session_state:
    st.session_state.last_states = {} # {tid: status_text}
if 'last_trade_count' not in st.session_state:
    st.session_state.last_trade_count = 0

# --- 3. PDF GENERÁLÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.darkblue)
    c.drawString(50, height - 50, "HIVATALOS SZAMLA / INVOICE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(50, height - 70, f"Tranzakcio ID: {tid}")
    c.drawString(50, height - 85, f"Elfogadva: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 95, width - 50, height - 95)
    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "SZALLITASI INFORMACIOK")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Felado: {t['sender'].capitalize()} | Cimzett: {t['receiver'].capitalize()}")
    c.drawString(60, y-15, f"Utvonal: {t['start_loc']} -> {t['end_loc']}")
    y -= 45
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "TERMEK ES PENZUGY")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Termek: {t['item']} ({t['price']} Ft)")
    c.drawString(60, y-15, f"Leiras: {t.get('description', '-')}")
    c.drawString(60, y-30, f"Szallitasi dij: 990 Ft")
    y -= 60
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(50, y, f"VEGOSSZEG: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 4. LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGISTIC - LOGIN")
    u = st.text_input("Felhasznalonev").lower().strip()
    p = st.text_input("Jelszo", type="password")
    if st.button("Belepes"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- 5. HANG LOGIKA (Minden változásra) ---
current_trades = global_data["active_trades"]

# A: Új trade érkezett (Vevőnek)
incoming = [tid for tid, t in current_trades.items() if t['receiver'] == current_user and t['status'] == 'WAITING']
if len(incoming) > st.session_state.last_trade_count:
    play_notification_sound()
    st.toast("📩 Új trade érkezett!")
st.session_state.last_trade_count = len(incoming)

# B: Státusz frissülés (Bárkinek, aki érintett a trade-ben)
for tid, t in current_trades.items():
    if current_user in [t['sender'], t['receiver']]:
        state_key = f"{tid}_{t['status']}_{t['state_text']}"
        if tid in st.session_state.last_states:
            if st.session_state.last_states[tid] != state_key:
                play_notification_sound()
                st.toast(f"🔔 Frissítés: {t['item']} -> {t['state_text']}")
        st.session_state.last_states[tid] = state_key

# --- 6. UI ÉS TABS ---
st.sidebar.title(f"Szia, {current_user.capitalize()}!")
online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE"])

with menu[0]:
    st.header("Új Szállítás")
    targets = [u for u in online_now if u != current_user]
    if not targets: st.info("Nincs online partner.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "London", "Budapest"])
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "London", "Budapest"])
        with c2:
            price_val = st.number_input("Ár (Ft)", min_value=0, value=1000)
            item_val = st.text_input("Termék neve")
        desc_val = st.text_area("Leírás")
        up_photo = st.file_uploader("Fotó", type=['jpg', 'png'])
        if st.button("🚀 KÜLDÉS"):
            if item_val and up_photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item_val, "description": desc_val,
                    "price": price_val, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "photo": up_photo, "start_loc": start, "end_loc": end,
                    "eta_time": datetime.now() + timedelta(minutes=5)
                }
                play_notification_sound() # Küldéskor is szóljon
                st.success("Kérelem elküldve!")
                st.rerun()

with menu[1]:
    # Bejövő trade-ek
    reqs = {tid: t for tid, t in current_trades.items() if t['receiver'] == current_user and t['status'] == 'WAITING'}
    for tid, t in reqs.items():
        with st.container(border=True):
            st.subheader(f"📩 Érkezik: {t['item']}")
            col_img, col_txt = st.columns([1, 2])
            with col_img: st.image(t["photo"], use_container_width=True)
            with col_txt:
                st.write(f"**Ár:** {t['price']} Ft | **Leírás:** {t['description']}")
                if st.button(f"ELFOGADOM ✅", key=f"acc_{tid}"):
                    total = t['price'] + 990
                    if global_data["balances"][current_user] >= total:
                        global_data["balances"][current_user] -= total
                        global_data["balances"][t['sender']] += (t['price'] + 495)
                        t["status"] = "ACCEPTED"
                        t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        play_notification_sound() # Elfogadáskor is szóljon
                        st.rerun()

    st.divider()

    # Aktív folyamatok (Szerkesztés + Timer)
    active = {tid: t for tid, t in current_trades.items() if t['status'] == 'ACCEPTED'}
    for tid, t in active.items():
        is_sender = (t["sender"] == current_user)
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            c_left, c_right = st.columns(2)
            with c_left:
                if is_sender:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    new_s = st.selectbox("Státusz", states, index=states.index(t["state_text"]) if t["state_text"] in states else 0, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        st.rerun()
                    m_edit = st.number_input("Perc módosítása:", 1, 120, 5, key=f"m_{tid}")
                    if st.button("FRISSÍTÉS ⏱️", key=f"t_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=m_edit)
                        st.rerun()
                else:
                    st.info(f"📍 Státusz: {t['state_text']}")

            with c_right:
                rem = (t["eta_time"] - datetime.now()).total_seconds()
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"⏳ {m:02d}:{s:02d}")
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t["receiver"]:
                        if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"r_{tid}"):
                            t["status"] = "DONE"; st.rerun()

            with st.expander("📄 SZÁMLA"):
                pdf_data = create_pdf(t, tid)
                st.download_button("📥 PDF Letöltése", data=pdf_data, file_name=f"szamla_{tid}.pdf", mime="application/pdf", key=f"pdf_{tid}")

# --- AUTO-REFRESH ÉS VÉGE ---
time.sleep(3)
st.rerun()

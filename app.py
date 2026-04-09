import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC CONTROL", layout="wide")

# --- PDF GENERÁLÓ FÜGGVÉNY ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Fejléc
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "LOGISTIC INVOICE / SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Kiállítás dátuma: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.line(50, height - 80, width - 50, height - 80)

    # Adatok
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 110, f"Tranzakció ID: {tid}")
    
    c.setFont("Helvetica", 12)
    y = height - 140
    data = [
        f"Feladó: {t['sender'].capitalize()}",
        f"Címzett: {t['receiver'].capitalize()}",
        f"Termék: {t['item']}",
        f"Útvonal: {t['start_loc']} -> {t['end_loc']}",
        f"Alapár: {t['price']} Ft",
        f"Szállítási díj: 990 Ft",
        "",
        f"ÖSSZESEN: {t['price'] + 990} Ft"
    ]

    for line in data:
        if "ÖSSZESEN" in line:
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.red)
        c.drawString(60, y, line)
        y -= 25
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)

    # Lábléc
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "Ez egy automatikusan generált IRL LOGISTIC bizonylat.")
    
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {}, 
        "trade_history": [],
        "active_trades": {}, 
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000},
        "base_gallery": []
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99"}

# --- SEGÉDFÜGGVÉNYEK ---
def safe_date_format(dt, fmt="%H:%M:%S"):
    if dt is None: return "--:--:--"
    if isinstance(dt, str):
        try: dt = datetime.fromisoformat(dt)
        except: return dt
    try: return dt.strftime(fmt)
    except: return str(dt)

# --- LOGIN ---
if 'username' not in st.session_state:
    st.title("🛡️ IRL LOGIN")
    u = st.text_input("Név", key="login_name").lower().strip()
    p = st.text_input("PW", type="password", key="login_pw")
    if st.button("Belépés", key="login_btn"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            if u not in global_data["balances"]: global_data["balances"][u] = 50000
            st.rerun()
    st.stop()

current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# --- TABS ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE"])

# --- 1. TRADE INDÍTÁS ---
with menu[0]:
    st.header("Új szállítás")
    others_online = [u for u in global_data["online_users"].keys() if u != current_user]
    if not others_online:
        st.info("Nincs más online futár.")
    else:
        target = st.selectbox("Címzett", others_online, key="trade_target")
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulás", ["Catánia (HU)", "Codeland (RO)", "New York", "London"], key="trade_start")
            end = st.selectbox("Cél", ["Catánia (HU)", "Codeland (RO)", "New York", "London"], key="trade_end")
        with c2:
            price_input = st.number_input("Ár (Ft)", min_value=0, value=1000)
            item_name = st.text_input("Tárgy")
        
        photo = st.file_uploader("Kép", type=['jpg', 'png'])
        
        if st.button("🚀 KÜLDÉS"):
            if item_name and photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item_name,
                    "price": price_input, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "photo": photo, "start_loc": start, "end_loc": end,
                    "start_time": datetime.now(), "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success(f"✅ Elküldve {target} részére!")
                st.rerun()

# --- 2. CONTROL PANEL ---
with menu[1]:
    # --- Címzett Elfogadás ---
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t.get("receiver") == current_user and t.get("status") == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1: st.image(t["photo"], use_container_width=True)
            with col2:
                st.write(f"**Küldő:** {t['sender']} | **Tárgy:** {t['item']}")
                st.write(f"**Útvonal:** {t['start_loc']} -> {t['end_loc']}")
                if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                    global_data["balances"][t["sender"]] -= (t["price"] + 990)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()

    # --- Futár Kontroll ---
    my_trades = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    for tid, t in my_trades.items():
        is_sender = (t.get("sender") == current_user)
        with st.container(border=True):
            st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
            c_edit, c_timer = st.columns(2)
            
            with c_edit:
                if is_sender:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                    new_s = st.selectbox("Státusz", states, index=curr_idx, key=f"sel_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        st.rerun()
                    
                    m_edit = st.number_input("Módosítás (perc):", 1, 60, 5, key=f"m_{tid}")
                    if st.button("IDŐ FRISSÍTÉSE", key=f"t_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=m_edit)
                        st.rerun()
                else:
                    st.info(f"📍 Helyzet: {t['state_text']}")

            with c_timer:
                rem = (t["eta_time"] - datetime.now()).total_seconds()
                st.write(f"ETA: {safe_date_format(t['eta_time'])}")
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"{m:02d}:{s:02d}")
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t["receiver"] and st.button("ÁTVÉTEL", key=f"r_{tid}"):
                        t["status"] = "DONE"; st.rerun()

            # --- IMPROVED INVOICE / PDF ---
            with st.expander("📄 SZÁMLA ÉS PDF"):
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    st.image(t["photo"], width=150)
                with col_i2:
                    st.write(f"**ID:** {tid}")
                    st.write(f"**Összeg:** {t['price'] + 990} Ft")
                    pdf_file = create_pdf(t, tid)
                    st.download_button(
                        label="📥 SZÁMLA LETÖLTÉSE (PDF)",
                        data=pdf_file,
                        file_name=f"szamla_{tid}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{tid}"
                    )

# AUTO-REFRESH
if any(t.get("status") == "ACCEPTED" for t in global_data["active_trades"].values()):
    time.sleep(1); st.rerun()

import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="📦")

# --- 2. KÖZÖS MEMÓRIA ---
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

# --- 3. SZÁMLA GENERÁLÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, 800, "INVOICE / SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"ID: {tid} | Idő: {t.get('accepted_at', 'N/A')}")
    c.line(50, 760, 550, 760)
    c.drawString(50, 730, f"Feladó: {t['sender']} | Címzett: {t['receiver']}")
    c.drawString(50, 710, f"Útvonal: {t['start_loc']} -> {t['end_loc']}")
    c.drawString(50, 680, f"Termék: {t['item']}")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(50, 640, f"VÉGÖSSZEG: {t['price'] + 990} Ft")
    c.save()
    buf.seek(0)
    return buf

# --- 4. LOGIN LOGIKA (Garantált szétválasztás) ---
if 'username' not in st.session_state:
    # CSAK EZ LÁTSZIK, HA NINCS BELÉPVE
    st.title("🛡️ IRL LOGISTIC - LOGIN")
    with st.container(border=True):
        u = st.text_input("Felhasználónév").lower().strip()
        p = st.text_input("Jelszó", type="password")
        if st.button("Belépés"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Hibás adatok!")
else:
    # --- CSAK EZ LÁTSZIK, HA BE VAN LÉPVE ---
    current_user = st.session_state.username
    global_data["online_users"][current_user] = time.time()

    # SIDEBAR
    st.sidebar.title(f"Szia, {current_user.capitalize()}!")
    online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
    st.sidebar.write(f"🟢 Online: {', '.join(online_now)}")
    st.sidebar.metric("Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")
    
    if st.sidebar.button("Kijelentkezés"):
        del st.session_state.username
        st.rerun()

    # FŐ TARTALOM
    menu = st.tabs(["🚀 KÜLDÉS", "📋 CONTROL PANEL", "📜 HISTORY"])

    with menu[0]:
        targets = [u for u in online_now if u != current_user]
        if not targets: st.info("Nincs online partner.")
        else:
            target = st.selectbox("Címzett", targets)
            c1, c2 = st.columns(2)
            start = c1.selectbox("Indulás", ["Budapest", "Catánia", "London", "New York"])
            end = c1.selectbox("Cél", ["Budapest", "Catánia", "London", "New York"])
            price = c2.number_input("Ár (Ft)", min_value=0, value=1000)
            item = c2.text_input("Termék neve")
            desc = st.text_area("Leírás")
            photo = st.file_uploader("Fotó", type=['jpg', 'png'])
            
            if st.button("🚀 KÜLDÉS"):
                if item and photo:
                    tid = f"TID-{int(time.time())}"
                    global_data["active_trades"][tid] = {
                        "sender": current_user, "receiver": target, "item": item, "description": desc,
                        "price": price, "status": "WAITING", "state_text": "Várakozás...",
                        "photo": photo, "start_loc": start, "end_loc": end,
                        "eta_time": datetime.now() + timedelta(minutes=5)
                    }
                    st.success("Küldve!"); st.rerun()

    with menu[1]:
        # Bejövő kérelmek
        reqs = {tid: t for tid, t in global_data["active_trades"].items() if t['receiver'] == current_user and t['status'] == "WAITING"}
        for tid, t in reqs.items():
            with st.container(border=True):
                st.write(f"📩 **{t['sender']}** -> {t['item']}")
                if st.button(f"ELFOGADOM ({t['price']+990} Ft)", key=f"acc_{tid}"):
                    cost = t["price"] + 990
                    if global_data["balances"][current_user] >= cost:
                        global_data["balances"][current_user] -= cost
                        global_data["balances"][t['sender']] += (t['price'] + 495)
                        t["status"] = "ACCEPTED"
                        t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.rerun()

        st.divider()

        # Aktív szállítások
        active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
        for tid, t in active.items():
            with st.container(border=True):
                st.write(f"🚚 **{t['item']}** | {t['start_loc']} -> {t['end_loc']}")
                cl, cr = st.columns(2)
                with cl:
                    if t["sender"] == current_user:
                        states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                        curr_v = t["state_text"] if t["state_text"] in states else states[0]
                        new_s = st.selectbox("Állapot", states, index=states.index(curr_v), key=f"s_{tid}")
                        if new_s != t["state_text"]:
                            t["state_text"] = new_s; st.rerun()
                    else:
                        st.info(f"📍 Helyzet: **{t['state_text']}**")
                with cr:
                    rem = (t["eta_time"] - datetime.now()).total_seconds()
                    if rem > 0:
                        st.write(f"⏳ ETA: {int(rem//60):02d}:{int(rem%60):02d}")
                    else:
                        st.success("✅ MEGÉRKEZETT!")
                        if current_user == t["receiver"] and st.button("ÁTVÉTEL", key=f"d_{tid}"):
                            t["status"] = "DONE"; st.rerun()
                    
                    pdf = create_pdf(t, tid)
                    st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{tid}.pdf", key=f"p_{tid}")

    # --- AUTO-REFRESH (Csak belépve fut) ---
    time.sleep(3)
    st.rerun()

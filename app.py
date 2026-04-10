import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

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

# --- 3. PDF GENERÁLÓ FÜGGVÉNY ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "LOGISTIC INVOICE / SZÁMLA")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.line(50, height - 80, width - 50, height - 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 110, f"Tranzakcio ID: {tid}")
    c.setFont("Helvetica", 12)
    y = height - 140
    lines = [
        f"Felado: {t['sender'].capitalize()}",
        f"Cimzett: {t['receiver'].capitalize()}",
        f"Termek: {t['item']}",
        f"Utvonal: {t['start_loc']} -> {t['end_loc']}",
        f"Alapar: {t['price']} Ft",
        f"Szallitas: 990 Ft",
        "",
        f"OSSZESEN: {t['price'] + 990} Ft"
    ]
    for line in lines:
        if "OSSZESEN" in line: c.setFont("Helvetica-Bold", 14)
        c.drawString(60, y, line)
        y -= 25
    c.save()
    buf.seek(0)
    return buf

# --- 4. SEGÉDFÜGGVÉNYEK ---
def safe_date_format(dt, fmt="%H:%M:%S"):
    if dt is None: return "--:--:--"
    if isinstance(dt, str):
        try: dt = datetime.fromisoformat(dt)
        except: return dt
    return dt.strftime(fmt)

# --- 5. LOGIN RENDSZER ---
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

# --- 6. SIDEBAR ---
st.sidebar.title(f"Udv, {current_user.capitalize()}!")
st.sidebar.divider()
st.sidebar.subheader("🟢 Online futarok")
current_t = time.time()
online_now = [u for u, last in global_data["online_users"].items() if current_t - last < 10]
for o in online_now:
    st.sidebar.write(f"• {o.capitalize()}")
st.sidebar.divider()
st.sidebar.metric("Sajat Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

# --- 7. TABS ---
menu = st.tabs(["🚀 TRADE INDITAS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE HQ"])

# --- TAB 1: KÜLDÉS ---
with menu[0]:
    st.header("Uj szallitas inditasa")
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs mas online futar.")
    else:
        target = st.selectbox("Cimzett", targets)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulas", ["Catania (HU)", "Codeland (RO)", "New York", "London", "Budapest HUB"])
            end = st.selectbox("Celallomas", ["Catania (HU)", "Codeland (RO)", "New York", "London", "Budapest HUB"])
        with c2:
            price_val = st.number_input("Termek erteke (Ft)", min_value=0, value=1000)
            item_val = st.text_input("Csomag tartalma")
        
        up_photo = st.file_uploader("Termekfoto feltoltese", type=['jpg', 'png'])
        
        if st.button("🚀 Kerelem kuldese"):
            if item_val and up_photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item_val,
                    "price": price_val, "status": "WAITING", "state_text": "Csomagolas alatt...",
                    "photo": up_photo, "start_loc": start, "end_loc": end,
                    "start_time": datetime.now(), "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success(f"✅ Sikeresen elkuldve {target} reszere!")
                time.sleep(1)
                st.rerun()

# --- TAB 2: CONTROL PANEL ---
with menu[1]:
    # Bejövő kérelmek
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t.get("receiver") == current_user and t.get("status") == "WAITING"}
    for tid, t in reqs.items():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1: st.image(t["photo"], use_container_width=True)
            with col2:
                st.write(f"**Kuldo:** {t['sender']} | **Targy:** {t['item']}")
                st.write(f"**Utvonal:** {t['start_loc']} -> {t['end_loc']}")
                if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                    global_data["balances"][t["sender"]] -= (t["price"] + 990)
                    t["status"] = "ACCEPTED"
                    st.rerun()

    st.divider()

    # Aktív folyamatok
    active = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    for tid, t in active.items():
        is_sender = (t["sender"] == current_user)
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** | {t['start_loc']} ➔ {t['end_loc']}")
            c_left, c_right = st.columns(2)
            
            with c_left:
                if is_sender:
                    states = ["Csomagolas alatt...", "Uton a repterre", "A levegoben ✈️", "Kiszallitas alatt", "A kapu elott 🚪"]
                    curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                    new_s = st.selectbox("Statusz", states, index=curr_idx, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        st.rerun()
                    m_edit = st.number_input("Ido (perc):", 1, 60, 5, key=f"m_{tid}")
                    if st.button("FRISSITES ⏱️", key=f"t_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=m_edit)
                        st.rerun()
                else:
                    st.info(f"📍 Helyzet: **{t['state_text']}**")

            with c_right:
                eta = t["eta_time"]
                if isinstance(eta, str): eta = datetime.fromisoformat(eta)
                rem = (eta - datetime.now()).total_seconds()
                st.write(f"Erkezes: {safe_date_format(eta)}")
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"{m:02d}:{s:02d}")
                else:
                    st.success("✅ MEGERKEZETT!")
                    if current_user == t["receiver"]:
                        if st.button("ATVETEL", key=f"recv_{tid}"):
                            t["status"] = "DONE"
                            st.rerun()

            with st.expander("📄 Szamla & PDF"):
                st.image(t["photo"], width=150)
                pdf_data = create_pdf(t, tid)
                st.download_button(
                    label="📥 PDF Letoltese",
                    data=pdf_data,
                    file_name=f"szamla_{tid}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{tid}"
                )

# --- TAB 3: HISTORY ---
with menu[2]:
    done = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "DONE"}
    for tid, t in done.items():
        if t["sender"] == current_user:
            if st.button(f"Szatyor vissza: {t['item']}", key=f"b_{tid}"):
                global_data["trade_history"].append({"Ido": datetime.now().strftime("%H:%M"), "Kuldo": t["sender"], "Vevo": t["receiver"], "Targy": t["item"]})
                del global_data["active_trades"][tid]
                st.rerun()
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- TAB 4: BASE ---
with menu[3]:
    st.header("Bazis Galeria")
    nb = st.file_uploader("Kep", type=['jpg', 'png'], key="base")
    if st.button("Feltoltes") and nb:
        global_data["base_gallery"].append({"photo": nb, "user": current_user, "time": datetime.now().strftime("%H:%M")})
        st.rerun()
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"{entry['user']} | {entry['time']}")

# --- AUTO-REFRESH ---
time.sleep(3)
st.rerun()

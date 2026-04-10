import streamlit as st
import time
import pandas as pd
import random
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. AUTO-REFRESH ÉS OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="IRL LOGISTIC HUB", layout="wide", page_icon="🚚")

# --- 2. KÖZÖS MEMÓRIA (Mindenki ezt látja) ---
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
    c.drawString(50, height - 70, f"Dátum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.line(50, height - 80, width - 50, height - 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 110, f"Tranzakció ID: {tid}")
    c.setFont("Helvetica", 12)
    y = height - 140
    lines = [
        f"Feladó: {t['sender'].capitalize()}",
        f"Címzett: {t['receiver'].capitalize()}",
        f"Termék: {t['item']}",
        f"Útvonal: {t['start_loc']} -> {t['end_loc']}",
        f"Alapár: {t['price']} Ft",
        f"Szállítás: 990 Ft",
        "",
        f"ÖSSZESEN: {t['price'] + 990} Ft"
    ]
    for line in lines:
        if "ÖSSZESEN" in line: c.setFont("Helvetica-Bold", 14)
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
    u = st.text_input("Felhasználónév").lower().strip()
    p = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if u in USERS and USERS[u] == p:
            st.session_state.username = u
            st.rerun()
    st.stop()

current_user = st.session_state.username
# Online állapot frissítése
global_data["online_users"][current_user] = time.time()

# --- 6. SIDEBAR (Ki van online?) ---
st.sidebar.title(f"Üdv, {current_user.capitalize()}!")
st.sidebar.divider()
st.sidebar.subheader("🟢 Online futárok")
current_t = time.time()
online_now = [u for u, last in global_data["online_users"].items() if current_t - last < 10]
for o in online_now:
    st.sidebar.write(f"• {o.capitalize()}")

st.sidebar.divider()
st.sidebar.metric("Saját Egyenleg", f"{global_data['balances'].get(current_user, 0)} Ft")

# --- 7. FŐ TARTALOM ---
menu = st.tabs(["🚀 TRADE INDÍTÁS", "📋 CONTROL PANEL", "📜 HISTORY", "🏠 BASE HQ"])

# --- TAB 1: KÜLDÉS ---
with menu[0]:
    st.header("Új szállítás indítása")
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs más online futár a hálózaton.")
    else:
        target = st.selectbox("Címzett", targets)
        c1, c2 = st.columns(2)
        with c1:
            start = st.selectbox("Indulási pont", ["Catánia (HU)", "Codeland (RO)", "New York", "London", "Budapest HUB"])
            end = st.selectbox("Célállomás", ["Catánia (HU)", "Codeland (RO)", "New York", "London", "Budapest HUB"])
        with c2:
            price = st.number_input("Termék értéke (Ft)", min_value=0, value=1000)
            item = st.text_input("Csomag tartalma")
        
        up_photo = st.file_uploader("Termékfotó feltöltése", type=['jpg', 'png'])
        
        if st.button("🚀 Kérelem küldése"):
            if item and up_photo:
                tid = f"TID-{int(time.time())}"
                global_data["active_trades"][tid] = {
                    "sender": current_user, "receiver": target, "item": item,
                    "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "photo": up_photo, "start_loc": start, "end_loc": end,
                    "start_time": datetime.now(), "eta_time": datetime.now() + timedelta(minutes=5)
                }
                st.success(f"Sikeresen elküldve {target} részére!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Minden adatot meg kell adni!")

# --- TAB 2: CONTROL PANEL (Itt történik a varázslat) ---
with menu[1]:
    # --- CÍMZETT PANEL: ELFOGADÁS ---
    reqs = {tid: t for tid, t in global_data["active_trades"].items() if t.get("receiver") == current_user and t.get("status") == "WAITING"}
    if reqs:
        st.subheader("📩 Bejövő kérelmeid")
        for tid, t in reqs.items():
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])
                with col1: st.image(t["photo"], use_container_width=True)
                with col2:
                    st.write(f"**Küldő:** {t['sender']} | **Tárgy:** {t['item']}")
                    st.write(f"**Útvonal:** {t['start_loc']} -> {t['end_loc']}")
                    st.write(f"**Érték:** {t['price']} Ft (+990 Ft szállítás)")
                    if st.button("ELFOGADOM ✅", key=f"acc_{tid}"):
                        global_data["balances"][t["sender"]] -= (t["price"] + 990)
                        t["status"] = "ACCEPTED"
                        st.rerun()

    st.divider()

    # --- KÖZÖS CONTROL & TIMER ---
    st.subheader("🚚 Aktív Szállítások")
    active = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "ACCEPTED"}
    
    if not active:
        st.info("Nincs folyamatban lévő szállítás.")

    for tid, t in active.items():
        is_sender = (t["sender"] == current_user)
        with st.container(border=True):
            st.write(f"📦 **{t['item']}** | {t['start_loc']} ➔ {t['end_loc']}")
            c_left, c_right = st.columns(2)
            
            with c_left:
                if is_sender:
                    # Státusz állítás
                    st.write("🛠️ **Futár Vezérlés**")
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    curr_idx = states.index(t["state_text"]) if t["state_text"] in states else 0
                    new_s = st.selectbox("Státusz frissítése", states, index=curr_idx, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        t["state_text"] = new_s
                        st.rerun()
                    # Idő módosítása
                    m_edit = st.number_input("ETA módosítása (perc):", 1, 60, 5, key=f"m_{tid}")
                    if st.button("IDŐ FRISSÍTÉSE ⏱️", key=f"t_{tid}"):
                        t["eta_time"] = datetime.now() + timedelta(minutes=m_edit)
                        st.rerun()
                else:
                    st.info(f"📍 Aktuális helyzet: **{t['state_text']}**")
                    st.write(f"Küldő: {t['sender']}")

            with c_right:
                st.write("⌛ **Visszaszámláló**")
                eta = t["eta_time"]
                if isinstance(eta, str): eta = datetime.fromisoformat(eta)
                rem = (eta - datetime.now()).total_seconds()
                
                st.write(f"Érkezés: {safe_date_format(eta)}")
                if rem > 0:
                    m, s = divmod(int(rem), 60)
                    st.header(f"{m:02d}:{s:02d}")
                    st.progress(min(1.0, 1.0 - (rem / 600)))
                else:
                    st.success("✅ MEGÉRKEZETT!")
                    if current_user == t["receiver"]:
                        if st.button("ÁTVÉTEL IGAZOLÁSA", key=f"recv_{tid}"):
                            t["status"] = "DONE"
                            st.rerun()

            with st.expander("📄 Digitális Számla & PDF"):
                st.image(t["photo"], width=150)
                st.write(f"Tranzakció ID: {tid}")
                st.write(f"Összeg: {t['price'] + 990} Ft")
                pdf = create_pdf(t, tid)
                st.download_button("📥 PDF Letöltése", data=pdf, file_name=f"szamla_{tid}.pdf", mime="application/pdf", key=f"p_{tid}")

# --- TAB 3: HISTORY ---
with menu[2]:
    st.header("Lezárt folyamatok")
    done = {tid: t for tid, t in global_data["active_trades"].items() if t.get("status") == "DONE"}
    for tid, t in done.items():
        if t["sender"] == current_user:
            if st.button(f"Szatyor visszaérkezett: {t['item']}", key=f"b_{tid}"):
                global_data["trade_history"].append({
                    "Idő": datetime.now().strftime("%H:%M"),
                    "Küldő": t["sender"], "Vevő": t["receiver"], "Tárgy": t["item"]
                })
                del global_data["active_trades"][tid]
                st.rerun()
    if global_data["trade_history"]:
        st.table(pd.DataFrame(global_data["trade_history"]))

# --- TAB 4: BASE ---
with menu[3]:
    st.header("Bázis Galéria")
    nb = st.file_uploader("Kép feltöltése", type=['jpg', 'png'], key="base")
    if st.button("Feltöltés"):
        if nb:
            global_data["base_gallery"].append({"photo": nb, "user": current_user, "time": datetime.now().strftime("%H:%M")})
            st.rerun()
    cols = st.columns(3)
    for idx, entry in enumerate(global_data["base_gallery"][::-1]):
        with cols[idx % 3]:
            st.image(entry["photo"])
            st.caption(f"{entry['user']} | {entry['time']}")

# --- 8. AZ AUTO-REFRESH MOTORJA ---
# 3 másodpercenként frissítjük az oldalt, hogy lássuk a belépőket/módosításokat
time.sleep(3)
st.rerun() 
                        key=f"pdf_{tid}"
                    )

# AUTO-REFRESH
if any(t.get("status") == "ACCEPTED" for t in global_data["active_trades"].values()):
    time.sleep(1); st.rerun()

import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. OLDAL BEÁLLÍTÁSA ---
st.set_page_config(page_title="Tréd🔥🔥🔥", layout="wide", page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTq9xFPrGZcuBi4sGho51wcEmiwO7M_cN35kQ&s")

# --- MACSKANYAVOGAS HANGOK + REVOLUT STÍLUS ---
CAT_SOUND_JS = """
<script>
function playCatSound(type) {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    if (type === 'send') {
        // Nyávogás küldéskor - felmegy
        oscillator.frequency.setValueAtTime(400, ctx.currentTime);
        oscillator.frequency.linearRampToValueAtTime(800, ctx.currentTime + 0.2);
        oscillator.frequency.linearRampToValueAtTime(600, ctx.currentTime + 0.4);
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.5);
    } else if (type === 'receive') {
        // Nyávogás fogadáskor - lejön
        oscillator.frequency.setValueAtTime(700, ctx.currentTime);
        oscillator.frequency.linearRampToValueAtTime(350, ctx.currentTime + 0.3);
        oscillator.frequency.linearRampToValueAtTime(500, ctx.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.6);
    } else if (type === 'alert') {
        // Duplanyávogás alertre
        oscillator.frequency.setValueAtTime(600, ctx.currentTime);
        oscillator.frequency.linearRampToValueAtTime(900, ctx.currentTime + 0.15);
        oscillator.frequency.setValueAtTime(600, ctx.currentTime + 0.25);
        oscillator.frequency.linearRampToValueAtTime(900, ctx.currentTime + 0.4);
        gainNode.gain.setValueAtTime(0.25, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.5);
    } else if (type === 'done') {
        // Boldog nyávogás kézbesítéskor
        oscillator.frequency.setValueAtTime(500, ctx.currentTime);
        oscillator.frequency.linearRampToValueAtTime(1000, ctx.currentTime + 0.3);
        oscillator.frequency.linearRampToValueAtTime(800, ctx.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.6);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.6);
    }
}
</script>
"""

REVOLUT_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.rev-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    padding: 24px;
    color: white;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.1);
}

.rev-balance {
    font-size: 42px;
    font-weight: 800;
    background: linear-gradient(90deg, #fff 0%, #a8edea 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}

.rev-label {
    font-size: 12px;
    font-weight: 500;
    color: rgba(255,255,255,0.6);
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.nfc-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 50px;
    padding: 12px 28px;
    color: white;
    font-weight: 700;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.nfc-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.card-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border: none;
    border-radius: 50px;
    padding: 12px 28px;
    color: white;
    font-weight: 700;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
}

.payment-modal {
    background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    border-radius: 24px;
    padding: 32px;
    border: 1px solid rgba(255,255,255,0.15);
    text-align: center;
}

.nfc-animation {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    margin: 16px auto;
    animation: nfc-pulse 1.5s infinite;
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
}

@keyframes nfc-pulse {
    0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
    70% { box-shadow: 0 0 0 20px rgba(102, 126, 234, 0); }
    100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
}

.msg-bubble {
    background: rgba(102, 126, 234, 0.15);
    border-left: 3px solid #667eea;
    border-radius: 0 12px 12px 0;
    padding: 10px 16px;
    margin: 8px 0;
    font-size: 13px;
    color: #e0e0e0;
}

.msg-bubble.cat {
    background: rgba(245, 87, 108, 0.1);
    border-left-color: #f5576c;
}

.paper-sign {
    background: linear-gradient(145deg, #fefefe 0%, #f0f0e8 100%);
    border: 2px solid #d4c5a0;
    border-radius: 4px;
    padding: 32px;
    color: #2c2c2c;
    box-shadow: 4px 4px 12px rgba(0,0,0,0.15), inset 0 0 30px rgba(200,190,160,0.2);
    font-family: 'Georgia', serif !important;
    position: relative;
}

.paper-sign::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(transparent, transparent 27px, #e8e0d0 27px, #e8e0d0 28px);
    border-radius: 4px;
    opacity: 0.4;
    pointer-events: none;
}

.sign-line {
    border-bottom: 2px solid #2c2c2c;
    margin: 24px 0 8px 0;
    height: 40px;
    display: flex;
    align-items: flex-end;
    padding-bottom: 4px;
    font-style: italic;
    font-size: 22px;
}

.tx-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.tx-amount-neg { color: #f5576c; font-weight: 600; }
.tx-amount-pos { color: #43e97b; font-weight: 600; }

.pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.pill-waiting { background: rgba(255,193,7,0.2); color: #ffc107; }
.pill-accepted { background: rgba(102,126,234,0.2); color: #667eea; }
.pill-done { background: rgba(67,233,123,0.2); color: #43e97b; }
</style>
"""

# --- 2. KÖZÖS MEMÓRIA ---
@st.cache_resource
def get_global_data():
    return {
        "online_users": {},
        "trade_history": [],
        "active_trades": {},
        "balances": {"admin": 50000, "peti": 50000, "adel": 50000, "ddnemet": 50000, "kormuranusz": 50000},
        "base_gallery": [],
        "messages": {},   # user -> list of {text, type, ts}
        "eta_notified": set(),  # tid-k amikre már küldtünk ETA lejárt üzenetet
        "order_counter": [1000]
    }

global_data = get_global_data()
USERS = {"admin": "1234", "peti": "pisti77", "adel": "trade99", "kormuranusz": "kormicica", "ddnemet": "koficcica"}

def next_order_id():
    global_data["order_counter"][0] += 1
    return f"ORD-{global_data['order_counter'][0]}"

def send_message(user, text, mtype="info"):
    """Üzenet küldése egy felhasználónak"""
    if user not in global_data["messages"]:
        global_data["messages"][user] = []
    global_data["messages"][user].append({
        "text": text,
        "type": mtype,
        "ts": datetime.now().strftime("%H:%M:%S"),
        "read": False
    })

def get_unread(user):
    msgs = global_data["messages"].get(user, [])
    return [m for m in msgs if not m["read"]]

def mark_all_read(user):
    for m in global_data["messages"].get(user, []):
        m["read"] = True

# --- 3. PROFI SZÁMLA GENERÁLÓ ---
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    # Header sáv
    c.setFillColor(colors.HexColor("#1a1a2e"))
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.white)
    c.drawString(50, height - 50, "TRÉD PLATFORM  •  HIVATALOS SZÁMLA")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#a8edea"))
    c.drawString(50, height - 68, f"Order szám: {t.get('order_id', tid)}   |   Tranzakció: {tid}")
    # Törzsrész
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 100, f"Elfogadás ideje: {t.get('accepted_at', 'N/A')}")
    c.line(50, height - 110, width - 50, height - 110)
    y = height - 135
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "SZÁLLÍTÁSI ADATOK")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Feladó: {t['sender'].capitalize()}")
    y -= 15; c.drawString(60, y, f"Címzett: {t['receiver'].capitalize()}")
    y -= 15; c.drawString(60, y, f"Útvonal: {t['start_loc']}  ——>>>  {t['end_loc']}")
    y -= 40; c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "TERMÉK INFORMÁCIÓ")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Megnevezés: {t['item']}")
    y -= 15; c.setFont("Helvetica-Oblique", 10)
    c.drawString(60, y, f"Leírás: {t.get('description', 'Nincs leírás')}")
    y -= 50; c.line(50, y + 10, width - 50, y + 10)
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "KÖLTSÉGVETÉS")
    c.setFont("Helvetica", 11); y -= 20
    c.drawString(60, y, f"Termék eredeti ára: {t['price']} Cam")
    y -= 15; c.drawString(60, y, f"Szállítási díj: 990 Cam")
    y -= 30; c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#f5576c"))
    c.drawString(50, y, f"TELJES FIZETETT ÖSSZEG: {t['price'] + 990} Cam")
    # Fizetési mód
    y -= 30; c.setFont("Helvetica", 11); c.setFillColor(colors.black)
    pay_mode = t.get('payment_method', 'Ismeretlen')
    c.drawString(50, y, f"Fizetési mód: {pay_mode}")
    # Footer
    c.setFillColor(colors.HexColor("#f0f0f0"))
    c.rect(0, 0, width, 40, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#666"))
    c.setFont("Helvetica", 9)
    c.drawString(50, 14, "Tréd Platform  •  Automatikusan generált számla  •  Minden jog fenntartva")
    c.save(); buf.seek(0)
    return buf

# --- 4. LOGIN KEZELÉS ---
st.markdown(REVOLUT_STYLE, unsafe_allow_html=True)
st.markdown(CAT_SOUND_JS, unsafe_allow_html=True)

placeholder = st.empty()

if 'username' not in st.session_state:
    with placeholder.container():
        st.markdown("""
        <div style='max-width:400px;margin:80px auto;text-align:center;'>
            <div style='font-size:60px;margin-bottom:16px;'>😼</div>
            <h1 style='font-size:32px;font-weight:800;background:linear-gradient(90deg,#667eea,#f5576c);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>TRÉD</h1>
            <p style='color:#888;margin-bottom:32px;'>Macskás kereskedési platform</p>
        </div>
        """, unsafe_allow_html=True)
        u = st.text_input("Felhasználónév", key="login_u").lower().strip()
        p = st.text_input("Jelszó", type="password", key="login_p")
        if st.button("🐾 Belépés", key="login_btn", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                placeholder.empty()
                st.rerun()
            else:
                st.error("Hibás adatok! 🙀")
    st.stop()

# --- 5. HA BE VAN LÉPVE ---
current_user = st.session_state.username
global_data["online_users"][current_user] = time.time()

# ETA LEJÁRAT FIGYELÉS - üzenetek küldése
for tid, t in global_data["active_trades"].items():
    if t['status'] == "ACCEPTED":
        rem = (t["eta_time"] - datetime.now()).total_seconds()
        if rem <= 0 and tid not in global_data["eta_notified"]:
            global_data["eta_notified"].add(tid)
            order_id = t.get('order_id', tid)
            send_message(t['sender'], f"🕐 {order_id} – Az ETA lejárt! A csomag hamarosan megérkezik a célállomásra. 🐾", "alert")
            send_message(t['receiver'], f"🕐 {order_id} – Az ETA lejárt! A csomagod hamarosan megérkezik, légy türelemmel! 🐾", "alert")

# SIDEBAR - REVOLUT STÍLUS
with st.sidebar:
    online_now = [u for u, last in global_data["online_users"].items() if time.time() - last < 10]
    bal = global_data['balances'].get(current_user, 0)
    unread = get_unread(current_user)

    st.markdown(f"""
    <div class="rev-card">
        <div class="rev-label">Főszámla egyenleg</div>
        <div class="rev-balance">{bal:,} Cam</div>
        <div style="margin-top:12px;font-size:13px;color:rgba(255,255,255,0.6);">
            👤 {current_user.capitalize()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Online userek
    st.markdown(f"<div style='font-size:13px;color:#888;margin-bottom:8px;'>🟢 Online: {', '.join(online_now)}</div>", unsafe_allow_html=True)

    # Üzenetek
    if unread:
        st.markdown(f"### 🔔 Értesítések ({len(unread)})")
        for m in unread[-5:]:
            icon = "🐱" if m["type"] == "info" else "🙀" if m["type"] == "alert" else "😺"
            st.markdown(f"""
            <div class="msg-bubble {'cat' if m['type'] == 'alert' else ''}">
                {icon} <b>{m['ts']}</b><br>{m['text']}
            </div>
            """, unsafe_allow_html=True)
        if st.button("✓ Olvasottnak jelöl", use_container_width=True):
            mark_all_read(current_user)
            st.rerun()
    else:
        st.markdown("<div style='color:#555;font-size:13px;'>Nincs új értesítés 😸</div>", unsafe_allow_html=True)

    st.divider()

    # Tranzakció előzmények a sidebarban
    my_done = [t for t in global_data["active_trades"].values()
               if t['status'] == "DONE" and (t['sender'] == current_user or t['receiver'] == current_user)]
    if my_done:
        st.markdown("### 📊 Tranzakciók")
        for t in my_done[-5:]:
            is_sender = t['sender'] == current_user
            amount = -(t['price'] + 990) if not is_sender else (t['price'] + 495)
            color_class = "tx-amount-pos" if amount > 0 else "tx-amount-neg"
            sign = "+" if amount > 0 else ""
            st.markdown(f"""
            <div class="tx-item">
                <div>
                    <div style='font-size:13px;font-weight:500;'>{t['item']}</div>
                    <div style='font-size:11px;color:#555;'>{t.get('order_id','?')}</div>
                </div>
                <div class="{color_class}">{sign}{amount} Cam</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Kijelentkezés", use_container_width=True):
        del st.session_state.username
        st.rerun()

# --- FŐ APP ---
menu = st.tabs(["🚀 KÜLDÉS", "📋 BEJÖVŐ & AKTÍV", "🏦 BANK", "📜 HISTORY"])

# ==================== TAB 1: KÜLDÉS ====================
with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs online partner. Várj egy macskát... 😴")
    else:
        st.markdown("### 📦 Új szállítási ajánlat")
        col_form, col_prev = st.columns([3, 2])
        with col_form:
            target = st.selectbox("Címzett", targets)
            c1, c2 = st.columns(2)
            start = c1.selectbox("Indulás", ["Budapest HUB", "Catánia", "London", "New York", "Codeland",
                                              "Catániai Félszigetek", "Nyauperth", "Macskatelep", "Tarantulai Fészkek"])
            end = c1.selectbox("Célállomás", ["Budapest HUB", "Catánia", "London", "New York", "Codeland",
                                               "Catániai Félszigetek", "Nyauperth", "Macskatelep", "Tarantulai Fészkek"])
            price = c2.number_input("Ár (Cam)", min_value=0, value=1000)
            item = c2.text_input("Termék neve")
            desc = st.text_area("Termék leírása")
            photo = st.file_uploader("Fotó", type=['jpg', 'png'])

            if st.button("🚀 KÜLDÉS", use_container_width=True) and item and photo:
                tid = f"TID-{int(time.time())}"
                oid = next_order_id()
                global_data["active_trades"][tid] = {
                    "order_id": oid,
                    "sender": current_user, "receiver": target, "item": item, "description": desc,
                    "price": price, "status": "WAITING", "state_text": "Csomagolás alatt...",
                    "photo": photo, "start_loc": start, "end_loc": end,
                    "eta_time": datetime.now() + timedelta(minutes=5),
                    "payment_method": None,
                    "confirm_requested": False,
                    "confirmed": False,
                    "signature": None
                }
                send_message(target,
                    f"😺 {current_user.capitalize()} küldött neked egy ajánlatot! • {oid} • Termék: {item} • Ár: {price+990} Cam",
                    "info")
                st.markdown("<script>playCatSound('send')</script>", unsafe_allow_html=True)
                st.success(f"🐾 Elküldve! Order: {oid}")
                st.rerun()

        with col_prev:
            st.markdown(f"""
            <div class="rev-card">
                <div class="rev-label">Összesítő</div>
                <div style="margin-top:12px;">
                    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1);">
                        <span style="color:#aaa">Termék ár</span>
                        <span style="font-weight:600">{price if 'price' in dir() else '...'} Cam</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1);">
                        <span style="color:#aaa">Szállítás</span>
                        <span style="font-weight:600">990 Cam</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:12px 0;margin-top:4px;">
                        <span style="color:white;font-weight:700">ÖSSZESEN</span>
                        <span style="color:#43e97b;font-weight:800;font-size:18px;">{(price if 'price' in dir() else 0)+990} Cam</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==================== TAB 2: BEJÖVŐ & AKTÍV ====================
with menu[1]:
    # --- BEJÖVŐ AJÁNLATOK (WAITING) ---
    reqs = {tid: t for tid, t in global_data["active_trades"].items()
            if t['receiver'] == current_user and t['status'] == "WAITING"}

    if reqs:
        st.markdown("### 📩 Bejövő ajánlatok")
        for tid, t in reqs.items():
            with st.container(border=True):
                ca, cb = st.columns([3, 1])
                with ca:
                    st.markdown(f"""
                    <div>
                        <span style='font-size:18px;font-weight:700;'>📦 {t['item']}</span>
                        <span class='pill pill-waiting' style='margin-left:8px;'>VÁRAKOZIK</span><br>
                        <span style='color:#888;font-size:13px;'>Feladó: {t['sender'].capitalize()} • {t['start_loc']} → {t['end_loc']}</span><br>
                        <span style='color:#888;font-size:13px;'>Order: {t.get('order_id','?')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with cb:
                    cost = t["price"] + 990
                    st.markdown(f"**{cost} Cam**")

                # FIZETÉSI MÓD VÁLASZTÁS
                st.markdown("#### 💳 Fizetési mód")
                pay_col1, pay_col2 = st.columns(2)
                with pay_col1:
                    if st.button(f"💳 Kártyával ({cost} Cam)", key=f"card_{tid}", use_container_width=True):
                        if global_data["balances"][current_user] >= cost:
                            global_data["balances"][current_user] -= cost
                            global_data["balances"][t["sender"]] += (t["price"] + 495)
                            t["status"] = "ACCEPTED"
                            t["payment_method"] = "💳 Kártya"
                            t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            send_message(t['sender'],
                                f"😸 {current_user.capitalize()} elfogadta az ajánlatodat! • {t.get('order_id','?')} • Fizetés: Kártyával • {cost} Cam levonva",
                                "info")
                            send_message(current_user,
                                f"✅ Sikeresen fizettél! • {t.get('order_id','?')} • {cost} Cam levonva kártyáról 💳",
                                "info")
                            st.markdown("<script>playCatSound('receive')</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.error("Nincs elég egyenleg! 😿")

                with pay_col2:
                    if st.button(f"📲 NFC ({cost} Cam)", key=f"nfc_{tid}", use_container_width=True):
                        st.session_state[f"nfc_pending_{tid}"] = True

                # NFC FIZETÉSI ANIMÁCIÓ
                if st.session_state.get(f"nfc_pending_{tid}"):
                    st.markdown(f"""
                    <div class="payment-modal">
                        <div class="rev-label" style="color:#a8edea;">NFC FIZETÉS</div>
                        <div class="nfc-animation">📲</div>
                        <div style="color:white;font-size:18px;font-weight:700;margin:12px 0;">Tartsd a telefonod a terminálhoz</div>
                        <div style="color:#888;font-size:14px;">Összeg: <b style="color:#43e97b;">{cost} Cam</b></div>
                        <div style="color:#555;font-size:12px;margin-top:8px;">Order: {t.get('order_id','?')}</div>
                    </div>
                    <script>playCatSound('alert')</script>
                    """, unsafe_allow_html=True)
                    nfc_cols = st.columns(2)
                    if nfc_cols[0].button("✅ NFC Jóváhagyás", key=f"nfc_ok_{tid}", use_container_width=True):
                        if global_data["balances"][current_user] >= cost:
                            global_data["balances"][current_user] -= cost
                            global_data["balances"][t["sender"]] += (t["price"] + 495)
                            t["status"] = "ACCEPTED"
                            t["payment_method"] = "📲 NFC"
                            t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            del st.session_state[f"nfc_pending_{tid}"]
                            send_message(t['sender'],
                                f"😸 {current_user.capitalize()} elfogadta az ajánlatodat! • {t.get('order_id','?')} • Fizetés: NFC • {cost} Cam levonva",
                                "info")
                            send_message(current_user,
                                f"✅ NFC fizetés sikeres! • {t.get('order_id','?')} • {cost} Cam 📲",
                                "info")
                            st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.error("Nincs elég egyenleg! 😿")
                    if nfc_cols[1].button("❌ Mégse", key=f"nfc_cancel_{tid}", use_container_width=True):
                        del st.session_state[f"nfc_pending_{tid}"]
                        st.rerun()

    st.divider()

    # --- AKTÍV SZÁLLÍTÁSOK (ACCEPTED) ---
    active = {tid: t for tid, t in global_data["active_trades"].items() if t['status'] == "ACCEPTED"}
    if active:
        st.markdown("### 🚚 Aktív szállítások")

    for tid, t in active.items():
        with st.container(border=True):
            rem = (t["eta_time"] - datetime.now()).total_seconds()
            order_id = t.get('order_id', tid)

            # Header
            hcol1, hcol2 = st.columns([3, 1])
            with hcol1:
                st.markdown(f"""
                <div>
                    <span style='font-size:16px;font-weight:700;'>🚚 {t['item']}</span>
                    <span class='pill pill-accepted' style='margin-left:8px;'>ELFOGADVA</span><br>
                    <span style='color:#888;font-size:13px;'>{t['start_loc']} → {t['end_loc']} • {order_id}</span><br>
                    <span style='color:#888;font-size:13px;'>Feladó: {t['sender'].capitalize()} • Címzett: {t['receiver'].capitalize()}</span>
                </div>
                """, unsafe_allow_html=True)
            with hcol2:
                if rem > 0:
                    st.markdown(f"<div style='text-align:right;'><span style='font-size:24px;font-weight:800;color:#667eea;'>⏳ {int(rem//60):02d}:{int(rem%60):02d}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:right;'><span style='font-size:16px;font-weight:700;color:#ffc107;'>⏰ ETA lejárt – hamarosan!</span></div>", unsafe_allow_html=True)

            c_ctrl, c_info = st.columns(2)

            with c_ctrl:
                if t["sender"] == current_user:
                    states = ["Csomagolás alatt...", "Úton a reptérre", "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"]
                    new_s = st.selectbox("📍 Státusz frissítése", states,
                        index=states.index(t["state_text"]) if t["state_text"] in states else 0,
                        key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        old_s = t["state_text"]
                        t["state_text"] = new_s
                        send_message(t['receiver'],
                            f"🐾 {order_id} • Friss státusz: **{new_s}** (volt: {old_s})",
                            "info")
                        st.markdown("<script>playCatSound('send')</script>", unsafe_allow_html=True)
                        st.rerun()

                    with st.expander("⏱️ ETA módosítás"):
                        new_eta = st.number_input("Perc:", 1, 120, 5, key=f"eta_{tid}")
                        if st.button("🕐 Mentés", key=f"etab_{tid}"):
                            t["eta_time"] = datetime.now() + timedelta(minutes=new_eta)
                            # Ha volt már notifikálva, töröljük hogy újra küldhessen
                            global_data["eta_notified"].discard(tid)
                            send_message(t['receiver'],
                                f"⏱️ {order_id} • ETA frissítve: {new_eta} perc múlva érkezik!",
                                "info")
                            st.rerun()

                    # VISSZAIGAZOLÁS GOMB (felado nyomja)
                    if not t.get("confirm_requested") and not t.get("confirmed"):
                        if st.button(f"📋 Visszaigazolás kérése", key=f"conf_req_{tid}", use_container_width=True):
                            t["confirm_requested"] = True
                            send_message(t['receiver'],
                                f"✍️ {order_id} • {t['sender'].capitalize()} kéri a csomag visszaigazolását! Kérlek írd alá a digitális papírt! 🐾",
                                "alert")
                            st.markdown("<script>playCatSound('alert')</script>", unsafe_allow_html=True)
                            st.rerun()
                    elif t.get("confirm_requested") and not t.get("confirmed"):
                        st.info("⏳ Várakozás az aláírásra...")
                    elif t.get("confirmed"):
                        st.success(f"✅ Visszaigazolva! Aláírás: *{t.get('signature','')}*")

                else:
                    st.info(f"📍 Helyzet: {t['state_text']}")

            with c_info:
                # DIGITÁLIS PAPÍR ALÁÍRÁS (cimzettnek, ha kérték)
                if t['receiver'] == current_user and t.get("confirm_requested") and not t.get("confirmed"):
                    st.markdown("""
                    <div class="paper-sign">
                        <div style="text-align:center;font-size:18px;font-weight:700;margin-bottom:16px;position:relative;z-index:1;">
                            🐾 ÁTVÉTELI ELISMERVÉNY
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="position:relative;z-index:1;font-family:Georgia,serif;">
                            <p>Alulírott <b>{current_user.capitalize()}</b> igazolom, hogy a(z) <b>{t['item']}</b>
                            nevű küldeményt ({order_id}) a mai napon ({datetime.now().strftime('%Y.%m.%d')})
                            átvettem. A csomag épségben megérkezett.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    sig = st.text_input("✍️ Aláírásod (írd be a neved):", key=f"sig_{tid}", placeholder="pl. Peti...")
                    if st.button("🖊️ ALÁÍR & VISSZAIGAZOL", key=f"sign_{tid}", use_container_width=True):
                        if sig.strip():
                            t["confirmed"] = True
                            t["signature"] = sig.strip()
                            t["status"] = "DONE"
                            t["done_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            global_data["trade_history"].append(t.copy())
                            send_message(t['sender'],
                                f"😺 {order_id} • {current_user.capitalize()} aláírta az elismervényt és visszaigazolta az átvételt! Aláírás: *{sig}* 🎉",
                                "info")
                            send_message(current_user,
                                f"✅ {order_id} • Sikeres átvétel visszaigazolva! Ügylet lezárva. 🐾",
                                "info")
                            st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.warning("Kérlek írd be a neved az aláíráshoz! 😾")

                # Számla letöltés
                pdf = create_pdf(t, tid)
                st.download_button("📥 SZÁMLA PDF", data=pdf, file_name=f"szamla_{order_id}.pdf",
                                   key=f"p_{tid}", use_container_width=True)

# ==================== TAB 3: BANK ====================
with menu[2]:
    st.markdown("### 🏦 Tréd Bank")
    bal = global_data['balances'].get(current_user, 0)

    # Főkártya
    st.markdown(f"""
    <div class="rev-card" style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 40%,#0f3460 100%);min-height:180px;">
        <div class="rev-label">Tréd Főszámla</div>
        <div class="rev-balance" style="font-size:48px;margin:12px 0;">{bal:,} Cam</div>
        <div style="display:flex;gap:32px;margin-top:16px;">
            <div>
                <div class="rev-label">Tulajdonos</div>
                <div style="color:white;font-weight:600;margin-top:4px;">{current_user.capitalize()}</div>
            </div>
            <div>
                <div class="rev-label">Kártya típus</div>
                <div style="color:#a8edea;font-weight:600;margin-top:4px;">Tréd Premium 🐾</div>
            </div>
        </div>
        <div style="margin-top:16px;font-size:22px;letter-spacing:4px;color:rgba(255,255,255,0.4);">
            •••• •••• •••• {abs(hash(current_user)) % 9000 + 1000}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # NFC Terminál
    st.markdown("---")
    st.markdown("#### 📲 NFC Terminál")
    nfc_col1, nfc_col2 = st.columns(2)
    with nfc_col1:
        nfc_amount = st.number_input("Összeg (Cam)", min_value=1, value=100, key="nfc_direct_amount")
        nfc_target = st.selectbox("Kinek küldöd", [u for u in USERS if u != current_user], key="nfc_direct_target")
    with nfc_col2:
        st.markdown(f"""
        <div style="background:rgba(102,126,234,0.1);border-radius:16px;padding:20px;text-align:center;border:1px solid rgba(102,126,234,0.3);">
            <div class="nfc-animation" style="width:60px;height:60px;font-size:28px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2);">📲</div>
            <div style="color:#a8edea;font-size:13px;margin-top:8px;">NFC KÉSZ</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("📲 NFC Küldés", use_container_width=True, key="nfc_direct_send"):
        if global_data["balances"][current_user] >= nfc_amount:
            global_data["balances"][current_user] -= nfc_amount
            global_data["balances"][nfc_target] = global_data["balances"].get(nfc_target, 0) + nfc_amount
            send_message(nfc_target,
                f"📲 {current_user.capitalize()} NFC-n keresztül küldött neked {nfc_amount} Cam-et! 😸",
                "info")
            send_message(current_user,
                f"✅ NFC átutalás sikeres! {nfc_amount} Cam → {nfc_target.capitalize()} 📲",
                "info")
            st.markdown("<script>playCatSound('done')</script>", unsafe_allow_html=True)
            st.success(f"📲 Elküldve! {nfc_amount} Cam → {nfc_target.capitalize()}")
            st.rerun()
        else:
            st.error("Nincs elég egyenleg! 😿")

    # Egyenlegek táblázat
    st.markdown("---")
    st.markdown("#### 👥 Összes egyenleg")
    bal_data = [{"Felhasználó": u.capitalize(), "Egyenleg": f"{b:,} Cam",
                 "Online": "🟢" if u in online_now else "⚫"}
                for u, b in global_data["balances"].items()]
    st.dataframe(pd.DataFrame(bal_data), use_container_width=True, hide_index=True)

# ==================== TAB 4: HISTORY ====================
with menu[3]:
    st.markdown("### 📜 Lezárt ügyletek")
    done_trades = [t for t in global_data["active_trades"].values() if t['status'] == "DONE"]

    if not done_trades:
        st.info("Még nincs lezárt ügylet. 😴")
    else:
        for t in reversed(done_trades):
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"""
                    <div>
                        <span style='font-weight:700;font-size:15px;'>✅ {t['item']}</span>
                        <span class='pill pill-done' style='margin-left:8px;'>LEZÁRVA</span><br>
                        <span style='color:#888;font-size:12px;'>{t.get('order_id','?')} • {t['sender'].capitalize()} → {t['receiver'].capitalize()}</span><br>
                        <span style='color:#888;font-size:12px;'>{t['start_loc']} → {t['end_loc']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with h2:
                    st.markdown(f"<div style='text-align:right;color:#43e97b;font-weight:700;'>{t['price']+990} Cam</div>", unsafe_allow_html=True)
                    if t.get("signature"):
                        st.markdown(f"<div style='text-align:right;color:#888;font-size:12px;'>✍️ {t['signature']}</div>", unsafe_allow_html=True)

                pdf = create_pdf(t, t.get('order_id', 'N/A'))
                st.download_button("📥 Számla", data=pdf,
                    file_name=f"szamla_{t.get('order_id','ORD')}.pdf",
                    key=f"hist_pdf_{t.get('order_id',id(t))}", use_container_width=True)

time.sleep(3)
st.rerun()

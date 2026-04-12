import streamlit as st
import streamlit.components.v1 as components
import time
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import os

# ─────────────────────────────────────────────
# FIREBASE ADMIN
# ─────────────────────────────────────────────
_firebase_ok = False
try:
    import firebase_admin
    from firebase_admin import credentials, messaging as fb_messaging
    if not firebase_admin._apps:
        key_path = os.path.join(os.getcwd(), "cattrade-591fb-firebase-adminsdk-fbsvc-8cbfef732c.json")
        if not os.path.exists(key_path):
            key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "cattrade-591fb-firebase-adminsdk-fbsvc-8cbfef732c.json")
        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            _firebase_ok = True
        else:
            _firebase_ok = False
    else:
        _firebase_ok = True
except Exception:
    _firebase_ok = False

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Tréd 🐾", layout="wide",
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
FCM_VAPID = "VyDf5IEpIo2PmkQRQZPzU1jmBrMiO_MlQHAMa9zs6oo"
FCM_CONFIG = {
    "apiKey": "AIzaSyDZb9bdfMFfzBRKM7bMO7GbvIH5CutYZB0",
    "authDomain": "cattrade-591fb.firebaseapp.com",
    "projectId": "cattrade-591fb",
    "storageBucket": "cattrade-591fb.firebasestorage.app",
    "messagingSenderId": "168227931827",
    "appId": "1:168227931827:web:07fb9c3de0be56395252c6",
}
USERS = {
    "admin": "1234", "peti": "pisti77", "adel": "trade99",
    "kormuranusz": "kormicica", "ddnemet": "koficcica"
}
LOCATIONS = [
    "Budapest HUB", "Catánia", "London", "New York", "Codeland",
    "Catániai Félszigetek", "Nyauperth", "Macskatelep", "Tarantulai Fészkek"
]
STATES = [
    "Csomagolás alatt...", "Úton a reptérre",
    "A levegőben ✈️", "Kiszállítás alatt", "A kapu előtt 🚪"
]
BLOCKED_WORDS = [
    "nigger","nigga","neger","negro","faggot","retard",
    "kike","spic","chink","gook","tranny","cunt","slut","whore"
]

# ─────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────
@st.cache_resource
def get_global_data():
    return {
        "online_users": {},
        "active_trades": {},
        "balances": {
            "admin": 50000, "peti": 50000, "adel": 50000,
            "ddnemet": 50000, "kormuranusz": 50000
        },
        "messages": {},
        "eta_notified": set(),
        "order_counter": [1000],
        "bank_pins": {},
        "bank_sessions": {},
        "last_msg_count": {},
        "fcm_tokens": {},
        "nfc_pending": {},   # tid -> {amount, order_id, receiver} awaiting delivery payment
    }

gd = get_global_data()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def next_oid():
    gd["order_counter"][0] += 1
    return f"ORD-{gd['order_counter'][0]}"

def contains_blocked(txt):
    lo = txt.lower()
    return any(w in lo for w in BLOCKED_WORDS)

def send_msg(user, text, mtype="info"):
    gd["messages"].setdefault(user, []).append({
        "text": text, "type": mtype,
        "ts": datetime.now().strftime("%H:%M:%S"), "read": False
    })
    _send_fcm(user, "🐾 Tréd értesítés", text)

def _send_fcm(user, title, body):
    if not _firebase_ok:
        return
    token = gd["fcm_tokens"].get(user)
    if not token:
        return
    try:
        from firebase_admin import messaging as fb_messaging
        msg = fb_messaging.Message(
            notification=fb_messaging.Notification(title=title, body=body),
            token=token,
            android=fb_messaging.AndroidConfig(priority="high"),
            apns=fb_messaging.APNSConfig(
                payload=fb_messaging.APNSPayload(
                    aps=fb_messaging.Aps(sound="default")
                )
            )
        )
        fb_messaging.send(msg)
    except Exception:
        pass

def get_unread(user):
    return [m for m in gd["messages"].get(user, []) if not m["read"]]

def mark_read(user):
    for m in gd["messages"].get(user, []):
        m["read"] = True

# ─────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────
def create_pdf(t, tid):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    oid = t.get("order_id", tid)

    # ── header ──
    c.setFillColor(colors.HexColor("#0f3460"))
    c.rect(0, H-90, W, 90, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#667eea"))
    c.rect(0, H-90, 10, 90, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 28); c.setFillColor(colors.white)
    c.drawString(30, H-55, "TRÉD")
    c.setFont("Helvetica", 11); c.setFillColor(colors.HexColor("#a8edea"))
    c.drawString(30, H-72, "Kereskedési Platform")
    c.setFont("Helvetica-Bold", 20); c.setFillColor(colors.white)
    c.drawRightString(W-30, H-50, "SZÁMLA")
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#a8edea"))
    c.drawRightString(W-30, H-66, f"Order: {oid}")

    # ── info bar ──
    y = H - 115
    c.setFillColor(colors.HexColor("#f0f4ff"))
    c.rect(30, y-12, W-60, 44, fill=1, stroke=0)
    labels = ["Kiállítva", "Feladó", "Címzett", "Fizetési mód"]
    vals = [
        t.get("accepted_at", datetime.now().strftime("%Y-%m-%d %H:%M"))[:16],
        t["sender"].capitalize(), t["receiver"].capitalize(),
        t.get("payment_method", "–")
    ]
    xs = [40, 160, 290, 420]
    for lbl, val, x in zip(labels, vals, xs):
        c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.HexColor("#888"))
        c.drawString(x, y+18, lbl)
        c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#111"))
        c.drawString(x, y+4, str(val)[:20])

    # ── szállítási adatok ──
    y -= 36
    c.setFillColor(colors.HexColor("#667eea")); c.rect(30, y, W-60, 22, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(colors.white)
    c.drawString(40, y+6, "SZÁLLÍTÁSI ADATOK")
    rows_data = [
        ("Útvonal", f"{t.get('start_loc','?')}  →  {t.get('end_loc','?')}"),
        ("Termék neve", t.get("item", "–")),
        ("Leírás", (t.get("description", "–") or "–")[:65]),
        ("TID", tid),
    ]
    y -= 2
    for i, (lbl, val) in enumerate(rows_data):
        bg = colors.HexColor("#f7f9ff") if i % 2 == 0 else colors.white
        c.setFillColor(bg); c.rect(30, y-16, W-60, 20, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#555"))
        c.drawString(40, y-8, lbl+":")
        c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#111"))
        c.drawString(165, y-8, str(val))
        y -= 20

    # ── összesítő ──
    y -= 14
    c.setFillColor(colors.HexColor("#0f3460")); c.rect(30, y, W-60, 22, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(colors.white)
    c.drawString(40, y+6, "ÖSSZESÍTŐ")
    for i, (lbl, val) in enumerate([
        ("Termék ára", f"{t['price']:,} Cam"),
        ("Szállítási díj", "990 Cam")
    ]):
        bg = colors.HexColor("#f7f9ff") if i % 2 == 0 else colors.white
        y -= 20
        c.setFillColor(bg); c.rect(30, y, W-60, 20, fill=1, stroke=0)
        c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#333"))
        c.drawString(40, y+5, lbl)
        c.drawRightString(W-38, y+5, val)

    # ── total ──
    y -= 28
    c.setFillColor(colors.HexColor("#43e97b")); c.rect(30, y, W-60, 26, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#0a2a1a"))
    c.drawString(40, y+7, "VÉGÖSSZEG")
    c.drawRightString(W-38, y+7, f"{t['price']+990:,} Cam")

    # ── aláírás ──
    if t.get("signature"):
        y -= 40
        c.setFillColor(colors.HexColor("#fff8e7")); c.rect(30, y-8, W-60, 30, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor("#d4c5a0")); c.rect(30, y-8, W-60, 30, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#888"))
        c.drawString(40, y+14, "ÁTVÉTELI ALÁÍRÁS:")
        c.setFont("Helvetica", 12); c.setFillColor(colors.HexColor("#222"))
        c.drawString(190, y+14, t["signature"])

    # ── watermark ──
    if t.get("status") == "DONE":
        c.saveState()
        c.translate(W/2, H/2); c.rotate(32)
        c.setFont("Helvetica-Bold", 80)
        c.setFillColor(colors.HexColor("#43e97b"))
        c.setFillAlpha(0.06)
        c.drawCentredString(0, 0, "TELJESÍTVE")
        c.restoreState()

    # ── footer ──
    c.setFillColor(colors.HexColor("#1a1a2e")); c.rect(0, 0, W, 42, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#667eea")); c.rect(0, 0, 6, 42, fill=1, stroke=0)
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#aaa"))
    c.drawString(20, 26, "TRÉD Platform  •  Automatikusan generált számla  •  Minden jog fenntartva")
    c.drawRightString(W-20, 26, f"Generálva: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.setFillColor(colors.HexColor("#555"))
    c.drawString(20, 12, f"TID: {tid}")
    c.drawRightString(W-20, 12, f"Order: {oid}")
    c.save(); buf.seek(0)
    return buf

# ─────────────────────────────────────────────
# FCM via components iframe
# ─────────────────────────────────────────────
FCM_IFRAME_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js"></script>
</head>
<body style="margin:0;background:transparent;">
<script>
(async function() {{
  const config = {FCM_CONFIG};
  const vapid  = "{FCM_VAPID}";

  // Register SW inline via blob — no /static/ needed!
  const swCode = `
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');
firebase.initializeApp(${{JSON.stringify(config)}});
const messaging = firebase.messaging();
messaging.onBackgroundMessage(payload => {{
  self.registration.showNotification(
    payload.notification?.title || 'Tréd',
    {{ body: payload.notification?.body || '', icon: '/favicon.ico' }}
  );
}});
`;
  const blob = new Blob([swCode.replace('${{JSON.stringify(config)}}', JSON.stringify(config))], {{type:'text/javascript'}});
  const swUrl = URL.createObjectURL(blob);

  try {{
    if (!firebase.apps.length) firebase.initializeApp(config);
    const messaging = firebase.messaging();
    const reg = await navigator.serviceWorker.register(swUrl, {{scope:'/'}});
    await navigator.serviceWorker.ready;

    const perm = await Notification.requestPermission();
    if (perm !== 'granted') {{
      window.parent.postMessage({{type:'fcm_token', token:'DENIED'}}, '*');
      return;
    }}
    const token = await messaging.getToken({{ serviceWorkerRegistration: reg, vapidKey: vapid }});
    window.parent.postMessage({{type:'fcm_token', token: token}}, '*');

    messaging.onMessage(payload => {{
      window.parent.postMessage({{type:'fcm_fg', payload: payload}}, '*');
    }});
  }} catch(e) {{
    window.parent.postMessage({{type:'fcm_token', token:'ERROR:'+e.message}}, '*');
  }}
}})();
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────
# GLOBAL JS  (sound + vibrate + flash + NFC)
# ─────────────────────────────────────────────
JS_ALL = r"""
<script>
// Listen for FCM token from iframe
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'fcm_token') {
    const inp = document.querySelector('input[aria-label="fcm_input"]');
    if (inp) {
      inp.value = e.data.token;
      inp.dispatchEvent(new Event('input', {bubbles:true}));
    }
  }
  if (e.data && e.data.type === 'fcm_fg') {
    const p = e.data.payload;
    showToast('🐾 ' + (p.notification?.title||'Tréd'), p.notification?.body||'');
    fullAlert('receive');
  }
});

// ── Toast ────────────────────────────────────
function showToast(title, body) {
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;top:20px;right:20px;z-index:999999;background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:16px 20px;border-radius:16px;border:1px solid rgba(102,126,234,0.4);box-shadow:0 8px 32px rgba(0,0,0,0.5);max-width:320px;animation:toastIn 0.3s ease;font-family:Inter,sans-serif;';
  d.innerHTML = '<div style="font-weight:700;font-size:14px;margin-bottom:4px;">'+title+'</div><div style="font-size:12px;color:#aaa;">'+body+'</div>';
  document.body.appendChild(d);
  setTimeout(()=>{d.style.opacity='0';d.style.transition='opacity 0.4s';setTimeout(()=>d.remove(),400);}, 4000);
}

// ── Sounds ──────────────────────────────────
function playCatSound(type) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    const t = ctx.currentTime;
    if (type==='send') {
      osc.frequency.setValueAtTime(400,t); osc.frequency.linearRampToValueAtTime(800,t+0.2); osc.frequency.linearRampToValueAtTime(600,t+0.4);
      gain.gain.setValueAtTime(0.35,t); gain.gain.exponentialRampToValueAtTime(0.01,t+0.5);
      osc.start(t); osc.stop(t+0.5);
    } else if (type==='receive') {
      const o2=ctx.createOscillator(), g2=ctx.createGain(); o2.connect(g2); g2.connect(ctx.destination);
      osc.frequency.setValueAtTime(880,t); gain.gain.setValueAtTime(0.4,t); gain.gain.exponentialRampToValueAtTime(0.01,t+0.25); osc.start(t); osc.stop(t+0.25);
      o2.frequency.setValueAtTime(1100,t+0.3); g2.gain.setValueAtTime(0.4,t+0.3); g2.gain.exponentialRampToValueAtTime(0.01,t+0.55); o2.start(t+0.3); o2.stop(t+0.55);
    } else if (type==='alert') {
      osc.frequency.setValueAtTime(600,t); osc.frequency.linearRampToValueAtTime(1200,t+0.15); osc.frequency.setValueAtTime(600,t+0.25); osc.frequency.linearRampToValueAtTime(1200,t+0.4);
      gain.gain.setValueAtTime(0.4,t); gain.gain.exponentialRampToValueAtTime(0.01,t+0.5); osc.start(t); osc.stop(t+0.5);
    } else if (type==='done') {
      osc.frequency.setValueAtTime(500,t); osc.frequency.linearRampToValueAtTime(1000,t+0.2); osc.frequency.linearRampToValueAtTime(1500,t+0.4);
      gain.gain.setValueAtTime(0.35,t); gain.gain.exponentialRampToValueAtTime(0.01,t+0.5); osc.start(t); osc.stop(t+0.5);
    } else if (type==='nfc') {
      osc.frequency.setValueAtTime(300,t); osc.frequency.linearRampToValueAtTime(1400,t+0.25);
      gain.gain.setValueAtTime(0.35,t); gain.gain.exponentialRampToValueAtTime(0.01,t+0.35); osc.start(t); osc.stop(t+0.35);
    }
  } catch(e){}
}

function vibrate(p) { try { if(navigator.vibrate) navigator.vibrate(p); } catch(e){} }

function flashScreen(color) {
  const el = document.createElement('div');
  el.style.cssText='position:fixed;inset:0;z-index:99999;pointer-events:none;background:'+(color||'rgba(102,126,234,0.3)')+';transition:opacity 0.4s';
  document.body.appendChild(el);
  setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),400);},200);
}

function fullAlert(type) {
  if      (type==='receive') { playCatSound('receive'); vibrate([200,100,200,100,400]); flashScreen('rgba(67,233,123,0.25)'); }
  else if (type==='alert')   { playCatSound('alert');   vibrate([300,100,300,100,300]); flashScreen('rgba(245,87,108,0.3)'); }
  else if (type==='done')    { playCatSound('done');    vibrate([100,50,100,50,600]);   flashScreen('rgba(67,233,123,0.2)'); }
  else if (type==='nfc')     { playCatSound('nfc');     vibrate([50,30,50,30,200]);     flashScreen('rgba(102,126,234,0.4)'); }
  else                       { playCatSound(type);      vibrate([150]); }
}

// ── Title blink ──────────────────────────────
let _origTitle = document.title, _ti = null;
function alertTitle(msg) {
  if (_ti) return; let on=true;
  _ti = setInterval(()=>{ document.title = on?('🔔 '+msg):_origTitle; on=!on; }, 900);
}
function clearTitleAlert() {
  if(_ti){clearInterval(_ti);_ti=null;} document.title=_origTitle;
}

// ── NFC ──────────────────────────────────────
// Uses plain TEXT records — avoids the vnd.android.nfc intent bug completely.
window._nfcAbort = null;

async function startNFCWrite(amount, orderId, statusId) {
  const el = document.getElementById('nfc-status-'+statusId);
  const set=(m,c)=>{ if(el){el.innerHTML=m; if(c)el.style.color=c;} };
  if(!('NDEFReader' in window)){ set('❌ Web NFC: Chrome Android 89+ szükséges','#f5576c'); return; }
  try {
    set('🔐 NFC engedély kérése...','#ffc107');
    const ndef = new NDEFReader();
    const payload = JSON.stringify({tred:1, amount:amount, order:orderId, ts:Date.now()});
    await ndef.write({ records:[{ recordType:"text", data:payload, lang:"hu" }] });
    set('✅ NFC adat kiírva! Tartsd a fizető telefonját közel...','#43e97b');
    fullAlert('nfc');
  } catch(e) {
    if(e.name==='NotAllowedError') set('🔒 NFC engedély megtagadva','#f5576c');
    else set('❌ '+e.message,'#f5576c');
  }
}

async function startNFCRead(statusId, confirmBtnId) {
  const el = document.getElementById('nfc-status-'+statusId);
  const set=(m,c)=>{ if(el){el.innerHTML=m; if(c)el.style.color=c;} };
  if(!('NDEFReader' in window)){ set('❌ Web NFC: Chrome Android 89+ szükséges','#f5576c'); return; }
  try {
    set('📡 NFC olvasó aktív – érintsd a postás telefonját...','#ffc107');
    const ndef = new NDEFReader();
    if(window._nfcAbort) window._nfcAbort.abort();
    window._nfcAbort = new AbortController();
    await ndef.scan({signal:window._nfcAbort.signal});
    ndef.addEventListener('reading',({message})=>{
      try {
        const rec = message.records[0];
        const txt = new TextDecoder(rec.encoding||'utf-8').decode(rec.data);
        const data = JSON.parse(txt);
        if(data.tred){
          set('✅ Tréd NFC fizetés! Összeg: '+data.amount+' Cam','#43e97b');
          fullAlert('receive');
          const btn = document.getElementById(confirmBtnId);
          if(btn) setTimeout(()=>btn.click(),600);
        } else { set('⚠️ Ismeretlen NFC adat','#ffc107'); }
      } catch(e2){ set('⚠️ Hiba: '+e2.message,'#ffc107'); }
    });
    ndef.addEventListener('readingerror',()=>set('⚠️ NFC olvasási hiba','#ffc107'));
  } catch(e){
    if(e.name==='AbortError'){ set('⏹️ Leállítva','#888'); return; }
    if(e.name==='NotAllowedError'){ set('🔒 NFC engedély megtagadva','#f5576c'); return; }
    set('❌ '+e.message,'#f5576c');
  }
}

function stopNFC(statusId) {
  if(window._nfcAbort){window._nfcAbort.abort();window._nfcAbort=null;}
  const el=document.getElementById('nfc-status-'+(statusId||''));
  if(el) el.innerHTML='⏹️ NFC leállítva.';
}

// style inject for toast animation
const s=document.createElement('style');
s.textContent='@keyframes toastIn{from{transform:translateX(100%);opacity:0}to{transform:none;opacity:1}}';
document.head.appendChild(s);
</script>
"""

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── reset & dark bg ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, .block-container {
    background: transparent !important;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #050b18 0%, #0a1628 40%, #0d1f3c 70%, #0a1020 100%) !important;
    min-height: 100vh;
}

/* ── sidebar dark ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0d1630 100%) !important;
    border-right: 1px solid rgba(102,126,234,0.15) !important;
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

/* ── hide clutter ── */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
button[title="View menu"] { display: none !important; visibility: hidden !important; }

/* ── fix double arrow in expander ── */
[data-testid="stExpander"] summary > div > p { display: none !important; }
details > summary::-webkit-details-marker { display: none !important; }

/* ── fix double label on file uploader ── */
[data-testid="stFileUploader"] > label:nth-of-type(2) { display: none !important; }

/* ── global font ── */
* { font-family: 'Inter', sans-serif !important; }

/* ── containers ── */
[data-testid="stVerticalBlock"] > div { background: transparent !important; }
[data-testid="element-container"] { background: transparent !important; }

/* ── inputs dark ── */
input, textarea, select,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.06) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
}
input::placeholder, textarea::placeholder { color: rgba(255,255,255,0.3) !important; }
label { color: rgba(255,255,255,0.7) !important; }

/* ── tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: rgba(255,255,255,0.5) !important;
    font-weight: 600;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(102,126,234,0.2) !important;
    color: #a8edea !important;
    border-radius: 10px;
}

/* ── st.container(border=True) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 16px !important;
}

/* ── buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.4) !important;
}

/* ── download button ── */
[data-testid="stDownloadButton"] > button {
    background: rgba(102,126,234,0.15) !important;
    color: #a8edea !important;
    border: 1px solid rgba(102,126,234,0.3) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* ── markdown text ── */
p, li, span, div { color: rgba(255,255,255,0.85); }
h1,h2,h3,h4 { color: white !important; }

/* ── st.info / warning / success ── */
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* ── dataframe ── */
[data-testid="stDataFrame"] { background: rgba(255,255,255,0.03) !important; border-radius: 12px !important; }

/* ── hide FCM hidden input ── */
div:has(> div > div > input[aria-label="fcm_input"]) { display:none !important; height:0 !important; overflow:hidden !important; }

/* ══ COMPONENTS ════════════════════════════ */

.rev-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px; padding: 24px; color: white; margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08);
}
.rev-balance {
    font-size: 44px; font-weight: 900;
    background: linear-gradient(90deg, #fff 0%, #a8edea 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -2px;
}
.rev-label {
    font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.5);
    text-transform: uppercase; letter-spacing: 2px;
}
.nfc-pulse {
    width: 90px; height: 90px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    font-size: 40px; margin: 0 auto 16px;
    animation: nfcPulse 1.2s ease-in-out infinite;
}
@keyframes nfcPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(102,126,234,0.8); transform:scale(1); }
    50%      { box-shadow: 0 0 0 22px rgba(102,126,234,0); transform:scale(1.06); }
}
.payment-modal {
    background: linear-gradient(180deg, #1a1a2e, #0a0f1e);
    border-radius: 24px; padding: 28px; border: 1px solid rgba(255,255,255,0.1);
    text-align: center; margin: 10px 0;
}
.msg-bubble {
    background: rgba(102,126,234,0.1); border-left: 3px solid #667eea;
    border-radius: 0 10px 10px 0; padding: 9px 14px; margin: 6px 0; font-size: 12px; color: #ddd;
}
.msg-bubble.alert { background: rgba(245,87,108,0.1); border-left-color: #f5576c; }
.paper-sign {
    background: linear-gradient(145deg,#fefefe,#f0efe6); border: 2px solid #d4c5a0;
    border-radius: 4px; padding: 28px; color: #2c2c2c;
    box-shadow: 4px 4px 12px rgba(0,0,0,0.2); position: relative; overflow: hidden;
}
.paper-sign::before {
    content:''; position:absolute; inset:0;
    background: repeating-linear-gradient(transparent,transparent 27px,#e0d8c8 27px,#e0d8c8 28px);
    opacity:0.4; pointer-events:none;
}
.pill { display:inline-block; padding:3px 10px; border-radius:20px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; }
.pill-waiting  { background:rgba(255,193,7,.2);   color:#ffc107; }
.pill-accepted { background:rgba(102,126,234,.2); color:#667eea; }
.pill-done     { background:rgba(67,233,123,.2);  color:#43e97b; }
.tx-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); }
.pos { color:#43e97b; font-weight:700; }
.neg { color:#f5576c; font-weight:700; }
.eta-timer { text-align:right; font-size:28px; font-weight:900; color:#667eea; }
.eta-soon  { text-align:right; color:#ffc107; font-weight:700; font-size:14px; }
.notif-banner {
    background: linear-gradient(90deg,#f5576c,#c0392b); border-radius:12px;
    padding:12px 16px; margin:8px 0; color:white; font-weight:700; font-size:14px;
    animation: bannerPulse 0.9s ease-in-out infinite alternate;
}
@keyframes bannerPulse {
    from { box-shadow: 0 0 0 0 rgba(245,87,108,0.6); }
    to   { box-shadow: 0 0 20px 4px rgba(245,87,108,0.25); }
}

/* ══ ANIMÁLT BEJELENTKEZÉS HÁTTÉR ══════════ */
.login-bg {
    position: fixed; inset: 0; z-index: 0; overflow: hidden;
    background: linear-gradient(180deg, #020b1a 0%, #041025 30%, #071830 60%, #020b1a 100%);
}
.stars-layer {
    position: absolute; inset: 0;
    background-image:
        radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.9) 0%, transparent 100%),
        radial-gradient(1px 1px at 25% 8%,  rgba(255,255,255,0.7) 0%, transparent 100%),
        radial-gradient(2px 2px at 40% 20%, rgba(168,237,234,0.8) 0%, transparent 100%),
        radial-gradient(1px 1px at 55% 5%,  rgba(255,255,255,0.6) 0%, transparent 100%),
        radial-gradient(1px 1px at 70% 12%, rgba(255,255,255,0.9) 0%, transparent 100%),
        radial-gradient(2px 2px at 85% 7%,  rgba(168,237,234,0.7) 0%, transparent 100%),
        radial-gradient(1px 1px at 92% 18%, rgba(255,255,255,0.8) 0%, transparent 100%),
        radial-gradient(1px 1px at 15% 35%, rgba(255,255,255,0.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 30% 42%, rgba(255,255,255,0.7) 0%, transparent 100%),
        radial-gradient(2px 2px at 48% 30%, rgba(168,237,234,0.6) 0%, transparent 100%),
        radial-gradient(1px 1px at 62% 38%, rgba(255,255,255,0.8) 0%, transparent 100%),
        radial-gradient(1px 1px at 78% 25%, rgba(255,255,255,0.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 5%  50%, rgba(255,255,255,0.6) 0%, transparent 100%),
        radial-gradient(1px 1px at 90% 45%, rgba(255,255,255,0.7) 0%, transparent 100%),
        radial-gradient(2px 2px at 35% 55%, rgba(168,237,234,0.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 20% 60%, rgba(255,255,255,0.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 72% 58%, rgba(255,255,255,0.6) 0%, transparent 100%);
    animation: starsTwinkle 4s ease-in-out infinite alternate;
}
@keyframes starsTwinkle {
    0%   { opacity: 0.6; }
    50%  { opacity: 1.0; }
    100% { opacity: 0.7; }
}

/* Mountains SVG injected via HTML, but we also do a CSS version for the gradient */
.moon {
    position: absolute; width: 80px; height: 80px; border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #fff9e6, #ffeaa0);
    top: 8%; right: 15%;
    box-shadow: 0 0 40px 12px rgba(255,230,100,0.25), 0 0 80px 30px rgba(255,220,80,0.1);
    animation: moonGlow 3s ease-in-out infinite alternate;
}
@keyframes moonGlow {
    from { box-shadow: 0 0 40px 12px rgba(255,230,100,0.2), 0 0 80px 30px rgba(255,220,80,0.08); }
    to   { box-shadow: 0 0 50px 18px rgba(255,230,100,0.35), 0 0 100px 40px rgba(255,220,80,0.15); }
}

/* Cats walking across the bottom */
.cat-walk {
    position: absolute; bottom: 22%; font-size: 28px;
    animation: catWalk 18s linear infinite;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.6));
}
.cat-walk:nth-child(1) { animation-delay: 0s;    bottom: 20%; font-size: 24px; }
.cat-walk:nth-child(2) { animation-delay: 6s;    bottom: 23%; font-size: 20px; animation-duration:22s; }
.cat-walk:nth-child(3) { animation-delay: 12s;   bottom: 21%; font-size: 26px; animation-duration:16s; }
@keyframes catWalk {
    0%   { left: -80px;  transform: scaleX(1); }
    49%  { left: 110%;   transform: scaleX(1); }
    50%  { left: 110%;   transform: scaleX(-1); }
    99%  { left: -80px;  transform: scaleX(-1); }
    100% { left: -80px;  transform: scaleX(1); }
}

/* shooting stars */
.shoot {
    position: absolute; width: 2px; height: 2px; border-radius: 50%;
    background: white;
    animation: shoot 6s linear infinite;
    opacity: 0;
}
.shoot:nth-child(1) { top:10%; left:20%; animation-delay:0s; }
.shoot:nth-child(2) { top:5%;  left:60%; animation-delay:2s; animation-duration:8s; }
.shoot:nth-child(3) { top:15%; left:80%; animation-delay:4.5s; animation-duration:5s; }
@keyframes shoot {
    0%   { opacity:0; transform:translate(0,0) rotate(-30deg); }
    5%   { opacity:1; }
    20%  { opacity:0; transform:translate(200px,120px) rotate(-30deg); }
    100% { opacity:0; transform:translate(200px,120px) rotate(-30deg); }
}
.shoot::after {
    content:''; position:absolute; top:0; left:-80px; width:80px; height:1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8));
    transform: rotate(0deg);
}

.login-card-wrap {
    position: relative; z-index: 10;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
}
</style>
"""

# ─────────────────────────────────────────────
# INJECT CSS + JS
# ─────────────────────────────────────────────
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(JS_ALL, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FCM IFRAME (always injected, hidden)
# ─────────────────────────────────────────────
components.html(FCM_IFRAME_HTML, height=0, scrolling=False)

# FCM token pickup via hidden input
fcm_token_val = st.text_input("x", key="fcm_input", label_visibility="collapsed")
if fcm_token_val and "username" in st.session_state:
    cu = st.session_state.username
    if fcm_token_val.startswith("ERROR:") or fcm_token_val == "DENIED":
        st.session_state["fcm_err"] = fcm_token_val
    else:
        gd["fcm_tokens"][cu] = fcm_token_val
        st.session_state.pop("fcm_err", None)

# ─────────────────────────────────────────────
# LOGIN – animated
# ─────────────────────────────────────────────
if "username" not in st.session_state:
    # Full-screen animated background
    st.markdown("""
    <div class="login-bg">
        <div class="stars-layer"></div>
        <!-- Shooting stars -->
        <div class="shoot"></div>
        <div class="shoot"></div>
        <div class="shoot"></div>
        <!-- Moon -->
        <div class="moon"></div>
        <!-- SVG Mountains -->
        <svg style="position:absolute;bottom:0;left:0;width:100%;height:45%;" viewBox="0 0 1440 320" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
            <!-- back mountains - deep blue -->
            <polygon points="0,320 0,200 120,80 240,160 360,60 480,140 600,40 720,120 840,50 960,130 1080,45 1200,110 1320,55 1440,100 1440,320" fill="#0a1628" opacity="0.9"/>
            <!-- mid mountains - slightly lighter -->
            <polygon points="0,320 0,240 100,140 200,200 320,110 420,180 540,100 660,170 780,90 900,160 1020,105 1140,165 1260,95 1380,150 1440,120 1440,320" fill="#0d1f3c" opacity="0.95"/>
            <!-- front mountains - darkest -->
            <polygon points="0,320 0,280 80,200 180,250 280,180 380,240 480,170 580,230 680,160 780,220 880,165 980,225 1080,170 1180,230 1280,180 1380,240 1440,200 1440,320" fill="#071020" opacity="1"/>
            <!-- snow caps -->
            <polygon points="120,80 100,110 140,110" fill="rgba(255,255,255,0.15)"/>
            <polygon points="360,60 340,90 380,90" fill="rgba(255,255,255,0.15)"/>
            <polygon points="600,40 578,72 622,72" fill="rgba(255,255,255,0.2)"/>
            <polygon points="840,50 818,82 862,82" fill="rgba(255,255,255,0.15)"/>
            <polygon points="1080,45 1058,78 1102,78" fill="rgba(255,255,255,0.18)"/>
            <polygon points="1320,55 1298,88 1342,88" fill="rgba(255,255,255,0.12)"/>
        </svg>
        <!-- Walking cats -->
        <div class="cat-walk">🐈</div>
        <div class="cat-walk">😺</div>
        <div class="cat-walk">🐈‍⬛</div>
    </div>
    """, unsafe_allow_html=True)

    # Login card centered
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("""
        <div style="
            background: rgba(10,15,30,0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102,126,234,0.3);
            border-radius: 28px;
            padding: 48px 40px 40px;
            text-align: center;
            box-shadow: 0 24px 64px rgba(0,0,0,0.6);
            margin-top: 60px;
        ">
            <div style="font-size:72px;margin-bottom:12px;animation:catBounce 2s ease-in-out infinite;">😼</div>
            <h1 style="font-size:42px;font-weight:900;background:linear-gradient(90deg,#667eea,#a8edea,#f5576c);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 6px;">TRÉD</h1>
            <p style="color:rgba(255,255,255,0.4);font-size:13px;margin-bottom:36px;letter-spacing:2px;">MACSKÁS KERESKEDÉSI PLATFORM</p>
        </div>
        <style>
        @keyframes catBounce {
            0%,100% { transform: translateY(0) rotate(-5deg); }
            50%      { transform: translateY(-12px) rotate(5deg); }
        }
        </style>
        """, unsafe_allow_html=True)

        u = st.text_input("Felhasználónév", key="lu", placeholder="felhasznalonev").lower().strip()
        p = st.text_input("Jelszó", type="password", key="lp", placeholder="••••••••")
        if st.button("🐾 Belépés", use_container_width=True, key="login_btn"):
            if u in USERS and USERS[u] == p:
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Hibás adatok! 🙀")
    st.stop()

# ─────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────
current_user = st.session_state.username
gd["online_users"][current_user] = time.time()
online_now = [u for u, ts in gd["online_users"].items() if time.time() - ts < 10]

# ── New message alert trigger ──
prev_count = gd["last_msg_count"].get(current_user, 0)
cur_unreads = get_unread(current_user)
cur_count = len(cur_unreads)
if cur_count > prev_count:
    latest = cur_unreads[-1]
    atype = "alert" if latest["type"] == "alert" else "receive"
    st.markdown(f"<script>fullAlert('{atype}'); alertTitle('ÚJ ÉRTESÍTÉS');</script>", unsafe_allow_html=True)
    gd["last_msg_count"][current_user] = cur_count

# ── ETA lejárat ──
for tid, t in list(gd["active_trades"].items()):
    if t["status"] == "ACCEPTED":
        rem = (t["eta_time"] - datetime.now()).total_seconds()
        if rem <= 0 and tid not in gd["eta_notified"]:
            gd["eta_notified"].add(tid)
            oid = t.get("order_id", tid)
            send_msg(t["sender"],   f"🕐 {oid} – ETA lejárt! A csomag hamarosan megérkezik. 🐾", "alert")
            send_msg(t["receiver"], f"🕐 {oid} – ETA lejárt! A csomagod hamarosan ott lesz! 🐾", "alert")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    bal = gd["balances"].get(current_user, 0)
    fcm_ok = current_user in gd["fcm_tokens"]

    st.markdown(f"""
    <div class="rev-card">
        <div class="rev-label">Főszámla</div>
        <div class="rev-balance">{bal:,} Cam</div>
        <div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:13px;color:rgba(255,255,255,0.55);">👤 {current_user.capitalize()}</span>
            <span style="font-size:10px;color:{'#43e97b' if fcm_ok else '#f5576c'};">
                {'🔔 FCM OK' if fcm_ok else '🔕 FCM –'}
            </span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:12px;color:#555;margin-bottom:10px;'>🟢 Online: {', '.join(online_now)}</div>",
        unsafe_allow_html=True
    )

    if cur_unreads:
        st.markdown(
            f'<div class="notif-banner">🔔 {len(cur_unreads)} új értesítés!</div>',
            unsafe_allow_html=True
        )
        for m in cur_unreads[-6:]:
            icon = "🙀" if m["type"] == "alert" else "😺"
            css  = "alert" if m["type"] == "alert" else ""
            st.markdown(
                f'<div class="msg-bubble {css}">{icon} <b>{m["ts"]}</b><br>{m["text"]}</div>',
                unsafe_allow_html=True
            )
        if st.button("✓ Olvasottnak jelöl", use_container_width=True, key="mark_read"):
            mark_read(current_user)
            gd["last_msg_count"][current_user] = 0
            st.markdown("<script>clearTitleAlert();</script>", unsafe_allow_html=True)
            st.rerun()
    else:
        st.markdown(
            "<div style='color:#444;font-size:12px;'>Nincs új értesítés 😸</div>",
            unsafe_allow_html=True
        )

    st.divider()

    my_done = [
        t for t in gd["active_trades"].values()
        if t["status"] == "DONE" and current_user in (t["sender"], t["receiver"])
    ]
    if my_done:
        st.markdown("#### 📊 Saját tranzakciók")
        for t in my_done[-5:]:
            amt  = -(t["price"] + 990) if t["receiver"] == current_user else (t["price"] + 495)
            cls  = "pos" if amt > 0 else "neg"
            sign = "+" if amt > 0 else ""
            st.markdown(f"""
            <div class="tx-row">
                <div>
                    <div style='font-size:12px;font-weight:600;color:white;'>{t['item']}</div>
                    <div style='font-size:10px;color:#555;'>{t.get('order_id','?')}</div>
                </div>
                <div class="{cls}">{sign}{amt:,} Cam</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Kijelentkezés", use_container_width=True, key="logout"):
        del st.session_state.username
        gd["bank_sessions"].pop(current_user, None)
        st.rerun()

# ─────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────
menu = st.tabs(["🚀 KÜLDÉS", "📋 BEJÖVŐ & AKTÍV", "🏦 BANK", "📜 HISTORY"])

# ════════════════════════════════════════════
# TAB 1 – KÜLDÉS
# ════════════════════════════════════════════
with menu[0]:
    targets = [u for u in online_now if u != current_user]
    if not targets:
        st.info("Nincs online partner. Várj egy macskát... 😴")
    else:
        st.markdown("### 📦 Új szállítási ajánlat")
        col_form, col_prev = st.columns([3, 2])

        with col_form:
            target = st.selectbox("Címzett", targets, key="send_target")

            # Helyszínek - külön sorok, nincs egymásba csúszás
            lc1, lc2 = st.columns(2)
            with lc1:
                start = st.selectbox("Indulás", LOCATIONS, key="send_start")
            with lc2:
                end = st.selectbox("Célállomás", LOCATIONS, key="send_end")

            # Ár + terméknév külön sorban
            pc1, pc2 = st.columns(2)
            with pc1:
                price = st.number_input("Ár (Cam)", min_value=0, value=1000, key="send_price")
            with pc2:
                item = st.text_input("Termék neve", key="send_item", placeholder="pl. Arany lánc")

            desc = st.text_area("Termék leírása (opcionális)", key="send_desc", placeholder="...")

            # Fotó - saját label, label_visibility=collapsed hogy ne duplikáljon
            st.markdown("**📷 Fotó feltöltése**")
            photo = st.file_uploader(
                "foto_upload", type=["jpg", "jpeg", "png"],
                key="send_photo", label_visibility="collapsed"
            )
            if photo:
                st.image(photo, caption="Előnézet", use_container_width=True)

            if st.button("🚀 KÜLDÉS", use_container_width=True, key="send_btn"):
                if not item.strip():
                    st.warning("Add meg a termék nevét! 😾")
                elif contains_blocked(item):
                    st.error("⛔ A termék neve nem megfelelő tartalmat tartalmaz!")
                elif not photo:
                    st.warning("Tölts fel egy fotót! 😾")
                elif start == end:
                    st.warning("Az indulás és a célállomás nem lehet ugyanaz! 😾")
                else:
                    tid = f"TID-{int(time.time())}"
                    oid = next_oid()
                    gd["active_trades"][tid] = {
                        "order_id":        oid,
                        "sender":          current_user,
                        "receiver":        target,
                        "item":            item.strip(),
                        "description":     desc,
                        "price":           price,
                        "status":          "WAITING",
                        "state_text":      "Csomagolás alatt...",
                        "photo":           photo,
                        "start_loc":       start,
                        "end_loc":         end,
                        "eta_time":        datetime.now() + timedelta(minutes=5),
                        "payment_method":  None,
                        "confirm_requested": False,
                        "confirmed":       False,
                        "signature":       None,
                        "accepted_at":     None,
                        "delivery_paid":   False,   # NFC fizetés a kézbesítéskor
                    }
                    send_msg(
                        target,
                        f"😺 {current_user.capitalize()} küldött neked egy ajánlatot! "
                        f"• {oid} • {item.strip()} • {price + 990:,} Cam",
                        "info"
                    )
                    st.markdown("<script>fullAlert('send');</script>", unsafe_allow_html=True)
                    st.success(f"🐾 Elküldve! Order: {oid}")
                    st.rerun()

        with col_prev:
            p_val = st.session_state.get("send_price", 1000)
            st.markdown(f"""
            <div class="rev-card">
                <div class="rev-label">Összesítő előnézet</div>
                <div class="tx-row">
                    <span style="color:#aaa;">Termék ár</span>
                    <span style="font-weight:600;color:white;">{p_val:,} Cam</span>
                </div>
                <div class="tx-row">
                    <span style="color:#aaa;">Szállítás</span>
                    <span style="font-weight:600;color:white;">990 Cam</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:16px 0 4px;">
                    <span style="color:white;font-weight:800;font-size:16px;">ÖSSZESEN</span>
                    <span class="pos" style="font-size:22px;">{p_val + 990:,} Cam</span>
                </div>
                <div style="margin-top:16px;padding:10px;background:rgba(255,193,7,0.08);border-radius:10px;font-size:12px;color:#aaa;">
                    ℹ️ A fizetés a kézbesítéskor történik — NFC vagy kártya.
                </div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════
# TAB 2 – BEJÖVŐ & AKTÍV
# ════════════════════════════════════════════
with menu[1]:

    # ─── BEJÖVŐ AJÁNLATOK (WAITING) ──────────────────────────────────
    reqs = {
        tid: t for tid, t in gd["active_trades"].items()
        if t["receiver"] == current_user and t["status"] == "WAITING"
    }
    if reqs:
        st.markdown("### 📩 Bejövő ajánlatok")

    for tid, t in reqs.items():
        with st.container(border=True):
            oid  = t.get("order_id", tid)
            cost = t["price"] + 990
            ia, ib = st.columns([3, 1])
            with ia:
                st.markdown(f"""
                <div>
                  <span style='font-size:17px;font-weight:700;color:white;'>📦 {t['item']}</span>
                  <span class='pill pill-waiting' style='margin-left:8px;'>VÁRAKOZIK</span><br>
                  <span style='color:#888;font-size:12px;'>Feladó: {t['sender'].capitalize()} • {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>Order: {oid}</span>
                </div>""", unsafe_allow_html=True)
            with ib:
                st.markdown(
                    f"<div style='text-align:right;font-size:18px;font-weight:800;color:#f5576c;'>{cost:,} Cam</div>",
                    unsafe_allow_html=True
                )

            # ── Elfogadás: NEM kér fizetési módot itt, csak elfogadja ──
            # Fizetés a kézbesítéskor fog történni (NFC a kapunál)
            st.markdown("""
            <div style="background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);
                border-radius:10px;padding:10px;font-size:12px;color:#aaa;margin:8px 0;">
                ℹ️ Az ajánlat elfogadásával <b>NEM vonódik le egyenleg</b>.<br>
                A fizetés a kézbesítéskor történik – a postás kapunál NFC-vel vagy kártyával.
            </div>""", unsafe_allow_html=True)

            acc_col1, acc_col2 = st.columns(2)
            with acc_col1:
                if st.button(f"✅ Elfogadom az ajánlatot", key=f"acc_{tid}", use_container_width=True):
                    t["status"]     = "ACCEPTED"
                    t["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    send_msg(
                        t["sender"],
                        f"😸 {current_user.capitalize()} elfogadta az ajánlatodat! • {oid} • "
                        f"Fizetés kézbesítéskor: {cost:,} Cam",
                        "info"
                    )
                    send_msg(
                        current_user,
                        f"✅ {oid} • Ajánlat elfogadva! Fizetés a kézbesítéskor: {cost:,} Cam",
                        "info"
                    )
                    st.markdown("<script>fullAlert('receive');</script>", unsafe_allow_html=True)
                    st.rerun()
            with acc_col2:
                if st.button(f"❌ Elutasítom", key=f"rej_{tid}", use_container_width=True):
                    gd["active_trades"].pop(tid, None)
                    send_msg(t["sender"], f"😿 {current_user.capitalize()} elutasította az ajánlatodat. • {oid}", "alert")
                    st.rerun()

    st.divider()

    # ─── AKTÍV SZÁLLÍTÁSOK (ACCEPTED) ────────────────────────────────
    active = {
        tid: t for tid, t in gd["active_trades"].items()
        if t["status"] == "ACCEPTED"
    }
    if active:
        st.markdown("### 🚚 Aktív szállítások")

    for tid, t in active.items():
        with st.container(border=True):
            oid = t.get("order_id", tid)
            rem = (t["eta_time"] - datetime.now()).total_seconds()
            cost = t["price"] + 990

            # ── fejléc ──
            hc1, hc2 = st.columns([3, 1])
            with hc1:
                st.markdown(f"""
                <div>
                  <span style='font-size:15px;font-weight:700;color:white;'>🚚 {t['item']}</span>
                  <span class='pill pill-accepted' style='margin-left:8px;'>AKTÍV</span><br>
                  <span style='color:#888;font-size:12px;'>{oid} • {t['start_loc']} → {t['end_loc']}</span><br>
                  <span style='color:#888;font-size:12px;'>{t['sender'].capitalize()} → {t['receiver'].capitalize()}</span>
                </div>""", unsafe_allow_html=True)
            with hc2:
                if rem > 0:
                    st.markdown(
                        f"<div class='eta-timer'>⏳ {int(rem//60):02d}:{int(rem%60):02d}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<div class='eta-soon'>⏰ Hamarosan megérkezik!</div>",
                        unsafe_allow_html=True
                    )

            ctrl_col, info_col = st.columns(2)

            with ctrl_col:
                if t["sender"] == current_user:
                    # ── Státusz frissítés ──
                    cur_idx = STATES.index(t["state_text"]) if t["state_text"] in STATES else 0
                    new_s = st.selectbox("📍 Státusz", STATES, index=cur_idx, key=f"s_{tid}")
                    if new_s != t["state_text"]:
                        old = t["state_text"]; t["state_text"] = new_s
                        send_msg(
                            t["receiver"],
                            f"🐾 {oid} • Státusz frissítve: {new_s} (volt: {old})",
                            "info"
                        )
                        st.markdown("<script>fullAlert('send');</script>", unsafe_allow_html=True)
                        st.rerun()

                    # ── ETA módosítás (expander nélkül – arrow bug elkerülése) ──
                    st.markdown("**⏱️ ETA módosítás**")
                    ec1, ec2 = st.columns([3, 1])
                    with ec1:
                        new_eta = st.number_input(
                            "Perc", min_value=1, max_value=120, value=5,
                            key=f"eta_{tid}", label_visibility="collapsed"
                        )
                    with ec2:
                        if st.button("🕐", key=f"etab_{tid}", use_container_width=True):
                            t["eta_time"] = datetime.now() + timedelta(minutes=new_eta)
                            gd["eta_notified"].discard(tid)
                            send_msg(t["receiver"], f"⏱️ {oid} • ETA frissítve: {new_eta} perc!", "info")
                            st.rerun()

                    st.divider()

                    # ── KÉZBESÍTÉSI NFC FIZETÉS (feladó/postás indítja) ──
                    st.markdown("**💰 Kézbesítési fizetés**")
                    if not t.get("delivery_paid"):
                        st.markdown(f"""
                        <div style="background:rgba(67,233,123,0.08);border:1px solid rgba(67,233,123,0.2);
                            border-radius:10px;padding:10px;font-size:12px;color:#aaa;margin-bottom:8px;">
                            🚪 A csomag megérkezett a kapuhoz? Indítsd el az NFC terminált,
                            hogy {t['receiver'].capitalize()} ki tudjon fizetni.
                        </div>""", unsafe_allow_html=True)

                        nfc_id_delivery = f"delivery_{tid}"
                        confirm_id_delivery = f"nfc-confirm-delivery-{tid}"

                        st.markdown(f"""
                        <div class="payment-modal" style="padding:20px;">
                            <div class="nfc-pulse" style="width:70px;height:70px;font-size:32px;">💸</div>
                            <div style="color:white;font-size:15px;font-weight:700;">Kézbesítési NFC terminál</div>
                            <div style="color:#888;font-size:12px;margin:6px 0;">Összeg: <b style="color:#43e97b;">{cost:,} Cam</b></div>
                            <div id="nfc-status-{nfc_id_delivery}" style="font-size:12px;color:#667eea;margin-top:8px;">Válassz ↓</div>
                        </div>""", unsafe_allow_html=True)

                        dn1, dn2, dn3, dn4 = st.columns(4)
                        with dn1:
                            if st.button("✏️ NFC Írás", key=f"nfc_write_del_{tid}", use_container_width=True):
                                st.markdown(
                                    f"<script>startNFCWrite({cost},'{oid}','{nfc_id_delivery}');</script>",
                                    unsafe_allow_html=True
                                )
                        with dn2:
                            if st.button("📡 NFC Olv.", key=f"nfc_read_del_{tid}", use_container_width=True):
                                st.markdown(
                                    f"<script>startNFCRead('{nfc_id_delivery}','{confirm_id_delivery}');</script>",
                                    unsafe_allow_html=True
                                )
                        with dn3:
                            # Auto-clicked by JS on NFC tap
                            nfc_del_ok = st.button("✅ NFC OK", key=f"nfc_del_ok_{tid}", use_container_width=True)
                            st.markdown(f'<span id="{confirm_id_delivery}" style="display:none"></span>', unsafe_allow_html=True)
                            if nfc_del_ok:
                                if gd["balances"].get(t["receiver"], 0) >= cost:
                                    gd["balances"][t["receiver"]]  = gd["balances"].get(t["receiver"], 0) - cost
                                    gd["balances"][current_user]   = gd["balances"].get(current_user, 0) + t["price"] + 495
                                    t["payment_method"] = "📲 NFC (kézbesítés)"
                                    t["delivery_paid"]  = True
                                    send_msg(
                                        t["receiver"],
                                        f"📲 {oid} • NFC kézbesítési fizetés sikeres! {cost:,} Cam levonva.",
                                        "info"
                                    )
                                    send_msg(
                                        current_user,
                                        f"💰 {oid} • Fizetés beérkezett: {t['price']+495:,} Cam NFC-vel 🎉",
                                        "info"
                                    )
                                    st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.error(f"{t['receiver'].capitalize()} egyenlege nem elegendő! 😿")
                        with dn4:
                            if st.button("💳 Kártya", key=f"card_del_{tid}", use_container_width=True):
                                if gd["balances"].get(t["receiver"], 0) >= cost:
                                    gd["balances"][t["receiver"]]  = gd["balances"].get(t["receiver"], 0) - cost
                                    gd["balances"][current_user]   = gd["balances"].get(current_user, 0) + t["price"] + 495
                                    t["payment_method"] = "💳 Kártya (kézbesítés)"
                                    t["delivery_paid"]  = True
                                    send_msg(
                                        t["receiver"],
                                        f"💳 {oid} • Kártyás kézbesítési fizetés sikeres! {cost:,} Cam levonva.",
                                        "info"
                                    )
                                    send_msg(
                                        current_user,
                                        f"💰 {oid} • Kártyás fizetés beérkezett: {t['price']+495:,} Cam 🎉",
                                        "info"
                                    )
                                    st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.error(f"{t['receiver'].capitalize()} egyenlege nem elegendő! 😿")
                    else:
                        st.success(f"✅ Fizetés teljesítve! ({t.get('payment_method','–')})")

                    # ── Visszaigazolás kérése ──
                    st.divider()
                    if not t.get("confirm_requested") and not t.get("confirmed"):
                        if st.button("📋 Visszaigazolás kérése", key=f"creq_{tid}", use_container_width=True):
                            t["confirm_requested"] = True
                            send_msg(
                                t["receiver"],
                                f"✍️ {oid} • {t['sender'].capitalize()} kéri az aláírásodat! 🐾",
                                "alert"
                            )
                            st.markdown("<script>fullAlert('alert');</script>", unsafe_allow_html=True)
                            st.rerun()
                    elif t.get("confirm_requested") and not t.get("confirmed"):
                        st.info("⏳ Várakozás az aláírásra...")
                    elif t.get("confirmed"):
                        st.success(f"✅ Aláírva: *{t.get('signature','')}*")

                else:
                    # ── Cimzett nézete ──
                    st.info(f"📍 {t['state_text']}")

                    if t.get("delivery_paid"):
                        pm = t.get("payment_method", "–")
                        st.success(f"✅ Fizetés teljesítve! ({pm})")
                    elif rem <= 0:
                        st.markdown(f"""
                        <div style="background:rgba(67,233,123,0.08);border:1px solid rgba(67,233,123,0.3);
                            border-radius:10px;padding:12px;font-size:13px;color:#aaa;margin-top:8px;">
                            🚪 A csomag hamarosan megérkezik! A postás fogja elindítani az NFC terminált
                            a fizetéshez — tartsd készen a telefonod ({cost:,} Cam).
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);
                            border-radius:10px;padding:10px;font-size:12px;color:#aaa;margin-top:8px;">
                            💡 Fizetés ({cost:,} Cam) a kézbesítéskor – NFC vagy kártya.
                        </div>""", unsafe_allow_html=True)

            with info_col:
                # ── Digitális papír aláírás ──
                if t["receiver"] == current_user and t.get("confirm_requested") and not t.get("confirmed"):
                    st.markdown(f"""
                    <div class="paper-sign">
                      <div style="text-align:center;font-size:15px;font-weight:700;margin-bottom:12px;
                          position:relative;z-index:1;color:#2c2c2c;">
                          🐾 ÁTVÉTELI ELISMERVÉNY
                      </div>
                      <div style="position:relative;z-index:1;line-height:1.9;font-size:13px;color:#2c2c2c;">
                          Alulírott <b>{current_user.capitalize()}</b> igazolom, hogy a(z)
                          <b>{t['item']}</b> nevű küldeményt ({oid}) a mai napon
                          ({datetime.now().strftime('%Y.%m.%d')}) átvettem. A csomag épségben megérkezett.
                      </div>
                    </div>""", unsafe_allow_html=True)
                    sig = st.text_input("✍️ Aláírás:", key=f"sig_{tid}", placeholder="pl. Peti...")
                    if st.button("🖊️ ALÁÍR & VISSZAIGAZOL", key=f"sign_{tid}", use_container_width=True):
                        if sig.strip():
                            t.update({
                                "confirmed":  True,
                                "signature":  sig.strip(),
                                "status":     "DONE",
                                "done_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            send_msg(
                                t["sender"],
                                f"😺 {oid} • {current_user.capitalize()} aláírta az elismervényt! ✍️ {sig} 🎉",
                                "info"
                            )
                            send_msg(current_user, f"✅ {oid} • Ügylet sikeresen lezárva! 🐾", "info")
                            st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.warning("Írd be a neved az aláíráshoz! 😾")

                # ── Számla PDF ──
                pdf = create_pdf(t, tid)
                st.download_button(
                    "📥 SZÁMLA PDF", data=pdf,
                    file_name=f"szamla_{oid}.pdf",
                    key=f"pdf_{tid}", use_container_width=True
                )

# ════════════════════════════════════════════
# TAB 3 – BANK (4 jegyű PIN)
# ════════════════════════════════════════════
with menu[2]:
    bank_in = gd["bank_sessions"].get(current_user, False)

    if not bank_in:
        st.markdown("### 🏦 Tréd Bank")
        has_pin = current_user in gd["bank_pins"]
        _, cc, _ = st.columns([1, 1.5, 1])
        with cc:
            st.markdown(f"""
            <div class="rev-card" style="text-align:center;">
                <div style="font-size:56px;margin-bottom:10px;">🔐</div>
                <div class="rev-label">{"BANK PIN BELÉPÉS" if has_pin else "ELSŐ BELÉPÉS – PIN BEÁLLÍTÁSA"}</div>
                <div style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:6px;">
                    {"Add meg a 4 jegyű bank PIN-kódodat" if has_pin else "Válassz egy 4 számjegyű PIN-kódot"}
                </div>
            </div>""", unsafe_allow_html=True)

            if not has_pin:
                p1 = st.text_input("Új PIN (4 szám)", type="password", max_chars=4, key="bp1", placeholder="••••")
                p2 = st.text_input("PIN megerősítése", type="password", max_chars=4, key="bp2", placeholder="••••")
                if st.button("🔐 PIN beállítása", use_container_width=True, key="set_pin"):
                    if len(p1) == 4 and p1.isdigit() and p1 == p2:
                        gd["bank_pins"][current_user] = p1
                        st.success("✅ PIN beállítva! Most beléphet.")
                        st.rerun()
                    else:
                        st.error("4 számjegy kell, és egyezzen! 😾")
            else:
                entered = st.text_input(
                    "PIN", type="password", max_chars=4, key="blp",
                    label_visibility="collapsed", placeholder="••••"
                )
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🏦 Belépés", use_container_width=True, key="bank_login"):
                        if entered == gd["bank_pins"].get(current_user):
                            gd["bank_sessions"][current_user] = True
                            st.rerun()
                        else:
                            st.error("Hibás PIN! 😿")
                with b2:
                    if st.button("PIN törlése", use_container_width=True, key="del_pin"):
                        gd["bank_pins"].pop(current_user, None)
                        st.rerun()
    else:
        bal = gd["balances"].get(current_user, 0)
        bh1, bh2 = st.columns([5, 1])
        with bh1:
            st.markdown("### 🏦 Tréd Bank")
        with bh2:
            if st.button("🔒 Zár", use_container_width=True, key="bank_lock"):
                gd["bank_sessions"][current_user] = False
                st.rerun()

        card_num = f"{abs(hash(current_user)) % 9000 + 1000}"
        st.markdown(f"""
        <div class="rev-card" style="min-height:210px;position:relative;overflow:hidden;">
            <div style="position:absolute;right:-40px;top:-40px;width:200px;height:200px;
                border-radius:50%;background:rgba(255,255,255,0.03);"></div>
            <div style="position:absolute;right:60px;bottom:-20px;width:120px;height:120px;
                border-radius:50%;background:rgba(102,126,234,0.05);"></div>
            <div class="rev-label">Tréd Premium Számla</div>
            <div class="rev-balance" style="font-size:46px;margin:14px 0 10px;">{bal:,} Cam</div>
            <div style="display:flex;gap:40px;margin-top:8px;">
                <div>
                    <div class="rev-label">Tulajdonos</div>
                    <div style="color:white;font-weight:600;margin-top:4px;">{current_user.capitalize()}</div>
                </div>
                <div>
                    <div class="rev-label">Típus</div>
                    <div style="color:#a8edea;font-weight:600;margin-top:4px;">Premium 🐾</div>
                </div>
                <div>
                    <div class="rev-label">FCM Push</div>
                    <div style="color:{'#43e97b' if current_user in gd['fcm_tokens'] else '#f5576c'};font-weight:600;margin-top:4px;">
                        {'Aktív ✓' if current_user in gd['fcm_tokens'] else 'Inaktív ✗'}
                    </div>
                </div>
            </div>
            <div style="margin-top:18px;font-size:20px;letter-spacing:6px;color:rgba(255,255,255,0.25);">
                •••• •••• •••• {card_num}
            </div>
        </div>""", unsafe_allow_html=True)

        bt = st.tabs(["📲 NFC Terminál", "💳 Kártya küldés", "📊 Kimutatás"])

        with bt[0]:
            st.markdown("#### 📲 NFC Terminál")
            st.markdown("""
            <div style="background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);
                border-radius:12px;padding:14px;font-size:13px;color:#aaa;margin-bottom:16px;">
                <b>Postás / terminál oldal:</b> Add meg az összeget → <b>NFC Írás</b> → tartsd a fizető telefonját<br>
                <b>Fizető oldal:</b> <b>NFC Olvasás</b> → érintsd a terminált → automatikus jóváhagyás<br>
                <b>Nincs NFC?</b> Kézi Jóváhagyás gombbal is működik<br><br>
                ✅ <b>vnd.android hiba javítva</b> — plain TEXT NDEF rekordot írunk, nem URL-t.
            </div>""", unsafe_allow_html=True)

            tc1, tc2 = st.columns(2)
            nfc_amt  = tc1.number_input("Összeg (Cam)", min_value=1, value=500, key="nfc_bank_amount")
            nfc_to   = tc2.selectbox("Fizető fél", [u for u in USERS if u != current_user], key="nfc_bank_to")
            nfc_oid  = st.text_input("Order ID (opcionális)", placeholder="ORD-...", key="nfc_bank_oid")
            nfc_ref  = nfc_oid.strip() if nfc_oid.strip() else "BANK"
            nb_id    = f"bank_{current_user}"
            nb_cid   = f"nfc-confirm-bank-{current_user}"

            st.markdown(f"""
            <div class="payment-modal">
                <div class="nfc-pulse">📲</div>
                <div style="color:white;font-size:16px;font-weight:700;">NFC Terminál</div>
                <div style="color:#888;font-size:13px;margin:8px 0;">
                    Összeg: <b style="color:#43e97b;">{nfc_amt:,} Cam</b>
                    • Fizető: <b style="color:#a8edea;">{nfc_to.capitalize()}</b>
                </div>
                <div id="nfc-status-{nb_id}" style="color:#667eea;font-size:13px;margin-top:10px;">Várakozás...</div>
            </div>""", unsafe_allow_html=True)

            bn1, bn2, bn3, bn4 = st.columns(4)
            with bn1:
                if st.button("✏️ NFC Írás", use_container_width=True, key="nfc_write_bank"):
                    st.markdown(f"<script>startNFCWrite({nfc_amt},'{nfc_ref}','{nb_id}');</script>",
                                unsafe_allow_html=True)
            with bn2:
                if st.button("📡 NFC Olvasás", use_container_width=True, key="nfc_read_bank"):
                    st.markdown(f"<script>startNFCRead('{nb_id}','{nb_cid}');</script>",
                                unsafe_allow_html=True)
            with bn3:
                bank_ok = st.button("✅ Jóváhagyás", use_container_width=True, key="nfc_bank_ok")
                st.markdown(f'<span id="{nb_cid}" style="display:none"></span>', unsafe_allow_html=True)
                if bank_ok:
                    if gd["balances"].get(nfc_to, 0) >= nfc_amt:
                        gd["balances"][nfc_to]       = gd["balances"].get(nfc_to, 0) - nfc_amt
                        gd["balances"][current_user] = gd["balances"].get(current_user, 0) + nfc_amt
                        send_msg(nfc_to, f"📲 NFC: {nfc_amt:,} Cam levonva → {current_user.capitalize()}", "info")
                        send_msg(current_user, f"✅ NFC beérkezett: {nfc_amt:,} Cam ← {nfc_to.capitalize()}", "info")
                        st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                        st.success(f"✅ {nfc_amt:,} Cam beérkezett!")
                        st.rerun()
                    else:
                        st.error("A fizető félnek nincs elég egyenlege! 😿")
            with bn4:
                if st.button("⏹️ Stop", use_container_width=True, key="nfc_stop_bank"):
                    st.markdown(f"<script>stopNFC('{nb_id}');</script>", unsafe_allow_html=True)

        with bt[1]:
            st.markdown("#### 💳 Kártya küldés")
            ka, kb = st.columns(2)
            k_to   = ka.selectbox("Kinek", [u for u in USERS if u != current_user], key="k_to")
            k_amt  = kb.number_input("Összeg (Cam)", min_value=1, value=200, key="k_amt")
            k_note = st.text_input("Megjegyzés (opcionális)", key="k_note")
            if st.button("💳 Küldés", use_container_width=True, key="k_send"):
                if gd["balances"].get(current_user, 0) >= k_amt:
                    gd["balances"][current_user] -= k_amt
                    gd["balances"][k_to] = gd["balances"].get(k_to, 0) + k_amt
                    note_txt = f" • {k_note}" if k_note else ""
                    send_msg(k_to, f"💳 {current_user.capitalize()} küldött {k_amt:,} Cam-et{note_txt}", "info")
                    send_msg(current_user, f"✅ {k_amt:,} Cam elküldve → {k_to.capitalize()}{note_txt}", "info")
                    st.markdown("<script>fullAlert('done');</script>", unsafe_allow_html=True)
                    st.success(f"✅ Elküldve! {k_amt:,} Cam → {k_to.capitalize()}")
                    st.rerun()
                else:
                    st.error("Nincs elég egyenleg! 😿")

        with bt[2]:
            st.markdown("#### 📊 Saját kimutatás")
            my_trades = [
                t for t in gd["active_trades"].values()
                if current_user in (t["sender"], t["receiver"])
            ]
            if not my_trades:
                st.info("Még nincs tranzakció.")
            else:
                rows = []
                for t in my_trades:
                    is_recv = t["receiver"] == current_user
                    if t["status"] == "DONE" or t.get("delivery_paid"):
                        amt = -(t["price"] + 990) if is_recv else (t["price"] + 495)
                    else:
                        amt = 0  # még nem fizetett
                    rows.append({
                        "Order":   t.get("order_id", "?"),
                        "Termék":  t["item"],
                        "Partner": t["sender"].capitalize() if is_recv else t["receiver"].capitalize(),
                        "Összeg":  f"{'+' if amt > 0 else ''}{amt:,} Cam" if amt != 0 else "– (folyamatban)",
                        "Státusz": t["status"],
                        "Fizetés": t.get("payment_method", "– (kézbesítéskor)")
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════
# TAB 4 – HISTORY
# ════════════════════════════════════════════
with menu[3]:
    st.markdown("### 📜 Lezárt ügyletek")
    done = [t for t in gd["active_trades"].values() if t["status"] == "DONE"]

    if not done:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#444;">
            <div style="font-size:56px;margin-bottom:16px;">😴</div>
            <div style="font-size:16px;">Még nincs lezárt ügylet.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for t in reversed(done):
            oid = t.get("order_id", "?")
            with st.container(border=True):
                hh1, hh2 = st.columns([4, 1])
                with hh1:
                    sig_html = (
                        f"<br><span style='color:#888;font-size:12px;'>✍️ {t['signature']}</span>"
                        if t.get("signature") else ""
                    )
                    st.markdown(f"""
                    <div>
                      <span style='font-weight:700;color:white;'>✅ {t['item']}</span>
                      <span class='pill pill-done' style='margin-left:8px;'>LEZÁRVA</span><br>
                      <span style='color:#888;font-size:12px;'>{oid} • {t['sender'].capitalize()} → {t['receiver'].capitalize()}</span><br>
                      <span style='color:#888;font-size:12px;'>{t['start_loc']} → {t['end_loc']} • {t.get('payment_method','–')}</span>
                      {sig_html}
                    </div>""", unsafe_allow_html=True)
                with hh2:
                    st.markdown(
                        f"<div style='text-align:right;color:#43e97b;font-weight:800;font-size:18px;'>"
                        f"{t['price']+990:,} Cam</div>",
                        unsafe_allow_html=True
                    )
                pdf = create_pdf(t, oid)
                st.download_button(
                    "📥 Számla PDF", data=pdf,
                    file_name=f"szamla_{oid}.pdf",
                    key=f"hist_{oid}_{id(t)}",
                    use_container_width=True
                )

# ─────────────────────────────────────────────
# AUTO REFRESH (3 mp)
# ─────────────────────────────────────────────
time.sleep(3)
st.rerun()

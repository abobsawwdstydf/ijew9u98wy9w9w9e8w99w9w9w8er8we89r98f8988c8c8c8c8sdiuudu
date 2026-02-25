import http.server, socketserver, threading, time, hashlib, json, os, sqlite3, secrets, urllib.request, urllib.error, sys
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlparse

try:
    import psycopg2
except:
    os.system('pip install psycopg2-binary -q')
    import psycopg2

PORT = int(os.environ.get("PORT", 48328))
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = "dh_runbotime.db"
DB_LOCK = threading.Lock()
conn = None

def get_db():
    global conn
    if conn is None:
        if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
            try:
                conn = psycopg2.connect(DATABASE_URL)
                conn.autocommit = True
            except:
                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        else:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    c = get_db().cursor()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS deploys(id SERIAL PRIMARY KEY, user_id INTEGER, url TEXT, interval INTEGER, status INTEGER DEFAULT 1, pings INTEGER DEFAULT 0, last_ping INTEGER, next_ping INTEGER, system_flag INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS sessions(id SERIAL PRIMARY KEY, token TEXT UNIQUE, user_id INTEGER, created INTEGER)")
    except:
        c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS deploys(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, url TEXT, interval INTEGER, status INTEGER DEFAULT 1, pings INTEGER DEFAULT 0, last_ping INTEGER, next_ping INTEGER, system_flag INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE, user_id INTEGER, created INTEGER)")
    try:
        c.execute("SELECT COUNT(*) FROM deploys WHERE system_flag = 1")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO deploys(user_id, url, interval, status, next_ping, system_flag) VALUES(0, 'https://example.com', 420, 1, %s, 1)", (int(time.time()) + 420,))
    except:
        pass
    get_db().commit()

def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

def create_session(uid):
    token = secrets.token_hex(32)
    c = get_db().cursor()
    try: c.execute("INSERT INTO sessions(token, user_id, created) VALUES(%s, %s, %s)", (token, uid, int(time.time())))
    except: c.execute("INSERT INTO sessions(token, user_id, created) VALUES(?, ?, ?)", (token, uid, int(time.time())))
    get_db().commit()
    return token

def check_session(token):
    c = get_db().cursor()
    try: c.execute("SELECT user_id FROM sessions WHERE token=%s", (token,))
    except: c.execute("SELECT user_id FROM sessions WHERE token=?", (token,))
    r = c.fetchone()
    return r[0] if r else None

def delete_session(token):
    c = get_db().cursor()
    try: c.execute("DELETE FROM sessions WHERE token=%s", (token,))
    except: c.execute("DELETE FROM sessions WHERE token=?", (token,))
    get_db().commit()

def validate_url(url):
    if not url or len(url) > 500: return False
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and p.netloc
    except: return False

CSS = "*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh;overflow-x:hidden}body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background-image:linear-gradient(rgba(138,43,226,0.08) 1px,transparent 1px),linear-gradient(90deg,rgba(138,43,226,0.08) 1px,transparent 1px);background-size:40px 40px,40px 40px;animation:gridPulse 4s ease-in-out infinite;pointer-events:none;z-index:-1}@keyframes gridPulse{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(2px,2px) scale(1.01)}50%{transform:translate(0,0) scale(1)}75%{transform:translate(-2px,-2px) scale(0.99)}}.nav{background:rgba(26,10,42,0.95);padding:15px 30px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #4a1a6b;backdrop-filter:blur(10px);position:sticky;top:0;z-index:100;box-shadow:0 2px 20px rgba(138,43,226,0.3)}.nav h1{font-size:1.5rem;color:#00ff88;text-shadow:0 0 20px rgba(0,255,136,0.5);cursor:pointer;transition:0.3s}.nav h1:hover{transform:scale(1.05)}.nav a{color:#888;text-decoration:none;margin-left:20px;transition:0.3s;position:relative}.nav a:hover{color:#8a2be2}.nav a::after{content:'';position:absolute;bottom:-5px;left:0;width:0;height:2px;background:linear-gradient(90deg,#8a2be2,#00ff88);transition:0.3s}.nav a:hover::after{width:100%}.container{max-width:1200px;margin:0 auto;padding:30px}h2{margin-bottom:20px;background:linear-gradient(135deg,#8a2be2,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 20px rgba(138,43,226,0.5)}h3{margin-bottom:15px;color:#8a2be2}.btn{display:inline-block;padding:12px 30px;margin:10px;background:linear-gradient(135deg,#8a2be2,#9d4edd);color:#fff;text-decoration:none;border-radius:25px;font-weight:bold;cursor:pointer;border:none;transition:all 0.3s;box-shadow:0 4px 15px rgba(138,43,226,0.4)}.btn:hover{transform:translateY(-3px);box-shadow:0 8px 25px rgba(138,43,226,0.6);background:linear-gradient(135deg,#9d4edd,#8a2be2)}.btn:active{transform:translateY(-1px)}.btn-danger{background:linear-gradient(135deg,#ff4444,#cc3333);box-shadow:0 4px 15px rgba(255,68,68,0.3)}.btn-danger:hover{box-shadow:0 8px 25px rgba(255,68,68,0.5)}.btn-small{padding:8px 16px;margin:2px;border-radius:15px;font-size:0.9rem}.form{background:rgba(26,10,42,0.9);padding:40px;border-radius:20px;width:100%;max-width:400px;box-shadow:0 10px 40px rgba(138,43,226,0.2);backdrop-filter:blur(10px);border:1px solid rgba(138,43,226,0.3)}input,select{width:100%;padding:15px;margin-bottom:15px;background:rgba(42,20,58,0.5);border:1px solid #4a1a6b;color:#e0e0e0;border-radius:12px;transition:all 0.3s;font-size:1rem}input:focus,select:focus{outline:none;border-color:#8a2be2;box-shadow:0 0 20px rgba(138,43,226,0.4);transform:translateX(5px)}input::placeholder{color:#666}.link{display:block;text-align:center;margin-top:20px;color:#888;text-decoration:none;transition:0.3s}.link:hover{color:#8a2be2}table{width:100%;border-collapse:separate;border-spacing:0 10px}td{padding:15px;background:rgba(26,10,42,0.6);border-radius:10px;transition:all 0.3s;border:1px solid rgba(138,43,226,0.1)}td:hover{background:rgba(42,20,58,0.8);transform:scale(1.01);border-color:#8a2be2}th{padding:15px;color:#8a2be2;text-align:left;font-weight:500}.hidden{display:none;opacity:0;transition:opacity 0.3s}.center{display:flex;align-items:center;justify-content:center;min-height:100vh}.hero{text-align:center;max-width:700px;padding:40px;animation:fadeIn 0.8s ease}.typewriter{font-size:3.5rem;margin-bottom:25px;display:inline-block;min-height:70px}.typewriter span{background:linear-gradient(90deg,#8a2be2,#00ff88,#8a2be2);background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 30px rgba(138,43,226,0.5);animation:shine 2s linear infinite,glow 3s ease-in-out infinite}.typewriter span::after{content:'▋';position:absolute;margin-left:5px;animation:blink 0.8s infinite;color:#8a2be2}@keyframes shine{to{background-position:200% center}}@keyframes glow{0%,100%{text-shadow:0 0 20px rgba(138,43,226,0.5),0 0 30px rgba(138,43,226,0.3)}50%{text-shadow:0 0 40px rgba(138,43,226,0.8),0 0 60px rgba(138,43,226,0.5),0 0 80px rgba(0,255,136,0.3)}}@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}.hero p{color:#aaa;margin-bottom:30px;font-size:1.1rem;animation:slideUp 0.8s ease 0.5s both}.tabs{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.tab{padding:12px 25px;background:rgba(42,20,58,0.5);border:none;color:#888;cursor:pointer;border-radius:25px;transition:all 0.3s;font-size:1rem}.tab:hover{background:rgba(138,43,226,0.2);color:#8a2be2}.tab.active{background:linear-gradient(135deg,#8a2be2,#9d4edd);color:#fff;box-shadow:0 4px 15px rgba(138,43,226,0.4)}.content{background:rgba(26,10,42,0.7);padding:30px;border-radius:20px;backdrop-filter:blur(10px);border:1px solid rgba(138,43,226,0.2);animation:fadeIn 0.5s ease}.status-active{color:#00ff88;text-shadow:0 0 10px rgba(0,255,136,0.5)}.status-inactive{color:#ff4444;text-shadow:0 0 10px rgba(255,68,68,0.5)}.countdown{font-family:'Consolas',monospace;color:#8a2be2;background:rgba(138,43,226,0.1);padding:5px 10px;border-radius:8px}@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}@keyframes slideUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}.toast{position:fixed;bottom:30px;right:30px;padding:15px 25px;background:linear-gradient(135deg,#8a2be2,#9d4edd);color:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(138,43,226,0.4);animation:slideIn 0.3s ease,slideOut 0.3s ease 2.7s both;z-index:1000}@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}@keyframes slideOut{from{transform:translateX(0);opacity:1}to{transform:translateX(100%);opacity:0}}.loading{display:inline-block;width:20px;height:20px;border:2px solid rgba(138,43,226,0.3);border-radius:50%;border-top-color:#8a2be2;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.card{background:rgba(26,10,42,0.6);border-radius:15px;padding:20px;margin-bottom:15px;transition:all 0.3s;border:1px solid rgba(138,43,226,0.2)}.card:hover{transform:translateY(-5px);box-shadow:0 10px 30px rgba(138,43,226,0.2);border-color:#8a2be2}.stat{display:inline-block;margin-right:20px}.stat-value{font-size:1.5rem;color:#8a2be2;font-weight:bold}.stat-label{font-size:0.85rem;color:#888}.info-card{background:linear-gradient(135deg,rgba(138,43,226,0.1),rgba(0,255,136,0.05));border:1px solid rgba(138,43,226,0.3);border-radius:15px;padding:25px;margin:15px 0;transition:all 0.3s}.info-card:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(138,43,226,0.2)}.info-title{color:#00ff88;font-size:1.2rem;margin-bottom:10px;display:flex;align-items:center;gap:10px}.info-text{color:#888;line-height:1.6}.feature-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin:20px 0}.feature{background:rgba(138,43,226,0.1);padding:20px;border-radius:12px;border-left:3px solid #8a2be2}.feature-title{color:#00ff88;font-weight:bold;margin-bottom:8px}.feature-desc{color:#888;font-size:0.9rem}.modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(5px);display:flex;align-items:center;justify-content:center;z-index:1000;animation:fadeIn 0.3s ease}.modal{background:linear-gradient(135deg,rgba(26,10,42,0.95),rgba(42,20,58,0.95));padding:35px;border-radius:20px;max-width:450px;width:90%;box-shadow:0 20px 60px rgba(138,43,226,0.3);border:1px solid rgba(138,43,226,0.3);animation:scaleIn 0.3s ease}@keyframes scaleIn{from{transform:scale(0.9);opacity:0}to{transform:scale(1);opacity:1}}.modal h3{color:#00ff88;margin-bottom:20px;text-align:center}.modal label{display:block;margin-bottom:8px;color:#888;font-size:0.9rem}.modal-buttons{display:flex;gap:10px;margin-top:25px}.modal-buttons .btn{flex:1;margin:0}.icon{display:inline-block;width:24px;height:24px;vertical-align:middle;margin-right:8px}.icon-rocket{background:linear-gradient(135deg,#8a2be2,#00ff88);mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M12 2C12 2 8 8 8 14C8 17.5 9.5 20 12 22C14.5 20 16 17.5 16 14C16 8 12 2 12 2Z\"/></svg>') center/contain no-repeat;-webkit-mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M12 2C12 2 8 8 8 14C8 17.5 9.5 20 12 22C14.5 20 16 17.5 16 14C16 8 12 2 12 2Z\"/></svg>') center/contain no-repeat}.icon-bolt{background:linear-gradient(135deg,#00ff88,#8a2be2);mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M13 2L3 14H12L11 22L21 10H12L13 2Z\"/></svg>') center/contain no-repeat;-webkit-mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M13 2L3 14H12L11 22L21 10H12L13 2Z\"/></svg>') center/contain no-repeat}.icon-target{background:linear-gradient(135deg,#8a2be2,#9d4edd);mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><circle cx=\"12\" cy=\"12\" r=\"6\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/></svg>') center/contain no-repeat;-webkit-mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><circle cx=\"12\" cy=\"12\" r=\"6\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/></svg>') center/contain no-repeat}.icon-diamond{background:linear-gradient(135deg,#00ff88,#8a2be2);mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M12 2L2 9L12 22L22 9L12 2Z\"/></svg>') center/contain no-repeat;-webkit-mask:url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path d=\"M12 2L2 9L12 22L22 9L12 2Z\"/></svg>') center/contain no-repeat}"

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def send_page(self, html, s=200):
        b = html.encode('utf-8')
        self.send_response(s)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(b))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b)
    def send_json(self, d, s=200):
        b = json.dumps(d).encode('utf-8')
        self.send_response(s)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b)
    def send_redirect(self, p):
        self.send_response(303)
        self.send_header("Location", p)
        self.send_header("Content-Length", 0)
        self.send_header("Connection", "close")
        self.end_headers()
    def get_cookie(self):
        ck = self.headers.get("Cookie", "")
        if ck:
            c = SimpleCookie()
            c.load(ck)
            if "session" in c: return c["session"].value
        return None
    def get_uid(self):
        t = self.get_cookie()
        return check_session(t) if t else None
    def read_body(self):
        l = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(l).decode('utf-8') if l else ""
    def do_GET(self):
        p = self.path.split("?")[0]
        uid = self.get_uid()
        if p == "/": self.send_page(self.main(uid))
        elif p == "/login": self.send_page(self.login()) if not uid else self.send_redirect("/dashboard")
        elif p == "/register": self.send_page(self.register()) if not uid else self.send_redirect("/dashboard")
        elif p == "/dashboard": self.send_page(self.dashboard(uid)) if uid else self.send_redirect("/login")
        elif p == "/api/deploys": self.send_json(self.get_deploys(uid)) if uid else self.send_json({"error": "auth"}, 401)
        elif p == "/api/logout":
            t = self.get_cookie()
            if t: delete_session(t)
            self.send_redirect("/")
        else: self.send_page("<h1>404</h1>", 404)
    def do_POST(self):
        p = self.path.split("?")[0]
        d = parse_qs(self.read_body())
        if p == "/api/register":
            u, pw = d.get("username", [""])[0], d.get("password", [""])[0]
            if len(u) < 2 or len(pw) < 4: return self.send_json({"error": "invalid", "message": "Логин от 2 символов, пароль от 4"})
            with DB_LOCK:
                c = get_db().cursor()
                try:
                    c.execute("INSERT INTO users(username, password_hash) VALUES(%s, %s)", (u, hash_pwd(pw)))
                    get_db().commit()
                    self.send_json({"ok": True, "token": create_session(c.lastrowid)})
                except: self.send_json({"error": "exists", "message": "Аккаунт уже существует"})
        elif p == "/api/login":
            u, pw = d.get("username", [""])[0], d.get("password", [""])[0]
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("SELECT id FROM users WHERE username=%s AND password_hash=%s", (u, hash_pwd(pw)))
                except: c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (u, hash_pwd(pw)))
                r = c.fetchone()
            if r: self.send_json({"ok": True, "token": create_session(r[0])})
            else: self.send_json({"error": "invalid", "message": "Неверный логин или пароль"})
        elif p == "/api/deploy/create":
            uid = self.get_uid()
            if not uid: return self.send_json({"error": "auth", "message": "Требуется авторизация"})
            url, iv = d.get("url", [""])[0], int(d.get("interval", ["420"])[0])
            if not validate_url(url): return self.send_json({"error": "invalid_url", "message": "Некорректный URL"})
            if iv < 60 or iv > 604800: return self.send_json({"error": "invalid_interval", "message": "Интервал 60-604800 секунд"})
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("SELECT COUNT(*) FROM deploys WHERE user_id=%s", (uid,))
                except: c.execute("SELECT COUNT(*) FROM deploys WHERE user_id=?", (uid,))
                if c.fetchone()[0] >= 50: return self.send_json({"error": "limit", "message": "Лимит: 50 деплоев"})
                try: c.execute("INSERT INTO deploys(user_id, url, interval, next_ping) VALUES(%s, %s, %s, %s)", (uid, url, iv, int(time.time()) + iv))
                except: c.execute("INSERT INTO deploys(user_id, url, interval, next_ping) VALUES(?, ?, ?, ?)", (uid, url, iv, int(time.time()) + iv))
                get_db().commit()
            self.send_json({"ok": True})
        elif p == "/api/deploy/toggle":
            uid = self.get_uid()
            if not uid: return self.send_json({"error": "auth", "message": "Требуется авторизация"})
            did = int(d.get("id", ["0"])[0])
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("SELECT status FROM deploys WHERE id=%s AND user_id=%s", (did, uid))
                except: c.execute("SELECT status FROM deploys WHERE id=? AND user_id=?", (did, uid))
                r = c.fetchone()
                if r:
                    try: c.execute("UPDATE deploys SET status=%s WHERE id=%s", (0 if r[0] else 1, did))
                    except: c.execute("UPDATE deploys SET status=? WHERE id=?", (0 if r[0] else 1, did))
                    get_db().commit()
            self.send_json({"ok": True})
        elif p == "/api/deploy/delete":
            uid = self.get_uid()
            if not uid: return self.send_json({"error": "auth", "message": "Требуется авторизация"})
            did = int(d.get("id", ["0"])[0])
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("DELETE FROM deploys WHERE id=%s AND user_id=%s AND system_flag=0", (did, uid))
                except: c.execute("DELETE FROM deploys WHERE id=? AND user_id=? AND system_flag=0", (did, uid))
                get_db().commit()
            self.send_json({"ok": True})
        elif p == "/api/deploy/edit":
            uid = self.get_uid()
            if not uid: return self.send_json({"error": "auth", "message": "Требуется авторизация"})
            did, url, iv = int(d.get("id", ["0"])[0]), d.get("url", [""])[0], int(d.get("interval", ["420"])[0])
            if not validate_url(url): return self.send_json({"error": "invalid_url", "message": "Некорректный URL"})
            if iv < 60 or iv > 604800: return self.send_json({"error": "invalid_interval", "message": "Интервал 60-604800 секунд"})
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("UPDATE deploys SET url=%s, interval=%s WHERE id=%s AND user_id=%s", (url, iv, did, uid))
                except: c.execute("UPDATE deploys SET url=?, interval=? WHERE id=? AND user_id=?", (url, iv, did, uid))
                get_db().commit()
            self.send_json({"ok": True})
        else: self.send_json({"error": "not_found"}, 404)
    def main(self, uid):
        auth = '<a href="/login" class="btn">Вход</a><a href="/register" class="btn">Регистрация</a>' if not uid else '<a href="/dashboard" class="btn">Панель</a>'
        js = '<script>const texts=["DH RUNBOTIME","Автоматический пинг","Бесплатно","Для ваших проектов"];let ti=0,ci=0,del=false;function type(){const el=document.getElementById("tw");if(!el)return;let t=texts[ti];if(del){ci--;el.innerHTML="<span>"+t.substring(0,ci)+"</span>";if(ci<=0){del=false;ti=(ti+1)%texts}}else{ci++;el.innerHTML="<span>"+t.substring(0,ci)+"</span>";if(ci>=t.length){del=true;setTimeout(type,1500);return}}setTimeout(type,del?50:100)}document.addEventListener("DOMContentLoaded",type);</script>'
        desc = '<p style="font-size:1.15rem;line-height:2;margin-bottom:35px;max-width:600px;margin-left:auto;margin-right:auto"><span class="icon icon-rocket"></span>Не дайте проекту уснуть <span style="color:#4a1a6b">•</span><br><span class="icon icon-bolt"></span>GET-запросы через интервалы <span style="color:#4a1a6b">•</span><br><span class="icon icon-target"></span>Для <span style="color:#8a2be2;font-weight:bold">Render</span>, <span style="color:#8a2be2;font-weight:bold">Heroku</span>, <span style="color:#8a2be2;font-weight:bold">HF Spaces</span> <span style="color:#4a1a6b">•</span><br><span class="icon icon-diamond"></span>Полностью бесплатно</p>'
        return '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DH RUNBOTIME</title><style>' + CSS + '</style></head><body><div class="center"><div class="hero"><div class="typewriter" id="tw"><span>DH RUNBOTIME</span></div>' + desc + auth + '</div></div>' + js + '</body></html>'
    def login(self):
        js = 'document.getElementById("f").onsubmit=async e=>{e.preventDefault();const btn=e.target.querySelector("button");const orig=btn.innerHTML;btn.innerHTML=\'<span class="loading"></span>\';btn.disabled=true;try{const r=await fetch("/api/login",{method:"POST",body:new URLSearchParams(new FormData(e.target))});const j=await r.json();if(j.ok){document.cookie="session="+j.token+";path=/;max-age=2592000";location.href="/dashboard"}else{showToast(j.message||j.error||"Ошибка")}}catch(err){showToast("Ошибка соединения")}btn.innerHTML=orig;btn.disabled=false};'
        return '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход</title><style>' + CSS + '</style></head><body><div class="center"><form class="form" id="f"><h2>Вход</h2><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Пароль" required><button type="submit" class="btn" style="width:100%">Войти</button><a href="/register" class="link">Нет аккаунта? Регистрация</a></form></div><script>function showToast(m){const t=document.createElement("div");t.className="toast";t.textContent=m;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}' + js + '</script></body></html>'
    def register(self):
        js = 'document.getElementById("f").onsubmit=async e=>{e.preventDefault();const btn=e.target.querySelector("button");const orig=btn.innerHTML;btn.innerHTML=\'<span class="loading"></span>\';btn.disabled=true;try{const r=await fetch("/api/register",{method:"POST",body:new URLSearchParams(new FormData(e.target))});const j=await r.json();if(j.ok){document.cookie="session="+j.token+";path=/;max-age=2592000";location.href="/dashboard"}else{showToast(j.message||j.error||"Ошибка")}}catch(err){showToast("Ошибка соединения")}btn.innerHTML=orig;btn.disabled=false};'
        return '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Регистрация</title><style>' + CSS + '</style></head><body><div class="center"><form class="form" id="f"><h2>Регистрация</h2><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Пароль" required><button type="submit" class="btn" style="width:100%">Создать</button><a href="/login" class="link">Уже есть? Вход</a></form></div><script>function showToast(m){const t=document.createElement("div");t.className="toast";t.textContent=m;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}' + js + '</script></body></html>'
    def dashboard(self, uid):
        with DB_LOCK:
            c = get_db().cursor()
            try: c.execute("SELECT username FROM users WHERE id=%s", (uid,))
            except: c.execute("SELECT username FROM users WHERE id=?", (uid,))
            un = c.fetchone()[0]
            try: c.execute("SELECT COUNT(*) FROM deploys WHERE user_id=%s", (uid,))
            except: c.execute("SELECT COUNT(*) FROM deploys WHERE user_id=?", (uid,))
            dc = c.fetchone()[0]
        ph = '<div class="card"><h3>👤 Профиль</h3><div class="info-card" style="margin:15px 0"><div class="info-title">📈 Статистика</div><div class="stat" style="margin-right:30px"><div class="stat-value">' + un + '</div><div class="stat-label">Username</div></div><div class="stat"><div class="stat-value">' + str(dc) + '<span style="color:#888;font-size:1rem">/50</span></div><div class="stat-label">Деплоев</div></div></div><div class="info-card"><div class="info-title">ℹ️ Информация</div><p class="info-text">Максимум 50 деплоев. Системный не учитывается.</p></div><a href="/api/logout" class="btn btn-danger" style="width:100%">Выйти</a></div>'
        return '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Панель</title><style>' + CSS + '</style></head><body><div class="nav"><h1 onclick="location.href=\'/\'">DH RUNBOTIME</h1><div><a href="/api/logout">Выход</a></div></div><div class="container"><div class="tabs"><button class="tab active" onclick="t(\'d\')">📋 Деплои</button><button class="tab" onclick="t(\'c\')">➕ Создать</button><button class="tab" onclick="t(\'p\')">👤 Профиль</button></div><div id="d" class="content"></div><div id="c" class="content hidden">' + self.create() + '</div><div id="p" class="content hidden">' + ph + '</div></div><script>' + DJ + '</script></body></html>'
    def create(self):
        info = '<div class="info-card" style="margin-bottom:20px"><div class="info-title">📊 Информация</div><p class="info-text">Создайте деплой для авто-пинга. Укажите URL и интервал.</p></div>'
        return '<h3>➕ Создать деплой</h3>' + info + '<form id="cf" style="max-width:500px"><div style="margin-bottom:15px"><label style="display:block;margin-bottom:8px;color:#888">URL</label><input type="url" name="url" placeholder="https://app.onrender.com" required></div><div style="margin-bottom:20px"><label style="display:block;margin-bottom:8px;color:#888">Интервал</label><select id="is" onchange="ui()"><option value="420">7 минут</option><option value="600">10 минут (Render)</option><option value="3600">1 час</option><option value="72000">20 часов (HF)</option><option value="86400">1 день</option><option value="custom">Свой</option></select><input type="number" id="ic" placeholder="Секунды (60-604800)" min="60" max="604800" style="display:none;margin-top:10px"></div><div class="feature-grid"><div class="feature"><div class="feature-title">🎯 Render</div><div class="feature-desc">10 минут для бесплатного инстанса</div></div><div class="feature"><div class="feature-title">🚀 HF Spaces</div><div class="feature-desc">20 часов для Spaces</div></div></div><button type="submit" class="btn" style="width:100%">Создать</button></form><script>function ui(){document.getElementById("ic").style.display=document.getElementById("is").value==="custom"?"block":"none"}document.getElementById("cf").onsubmit=async e=>{e.preventDefault();const btn=e.target.querySelector("button");btn.innerHTML=\'<span class="loading"></span>\';btn.disabled=true;const s=document.getElementById("is");let i=s.value==="custom"?parseInt(document.getElementById("ic").value):parseInt(s.value);try{const r=await fetch("/api/deploy/create",{method:"POST",body:"url="+encodeURIComponent(e.target.url.value)+"&interval="+i,headers:{"Content-Type":"application/x-www-form-urlencoded"}});const j=await r.json();if(j.ok){showToast("Создано!");location.href="/dashboard"}else{showToast(j.error)}}catch(err){showToast("Ошибка")}btn.innerHTML="Создать";btn.disabled=false};function showToast(m){const t=document.createElement("div");t.className="toast";t.textContent=m;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}</script>'
    def get_deploys(self, uid):
        with DB_LOCK:
            c = get_db().cursor()
            try: c.execute("SELECT id, url, interval, status, pings, next_ping FROM deploys WHERE user_id=%s AND system_flag=0", (uid,))
            except: c.execute("SELECT id, url, interval, status, pings, next_ping FROM deploys WHERE user_id=? AND system_flag=0", (uid,))
            rows = c.fetchall()
        return [{"id": r[0], "url": r[1], "interval": r[2], "status": r[3], "pings": r[4], "next_ping": r[5] * 1000} for r in rows]

DJ = '''function t(n){document.querySelectorAll(".content").forEach(c=>c.classList.add("hidden"));document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));document.getElementById(n).classList.remove("hidden");event.target.classList.add("active");if(n==="d")load()}
async function load(){const r=await fetch("/api/deploys");const j=await r.json();const c=document.getElementById("d");if(!j||!j.length){c.innerHTML="<div class=\'info-card\' style=\'margin-bottom:20px\'><div class=\'info-title\'>📊 Инфо</div><p class=\'info-text\'>Нет деплоев. Создайте первый!</p></div><p style=\'color:#888;text-align:center;padding:40px\'>📭 Пусто</p>";return}
let info="<div class=\'info-card\' style=\'margin-bottom:20px\'><div class=\'info-title\'>📈 Статистика</div><p class=\'info-text\'>Всего: "+j.length+" из 50. Активных: "+j.filter(d=>d.status).length+". Остановлено: "+j.filter(d=>!d.status).length+".</p></div>";
let h="<table><tr><th>URL</th><th>Интервал</th><th>Статус</th><th>Пингов</th><th>След. пинг</th><th>Действия</th></tr>";
j.forEach(d=>{const sec=Math.max(0,Math.floor(d.next_ping/1000-Date.now()/1000));let cd=sec<=0?"🔄 Сейчас":sec<60?sec+"с":sec<3600?Math.floor(sec/60)+"м "+(sec%60)+"с":Math.floor(sec/3600)+"ч "+Math.floor((sec%3600)/60)+"м";
h+="<tr><td style=\'max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap\' title=\'"+d.url+"\'>"+d.url+"</td><td>"+fmt(d.interval)+"</td><td><span class=\'"+(d.status?"status-active":"status-inactive")+"\'>"+(d.status?"🟢 Активен":"🔴 Остановлен")+"</span></td><td>📊 "+d.pings+"</td><td class=\'cd-"+d.id+"\'><span class=\'countdown\'>"+cd+"</span></td><td>";
h+="<button onclick=\'tg("+d.id+")\' class=\'btn btn-small "+(d.status?"btn-danger":"")+"\' style=\'background:"+ (d.status?"linear-gradient(135deg,#ff4444,#cc3333)":"linear-gradient(135deg,#00ff88,#00cc6a)") +"\'>"+(d.status?"⏹ Стоп":"▶ Старт")+"</button> ";
h+="<button onclick=\'openEdit("+d.id+",\\""+d.url.replace(/"/g,"&quot;")+"\\","+d.interval+")\' class=\'btn btn-small\' style=\'background:linear-gradient(135deg,#444,#333)\'><span style=\'color:#fff\'>✏ Ред.</span></button> ";
h+="<button onclick=\'del("+d.id+")\' class=\'btn btn-small btn-danger\'><span style=\'color:#fff\'>🗑 Удалить</span></button></td></tr>"});h+="</table>";c.innerHTML=info+h;updateCountdowns()}
function fmt(s){if(s<60)return s+"с";if(s<3600)return Math.floor(s/60)+"м";if(s<86400)return Math.floor(s/3600)+"ч";return Math.floor(s/86400)+"д"}
function updateCountdowns(){setInterval(()=>{fetch("/api/deploys").then(r=>r.json()).then(j=>{j.forEach(d=>{const el=document.querySelector(".cd-"+d.id);if(el){const sec=Math.max(0,Math.floor(d.next_ping/1000-Date.now()/1000));let cd=sec<=0?"🔄 Сейчас":sec<60?sec+"с":sec<3600?Math.floor(sec/60)+"м "+(sec%60)+"с":Math.floor(sec/3600)+"ч "+Math.floor((sec%3600)/60)+"м";el.innerHTML="<span class=\'countdown\'>"+cd+"</span>"}})})},1000)}
async function tg(id){const btn=event.target;btn.disabled=true;try{await fetch("/api/deploy/toggle",{method:"POST",body:"id="+id,headers:{"Content-Type":"application/x-www-form-urlencoded"}});load()}catch(err){showToast("Ошибка")}btn.disabled=false}
async function del(id){if(confirm("Удалить?")){try{await fetch("/api/deploy/delete",{method:"POST",body:"id="+id,headers:{"Content-Type":"application/x-www-form-urlencoded"}});showToast("Удалено");load()}catch(err){showToast("Ошибка")}}}
function openEdit(id,url,interval){let unit="s",val=interval;if(interval>=86400&&interval%86400===0){unit="d";val=interval/86400}else if(interval>=3600&&interval%3600===0){unit="h";val=interval/3600}else if(interval>=60&&interval%60===0){unit="m";val=interval/60}
const overlay=document.createElement("div");overlay.className="modal-overlay";overlay.innerHTML="<div class=\'modal\'><h3>✏ Редактировать</h3><label>URL</label><input type=\'url\' id=\'editUrl\' value=\'"+url+"\'><label>Интервал</label><div style=\'display:flex;gap:10px\'><input type=\'number\' id=\'editIntervalVal\' value=\'"+val+"\' min=\'1\' max=\'10080\' style=\'flex:1\'><select id=\'editIntervalUnit\' style=\'width:100px\'><option value=\'s\' "+(unit==="s"?"selected":"")+">сек</option><option value=\'m\' "+(unit==="m"?"selected":"")+">мин</option><option value=\'h\' "+(unit==="h"?"selected":"")+">час</option><option value=\'d\' "+(unit==="d"?"selected":"")+">дней</option></select></div><div class=\'modal-buttons\'><button class=\'btn\' onclick=\'saveEdit("+id+")\'>💾 Сохранить</button><button class=\'btn btn-danger\' onclick=\'closeModal(this)\'>❌ Отмена</button></div></div>";document.body.appendChild(overlay);overlay.onclick=function(e){if(e.target===overlay)closeModal(overlay)}}
function closeModal(el){el.style.animation="slideOut 0.3s ease";setTimeout(()=>el.remove(),300)}
async function saveEdit(id){const url=document.getElementById("editUrl").value;const val=parseInt(document.getElementById("editIntervalVal").value);const unit=document.getElementById("editIntervalUnit").value;if(!url||url.length<5){showToast("Введите URL");return}let interval=val;if(unit==="m")interval=val*60;else if(unit==="h")interval=val*3600;else if(unit==="d")interval=val*86400;if(interval<60||interval>604800){showToast("Интервал 60-604800 сек");return}try{const btn=event.target;btn.innerHTML=\'<span class="loading"></span>\';btn.disabled=true;await fetch("/api/deploy/edit",{method:"POST",body:"id="+id+"&url="+encodeURIComponent(url)+"&interval="+interval,headers:{"Content-Type":"application/x-www-form-urlencoded"}});showToast("Изменено!");const modal=document.querySelector(".modal-overlay");if(modal)closeModal(modal);load()}catch(err){showToast("Ошибка")}}
function showToast(m){const t=document.createElement("div");t.className="toast";t.textContent=m;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}
load();'''

def pinger_loop():
    while True:
        try:
            now = int(time.time())
            with DB_LOCK:
                c = get_db().cursor()
                try: c.execute("SELECT id, url, interval FROM deploys WHERE status=1 AND next_ping<=%s", (now,))
                except: c.execute("SELECT id, url, interval FROM deploys WHERE status=1 AND next_ping<=?", (now,))
                for did, url, iv in c.fetchall():
                    try:
                        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "DH-RUNBOTIME/1.0"}), timeout=5)
                        try: c.execute("UPDATE deploys SET pings=pings+1, last_ping=%s, next_ping=%s WHERE id=%s", (now, now + iv, did))
                        except: c.execute("UPDATE deploys SET pings=pings+1, last_ping=?, next_ping=? WHERE id=?", (now, now + iv, did))
                    except:
                        try: c.execute("UPDATE deploys SET next_ping=%s WHERE id=%s", (now + iv, did))
                        except: c.execute("UPDATE deploys SET next_ping=? WHERE id=?", (now + iv, did))
                get_db().commit()
        except: pass
        time.sleep(1)

class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run():
    global DATABASE_URL
    for i, a in enumerate(sys.argv):
        if a == "--db" and i + 1 < len(sys.argv): DATABASE_URL = sys.argv[i + 1]
        elif a.startswith("--db="): DATABASE_URL = a.split("=", 1)[1]
    init_db()
    threading.Thread(target=pinger_loop, daemon=True).start()
    dt = "Neon DB" if DATABASE_URL and DATABASE_URL.startswith("postgresql://") else "SQLite"
    print(f"DH RUNBOTIME на порту {PORT} ({dt})")
    TS(("0.0.0.0", PORT), H).serve_forever()

if __name__ == "__main__":
    run()

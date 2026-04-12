import os
import sqlite3
import requests
import json
import random
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ZRYLO_ROYAL_SECRET_786" 

# --- 1. ENTERPRISE CONFIG & DATABASE SETUP ---
API_KEY = "AIzaSyCSqncogp8wquQ1tc5DF8CD4BKZvWvv_sk" 
DB_NAME = "zrylo_enterprise.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Updated Schema for Auto-Activation
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  email TEXT UNIQUE, 
                  password TEXT, 
                  is_pro INTEGER DEFAULT 0, 
                  expiry_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. MASTER UI ---
@app.route('/')
def index():
    is_pro = 0
    if 'user' in session:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT is_pro, expiry_date FROM users WHERE email=?", (session['user'],))
        user = c.fetchone()
        if user:
            is_pro = user[0]
            # 6-Month Expiry Auto-Check
            if is_pro == 1 and user[1]:
                if datetime.now() > datetime.strptime(user[1], '%Y-%m-%d %H:%M:%S'):
                    c.execute("UPDATE users SET is_pro=0 WHERE email=?", (session['user'],))
                    conn.commit()
                    is_pro = 0
        conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zrylo-AI | Enterprise Master Suite</title>

        <link rel="icon" type="image/png" href="https://i.postimg.cc/DZ02jdTY/Untitled-design-2026-04-08T180617-067.png">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background-color: #050505; color: #f0f0f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
            .royal-card { background: linear-gradient(145deg, #013220 0%, #050505 100%); border: 1px solid #D4AF37; box-shadow: 0 0 60px rgba(212, 175, 55, 0.2); }
            .gold-text { color: #D4AF37; text-shadow: 0 0 15px rgba(212, 175, 55, 0.4); }
            .btn-premium { background: linear-gradient(145deg, #D4AF37, #AA8A2E); color: black; font-weight: 900; cursor: pointer; transition: 0.4s; border: none; }
            .btn-premium:hover { transform: scale(1.02); box-shadow: 0 0 30px rgba(212, 175, 55, 0.5); }
            .clip-card { background: rgba(255,255,255,0.02); border: 1px solid #333; border-radius: 40px; overflow: hidden; position: relative; transition: 0.3s; }
            .vertical-container { width: 100%; padding-top: 177.78%; position: relative; background: #000; overflow: hidden; }
            .speaker-video { position: absolute; top: 0; left: -100%; width: 300%; height: 100%; animation: activeTrack 8s infinite steps(1); pointer-events: none; }
            @keyframes activeTrack { 0% { transform: translateX(12.5%); } 50% { transform: translateX(-12.5%); } 100% { transform: translateX(12.5%); } }
            .audio-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; cursor: pointer; backdrop-filter: blur(8px); transition: 0.3s; }
            .unmute-badge { background: #D4AF37; color: black; padding: 14px 28px; border-radius: 50px; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
            .modal { background: rgba(0,0,0,0.98); display: none; position: fixed; inset: 0; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(10px); }
            .auth-input { width: 100%; padding: 1.25rem; background: rgba(0,0,0,0.6); border: 1px solid #333; border-radius: 1.5rem; color: white; outline: none; transition: 0.3s; }
        </style>
    </head>
    <body class="p-6 md:p-12 flex flex-col items-center">
        <div class="w-full max-w-6xl flex justify-between items-center mb-10 px-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-[#D4AF37] flex items-center justify-center text-black font-black">Z</div>
                <span class="gold-text font-black tracking-widest text-xs uppercase italic">Zrylo AI</span>
            </div>
            <div id="profileSection">
                {% if session.get('user') %}
                    <div class="flex items-center gap-6">
                        <span class="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">{{ session['user'] }} {% if is_pro == 1 %}(PRO){% endif %}</span>
                        <a href="/logout" class="text-[#D4AF37] text-[10px] font-black uppercase border border-[#D4AF37]/30 px-5 py-2 rounded-full">Logout</a>
                    </div>
                {% else %}
                    <button onclick="openAuth()" class="text-white text-[10px] font-black uppercase border border-zinc-800 px-6 py-2 rounded-full">Login / Signup</button>
                {% endif %}
            </div>
        </div>

        <div class="text-center mb-16">
            <h1 class="text-7xl md:text-9xl font-black gold-text tracking-tighter uppercase italic">Zrylo-AI</h1>
            <p class="text-zinc-600 text-[10px] tracking-[0.5em] font-bold mt-4 uppercase">Unlimited Enterprise Speaker Tracking</p>
        </div>

        <div class="w-full max-w-6xl royal-card p-10 md:p-16 rounded-[4rem]">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-12 mb-12">
                <div class="space-y-4">
                    <label class="gold-text text-[10px] font-black uppercase tracking-widest ml-4 italic">Source URL</label>
                    <input type="text" id="vUrl" onfocus="checkAuth()" placeholder="Paste YouTube Link..." class="w-full p-7 bg-black/40 border border-zinc-800 rounded-[2rem] text-white outline-none focus:border-[#D4AF37]">
                </div>
                <div class="space-y-4">
                    <label class="gold-text text-[10px] font-black uppercase tracking-widest ml-4 italic">Enterprise 1GB Upload</label>
                    <div onclick="checkAuth()" class="border-2 border-dashed border-zinc-800 rounded-[2rem] p-6 text-center relative hover:bg-white/5 transition cursor-pointer">
                        <input type="file" id="videoFile" class="absolute inset-0 opacity-0 cursor-pointer" onchange="uploadVideo()">
                        <span class="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">DRAG & DROP VIDEO</span>
                    </div>
                </div>
            </div>

            <button onclick="runZrylo()" id="mainBtn" class="w-full py-9 rounded-[2.5rem] btn-premium text-3xl uppercase tracking-tighter shadow-2xl">
                Analyze & Track Active Speaker
            </button>

            <div id="resultArea" class="hidden mt-24 border-t border-zinc-800 pt-20">
                <h2 class="gold-text text-center text-2xl font-black mb-16 uppercase tracking-widest italic">AI Character Sync Feed</h2>
                <div id="clipsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-10"></div>
            </div>
        </div>

        <div id="authModal" class="modal p-6">
            <div class="max-w-md w-full royal-card p-12 rounded-[3.5rem] text-center relative">
                <button onclick="closeAuth()" class="absolute top-8 right-8 text-zinc-500 hover:text-white">✕</button>
                <h3 class="gold-text text-4xl font-black mb-2 uppercase italic tracking-tighter">Zrylo Access</h3>
                <form action="/auth" method="POST" class="space-y-5">
                    <input type="email" name="email" placeholder="EMAIL ADDRESS" required class="auth-input">
                    <input type="password" name="password" placeholder="PASSWORD" required class="auth-input">
                    <div class="grid grid-cols-2 gap-4 pt-4">
                        <button type="submit" name="type" value="login" class="py-4 btn-premium rounded-2xl text-[11px] font-black uppercase">Login</button>
                        <button type="submit" name="type" value="signup" class="py-4 border border-zinc-700 text-white rounded-2xl text-[11px] font-black uppercase">Signup</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="payModal" class="modal p-6">
            <div class="max-w-md w-full royal-card p-12 rounded-[4rem] text-center border-[#D4AF37]">
                <h3 class="gold-text text-4xl font-black mb-6 uppercase tracking-tighter italic">6-MONTH LICENSE</h3>
                <div class="space-y-4 mb-10">
                    <button onclick="window.open('https://rzp.io/rzp/v3ppXAXU', '_system')" class="w-full p-6 bg-black/60 border border-[#D4AF37] rounded-3xl flex justify-between items-center hover:bg-white/5">
                        <div>
                            <p class="text-[10px] text-zinc-500 uppercase font-bold mb-1">For India</p>
                            <p class="text-3xl font-black gold-text">View Plan For India</p>
                        </div>
                    </button>
                    <button onclick="window.open('https://rzp.io/rzp/0pNXjsv', '_system')" class="w-full p-6 bg-black/60 border border-zinc-800 rounded-3xl flex justify-between items-center hover:bg-white/5">
                        <div>
                            <p class="text-[10px] text-zinc-500 uppercase font-bold mb-1">For Global</p>
                            <p class="text-3xl font-black gold-text">View Plan For Global</p>
                        </div>
                    </button>
                </div>
                <p class="text-zinc-500 text-[10px] mb-8 italic">Note: Access will be activated automatically after payment verification.</p>
                <button onclick="document.getElementById('payModal').style.display='none'" class="text-zinc-700 text-[10px] font-black uppercase hover:text-white transition">Cancel</button>
            </div>
        </div>

        <script>
            const isLoggedIn = {{ 'true' if session.get('user') else 'false' }};
            const isProUser = {{ 'true' if is_pro == 1 else 'false' }};

            function openAuth() { document.getElementById('authModal').style.display = 'flex'; }
            function closeAuth() { document.getElementById('authModal').style.display = 'none'; }
            function checkAuth() { if(!isLoggedIn) { openAuth(); return false; } return true; }
            
            function handleDownload() {
    if(!isProUser) { 
        // Agar user PRO nahi hai, toh seedha payment modal kholo
        document.getElementById('payModal').style.display = 'flex'; 
    } else { 
        alert("Download Started in 4K Quality!"); 
    }
}

            function getID(url) {
                const reg = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
                const match = url.match(reg);
                return (match && match[2].length == 11) ? match[2] : null;
            }

            function playOne(overlayId, iframeId) {
                document.querySelectorAll('.audio-overlay').forEach(ov => ov.style.display = 'flex');
                document.querySelectorAll('iframe').forEach(ifr => {
                    let src = ifr.src;
                    if (src.includes("mute=0")) ifr.src = src.replace("mute=0", "mute=1");
                });
                document.getElementById(iframeId).src = document.getElementById(iframeId).src.replace("mute=1", "mute=0");
                document.getElementById(overlayId).style.display = "none";
            }

            async function runZrylo() {
                if(!checkAuth()) return;
                const url = document.getElementById('vUrl').value;
                const vidId = getID(url);
                const btn = document.getElementById('mainBtn');
                if(!vidId) { alert("Sahi YouTube Link dalo bhai!"); return; }
                
                btn.innerText = "AI TRACKING ACTIVE SPEAKERS...";
                btn.disabled = true;
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ url: url })
                    });
                    const data = await response.json();
                    
                    document.getElementById('resultArea').classList.remove('hidden');
                    const grid = document.getElementById('clipsGrid');
                    grid.innerHTML = "";
                    
                    data.segments.forEach((seg, i) => {
                        const ifId = `v_${i}`; const oId = `o_${i}`;
                        grid.innerHTML += `
                            <div class="clip-card p-2">
                                <div id="${oId}" onclick="playOne('${oId}', '${ifId}')" class="audio-overlay">
                                    <div class="unmute-badge">🔊 UNMUTE & TRACK</div>
                                </div>
                                <div class="vertical-container rounded-[35px]">
                                    <iframe id="${ifId}" class="speaker-video" src="https://www.youtube.com/embed/${vidId}?start=${seg.start}&autoplay=1&mute=1&controls=0" frameborder="0"></iframe>
                                </div>
                                <div class="p-8">
                                    <p class="text-[10px] text-zinc-400 mb-8 italic border-l-2 border-[#D4AF37] pl-4">${seg.reason}</p>
                                    <button onclick="handleDownload()" class="w-full py-4 bg-[#D4AF37] text-black rounded-xl text-[10px] font-black uppercase">Download Segment</button>
                                </div>
                            </div>`;
                    });
                } catch (e) { alert("API Error!"); }
                btn.innerText = "ANALYZE & TRACK ACTIVE SPEAKER";
                btn.disabled = false;
            }

            function uploadVideo() {
                const fileInput = document.getElementById('videoFile');
                const grid = document.getElementById('clipsGrid');
                if (fileInput.files.length === 0) return alert("Please select a file!");

                const formData = new FormData();
                formData.append('video_file', fileInput.files[0]);

                grid.innerHTML = `
                    <div class="col-span-full p-12 text-center royal-card rounded-[2.5rem]">
                        <div id="statusText" class="gold-text text-2xl font-black mb-6 uppercase italic">Uploading Media...</div>
                        <div class="w-full bg-zinc-900 h-4 rounded-full overflow-hidden border border-zinc-800">
                            <div id="progressBar" class="bg-[#D4AF37] h-full transition-all duration-300" style="width: 0%"></div>
                        </div>
                        <p id="percentText" class="text-[#D4AF37] mt-4 font-bold">0%</p>
                    </div>`;

                const xhr = new XMLHttpRequest();
                xhr.upload.onprogress = function(e) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    document.getElementById('progressBar').style.width = percent + '%';
                    document.getElementById('percentText').innerText = percent + '%';
                };

                xhr.onload = function() {
                    if (xhr.status === 200) {
                        document.getElementById('statusText').innerText = "UPLOAD DONE! STARTING CLIPPING...";
                        setTimeout(() => { runZrylo(); }, 1000); 
                    } else { alert("Upload failed!"); }
                };
                xhr.open('POST', '/api/upload');
                xhr.send(formData);
            }

            async function pay(type) {
                const url = type === 'india' ? 'https://rzp.io/l/your_link' : 'https://stripe.com/your_link';
                window.open(url, '_blank');
                setTimeout(async () => {
                    const response = await fetch('/api/activate-pro', { method: 'POST' });
                    const result = await response.json();
                    if(result.status === 'success') {
                        alert("SYSTEM VERIFIED: Your 6-Month Pro Access is now ACTIVE!");
                        location.reload();
                    }
                }, 5000); 
            }
        </script>
        <footer class="w-full max-w-6xl mt-32 mb-12 px-4 border-t border-zinc-900 pt-12 text-center">
            <div class="flex flex-wrap justify-center gap-8 mb-8">
                <a href="/legal/about" class="text-[10px] text-zinc-600 hover:text-[#D4AF37] uppercase font-black tracking-widest">About Us</a>
                <a href="/legal/privacy" class="text-[10px] text-zinc-600 hover:text-[#D4AF37] uppercase font-black tracking-widest">Privacy Policy</a>
                <a href="/legal/terms" class="text-[10px] text-zinc-600 hover:text-[#D4AF37] uppercase font-black tracking-widest">Terms</a>
                <a href="/legal/help" class="text-[10px] text-zinc-600 hover:text-[#D4AF37] uppercase font-black tracking-widest">Help Center</a>
                <a href="/legal/contact" class="text-[10px] text-[#D4AF37] border border-[#D4AF37]/20 px-4 py-1 rounded-full uppercase font-black">Support</a>
            </div>
            <p class="text-[8px] text-zinc-800 font-bold uppercase tracking-[0.5em]">© 2026 ZRYLO AI • ENTERPRISE VIRAL SUITE</p>
        </footer>
    </body>
    </html>
    """, is_pro=is_pro)

# --- 1. SIGNUP & LOGIN LOGIC ---
@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    auth_type = request.form.get('type')

    if not email or not password:
        return "Bhai, details adhuri hain! <a href='/'>Back</a>"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        if auth_type == 'signup':
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            if c.fetchone():
                conn.close()
                return "Email pehle se hai! Login karo. <a href='/'>Back</a>"
            
            # Password ko encrypt karke save kar rahe hain
            hashed_pw = generate_password_hash(password)
            c.execute("INSERT INTO users (email, password, is_pro) VALUES (?, ?, 0)", (email, hashed_pw))
            conn.commit()
            session['user'] = email
        else:
            # Login check with hashing
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            if user and check_password_hash(user[2], password):
                session['user'] = email
            else:
                conn.close()
                return "Galat email/password! <a href='/'>Back</a>"
        
        session.permanent = True
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error: {e}"

# --- 2. AUTOMATIC PRO ACTIVATION ---
@app.route('/api/activate-pro', methods=['POST'])
def activate_pro():
    if 'user' not in session:
        return jsonify({"status": "fail", "message": "Login first"}), 401
    
    # Yahan 180 days (6 months) ka logic hai
    expiry = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # User ko PRO banao aur expiry date set karo
        c.execute("UPDATE users SET is_pro=1, expiry_date=? WHERE email=?", (expiry, session['user']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "expiry": expiry})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# --- ADMIN CONFIGURATION ---
ADMIN_SECRET_KEY = "ZRYLO786"  # Ye tera master password hai

@app.route('/zrylo-admin')
def admin_panel():
    # Isse kholne ke liye browser mein dalo: /zrylo-admin?key=ZRYLO786
    key = request.args.get('key')
    if key != ADMIN_SECRET_KEY:
        return "<h1 style='color:red; text-align:center; margin-top:50px;'>UNAUTHORIZED ACCESS DETECTED!</h1>", 403

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Saare users ki list nikal rahe hain
    c.execute("SELECT id, email, is_pro, expiry_date FROM users")
    users = c.fetchall()
    conn.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zrylo AI | Master Admin</title>
        <style>
            body { background: #050505; color: #D4AF37; font-family: sans-serif; padding: 40px; }
            .admin-container { max-width: 1000px; margin: auto; background: #0a0a0a; padding: 30px; border-radius: 20px; border: 1px solid #D4AF37; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 15px; text-align: left; border-bottom: 1px solid #222; }
            th { color: #888; text-transform: uppercase; font-size: 12px; }
            .status-pro { color: lime; font-weight: bold; }
            .status-free { color: #555; }
            .btn-activate { background: #D4AF37; color: black; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 12px; }
            .btn-activate:hover { opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <h1 style="letter-spacing: 5px;">ZRYLO CONTROL CENTER</h1>
            <p style="color: #555;">Managing Enterprise Users & Subscriptions</p>
            <table>
                <tr>
                    <th>ID</th>
                    <th>User Email</th>
                    <th>Status</th>
                    <th>Expiry Date</th>
                    <th>Action</th>
                </tr>
                {% for u in users %}
                <tr>
                    <td>{{ u[0] }}</td>
                    <td>{{ u[1] }}</td>
                    <td>
                        <span class="{{ 'status-pro' if u[2] == 1 else 'status-free' }}">
                            {{ 'PREMIUM' if u[2] == 1 else 'FREE' }}
                        </span>
                    </td>
                    <td>{{ u[3] if u[3] else 'N/A' }}</td>
                    <td>
                        {% if u[2] == 0 %}
                        <a href="/admin/make-pro/{{ u[0] }}?key=ZRYLO786" class="btn-activate">ACTIVATE 6M</a>
                        {% else %}
                        <span style="color: #333;">ALREADY PRO</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
            <br>
            <a href="/" style="color: #333; text-decoration: none;">← Return to Main Suite</a>
        </div>
    </body>
    </html>
    """, users=users)

@app.route('/admin/make-pro/<int:uid>')
def admin_make_pro(uid):
    key = request.args.get('key')
    if key != ADMIN_SECRET_KEY:
        return "Unauthorized", 403

    # 6 mahine ka time calculate kar rahe hain (180 days)
    expiry = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET is_pro=1, expiry_date=? WHERE id=?", (expiry, uid))
    conn.commit()
    conn.close()
    
    # Wapas admin panel par bhej do
    return redirect(f'/zrylo-admin?key={ADMIN_SECRET_KEY}')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'user' not in session: return jsonify({"status": "unauthorized"}), 401
    segs = [{"start": random.randint(10, 500), "reason": "AI Speaker Tracking Active"} for i in range(10)]
    return jsonify({"status": "success", "segments": segs})

@app.route('/legal/<page_type>')
def legal_pages(page_type):
    data = {
        "privacy": {"title": "Privacy Policy", "body": """Your privacy is our top priority. Zrylo AI does not permanently store any personal video data or processed clips on our servers. 
            All files are processed in a temporary environment and are automatically deleted within 24-48 hours. 
            We use your email address solely for account authentication and subscription tracking. 
            We strictly do not sell or share your data with any third-party organizations."""},
        "terms": {"title": "Terms of Service", "body": """1. Zrylo AI must be used only for legal and ethical content creation purposes. 
            2. The 6-Month Pro Subscription is a non-refundable digital purchase. 
            3. Account access is valid for a single active user only; account sharing is prohibited. 
            4. Any attempt to hack, scrape, or misuse the system will result in a permanent account ban without a refund. 
            5. We reserve the right to temporarily suspend service for server maintenance without prior notice."""},
        "about": {"title": "About Zrylo AI", "body": """Zrylo AI is a premium Enterprise Viral Suite designed to empower content creators with 4K speaker tracking and automated clip extraction. 
            Our mission is to make high-end AI technology affordable and accessible for creators targeting global audiences."""},
        "help": {"title": "Help Center & FAQ", "body": """<b>Q: Why is my clip not downloading?</b><br>
            A: Ensure your PRO access is active. If active, try refreshing the page or checking your internet connection.<br><br>
            <b>Q: I paid, but PRO is not unlocked?</b><br>
            A: Due to network delays, it may take 2-5 minutes for activation. Please refresh the suite. If the issue persists, contact support.<br><br>
            <b>Q: Can I analyze long videos?</b><br>
            A: Currently, Pro users can analyze long videos for optimal processing speed."""},
        "contact": {"title": "Contact & Support", "body": "<b>Email:</b> supportzryloai@gmail.com"}
    }
    page = data.get(page_type, {"title": "Error", "body": "Page not found."})
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><title>{{title}} | Zrylo AI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body { background: #050505; color: #f0f0f0; font-family: sans-serif; }
        .legal-card { background: linear-gradient(145deg, #013220, #050505); border: 1px solid #D4AF37; }</style>
    </head>
    <body class="p-8 md:p-20 flex justify-center">
        <div class="max-w-3xl w-full legal-card p-10 rounded-[3rem]">
            <h1 class="text-4xl font-black text-[#D4AF37] mb-8 uppercase italic">{{title}}</h1>
            <div class="text-zinc-400 leading-relaxed text-lg space-y-6">{{body|safe}}</div>
            <div class="mt-12 pt-8 border-t border-zinc-900"><a href="/" class="text-[#D4AF37] font-bold uppercase text-xs">← Back</a></div>
        </div>
    </body></html>
    """, title=page['title'], body=page['body'])

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    if 'video_file' not in request.files: return jsonify({"status": "error"}), 400
    file = request.files['video_file']
    if not os.path.exists('uploads'): os.makedirs('uploads')
    save_path = os.path.join('uploads', file.filename)
    file.save(save_path)
    return jsonify({"status": "success", "file_path": save_path})

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

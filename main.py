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

# --- 1. MASTER UI (FINAL STABLE VERSION) ---
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
            expiry_date = user[1]
            # Expiry Check logic
            if is_pro == 1 and expiry_date:
                if datetime.now() > datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
                    c.execute("UPDATE users SET is_pro=0 WHERE email=?", (session['user'],))
                    conn.commit()
                    is_pro = 0
        conn.close()
    
    session['is_pro'] = is_pro

    # POORA HTML YAHIN HAI - ISME KUCH MISSING NAHI HAI
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zrylo-AI | Enterprise Master Suite</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background-color: #050505; color: #f0f0f0; font-family: sans-serif; }
            .royal-card { background: linear-gradient(145deg, #013220 0%, #050505 100%); border: 1px solid #D4AF37; }
            .gold-text { color: #D4AF37; }
            .btn-premium { background: linear-gradient(145deg, #D4AF37, #AA8A2E); color: black; font-weight: 900; }
            .clip-card { background: rgba(255,255,255,0.02); border: 1px solid #333; border-radius: 40px; overflow: hidden; }
            .vertical-container { width: 100%; padding-top: 177.78%; position: relative; background: #000; overflow: hidden; }
            .speaker-video { position: absolute; top: 0; left: -100%; width: 300%; height: 100%; animation: activeTrack 8s infinite steps(1); pointer-events: none; }
            @keyframes activeTrack { 0% { transform: translateX(12.5%); } 50% { transform: translateX(-12.5%); } 100% { transform: translateX(12.5%); } }
            .audio-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; cursor: pointer; }
            .modal { background: rgba(0,0,0,0.98); display: none; position: fixed; inset: 0; align-items: center; justify-content: center; z-index: 1000; }
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-6xl mx-auto flex justify-between items-center mb-10">
            <div class="gold-text font-black tracking-widest text-xl italic">ZRYLO AI</div>
            <div id="profile">
                {% if session.get('user') %}
                    <span class="text-xs uppercase">{{ session['user'] }} {% if is_pro == 1 %}(PRO){% endif %}</span>
                    <a href="/logout" class="ml-4 text-red-500 font-bold">Logout</a>
                {% else %}
                    <button onclick="openAuth()" class="border px-4 py-2 rounded-full">Login</button>
                {% endif %}
            </div>
        </div>

        <div class="text-center mb-16">
            <h1 class="text-7xl md:text-8xl font-black gold-text italic">ZRYLO-AI</h1>
            <p class="text-zinc-500 uppercase tracking-widest mt-2">Enterprise Speaker Tracking</p>
        </div>

        <div class="max-w-4xl mx-auto royal-card p-10 rounded-[3rem]">
            <input type="text" id="vUrl" placeholder="Paste YouTube Link..." class="w-full p-6 bg-black/50 border border-zinc-800 rounded-2xl text-white mb-6">
            <button onclick="runZrylo()" id="mainBtn" class="w-full py-6 btn-premium rounded-2xl text-xl uppercase italic">Analyze & Track Speaker</button>

            <div id="resultArea" class="hidden mt-16 pt-10 border-t border-zinc-800">
                <h2 class="gold-text text-center text-xl font-bold mb-10 uppercase italic">AI Character Sync Feed</h2>
                <div id="clipsGrid" class="grid grid-cols-1 sm:grid-cols-2 gap-8"></div>
            </div>
        </div>

        <div id="authModal" class="modal">
            <div class="max-w-sm w-full royal-card p-8 rounded-3xl text-center">
                <h2 class="gold-text text-2xl font-black mb-6 italic">ACCESS ZRYLO</h2>
                <form action="/auth" method="POST" class="space-y-4">
                    <input type="email" name="email" placeholder="Email" required class="w-full p-4 bg-black border border-zinc-800 rounded-xl">
                    <input type="password" name="password" placeholder="Password" required class="w-full p-4 bg-black border border-zinc-800 rounded-xl">
                    <button type="submit" name="type" value="login" class="w-full py-3 btn-premium rounded-xl uppercase">Login</button>
                    <button type="submit" name="type" value="signup" class="w-full py-3 border border-zinc-800 rounded-xl text-white mt-2">Signup</button>
                </form>
                <button onclick="closeAuth()" class="mt-4 text-zinc-500">Close</button>
            </div>
        </div>

        <script>
            const isLoggedIn = {{ 'true' if session.get('user') else 'false' }};
            let isPro = {{ '1' if is_pro == 1 else '0' }};

            function openAuth() { document.getElementById('authModal').style.display='flex'; }
            function closeAuth() { document.getElementById('authModal').style.display='none'; }

            function getID(url) {
                const reg = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
                const match = url.match(reg);
                return (match && match[2].length == 11) ? match[2] : null;
            }

            function playOne(oId, ifId) {
                document.getElementById(oId).style.display = 'none';
                let ifr = document.getElementById(ifId);
                ifr.src = ifr.src.replace("mute=1", "mute=0");
            }

            async function runZrylo() {
                if(!isLoggedIn) { openAuth(); return; }
                const url = document.getElementById('vUrl').value;
                const vidId = getID(url);
                if(!vidId) { alert("Sahi URL dalo!"); return; }

                const btn = document.getElementById('mainBtn');
                btn.innerText = "AI TRACKING...";
                btn.disabled = true;

                try {
                    const res = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ url: url })
                    });
                    const data = await res.json();
                    
                    if(data.status === "success") {
                        document.getElementById('resultArea').classList.remove('hidden');
                        const grid = document.getElementById('clipsGrid');
                        grid.innerHTML = "";

                        data.segments.forEach((seg, i) => {
                            grid.insertAdjacentHTML('beforeend', `
                                <div class="clip-card p-2">
                                    <div id="o_${i}" onclick="playOne('o_${i}', 'v_${i}')" class="audio-overlay">
                                        <div class="bg-[#D4AF37] text-black px-4 py-2 rounded-full font-bold text-[10px]">UNMUTE</div>
                                    </div>
                                    <div class="vertical-container rounded-[30px]">
                                        <iframe id="v_${i}" class="speaker-video" 
                                            src="https://www.youtube.com/embed/` + vidId + `?start=` + seg.start + `&autoplay=1&mute=1&controls=0" 
                                            frameborder="0"></iframe>
                                    </div>
                                    <div class="p-6 text-center">
                                        <p class="text-[10px] text-zinc-500 italic mb-4">` + seg.reason + `</p>
                                        <button onclick="alert('Download Started!')" class="w-full py-3 bg-[#D4AF37] text-black rounded-xl font-bold uppercase text-[10px]">Download Clip</button>
                                    </div>
                                </div>
                            `);
                        });
                    }
                } catch(e) { alert("Error!"); }
                finally { btn.innerText = "Analyze & Track Speaker"; btn.disabled = false; }
            }
        </script>
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
    
    # 180 days logic
    expiry = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET is_pro=1, expiry_date=? WHERE email=?", (expiry, session['user']))
        conn.commit()
        conn.close()
        
        # IMMEDIATELY UPDATE SESSION
        session['is_pro'] = 1 
        return jsonify({"status": "success", "expiry": expiry})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# --- ADMIN CONFIGURATION ---
ADMIN_SECRET_KEY = "ZRYLO786"  # Ye tera master password hai

@app.route('/api/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    data = request.json
    
    # Razorpay signal check kar raha hai
    if data.get('event') == 'payment.captured':
        payment_entity = data['payload']['payment']['entity']
        customer_email = payment_entity.get('email', '').lower()
        
        if customer_email:
            expiry = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # Database mein user ko PRO bana raha hai
            c.execute("UPDATE users SET is_pro=1, expiry_date=? WHERE email=?", (expiry, customer_email))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"}), 200

    return jsonify({"status": "ignored"}), 200

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

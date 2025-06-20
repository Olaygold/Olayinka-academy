from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import sqlite3, random, string

app = Flask(__name__)
app.secret_key = 'your_flask_secret_key_here'

# Configure Flask‑Mail (use real SMTP creds in production)
app.config.update(
    MAIL_SERVER='smtp.example.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='you@example.com',
    MAIL_PASSWORD='password',
    MAIL_DEFAULT_SENDER=('Olayinka Trading Academy', 'noreply@olayinkatrading.com')
)
mail = Mail(app)

DB = 'waitlist.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        otp TEXT,
        verified INTEGER DEFAULT 0,
        phone TEXT,
        referral_code TEXT UNIQUE,
        referred_by TEXT,
        invited_count INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def random_code(n=6):
    return ''.join(random.choices(string.digits, k=n))

def random_ref():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@app.before_first_request
def setup():
    init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    otp = random_code()

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    ref_code = random_ref()
    try:
        c.execute('INSERT INTO users (email, otp, referral_code) VALUES (?, ?, ?)', (email, otp, ref_code))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    conn.close()

    msg = Message('Your OTP to join Olayinka Trading Academy Waitlist')
    msg.html = f"<h3>Olayinka Trading Academy</h3><p>Your OTP: <b>{otp}</b></p>"
    mail.send(msg)

    return jsonify({'status': 'otp_sent'})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    email, otp = data.get('email'), data.get('otp')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT otp, verified, referral_code FROM users WHERE email=?', (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Email not found'}), 400
    db_otp, verified, ref_code = row
    if verified:
        return jsonify({'status': 'already_verified', 'referral_code': ref_code})
    if otp == db_otp:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('UPDATE users SET verified=1 WHERE email=?', (email,))
        conn.commit()
        conn.close()
        session['email'] = email
        return jsonify({'status': 'verified', 'referral_code': ref_code})
    else:
        return jsonify({'error': 'Invalid OTP'}), 400

@app.route('/save_phone', methods=['POST'])
def save_phone():
    email = session.get('email')
    phone = request.json.get('phone')
    if not email:
        return jsonify({'error': 'Not logged in'}), 401
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE users SET phone=? WHERE email=?', (phone, email))
    conn.commit()
    conn.close()
    return jsonify({'status': 'phone_saved'})

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    if not email:
        return redirect(url_for('home'))
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT referral_code, invited_count FROM users WHERE email=?', (email,))
    ref_code, count = c.fetchone()
    conn.close()
    chance = random.randint(1,50)
    link = f"{request.host_url}?ref={ref_code}"
    return render_template('dashboard.html', code=ref_code, count=count, chance=chance, link=link)

@app.route('/invite')
def invite_register():
    ref = request.args.get('ref')
    session['ref'] = ref
    return redirect(url_for('home'))

@app.route('/register_with_ref', methods=['POST'])
def register_with_ref():
    email = request.json.get('email')
    otp = random_code()
    referrer = session.get('ref')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    ref_code = random_ref()
    try:
        c.execute('INSERT INTO users (email, otp, referral_code, referred_by) VALUES (?, ?, ?, ?)',
                  (email, otp, ref_code, referrer))
        if referrer:
            c.execute('UPDATE users SET invited_count = invited_count + 1 WHERE referral_code=?', (referrer,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    conn.close()
    msg = Message('Your OTP to join Olayinka Trading Academy Waitlist')
    msg.html = f"<h3>Olayinka Trading Academy</h3><p>Your OTP: <b>{otp}</b></p>"
    mail.send(msg)
    return jsonify({'status': 'otp_sent'})

if __name__ == '__main__':
    app.run(debug=True)

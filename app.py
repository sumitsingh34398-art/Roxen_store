from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'roxen_quick_store_ultra_secure_2026'

# ========================================================
# 🚀 PRE-CONFIGURED GMAIL SMTP WITH NEW APP PASSWORD
# ========================================================
SMTP_EMAIL = "sumitsingh34398@gmail.com"
SMTP_PASSWORD = "gcyb jcis yxfe xqto"
# ========================================================

def get_db():
    conn = sqlite3.connect('roxen.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            address TEXT DEFAULT 'Hisar, Haryana, India',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def send_email_async(email, otp):
    clean_pass = SMTP_PASSWORD.replace(" ", "")
    msg = MIMEMultipart()
    msg['From'] = f"Roxen Quick Store <{SMTP_EMAIL}>"
    msg['To'] = email
    msg['Subject'] = f"{otp} is your Roxen verification code"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px; border: 1px solid #e1e8e4; border-radius: 16px; background-color: #ffffff;">
        <h2 style="color: #0c831f; margin: 0 0 8px 0; font-size: 24px;">Roxen</h2>
        <h3 style="color: #172b20; margin-top: 0;">Verify your account</h3>
        <p style="color: #4b5a52; font-size: 14px; line-height: 1.5;">Use the 4-digit code below to complete your registration:</p>
        <div style="text-align: center; margin: 24px 0;">
            <span style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0c831f; background: #f0fdf4; padding: 12px 28px; border-radius: 12px; display: inline-block; border: 1.5px solid #bbf7d0;">
                {otp}
            </span>
        </div>
        <p style="color: #728279; font-size: 12px;">Valid for 10 minutes. Do not share this OTP with anyone.</p>
        <hr style="border: none; border-top: 1px solid #f1f5f3; margin: 20px 0;">
        <p style="color: #9ab0a4; font-size: 11px; text-align: center; margin: 0;">&copy; 2026 Roxen Commerce. All rights reserved.</p>
    </div>
    """
    msg.attach(MIMEText(html_content, 'html'))

    # Connection on Port 587 (TLS - Render & Cloud standard)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, clean_pass)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
        print(f"✔ [SUCCESS] OTP delivered to {email}")
    except Exception as e:
        print(f"⚠️ Port 587 failed ({e}), trying Port 465 SSL...")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
                server.login(SMTP_EMAIL, clean_pass)
                server.sendmail(SMTP_EMAIL, email, msg.as_string())
            print(f"✔ [SUCCESS] OTP delivered via SSL to {email}")
        except Exception as e2:
            print(f"❌ Real Delivery Failed: {e2}")

@app.route('/')
def root():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return redirect(url_for('home'))

@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('root'))
    return render_template('auth.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'error': 'Valid email is required.'})

    otp = str(random.randint(1000, 9999))
    session['temp_otp'] = otp
    session['temp_email'] = email

    print(f"\n==========================================")
    print(f"⚡ [ROXEN QUICK COMMERCE] ⚡")
    print(f"👉 Generated OTP for {email}: {otp}")
    print(f"==========================================\n")

    thread = threading.Thread(target=send_email_async, args=(email, otp))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True})

@app.route('/api/verify-register', methods=['POST'])
def verify_register():
    try:
        data = request.get_json() or {}
        entered_otp = data.get('otp', '').strip()
        password = data.get('password', '').strip()
        fullname = data.get('fullname', '').strip()
        mobile = data.get('mobile', '').strip()
        email = data.get('email', '').strip()

        saved_otp = session.get('temp_otp')
        if not saved_otp or entered_otp != saved_otp:
            return jsonify({'success': False, 'error': 'Invalid OTP code. Please check your email.'})

        hashed_password = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, phone, email, password_hash, role, address)
            VALUES (?, ?, ?, ?, 'customer', 'Hisar, Haryana, India')
        ''', (fullname, mobile, email, hashed_password))
        conn.commit()
        conn.close()

        session.pop('temp_otp', None)
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Mobile number or email already registered.'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    password = data.get('password', '').strip()

    if not identifier or not password:
        return jsonify({'success': False, 'error': 'All fields are required.'})

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE phone = ? OR email = ?', (identifier, identifier)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        return jsonify({'success': True, 'redirect': '/home'})

    return jsonify({'success': False, 'error': 'Invalid mobile/email or password.'})

# UPDATED: Single safe /home route with NoneType prevention
@app.route('/home')
def home():
    if 'user_id' not in session or session.get('user_role') != 'customer':
        return redirect(url_for('auth_page'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    # Agar deployment/restart ke baad user record missing ho, toh crash hone ki jagah auth par redirect karega
    if not user:
        session.clear()
        return redirect(url_for('auth_page'))

    return render_template('home.html', user=user)

@app.route('/api/update-location', methods=['POST'])
def update_location():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    data = request.get_json() or {}
    address = data.get('address')
    conn = get_db()
    conn.execute('UPDATE users SET address = ? WHERE id = ?', (address, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_page'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'roxen_super_secret_key_2026'

# ========================================================
# 🚀 GMAIL SMTP SETUP (Enter your credentials below)
# ========================================================
SMTP_EMAIL = "sumitsingh3439email@gmail.com"
SMTP_PASSWORD = "bzyo mgml zalt scyx"  # 16-digit App Password
# ========================================================

def get_db():
    conn = sqlite3.connect('roxen.db')
    conn.row_factory = sqlite3.Row
    return conn

# Auto-initialize database schema on startup
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

@app.route('/')
def root():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('home'))

@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('root'))
    return render_template('auth.html')

# 1. SEND REAL 4-DIGIT OTP API
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'error': 'A valid email address is required.'})

    otp = str(random.randint(1000, 9999))
    session['temp_otp'] = otp
    session['temp_email'] = email

    print(f"\n==========================================")
    print(f"⚡ [ROXEN QUICK COMMERCE] ⚡")
    print(f"👉 Real OTP for {email}: {otp}")
    print(f"==========================================\n")

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Roxen Store <{SMTP_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = f"{otp} is your Roxen verification code"

        html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 480px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px;">
            <h2 style="color: #0b4629; margin: 0 0 10px 0;">Roxen</h2>
            <h3 style="color: #1a202c; margin-top: 0;">Welcome to Roxen!</h3>
            <p style="color: #4a5568; font-size: 14px; line-height: 1.5;">Please use the 4-digit code below to verify your email address and complete registration:</p>
            <div style="text-align: center; margin: 26px 0;">
                <span style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0e8345; background: #eaf8f0; padding: 12px 28px; border-radius: 12px; display: inline-block;">
                    {otp}
                </span>
            </div>
            <p style="color: #718096; font-size: 12px; margin-bottom: 0;">This code is valid for 10 minutes. Please do not share it with anyone.</p>
            <hr style="border: none; border-top: 1px solid #edf2f7; margin: 20px 0;">
            <p style="color: #a0aec0; font-size: 11px; text-align: center; margin: 0;">&copy; 2026 Roxen Quick Commerce. All rights reserved.</p>
        </div>
        """
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            clean_pass = SMTP_PASSWORD.replace(" ", "")
            server.login(SMTP_EMAIL, clean_pass)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())

        return jsonify({'success': True})
    except Exception as e:
        print(f"Mail Exception: {e}")
        return jsonify({'success': True, 'msg': 'OTP generated (Check Terminal)'})

# 2. VERIFY OTP & CREATE ACCOUNT
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
            return jsonify({'success': False, 'error': 'Invalid verification code. Please check your inbox.'})

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
        print(f"❌ Verification Server Error: {e}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'})

# 3. SIGN IN API
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
        
        target = '/admin' if user['role'] == 'admin' else '/home'
        return jsonify({'success': True, 'redirect': target})

    return jsonify({'success': False, 'error': 'Invalid mobile/email or password.'})

# 4. HOME STORE PAGE (With live address & account details)
@app.route('/home')
def home():
    if 'user_id' not in session or session.get('user_role') != 'customer':
        return redirect(url_for('auth_page'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    return render_template('home.html', user=user)

# 5. UPDATE ADDRESS / LOCATION MODAL API
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

# 6. ADMIN DASHBOARD
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth_page'))
    return f"""
    <div style='font-family:sans-serif; text-align:center; padding-top:60px;'>
        <h1 style='color:#0d5c3a;'>Dark Store Operations Panel 📦</h1>
        <p>Logged in as Store Manager: {session.get('user_name')}</p>
        <br>
        <a href='/logout' style='color:#dc2626; font-weight:bold; text-decoration:none;'>Logout</a>
    </div>
    """

# 7. LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_page'))

if __name__ == '__main__':
    app.run(debug=True)

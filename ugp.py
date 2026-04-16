from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import random
from datetime import datetime
import time
import os
from captcha.image import ImageCaptcha
from authlib.integrations.flask_client import OAuth
import pickle
import threading
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.secret_key = os.environ.get('APP_KEY')
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'users_data.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, mobile TEXT, state TEXT, district TEXT)''')
    conn.commit()
    conn.close()
# ==========================================
# 🌐 GOOGLE LOGIN SETUP
# ==========================================
# ==========================================
# 🌐 GOOGLE LOGIN SETUP (Updated for Localhost)
# ==========================================
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),       
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'), 
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'} 
)

# --- Google Login Routes ---
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    email = user_info['email']

    conn = sqlite3.connect(DB_PATH) 
    c = conn.cursor()
    
    if not c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
        c.execute("INSERT INTO users (email) VALUES (?)", (email,)) 
        conn.commit()
    conn.close()

    session['logged_in'] = True
    session['user_email'] = email
    flash('✅ Google Login Successful!', 'success')
    return redirect(url_for('dashboard'))

# ==========================================
# 🚀 MAIL API SETUP (Via PythonAnywhere)
# ==========================================
def send_real_mail(receiver_email, subject, body):
   
    api_url = "https://drivergrievancemail123.pythonanywhere.com/send_api_mail"
    
    payload = {
        "email": receiver_email,
        "subject": subject,
        "body": body
    }
    
    try:
        
        response = requests.post(api_url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print("✅ Awesome! PythonAnywhere triggered the mail.")
            return True
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection Failed to Mail API: {e}")
        return False

def init_db():
    conn = sqlite3.connect('users_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, mobile TEXT, state TEXT, district TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🔄 CAPTCHA GENERATOR LOGIC
# ==========================================
def generate_captcha(action):
    val = str(random.randint(1000, 9999))
    image = ImageCaptcha(width=160, height=60)
    
    if action == 'login':
        session['login_captcha_val'] = val
        img_path = os.path.join('static', 'login_captcha.png')
    else:
        session['register_captcha_val'] = val
        img_path = os.path.join('static', 'register_captcha.png')
        
    image.write(val, img_path)
    return img_path

@app.route('/refresh_captcha/<action>')
def refresh_captcha(action):
    generate_captcha(action)
    if action == 'login':
        return redirect(url_for('login_page'))
    else:
        return redirect(url_for('register_page'))

# ==========================================
# 1. LOGIN ROUTE (Separate Page)
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if 'login_captcha_val' not in session:
        generate_captcha('login')
    return render_template('login.html', captcha_url=url_for('static', filename='login_captcha.png'))

@app.route('/login_submit', methods=['POST'])
def login_submit():
    email = request.form.get('log_email')
    captcha_input = request.form.get('log_captcha')

    if captcha_input != session.get('login_captcha_val'):
        flash('❌ Invalid Captcha!', 'error')
        generate_captcha('login') # Auto-refresh on fail
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('users_data.db')
    if not conn.cursor().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
        flash('❌ Email not found. Please register first!', 'error')
    else:
        session['logged_in'] = True
        session['user_email'] = email
        return redirect(url_for('dashboard'))
    conn.close()
    generate_captcha('login')
    return redirect(url_for('login_page'))

# ==========================================
# 2. REGISTER ROUTE (Separate Page)
# ==========================================
@app.route('/register_page', methods=['GET', 'POST'])
def register_page():
    if 'register_captcha_val' not in session:
        generate_captcha('register')
    return render_template('register.html', captcha_url=url_for('static', filename='register_captcha.png'))

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('reg_email')
    captcha_input = request.form.get('reg_captcha')

    if captcha_input != session.get('register_captcha_val'):
        flash('❌ Invalid Captcha!', 'error')
        generate_captcha('register') # Auto-refresh on fail
        return redirect(url_for('register_page'))

    conn = sqlite3.connect('users_data.db')
    if conn.cursor().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
        flash('❌ Already registered! Go to Login.', 'error')
    else:
        otp = str(random.randint(100000, 999999))
        session['generated_otp'] = otp
        session['otp_time'] = time.time()
        session['reg_email'] = email
        subject = "🔐 Action Required: Your UGP Registration Verification Code"
        body = f"""Dear Driver Partner,

Welcome to the AI-Powered Driver Grievance Portal.

We have received a request to register your email address ({email}) with our system. To complete your secure registration, please use the following One-Time Password (OTP):

=========================================
🔑 VERIFICATION CODE: {otp}
=========================================

🚨 SECURITY ALERT:
• This OTP is highly confidential and valid strictly for 3 MINUTES.
• Do not share this code with anyone, including UGP executives.
• If you did not request this, please ignore this email immediately.

Thank you for joining our network. We are committed to ensuring your voice is heard!

Best Regards,
Automated Security Team
AI Grievance Portal
(Note: This is an auto-generated system email. Please do not reply.)"""
        
        send_real_mail(email, subject, body)
        flash('✅ OTP sent successfully! Valid for 3 Minutes ⏳', 'success')
    
    conn.close()
    generate_captcha('register')
    return redirect(url_for('register_page'))

@app.route('/register_submit', methods=['POST'])
def register_submit():
    user_otp = request.form.get('reg_otp')
    if user_otp == session.get('generated_otp'):
        time_elapsed = time.time() - session.get('otp_time', 0)
        if time_elapsed <= 180:
            conn = sqlite3.connect('users_data.db')
            conn.cursor().execute("INSERT INTO users (email) VALUES (?)", (session['reg_email'],))
            conn.commit()
            conn.close()
            session.pop('generated_otp', None) # Clear OTP after success
            flash('✅ Registered Successfully! You can login now.', 'success')
            return redirect(url_for('login_page'))
        else:
            flash('❌ OTP Expired! Please request a new OTP.', 'error')
    else:
        flash('❌ Incorrect OTP!', 'error')
    
    return redirect(url_for('register_page'))

# ==========================================
# 🧠 LOAD ML MODELS
# ==========================================
try:
    with open('svm_model.pkl', 'rb') as f:
        svm_model = pickle.load(f)
    with open('tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
except Exception as e:
    print("🚨 Error loading ML Models. Make sure .pkl files are in the folder!")

# ==========================================
# 3. DASHBOARD ROUTE
# ==========================================
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please login to access the dashboard.", "error")
        return redirect(url_for('login_page'))
    
    ride_apps = ["Uber Driver", "Ola Partner", "Rapido Captain", "Namma Yatri Partner", "inDrive - Drivers", "Porter Partner", "RedTaxi Driver"]
    return render_template('dashboard.html', email=session['user_email'], apps=ride_apps)

@app.route('/submit_grievance', methods=['POST'])
def submit_grievance():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    ride_apps = ["Uber Driver", "Ola Partner", "Rapido Captain", "Namma Yatri Partner", "inDrive - Drivers", "Porter Partner", "RedTaxi Driver"]
    app_name = request.form.get('app_name')
    raw_grievance = request.form.get('grievance_text')
    
    # User Details from Dashboard Form
    u_name = request.form.get('user_name', 'Not Provided')
    u_mobile = request.form.get('user_mobile', 'Not Provided')
    u_state = request.form.get('state', 'Not Provided')
    u_district = request.form.get('district', 'Not Provided')

    # Update User Details in Database
    conn = sqlite3.connect('users_data.db')
    conn.cursor().execute('''
        UPDATE users 
        SET name=?, mobile=?, state=?, district=? 
        WHERE email=?
    ''', (u_name, u_mobile, u_state, u_district, session['user_email']))
    conn.commit()
    conn.close()

    if not raw_grievance or raw_grievance.strip() == "":
        flash("❌ Grievance text cannot be empty!", "error")
        return redirect(url_for('dashboard'))

    try:
        # 1. Translate to English
        try:
            translated_text = GoogleTranslator(source='auto', target='en').translate(raw_grievance)
        except:
            translated_text = raw_grievance

        # 2. ML Prediction & Keywords Check
        pred = svm_model.predict(vectorizer.transform([translated_text]))[0]
        negative_words = ["worst", "waste", "lag", "lagging", "bad", "issue", "money", "fake", "late", "rude", "cancel", "commission", "problem", "poor", "mosam", "high"]
        is_forced_grievance = any(word in translated_text.lower() or word in raw_grievance.lower() for word in negative_words)

        playstore_link = f"https://play.google.com/store/search?q={app_name.replace(' ', '+')}&c=apps"
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        ticket_id = f"UGP-TKT-{random.randint(10000, 99999)}"

        if pred == 1 or str(pred).lower() == 'grievance' or is_forced_grievance:
            
            verified_emails = {
                "Rapido Captain": "captaincare@rapido.bike",
                "Ola Partner": "partnersupport@olacabs.com",
                "Uber Driver": "drivers@uber.com",
                "Namma Yatri Partner": "support@nammayatri.in"
            }
            clean_name = app_name.replace(" ", "").replace("-", "").lower()
            company_mail = verified_emails.get(app_name, f"support@{clean_name}.com")

            subject = f"🚨 URGENT: High-Priority Driver Grievance | Ticket ID: {ticket_id} | {app_name}"
            
            alert_body = f"""CRITICAL SYSTEM ALERT: High-Priority Driver Partner Grievance

Dear {app_name} Partner Support & Escalation Team,

=========================================
🎫 TICKET DETAILS
=========================================
• Ticket ID       : {ticket_id}
• Date & Time     : {current_time}
• Platform        : {app_name}
• AI Severity Level: HIGH (Action Required)

=========================================
👤 DRIVER PARTNER DETAILS
=========================================
• Name            : {u_name}
• Mobile Number   : {u_mobile}
• Registered Email: {session['user_email']}
• State           : {u_state}
• District        : {u_district}

=========================================
📝 GRIEVANCE STATEMENT (Translated & Analyzed)
=========================================
"{translated_text}"

=========================================
ACTION REQUIRED:
Please review the statement above and initiate your internal escalation protocols.

Best Regards,
AI Grievance Detection Engine
"""
            send_real_mail(SENDER_EMAIL, subject, alert_body)
            
            return render_template('dashboard.html', email=session['user_email'], apps=ride_apps,
                                   original=raw_grievance, translated=translated_text,
                                   company_mail=company_mail, playstore_link=playstore_link,
                                   selected_app=app_name, is_critical=True)
        else:
            return render_template('dashboard.html', email=session['user_email'], apps=ride_apps,
                                   original=raw_grievance, translated=translated_text,
                                   is_critical=False)
                                   
    except Exception as e:
        flash("🚨 System Error during ML prediction.", "error")
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
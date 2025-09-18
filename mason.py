from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for, session
import requests
import random
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'c7ka_panel_super_gizli_anahtar_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Dosya yükleme klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Veritabanı başlatma
def init_db():
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    
    # Kullanıcılar tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT,
                  full_name TEXT,
                  profile_pic TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Sorgu geçmişi tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS query_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  api_name TEXT NOT NULL,
                  input_data TEXT NOT NULL,
                  result TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Mesajlaşma tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

init_db()

API_URLS = {
    "telegram": lambda username, _: f"https://api.hexnox.pro/sowixapi/telegram_sorgu.php?username={username}",
    "isyeri": lambda tc, _: f"https://api.hexnox.pro/sowixapi/isyeri.php?tc={tc}",
    "hane": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hane.php?tc={tc}",
    "baba": lambda tc, _: f"https://api.hexnox.pro/sowixapi/baba.php?tc={tc}",
    "anne": lambda tc, _: f"https://api.hexnox.pro/sowixapi/anne.php?tc={tc}",
    "ayak": lambda tc, _: f"https://api.hexnox.pro/sowixapi/ayak.php?tc={tc}",
    "boy": lambda tc, _: f"https://api.hexnox.pro/sowixapi/boy.php?tc={tc}",
    "burc": lambda tc, _: f"https://api.hexnox.pro/sowixapi/burc.php?tc={tc}",
    "cm": lambda tc, _: f"https://api.hexnox.pro/sowixapi/cm.php?tc={tc}",
    "cocuk": lambda tc, _: f"https://api.hexnox.pro/sowixapi/cocuk.php?tc={tc}",
    "ehlt": lambda tc, _: f"https://api.hexnox.pro/sowixapi/ehlt.php?tc={tc}",
    "email_sorgu": lambda email, _: f"https://api.hexnox.pro/sowixapi/email_sorgu.php?email={email}",
    "havadurumu": lambda sehir, _: f"https://api.hexnox.pro/sowixapi/havadurumu.php?sehir={sehir}",
    "imei": lambda imei, _: f"https://api.hexnox.pro/sowixapi/imei.php?imei={imei}",
    "operator": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/operator.php?gsm={gsm}",
    "hikaye": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hikaye.php?tc={tc}",
    "hanep": lambda tc, _: f"https://api.hexnox.pro/sowixapi/hanepro.php?tc={tc}",
    "muhallev": lambda tc, _: f"https://api.hexnox.pro/sowixapi/muhallev.php?tc={tc}",
    "lgs": lambda tc, _: f"https://hexnox.pro/sowixfree/lgs/lgs.php?tc={tc}",
    "plaka": lambda plaka, _: f"https://hexnox.pro/sowixfree/plaka.php?plaka={plaka}",
    "nude": lambda _, __: f"https://hexnox.pro/sowixfree/nude.php",
    "sertifika": lambda tc, _: f"https://hexnox.pro/sowixfree/sertifika.php?tc={tc}",
    "aracparca": lambda plaka, _: f"https://hexnox.pro/sowixfree/aracparca.php?plaka={plaka}",
    "şehit": lambda ad_soyad, _: f"https://hexnox.pro/sowixfree/sehit.php?Ad={ad_soyad.split(' ')[0] if ad_soyad else ''}&Soyad={ad_soyad.split(' ')[1] if ad_soyad and ' ' in ad_soyad else ''}",
    "interpol": lambda ad_soyad, _: f"https://hexnox.pro/sowixfree/interpol.php?ad={ad_soyad.split(' ')[0] if ad_soyad else ''}&soyad={ad_soyad.split(' ')[1] if ad_soyad and ' ' in ad_soyad else ''}",
    "personel": lambda tc, _: f"https://hexnox.pro/sowixfree/personel.php?tc={tc}",
    "internet": lambda tc, _: f"https://hexnox.pro/sowixfree/internet.php?tc={tc}",
    "nvi": lambda tc, _: f"https://hexnox.pro/sowixfree/nvi.php?tc={tc}",
    "nezcane": lambda il_ilce, _: f"https://hexnox.pro/sowixfree/nezcane.php?il={il_ilce.split(' ')[0] if il_ilce else ''}&ilce={il_ilce.split(' ')[1] if il_ilce and ' ' in il_ilce else ''}",
    "basvuru": lambda tc, _: f"https://hexnox.pro/sowixfree/basvuru/basvuru.php?tc={tc}",
    "diploma": lambda tc, _: f"https://hexnox.pro/sowixfree/diploma/diploma.php?tc={tc}",
    "facebook": lambda numara, _: f"https://hexnox.pro/sowixfree/facebook.php?numara={numara}",
    "vergi": lambda tc, _: f"https://hexnox.pro/sowixfree/vergi/vergi.php?tc={tc}",
    "premadres": lambda tc, _: f"https://hexnox.pro/sowixfree/premadres.php?tc={tc}",
    "sgkpro": lambda tc, _: f"https://api.hexnox.pro/sowixapi/sgkpro.php?tc={tc}",
    "mhrs": lambda tc, _: f"https://hexnox.pro/sowixfree/mhrs/mhrs.php?tc={tc}",
    "premad": lambda ad_il_ilce, _: f"https://api.hexnox.pro/sowixapi/premad.php?ad={ad_il_ilce.split(' ')[0] if ad_il_ilce else ''}&il={ad_il_ilce.split(' ')[1] if ad_il_ilce and len(ad_il_ilce.split(' ')) > 1 else ''}&ilce={ad_il_ilce.split(' ')[2] if ad_il_ilce and len(ad_il_ilce.split(' ')) > 2 else ''}",
    "fatura": lambda tc, _: f"https://hexnox.pro/sowixfree/fatura.php?tc={tc}",
    "subdomain": lambda url, _: f"https://api.hexnox.pro/sowixapi/subdomain.php?url={url}",
    "sexgörsel": lambda soru, _: f"https://hexnox.pro/sowixfree/sexgorsel.php?soru={soru}",
    "meslek": lambda tc, _: f"https://api.hexnox.pro/sowixapi/meslek.php?tc={tc}",
    "adsoyad": lambda ad, soyad: f"https://apiservices.alwaysdata.net/diger/adsoyad.php?ad={ad}&soyad={soyad}",
    "adsoyadil": lambda ad, soyad_il: f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad_il.split(' ')[0] if soyad_il else ''}&il={soyad_il.split(' ')[1] if soyad_il and ' ' in soyad_il else ''}",
    "tcpro": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcpro.php?tc={tc}",
    "tcgsm": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcgsm.php?tc={tc}",
    "tapu": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tapu.php?tc={tc}",
    "sulale": lambda tc, _: f"https://api.hexnox.pro/sowixapi/sulale.php?tc={tc}",
    "vesika": lambda tc, _: f"https://20.122.193.203/apiservice/woxy/tc.php?tc={tc}&auth=woxynindaramcigi",
    "allvesika": lambda tc, _: f"https://84.32.15.160/apiservice/woxy/allvesika.php?tc={tc}&auth=cyberinsikimemesiamigotu",
    "okulsicil": lambda tc, _: f"https://merial.cfd/Daimon/freePeker/okulsicil.php?tc={tc}",
    "kizlik": lambda tc, _: f"https://212.68.34.148/apiservices/kizlik?tc={tc}",
    "okulno": lambda tc, _: f"https://api.hexnox.pro/sowixapi/okulno.php?tc={tc}",
    "isyeriyetkili": lambda tc, _: f"https://api.hexnox.pro/sowixapi/isyeriyetkili.php?tc={tc}",
    "gsmdetay": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsmdetay.php?gsm={gsm}",
    "gsm": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsm.php?gsm={gsm}",
    "adres": lambda tc, _: f"https://api.hexnox.pro/sowixapi/adres.php?tc={tc}",
    "insta": lambda username, _: f"https://keneviznewapi.onrender.com/api/insta?usr={username}",
    "facebook_hanedan": lambda ad, soyad: f"https://keneviznewapi.onrender.com/api/facebook_hanedan?ad={ad}&soyad={soyad}",
    "uni": lambda tc, _: f"https://keneviznewapi.onrender.com/api/uni?tc={tc}",
    "akp": lambda ad, soyad: f"https://keneviznewapi.onrender.com/api/akp?ad={ad}&soyad={soyad}",
    "aifoto": lambda img_url, _: f"https://keneviznewapi.onrender.com/api/aifoto?img={img_url}",
    "papara": lambda numara, _: f"https://keneviznewapi.onrender.com/api/papara?paparano={numara}",
    "ininal": lambda numara, _: f"https://keneviznewapi.onrender.com/api/ininal?ininal_no={numara}",
    "smsbomber": lambda number, _: f"https://keneviznewapi.onrender.com/api/smsbomber?number={number}"
}

def get_user_count():
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_query_count():
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM query_history")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_user_data(user_id):
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def save_query_history(user_id, api_name, input_data, result):
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO query_history (user_id, api_name, input_data, result) VALUES (?, ?, ?, ?)",
              (user_id, api_name, input_data, result))
    conn.commit()
    conn.close()

def get_messages(limit=20):
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute('''SELECT messages.*, users.username 
                 FROM messages 
                 JOIN users ON messages.user_id = users.id 
                 ORDER BY messages.timestamp DESC LIMIT ?''', (limit,))
    messages = c.fetchall()
    conn.close()
    return messages

def add_message(user_id, message):
    conn = sqlite3.connect('c7ka_panel.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message) VALUES (?, ?)", (user_id, message))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_data = get_user_data(session['user_id'])
    messages = get_messages()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C7KA Sorgu Paneli</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background: linear-gradient(to bottom, #000000, #1a0000, #330000);
                color: #fff;
                min-height: 100vh;
                overflow-x: hidden;
                position: relative;
            }
            
            .fireball {
                position: absolute;
                width: 20px;
                height: 20px;
                background: radial-gradient(circle, #ff3300, #ff6600, #ff9900);
                border-radius: 50%;
                box-shadow: 0 0 10px #ff3300, 0 0 20px #ff6600;
                z-index: -1;
                opacity: 0.7;
                animation: fall linear forwards;
            }
            
            @keyframes fall {
                to {
                    transform: translateY(100vh) rotate(360deg);
                    opacity: 0;
                }
            }
            
            .container {
                display: flex;
                min-height: 100vh;
            }
            
            .sidebar {
                width: 280px;
                background: rgba(0, 0, 0, 0.85);
                padding: 20px;
                border-right: 2px solid #ff3300;
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.6);
                overflow-y: auto;
                position: relative;
                z-index: 10;
            }
            
            .user-profile {
                text-align: center;
                margin-bottom: 25px;
                padding: 15px;
                background: linear-gradient(to right, #330000, #660000);
                border-radius: 10px;
                border: 1px solid #ff3300;
                box-shadow: 0 0 10px rgba(255, 51, 0, 0.4);
            }
            
            .profile-pic {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid #ff3300;
                margin-bottom: 10px;
                box-shadow: 0 0 15px rgba(255, 51, 0, 0.5);
            }
            
            .username {
                font-weight: bold;
                color: #ff9900;
                margin-bottom: 5px;
                font-size: 16px;
            }
            
            .nav-links {
                margin-top: 20px;
            }
            
            .nav-link {
                display: flex;
                align-items: center;
                padding: 12px 15px;
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                margin-bottom: 8px;
                transition: all 0.3s ease;
                background: rgba(255, 51, 0, 0.1);
            }
            
            .nav-link i {
                margin-right: 10px;
                font-size: 18px;
            }
            
            .nav-link:hover {
                background: rgba(255, 51, 0, 0.3);
                transform: translateX(5px);
            }
            
            .logo {
                text-align: center;
                margin-bottom: 25px;
                padding: 15px;
                background: linear-gradient(to right, #ff3300, #ff6600);
                border-radius: 10px;
                font-weight: bold;
                font-size: 26px;
                text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
                box-shadow: 0 0 15px rgba(255, 51, 0, 0.5);
            }
            
            .menu-title {
                margin: 20px 0 12px;
                color: #ff6600;
                font-size: 18px;
                border-bottom: 2px solid #ff3300;
                padding-bottom: 8px;
                display: flex;
                align-items: center;
            }
            
            .menu-title i {
                margin-right: 10px;
            }
            
            .menu-buttons {
                display: grid;
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .menu-btn {
                background: linear-gradient(to right, #330000, #550000);
                color: #fff;
                border: none;
                padding: 12px 15px;
                border-radius: 8px;
                cursor: pointer;
                text-align: left;
                transition: all 0.3s ease;
                font-size: 14px;
                display: flex;
                align-items: center;
                border: 1px solid #ff3300;
            }
            
            .menu-btn i {
                margin-right: 10px;
                font-size: 16px;
            }
            
            .menu-btn:hover {
                background: linear-gradient(to right, #660000, #990000);
                transform: translateX(5px);
                box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
            }
            
            .content {
                flex: 1;
                padding: 25px;
                display: flex;
                flex-direction: column;
                gap: 25px;
            }
            
            .dashboard {
                background: rgba(0, 0, 0, 0.7);
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #ff3300;
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.4);
                display: flex;
                justify-content: space-around;
                text-align: center;
            }
            
            .stat-box {
                padding: 15px;
            }
            
            .stat-number {
                font-size: 28px;
                color: #ff6600;
                font-weight: bold;
                text-shadow: 0 0 10px rgba(255, 102, 0, 0.5);
            }
            
            .stat-label {
                font-size: 14px;
                color: #ff9900;
                margin-top: 5px;
            }
            
            .welcome-banner {
                background: linear-gradient(to right, #330000, #660000);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #ff3300;
                box-shadow: 0 0 15px rgba(255, 51, 0, 0.4);
            }
            
            .welcome-banner h2 {
                color: #ff6600;
                margin-bottom: 10px;
                font-size: 24px;
            }
            
            .welcome-banner p {
                color: #ff9900;
                font-size: 16px;
            }
            
            .search-area {
                background: rgba(0, 0, 0, 0.7);
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #ff3300;
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.4);
            }
            
            .search-title {
                color: #ff6600;
                margin-bottom: 20px;
                font-size: 24px;
                text-align: center;
                border-bottom: 1px solid #ff3300;
                padding-bottom: 10px;
            }
            
            .input-group {
                margin-bottom: 20px;
            }
            
            .input-group label {
                display: block;
                margin-bottom: 8px;
                color: #ff9900;
                font-weight: 500;
            }
            
            .input-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ff3300;
                background: #1a0000;
                color: #fff;
                border-radius: 8px;
                outline: none;
                transition: all 0.3s;
            }
            
            .input-group input:focus {
                border-color: #ff6600;
                box-shadow: 0 0 10px rgba(255, 102, 0, 0.5);
            }
            
            .search-btn {
                background: linear-gradient(to right, #ff3300, #ff6600);
                color: #fff;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                font-weight: bold;
                transition: all 0.3s;
                font-size: 16px;
                box-shadow: 0 0 15px rgba(255, 51, 0, 0.4);
            }
            
            .search-btn:hover {
                background: linear-gradient(to right, #ff6600, #ff9900);
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.7);
                transform: translateY(-2px);
            }
            
            .result-area {
                background: rgba(0, 0, 0, 0.7);
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #ff3300;
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.4);
                overflow-y: auto;
            }
            
            .result-title {
                color: #ff6600;
                margin-bottom: 20px;
                font-size: 24px;
                text-align: center;
                border-bottom: 1px solid #ff3300;
                padding-bottom: 10px;
            }
            
            .result-content {
                background: #1a0000;
                padding: 20px;
                border-radius: 8px;
                min-height: 200px;
                max-height: 500px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                border: 1px solid #ff3300;
            }
            
            .chat-container {
                background: rgba(0, 0, 0, 0.7);
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #ff3300;
                box-shadow: 0 0 20px rgba(255, 51, 0, 0.4);
                max-height: 350px;
                overflow-y: auto;
            }
            
            .chat-container h3 {
                color: #ff6600;
                margin-bottom: 15px;
                text-align: center;
                border-bottom: 1px solid #ff3300;
                padding-bottom: 10px;
            }
            
            .chat-message {
                margin-bottom: 15px;
                padding: 12px;
                background: rgba(51, 0, 0, 0.5);
                border-radius: 8px;
                border-left: 3px solid #ff3300;
            }
            
            .message-user {
                font-weight: bold;
                color: #ff6600;
                margin-bottom: 5px;
            }
            
            .message-text {
                word-break: break-word;
            }
            
            .message-time {
                font-size: 12px;
                color: #ff9900;
                text-align: right;
            }
            
            .chat-input {
                display: flex;
                margin-top: 15px;
            }
            
            .chat-input input {
                flex: 1;
                padding: 12px;
                border: 1px solid #ff3300;
                background: #1a0000;
                color: #fff;
                border-radius: 8px 0 0 8px;
                outline: none;
            }
            
            .chat-input button {
                padding: 12px 20px;
                background: #ff3300;
                color: #fff;
                border: none;
                border-radius: 0 8px 8px 0;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .chat-input button:hover {
                background: #ff6600;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                background: #1a0000;
                color: #fff;
                border-radius: 8px;
                overflow: hidden;
            }
            
            th, td {
                border: 1px solid #ff3300;
                padding: 12px;
                text-align: left;
            }
            
            th {
                background-color: #330000;
                color: #ff6600;
                font-weight: bold;
            }
            
            tr:nth-child(even) {
                background-color: #260000;
            }
            
            tr:hover {
                background-color: #400000;
            }
            
            .loading {
                color: #ff9900;
                text-align: center;
                display: none;
                font-size: 18px;
                margin: 20px 0;
            }
            
            .loading i {
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #1a0000;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #ff3300;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #ff6600;
            }
            
            @media (max-width: 1024px) {
                .container {
                    flex-direction: column;
                }
                
                .sidebar {
                    width: 100%;
                    border-right: none;
                    border-bottom: 2px solid #ff3300;
                    max-height: 400px;
                }
                
                .dashboard {
                    flex-direction: column;
                    gap: 15px;
                }
            }
            
            @media (max-width: 768px) {
                .content {
                    padding: 15px;
                }
                
                .stat-number {
                    font-size: 24px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="user-profile">
                    <img src="{{ user_data[5] if user_data and user_data[5] else 'https://via.placeholder.com/80' }}" class="profile-pic">
                    <div class="username">{{ user_data[1] if user_data else 'Kullanıcı' }}</div>
                    <a href="{{ url_for('profile') }}" class="nav-link"><i class="fas fa-user-edit"></i>Profili Düzenle</a>
                    <a href="{{ url_for('logout') }}" class="nav-link"><i class="fas fa-sign-out-alt"></i>Çıkış Yap</a>
                </div>
                
                <div class="logo">C7KA SORGULARI</div>
                
                <div class="nav-links">
                    <a href="{{ url_for('index') }}" class="nav-link"><i class="fas fa-home"></i>Ana Sayfa</a>
                </div>
                
                <div class="menu-title"><i class="fas fa-id-card"></i>TC SORGULARI</div>
                <div class="menu-buttons">
                    <button class="menu-btn" onclick="setActiveMenu('tcpro', 'TC Kimlik No')"><i class="fas fa-id-card"></i>TC Pro Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('tcgsm', 'TC Kimlik No')"><i class="fas fa-phone"></i>TC GSM Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('hane', 'TC Kimlik No')"><i class="fas fa-house-user"></i>Hane Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('baba', 'TC Kimlik No')"><i class="fas fa-male"></i>Baba Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('anne', 'TC Kimlik No')"><i class="fas fa-female"></i>Anne Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('adres', 'TC Kimlik No')"><i class="fas fa-address-card"></i>Adres Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('vesika', 'TC Kimlik No')"><i class="fas fa-id-badge"></i>Vesika Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('allvesika', 'TC Kimlik No')"><i class="fas fa-id-badge"></i>Tüm Vesika Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('sulale', 'TC Kimlik No')"><i class="fas fa-users"></i>Sülale Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('okulsicil', 'TC Kimlik No')"><i class="fas fa-graduation-cap"></i>Okul Sicil Sorgu</button>
                </div>
                
                <div class="menu-title"><i class="fas fa-mobile-alt"></i>GSM SORGULARI</div>
                <div class="menu-buttons">
                    <button class="menu-btn" onclick="setActiveMenu('gsm', 'GSM No')"><i class="fas fa-mobile"></i>GSM Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('gsmdetay', 'GSM No')"><i class="fas fa-info-circle"></i>GSM Detay Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('operator', 'GSM No')"><i class="fas fa-sim-card"></i>Operatör Sorgu</button>
                </div>
                
                <div class="menu-title"><i class="fas fa-share-alt"></i>SOSYAL MEDYA</div>
                <div class="menu-buttons">
                    <button class="menu-btn" onclick="setActiveMenu('telegram', 'Kullanıcı Adı')"><i class="fab fa-telegram"></i>Telegram Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('insta', 'Kullanıcı Adı')"><i class="fab fa-instagram"></i>Instagram Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('facebook', 'Telefon No')"><i class="fab fa-facebook"></i>Facebook Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('facebook_hanedan', 'Ad', 'Soyad')"><i class="fab fa-facebook-square"></i>Facebook Hanedan</button>
                </div>
                
                <div class="menu-title"><i class="fas fa-car"></i>ARAÇ SORGULARI</div>
                <div class="menu-buttons">
                    <button class="menu-btn" onclick="setActiveMenu('plaka', 'Plaka No')"><i class="fas fa-car"></i>Plaka Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('aracparca', 'Plaka No')"><i class="fas fa-cog"></i>Araç Parça Sorgu</button>
                </div>
                
                <div class="menu-title"><i class="fas fa-database"></i>DİĞER SORGULAR</div>
                <div class="menu-buttons">
                    <button class="menu-btn" onclick="setActiveMenu('adsoyad', 'Ad', 'Soyad')"><i class="fas fa-user"></i>Ad Soyad Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('adsoyadil', 'Ad', 'Soyad İl')"><i class="fas fa-map-marker"></i>Ad Soyad İl Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('email_sorgu', 'E-posta')"><i class="fas fa-envelope"></i>E-posta Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('imei', 'IMEI No')"><i class="fas fa-mobile-alt"></i>IMEI Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('interpol', 'Ad Soyad')"><i class="fas fa-globe"></i>Interpol Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('isyeri', 'TC Kimlik No')"><i class="fas fa-building"></i>İşyeri Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('isyeriyetkili', 'TC Kimlik No')"><i class="fas fa-user-tie"></i>İşyeri Yetkili Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('şehit', 'Ad Soyad')"><i class="fas fa-star"></i>Şehit Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('nvi', 'TC Kimlik No')"><i class="fas fa-landmark"></i>NVI Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('vergi', 'TC Kimlik No')"><i class="fas fa-receipt"></i>Vergi Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('tapu', 'TC Kimlik No')"><i class="fas fa-home"></i>Tapu Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('okulno', 'TC Kimlik No')"><i class="fas fa-graduation-cap"></i>Okul No Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('personel', 'TC Kimlik No')"><i class="fas fa-briefcase"></i>Personel Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('internet', 'TC Kimlik No')"><i class="fas fa-wifi"></i>Internet Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('fatura', 'TC Kimlik No')"><i class="fas fa-file-invoice"></i>Fatura Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('subdomain', 'URL')"><i class="fas fa-globe"></i>Subdomain Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('havadurumu', 'Şehir')"><i class="fas fa-cloud-sun"></i>Hava Durumu Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('nezcane', 'İl İlçe')"><i class="fas fa-hospital"></i>Nezcane Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('basvuru', 'TC Kimlik No')"><i class="fas fa-file-alt"></i>Başvuru Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('diploma', 'TC Kimlik No')"><i class="fas fa-certificate"></i>Diploma Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('premadres', 'TC Kimlik No')"><i class="fas fa-address-book"></i>Premadres Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('sgkpro', 'TC Kimlik No')"><i class="fas fa-heartbeat"></i>SGK Pro Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('mhrs', 'TC Kimlik No')"><i class="fas fa-hospital-user"></i>MHRS Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('premad', 'Ad İl İlçe')"><i class="fas fa-map-marked"></i>Premad Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('sexgörsel', 'Soru')"><i class="fas fa-image"></i>Sex Görsel Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('meslek', 'TC Kimlik No')"><i class="fas fa-briefcase"></i>Meslek Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('uni', 'TC Kimlik No')"><i class="fas fa-university"></i>Üniversite Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('akp', 'Ad', 'Soyad')"><i class="fas fa-landmark"></i>AKP Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('aifoto', 'Görsel URL')"><i class="fas fa-camera"></i>AI Foto Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('papara', 'Numara')"><i class="fas fa-money-bill-wave"></i>Papara Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('ininal', 'Numara')"><i class="fas fa-credit-card"></i>Ininal Sorgu</button>
                    <button class="menu-btn" onclick="setActiveMenu('smsbomber', 'Numara')"><i class="fas fa-sms"></i>SMS Bomber</button>
                </div>
            </div>
            
            <div class="content">
                <div class="dashboard">
                    <div class="stat-box">
                        <div class="stat-number">{{ get_user_count() }}</div>
                        <div class="stat-label">Toplam Kullanıcı</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{{ get_query_count() }}</div>
                        <div class="stat-label">Toplam Sorgu</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{{ session['query_count'] if 'query_count' in session else 0 }}</div>
                        <div class="stat-label">Sizin Sorgularınız</div>
                    </div>
                </div>
                
                <div class="welcome-banner">
                    <h2>C7KA Paneline Hoşgeldiniz</h2>
                    <p>Sorgularınızı güvenli şekilde yapabilirsiniz</p>
                </div>
                
                <div class="search-area">
                    <h2 class="search-title" id="search-title">Sorgu Seçin</h2>
                    <div id="input-fields">
                        <div class="input-group">
                            <label for="input1">Değer</label>
                            <input type="text" id="input1" placeholder="Değer girin...">
                        </div>
                        <div class="input-group" id="input2-group" style="display: none;">
                            <label for="input2">İkinci Değer</label>
                            <input type="text" id="input2" placeholder="İkinci değer girin...">
                        </div>
                    </div>
                    <button class="search-btn" onclick="runQuery()">SORGULA</button>
                </div>
                
                <div class="result-area">
                    <h2 class="result-title">SONUÇLAR</h2>
                    <div class="loading" id="loading"><i class="fas fa-spinner"></i> Sorgulanıyor...</div>
                    <div class="result-content" id="result">
                        Sonuçlar burada görünecek...
                    </div>
                </div>
                
                <div class="chat-container">
                    <h3>Toplu Sohbet</h3>
                    <div id="chat-messages">
                        {% for message in messages %}
                        <div class="chat-message">
                            <span class="message-user">{{ message[3] }}:</span> 
                            <span class="message-text">{{ message[2] }}</span>
                            <div class="message-time">{{ message[4] }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Mesajınızı yazın...">
                        <button onclick="sendMessage()">Gönder</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let activeApi = '';
            let input1Label = 'Değer';
            let input2Label = 'İkinci Değer';
            let needsSecondInput = false;
            
            function createFireballs() {
                const count = 15;
                for (let i = 0; i < count; i++) {
                    setTimeout(() => {
                        const fireball = document.createElement('div');
                        fireball.classList.add('fireball');
                        fireball.style.left = Math.random() * 100 + 'vw';
                        fireball.style.animationDuration = (Math.random() * 5 + 3) + 's';
                        document.body.appendChild(fireball);
                        
                        setTimeout(() => {
                            fireball.remove();
                        }, 8000);
                    }, i * 400);
                }
                
                setTimeout(createFireballs, 6000);
            }
            
            window.addEventListener('load', createFireballs);
            
            function setActiveMenu(api, label1, label2 = null) {
                console.log('setActiveMenu called with:', api, label1, label2);
                activeApi = api;
                input1Label = label1;
                needsSecondInput = !!label2;
                input2Label = label2 || 'İkinci Değer';
                
                const searchArea = document.querySelector('.search-area');
                searchArea.style.display = 'block';
                
                document.getElementById('search-title').textContent = api.toUpperCase() + ' Sorgusu';
                document.querySelector('#input-fields .input-group label').textContent = label1;
                document.getElementById('input1').placeholder = label1 + ' girin...';
                
                const input2Group = document.getElementById('input2-group');
                
                if (needsSecondInput) {
                    input2Group.style.display = 'block';
                    input2Group.querySelector('label').textContent = label2;
                    document.getElementById('input2').placeholder = label2 + ' girin...';
                } else {
                    input2Group.style.display = 'none';
                }
            }
            
            function sendMessage() {
                const messageInput = document.getElementById('chat-input');
                const message = messageInput.value.trim();
                
                if (!message) {
                    alert('Mesaj boş olamaz!');
                    return;
                }
                
                fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        messageInput.value = '';
                        location.reload();
                    } else {
                        alert(data.error || 'Mesaj gönderilirken hata oluştu!');
                    }
                })
                .catch(error => {
                    console.error('Hata:', error);
                    alert('Mesaj gönderilirken hata oluştu!');
                });
            }
            
            function runQuery() {
                console.log('runQuery called with activeApi:', activeApi);
                const input1 = document.getElementById('input1').value.trim();
                const input2 = needsSecondInput ? document.getElementById('input2').value.trim() : '';
                
                if (!input1 || (needsSecondInput && !input2)) {
                    alert('Lütfen tüm gerekli alanları doldurun!');
                    return;
                }
                
                if (!activeApi) {
                    alert('Lütfen bir sorgu türü seçin!');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').innerHTML = '';
                
                fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        api: activeApi,
                        input1: input1,
                        input2: input2
                    })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    if (data.error) {
                        document.getElementById('result').innerHTML = '<table><tr><td>Hata: ' + data.error + '</td></tr></table>';
                    } else {
                        displayResults(data.result);
                    }
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result').innerHTML = '<table><tr><td>Hata: ' + error.message + '</td></tr></table>';
                    console.error('Hata:', error);
                });
            }
            
            function displayResults(result) {
                try {
                    let data = result;
                    let tableHtml = '<table><tr>';
                    
                    // API'den gelen ham veriyi JSON olarak parse et
                    if (typeof result === 'string') {
                        try {
                            data = JSON.parse(result);
                        } catch (e) {
                            // JSON değilse, ham metni tabloya ekle
                            document.getElementById('result').innerHTML = '<table><tr><td>' + result + '</td></tr></table>';
                            return;
                        }
                    }

                    // Veriyi tabloya dönüştür
                    if (Array.isArray(data) && data.length > 0) {
                        // Dizi ise, ilk elemanın anahtarlarını başlık yap
                        const headers = Object.keys(data[0]);
                        tableHtml += headers.map(header => '<th>' + header + '</th>').join('');
                        tableHtml += '</tr>';

                        data.forEach(row => {
                            tableHtml += '<tr>';
                            headers.forEach(header => {
                                tableHtml += '<td>' + (row[header] || '') + '</td>';
                            });
                            tableHtml += '</tr>';
                        });
                    } else if (typeof data === 'object' && data !== null) {
                        // Tek bir nesne ise, anahtarlarını başlık yap
                        const headers = Object.keys(data);
                        tableHtml += headers.map(header => '<th>' + header + '</th>').join('');
                        tableHtml += '</tr><tr>';
                        headers.forEach(header => {
                            tableHtml += '<td>' + (data[header] || '') + '</td>';
                        });
                        tableHtml += '</tr>';
                    } else {
                        // Ne dizi ne de nesne ise, ham veriyi tabloya ekle
                        document.getElementById('result').innerHTML = '<table><tr><td>' + result + '</td></tr></table>';
                        return;
                    }

                    tableHtml += '</table>';
                    document.getElementById('result').innerHTML = tableHtml;
                } catch (e) {
                    document.getElementById('result').innerHTML = '<table><tr><td>Hata: ' + e.message + '</td></tr></table>';
                }
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM loaded');
            });
        </script>
    </body>
    </html>
    ''', user_data=user_data, messages=messages, get_user_count=get_user_count, get_query_count=get_query_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('c7ka_panel.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['query_count'] = 0
            return redirect(url_for('index'))
        else:
            return render_template_string('''
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Giriş Yap</title>
                <style>
                    body { background: linear-gradient(to bottom, #000000, #1a0000, #330000); color: #fff; font-family: Arial, sans-serif; }
                    .login-container { max-width: 400px; margin: 100px auto; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 10px; border: 1px solid #ff3300; }
                    .login-container h2 { color: #ff6600; text-align: center; }
                    .input-group { margin-bottom: 15px; }
                    .input-group label { display: block; color: #ff9900; }
                    .input-group input { width: 100%; padding: 10px; border: 1px solid #ff3300; background: #1a0000; color: #fff; border-radius: 5px; }
                    .login-btn { width: 100%; padding: 10px; background: #ff3300; border: none; color: #fff; border-radius: 5px; cursor: pointer; }
                    .login-btn:hover { background: #ff6600; }
                    .error { color: #ff3300; text-align: center; }
                </style>
            </head>
            <body>
                <div class="login-container">
                    <h2>Giriş Yap</h2>
                    <form method="POST">
                        <div class="input-group">
                            <label for="username">Kullanıcı Adı</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="input-group">
                            <label for="password">Şifre</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <button type="submit" class="login-btn">Giriş Yap</button>
                    </form>
                    <p class="error">Kullanıcı adı veya şifre yanlış!</p>
                    <p style="text-align: center;"><a href="{{ url_for('register') }}" style="color: #ff9900;">Hesabınız yok mu? Kayıt olun</a></p>
                </div>
            </body>
            </html>
            ''')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Giriş Yap</title>
        <style>
            body { background: linear-gradient(to bottom, #000000, #1a0000, #330000); color: #fff; font-family: Arial, sans-serif; }
            .login-container { max-width: 400px; margin: 100px auto; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 10px; border: 1px solid #ff3300; }
            .login-container h2 { color: #ff6600; text-align: center; }
            .input-group { margin-bottom: 15px; }
            .input-group label { display: block; color: #ff9900; }
            .input-group input { width: 100%; padding: 10px; border: 1px solid #ff3300; background: #1a0000; color: #fff; border-radius: 5px; }
            .login-btn { width: 100%; padding: 10px; background: #ff3300; border: none; color: #fff; border-radius: 5px; cursor: pointer; }
            .login-btn:hover { background: #ff6600; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>Giriş Yap</h2>
            <form method="POST">
                <div class="input-group">
                    <label for="username">Kullanıcı Adı</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="input-group">
                    <label for="password">Şifre</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Giriş Yap</button>
            </form>
            <p style="text-align: center;"><a href="{{ url_for('register') }}" style="color: #ff9900;">Hesabınız var mı? Giriş yap</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        
        conn = sqlite3.connect('c7ka_panel.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, email, full_name) VALUES (?, ?, ?, ?)",
                      (username, generate_password_hash(password), email, full_name))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string('''
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Kayıt Ol</title>
                <style>
                    body { background: linear-gradient(to bottom, #000000, #1a0000, #330000); color: #fff; font-family: Arial, sans-serif; }
                    .register-container { max-width: 400px; margin: 100px auto; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 10px; border: 1px solid #ff3300; }
                    .register-container h2 { color: #ff6600; text-align: center; }
                    .input-group { margin-bottom: 15px; }
                    .input-group label { display: block; color: #ff9900; }
                    .input-group input { width: 100%; padding: 10px; border: 1px solid #ff3300; background: #1a0000; color: #fff; border-radius: 5px; }
                    .register-btn { width: 100%; padding: 10px; background: #ff3300; border: none; color: #fff; border-radius: 5px; cursor: pointer; }
                    .register-btn:hover { background: #ff6600; }
                    .error { color: #ff3300; text-align: center; }
                </style>
            </head>
            <body>
                <div class="register-container">
                    <h2>Kayıt Ol</h2>
                    <form method="POST">
                        <div class="input-group">
                            <label for="username">Kullanıcı Adı</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="input-group">
                            <label for="password">Şifre</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <div class="input-group">
                            <label for="email">E-posta</label>
                            <input type="email" id="email" name="email" required>
                        </div>
                        <div class="input-group">
                            <label for="full_name">Tam Ad</label>
                            <input type="text" id="full_name" name="full_name" required>
                        </div>
                        <button type="submit" class="register-btn">Kayıt Ol</button>
                    </form>
                    <p class="error">Bu kullanıcı adı zaten alınmış!</p>
                    <p style="text-align: center;"><a href="{{ url_for('login') }}" style="color: #ff9900;">Hesabınız var mı? Giriş yap</a></p>
                </div>
            </body>
            </html>
            ''')
        finally:
            conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kayıt Ol</title>
        <style>
            body { background: linear-gradient(to bottom, #000000, #1a0000, #330000); color: #fff; font-family: Arial, sans-serif; }
            .register-container { max-width: 400px; margin: 100px auto; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 10px; border: 1px solid #ff3300; }
            .register-container h2 { color: #ff6600; text-align: center; }
            .input-group { margin-bottom: 15px; }
            .input-group label { display: block; color: #ff9900; }
            .input-group input { width: 100%; padding: 10px; border: 1px solid #ff3300; background: #1a0000; color: #fff; border-radius: 5px; }
            .register-btn { width: 100%; padding: 10px; background: #ff3300; border: none; color: #fff; border-radius: 5px; cursor: pointer; }
            .register-btn:hover { background: #ff6600; }
        </style>
    </head>
    <body>
        <div class="register-container">
            <h2>Kayıt Ol</h2>
            <form method="POST">
                <div class="input-group">
                    <label for="username">Kullanıcı Adı</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="input-group">
                    <label for="password">Şifre</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div class="input-group">
                    <label for="email">E-posta</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="input-group">
                    <label for="full_name">Tam Ad</label>
                    <input type="text" id="full_name" name="full_name" required>
                </div>
                <button type="submit" class="register-btn">Kayıt Ol</button>
            </form>
            <p style="text-align: center;"><a href="{{ url_for('login') }}" style="color: #ff9900;">Hesabınız var mı? Giriş yap</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_data = get_user_data(session['user_id'])
    
    if request.method == 'POST':
        email = request.form['email']
        full_name = request.form['full_name']
        profile_pic = request.files.get('profile_pic')
        
        conn = sqlite3.connect('c7ka_panel.db')
        c = conn.cursor()
        
        profile_pic_path = user_data[5]
        if profile_pic:
            filename = f"{session['user_id']}_{profile_pic.filename}"
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        c.execute("UPDATE users SET email = ?, full_name = ?, profile_pic = ? WHERE id = ?",
                  (email, full_name, profile_pic_path, session['user_id']))
        conn.commit()
        conn.close()
        
        return redirect(url_for('profile'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profil Düzenle</title>
        <style>
            body { background: linear-gradient(to bottom, #000000, #1a0000, #330000); color: #fff; font-family: Arial, sans-serif; }
            .profile-container { max-width: 500px; margin: 100px auto; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 10px; border: 1px solid #ff3300; }
            .profile-container h2 { color: #ff6600; text-align: center; }
            .input-group { margin-bottom: 15px; }
            .input-group label { display: block; color: #ff9900; }
            .input-group input { width: 100%; padding: 10px; border: 1px solid #ff3300; background: #1a0000; color: #fff; border-radius: 5px; }
            .profile-btn { width: 100%; padding: 10px; background: #ff3300; border: none; color: #fff; border-radius: 5px; cursor: pointer; }
            .profile-btn:hover { background: #ff6600; }
            .profile-pic { width: 100px; height: 100px; border-radius: 50%; display: block; margin: 0 auto 15px; }
        </style>
    </head>
    <body>
        <div class="profile-container">
            <h2>Profil Düzenle</h2>
            <img src="{{ user_data[5] if user_data and user_data[5] else 'https://via.placeholder.com/100' }}" class="profile-pic">
            <form method="POST" enctype="multipart/form-data">
                <div class="input-group">
                    <label for="email">E-posta</label>
                    <input type="email" id="email" name="email" value="{{ user_data[3] if user_data else '' }}" required>
                </div>
                <div class="input-group">
                    <label for="full_name">Tam Ad</label>
                    <input type="text" id="full_name" name="full_name" value="{{ user_data[4] if user_data else '' }}" required>
                </div>
                <div class="input-group">
                    <label for="profile_pic">Profil Resmi</label>
                    <input type="file" id="profile_pic" name="profile_pic">
                </div>
                <button type="submit" class="profile-btn">Kaydet</button>
            </form>
            <p style="text-align: center;"><a href="{{ url_for('index') }}" style="color: #ff9900;">Ana Sayfaya Dön</a></p>
        </div>
    </body>
    </html>
    ''', user_data=user_data)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('query_count', None)
    return redirect(url_for('login'))

@app.route('/query', methods=['POST'])
def query():
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız!'})
    
    data = request.get_json()
    api = data.get('api')
    input1 = data.get('input1')
    input2 = data.get('input2', '')
    
    if not api or api not in API_URLS:
        return jsonify({'error': 'Geçersiz API!'})
    
    if not input1:
        return jsonify({'error': 'Gerekli alanları doldurun!'})
    
    try:
        api_url = API_URLS[api](input1, input2)
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        result = response.text
        
        save_query_history(session['user_id'], api, f"{input1} {input2}".strip(), result)
        session['query_count'] = session.get('query_count', 0) + 1
        
        return jsonify({'result': result})
    except requests.RequestException as e:
        return jsonify({'error': str(e)})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız!'})
    
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Mesaj boş olamaz!'})
    
    try:
        add_message(session['user_id'], message)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Mesaj gönderilirken hata oluştu: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

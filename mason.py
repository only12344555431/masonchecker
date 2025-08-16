import subprocess
import sys
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import requests
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "cappybeam_secret_key_1234"

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

API_URLS = {
    "adsoyad": lambda ad, soyad: f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad}",
    "adsoyadil": lambda ad, soyad_il: f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={ad}&soyad={soyad_il.split(' ')[0] if soyad_il else ''}&il={soyad_il.split(' ')[1] if soyad_il and ' ' in soyad_il else ''}",
    "tcpro": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcpro.php?tc={tc}",
    "tcgsm": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tcgsm.php?tc={tc}",
    "tapu": lambda tc, _: f"https://api.hexnox.pro/sowixapi/tapu.php?tc={tc}",
    "sulale": lambda tc, _: f"https://api.hexnox.pro/sowixapi/sulale.php?tc={tc}",
    "okulno": lambda tc, _: f"https://api.hexnox.pro/sowixapi/okulno.php?tc={tc}",
    "isyeriyetkili": lambda tc, _: f"https://api.hexnox.pro/sowixapi/isyeriyetkili.php?tc={tc}",
    "gsmdetay": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsmdetay.php?gsm={gsm}",
    "gsm": lambda gsm, _: f"https://api.hexnox.pro/sowixapi/gsm.php?gsm={gsm}",
    "adres": lambda tc, _: f"https://api.hexnox.pro/sowixapi/adres.php?tc={tc}",
}

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>Giriş Yap - MASON</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Poppins',sans-serif;}
    body,html{height:100%;background:#fff;display:flex;justify-content:center;align-items:center;}
    .container {
      width: 360px;
      background: #fff;
      padding: 40px 30px;
      border-radius: 25px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.1);
      text-align:center;
      border: 1px solid #eee;
    }
    .logo {
      width: 120px;
      height: 120px;
      margin: 0 auto 25px;
      border-radius: 50%;
      overflow: hidden;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    .logo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
    }
    h2 {
      color: #333;
      margin-bottom: 30px;
      font-weight: 600;
      letter-spacing: 1px;
      font-size: 1.8rem;
    }
    label {
      display: block;
      text-align: left;
      margin-bottom: 8px;
      font-weight: 600;
      color: #555;
    }
    input {
      width: 100%;
      padding: 12px 15px;
      border-radius: 8px;
      border: 1px solid #ddd;
      margin-bottom: 20px;
      font-size: 1rem;
      outline:none;
      transition: 0.3s;
    }
    input:focus {
      border-color: #0a4cff;
      box-shadow: 0 0 0 2px rgba(10,76,255,0.2);
    }
    button {
      width: 100%;
      padding: 14px 0;
      background: #0a4cff;
      border: none;
      color: white;
      font-weight: 600;
      border-radius: 8px;
      font-size: 1rem;
      cursor: pointer;
      transition: 0.3s;
    }
    button:hover {
      background: #083ecf;
    }
    .error {
      margin-bottom: 15px;
      color: #e74c3c;
      font-weight: 600;
      font-size: 0.9rem;
    }
    .link {
      margin-top: 15px;
      font-size: 0.9rem;
      color: #666;
    }
    .link a {
      color: #0a4cff;
      text-decoration: none;
      font-weight: 600;
    }
    .link a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container" role="main">
    <div class="logo" aria-label="Cappy Logo">
      <img src="https://cdn.discordapp.com/attachments/1405999275141501008/1406335898353668196/Screenshot_2025-08-16-19-20-51-580_com.lyrebirdstudio.photo_background_changer-edit.jpg?ex=68a217de&is=68a0c65e&hm=9d3b15a79aea78ab5f96cba7c92da766ef73e05e6eb0d83312948f2d157e8b53&" alt="Cappy Logo"/>
    </div>
    <h2>Giriş Yap</h2>
    {% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
    <form method="POST" action="{{ url_for('login') }}" novalidate>
      <label for="username">Kullanıcı Adı</label>
      <input type="text" id="username" name="username" required autocomplete="username" />
      <label for="password">Şifre</label>
      <input type="password" id="password" name="password" required autocomplete="current-password" />
      <button type="submit">Giriş</button>
    </form>
    <div class="link" role="link" aria-label="Kayıt ol linki">
      Henüz hesabın yok mu? <a href="{{ url_for('register') }}">Kayıt Ol</a>
    </div>
  </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>Kayıt Ol - MASON</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Poppins',sans-serif;}
    body,html{height:100%;background:#fff;display:flex;justify-content:center;align-items:center;}
    .container {
      width: 360px;
      background: #fff;
      padding: 40px 30px;
      border-radius: 25px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.1);
      text-align:center;
      border: 1px solid #eee;
    }
    .logo {
      width: 120px;
      height: 120px;
      margin: 0 auto 25px;
      border-radius: 50%;
      overflow: hidden;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    .logo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
    }
    h2 {
      color: #333;
      margin-bottom: 30px;
      font-weight: 600;
      letter-spacing: 1px;
      font-size: 1.8rem;
    }
    label {
      display: block;
      text-align: left;
      margin-bottom: 8px;
      font-weight: 600;
      color: #555;
    }
    input {
      width: 100%;
      padding: 12px 15px;
      border-radius: 8px;
      border: 1px solid #ddd;
      margin-bottom: 20px;
      font-size: 1rem;
      outline:none;
      transition: 0.3s;
    }
    input:focus {
      border-color: #0a4cff;
      box-shadow: 0 0 0 2px rgba(10,76,255,0.2);
    }
    button {
      width: 100%;
      padding: 14px 0;
      background: #0a4cff;
      border: none;
      color: white;
      font-weight: 600;
      border-radius: 8px;
      font-size: 1rem;
      cursor: pointer;
      transition: 0.3s;
    }
    button:hover {
      background: #083ecf;
    }
    .error {
      margin-bottom: 15px;
      color: #e74c3c;
      font-weight: 600;
      font-size: 0.9rem;
    }
    .link {
      margin-top: 15px;
      font-size: 0.9rem;
      color: #666;
    }
    .link a {
      color: #0a4cff;
      text-decoration: none;
      font-weight: 600;
    }
    .link a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container" role="main">
    <div class="logo" aria-label="Cappy Logo">
      <img src="https://cdn.discordapp.com/attachments/1405999275141501008/1406335898353668196/Screenshot_2025-08-16-19-20-51-580_com.lyrebirdstudio.photo_background_changer-edit.jpg?ex=68a217de&is=68a0c65e&hm=9d3b15a79aea78ab5f96cba7c92da766ef73e05e6eb0d83312948f2d157e8b53&" alt="Cappy Logo"/>
    </div>
    <h2>Kayıt Ol</h2>
    {% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
    <form method="POST" action="{{ url_for('register') }}" novalidate>
      <label for="username">Kullanıcı Adı</label>
      <input type="text" id="username" name="username" required autocomplete="username" />
      <label for="password">Şifre</label>
      <input type="password" id="password" name="password" required autocomplete="new-password" />
      <label for="password2">Şifre Tekrar</label>
      <input type="password" id="password2" name="password2" required autocomplete="new-password" />
      <button type="submit">Kayıt Ol</button>
    </form>
    <div class="link" role="link" aria-label="Giriş yap linki">
      Zaten hesabın var mı? <a href="{{ url_for('login') }}">Giriş Yap</a>
    </div>
  </div>
</body>
</html>
"""

PANEL_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>MASON! Panel</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');
    *{margin:0;padding:0;box-sizing:border-box;font-family:'Poppins',sans-serif;}
    body,html {
      height: 100%;
      background: #fff;
      color: #333;
      display: flex;
      flex-direction: column;
      font-size: 15px;
    }
    header {
      background: #fff;
      color: #333;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      border-bottom: 1px solid #eee;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    header h1 {
      font-weight: 700;
      font-size: 1.4rem;
      letter-spacing: 1px;
      user-select:none;
      color: #0a4cff;
    }
    #logout-btn {
      background: #f8f9fa;
      border: 1px solid #ddd;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      color: #333;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.3s ease;
    }
    #logout-btn:hover {
      background: #e9ecef;
      border-color: #ccc;
    }
    main {
      flex-grow: 1;
      display: flex;
      height: calc(100vh - 64px);
      overflow: hidden;
      background: #fff;
    }
    nav {
      width: 240px;
      background: #fff;
      border-right: 1px solid #eee;
      padding: 1.2rem 1rem;
      overflow-y: auto;
      box-shadow: 2px 0 10px rgba(0,0,0,0.02);
      transition: transform 0.3s ease;
    }
    nav.hide {
      transform: translateX(-100%);
    }
    nav h2 {
      font-weight: 600;
      margin-bottom: 1rem;
      color: #555;
      user-select:none;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid #eee;
      font-size: 1.1rem;
    }
    nav ul {
      list-style: none;
    }
    nav ul li {
      margin-bottom: 0.5rem;
    }
    nav ul li button {
      width: 100%;
      background: transparent;
      border: none;
      text-align: left;
      padding: 0.5rem 0.8rem;
      border-radius: 6px;
      font-weight: 500;
      color: #555;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
    }
    nav ul li button i {
      margin-right: 8px;
      font-size: 1rem;
      width: 20px;
      text-align: center;
    }
    nav ul li button:hover,
    nav ul li button.active {
      background: #f0f5ff;
      color: #0a4cff;
    }
    nav ul li button.active {
      font-weight: 600;
    }
    #hamburger {
      position: absolute;
      top: 15px;
      left: 15px;
      width: 30px;
      height: 24px;
      display: none;
      flex-direction: column;
      justify-content: space-between;
      cursor: pointer;
      z-index: 1001;
    }
    #hamburger div {
      height: 3px;
      background: #333;
      border-radius: 3px;
      transition: 0.3s ease;
    }
    #hamburger.active div:nth-child(1) {
      transform: translateY(10px) rotate(45deg);
    }
    #hamburger.active div:nth-child(2) {
      opacity: 0;
    }
    #hamburger.active div:nth-child(3) {
      transform: translateY(-10px) rotate(-45deg);
    }
    section#content {
      flex-grow: 1;
      padding: 1.5rem 2rem;
      overflow-y: auto;
      background: #fff;
      user-select:none;
    }
    .home-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      padding: 2rem;
    }
    .home-logo {
      width: 180px;
      height: 180px;
      margin-bottom: 2rem;
      border-radius: 50%;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      border: 5px solid #f0f5ff;
    }
    .home-logo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 50%;
    }
    .home-title {
      font-size: 2.2rem;
      font-weight: 700;
      color: #0a4cff;
      margin-bottom: 1rem;
    }
    .home-subtitle {
      font-size: 1.1rem;
      color: #666;
      max-width: 600px;
      line-height: 1.6;
    }
    form {
      max-width: 500px;
      margin-top: 1rem;
      background: #fff;
      padding: 1.5rem;
      border-radius: 10px;
      box-shadow: 0 2px 15px rgba(0,0,0,0.05);
      border: 1px solid #eee;
    }
    label {
      display: block;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #555;
      font-size: 0.95rem;
    }
    input[type="text"],
    input[type="tel"] {
      width: 100%;
      padding: 0.6rem 0.8rem;
      font-size: 0.95rem;
      border-radius: 6px;
      border: 1px solid #ddd;
      margin-bottom: 1rem;
      outline: none;
      transition: 0.3s;
      color: #333;
      background: #f9f9f9;
    }
    input[type="text"]:focus,
    input[type="tel"]:focus {
      border-color: #0a4cff;
      box-shadow: 0 0 0 2px rgba(10,76,255,0.1);
      background: #fff;
    }
    button.submit-btn {
      background: #0a4cff;
      border: none;
      padding: 0.7rem 1.2rem;
      border-radius: 6px;
      font-weight: 600;
      color: white;
      font-size: 0.95rem;
      cursor: pointer;
      transition: background 0.3s ease;
      width: 100%;
    }
    button.submit-btn:hover {
      background: #083ecf;
    }
    .result-container {
      margin-top: 1.5rem;
      border: 1px solid #eee;
      border-radius: 8px;
      padding: 0;
      background: #fff;
      box-shadow: 0 2px 15px rgba(0,0,0,0.05);
      font-family: 'Courier New', Courier, monospace;
      font-size: 0.9rem;
      color: #333;
      max-height: 500px;
      overflow-y: auto;
      user-select: text;
    }
    .result-table {
      width: 100%;
      border-collapse: collapse;
    }
    .result-table th {
      background: #f5f5f5;
      padding: 0.6rem 0.8rem;
      text-align: left;
      font-weight: 600;
      font-size: 0.85rem;
      color: #555;
      border-bottom: 1px solid #eee;
    }
    .result-table td {
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid #eee;
      font-size: 0.85rem;
    }
    .result-table tr:last-child td {
      border-bottom: none;
    }
    .result-table tr:hover td {
      background: #f9f9f9;
    }
    .loading {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 3px solid rgba(10,76,255,0.2);
      border-radius: 50%;
      border-top-color: #0a4cff;
      animation: spin 1s ease-in-out infinite;
      margin-right: 10px;
      vertical-align: middle;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    @media (max-width: 850px) {
      nav {
        position: fixed;
        top: 0;
        left: 0;
        height: 100%;
        z-index: 1000;
        transform: translateX(-100%);
        background: #fff;
        box-shadow: 3px 0 15px rgba(0,0,0,0.1);
      }
      nav.show {
        transform: translateX(0);
      }
      #hamburger {
        display: flex;
      }
      main {
        flex-direction: column;
        height: auto;
      }
      section#content {
        padding: 1.2rem;
      }
      .home-logo {
        width: 140px;
        height: 140px;
      }
      .home-title {
        font-size: 1.8rem;
      }
    }
  </style>
  <link rel="stylesheet" href="https://cdn.discordapp.com/attachments/1405999275141501008/1406335898353668196/Screenshot_2025-08-16-19-20-51-580_com.lyrebirdstudio.photo_background_changer-edit.jpg?ex=68a217de&is=68a0c65e&hm=9d3b15a79aea78ab5f96cba7c92da766ef73e05e6eb0d83312948f2d157e8b53&">
</head>
<body>
<header>
  <h1>MASONLAR PANEL!</h1>
  <button id="logout-btn" aria-label="Çıkış yap"><i class="fas fa-sign-out-alt"></i> Çıkış Yap</button>
  <div id="hamburger" aria-label="Menüyü aç/kapat" role="button" tabindex="0" aria-expanded="false">
    <div></div><div></div><div></div>
  </div>
</header>
<main>
  <nav aria-label="Sorgu menüsü">
    <h2>Sorgular</h2>
    <ul>
      <li><button class="query-btn active" data-query="home"><i class="fas fa-home"></i> Anasayfa</button></li>
      <li><button class="query-btn" data-query="adsoyad"><i class="fas fa-user"></i> Ad Soyad</button></li>
      <li><button class="query-btn" data-query="adsoyadil"><i class="fas fa-user-tag"></i> Ad Soyad İl</button></li>
      <li><button class="query-btn" data-query="tcpro"><i class="fas fa-id-card"></i> TC Kimlik No</button></li>
      <li><button class="query-btn" data-query="tcgsm"><i class="fas fa-phone"></i> TC GSM</button></li>
      <li><button class="query-btn" data-query="tapu"><i class="fas fa-home"></i> Tapu</button></li>
      <li><button class="query-btn" data-query="sulale"><i class="fas fa-users"></i> Sülale</button></li>
      <li><button class="query-btn" data-query="okulno"><i class="fas fa-school"></i> Okul No</button></li>
      <li><button class="query-btn" data-query="isyeriyetkili"><i class="fas fa-briefcase"></i> İşyeri Yetkili</button></li>
      <li><button class="query-btn" data-query="gsmdetay"><i class="fas fa-mobile-alt"></i> GSM Detay</button></li>
      <li><button class="query-btn" data-query="gsm"><i class="fas fa-phone-alt"></i> GSM</button></li>
      <li><button class="query-btn" data-query="adres"><i class="fas fa-map-marker-alt"></i> Adres</button></li>
    </ul>
  </nav>
  <section id="content" tabindex="0" aria-live="polite" aria-atomic="true">
    <div class="home-container" id="home-container">
      <div class="home-logo">
        <img src="https://cdn.discordapp.com/attachments/1405999275141501008/1406335898353668196/Screenshot_2025-08-16-19-20-51-580_com.lyrebirdstudio.photo_background_changer-edit.jpg?ex=68a217de&is=68a0c65e&hm=9d3b15a79aea78ab5f96cba7c92da766ef73e05e6eb0d83312948f2d157e8b53&" alt="Cappy Logo"/>
      </div>
      <h1 class="home-title">MASONLAR PANEL</h1>
      <p class="home-subtitle">
        Hoşgeldin, {{ session['user'] }}!<br />
        Sol menüden sorgu seçip sorgularınızı güvenli bir şekilde yapabilirsiniz.
      </p>
    </div>
    <form id="query-form" style="display:none;" aria-label="Sorgu formu">
      <label id="label1" for="input1">Ad:</label>
      <input type="text" id="input1" name="input1" required autocomplete="off" />
      <label id="label2" for="input2">Soyad/İl (Opsiyonel):</label>
      <input type="text" id="input2" name="input2" autocomplete="off" placeholder="Sadece soyad veya 'soyad il' şeklinde girin" />
      <button type="submit" class="submit-btn" aria-label="Sorguyu çalıştır"><i class="fas fa-search"></i> Sorgula</button>
    </form>
    <div class="result-container" id="result-container" aria-live="polite" aria-atomic="true" style="display:none;"></div>
  </section>
</main>

<script>
  const hamburger = document.getElementById('hamburger');
  const nav = document.querySelector('nav');
  hamburger.addEventListener('click', () => {
    nav.classList.toggle('show');
    hamburger.classList.toggle('active');
    const expanded = hamburger.getAttribute('aria-expanded') === 'true' || false;
    hamburger.setAttribute('aria-expanded', !expanded);
  });
  hamburger.addEventListener('keydown', e => {
    if(e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      hamburger.click();
    }
  });

  const queryButtons = document.querySelectorAll('.query-btn');
  const form = document.getElementById('query-form');
  const label1 = document.getElementById('label1');
  const label2 = document.getElementById('label2');
  const input1 = document.getElementById('input1');
  const input2 = document.getElementById('input2');
  const resultContainer = document.getElementById('result-container');
  const homeContainer = document.getElementById('home-container');

  const queryLabels = {
    "adsoyad": ["Ad", "Soyad"],
    "adsoyadil": ["Ad", "Soyad veya Soyad+İl (Opsiyonel)"],
    "tcpro": ["TC Kimlik No", ""],
    "tcgsm": ["TC Kimlik No", ""],
    "tapu": ["TC Kimlik No", ""],
    "sulale": ["TC Kimlik No", ""],
    "okulno": ["TC Kimlik No", ""],
    "isyeriyetkili": ["TC Kimlik No", ""],
    "gsmdetay": ["GSM Numarası", ""],
    "gsm": ["GSM Numarası", ""],
    "adres": ["TC Kimlik No", ""]
  };

  function updateFormFields(queryKey) {
    if(queryKey === "home") {
      homeContainer.style.display = "flex";
      form.style.display = "none";
      resultContainer.style.display = "none";
      return;
    }
    
    const labels = queryLabels[queryKey] || ["Input1","Input2"];
    label1.textContent = labels[0];
    label2.textContent = labels[1];
    input1.value = "";
    input2.value = "";
    if(labels[1] === "") {
      label2.style.display = "none";
      input2.style.display = "none";
      input2.required = false;
    } else {
      label2.style.display = "block";
      input2.style.display = "block";
      input2.required = false; // Ad Soyad İl için opsiyonel yapıldı
      if(queryKey === "adsoyadil") {
        input2.placeholder = "Sadece soyad veya 'soyad il' şeklinde girin";
      } else {
        input2.placeholder = "";
      }
    }
    resultContainer.textContent = "";
    resultContainer.style.display = "none";
    homeContainer.style.display = "none";
    form.style.display = "block";
    input1.focus();
  }

  let currentQuery = "home";
  updateFormFields(currentQuery);

  queryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      queryButtons.forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      currentQuery = btn.dataset.query;
      updateFormFields(currentQuery);
      if(window.innerWidth <= 850){
        nav.classList.remove('show');
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', false);
      }
    });
  });

  function createTableFromData(data) {
    if (!data) return "<p>Sonuç bulunamadı.</p>";
    
    // API'den direkt dizi geliyorsa (sülale sorgusu gibi)
    if (Array.isArray(data)) {
      if (data.length === 0) return "<p>Sonuç bulunamadı.</p>";
      
      // Tüm olası sütunları bul
      const allColumns = new Set();
      data.forEach(item => {
        Object.keys(item).forEach(key => allColumns.add(key));
      });
      const columns = Array.from(allColumns);
      
      let html = '<table class="result-table"><thead><tr>';
      
      // Başlıkları oluştur
      columns.forEach(column => {
        html += `<th>${column.toUpperCase()}</th>`;
      });
      html += '</tr></thead><tbody>';
      
      // Veri satırlarını oluştur
      data.forEach(row => {
        html += '<tr>';
        columns.forEach(column => {
          html += `<td>${row[column] || ''}</td>`;
        });
        html += '</tr>';
      });
      
      html += '</tbody></table>';
      return html;
    }
    
    // Tek bir nesne geliyorsa
    if (typeof data === 'object') {
      let html = '<table class="result-table"><tbody>';
      for (const key in data) {
        if (data.hasOwnProperty(key)) {
          // Eğer value bir nesne ise, string'e çevir
          const value = typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key];
          html += `<tr><th>${key.toUpperCase()}</th><td>${value || ''}</td></tr>`;
        }
      }
      html += '</tbody></table>';
      return html;
    }
    
    // Diğer durumlar (string, number vs.)
    return `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    resultContainer.innerHTML = '<div style="padding:1rem;text-align:center;"><span class="loading"></span> Sorgulanıyor, lütfen bekleyin...</div>';
    resultContainer.style.display = "block";
    
    const val1 = input1.value.trim();
    const val2 = input2.value.trim();
    
    if(val1 === "" || (input2.required && val2 === "")) {
      resultContainer.innerHTML = '<div style="padding:1rem;color:#e74c3c;font-weight:600;">Lütfen tüm zorunlu alanları doldurunuz.</div>';
      return;
    }
    
    fetch("/api/query", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        query: currentQuery,
        val1: val1,
        val2: val2
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('API hatası');
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        resultContainer.innerHTML = `<div style="padding:1rem;color:#e74c3c;font-weight:600;">Hata: ${data.error}</div>`;
      } else {
        resultContainer.innerHTML = createTableFromData(data.result);
      }
    })
    .catch(error => {
      resultContainer.innerHTML = `<div style="padding:1rem;color:#e74c3c;font-weight:600;">İstek sırasında hata oluştu: ${error.message}</div>`;
    });
  });

  // Çıkış butonu
  document.getElementById("logout-btn").addEventListener("click", () => {
    window.location.href = "/logout";
  });
</script>

</body>
</html>
"""

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        if username in users and check_password_hash(users[username]["password"], password):
            session["user"] = username
            return redirect(url_for("panel"))
        else:
            error = "Kullanıcı adı veya şifre hatalı."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if not username or not password or not password2:
            error = "Tüm alanları doldurun."
        elif password != password2:
            error = "Şifreler eşleşmiyor."
        else:
            users = load_users()
            if username in users:
                error = "Bu kullanıcı adı zaten alınmış."
            else:
                users[username] = {
                    "password": generate_password_hash(password)
                }
                save_users(users)
                session["user"] = username
                return redirect(url_for("panel"))
    return render_template_string(REGISTER_HTML, error=error)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/panel")
@login_required
def panel():
    return render_template_string(PANEL_HTML)

@app.route("/api/query", methods=["POST"])
@login_required
def api_query():
    data = request.get_json()
    query = data.get("query")
    val1 = data.get("val1")
    val2 = data.get("val2")

    if query not in API_URLS:
        return jsonify({"error": "Geçersiz sorgu tipi."})

    url_func = API_URLS[query]

    try:
        # Ad Soyad İl sorgusu için özel işleme
        if query == "adsoyadil":
            # Eğer val2 boş değilse ve içinde boşluk varsa, soyad ve il olarak ayır
            if val2 and ' ' in val2:
                parts = val2.split(' ')
                soyad = parts[0]
                il = ' '.join(parts[1:])  # Birden fazla kelimeli iller için
                url = f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={val1}&soyad={soyad}&il={il}"
            elif val2:
                # Sadece soyad girilmişse
                url = f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={val1}&soyad={val2}"
            else:
                # Sadece ad girilmişse
                url = f"https://api.hexnox.pro/sowixapi/adsoyadilice.php?ad={val1}"
        else:
            url = url_func(val1, val2)
            
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        
        # API yanıtını işle
        try:
            result = r.json()
            # Eğer API'den direkt dizi geliyorsa (sülale sorgusu gibi)
            if isinstance(result, list):
                return jsonify({"result": result})
            # Eğer bir obje geliyorsa ve içinde data veya results gibi bir anahtar varsa
            elif isinstance(result, dict) and ("data" in result or "results" in result):
                return jsonify({"result": result.get("data", result.get("results"))})
            else:
                return jsonify({"result": result})
        except ValueError:
            return jsonify({"result": r.text})
    except Exception as e:
        return jsonify({"error": f"API sorgusu başarısız: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

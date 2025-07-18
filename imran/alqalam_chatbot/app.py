import json
import logging
import threading
import nest_asyncio
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import pymysql
import pymysql.cursors
from datetime import datetime

# --- Flask App Setup ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "alqalam_secret_key"  # Use a secure key in production

# --- MySQL Config ---
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'alqalam_db'

# --- DB Connection ---
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

# --- Load Data ---
with open('school_data.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)
    aliases = full_data.get("aliases", {})

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM admins WHERE username=%s AND password=%s', (username, password))
                user = cursor.fetchone()
            conn.close()

            if user:
                session['username'] = username
                return redirect(url_for('admin_dashboard'))
            else:
                error = "Invalid login!"
        except Exception as e:
            error = f"Login error: {str(e)}"
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/get_data')
def get_data():
    return jsonify(full_data)

@app.route('/save_data', methods=['POST'])
def save_data():
    if 'username' not in session:
        return jsonify({"status": "unauthorized"})

    try:
        new_data = request.get_json()
        with open('school_data.json', 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO change_logs (username, details, change_time) VALUES (%s, %s, %s)", (
    session['username'],
    "Updated school_data.json",
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))
            conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route('/add_admin', methods=['POST'])
def add_admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Handle normal form submission (from dashboard.html)
    new_user = request.form.get("new_username")
    new_pass = request.form.get("new_password")

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (new_user, new_pass))
            conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        return render_template("dashboard.html", username=session["username"], error=str(e))



# --- Telegram Bot Logic ---
# --- Resolve Nested Path like "staff.vice_chancellor" ---
def resolve_nested_path(base, path):
    keys = path.split(".")
    current = base
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

# --- Smart Search Function with Root Detection ---
def search_data(query):
    query = query.strip().lower()
    resolved_path = aliases.get(query, query)

    # If it's a nested path like staff.chancellor
    if "." in resolved_path:
        root_key, sub_path = resolved_path.split(".", 1)
        section = full_data.get(root_key, {})
        return resolve_nested_path(section, sub_path)

    # If it's a top-level path like "staff" or "school_info"
    if resolved_path in full_data:
        return full_data[resolved_path]

    # Otherwise check each root section
    for root_key in ["data", "school_info", "staff"]:
        section = full_data.get(root_key, {})
        result = resolve_nested_path(section, resolved_path)
        if result is not None:
            return result

    return None

# --- Keyboard ---
alias_buttons = list(aliases.keys())
keyboard = [alias_buttons[i:i + 3] for i in range(0, len(alias_buttons), 3)]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Telegram Bot ---
BOT_TOKEN = "7850063077:AAGy85EYNzKDf05AGmXdIu_nVqsujyihlxs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Ask about anything Al-Qalam-related!", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()
    result = search_data(query)

    if result:
        if isinstance(result, (dict, list)):
            text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            text = str(result)
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❓ I couldn’t find that. Try a different keyword.")
        
def telegram_thread():
    nest_asyncio.apply()
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot is running...")
    app_telegram.run_polling()

# =================== Run App ===================
if __name__ == '__main__':
    threading.Thread(target=telegram_thread, daemon=True).start()
    print("🌐 Flask server is running at http://127.0.0.1:5000")
    app.run(debug=False, use_reloader=False)

    
#cd C:\Users\user\Desktop\imran\alqalam_chatbot
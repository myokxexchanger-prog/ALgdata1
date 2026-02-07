## bot.py  (PostgreSQL SAFE – FULL FIX, nothing removed)

import telebot
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import psycopg2
import time
import os

# ======================
# DATABASE CONNECTION
# ======================
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# ======================
# GLOBAL STATES
# ======================
admin_states = {}
last_menu_msg = {}
last_category_msg = {}
last_allfilms_msg = {}
allfilms_sessions = {}
cart_sessions = {}
series_sessions = {}
user_states = {}

# =========================
# DATABASE TABLES (SAFE)
# =========================

# -------- MOVIES --------
cur.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price INTEGER,
    file_id TEXT,
    file_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")

# -------- ITEMS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price INTEGER,
    file_id TEXT,
    file_name TEXT,
    group_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")

# -------- ORDERS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id BIGINT,
    movie_id INTEGER,
    item_id INTEGER,
    amount INTEGER,
    paid INTEGER DEFAULT 0,
    pay_ref TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- ORDER ITEMS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id TEXT,
    movie_id INTEGER,
    item_id INTEGER,
    price INTEGER,
    file_id TEXT
)
""")

# -------- WEEKLY --------
cur.execute("""
CREATE TABLE IF NOT EXISTS weekly (
    id SERIAL PRIMARY KEY,
    poster_file_id TEXT,
    items TEXT,
    file_name TEXT,
    file_id TEXT,
    channel_msg_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- CART --------
cur.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    movie_id INTEGER,
    item_id INTEGER,
    price INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- REFERRALS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT,
    referred_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reward_granted INTEGER DEFAULT 0
)
""")

# -------- REORDERS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS reorders (
    old_order_id INTEGER,
    new_order_id INTEGER,
    user_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (old_order_id, user_id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS referral_credits (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT,
    amount INTEGER,
    used INTEGER DEFAULT 0,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- USER PREFS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS user_prefs (
    user_id BIGINT PRIMARY KEY,
    lang TEXT DEFAULT 'ha'
)
""")

# -------- USER LIBRARY --------
cur.execute("""
CREATE TABLE IF NOT EXISTS user_library (
    user_id BIGINT NOT NULL,
    movie_id INTEGER,
    item_id INTEGER,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id, item_id)
)
""")

# -------- BUY ALL TOKENS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS buyall_tokens (
    token TEXT PRIMARY KEY,
    ids TEXT
)
""")

# -------- USER MOVIES --------
cur.execute("""
CREATE TABLE IF NOT EXISTS user_movies (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    movie_id INTEGER,
    item_id INTEGER,
    order_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resend_count INTEGER DEFAULT 0
)
""")

# =====================
# SERIES
# =====================
cur.execute("""
CREATE TABLE IF NOT EXISTS series (
    id SERIAL PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    file_id TEXT,
    price INTEGER,
    poster_file_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    channel_msg_id INTEGER,
    channel_username TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS series_items (
    id SERIAL PRIMARY KEY,
    series_id INTEGER,
    movie_id INTEGER,
    item_id INTEGER,
    file_id TEXT,
    title TEXT,
    order_id TEXT,
    price INTEGER DEFAULT 0,
    channel_msg_id INTEGER,
    channel_username TEXT,
    file_name TEXT
)
""")

# =====================
# FEEDBACK
# =====================
cur.execute("""
CREATE TABLE IF NOT EXISTS feedbacks (
    id SERIAL PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    mood TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS resend_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    used_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =====================
# HAUSA SERIES
# =====================
cur.execute("""
CREATE TABLE IF NOT EXISTS hausa_series (
    id SERIAL PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    file_id TEXT,
    price INTEGER,
    series_id TEXT,
    poster_file_id TEXT,
    channel_msg_id INTEGER,
    channel_username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS hausa_series_items (
    id SERIAL PRIMARY KEY,
    hausa_series_id INTEGER,
    movie_id INTEGER,
    item_id INTEGER,
    price INTEGER,
    file_id TEXT,
    title TEXT,
    order_id TEXT,
    series_id INTEGER,
    channel_msg_id INTEGER,
    channel_username TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT
)
""")

# ================= VISITED USERS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS visited_users (
    user_id BIGINT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------- ADMIN CONTROLS --------
cur.execute("""
CREATE TABLE IF NOT EXISTS admin_controls (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT UNIQUE,
    sendmovie_enabled INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= HOW TO BUY =================
cur.execute("""
CREATE TABLE IF NOT EXISTS how_to_buy (
    id SERIAL PRIMARY KEY,
    hausa_text TEXT,
    english_text TEXT,
    media_file_id TEXT,
    media_type TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("✅ DATABASE READY — BIGINT FIX APPLIED")
import uuid
import re
import json
import requests
import traceback
import random
import difflib
from datetime import datetime, timedelta
import urllib.parse
import os
import hmac
import hashlib

admin_states = {}

# --- Admins configuration ---
ADMINS = [6603268127]

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_MODE = os.getenv("BOT_MODE", "polling")

ADMIN_ID = 6603268127
OTP_ADMIN_ID = 6603268127

BOT_USERNAME = "Algaitabot"
CHANNEL = "@Algaitamoviestore"

# ========= DATABASE CONFIG =========
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")
# ========= PAYSTACK CONFIG =========
PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET")
PAYSTACK_PUBLIC = os.getenv("PAYSTACK_PUBLIC")
PAYSTACK_REDIRECT_URL = os.getenv("PAYSTACK_REDIRECT_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

PAYSTACK_BASE = "https://api.paystack.co"

# === PAYMENTS / STORAGE ===
PAYMENT_NOTIFY_GROUP = -1003555015230
STORAGE_CHANNEL = -1003520788779
SEND_ADMIN_PAYMENT_NOTIF = False

ADMIN_USERNAME = "CEOalgaitabot"
#end

# ========= IMPORTS =========
import telebot
import hmac
import hashlib
import requests
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# ========= BOT =========
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# ========= FLASK =========
app = Flask(__name__)

import time

def create_paystack_payment(user_id, order_id, amount, title):
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    payload = {
        "reference": f"{order_id}_{int(time.time())}",  # ✅ FIX
        "amount": int(amount) * 100,
        "currency": "NGN",
        "callback_url": PAYSTACK_REDIRECT_URL,
        "email": f"user{user_id}@telegram.com",
        "metadata": {
            "order_id": str(order_id),
            "user_id": user_id,
            "title": title[:50]
        }
    }

    r = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=30
    )

    data = r.json()
    if not data.get("status"):
        return None

    return data["data"]["authorization_url"]



# ========= HOME / KEEP ALIVE =========
@app.route("/")
def home():
    return "OK", 200


# ========= CALLBACK PAGE =========
@app.route("/paystack-callback", methods=["GET"])
def paystack_callback():
    return """
    <html>
    <head>
        <title>Payment Successful</title>
        <meta http-equiv="refresh" content="5;url=https://t.me/Aslamtv2bot">
    </head>
    <body style="font-family: Arial; text-align: center; padding-top: 150px; font-size: 22px;">
        <h2>✅ Payment Successful</h2>
        <p>An tabbatar da biyan ka.</p>
        <p>Kashe browser ka koma telegram</p>
        <a href="https://t.me/Algaitabot">Komawa Telegram yanzu</a>
    </body>
    </html>
    """

# ========= FEEDBACK =========
def send_feedback_prompt(user_id, order_id):
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM feedbacks WHERE order_id = %s",
        (order_id,)
    )
    exists = cur.fetchone()
    cur.close()

    if exists:
        return

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("😁 Very good", callback_data=f"feedback:very:{order_id}"),
        InlineKeyboardButton("🙂 Good", callback_data=f"feedback:good:{order_id}")
    )
    kb.add(
        InlineKeyboardButton("😓 Not sure", callback_data=f"feedback:neutral:{order_id}"),
        InlineKeyboardButton("😠 Angry", callback_data=f"feedback:angry:{order_id}")
    )

    bot.send_message(
        user_id,
        "We hope you enjoyed your shopping 🥰\nPlease choose how you’re feeling right now.",
        reply_markup=kb
    )
# ========= PAYSTACK WEBHOOK (POSTGRES - CLEAN) =========
@app.route("/webhook", methods=["POST"])
def paystack_webhook():

    # ================= SIGNATURE =================
    signature = request.headers.get("x-paystack-signature")

    if not signature:
        return "Missing signature", 401

    computed = hmac.new(
        PAYSTACK_SECRET.encode(),
        request.data,
        hashlib.sha512
    ).hexdigest()

    if signature != computed:
        return "Invalid signature", 401

    # ================= PAYLOAD =================
    payload = request.json or {}

    event = payload.get("event")
    if event != "charge.success":
        return "Ignored", 200

    data = payload.get("data", {})

    raw_reference = data.get("reference")
    currency = data.get("currency")
    paid_amount = int(data.get("amount", 0) / 100)

    # ================= FIX REFERENCE =================
    metadata = data.get("metadata", {}) or {}
    order_id = metadata.get("order_id")

    if not order_id and raw_reference:
        order_id = raw_reference.split("_")[0]

    if not order_id:
        return "Order ID missing", 200

    # ================= DB =================
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id, amount, paid
        FROM orders
        WHERE id=%s
        """,
        (order_id,)
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        return "Order not found", 200

    user_id, expected_amount, paid = row

    if paid == 1:
        cur.close()
        return "Already processed", 200

    if paid_amount != expected_amount or currency != "NGN":
        cur.close()
        return "Wrong payment", 200

    # ================= ITEMS =================
    cur.execute(
        "SELECT file_id FROM order_items WHERE order_id=%s",
        (order_id,)
    )
    items = cur.fetchall()

    if not items:
        cur.close()
        return "Empty order", 200

    # ================= MARK AS PAID =================
    cur.execute(
        "UPDATE orders SET paid=1 WHERE id=%s",
        (order_id,)
    )

    # ================= USER INFO (FULL NAME FIX) =================
    cur.execute(
        """
        SELECT first_name, last_name
        FROM visited_users
        WHERE user_id=%s
        """,
        (user_id,)
    )
    u = cur.fetchone()

    if u and (u[0] or u[1]):
        full_name = f"{u[0] or ''} {u[1] or ''}".strip()
    else:
        # fallback to Telegram profile (NOT username)
        try:
            chat = bot.get_chat(user_id)
            full_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
        except:
            full_name = "User"

    # ================= TITLES =================
    cur.execute(
        """
        SELECT i.title
        FROM order_items oi
        JOIN items i ON i.id = oi.item_id
        WHERE oi.order_id=%s
        """,
        (order_id,)
    )
    titles = [r[0] for r in cur.fetchall()]
    titles_text = ", ".join(titles) if titles else "N/A"

    conn.commit()
    cur.close()

    # ================= USER MESSAGE =================
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "⬇️ DOWNLOAD NOW",
            callback_data=f"deliver:{order_id}"
        )
    )

    bot.send_message(
        user_id,
        f"""🎉 <b>Payment Successful!</b>

👤 <b>Name:</b> {full_name}
🎬 <b>Items:</b> {titles_text}

🗃 <b>Order ID:</b>
<code>{order_id}</code>

💳 <b>Amount:</b> ₦{paid_amount}
""",
        parse_mode="HTML",
        reply_markup=kb
    )

    # ================= ADMIN / GROUP NOTIFICATION =================
    if PAYMENT_NOTIFY_GROUP:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        bot.send_message(
            PAYMENT_NOTIFY_GROUP,
            f"""✅ <b>NEW PAYMENT RECEIVED</b>

👤 User: {full_name}
🆔 User ID: <code>{user_id}</code>

🎬 Items: {titles_text}
🗃 Order ID: <code>{order_id}</code>
💰 Amount: ₦{paid_amount}
⏰ Time: {now}
""",
            parse_mode="HTML"
        )

    return "OK", 200




# 
# ========= TELEGRAM WEBHOOK =========
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

@bot.callback_query_handler(func=lambda c: c.data.startswith("deliver:"))
def deliver_items(call):
    user_id = call.from_user.id

    try:
        _, order_id = call.data.split(":", 1)
    except:
        bot.answer_callback_query(call.id, "❌ Invalid order info.")
        return

    cur = conn.cursor()

    # 1️⃣ CHECK ORDER (INT SAFE)
    cur.execute(
        "SELECT paid FROM orders WHERE id=%s AND user_id=%s",
        (order_id, user_id)
    )
    row = cur.fetchone()

    # ✅ FIX HERE
    if not row or row[0] != 1:
        cur.close()
        bot.answer_callback_query(
            call.id,
            "❌ Your payment has not been confirmed yet."
        )
        return

    # 2️⃣ PREVENT RESEND
    cur.execute(
        "SELECT 1 FROM user_movies WHERE order_id=%s LIMIT 1",
        (order_id,)
    )
    if cur.fetchone():
        cur.close()

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "📽 PAID MOVIES",
                callback_data="my_movies"
            )
        )

        bot.send_message(
            user_id,
            "ℹ️ You have already received this movie.\n\n"
            "📽 You can download it again from Paid Movies.",
            reply_markup=kb
        )
        return

    bot.answer_callback_query(call.id, "📤 Sending your items…")

    # 3️⃣ FETCH ITEMS
    cur.execute(
        """
        SELECT oi.item_id, oi.file_id, i.title
        FROM order_items oi
        JOIN items i ON i.id = oi.item_id
        WHERE oi.order_id=%s
        """,
        (order_id,)
    )
    items = cur.fetchall()

    if not items:
        cur.close()
        bot.send_message(user_id, "❌ Order items not found.")
        return

    sent = 0

    # 4️⃣ SEND ITEMS
    for item_id, file_id, title in items:
        if not file_id:
            continue

        cur.execute(
            "SELECT 1 FROM user_movies WHERE user_id=%s AND item_id=%s",
            (user_id, item_id)
        )
        if cur.fetchone():
            continue

        try:
            bot.send_video(user_id, file_id, caption=f"🎬 {title}")
        except:
            bot.send_document(user_id, file_id, caption=f"📁 {title}")

        cur.execute(
            """
            INSERT INTO user_movies (user_id, item_id, order_id)
            VALUES (%s,%s,%s)
            """,
            (user_id, item_id, order_id)
        )
        sent += 1

    conn.commit()
    cur.close()

    if sent == 0:
        bot.send_message(user_id, "❌ Items could not be sent.")
        return

    bot.send_message(
        user_id,
        f"✅ Your movie(s) have been delivered ({sent}).\n"
        "Thank you for your purchase 🤗"
    )

    send_feedback_prompt(user_id, order_id)
 #=========================================================
# ========= HARD START HOWTO (DEEPLINK LOCK) ===============
# =========================================================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.text.startswith("/start ")
        and len(m.text.split(" ", 1)) > 1
        and m.text.split(" ", 1)[1].startswith("howto_")
    )
)
def __hard_start_howto(msg):
    """
    Wannan handler:
    - Yana rike howto_ deeplink
    - Yana hana komawa main /start
    - Yana kira howto_start_handler kai tsaye
    """
    return howto_start_handler(msg)
# ================= HOW TO BUY STATE =================
HOWTO_STATE = {}


# ======================================================
# /update  (ADMIN ONLY)
# ======================================================
@bot.message_handler(commands=["update"])
def update_howto_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return

    HOWTO_STATE[m.from_user.id] = {"stage": "hausa"}

    bot.send_message(
        m.chat.id,
        "✍️ <b>Rubuta HAUSA version cikakke:</b>",
        parse_mode="HTML"
    )


# ======================================================
# UPDATE FLOW (HAUSA → ENGLISH → MEDIA)
# ======================================================
@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in HOWTO_STATE,
    content_types=["text", "video", "document", "photo"]
)
def howto_update_flow(m):
    state = HOWTO_STATE.get(m.from_user.id)
    if not state:
        return

    stage = state["stage"]

    # ---------- HAUSA ----------
    if stage == "hausa":
        if m.content_type != "text":
            bot.send_message(m.chat.id, "❌ Hausa text kawai ake bukata.")
            return
        state["hausa_text"] = m.text
        state["stage"] = "english"
        bot.send_message(
            m.chat.id,
            "✍️ <b>Rubuta ENGLISH version:</b>",
            parse_mode="HTML"
        )
        return

    # ---------- ENGLISH ----------
    if stage == "english":
        if m.content_type != "text":
            bot.send_message(m.chat.id, "❌ English text kawai ake bukata.")
            return
        state["english_text"] = m.text
        state["stage"] = "media"
        bot.send_message(
            m.chat.id,
            "🎬 Turo <b>VIDEO / DOCUMENT / PHOTO</b>:",
            parse_mode="HTML"
        )
        return

    # ---------- MEDIA ----------
    if stage == "media":
        file_id = None
        media_type = None

        if m.content_type == "video":
            file_id = m.video.file_id
            media_type = "video"
        elif m.content_type == "document":
            file_id = m.document.file_id
            media_type = "document"
        elif m.content_type == "photo":
            file_id = m.photo[-1].file_id
            media_type = "photo"
        else:
            bot.send_message(m.chat.id, "❌ Media bai dace ba.")
            return

        cur.execute("SELECT MAX(version) FROM how_to_buy")
        last_version = cur.fetchone()[0] or 0

        cur.execute(
            """
            INSERT INTO how_to_buy
            (hausa_text, english_text, media_file_id, media_type, version)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                state["hausa_text"],
                state["english_text"],
                file_id,
                media_type,
                last_version + 1
            )
        )

        HOWTO_STATE.pop(m.from_user.id, None)

        bot.send_message(
            m.chat.id,
            "✅ <b>HOW TO BUY an sabunta successfully</b>",
            parse_mode="HTML"
        )


# ======================================================
# /post  (ADMIN ONLY)
# ======================================================
@bot.message_handler(commands=["post"])
def post_to_channel(m):
    if m.from_user.id != ADMIN_ID:
        return

    cur.execute(
        """
        SELECT version
        FROM how_to_buy
        ORDER BY version DESC
        LIMIT 1
        """
    )
    row = cur.fetchone()

    if not row:
        bot.send_message(m.chat.id, "❌ Babu HOW TO BUY da aka saita tukuna.")
        return

    version = row[0]
    deeplink = f"https://t.me/{BOT_USERNAME}?start=howto_{version}"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "👉 Click here",
            url=deeplink
        )
    )

    bot.send_message(
        CHANNEL,
        " <b>👀🤝\n\n 🤩Kada ka bari a baka labari! Koyi yadda zaka siya 🎬 fim a  cikin sauri, sauƙi kuma babu wahala\n\n Cikin aminci 100% ba tare da jira ko damuwa ba 🥰\n\n\n 🤖@Algaitabot\n\nDANNA (Click here) 🔥\n\n🔰🔰🔰🔰🔰</b>",
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.send_message(m.chat.id, "✅ An tura post zuwa channel.")




# ======================================================
# DEEPLINK HANDLER

# ======================================================
# HOW TO START (HOWTO ONLY)
# ======================================================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start howto_"))
def howto_start_handler(m):

    args = m.text.split()

    # kariya
    if len(args) < 2 or not args[1].startswith("howto_"):
        return

    try:
        version = int(args[1].split("_")[1])
    except Exception:
        return

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT hausa_text, english_text, media_file_id, media_type
            FROM how_to_buy
            WHERE version=%s
            """,
            (version,)
        )
        row = cur.fetchone()
        cur.close()
    except Exception:
        return

    if not row:
        bot.send_message(m.chat.id, "❌ Wannan version bai wanzu ba.")
        return

    hausa_text, english_text, file_id, media_type = row

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🇬🇧 English", callback_data=f"howto_en:{version}"),
        types.InlineKeyboardButton("🇳🇬 Hausa", callback_data=f"howto_ha:{version}")
    )

    caption = hausa_text

    try:
        if media_type == "video":
            bot.send_video(m.chat.id, file_id, caption=caption, reply_markup=kb)
        elif media_type == "document":
            bot.send_document(m.chat.id, file_id, caption=caption, reply_markup=kb)
        else:
            bot.send_photo(m.chat.id, file_id, caption=caption, reply_markup=kb)
    except Exception:
        return


# ======================================================
# LANGUAGE SWITCH (EDIT ONLY)
# ======================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("howto_"))
def howto_language_switch(c):

    try:
        lang, version = c.data.split(":")
        version = int(version)
    except Exception:
        return

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT hausa_text, english_text
            FROM how_to_buy
            WHERE version=%s
            """,
            (version,)
        )
        row = cur.fetchone()
        cur.close()
    except Exception:
        return

    if not row:
        bot.answer_callback_query(c.id, "❌ Version bai wanzu ba.")
        return

    hausa_text, english_text = row
    text = english_text if lang == "howto_en" else hausa_text

    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🇬🇧 English", callback_data=f"howto_en:{version}"),
        types.InlineKeyboardButton("🇳🇬 Hausa", callback_data=f"howto_ha:{version}")
    )

    try:
        bot.edit_message_caption(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            caption=text,
            reply_markup=kb
        )
    except Exception:
        pass

    bot.answer_callback_query(c.id)



 #======================================================

# ========= HARD START BUYD =========
@bot.message_handler(
    func=lambda m: m.text
    and m.text.startswith("/start ")
    and m.text.split(" ", 1)[1].startswith("buyd_")
)
def __hard_start_buyd(msg):
    return buyd_deeplink_handler(msg)


# ========= HARD START GROUPITEM =========
@bot.message_handler(
    func=lambda m: m.text
    and m.text.startswith("/start ")
    and m.text.split(" ", 1)[1].startswith("groupitem_")
)
def __hard_start_groupitem(msg):
    return groupitem_deeplink_handler(msg)

# --- Added deep-link start handler for viewall/weakupdate (runs before other start handlers) ---  
@bot.message_handler(func=lambda m: (m.text or "").strip().split(" ")[0]=="/start" and len((m.text or "").strip().split(" "))>1 and (m.text or "").strip().split(" ")[1] in ("viewall","weakupdate"))  
def _start_deeplink_handler(msg):  
    """  
    Catch /start viewall or /start weakupdate deep-links from channel posts.  
    This handler tries to send the weekly list directly and then returns without invoking the normal start flow.  
    Placed early to take precedence over other start handlers.  
    """  
    try:  
        send_weekly_list(msg)  
    except Exception as e:  
        try:  
            bot.send_message(msg.chat.id, "An samu matsala wajen nuna weekly list.")  
        except:  
            pass  
    return




# ================== END RUKUNI B ==================



# --- Added callback handler for in-bot "View All Movies" buttons ---
@bot.callback_query_handler(func=lambda c: c.data in ("view_all_movies","viewall"))
def _callback_view_all(call):
    uid = call.from_user.id
    # Build a small message-like object expected by send_weekly_list
    class _Msg:
        def __init__(self, uid):
            self.chat = type('X', (), {'id': uid})
            self.text = ""
    try:
        send_weekly_list(_Msg(uid))
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "An samu matsala wajen nuna jerin.")





# ========== HELPERS ==========
def check_join(uid):
    try:
        member = bot.get_chat_member(CHANNEL, uid)
        return member.status in ("member", "administrator", "creator", "restricted")
    except Exception:
        return False

# name anonymization
def mask_name(fullname):
    """Mask parts of the name as requested: Muhmad, Khid, Sa*i style."""
    if not fullname:
        return "User"
    s = re.sub(r"\s+", " ", fullname.strip())
    # split on non-alphanumeric to preserve parts
    parts = re.split(r'(\W+)', s)
    out = []
    for p in parts:
        if not p or re.match(r'\W+', p):
            out.append(p)
            continue
        # p is a word
        n = len(p)
        if n <= 2:
            out.append(p[0] + "*"*(n-1))
            continue
        # keep first 2 and last 1, hide middle with **
        if n <= 4:
            keep = p[0] + "*"*(n-2) + p[-1]
            out.append(keep)
        else:
            # first two, two stars, last one
            out.append(p[:2] + "**" + p[-1])
    return "".join(out)

def tr_user(uid, key, default=""):
    return default

#farko
def reply_menu(uid=None):
    kb = InlineKeyboardMarkup()

    # ===== Labels =====
    paid_orders_label = "🗂Paid Orders"
    my_orders_label   = "Pending order"

    cart_label    = tr_user(uid, "btn_cart", default="Check cart")
    films_label   = "🎬Check Films"
    support_label = tr_user(uid, "btn_support", default="📞Help Center")
    channel_label = tr_user(uid, "btn_channel", default="🏘Our Channel")

    # ===== ROW 1 (PAID + MY ORDERS) =====
    kb.row(
        InlineKeyboardButton(paid_orders_label, callback_data="paid_orders"),
        InlineKeyboardButton(my_orders_label, callback_data="myorders_new")
    )

    # ===== ROW 2 (CHECK FILMS + SUPPORT) =====
    kb.row(
        InlineKeyboardButton(
            films_label,
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        ),
        InlineKeyboardButton(
            support_label,
            url=f"https://t.me/{ADMIN_USERNAME}"
        )
    )

    # ===== ROW 3 (OUR CHANNEL + CHECK CART) =====
    kb.row(
        InlineKeyboardButton(
            channel_label,
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        ),
        InlineKeyboardButton(
            cart_label,
            callback_data="viewcart"
        )
    )

    # ===== ADMIN ONLY BUTTONS =====
    if uid in ADMINS:
        kb.add(
            InlineKeyboardButton("🏛SERIES&MOV🌐", callback_data="groupitems")
        )

    return kb
# end






def user_main_menu(uid=None):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cart_label = tr_user(uid, "btn_cart", default="Check cart")
    help_label = tr_user(uid, "btn_help", default="HELP")

    # An cire "Films din wannan satin"
    # Buttons 1   2 a layi daya
    kb.add(
        KeyboardButton(help_label),
        KeyboardButton(cart_label)
    )

    return kb

#Start
def movie_buttons_inline(mid, user_id=None):
    kb = InlineKeyboardMarkup()

    add_cart = tr_user(user_id, "btn_add_cart", default="➕ Add to Cart")
    buy_now  = tr_user(user_id, "btn_buy_now", default="💳 Buy Now")
    channel  = tr_user(user_id, "btn_channel", default="🏘Our Channel")

    kb.add(
        InlineKeyboardButton(add_cart, callback_data=f"addcartdm:{mid}"),
        InlineKeyboardButton(
            buy_now,
            url=f"https://t.me/{BOT_USERNAME}?start=buyd_{mid}"
        )
    )
#end
    # 🛑 Idan user_id == None → channel ne → kada a ƙara sauran buttons
    if user_id is None:
        return kb

    # 🔰 Idan private chat ne → saka sauran buttons
    kb.row(
        
        InlineKeyboardButton(channel, url=f"https://t.me/{CHANNEL.lstrip('@')}")
    )

  

    return kb
#END

# ========== START ==========
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    fname = message.from_user.first_name or ""
    uname = f"@{message.from_user.username}" if message.from_user.username else "Babu username"
    text = (message.text or "").strip()

    # ========= REF =========
    param = None
    if text.startswith("/start "):
        param = text.split(" ", 1)[1].strip()
    elif text.startswith("/start"):
        parts = text.split(" ", 1)
        if len(parts) > 1:
            param = parts[1].strip()

    if param and param.startswith("ref"):
        try:
            ref_id = int(param[3:])
            add_referral(ref_id, uid)
            try:
                bot.send_message(
                    ref_id,
                    f"Someone used your invite link! ID: <code>{uid}</code>",
                    parse_mode="HTML"
                )
            except:
                pass
        except:
            pass

    # ========= ADMIN NOTIFY =========
    try:
        bot.send_message(
            ADMIN_ID,
            f"🟢 SABON VISITOR!\n\n"
            f"👤 Sunan: <b>{fname}</b>\n"
            f"🔗 Username: {uname}\n"
            f"🆔 ID: <code>{uid}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        print("Failed to notify admin about visitor:", e)

    # ========= JOIN CHECK =========
    joined = check_join(uid)



    # ❌ IDAN BAI SHIGA BA
    if not joined:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "Join Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        kb.add(
            InlineKeyboardButton(
                "I've Joined✅",
                callback_data="checkjoin"
            )
        )
        bot.send_message(
            uid,
            "⚠️ Kafin ka ci gaba, dole ne ka shiga channel ɗinmu.",
            reply_markup=kb
        )
        return

    # ========= MENUS =========
    bot.send_message(
        uid,
        "Abokin hulɗa, muna farin cikin maraba da kai na zuwa shagon fina-finanmu.",
        reply_markup=user_main_menu(uid)
    )
    bot.send_message(
        uid,
        "Shagon Algaita Movie Store na kawo maka zaɓaɓɓun fina-finai masu inganci. Mun tace su tsaf daga ɗanyen kaya, mun ware mafi kyau kawai. Duk fim ɗin da ka siya a nan, tabbas ba za mu ba ka kunya ba.\n\n Muna kawo fina-finan kowanne kamfanin fassara anan.",
        reply_markup=reply_menu(uid)
    )


# ======================================
# TEXT BUTTON HANDLER (GLOBAL SAFE)
# ======================================
@bot.message_handler(
    func=lambda msg: (
        isinstance(getattr(msg, "text", None), str)
        and msg.text.strip() in ["HELP", "Check cart"]
    )
)
def user_buttons(message):
    txt = message.text.strip()
    uid = str(message.from_user.id)   # 🔐 STRING FOR POSTGRES

    # ======= TAIMAKO =======
    if txt == "HELP":
        kb = InlineKeyboardMarkup()

        if ADMIN_USERNAME:
            kb.add(
                InlineKeyboardButton(
                    "Contact Admin",
                    url=f"https://t.me/{ADMIN_USERNAME}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Need help? Contact the admin.",
            reply_markup=kb
        )
        return

    # ======= CART =======
    if txt == "Check cart":
        try:
            show_cart(message.chat.id, uid)
        except Exception as e:
            print("CHECK CART ERROR:", e)
            bot.send_message(
                message.chat.id,
                "⚠️ An samu matsala wajen bude cart."
            )
        return


# ======================================
# CLEAR CART
# ======================================
def clear_cart(uid):
    uid = str(uid)
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM cart WHERE user_id = %s",
            (uid,)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        print("CLEAR CART ERROR:", e)


# ======================================
# GET CART (POSTGRES SAFE)
# ======================================
def get_cart(uid):
    uid = str(uid)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.item_id,
                i.title,
                i.price,
                i.file_id
            FROM cart c
            JOIN items i ON i.id = c.item_id
            WHERE c.user_id = %s
            ORDER BY c.id DESC
        """, (uid,))
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print("GET_CART ERROR:", e)
        return []


# ======================================
def get_credits_for_user(user_id):
    return 0, []


# ======================================
# PARSE CAPTION (TITLE + PRICE)
# ======================================
def parse_caption_for_title_price(text):
    if not text:
        return None, None

    text = text.replace("₦", "").strip()

    m = re.match(r"^(.*?)[\s\-]+(\d+)$", text)
    if m:
        return m.group(1).strip(), int(m.group(2))

    parts = text.splitlines()
    if len(parts) >= 2 and parts[1].strip().isdigit():
        return parts[0].strip(), int(parts[1].strip())

    return None, None

@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in admin_states
)
def admin_inputs(message):
    try:
        state_entry = admin_states.get(message.from_user.id)
        if not state_entry:
            return

        state = state_entry.get("state")

        # ⚠️ NOTE:
        # An cire ADD MOVIE logic, amma sauran admin states
        # (weak_update, update_week, da sauransu)
        # suna nan a sauran code ɗinka

        return

    except Exception as e:
        print("ADMIN INPUT ERROR:", e)
        return




    # ========== CANCEL ==========
@bot.message_handler(commands=["cancel"])
def cancel_cmd(message):
    if message.from_user.id == ADMIN_ID and admin_states.get(ADMIN_ID) and admin_states[ADMIN_ID].get("state") in ("weak_update", "update_week"):
        inst = admin_states[ADMIN_ID]
        inst_msg_id = inst.get("inst_msg_id")
        if inst_msg_id:
            try:
                bot.delete_message(chat_id=ADMIN_ID, message_id=inst_msg_id)
            except Exception as e:
                print("Failed to delete instruction message on cancel:", e)
        admin_states.pop(ADMIN_ID, None)
        bot.reply_to(message, "An soke Update/Weak update kuma an goge sakon instruction.")
        return

    if message.from_user.id == ADMIN_ID and admin_states.get(ADMIN_ID):
        admin_states.pop(ADMIN_ID, None)
        bot.reply_to(message, "An soke aikin admin na yanzu.")
        return

# ==================================================
# ==================================================
def get_cart(uid):
    uid = str(uid)  # 🔐 MUHIMMI

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                c.item_id,
                i.title,
                i.price,
                i.file_id,
                i.group_key
            FROM cart c
            JOIN items i ON i.id = c.item_id
            WHERE c.user_id = %s
            """,
            (uid,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    except Exception as e:
        # 🔥 DEBUG MAI KARFI
        print("GET_CART ERROR:", e)
        return []
# End

#End

# ========== BUILD CART VIEW (GROUP-AWARE - FIXED) ==========
def build_cart_view(uid):
    uid = str(uid)  # 🔐 MUHIMMI
    rows = get_cart(uid)

    kb = InlineKeyboardMarkup()

    # ===== IDAN CART BABU KOMAI =====
    if not rows:
        text = (
            "<b>You haven’t added any items to your cart yet.\n\n"
            "Check our channel to buy movie.</b>"
        )

        kb.row(
            InlineKeyboardButton(
                "🏘 Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return text, kb

    total = 0
    lines = []

    # ===============================
    # GROUP ITEMS BY GROUP_KEY
    # ===============================
    grouped = {}

    for movie_id, title, price, file_id, group_key in rows:
        key = group_key or f"single_{movie_id}"

        if key not in grouped:
            grouped[key] = {
                "ids": [],
                "title": title or "🧺 Group / Series Item",
                "price": int(price or 0)
            }

        grouped[key]["ids"].append(movie_id)

    # ===============================
    # DISPLAY ITEMS
    # ===============================
    for g in grouped.values():
        ids = g["ids"]
        title = g["title"]
        price = g["price"]

        total += price
        lines.append(f"🎬 {title} — ₦{price}")

        ids_str = "_".join(str(i) for i in ids)

        kb.add(
            InlineKeyboardButton(
                f"❌ Remove: {title}",
                callback_data=f"removecart:{ids_str}"
            )
        )

    # ===== TOTAL =====
    lines.append("")
    lines.append(f"<b>Total:</b> ₦{total}")

    text = (
        "🛒 <b>Your cart list.</b>\n\n"
        + "\n".join(lines)
    )

    # ===== ACTION BUTTONS =====
    kb.row(
        InlineKeyboardButton("🧹 Clear Cart", callback_data="clearcart"),
        InlineKeyboardButton("💵 CHECKOUT", callback_data="checkout")
    )

    # ===== OUR CHANNEL BUTTON =====
    kb.row(
        InlineKeyboardButton(
            "🏘 Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    return text, kb
# ================= ADMIN ON / OFF =================
@bot.message_handler(commands=["on"])
def admin_on(m):
    if m.chat.type != "private" or m.from_user.id != ADMIN_ID:
        return

    conn.execute(
        """
        INSERT INTO admin_controls (admin_id, sendmovie_enabled)
        VALUES (%s, 1)
        ON CONFLICT (admin_id)
        DO UPDATE SET sendmovie_enabled = EXCLUDED.sendmovie_enabled
        """,
        (ADMIN_ID,)
    )
    conn.commit()
    bot.reply_to(m, "✅ An kunna SENDMOVIE / GETID")


@bot.message_handler(commands=["off"])
def admin_off(m):
    if m.chat.type != "private" or m.from_user.id != ADMIN_ID:
        return

    conn.execute(
        """
        INSERT INTO admin_controls (admin_id, sendmovie_enabled)
        VALUES (%s, 0)
        ON CONFLICT (admin_id)
        DO UPDATE SET sendmovie_enabled = EXCLUDED.sendmovie_enabled
        """,
        (ADMIN_ID,)
    )
    conn.commit()
    bot.reply_to(m, "⛔ An kashe SENDMOVIE / GETID")


def admin_feature_enabled():
    row = conn.execute(
        "SELECT sendmovie_enabled FROM admin_controls WHERE admin_id=%s",
        (ADMIN_ID,)
    ).fetchone()
    return row and row[0] == 1



# ================= GETID (FILE_NAME SEARCH) =================
@bot.message_handler(commands=["getid"])
def getid_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not admin_feature_enabled():
        return

    parts = (message.text or "").split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(
            message,
            "Amfani: /getid Sunan item\nMisali: /getid Wutar jeji"
        )
        return

    query = parts[1].strip()

    # ====== EXACT MATCH ======
    row = conn.execute(
        """
        SELECT id, title
        FROM items
        WHERE LOWER(title) = LOWER(%s)
        LIMIT 1
        """,
        (query,)
    ).fetchone()

    if row:
        bot.reply_to(
            message,
            f"Kamar yadda ka bukata ga ID ɗin fim din <b>{row[1]}</b>: <code>{row[0]}</code>",
            parse_mode="HTML"
        )
        return

    # ====== CONTAINS MATCH ======
    rows = conn.execute(
        """
        SELECT id, title
        FROM items
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY title ASC
        LIMIT 10
        """,
        (f"%{query}%",)
    ).fetchall()

    if not rows:
        bot.reply_to(message, "❌ Ban samu fim da kake nema ba.")
        return

    if len(rows) == 1:
        r = rows[0]
        bot.reply_to(
            message,
            f"Kamar yadda ka bukata ga ID ɗin fim din <b>{r[1]}</b>: <code>{r[0]}</code>",
            parse_mode="HTML"
        )
        return

    text_out = "An samu fina-finai masu kama:\n"
    for r in rows:
        text_out += f"• {r[1]} — ID: {r[0]}\n"

    bot.reply_to(message, text_out)


# ================= SENDMOVIE (ID / GROUP_KEY / NAME) =================
@bot.message_handler(commands=["sendmovie"])
def sendmovie_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not admin_feature_enabled():
        return

    parts = m.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(
            m,
            "Amfani:\n"
            "/sendmovie 20\n"
            "/sendmovie 1,2,3,7\n"
            "/sendmovie karn tsaye S1\n"
            "/sendmovie avatar"
        )
        return

    raw = parts[1].strip()
    rows = []
    not_found_ids = []

    # ================= ID MODE =================
    ids = [int(x) for x in raw.replace(" ", "").split(",") if x.isdigit()]

    if ids:
        placeholders = ",".join(["%s"] * len(ids))

        rows = conn.execute(
            f"""
            SELECT file_id, title
            FROM items
            WHERE id IN ({placeholders})
            """,
            ids
        ).fetchall()

        found_ids = {
            r[0] for r in conn.execute(
                f"SELECT id FROM items WHERE id IN ({placeholders})",
                ids
            ).fetchall()
        }

        not_found_ids = [str(i) for i in ids if i not in found_ids]

    else:
        q = raw.lower()

        rows = conn.execute(
            """
            SELECT file_id, title
            FROM items
            WHERE LOWER(group_key) = %s
            ORDER BY id ASC
            """,
            (q,)
        ).fetchall()

        if not rows:
            rows = conn.execute(
                """
                SELECT file_id, title
                FROM items
                WHERE LOWER(title) LIKE %s
                   OR LOWER(file_name) LIKE %s
                ORDER BY title ASC
                """,
                (f"%{q}%", f"%{q}%")
            ).fetchall()

    if not rows:
        bot.reply_to(m, "❌ Ban samu fim ko group ɗin da ka nema ba.")
        return

    sent = 0
    for file_id, title in rows:
        try:
            try:
                bot.send_video(m.chat.id, file_id, caption=f"🎬 {title}")
            except:
                bot.send_document(m.chat.id, file_id, caption=f"🎬 {title}")
            sent += 1
        except Exception as e:
            print("sendmovie error:", e)

    report = f"✅ An tura fina-finai: {sent}"
    if not_found_ids:
        report += "\n\n❌ Ba a samu waɗannan IDs ba:\n" + ", ".join(not_found_ids)

    bot.reply_to(m, report)
# End
    # ================= USER RESEND SEARCH (USING user_movies) =================

@bot.message_handler(
    func=lambda m: m.from_user.id in admin_states
    and admin_states.get(m.from_user.id, {}).get("state") in (
        "search_menu",
        "browse_menu",
        "series_menu",
        "search_trending",
    )
)
def ignore_unexpected_text(m):
    uid = m.from_user.id
    bot.send_message(
        uid,
        "ℹ️ Don Allah ka yi amfani da *buttons* da ke ƙasa.",
        parse_mode="Markdown"
    )
# ======================================================
# ACTIVE BUYERS (ADMIN ONLY | PAGINATION | EDIT MODE)
# ======================================================

from psycopg2.extras import RealDictCursor

# ================== CANCEL ORDER (POSTGRES | SAFE | CLEAN) ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("cancel:"))
def cancel_order_handler(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)

    try:
        order_id = c.data.split("cancel:", 1)[1]
    except Exception:
        return

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 🔎 Tabbatar order na wannan user ne kuma unpaid
    try:
        cur.execute(
            """
            SELECT id
            FROM orders
            WHERE id=%s
              AND user_id=%s
              AND paid=0
            """,
            (order_id, uid)
        )
        order = cur.fetchone()
    except Exception:
        cur.close()
        return

    if not order:
        bot.send_message(
            uid,
            "❌ <b>Ba a sami order ba ko kuma an riga an biya shi.</b>",
            parse_mode="HTML"
        )
        cur.close()
        return

    # 🧹 Goge order_items gaba ɗaya
    try:
        cur.execute(
            "DELETE FROM order_items WHERE order_id=%s",
            (order_id,)
        )

        # 🧹 Goge order
        cur.execute(
            "DELETE FROM orders WHERE id=%s",
            (order_id,)
        )

        conn.commit()
    except Exception:
        conn.rollback()
        cur.close()
        return

    bot.send_message(
        uid,
        "❌ <b>An soke wannan order ɗin.</b>",
        parse_mode="HTML"
    )

    cur.close()


# ================== END RUKUNI B ==================
@bot.message_handler(commands=["sales"])
def admin_sales_command(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    now = _ng_now()
    since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    send_sales_report(
        since,
        f"📊 MONTHLY SALES REPORT ({now.strftime('%B %Y')})",
        ADMIN_ID,
        silent_if_empty=False
    )

# --- Added callback handler for in-bot "View All Movies" buttons ---
@bot.callback_query_handler(func=lambda c: c.data in ("view_all_movies","viewall"))
def _callback_view_all(call):
    uid = call.from_user.id
    # Build a small message-like object expected by send_weekly_list
    class _Msg:
        def __init__(self, uid):
            self.chat = type('X', (), {'id': uid})
            self.text = ""
    try:
        send_weekly_list(_Msg(uid))
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "An samu matsala wajen nuna jerin.")





# ========== HELPERS =======
# ========== detect forwarded channel post ==========
@bot.message_handler(
    func=lambda m: getattr(m, "forward_from_chat", None) is not None
    or getattr(m, "forward_from_message_id", None) is not None
)
def handle_forwarded_post(m):
    fc = getattr(m, "forward_from_chat", None)
    fid = getattr(m, "forward_from_message_id", None)

    if not fc and not fid:
        return

    try:
        chat_info = ""

        if fc:
            if getattr(fc, "username", None):
                chat_info = f"@{fc.username}"
            else:
                chat_info = f"chat_id:{fc.id}"
        else:
            chat_info = "Unknown channel"

        if fid:
            bot.reply_to(
                m,
                f"Original channel: {chat_info}\nOriginal message id: {fid}"
            )
        else:
            bot.reply_to(
                m,
                f"Original channel: {chat_info}\nMessage id not found."
            )

    except Exception as e:
        print("forward handler error:", e)


# ========== show_cart ==========
def show_cart(chat_id, user_id):
    rows = get_cart(user_id)

    kb = InlineKeyboardMarkup()

    # ===== IDAN CART EMPTY =====
    if not rows:
        kb.row(
            InlineKeyboardButton(
                "🏘Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )

        s = tr_user(
            user_id,
            "cart_empty",
            default="You haven’t added any items to your cart yet,\n\nCheck our channel to buy movie."
        )

        msg = bot.send_message(chat_id, s, reply_markup=kb)

        # 🔑 MUHIMMI: adana message_id
        cart_sessions[str(user_id)] = msg.message_id
        return

    text_lines = ["🛒 <b>Your cart list.</b>"]
    total = 0

    # ===============================
    # GROUP ITEMS BY group_key
    # ===============================
    grouped = {}

    for movie_id, title, price, file_id, group_key in rows:
        key = group_key or f"single_{movie_id}"

        if key not in grouped:
            grouped[key] = {
                "ids": [],
                "title": title or "📦 Group / Series Item",
                "price": int(price or 0)
            }

        grouped[key]["ids"].append(movie_id)

    # ===============================
    # DISPLAY ITEMS
    # ===============================
    for g in grouped.values():
        ids = g["ids"]
        title = g["title"]
        price = g["price"]

        total += price

        if price > 0:
            text_lines.append(f"• {title} — ₦{price}")
        else:
            text_lines.append(f"• {title} — 📦 Series")

        ids_str = "_".join(str(i) for i in ids)

        kb.add(
            InlineKeyboardButton(
                f"❌ Remove: {title[:18]}",
                callback_data=f"removecart:{ids_str}"
            )
        )

    text_lines.append(f"\n<b>Total:</b> ₦{total}")

    # ===============================
    # ACTION BUTTONS
    # ===============================
    kb.row(
        InlineKeyboardButton("🧹 Clear Cart", callback_data="clearcart"),
        InlineKeyboardButton("💵 CHECKOUT", callback_data="checkout")
    )

    kb.row(
        InlineKeyboardButton(
            "🏘Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    msg = bot.send_message(
        chat_id,
        "\n".join(text_lines),
        reply_markup=kb,
        parse_mode="HTML"
    )

    # 🔑 MUHIMMI: adana message_id
    cart_sessions[str(user_id)] = msg.message_id




# ---------- weekly button ----------
@bot.callback_query_handler(func=lambda c: c.data == "weekly_films")
def send_weekly_films(call):
    return send_weekly_list(call.message)

# ---------- My Orders (UNPAID with per-item REMOVE | FIXED COUNT ONLY) ----------
ORDERS_PER_PAGE = 5

def build_unpaid_orders_view(uid, page):
    offset = page * ORDERS_PER_PAGE

    # ===== COUNT ORDERS (FIXED: IGNORE EMPTY / DELETED ORDERS) =====
    cur.execute(
        """
        SELECT COUNT(DISTINCT o.id)
        FROM orders o
        WHERE o.user_id=%s
          AND o.paid=0
          AND EXISTS (
              SELECT 1
              FROM order_items oi
              WHERE oi.order_id = o.id
          )
        """,
        (uid,)
    )
    total = cur.fetchone()[0]

    if total == 0:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "🏘 Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return (
            "📩<b>There are no unpaid orders.\n\nGo to our channel to buy Films</b>",
            kb
        )

    # ===== TOTAL BALANCE (SOURCE OF TRUTH) =====
    cur.execute(
        """
        SELECT COALESCE(SUM(o.amount), 0)
        FROM orders o
        WHERE o.user_id=%s
          AND o.paid=0
          AND EXISTS (
              SELECT 1
              FROM order_items oi
              WHERE oi.order_id = o.id
          )
        """,
        (uid,)
    )
    total_amount = cur.fetchone()[0]

    # ===== FETCH ORDERS (UNCHANGED) =====
    cur.execute(
        """
        SELECT
            o.id,
            COUNT(oi.item_id) AS items_count,
            o.amount AS amount,
            MAX(i.title) AS title,
            COUNT(DISTINCT i.group_key) AS gk_count,
            MIN(oi.price) AS base_price,
            MIN(i.group_key) AS group_key
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE o.user_id=%s AND o.paid=0
        GROUP BY o.id
        ORDER BY o.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (uid, ORDERS_PER_PAGE, offset)
    )
    rows = cur.fetchall()

    text = f"📩<b>Your unpaid orders ({total})</b>\n\n"
    kb = InlineKeyboardMarkup()

    for oid, count, amount, title, gk_count, base_price, group_key in rows:

        # ===== DISPLAY LOGIC (GROUP SAFE) =====
        if count > 1 and gk_count == 1:
            name = f"{title} (EP {count})"
            show_amount = base_price
        else:
            if count == 1:
                name = title or "Single item"
            else:
                name = f"Group order ({count} items)"
            show_amount = amount

        short = name[:27] + "…" if len(name) > 27 else name
        text += f"• {short} — ₦{int(show_amount)}\n"

        kb.row(
            InlineKeyboardButton(
                f"❌ Remove {short}",
                callback_data=f"remove_unpaid:{oid}"
            )
        )

    text += f"\n<b>Total balance:</b> ₦{int(total_amount)}"

    # ===== NAVIGATION =====
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "◀️ Back",
                callback_data=f"unpaid_prev:{page-1}"
            )
        )
    if offset + ORDERS_PER_PAGE < total:
        nav.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"unpaid_next:{page+1}"
            )
        )
    if nav:
        kb.row(*nav)

    # ===== ACTIONS =====
    kb.row(
        InlineKeyboardButton("💳 Pay all", callback_data="payall:"),
        InlineKeyboardButton("📩 Paid orders", callback_data="paid_orders")
    )

    kb.row(
        InlineKeyboardButton("🗑 Delete unpaid", callback_data="delete_unpaid")
    )

    kb.row(
        InlineKeyboardButton(
            "🏘 Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    return text, kb
def build_paid_orders_view(uid, page):
    offset = page * ORDERS_PER_PAGE

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id=%s AND paid=1",
        (uid,)
    )
    total = cur.fetchone()[0]

    if total == 0:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎥 PAID MOVIES", callback_data="my_movies"))
        kb.add(
            InlineKeyboardButton(
                "🏘 Our Channel",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )
        )
        return "📩 <b>There are no paid orders.\n\n Go to our Channel to buy films</b>", kb

    cur.execute(
        """
        SELECT
            o.id,
            COUNT(oi.item_id) AS items_count,
            MAX(i.title) AS title,
            COUNT(DISTINCT i.group_key) AS gk_count
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN items i ON i.id = oi.item_id
        WHERE o.user_id=%s AND o.paid=1
        GROUP BY o.id
        ORDER BY o.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (uid, ORDERS_PER_PAGE, offset)
    )
    rows = cur.fetchall()

    text = f"📩 <b>Your paid orders ({total})</b>\n\n"
    kb = InlineKeyboardMarkup()

    for oid, count, title, gk_count in rows:
        cur.execute(
            "SELECT COUNT(*) FROM user_movies WHERE order_id=%s AND user_id=%s",
            (oid, uid)
        )
        delivered = cur.fetchone()[0]

        remain = count - delivered

        if count > 1 and gk_count == 1:
            name = f"{title} (EP {count})"
        else:
            name = title or f"Group order ({count} items)"

        short = name[:27] + "…" if len(name) > 27 else name

        if remain > 0:
            text += f"• {short} — ✅ Paid (Remaining: {remain})\n"
        else:
            text += f"• {short} — ✅ Arrived\n"

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "◀️ Back",
                callback_data=f"paid_prev:{page-1}"
            )
        )
    if offset + ORDERS_PER_PAGE < total:
        nav.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"paid_next:{page+1}"
            )
        )
    if nav:
        kb.row(*nav)

    kb.add(InlineKeyboardButton("🎥PAID MOVIES", callback_data="my_movies"))
    kb.add(
        InlineKeyboardButton(
            "🏘Our Channel",
            url=f"https://t.me/{CHANNEL.lstrip('@')}"
        )
    )

    return text, kb


# ---------- START handler (VIEW) ----------
@bot.message_handler(commands=['start'])
def start_handler(msg):

    track_visited_user(msg)

    # 🛑 BAR BUYD DA GROUPITEM SU WUCE
    if msg.text.startswith("/start buyd_"):
        return
    if msg.text.startswith("/start groupitem_"):
        return
    # ===== ASALIN VIEW DINKA (BA A TABA SHI BA) =====
    args = msg.text.split()
    if len(args) > 1 and args[1] == "weakupdate":
        return send_weekly_list(msg)
    if len(args) > 1 and args[1] == "viewall":
        return send_weekly_list(msg)

    bot.send_message(msg.chat.id, "Welcome!")

# ========= BUYD (ITEM ONLY | DEEP LINK → DM) =========
from psycopg2.extras import RealDictCursor
import uuid
import time

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start groupitem_"))
def groupitem_deeplink_handler(msg):
    uid = msg.from_user.id
    user_name = msg.from_user.first_name or "Customer"

    # ========= PARSE ITEM IDS =========
    try:
        raw = msg.text.split("groupitem_", 1)[1]
        sep = "_" if "_" in raw else ","
        item_ids = [int(x) for x in raw.split(sep) if x.strip().isdigit()]
    except Exception:
        return

    if not item_ids:
        return

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ========= FETCH ITEMS =========
    try:
        placeholders = ",".join(["%s"] * len(item_ids))
        cur.execute(
            f"""
            SELECT id, title, price, file_id, group_key
            FROM items
            WHERE id IN ({placeholders})
            """,
            tuple(item_ids)
        )
        items = cur.fetchall()
    except Exception:
        cur.close()
        return

    if not items:
        cur.close()
        return

    # ========= FILE_ID REQUIRED =========
    items = [i for i in items if i.get("file_id")]
    if not items:
        cur.close()
        return

    item_ids_clean = [i["id"] for i in items]

    # ========= OWNERSHIP CHECK =========
    try:
        cur.execute(
            f"""
            SELECT 1 FROM user_movies
            WHERE user_id=%s
              AND item_id IN ({",".join(["%s"] * len(item_ids_clean))})
            LIMIT 1
            """,
            (uid, *item_ids_clean)
        )
        owned = cur.fetchone()
    except Exception:
        cur.close()
        return

    if owned:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📽 PAID MOVIES", callback_data="my_movies"))
        bot.send_message(
            uid,
            "✅ You have already purchased this movie.\n\n"
            "Please check your *Paid Movies* to download it again.",
            parse_mode="Markdown",
            reply_markup=kb
        )
        cur.close()
        return

    # ========= GROUP_KEY PRICING =========
    groups = {}
    for i in items:
        key = i["group_key"] or f"single_{i['id']}"
        if key not in groups:
            groups[key] = int(i["price"] or 0)

    total = sum(groups.values())
    item_count = len(items)

    if total <= 0:
        cur.close()
        return

    # ========= REUSE / CREATE ORDER =========
    try:
        cur.execute(
            f"""
            SELECT o.id
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id=%s
              AND o.paid=0
              AND oi.item_id IN ({",".join(["%s"] * len(item_ids_clean))})
            GROUP BY o.id
            HAVING COUNT(DISTINCT oi.item_id)=%s
            LIMIT 1
            """,
            (uid, *item_ids_clean, len(item_ids_clean))
        )
        row = cur.fetchone()
    except Exception:
        cur.close()
        return

    if row:
        order_id = row["id"]
    else:
        order_id = str(uuid.uuid4())
        try:
            cur.execute(
                "INSERT INTO orders (id, user_id, amount, paid) VALUES (%s,%s,%s,0)",
                (order_id, uid, total)
            )
            for i in items:
                cur.execute(
                    """
                    INSERT INTO order_items (order_id, item_id, file_id, price)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (order_id, i["id"], i["file_id"], int(i["price"] or 0))
                )
        except Exception:
            cur.close()
            return

    # ========= PAYSTACK =========
    display_title = f"{item_count} item(s)"
    pay_url = create_paystack_payment(uid, order_id, total, display_title)

    if not pay_url:
        cur.close()
        return

    # ========= FIXED TITLE DISPLAY (GROUP_KEY SAFE) =========
    unique_titles = [
        i["title"]
        for _, i in {
            (i["group_key"] or f"single_{i['id']}"): i
            for i in items
        }.items()
    ]

    # ========= FINAL =========
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        uid,
        f"""🧺 <b>Your order created 🎉</b>

🎬 <b>You will buy:</b>
{", ".join(unique_titles)}

📦 Films: {item_count}
💵 Total amount: ₦{total}

👤 <b>Your name is:</b> {user_name}
🆔 <b>Order ID:</b>
<code>{order_id}</code>
""",
        parse_mode="HTML",
        reply_markup=kb
    )

    cur.close()

# ================= ADMIN MANUAL SUPPORT SYSTEM ===========

ADMIN_SUPPORT = {}

# ---------- /problem ----------
@bot.message_handler(commands=["problem"])
def admin_problem_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[m.from_user.id] = {"stage": "menu"}

    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🔁 RESEND ORDER", callback_data="admin_resend"),
        InlineKeyboardButton("🎁 GIFT", callback_data="admin_gift")
    )

    bot.send_message(
        m.chat.id,
        "🧩 <b>ADMIN SUPPORT PANEL</b>\n\nZabi abin da kake so:",
        parse_mode="HTML",
        reply_markup=kb
    )


# ---------- RESEND ----------
@bot.callback_query_handler(func=lambda c: c.data == "admin_resend")
def admin_resend_start(c):
    if c.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[c.from_user.id] = {"stage": "wait_order_id"}
    bot.answer_callback_query(c.id)
    bot.send_message(
        c.from_user.id,
        "🧾 Turo <b>ORDER ID</b>:",
        parse_mode="HTML"
    )


# ---------- GIFT ----------
@bot.callback_query_handler(func=lambda c: c.data == "admin_gift")
def admin_gift_start(c):
    if c.from_user.id != ADMIN_ID:
        return

    ADMIN_SUPPORT[c.from_user.id] = {"stage": "gift_user"}
    bot.answer_callback_query(c.id)
    bot.send_message(
        c.from_user.id,
        "👤 Turo <b>USER ID</b> wanda za a bawa kyauta:",
        parse_mode="HTML"
    )


# ---------- ADMIN FLOW ----------
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in ADMIN_SUPPORT)
def admin_support_flow(m):
    data = ADMIN_SUPPORT.get(m.from_user.id)
    if not data:
        return

    stage = data.get("stage")
    text = (m.text or "").strip()

    # ===== RESEND ORDER =====
    if stage == "wait_order_id":

        cur.execute(
            "SELECT user_id, amount, paid FROM orders WHERE id=%s",
            (text,)
        )
        row = cur.fetchone()

        # ❌ ORDER ID BAYA WUJUWA
        if not row:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "❌ <b>Order ID bai dace ba.</b>\nBabu wannan order a system.",
                parse_mode="HTML"
            )
            return

        user_id, amount, paid = row

        # ⚠️ ORDER BAI BIYA BA
        if paid != 1:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "⚠️ <b>ORDER BAI BIYA BA</b>\nFaɗa wa user ya kammala biya.",
                parse_mode="HTML"
            )
            return

        cur.execute(
            """
            SELECT item_id
            FROM order_items
            WHERE order_id=%s
            """,
            (text,)
        )
        items = cur.fetchall()

        # ❌ BA ITEMS
        if not items:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "⚠️ Wannan order ɗin babu items a cikinsa.\nDuba order_items table."
            )
            return

        item_ids = [i[0] for i in items]

        ADMIN_SUPPORT[m.from_user.id] = {
            "stage": "resend_confirm",
            "user_id": user_id,
            "items": item_ids
        }

        bot.send_message(
            m.chat.id,
            f"""✅ <b>ORDER VERIFIED</b>

🆔 Order ID: <code>{text}</code>
👤 User ID: <code>{user_id}</code>
💰 Amount: ₦{amount}
🎬 Items: {len(item_ids)}

Tura <b>/sendall</b> domin a sake tura items.""",
            parse_mode="HTML"
        )
        return

    # ===== GIFT FLOW =====
    if stage == "gift_user":
        if not text.isdigit():
            bot.send_message(m.chat.id, "❌ Rubuta USER ID mai inganci.")
            return

        data["gift_user"] = int(text)
        data["stage"] = "gift_message"

        bot.send_message(
            m.chat.id,
            "✍️ Rubuta <b>MESSAGE</b> da user zai gani:",
            parse_mode="HTML"
        )
        return

    if stage == "gift_message":
        data["gift_message"] = text
        data["stage"] = "gift_item"

        bot.send_message(
            m.chat.id,
            "🎬 Rubuta <b>SUNAN ITEM</b> (title ko file name):",
            parse_mode="HTML"
        )
        return

    if stage == "gift_item":
        q = text.lower()

        cur.execute(
            """
            SELECT file_id, title
            FROM items
            WHERE LOWER(title) LIKE %s
               OR LOWER(file_name) LIKE %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (f"%{q}%", f"%{q}%")
        )
        row = cur.fetchone()

        if not row:
            ADMIN_SUPPORT.pop(m.from_user.id, None)
            bot.send_message(
                m.chat.id,
                "❌ Ba a samu item a ITEMS table ba.",
                parse_mode="HTML"
            )
            return

        file_id, title = row

        try:
            bot.send_video(
                data["gift_user"],
                file_id,
                caption=data["gift_message"]
            )
        except:
            bot.send_document(
                data["gift_user"],
                file_id,
                caption=data["gift_message"]
            )

        bot.send_message(
            m.chat.id,
            f"""🎁 <b>An kammala</b>

👤 User ID: <code>{data['gift_user']}</code>
🎬 Item: <b>{title}</b>""",
            parse_mode="HTML"
        )

        ADMIN_SUPPORT.pop(m.from_user.id, None)

import uuid
from psycopg2.extras import RealDictCursor

# ========= PAY ALL UNPAID (SAFE | GROUP-AWARE | CLEAN | FINAL FIX) =========
@bot.callback_query_handler(func=lambda c: c.data == "payall:")
def pay_all_unpaid(call):
    uid = call.from_user.id
    user_name = call.from_user.first_name or "Customer"
    bot.answer_callback_query(call.id)

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ==================================================
    # 1️⃣ FETCH ALL UNPAID ORDER ITEMS
    # ==================================================
    try:
        cur.execute(
            """
            SELECT
                o.id        AS old_order_id,
                i.id        AS item_id,
                i.title,
                i.price,
                i.file_id,
                i.group_key
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            JOIN items i ON i.id = oi.item_id
            WHERE o.user_id=%s
              AND o.paid=0
            """,
            (uid,)
        )
        rows = cur.fetchall()
    except Exception:
        cur.close()
        return

    if not rows:
        bot.send_message(uid, "❌ No unpaid orders found.")
        cur.close()
        return

    # ==================================================
    # 2️⃣ FILTER VALID ITEMS
    # ==================================================
    items = [
        r for r in rows
        if r["file_id"] and int(r["price"] or 0) > 0
    ]

    if not items:
        bot.send_message(uid, "❌ No payable items.")
        cur.close()
        return

    item_ids = list({i["item_id"] for i in items})
    old_order_ids = list({i["old_order_id"] for i in items})

    # ==================================================
    # 3️⃣ OWNERSHIP CHECK
    # ==================================================
    try:
        cur.execute(
            f"""
            SELECT 1
            FROM user_movies
            WHERE user_id=%s
              AND item_id IN ({",".join(["%s"] * len(item_ids))})
            LIMIT 1
            """,
            (uid, *item_ids)
        )
        owned = cur.fetchone()
    except Exception:
        cur.close()
        return

    if owned:
        bot.send_message(uid, "✅ You already own some of these items.")
        cur.close()
        return

    # ==================================================
    # 4️⃣ GROUP KEY LOGIC
    # ==================================================
    groups = {}
    for i in items:
        key = i["group_key"] or f"single_{i['item_id']}"
        if key not in groups:
            groups[key] = {
                "price": int(i["price"]),
                "items": []
            }
        groups[key]["items"].append(i)

    total_amount = sum(g["price"] for g in groups.values())
    if total_amount <= 0:
        bot.send_message(uid, "❌ Invalid total amount.")
        cur.close()
        return

    # ==================================================
    # 5️⃣ CREATE COLLECTOR ORDER
    # ==================================================
    order_id = str(uuid.uuid4())

    try:
        cur.execute(
            """
            INSERT INTO orders (id, user_id, amount, paid)
            VALUES (%s, %s, %s, 0)
            """,
            (order_id, uid, total_amount)
        )

        for g in groups.values():
            for i in g["items"]:
                cur.execute(
                    """
                    INSERT INTO order_items
                    (order_id, item_id, file_id, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, i["item_id"], i["file_id"], g["price"])
                )

        conn.commit()
    except Exception:
        conn.rollback()
        cur.close()
        return

    # ==================================================
    # 🔥 DELETE OLD ORDERS (EXCEPT NEW ONE)
    # ==================================================
    old_order_ids = [oid for oid in old_order_ids if oid != order_id]

    if old_order_ids:
        try:
            cur.execute(
                f"""
                DELETE FROM order_items
                WHERE order_id IN ({",".join(["%s"] * len(old_order_ids))})
                """,
                tuple(old_order_ids)
            )

            cur.execute(
                f"""
                DELETE FROM orders
                WHERE id IN ({",".join(["%s"] * len(old_order_ids))})
                """,
                tuple(old_order_ids)
            )

            conn.commit()
        except Exception:
            conn.rollback()
            cur.close()
            return

    # ==================================================
    # 6️⃣ PAYSTACK
    # ==================================================
    pay_url = create_paystack_payment(
        uid,
        order_id,
        total_amount,
        "Pay All Unpaid Orders"
    )

    if not pay_url:
        cur.close()
        return

    # ==================================================
    # 7️⃣ DISPLAY
    # ==================================================
    unique_titles = [
        i["title"]
        for _, i in {
            (i["group_key"] or f"single_{i['item_id']}"): i
            for i in items
        }.items()
    ]

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

    bot.send_message(
        uid,
        f"""🧺 <b>PAY ALL UNPAID ORDERS</b>

👤 <b>Your name is:</b> {user_name}

🎬 <b> Films:</b>
{", ".join(unique_titles)}

📦 <b>Films:</b> {len(item_ids)}
🗂 <b>G-orders:</b> {len(groups)}
💵 <b> Total amount:</b> ₦{total_amount}

🆔 <b>Order ID:</b>
<code>{order_id}</code>
""",
        parse_mode="HTML",
        reply_markup=kb
    )

    cur.close()

import uuid
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===============================
# SERIES UPLOAD – FULL FLOW
# ===============================

series_sessions = {}

# ===============================
# COLLECT SERIES FILES
# ===============================
@bot.message_handler(
    content_types=["video", "document"],
    func=lambda m: m.from_user.id in series_sessions
)
def series_collect_files(m):
    uid = m.from_user.id  # ✅ INT
    sess = series_sessions.get(uid)

    if not sess or sess.get("stage") != "collect":
        return

    if m.video:
        dm_file_id = m.video.file_id
        file_name = m.video.file_name or "video.mp4"
    else:
        dm_file_id = m.document.file_id
        file_name = m.document.file_name or "file"

    sess["files"].append({
        "dm_file_id": dm_file_id,
        "file_name": file_name
    })

    bot.send_message(
        uid,
        f"✅ An karɓi: <b>{file_name}</b>",
        parse_mode="HTML"
    )

# ===============================
# DONE
# ===============================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.text.lower().strip() == "done"
        and m.from_user.id in series_sessions
    )
)
def series_done(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    if not sess or sess.get("stage") != "collect":
        return

    if not sess.get("files"):
        bot.send_message(uid, "❌ Babu fim da aka turo.")
        return

    text = "✅ <b>An karɓi fina-finai:</b>\n\n"
    for f in sess["files"]:
        text += f"• {f['file_name']}\n"

    text += "\n❓ <b>Akwai Hausa series a ciki?</b>"
    sess["stage"] = "ask_hausa"

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ EH", callback_data="hausa_yes"),
        InlineKeyboardButton("❌ A'A", callback_data="hausa_no")
    )

    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

# ===============================
# HAUSA CHOICE
# ===============================
@bot.callback_query_handler(
    func=lambda c: c.data in ["hausa_yes", "hausa_no"] and c.from_user.id in series_sessions
)
def handle_hausa_choice(c):
    uid = c.from_user.id
    sess = series_sessions.get(uid)
    bot.answer_callback_query(c.id)

    if c.data == "hausa_no":
        sess["hausa_matches"] = []
        sess["stage"] = "meta"
        bot.send_message(uid, "📸 Turo poster + caption (suna da farashi)")
        return

    sess["stage"] = "hausa_names"
    bot.send_message(uid, "✍️ Rubuta sunayen Hausa series (layi-layi)")

# ===============================
# RECEIVE HAUSA TITLES
# ===============================
@bot.message_handler(
    func=lambda m: (
        m.text
        and m.from_user.id in series_sessions
        and series_sessions[m.from_user.id].get("stage") == "hausa_names"
    )
)
def receive_hausa_titles(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    titles = [t.strip().lower() for t in m.text.split("\n") if t.strip()]
    matches = []

    for f in sess["files"]:
        fname = f["file_name"].lower()
        for t in titles:
            if t in fname:
                matches.append(f["file_name"])
                break

    sess["hausa_matches"] = matches
    sess["stage"] = "meta"

    bot.send_message(uid, "📸 Yanzu turo poster + caption (suna da farashi)")

# ===============================
# FINALIZE (UPLOAD + DB)
# ===============================
@bot.message_handler(
    content_types=["photo"],
    func=lambda m: m.from_user.id in series_sessions
)
def series_finalize(m):
    uid = m.from_user.id
    sess = series_sessions.get(uid)

    if sess.get("stage") != "meta":
        return

    try:
        title, raw_price = m.caption.strip().rsplit("\n", 1)
        has_comma = "," in raw_price
        price = int(raw_price.replace(",", "").strip())
    except:
        bot.send_message(uid, "❌ Caption bai dace ba.")
        return

    poster_file_id = m.photo[-1].file_id
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO series (title, price, poster_file_id)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (title, price, poster_file_id)
    )
    series_id = cur.fetchone()[0]

    item_ids = []
    created_at = datetime.utcnow()
    group_key = str(uuid.uuid4())

    for f in sess["files"]:
        msg = bot.send_document(
            STORAGE_CHANNEL,
            f["dm_file_id"],
            caption=f["file_name"]
        )

        doc = msg.document or msg.video

        cur.execute(
            """
            INSERT INTO items
            (title, price, file_id, file_name, group_key, created_at, channel_msg_id, channel_username)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                title,
                price,
                doc.file_id if doc else None,
                f["file_name"],
                group_key,
                created_at,
                msg.message_id,
                str(STORAGE_CHANNEL)
            )
        )
        item_ids.append(cur.fetchone()[0])

    conn.commit()
    cur.close()

    display_price = f"{price:,}" if has_comma else str(price)
    ids_str = "_".join(str(i) for i in item_ids)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🗃 Add to cart", callback_data=f"addcartdm:{ids_str}"),
        InlineKeyboardButton(
            "💳 Buy now",
            url=f"https://t.me/{BOT_USERNAME}?start=groupitem_{ids_str}"
        )
    )

    bot.send_photo(
        CHANNEL,
        poster_file_id,
        caption=f"🎬 <b>{title}</b>\n💵Price: ₦{display_price}",
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.send_message(uid, "🎉 Series an adana dukka series lafiya.")
    del series_sessions[uid]
@bot.callback_query_handler(func=lambda c: True)
def all_callbacks(c):
    uid = c.from_user.id
    data = c.data


    # ================= FEEDBACK =================
    if data.startswith("feedback:"):

        bot.answer_callback_query(c.id)

        parts = data.split(":", 2)
        if len(parts) != 3:
            bot.answer_callback_query(
                c.id,
                "⚠️ Invalid feedback data",
                show_alert=True
            )
            return

        mood, order_id = parts[1], parts[2]

        cur = conn.cursor()

        # ================= CHECK ORDER =================
        try:
            cur.execute(
                """
                SELECT paid
                FROM orders
                WHERE id=%s AND user_id=%s
                """,
                (order_id, uid)
            )
            row = cur.fetchone()
        except Exception:
            cur.close()
            bot.answer_callback_query(
                c.id,
                "⚠️ Database error",
                show_alert=True
            )
            return

        if not row or row[0] != 1:
            cur.close()
            bot.answer_callback_query(
                c.id,
                "⚠️ Wannan order ba naka bane ko ba'a biya ba.",
                show_alert=True
            )
            return

        # ================= CHECK DUPLICATE =================
        cur.execute(
            "SELECT 1 FROM feedbacks WHERE order_id=%s",
            (order_id,)
        )
        exists = cur.fetchone()

        if exists:
            cur.close()
            bot.answer_callback_query(
                c.id,
                "Ka riga ka bada ra'ayi.",
                show_alert=True
            )
            return

        # ================= INSERT FEEDBACK =================
        try:
            cur.execute(
                """
                INSERT INTO feedbacks (order_id, user_id, mood)
                VALUES (%s, %s, %s)
                """,
                (order_id, uid, mood)
            )
            conn.commit()
        except Exception:
            cur.close()
            bot.answer_callback_query(
                c.id,
                "⚠️ Ba a iya adana ra'ayi ba",
                show_alert=True
            )
            return

        cur.close()

        # ================= USER INFO =================
        try:
            chat = bot.get_chat(uid)
            fname = chat.first_name or "User"
        except:
            fname = "User"

        admin_messages = {
            "very": "😘 Gaskiya na ji daɗin siyayya da bot ɗinku, yana da sauki kuma wannan babban cigabane",
            "good": "🙂 Na ji daɗin siyayya kuma gaskiya wannan bot ba karimin sauki yakawo manaba",
            "neutral": "😓 Ban gama fahimta sosai ba, ku karayin vidoe don wayar mana da kai",
            "angry": "🤬 Wannan bot naku bai kyauta min ba, yakamata ku gyara tsarin kasuwancinku domin akwai matsala"
        }

        admin_text = (
            "📣 FEEDBACK RECEIVED\n\n"
            f"👤 User: {fname}\n"
            f"🆔 ID: {uid}\n"
            f"📦 Order: {order_id}\n"
            f"💬 Mood: {mood}\n\n"
            f"{admin_messages.get(mood, mood)}"
        )

        # ================= SEND TO ADMIN =================
        try:
            bot.send_message(ADMIN_ID, admin_text)
        except:
            pass

        # ================= REMOVE BUTTONS =================
        try:
            bot.edit_message_reply_markup(
                chat_id=c.message.chat.id,
                message_id=c.message.message_id,
                reply_markup=None
            )
        except:
            pass

        # ================= USER CONFIRM =================
        bot.send_message(
            uid,
            "🙏 Mun gode da ra'ayinka! Za mu yi aiki da shi Insha Allah."
        )
        return

    # =====================
    # SAURAN CALLBACKS ZASU BI A NAN
    # (checkout, cart, resend, my_movies, da sauransu)
    # =====================
    
    

    if data == "groupitems":
        if uid != ADMIN_ID:
            bot.answer_callback_query(c.id, "Ba izini.")
            return

        series_sessions[uid] = {
            "files": [],
            "stage": "collect"
        }

        bot.send_message(
            uid,
            "📺 <b>Series Mode ya fara</b>\n\n"
            "Ka fara turo videos/documents.\n"
            "Idan ka gama rubuta <b>Done</b>.",
            parse_mode="HTML"
        )
        return
    

    # =====================
    # CHECKOUT (GROUPITEM LOGIC)
    # =====================
    if data == "checkout":

        rows = get_cart(uid)
        if not rows:
            bot.answer_callback_query(c.id, "❌ Cart empty")
            return

        order_id = str(uuid.uuid4())
        user_name = c.from_user.full_name or "User"

        # =====================
        # GROUP BY GROUP_KEY
        # =====================
        groups = {}
        owned_count = 0

        for row in rows:
            try:
                item_id, title, price, file_id, group_key = row
            except ValueError:
                continue

            # 🔎 CHECK OWNERSHIP
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM user_movies WHERE user_id=%s AND item_id=%s LIMIT 1",
                (uid, item_id)
            )
            owned = cur.fetchone()
            cur.close()

            if owned:
                owned_count += 1
                continue

            if not file_id or not price:
                continue

            key = group_key or f"single_{item_id}"

            if key not in groups:
                groups[key] = {
                    "price": int(price or 0),   # ✅ group price once
                    "items": [],
                    "title": title
                }

            groups[key]["items"].append({
                "item_id": item_id,
                "file_id": file_id,
                "price": int(price or 0),
                "title": title
            })

        # =====================
        # ALL ITEMS ALREADY OWNED
        # =====================
        if owned_count > 0 and not groups:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📽PAID MOVIES", callback_data="my_movies"))

            bot.send_message(
                uid,
                "✅ <b>You've already bought these movies.</b>\n\n"
                "📽 Check Paid Movies\n"
                "You can download again anytime.",
                parse_mode="HTML",
                reply_markup=kb
            )
            bot.answer_callback_query(c.id)
            return

        # =====================
        # CALCULATE TOTAL (GROUP PRICE)
        # =====================
        total = sum(g["price"] for g in groups.values())
        if total <= 0:
            bot.answer_callback_query(c.id, "⚠️ Nothing payable")
            return

        # =====================
        # COUNT FILMS (GROUPITEM STYLE)
        # =====================
        film_count = sum(len(g["items"]) for g in groups.values())

        # =====================
        # CREATE ORDER
        # =====================
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (id, user_id, amount, paid) VALUES (%s,%s,%s,0)",
                (order_id, uid, total)
            )

            for g in groups.values():
                for i in g["items"]:
                    cur.execute(
                        """
                        INSERT INTO order_items (order_id, item_id, file_id, price)
                        VALUES (%s,%s,%s,%s)
                        """,
                        (order_id, i["item_id"], i["file_id"], i["price"])
                    )

            conn.commit()
            cur.close()
        except Exception as e:
            conn.rollback()
            print("❌ CHECKOUT DB ERROR:", e)
            bot.answer_callback_query(c.id, "❌ Checkout failed")
            return

        # =====================
        # 🧹 CLEAR CART
        # =====================
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM cart WHERE user_id=%s",
                (uid,)
            )
            conn.commit()
            cur.close()
        except Exception as e:
            conn.rollback()
            print("❌ CART CLEAR ERROR:", e)

        # =====================
        # PAYSTACK
        # =====================
        pay_url = create_paystack_payment(
            uid,
            order_id,
            total,
            f"{film_count} film(s)"
        )

        if not pay_url:
            bot.answer_callback_query(c.id, "❌ Payment error")
            return

        # =====================
        # FORMAT MESSAGE
        # =====================
        unique_titles = [
            g["title"]
            for g in groups.values()
        ]

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💳 PAY NOW", url=pay_url))
        kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}"))

        bot.send_message(
            uid,
            f"""🧺 <b>Your order created 🎉</b>

🎬 <b>You will buy:</b>
{", ".join(unique_titles)}

📦 Films: {film_count}
💵 Total amount: ₦{total}

👤 <b>Your name is:</b> {user_name}
🆔 <b>Order ID:</b>
<code>{order_id}</code>
""",
            parse_mode="HTML",
            reply_markup=kb
        )

        bot.answer_callback_query(c.id)
        return   
    
    # =====================
    # REMOVE FROM CART
    # =====================
    if data.startswith("removecart:"):
        raw = data.split(":", 1)[1]
        ids = [i for i in raw.split("_") if i.isdigit()]

        if not ids:
            bot.answer_callback_query(c.id, "❌ No item selected")
            return

        removed = 0

        try:
            cur = conn.cursor()
            for item_id in ids:
                cur.execute(
                    "DELETE FROM cart WHERE user_id=%s AND item_id=%s",
                    (uid, item_id)
                )
                removed += cur.rowcount
            conn.commit()
            cur.close()
        except Exception:
            conn.rollback()
            bot.answer_callback_query(c.id, "❌ Remove failed")
            return

        # 🚫 idan babu abin da aka goge
        if removed == 0:
            bot.answer_callback_query(
                c.id,
                "⚠️ Wannan item din baya cikin cart"
            )
            return

        # 🔁 EDIT CART MESSAGE
        msg_id = cart_sessions.get(uid)
        if msg_id:
            text, kb = build_cart_view(uid)
            try:
                bot.edit_message_text(
                    chat_id=c.message.chat.id,
                    message_id=msg_id,
                    text=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except:
                pass

        bot.answer_callback_query(c.id, "🗑 Item removed")
        return

    # =====================
    # CLEAR CART
    # =====================
    if data == "clearcart":
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM cart WHERE user_id=%s",
                (uid,)
            )
            removed = cur.rowcount
            conn.commit()
            cur.close()
        except Exception:
            conn.rollback()
            bot.answer_callback_query(c.id, "❌ Clear failed")
            return

        if removed == 0:
            bot.answer_callback_query(
                c.id,
                "⚠️ Cart dinka tuni babu komai"
            )
            return

        # 🔁 EDIT CART MESSAGE (zai nuna empty cart)
        msg_id = cart_sessions.get(uid)
        if msg_id:
            text, kb = build_cart_view(uid)
            try:
                bot.edit_message_text(
                    chat_id=c.message.chat.id,
                    message_id=msg_id,
                    text=text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            except:
                pass

        bot.answer_callback_query(c.id, "🧹 Cart cleared")
        return



    # =====================
    # ADD TO CART (SAFE)
    # =====================
    if data.startswith("addcartdm:"):
        try:
            raw = data.split(":", 1)[1]
            item_ids = [i for i in raw.split("_") if i.isdigit()]
        except:
            bot.answer_callback_query(c.id, "❌ Invalid item")
            return

        if not item_ids:
            bot.answer_callback_query(c.id, "❌ Invalid item")
            return

        added = 0
        skipped = 0

        try:
            cur = conn.cursor()

            for item_id in item_ids:
                # 🔎 check item exists
                cur.execute(
                    "SELECT id FROM items WHERE id=%s",
                    (item_id,)
                )
                if not cur.fetchone():
                    skipped += 1
                    continue

                # 🔐 already in cart?
                cur.execute(
                    "SELECT 1 FROM cart WHERE user_id=%s AND item_id=%s",
                    (uid, item_id)
                )
                if cur.fetchone():
                    skipped += 1
                    continue

                # ➕ insert
                cur.execute(
                    "INSERT INTO cart (user_id, item_id) VALUES (%s, %s)",
                    (uid, item_id)
                )
                added += 1

            conn.commit()

        except Exception:
            conn.rollback()
            bot.answer_callback_query(c.id, "❌ Add to cart failed")
            return

        # ===== USER FEEDBACK =====
        if added and skipped:
            bot.answer_callback_query(
                c.id,
                f"✅ Added {added} | ⚠️ Already added {skipped}"
            )
        elif added:
            bot.answer_callback_query(
                c.id,
                "✅ Item added to cart"
            )
        else:
            bot.answer_callback_query(
                c.id,
                "⚠️ You've already added this item"
            )

        return
  

    # =====================
    # VIEW CART
    # =====================
    if data == "viewcart":
        text, kb = build_cart_view(uid)
        msg = bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")
        cart_sessions[uid] = msg.message_id
        bot.answer_callback_query(c.id)
        return


    # =====================
    # PENDING / UNPAID ORDERS
    # =====================
    if data == "myorders_new":
        text, kb = build_unpaid_orders_view(uid, page=0)

        bot.send_message(
            chat_id=uid,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id)
        return


    # ================= MY MOVIES =================
    if data == "my_movies":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "🔍 Check movie",
                callback_data="_resend_search_"
            )
        )

        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text=(
                "🎥 <b>PAID MOVIES</b>\n"
                "Your previously purchased movies will be resent to you.\n\n"
                "🔍 Tap the button below to search your purchased movies."
            ),
            parse_mode="HTML",
            reply_markup=kb
        )

        bot.answer_callback_query(c.id)
        return


    # ================= 🔍 RESEND SEARCH (STATE SETTER) =================
    if data == "_resend_search_":
        user_states[uid] = {"action": "_resend_search_"}

        bot.send_message(
            uid,
            "🔍 <b>Checking Mode</b>\n"
            "Type the movie name or first letter(s).\n"
            "Example: <b>Dan</b> = Dan Tawaye",
            parse_mode="HTML"
        )

        bot.answer_callback_query(c.id)
        return


    # ================= RESEND BY DAYS =================
    if data.startswith("resend:"):
        try:
            days = int(data.split(":", 1)[1])
        except:
            bot.answer_callback_query(c.id, "❌ Invalid time.")
            return

        used = conn.execute(
            "SELECT COUNT(*) FROM resend_logs WHERE user_id=%s",
            (uid,)
        ).fetchone()[0]

        if used >= 10:
            bot.send_message(
                uid,
                "⚠️ You’ve reached the maximum resend limit (10 times).\n"
                "Please purchase the movie again."
            )
            bot.answer_callback_query(c.id)
            return

        rows = conn.execute(
            """
            SELECT DISTINCT ui.item_id, i.file_id, i.title
            FROM user_movies ui
            JOIN items i ON i.id = ui.item_id
            WHERE ui.user_id=%s
              AND ui.created_at >= NOW() - INTERVAL '%s days'
            ORDER BY ui.created_at ASC
            """,
            (uid, days)
        ).fetchall()

        if not rows:
            bot.send_message(uid, "❌ Babu fim a wannan lokacin.")
            bot.answer_callback_query(c.id)
            return

        for _, file_id, title in rows:
            try:
                bot.send_video(uid, file_id, caption=f"🎬 {title}")
            except:
                bot.send_document(uid, file_id, caption=f"🎬 {title}")

        conn.execute(
            "INSERT INTO resend_logs (user_id, used_at) VALUES (%s, NOW())",
            (uid,)
        )
        conn.commit()

        bot.send_message(
            uid,
            f"✅ Movies resent successfully ({len(rows)}).\n"
            "⚠️ Limit: 10 times only."
        )
        bot.answer_callback_query(c.id)
        return


    # ================= RESEND ONE ITEM =================
    if data.startswith("resend_one:"):
        try:
            item_id = int(data.split(":", 1)[1])
        except:
            bot.answer_callback_query(c.id, "❌ Invalid movie.")
            return

        used = conn.execute(
            "SELECT COUNT(*) FROM resend_logs WHERE user_id=%s",
            (uid,)
        ).fetchone()[0]

        if used >= 10:
            bot.send_message(
                uid,
                "⚠️ You’ve reached the maximum resend limit (10 times)."
            )
            bot.answer_callback_query(c.id)
            return

        row = conn.execute(
            """
            SELECT i.file_id, i.title
            FROM user_movies ui
            JOIN items i ON i.id = ui.item_id
            WHERE ui.user_id=%s AND ui.item_id=%s
            LIMIT 1
            """,
            (uid, item_id)
        ).fetchone()

        if not row:
            bot.answer_callback_query(c.id, "❌ Movie not found.")
            return

        file_id, title = row

        try:
            bot.send_video(uid, file_id, caption=f"🎬 {title}")
        except:
            bot.send_document(uid, file_id, caption=f"🎬 {title}")

        conn.execute(
            "INSERT INTO resend_logs (user_id, used_at) VALUES (%s, NOW())",
            (uid,)
        )
        conn.commit()

        bot.answer_callback_query(
            c.id,
            "✅ Movie resent successfully.\n⚠️ Limit: 10 times."
        )
        return

   

     # ================= START SERIES MODE =================
    if data == "start_series":
        series_sessions[uid] = {
            "stage": "collect",
            "files": [],
            "hausa_titles": [],
            "hausa_matches": []
        }

        bot.answer_callback_query(c.id)
        bot.send_message(
            uid,
            "📦 <b>Series mode ya fara</b>\n\n"
            "➡️ Turo dukkan fina-finai (video ko document)\n"
            "➡️ Idan ka gama, rubuta <b>done</b>",
            parse_mode="HTML"
        )
        return



   

    # =====================
    # UNPAID PAGINATION
    # =====================
    if data.startswith("unpaid_next:") or data.startswith("unpaid_prev:"):
        page = int(data.split(":")[1])
        text, kb = build_unpaid_orders_view(uid, page)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    # =====================
    # REMOVE SINGLE UNPAID
    # =====================
    if data.startswith("remove_unpaid:"):
        oid = data.split(":", 1)[1]

        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM orders
                WHERE id=%s AND user_id=%s AND paid=0
                """,
                (oid, uid)
            )
            if not cur.fetchone():
                bot.answer_callback_query(c.id, "❌ Order not found")
                cur.close()
                return

            cur.execute(
                "DELETE FROM order_items WHERE order_id=%s",
                (oid,)
            )

            cur.execute(
                "DELETE FROM orders WHERE id=%s",
                (oid,)
            )

            conn.commit()
            cur.close()

        except Exception:
            conn.rollback()
            bot.answer_callback_query(c.id, "❌ Failed to remove")
            return

        text, kb = build_unpaid_orders_view(uid, page=0)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id, "❌ Order removed")
        return

    # =====================
    # DELETE ALL UNPAID
    # =====================
    if data == "delete_unpaid":
        try:
            cur = conn.cursor()

            cur.execute(
                """
                DELETE FROM order_items
                WHERE order_id IN (
                    SELECT id FROM orders
                    WHERE user_id=%s AND paid=0
                )
                """,
                (uid,)
            )

            cur.execute(
                """
                DELETE FROM orders
                WHERE user_id=%s AND paid=0
                """,
                (uid,)
            )

            conn.commit()
            cur.close()

        except Exception:
            conn.rollback()
            bot.answer_callback_query(c.id, "❌ Failed to delete")
            return

        text, kb = build_unpaid_orders_view(uid, page=0)
        bot.edit_message_text(
            chat_id=uid,
            message_id=c.message.message_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(c.id, "🗑 All unpaid orders deleted")
        return

  
    # =====================
    # OPEN PAID ORDERS
    # =====================
    if data == "paid_orders":
        text, kb = build_paid_orders_view(uid, page=0)

        bot.send_message(
            chat_id=uid,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )

        bot.answer_callback_query(c.id)
        return




    # =====================
    # ALL FILMS PAGINATION
    # =====================
    if data == "allfilms_prev":
        sess = allfilms_sessions.get(uid)
        if not sess:
            return

        idx = sess["index"] - 1
        if idx >= 0:
            send_allfilms_page(uid, idx)
        return



    # ================= FEEDBACK =================
    if not data.startswith("feedback:"):
        return   # ❗️MUHIMMI: kada a answer a nan

    parts = data.split(":", 2)
    if len(parts) != 3:
        print("❌ INVALID CALLBACK FORMAT:", data)
        bot.answer_callback_query(
            c.id,
            "⚠️ Invalid feedback data",
            show_alert=True
        )
        return

    mood, order_id = parts[1], parts[2]

    print("🧠 FEEDBACK MOOD:", mood)
    print("📦 FEEDBACK ORDER_ID:", order_id)

    # ================= CHECK ORDER =================
    try:
        row = conn.execute(
            """
            SELECT id FROM orders
            WHERE id=%s AND user_id=%s AND paid=1
            """,
            (order_id, uid)
        ).fetchone()
    except Exception as e:
        print("❌ DB ERROR (ORDER CHECK):", e)
        bot.answer_callback_query(
            c.id,
            "⚠️ Database error",
            show_alert=True
        )
        return

    print("📄 ORDER ROW:", row)

    if not row:
        bot.answer_callback_query(
            c.id,
            "⚠️ Wannan order ba naka bane ko ba'a biya ba.",
            show_alert=True
        )
        return

    # ================= CHECK DUPLICATE =================
    exists = conn.execute(
        "SELECT 1 FROM feedbacks WHERE order_id=%s",
        (order_id,)
    ).fetchone()

    print("🧾 FEEDBACK EXISTS:", exists)

    if exists:
        bot.answer_callback_query(
            c.id,
            "Ka riga ka bada ra'ayi.",
            show_alert=True
        )
        return

    # ================= INSERT FEEDBACK =================
    try:
        conn.execute(
            """
            INSERT INTO feedbacks (order_id, user_id, mood)
            VALUES (%s, %s, %s)
            """,
            (order_id, uid, mood)
        )
        conn.commit()
    except Exception as e:
        print("❌ INSERT FEEDBACK ERROR:", e)
        bot.answer_callback_query(
            c.id,
            "⚠️ Ba a iya adana ra'ayi ba",
            show_alert=True
        )
        return

    print("✅ FEEDBACK SAVED SUCCESSFULLY")

    # ================= USER INFO =================
    try:
        chat = bot.get_chat(uid)
        fname = chat.first_name or "User"
    except Exception as e:
        print("⚠️ GET_CHAT ERROR:", e)
        fname = "User"

    admin_messages = {
        "very": "😘 Gaskiya na ji daɗin siyayya da bot ɗinku",
        "good": "🙂 Na ji daɗin siyayya",
        "neutral": "😓 Ban gama fahimta sosai ba",
        "angry": "🤬 Wannan bot yana bani ciwon kai"
    }

    admin_text = (
        "📣 FEEDBACK RECEIVED\n\n"
        f"👤 User: {fname}\n"
        f"🆔 ID: {uid}\n"
        f"📦 Order: {order_id}\n"
        f"💬 Mood: {mood}\n\n"
        f"{admin_messages.get(mood, mood)}"
    )

    # ================= SEND TO ADMIN =================
    try:
        bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print("⚠️ ADMIN SEND ERROR:", e)

    # ================= REMOVE BUTTONS =================
    try:
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=None
        )
    except Exception as e:
        print("⚠️ REMOVE BUTTON ERROR:", e)

    # ================= USER CONFIRM =================
    bot.answer_callback_query(c.id)
    bot.send_message(
        uid,
        "🙏 Mun gode da ra'ayinka! Za mu yi aiki da shi Insha Allah."
    )    
    # =====================
    # ADD MOVIE (ADMIN)
    # =====================
    if data == "addmovie":
        if uid != ADMIN_ID:
            bot.answer_callback_query(c.id, "Only admin.")
            return
        admin_states[uid] = {"state": "add_movie_wait_file"}
        bot.send_message(uid, "Turo film.")
        bot.answer_callback_query(c.id)
        return

    # =====================
    # WEEKLY BUY
    # =====================
    if data.startswith("weekly_buy:"):
        try:
            idx = int(data.split(":", 1)[1])
        except:
            bot.answer_callback_query(c.id, "Invalid.")
            return

        row = conn.execute(
            "SELECT items FROM weekly ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if not row:
            bot.answer_callback_query(c.id, "No weekly items.")
            return

        items = json.loads(row[0] or "[]")

        if idx < 0 or idx >= len(items):
            bot.answer_callback_query(c.id, "Invalid item.")
            return

        item = items[idx]

        title = item["title"]
        price = int(item["price"])

        remaining_price, applied_sum, applied_ids = apply_credits_to_amount(
            uid,
            price
        )

        order_id = create_single_order_for_weekly(
            uid,
            title,
            remaining_price
        )

        bot.send_message(
            uid,
            f"Oda {order_id} – ₦{remaining_price}"
        )
        bot.answer_callback_query(c.id)
        return    
    # ======================================================
    # ================= ALL FILMS OPEN =====================
    # ======================================================
    if data == "all_films":
        rows = build_allfilms_rows()
        if not rows:
            bot.answer_callback_query(c.id, "❌ Babu fim a DB")
            return

        pages = paginate(rows, PER_PAGE)

        allfilms_sessions[uid] = {
            "pages": pages,
            "index": 0,
            "last_msg": c.message.message_id
        }

        send_allfilms_page(uid, 0)
        bot.answer_callback_query(c.id)
        return

    # ======================================================
    # ================= ALL FILMS NEXT =====================
    # ======================================================
    if data == "allfilms_next":
        sess = allfilms_sessions.get(uid)
        if not sess:
            bot.answer_callback_query(c.id)
            return

        send_allfilms_page(uid, sess["index"] + 1)
        bot.answer_callback_query(c.id)
        return

    # ======================================================
    # ================= ALL FILMS PREV =====================
    # ======================================================
    if data == "allfilms_prev":
        sess = allfilms_sessions.get(uid)
        if not sess:
            bot.answer_callback_query(c.id)
            return

        send_allfilms_page(uid, sess["index"] - 1)
        bot.answer_callback_query(c.id)
        return


 # Map new erase_all_data callback to existing erase_data handler (compat shim)
    if data == "erase_all_data":
        data = "erase_data"



    # NEW WEAK UPDATE SYSTEM
    if data == "weak_update":
        start_weak_update(msg=c.message)
        return

    # checkjoin: after user clicks I've Joined
    if data == "checkjoin":
        try:
            if check_join(uid):
                bot.answer_callback_query(
                    callback_query_id=c.id,
                    text=tr_user(uid, "joined_ok", default="✔ Channel joined!")
                )

                bot.send_message(
                    uid,
                    "Shagon Algaita Movie Store na kawo maka zaɓaɓɓun fina-finai masu inganci. "
                    "Mun tace su tsaf daga ɗanyen kaya, mun ware mafi kyau kawai. "
                    "Duk fim ɗin da ka siya a nan, tabbas ba za mu ba ka kunya ba.",
                    reply_markup=user_main_menu(uid)
                )

                bot.send_message(
                    uid,
                    "Sannu da zuwa!\n Duk fim din da kakeso ka shiga channel dinmu ka duba shi?:",
                    reply_markup=reply_menu(uid)
                )

            else:
                bot.answer_callback_query(
                    callback_query_id=c.id,
                    text=tr_user(uid, "not_joined", default="❌ You are not logged in.")
                )

        except Exception as e:
            print("checkjoin callback error:", e)

        return

 
  

    

# go home
    if data == "go_home":
        try:
            bot.answer_callback_query(callback_query_id=c.id)
            bot.send_message(
                uid,
                "Sannu! Ga zabuka, domin fara wa:",
                reply_markup=reply_menu(uid)
            )
        except Exception as e:
            print("go_home error:", e)
        return
    



    # Support Help -> Open admin DM directly (NO messages to admin, NO notifications)
    if data == "support_help":
        try:
            bot.answer_callback_query(callback_query_id=c.id)
        except:
            pass

        if ADMIN_USERNAME:
            # Open admin DM directly
            bot.send_message(uid, f"👉 Tuntuɓi admin kai tsaye: https://t.me/{ADMIN_USERNAME}")
        else:
            bot.send_message(uid, "Admin username bai sa ba. Tuntubi support.")
        return


    # fallback
    try:
        bot.answer_callback_query(callback_query_id=c.id)
    except:
        pass


# ========== /myorders command (SAFE – ITEMS BASED) ==========
@bot.message_handler(commands=["myorders"])
def myorders(message):
    uid = message.from_user.id

    rows = conn.execute(
        """
        SELECT id, amount, paid
        FROM orders
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (uid,)
    ).fetchall()

    if not rows:
        bot.reply_to(
            message,
            "❌ You don’t have any orders yet.",
            reply_markup=reply_menu(uid)
        )
        return

    txt = "🛒 <b>Your Orders</b>\n\n"

    for row in rows:
        oid = row["id"]
        amount = int(row["amount"] or 0)
        paid = row["paid"]

        # 🔒 SAFE COUNT (order_items ONLY)
        info = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM order_items
            WHERE order_id=%s
            """,
            (oid,)
        ).fetchone()

        items_count = info["cnt"] if info else 0

        # 🛡 KARIYA: idan babu item kwata-kwata, tsallake
        if items_count <= 0:
            continue

        # 🏷 LABEL
        label = "1 item" if items_count == 1 else f"Group items ({items_count})"

        txt += (
            f"🆔 <code>{oid}</code>\n"
            f"📦 {label}\n"
            f"💰 Amount: ₦{amount}\n"
            f"💳 Status: {'✅ Paid' if paid else '❌ Unpaid'}\n\n"
        )

    bot.send_message(
        uid,
        txt,
        parse_mode="HTML",
        reply_markup=reply_menu(uid)
    )
#s ========== ADMIN FILE UPLOAD (ITEMS ONLY
# ================== SALES REPORT SYSTEM (ITEMS BASED – POSTGRES FIXED) ==================

import threading
import time
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor


# ================= TIME =================
def _ng_now():
    return datetime.utcnow() + timedelta(hours=1)

def _last_day_of_month(dt):
    nxt = dt.replace(day=28) + timedelta(days=4)
    return (nxt - timedelta(days=nxt.day)).day


# ================= ONE REPORT ENGINE =================
def send_sales_report(since_dt, title, target_chat_id, silent_if_empty=False):
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            COALESCE(i.group_key, 'single_' || i.id) AS grp,
            MIN(i.title) AS title,
            COUNT(DISTINCT o.id) AS orders,
            SUM(oi.price) AS total
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        JOIN items i ON i.id = oi.item_id
        WHERE o.paid = 1
          AND o.created_at >= %s
        GROUP BY grp
        ORDER BY total DESC
        """,
        (since_dt,)
    )

    rows = cur.fetchall()
    cur.close()

    # ===== NO SALES =====
    if not rows:
        if not silent_if_empty:
            bot.send_message(
                target_chat_id,
                f"{title}\n\n❌ No sales yet."
            )
        return

    msg = f"{title}\n\n"
    total_orders = 0
    grand_total = 0

    for r in rows:
        qty = r["orders"]
        amount = int(r["total"] or 0)

        total_orders += qty
        grand_total += amount

        msg += f"• {r['title']} ({qty} sales) — ₦{amount:,}\n"

    msg += (
        "\n──────────────────\n"
        f"🧾 Total Orders: {total_orders}\n"
        f"💰 Total Revenue: ₦{grand_total:,}\n"
        f"🕒 {_ng_now().strftime('%d %b %Y, %H:%M (NG)')}"
    )

    bot.send_message(target_chat_id, msg)


# ================= AUTOMATIC WEEKLY (GROUP) =================
def weekly_sales():
    since = _ng_now() - timedelta(days=7)
    send_sales_report(
        since,
        "📊 WEEKLY SALES REPORT",
        PAYMENT_NOTIFY_GROUP,
        silent_if_empty=True
    )


# ================= AUTOMATIC MONTHLY (GROUP) =================
def monthly_sales():
    now = _ng_now()
    since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    send_sales_report(
        since,
        f"📊 MONTHLY SALES REPORT ({now.strftime('%B %Y')})",
        PAYMENT_NOTIFY_GROUP,
        silent_if_empty=True
    )


# ================= SCHEDULER =================
def sales_report_scheduler():
    weekly_sent = False
    monthly_sent = False

    while True:
        now = _ng_now()

        # Friday 23:50
        if now.weekday() == 4 and now.hour == 23 and now.minute == 50:
            if not weekly_sent:
                weekly_sales()
                weekly_sent = True
        else:
            weekly_sent = False

        # Last day of month 23:50
        if now.day == _last_day_of_month(now) and now.hour == 23 and now.minute == 50:
            if not monthly_sent:
                monthly_sales()
                monthly_sent = True
        else:
            monthly_sent = False

        time.sleep(20)





# ▶️ START BACKGROUND REPORT THREAD
# ================== START SERVER ==================
if __name__ == "__main__":

    if BOT_MODE == "webhook":
        print("🌐 Running in WEBHOOK mode")

        try:
            bot.remove_webhook()
            bot.set_webhook(f"{WEBHOOK_URL}/telegram")
            print("✅ Telegram webhook set successfully")
        except Exception as e:
            print("❌ Failed to set webhook:", e)

        port = int(os.environ.get("PORT", 10000))
        print(f"🚀 Flask server running on port {port}")
        app.run(host="0.0.0.0", port=port)

    else:
        # fallback (local testing only)
        print("🤖 Running in POLLING mode")
        bot.infinity_polling(skip_pending=True)

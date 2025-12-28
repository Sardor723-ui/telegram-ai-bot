import telebot, requests, os, json
from datetime import date

BOT_TOKEN = os.getenv("8445452648:AAF2w-PpKsuwzTRA-GbhtZOXvnvXdgDJd6M")
HF_TOKEN = os.getenv("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")
ADMIN_ID = int(os.getenv("1438837962"))

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "users.json"
DAILY_LIMIT = 5
REF_BONUS = 5

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    return json.load(open(DB_FILE))

def save_db(db):
    json.dump(db, open(DB_FILE, "w"))

def get_user(uid):
    db = load_db()
    today = str(date.today())
    if str(uid) not in db:
        db[str(uid)] = {
            "lang": "uz",
            "used": 0,
            "date": today,
            "ref": False
        }
    if db[str(uid)]["date"] != today:
        db[str(uid)]["used"] = 0
        db[str(uid)]["date"] = today
    save_db(db)
    return db[str(uid)]

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    args = msg.text.split()
    user = get_user(uid)

    if len(args) > 1 and not user["ref"]:
        ref_id = args[1]
        db = load_db()
        if ref_id in db:
            db[ref_id]["used"] = max(0, db[ref_id]["used"] - REF_BONUS)
            user["ref"] = True
            save_db(db)

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇺🇿 O‘zbek", "🇷🇺 Русский", "🇬🇧 English")
    bot.send_message(uid, "Tilni tanlang:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["🇺🇿 O‘zbek","🇷🇺 Русский","🇬🇧 English"])
def set_lang(msg):
    lang = {"🇺🇿 O‘zbek":"uz","🇷🇺 Русский":"ru","🇬🇧 English":"en"}[msg.text]
    db = load_db()
    db[str(msg.from_user.id)]["lang"] = lang
    save_db(db)
    bot.send_message(msg.chat.id, "✅ Til saqlandi. Savol yozing.")

@bot.message_handler(commands=['admin'])
def admin(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    db = load_db()
    bot.send_message(msg.chat.id, f"👥 Foydalanuvchilar: {len(db)}")

@bot.message_handler(func=lambda m: True)
def ai(msg):
    uid = msg.from_user.id
    user = get_user(uid)

    if user["used"] >= DAILY_LIMIT:
        bot.send_message(uid, "❌ Kunlik limit tugadi.")
        return

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    data = {"inputs": msg.text}

    r = requests.post(
        "https://api-inference.huggingface.co/models/google/flan-t5-base",
        headers=headers,
        json=data
    )

    try:
        answer = r.json()[0]["generated_text"]
    except:
        answer = "Xatolik, keyinroq urinib ko‘ring."

    user["used"] += 1
    db = load_db()
    db[str(uid)] = user
    save_db(db)

    bot.send_message(uid, answer)

bot.infinity_polling()

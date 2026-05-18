import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import threading
import time
import os
import http.server
import socketserver
from datetime import datetime, timedelta

# MongoDB ke liye packages
from pymongo import MongoClient
import certifi

# --- Your Official Bot Token ---
BOT_TOKEN = "8632696115:AAF8PH4Skx6Jl_bXjhOQZ7Yzopj7RyYxfgo"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# 👑 DUAL OWNER SECURITY LOCK
# ==========================================
OWNER_IDS = [8046759728, 8554107685]  # @descent_boyy & @sorry_madam_ji

# ==========================================
# ☁️ MONGODB CLOUD DATABASE SETUP
# ==========================================
MONGO_URI = "mongodb+srv://dhangarprashant98_db_user:18ERAEHHQN0b6wNu@cluster0.uivjajj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['school_survival_db']
users_collection = db['users']

# ==========================================
# 🛡️ ANTI-CRASH NAME FILTER & POINTS LOGIC
# ==========================================
def clean_name(name):
    if not name: 
        return "Player"
    return name.replace('[', '').replace(']', '').replace('*', '').replace('_', '').replace('`', '')

def add_points(user_id, name, points):
    uid = str(user_id)
    safe_name = clean_name(name)
    users_collection.update_one(
        {"_id": uid},
        {"$inc": {"points": points}, "$set": {"name": safe_name}},
        upsert=True
    )
    if points > 0:
        user = users_collection.find_one({"_id": uid})
        if user and "referred_by" in user:
            referrer_id = user["referred_by"]
            commission = int(points * 0.10)
            if commission > 0:
                users_collection.update_one(
                    {"_id": str(referrer_id)},
                    {"$inc": {"points": commission}}
                )

def get_points(user_id):
    user = users_collection.find_one({"_id": str(user_id)})
    return user.get("points", 0) if user else 0

def get_top_players():
    users = users_collection.find().sort("points", -1).limit(10)
    return [(u["_id"], u.get("name", "Player"), u.get("points", 0)) for u in users]

def build_leaderboard():
    rows = get_top_players()
    text = "🏆 **GLOBAL TOP 10 LEADERBOARD** 🏆\n\n"
    if not rows: 
        text += "_The database is currently empty. Start playing to rank up!_"
    else:
        for idx, (uid, name, pts) in enumerate(rows):
            display_name = clean_name(name) if name else "Player"
            text += f"**{idx + 1}.** [{display_name}](tg://user?id={uid}) ➡️ **{pts} points**\n"
            
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Refresh Standings", callback_data="refresh_leaderboard"))
    return text, markup

# ==========================================
# 🎮 WORD PAIRS LIBRARY
# ==========================================
WORD_PAIRS = [
    ("Apple", "Orange"), ("Pizza", "Burger"), ("Tea", "Coffee"), ("Milk", "Juice"), 
    ("Rice", "Wheat"), ("Butter", "Cheese"), ("Cake", "Pastry"), ("Biscuit", "Cookie"), 
    ("Soup", "Salad"), ("Potato", "Tomato"), ("Onion", "Garlic"), ("Carrot", "Radish"), 
    ("Lemon", "Lime"), ("Bread", "Roti"), ("Noodles", "Pasta"), ("Ice Cream", "Chocolate"), 
    ("Peanut", "Almond"), ("Sugar", "Salt"), ("Jam", "Honey"), ("Watermelon", "Papaya"),
    ("Tiger", "Lion"), ("Dog", "Wolf"), ("Cat", "Leopard"), ("Horse", "Donkey"), 
    ("Rabbit", "Mouse"), ("Frog", "Toad"), ("Butterfly", "Moth"), ("Snake", "Earthworm"), 
    ("Eagle", "Hawk"), ("Shark", "Dolphin"), ("Whale", "Shark"), ("Penguin", "Ostrich"), 
    ("Monkey", "Gorilla"), ("Elephant", "Hippo"), ("Bear", "Panda"), ("Cow", "Buffalo"), 
    ("Goat", "Sheep"), ("Hen", "Duck"), ("Crow", "Pigeon"), ("Parrot", "Peacock"), 
    ("Ant", "Spider"), ("Bee", "Wasp")
]

# ==========================================
# 🎮 GAME LOGIC & STATE MANAGEMENT
# ==========================================
games = {}

def init_game(chat_id):
    games[chat_id] = {
        'state': 'inactive',
        'players': {}, 
        'imposter_ids': [],
        'public_word': "",
        'imposter_word': "",
        'explanations': {}, 
        'votes': {},
        'initiator_id': None 
    }

def is_group(message):
    return message.chat.type in ['group', 'supergroup']

def is_private(message):
    return message.chat.type == 'private'

# ==========================================
# ⏱️ TIMERS & PHASES
# ==========================================
def lobby_timer(chat_id):
    intervals = [
        (90, "⏳ **1 minute left to join the arena!**"),
        (30, "⏳ **30 seconds left to join!**"),
        (20, "⏳ **10 seconds remaining!**"),
        (5,  "⏳ **5 seconds...**")
    ]
    
    for wait_time, warning_msg in intervals:
        time.sleep(wait_time)
        if chat_id not in games or games[chat_id]['state'] != 'lobby':
            return 
        bot.send_message(chat_id, warning_msg, parse_mode="Markdown")

    time.sleep(1) 
    if chat_id in games and games[chat_id]['state'] == 'lobby':
        if len(games[chat_id]['players']) >= 4:
            start_game_logic(chat_id)
        else:
            bot.send_message(chat_id, f"⚠️ **LOBBY TIMEOUT:** Minimum 4 players required. Game terminated.", parse_mode="Markdown")
            games[chat_id]['state'] = 'inactive'

def explanation_timer(chat_id):
    time.sleep(90) 
    if chat_id in games and games[chat_id]['state'] == 'explaining':
        conclude_explanation_phase(chat_id)

def conclude_explanation_phase(chat_id):
    game = games[chat_id]
    game['state'] = 'voting'
    
    compiled_text = "📊 **EXPLANATION PHASE CONCLUDED!** 📊\n\n"
    if game['explanations']:
        compiled_text += "**Review the statements:**\n\n"
        for uid, exp_text in game['explanations'].items():
            safe_name = clean_name(game['players'][uid]['name'])
            compiled_text += f"• {safe_name} explained: \"_{exp_text}_\"\n"
            
    compiled_text += "\n🚨 **THE VOTING PHASE IS NOW OPEN!** 🚨\n\n👉 Reply to someone with `/vote` to eliminate them!"
    bot.send_message(chat_id, compiled_text, parse_mode="Markdown")

# ==========================================
# 🚀 CORE GAME COMMANDS
# ==========================================
@bot.message_handler(commands=['start', 'game'])
def handle_start(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    safe_name = clean_name(message.from_user.first_name)

    if is_private(message):
        text_args = message.text.split()
        referral_bonus_text = ""
        existing_user = users_collection.find_one({"_id": user_id})
        
        if len(text_args) > 1 and text_args[1].startswith("ref_"):
            referrer_id = text_args[1].replace("ref_", "").strip()
            if not existing_user and referrer_id != user_id:
                users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {"name": safe_name, "points": 50, "referred_by": referrer_id}},
                    upsert=True
                )
                users_collection.update_one(
                    {"_id": str(referrer_id)},
                    {"$inc": {"points": 100}}
                )
                referral_bonus_text = "🎁 **REFERRAL BONUS ACTIVATED!**\n\n"
                try:
                    bot.send_message(int(referrer_id), f"🎉 Earned **+100 Points** from referral!", parse_mode="Markdown")
                except:
                    pass

        if not users_collection.find_one({"_id": user_id}):
            users_collection.update_one(
                {"_id": user_id},
                {"$set": {"name": safe_name, "points": 0}},
                upsert=True
            )

        text = f"🕵️‍♂️ **SYSTEM ACCESS GRANTED** 🕵️‍♂️\n\nGreetings, **{safe_name}**.\n\n{referral_bonus_text}Welcome to Blind Imposter bot. Add me to a group to play!"
        bot.send_message(chat_id, text, parse_mode="Markdown")
        return

    if chat_id not in games:
        init_game(chat_id)
        
    if games[chat_id]['state'] != 'inactive':
        bot.reply_to(message, "❌ **Game is already running. Type `/end` to stop it.**")
        return

    games[chat_id]['state'] = 'lobby'
    games[chat_id]['players'] = {}
    games[chat_id]['initiator_id'] = message.from_user.id 
    
    text = "🕵️‍♂️ **THE ARENA IS OPEN** 🕵️‍♂️\n\n👉 **Type `/join` to enter the game!**\n⚡ **Type `/startgame` to force start with 4+ players!**"
    bot.send_message(chat_id, text, parse_mode="Markdown")
    threading.Thread(target=lobby_timer, args=(chat_id,)).start()

@bot.message_handler(commands=['help'])
def show_help(message):
    text = (
        "📖 **PROTOCOL MANUAL** 📖\n\n"
        "• `/start` - Start game lobby in a group.\n"
        "• `/join` - Enter the lobby.\n"
        "• `/startgame` - Start game immediately.\n"
        "• `/vote` - Vote out suspects.\n"
        "• `/end` - Stop ongoing game.\n"
        "• `/score` - Check your points.\n"
        "• `/toprich` - View leaderboard.\n"
        "• `/daily` - Claim 50 daily points (PM Only).\n"
        "• `/id` - Get unique Telegram User ID.\n"
        "• `/refer` - Get referral link."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['join'])
def join_game(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **Use this command inside a Group Chat.**")
        return

    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'lobby':
        bot.reply_to(message, "❌ **No active lobby found. Type `/start` first.**")
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username or ""

    if user_id in games[chat_id]['players']:
        bot.reply_to(message, "⚠️ You have already joined.")
        return

    try:
        bot.send_message(user_id, "✅ **Lobby entry secured.**")
        games[chat_id]['players'][user_id] = {'name': user_name, 'username': username}
        bot.send_message(chat_id, f"✅ **{clean_name(user_name)} has joined! ({len(games[chat_id]['players'])}/4+)**", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ **Private message failed!** Click my profile, tap **START**, then try `/join` again.")

@bot.message_handler(commands=['startgame'])
def manual_start(message):
    chat_id = message.chat.id
    if chat_id in games and games[chat_id]['state'] == 'lobby':
        if len(games[chat_id]['players']) >= 4:
            start_game_logic(chat_id)
        else:
            bot.reply_to(message, f"⚠️ Min 4 players required. Current: {len(games[chat_id]['players'])}")
    else:
        bot.reply_to(message, "❌ No active lobby to start.")

def start_game_logic(chat_id):
    game = games[chat_id]
    game['state'] = 'explaining'
    
    num_players = len(game['players'])
    num_imposters = 1 if num_players < 8 else 2

    public_word, imposter_word = random.choice(WORD_PAIRS)
    game['public_word'], game['imposter_word'] = public_word, imposter_word
    
    player_ids = list(game['players'].keys())
    game['imposter_ids'] = random.sample(player_ids, num_imposters)
    game['explanations'], game['votes'] = {}, {}

    bot.send_message(chat_id, "🎮 **THE GAME HAS COMMENCED!** 🎮\n\n➡️ **Go to Bot Private Message (PM) to see your secret word and reply with your explanation!**", parse_mode="Markdown")

    for uid in player_ids:
        try:
            assigned_word = imposter_word if uid in game['imposter_ids'] else public_word
            bot.send_message(uid, f"🤫 **YOUR SECRET WORD:** **{assigned_word}**\n\n➡️ Type your explanation/clue here in PM!", parse_mode="Markdown")
        except:
            pass

    threading.Thread(target=explanation_timer, args=(chat_id,)).start()

# ==========================================
# 🤫 OWNER PROTOCOLS (.pari / .anc) & PM HANDLER
# ==========================================
def broadcast_worker(message_to_send, trigger_owner_id):
    all_users = users_collection.find({}, {"_id": 1})
    success_count = 0
    for user in all_users:
        try:
            bot.copy_message(chat_id=int(user["_id"]), from_chat_id=message_to_send.chat.id, message_id=message_to_send.message_id)
            success_count += 1
            time.sleep(0.3)  
        except:
            pass
    try:
        bot.send_message(trigger_owner_id, f"📢 Broadcast done! Sent to {success_count} users.")
    except:
        pass

@bot.message_handler(func=lambda m: is_private(m))
def handle_private_messages(message):
    user_id = message.from_user.id
    text_clean = message.text.strip() if message.text else ""

    # 🔥 STRICT COMMAND PASSTHROUGH (PM mein slash commands ko bypass hone do)
    if text_clean.startswith('/'):
        if text_clean.startswith('/daily'):
            claim_daily(message)
        elif text_clean.startswith('/id'):
            get_user_id(message)
        elif text_clean.startswith('/toprich'):
            show_leaderboard(message)
        elif text_clean.startswith('/refer') or text_clean.startswith('/affiliate'):
            generate_referral_link(message)
        elif text_clean.startswith('/score'):
            check_score(message)
        elif text_clean.startswith('/help'):
            show_help(message)
        return

    # 1. 👑 SEASON RESET COMMAND (.pari) - Deletes all documents for a fresh wipe
    if text_clean == ".pari":
        if user_id in OWNER_IDS:
            users_collection.delete_many({}) # Sab kuch delete mado! 🔥
            bot.reply_to(message, "⚙️ **DATABASE WIPE SUCCESSFUL:**\n\n🔥 Pichle season ke saare bando ka record saaf kar diya gaya hai! Leaderboard completely khali hai.")
        else:
            bot.reply_to(message, "🛑 Access Denied.")
        return

    # 2. 📢 GLOBAL ANNOUNCEMENT BROADCAST COMMAND (.anc)
    if text_clean == ".anc":
        if user_id in OWNER_IDS:
            if message.reply_to_message:
                bot.reply_to(message, "🚀 Broadcasting started...")
                threading.Thread(target=broadcast_worker, args=(message.reply_to_message, user_id), daemon=True).start()
            else:
                bot.reply_to(message, "❌ Reply to a message to broadcast.")
        else:
            bot.reply_to(message, "🛑 Access Denied.")
        return

    # Normal game PM collector
    for chat_id, game in games.items():
        if game['state'] == 'explaining' and user_id in game['players']:
            if message.text:  
                if user_id not in game['explanations']:
                    game['explanations'][user_id] = message.text
                    bot.reply_to(message, "✅ **Explanation recorded! Return to group.**")
                else:
                    bot.reply_to(message, "⚠️ Already submitted.")
                return

    bot.reply_to(message, "❌ **ERROR: Use official commands or inputs only.**")

# ==========================================
# 💰 COOLDOWN BASED DAILY COMMAND SYSTEM
# ==========================================
def claim_daily(message):
    user_id = str(message.from_user.id)
    user_name = clean_name(message.from_user.first_name)
    
    user = users_collection.find_one({"_id": user_id})
    row_claim = user.get("daily_claim") if user else None
    
    now = datetime.now()
    can_claim = False
    
    if not row_claim:
        can_claim = True
    else:
        last_claim = datetime.fromisoformat(row_claim)
        if now - last_claim >= timedelta(hours=24):
            can_claim = True
            
    if can_claim:
        users_collection.update_one(
            {"_id": user_id},
            {"$inc": {"points": 50}, "$set": {"name": user_name, "daily_claim": now.isoformat()}},
            upsert=True
        )
        bot.reply_to(message, "🎁 **DAILY BONUS CLAIMED!** 💰 **+50 points** added to your wallet.")
    else:
        last_claim = datetime.fromisoformat(row_claim)
        time_left = (last_claim + timedelta(hours=24)) - now
        h, rem = divmod(time_left.seconds, 3600)
        m, _ = divmod(rem, 60)
        bot.reply_to(message, f"❌ Already claimed! Try again in **{h}h {m}m**.")

# ==========================================
# 🗳️ VOTING & UTILITY COMMANDS
# ==========================================
@bot.message_handler(commands=['vote'])
def process_vote_command(message):
    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'voting':
        bot.reply_to(message, "❌ Voting is closed.")
        return
        
    game, voter_id = games[chat_id], message.from_user.id
    if voter_id not in game['players'] or voter_id in game['votes']:
        return

    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id

    if target_id and target_id in game['players']:
        game['votes'][voter_id] = target_id
        bot.reply_to(message, "🗳️ Vote Registered!")
        if len(game['votes']) == len(game['players']):
            conclude_game_results(chat_id)

def conclude_game_results(chat_id):
    game = games[chat_id]
    bot.send_message(chat_id, f"📊 **Game Over!**\n🍏 Public word: {game['public_word']}\n🥭 Imposter word: {game['imposter_word']}")
    game['state'] = 'inactive'

@bot.message_handler(commands=['id'])
def get_user_id(message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        bot.reply_to(message, f"🆔 User ID: `{target_id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"🆔 Your ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['score'])
def check_score(message):
    pts = get_points(message.from_user.id)
    bot.reply_to(message, f"🥇 Your balance: `{pts} points`")

@bot.message_handler(commands=['toprich'])
def show_leaderboard(message):
    text, markup = build_leaderboard()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_leaderboard")
def refresh_leaderboard_click(call):
    text, markup = build_leaderboard()
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "Synced!")
    except:
        bot.answer_callback_query(call.id, "Already updated!")

@bot.message_handler(commands=['end'])
def end_game(message):
    chat_id = message.chat.id
    if chat_id in games:
        games[chat_id]['state'] = 'inactive'
        bot.reply_to(message, "🛑 Game forcefully stopped.")

@bot.message_handler(commands=['refer'])
def generate_referral_link(message):
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    bot.reply_to(message, f"🔗 **Your Referral Link:**\n`{ref_link}`", parse_mode="Markdown")

# Server run block
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Ultimate Fixed Bot is running...")
bot.infinity_polling()

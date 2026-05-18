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
OWNER_IDS = [8046759728, 8554107685]  # @descent_boyy & @sorry_madam_ji Authorized

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
            # 🔥 Clickable User Tag Enforced
            text += f"**{idx + 1}.** [{display_name}](tg://user?id={uid}) ➡️ `{pts} points` \n"
            
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Refresh Standings", callback_data="refresh_leaderboard"))
    return text, markup

# ==========================================
# 🎮 MASSIVE 150+ WORD PAIRS LIBRARY
# ==========================================
WORD_PAIRS = [
    # 🍔 Food & Drinks
    ("Apple", "Orange"), ("Pizza", "Burger"), ("Tea", "Coffee"), ("Milk", "Juice"), 
    ("Rice", "Wheat"), ("Butter", "Cheese"), ("Cake", "Pastry"), ("Biscuit", "Cookie"), 
    ("Soup", "Salad"), ("Potato", "Tomato"), ("Onion", "Garlic"), ("Carrot", "Radish"), 
    ("Lemon", "Lime"), ("Bread", "Roti"), ("Noodles", "Pasta"), ("Ice Cream", "Chocolate"), 
    ("Peanut", "Almond"), ("Sugar", "Salt"), ("Jam", "Honey"), ("Watermelon", "Papaya"),
    # 🐾 Animals & Birds
    ("Tiger", "Lion"), ("Dog", "Wolf"), ("Cat", "Leopard"), ("Horse", "Donkey"), 
    ("Rabbit", "Mouse"), ("Frog", "Toad"), ("Butterfly", "Moth"), ("Snake", "Earthworm"), 
    ("Eagle", "Hawk"), ("Shark", "Dolphin"), ("Whale", "Shark"), ("Penguin", "Ostrich"), 
    ("Monkey", "Gorilla"), ("Elephant", "Hippo"), ("Bear", "Panda"), ("Cow", "Buffalo"), 
    ("Goat", "Sheep"), ("Hen", "Duck"), ("Crow", "Pigeon"), ("Parrot", "Peacock"), 
    ("Ant", "Spider"), ("Bee", "Wasp"),
    # 💻 Tech & Daily Objects
    ("Laptop", "Desktop"), ("Phone", "Tablet"), ("Television", "Monitor"), ("Watch", "Clock"), 
    ("Pen", "Marker"), ("Pencil", "Crayon"), ("Book", "Magazine"), ("Newspaper", "Magazine"), 
    ("Chair", "Sofa"), ("Table", "Desk"), ("Fan", "Cooler"), ("Fridge", "Air Conditioner"), 
    ("Glasses", "Goggles"), ("Backpack", "Suitcase"), ("Wallet", "Purse"), ("Key", "Lock"), 
    ("Scissors", "Knife"), ("Spoon", "Fork"), ("Plate", "Bowl"), ("Bottle", "Jug"), 
    ("Mirror", "Window"), ("Door", "Gate"), ("Bed", "Sofa"), ("Pillow", "Cushion"), 
    ("Towel", "Blanket"), ("Soap", "Shampoo"), ("Toothbrush", "Comb"), ("Umbrella", "Raincoat"), 
    ("Candle", "Bulb"), ("Matchbox", "Lighter"), ("Camera", "Binoculars"),
    # 🌍 Nature, Places & Materials
    ("Sun", "Moon"), ("Star", "Planet"), ("River", "Ocean"), ("Lake", "Pond"), 
    ("Mountain", "Hill"), ("Forest", "Jungle"), ("Rain", "Snow"), ("Cloud", "Fog"), 
    ("Village", "City"), ("Street", "Highway"), ("House", "Apartment"), ("School", "College"), 
    ("Hospital", "Clinic"), ("Shop", "Mall"), ("Park", "Garden"), ("Temple", "Mosque"), 
    ("Library", "Museum"), ("Beach", "Desert"), ("Island", "Continent"), ("Earth", "Mars"), 
    ("Gold", "Silver"), ("Diamond", "Ruby"), ("Iron", "Steel"), ("Coal", "Wood"),
    # 👕 Body Parts & Clothing
    ("Eye", "Ear"), ("Hand", "Foot"), ("Hair", "Nails"), ("Shirt", "T-shirt"), 
    ("Jacket", "Sweater"), ("Shoes", "Slippers"), ("Hat", "Cap"), ("Socks", "Gloves"), 
    ("Ring", "Necklace"), ("Pants", "Shorts"), ("Tie", "Belt"), ("Scarf", "Muffler"), 
    ("Perfume", "Deodorant")
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
            bot.send_message(chat_id, f"⚠️ **LOBBY TIMEOUT:** The minimum requirement of 4 players was not met. The session has been terminated. (Current: {len(games[chat_id]['players'])})", parse_mode="Markdown")
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
        compiled_text += "**Review the submitted statements carefully:**\n\n"
        for uid, exp_text in game['explanations'].items():
            safe_name = clean_name(game['players'][uid]['name'])
            # 🔥 Clickable User Tag Enforced
            compiled_text += f"• [{safe_name}](tg://user?id={uid}) explained: \"_{exp_text}_\"\n"
    else:
        compiled_text += "**No players submitted their statements in time.**\n"
        
    compiled_text += "\n🚨 **THE VOTING PHASE IS NOW OPEN!** 🚨\n\n👉 **How to cast your vote:**\n1️⃣ Reply to the suspect's message with `/vote`\n2️⃣ Type `/vote @username`\n3️⃣ Type `/vote [UserID]`"
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
                referral_bonus_text = "🎁 **REFERRAL BONUS ACTIVATED!** You received **+50 Points** and your friend received **+100 Points**!\n\n"
                try:
                    bot.send_message(int(referrer_id), f"🎉 *New Ally Joined!* Someone used your referral link. You earned **+100 Points**!", parse_mode="Markdown")
                except:
                    pass

        if not users_collection.find_one({"_id": user_id}):
            users_collection.update_one(
                {"_id": user_id},
                {"$set": {"name": safe_name, "points": 0}},
                upsert=True
            )

        text = (
            "🕵️‍♂️ **SYSTEM ACCESS GRANTED** 🕵️‍♂️\n\n"
            f"Greetings, **{safe_name}**.\n\n"
            f"{referral_bonus_text}"
            "You have entered the secure mainframe of **Blind Imposter**. "
            "This bot analyzes deception, strategy, and manipulation.\n\n"
            "🧠 **Your Objective:** When added to a group, analyze the secret words, identify the liars, and amass points to dominate the global leaderboard.\n\n"
            "Use `/help` to view the comprehensive protocol manual. Good luck."
        )
        bot.send_message(chat_id, text, parse_mode="Markdown")
        return

    if chat_id not in games:
        init_game(chat_id)
        
    if games[chat_id]['state'] != 'inactive':
        bot.reply_to(message, "❌ **ACTION DENIED: A game session is already forming or running in this chat. Type `/end` to terminate it first.**")
        return

    games[chat_id]['state'] = 'lobby'
    games[chat_id]['players'] = {}
    games[chat_id]['initiator_id'] = message.from_user.id 
    
    text = (
        "🕵️‍♂️ **THE ARENA IS OPEN** 🕵️‍♂️\n\n"
        "A new session of deception has been initiated. Are you sharp enough to survive?\n\n"
        "👉 **Type `/join` in this group to enter the game!** (Min: 4 Players)\n"
        "⚡ **Type `/startgame` to launch immediately once 4+ players join!**\n\n"
        "⚠️ **MANDATORY:** You must start the bot in private PM first, otherwise, you cannot receive your secret word."
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")
    threading.Thread(target=lobby_timer, args=(chat_id,)).start()

@bot.message_handler(commands=['help'])
def show_help(message):
    text = (
        "📖 **THE OFFICIAL PROTOCOL MANUAL** 📖\n\n"
        "**🎮 GAMEPLAY COMMANDS:**\n"
        "• `/start` - Initiate a new game lobby in a group.\n"
        "• `/join` - Enter the active lobby.\n"
        "• `/startgame` - Manually start the game without waiting for the timer.\n"
        "• `/vote` - Cast your vote (reply to a message, use `@username`, or User ID).\n"
        "• `/end` - Instantly terminate an ongoing session.\n\n"
        "**💰 ECONOMY & RANKING:**\n"
        "• `/score` - Check your current verified points.\n"
        "• `/toprich` - View the Global Top 10 Leaderboard.\n"
        "• `/daily` - Claim 50 free points daily (Executes **ONLY** in bot PM).\n"
        "• `/refer` - Generate your lifetime affiliate link to earn passive coins!\n\n"
        "**⚙️ UTILITIES:**\n"
        "• `/id` - Reply to someone with this to extract their unique identifier.\n\n"
        "**🧠 REWARDS SYSTEM:**\n"
        "• Public Victory: **+10 points** to innocents.\n"
        "• Imposter Victory: **+25 points** to imposters."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['join'])
def join_game(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: You can only join a game inside a Group Chat arena.**")
        return

    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'lobby':
        bot.reply_to(message, "❌ **ACTION DENIED: There is no active lobby. An administrator must type `/start` to initiate a new session.**")
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username or ""

    if user_id in games[chat_id]['players']:
        bot.reply_to(message, f"⚠️ **WARNING:** {clean_name(user_name)}, you are already registered in the current lobby.")
        return

    try:
        bot.send_message(user_id, "✅ **Lobby entry secured. Await further instructions in the group chat.**")
        games[chat_id]['players'][user_id] = {'name': user_name, 'username': username}
        # 🔥 Clickable User Tag Enforced for Lobby Updates
        p_list = "\n".join([f"👤 [{clean_name(p['name'])}](tg://user?id={uid})" for uid, p in games[chat_id]['players'].items()])
        bot.send_message(chat_id, f"✅ **[{clean_name(user_name)}](tg://user?id={user_id}) has successfully joined! ({len(games[chat_id]['players'])}/4+)**\n\n**Registered Players:**\n{p_list}", parse_mode="Markdown")
    except:
        bot.reply_to(message, f"❌ **ACCESS DENIED!** Click my profile, tap **START**, and then try `/join` again.")

@bot.message_handler(commands=['startgame'])
def manual_start(message):
    chat_id = message.chat.id
    if chat_id in games and games[chat_id]['state'] == 'lobby':
        if len(games[chat_id]['players']) >= 4:
            start_game_logic(chat_id)
        else:
            bot.reply_to(message, f"⚠️ **ACTION DENIED: A minimum of 4 players is required to force start the game. (Current: {len(games[chat_id]['players'])})**")
    else:
        bot.reply_to(message, "❌ **ACTION DENIED: There is no active lobby waiting to be started.**")

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

    # 🔥 Clickable User Tag Enforced
    tags = [f"[{clean_name(p['name'])}](tg://user?id={uid})" for uid, p in game['players'].items()]
    bot.send_message(chat_id, f"🎮 **THE GAME HAS OFFICIALLY COMMENCED!** 🎮\n\n{', '.join(tags)}\n\n➡️ **Proceed to the bot's Private Messages (PM) and explain your secret word.**\n\n⏳ **You have exactly 1 minute and 30 seconds to submit your statement!**", parse_mode="Markdown")

    for uid in player_ids:
        try:
            assigned_word = imposter_word if uid in game['imposter_ids'] else public_word
            bot.send_message(uid, f"🤫 **YOUR SECRET WORD:** **{assigned_word}**\n\n➡️ **Proceed to provide your explanation here in the PM.**\n\n⚠️ _Note: You do NOT know your identity! If your word is different from the majority, you are the Imposter. Defend your word carefully!_", parse_mode="Markdown")
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
        bot.send_message(trigger_owner_id, f"📢 **BROADCAST PROTOCOL COMPLETE** 📢\n\n✅ Sent Successfully: `{success_count}` users.", parse_mode="Markdown")
    except:
        pass

@bot.message_handler(func=lambda m: is_private(m))
def handle_private_messages(message):
    user_id = message.from_user.id
    text_clean = message.text.strip() if message.text else ""

    if text_clean.startswith('/'):
        if text_clean.startswith('/daily'): claim_daily(message)
        elif text_clean.startswith('/id'): get_user_id(message)
        elif text_clean.startswith('/toprich'): show_leaderboard(message)
        elif text_clean.startswith('/refer') or text_clean.startswith('/affiliate'): generate_referral_link(message)
        elif text_clean.startswith('/score'): check_score(message)
        elif text_clean.startswith('/help'): show_help(message)
        return

    # 1. 👑 SEASON RESET COMMAND (.pari) - Full Server Wipe
    if text_clean == ".pari":
        if user_id in OWNER_IDS:
            users_collection.delete_many({})
            bot.reply_to(message, "⚙️ **DATABASE WIPE SUCCESSFUL:**\n\n🔥 Pichle season ke saare bando ka record saaf kar diya gaya hai! Leaderboard completely khali hai.")
        else:
            bot.reply_to(message, "🛑 **ACCESS DENIED:** Unauthorized compilation.")
        return

    # 2. 📢 GLOBAL ANNOUNCEMENT BROADCAST COMMAND (.anc)
    if text_clean == ".anc":
        if user_id in OWNER_IDS:
            if message.reply_to_message:
                bot.reply_to(message, "🚀 **ANNOUNCEMENT ENGAGED:** Starting background transmission to all database users safely...", parse_mode="Markdown")
                threading.Thread(target=broadcast_worker, args=(message.reply_to_message, user_id), daemon=True).start()
            else:
                bot.reply_to(message, "❌ **PROTOCOL ERROR:** Please use this command by **REPLYING** to a message.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "🛑 **ACCESS DENIED:** Unauthorized broadcast transmission.")
        return

    # Normal game PM collector
    for chat_id, game in games.items():
        if game['state'] == 'explaining' and user_id in game['players']:
            if message.text:  
                if user_id not in game['explanations']:
                    game['explanations'][user_id] = message.text
                    bot.reply_to(message, "✅ **Your explanation has been securely encrypted and recorded. Return to the group.**", parse_mode="Markdown")
                else:
                    bot.reply_to(message, "⚠️ **ACTION FAILED: You have already submitted a statement for this round.**", parse_mode="Markdown")
                return

    bot.reply_to(message, "❌ **ERROR: Bot only processes inputs during game play or via official system commands.**")

# ==========================================
# 💰 COOLDOWN BASED DAILY REWARD SYSTEM
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
        bot.reply_to(message, "🎁 **DAILY BONUS AUTHORIZED!** 🎁\n\n💰 **+50 points** have been securely deposited into your account.\n⏳ _Return in 24 hours for your next claim._", parse_mode="Markdown")
    else:
        last_claim = datetime.fromisoformat(row_claim)
        time_left = (last_claim + timedelta(hours=24)) - now
        h, rem = divmod(time_left.seconds, 3600)
        m, _ = divmod(rem, 60)
        bot.reply_to(message, f"❌ **ACCESS DENIED: You have already claimed your daily reward.**\n\n⏰ _Next refresh available in:_ **{h}h {m}m**", parse_mode="Markdown")

# ==========================================
# 🗳️ VOTING & RESULTS LOGIC
# ==========================================
@bot.message_handler(commands=['vote'])
def process_vote_command(message):
    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'voting':
        bot.reply_to(message, "❌ **ACTION DENIED: The voting phase is currently closed or no active game exists.**")
        return
        
    game, voter_id = games[chat_id], message.from_user.id
    if voter_id not in game['players'] or voter_id in game['votes']:
        return

    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id

    if target_id and target_id in game['players']:
        game['votes'][voter_id] = target_id
        safe_target_name = clean_name(game['players'][target_id]['name'])
        # 🔥 Clickable User Tag Enforced
        target_tag = f"[{safe_target_name}](tg://user?id={target_id})"
        bot.reply_to(message, f"🗳️ **Vote Confirmed:** Your execution vote for {target_tag} has been registered.", parse_mode="Markdown")
        if len(game['votes']) == len(game['players']):
            conclude_game_results(chat_id)

def conclude_game_results(chat_id):
    game = games[chat_id]
    tally = {}
    for vid in game['votes'].values():
        tally[vid] = tally.get(vid, 0) + 1
        
    max_votes = max(tally.values())
    highest_voted_players = [uid for uid, count in tally.items() if count == max_votes]
    
    results = "📊 **FINAL ELIMINATION RESULTS!** 📊\n\n"
    for uid, count in tally.items():
        safe_name = clean_name(game['players'][uid]['name'])
        # 🔥 Clickable User Tag Enforced
        user_tag = f"[{safe_name}](tg://user?id={uid})"
        results += f"• {user_tag}: {count} votes\n"
        
    results += f"\n🍏 **Public Word:** **{game['public_word']}**\n🥭 **Imposter Word:** **{game['imposter_word']}**\n\n"

    if len(highest_voted_players) > 1:
        results += "👔 **STALEMATE! The group failed to reach a consensus.**\n🏆 **THE IMPOSTERS ESCAPE AND SECURE THE VICTORY!**\n\n🏅 **Points Rewarded:**\n"
        for imp_id in game['imposter_ids']:
            safe_imp_name = clean_name(game['players'][imp_id]['name'])
            add_points(imp_id, safe_imp_name, 25)
            # 🔥 Clickable User Tag Enforced
            imp_tag = f"[{safe_imp_name}](tg://user?id={imp_id})"
            results += f"• {imp_tag} (Imposter): **+25 points**\n"
    elif highest_voted_players[0] in game['imposter_ids']:
        caught_id = highest_voted_players[0]
        safe_caught_name = clean_name(game['players'][caught_id]['name'])
        # 🔥 Clickable User Tag Enforced
        caught_tag = f"[{safe_caught_name}](tg://user?id={caught_id})"
        results += f"🎯 **EXECUTION SUCCESSFUL! {caught_tag} was indeed a liar!**\n🏆 **THE PUBLIC WINS!**\n\n🏅 **Points Rewarded:**\n"
        for uid in game['players'].keys():
            if uid not in game['imposter_ids']:
                safe_norm_name = clean_name(game['players'][uid]['name'])
                add_points(uid, safe_norm_name, 10)
                # 🔥 Clickable User Tag Enforced
                norm_tag = f"[{safe_norm_name}](tg://user?id={uid})"
                results += f"• {norm_tag}: **+10 points**\n"
    else:
        wrong_id = highest_voted_players[0]
        safe_wrong_name = clean_name(game['players'][wrong_id]['name'])
        # 🔥 Clickable User Tag Enforced
        wrong_tag = f"[{safe_wrong_name}](tg://user?id={wrong_id})"
        results += f"❌ **CATASTROPHIC FAILURE! You executed {wrong_tag}, an innocent player!**\n🏆 **THE IMPOSTERS WIN THE GAME!**\n\n🏅 **Points Rewarded:**\n"
        for imp_id in game['imposter_ids']:
            safe_imp_name = clean_name(game['players'][imp_id]['name'])
            add_points(imp_id, safe_imp_name, 25)
            # 🔥 Clickable User Tag Enforced
            imp_tag = f"[{safe_imp_name}](tg://user?id={imp_id})"
            results += f"• {imp_tag} (Imposter): **+25 points**\n"

    bot.send_message(chat_id, results, parse_mode="Markdown")
    game['state'] = 'inactive'

@bot.message_handler(commands=['id'])
def get_user_id(message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = clean_name(message.reply_to_message.from_user.first_name)
        # 🔥 Clickable User Tag Enforced
        bot.reply_to(message, f"👤 **Target:** [{target_name}](tg://user?id={target_id})\n🆔 **Unique ID:** `{target_id}`", parse_mode="Markdown")
    else:
        sender_id = message.from_user.id
        sender_name = clean_name(message.from_user.first_name)
        # 🔥 Clickable User Tag Enforced
        bot.reply_to(message, f"👤 **User:** [{sender_name}](tg://user?id={sender_id})\n🆔 **Your Unique ID:** `{sender_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['score'])
def check_score(message):
    pts = get_points(message.from_user.id)
    safe_name = clean_name(message.from_user.first_name)
    # 🔥 Clickable User Tag Enforced
    bot.reply_to(message, f"🥇 **[{safe_name}](tg://user?id={message.from_user.id}), your current balance is:** `{pts} points`", parse_mode="Markdown")

@bot.message_handler(commands=['toprich'])
def show_leaderboard(message):
    text, markup = build_leaderboard()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_leaderboard")
def refresh_leaderboard_click(call):
    text, markup = build_leaderboard()
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "The leaderboard has been successfully synchronized!")
    except:
        bot.answer_callback_query(call.id, "The leaderboard is already up to date!")

@bot.message_handler(commands=['end'])
def end_game(message):
    chat_id = message.chat.id
    if chat_id in games:
        games[chat_id]['state'] = 'inactive'
        bot.reply_to(message, "🛑 **ADMINISTRATIVE OVERRIDE: The active game session has been forcefully terminated.**", parse_mode="Markdown")

@bot.message_handler(commands=['refer'])
def generate_referral_link(message):
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    text = (
        "👥 **BLIND IMPOSTER AFFILIATE PROGRAM** 👥\n\n"
        "Share your unique referral link to build your spy empire and earn permanent bonuses!\n\n"
        "🎁 **Instant Join Reward:**\n"
        "• You get: **+100 Points** instantly when they join!\n"
        "• Your friend gets: **+50 Points** to start their journey!\n\n"
        "💸 **Lifetime Passive Income:**\n"
        "• Earn **10% Bonus Points** every single time your referred friend wins a game!\n\n"
        "⏳ **Duration:** `Infinite / Lifetime` ♾️\n\n"
        f"🔗 **Your Personal Link:**\n`{ref_link}`\n\n"
        "_*Copy this link and drop it in groups or send it to friends!_"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# Server run block
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Ultimate Massive Fixed Bot with All Tags is running...")
bot.infinity_polling()

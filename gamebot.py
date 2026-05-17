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

# --- Your NEW Official Bot Token ---
BOT_TOKEN = "8537514716:AAEj-BrC-7L1FLws6AhrtQ3oNlMrZ1xSKZU"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# ☁️ MONGODB CLOUD DATABASE SETUP
# ==========================================
MONGO_URI = "mongodb+srv://dhangarprashant98_db_user:18ERAEHHQN0b6wNu@cluster0.uivjajj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['school_survival_db']
users_collection = db['users']

# ==========================================
# 🛡️ ANTI-CRASH NAME FILTER
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

def get_points(user_id):
    user = users_collection.find_one({"_id": str(user_id)})
    return user.get("points", 0) if user else 0

def get_top_players():
    users = users_collection.find().sort("points", -1).limit(10)
    return [(u["_id"], u.get("name", "Player"), u.get("points", 0)) for u in users]

# ==========================================
# 🎮 150+ MASSIVE WORD PAIRS LIBRARY
# ==========================================
WORD_PAIRS = [
    # 🍔 Food & Drinks (20)
    ("Apple", "Orange"), ("Pizza", "Burger"), ("Tea", "Coffee"), ("Milk", "Juice"), 
    ("Rice", "Wheat"), ("Butter", "Cheese"), ("Cake", "Pastry"), ("Biscuit", "Cookie"), 
    ("Soup", "Salad"), ("Potato", "Tomato"), ("Onion", "Garlic"), ("Carrot", "Radish"), 
    ("Lemon", "Lime"), ("Bread", "Roti"), ("Noodles", "Pasta"), ("Ice Cream", "Chocolate"), 
    ("Peanut", "Almond"), ("Sugar", "Salt"), ("Jam", "Honey"), ("Watermelon", "Papaya"),
    
    # 🐾 Animals & Birds (22)
    ("Tiger", "Lion"), ("Dog", "Wolf"), ("Cat", "Leopard"), ("Horse", "Donkey"), 
    ("Rabbit", "Mouse"), ("Frog", "Toad"), ("Butterfly", "Moth"), ("Snake", "Earthworm"), 
    ("Eagle", "Hawk"), ("Shark", "Dolphin"), ("Whale", "Shark"), ("Penguin", "Ostrich"), 
    ("Monkey", "Gorilla"), ("Elephant", "Hippo"), ("Bear", "Panda"), ("Cow", "Buffalo"), 
    ("Goat", "Sheep"), ("Hen", "Duck"), ("Crow", "Pigeon"), ("Parrot", "Peacock"), 
    ("Ant", "Spider"), ("Bee", "Wasp"),
    
    # 💻 Tech & Daily Objects (31)
    ("Laptop", "Desktop"), ("Phone", "Tablet"), ("Television", "Monitor"), ("Watch", "Clock"), 
    ("Pen", "Marker"), ("Pencil", "Crayon"), ("Book", "Magazine"), ("Newspaper", "Magazine"), 
    ("Chair", "Sofa"), ("Table", "Desk"), ("Fan", "Cooler"), ("Fridge", "Air Conditioner"), 
    ("Glasses", "Goggles"), ("Backpack", "Suitcase"), ("Wallet", "Purse"), ("Key", "Lock"), 
    ("Scissors", "Knife"), ("Spoon", "Fork"), ("Plate", "Bowl"), ("Bottle", "Jug"), 
    ("Mirror", "Window"), ("Door", "Gate"), ("Bed", "Sofa"), ("Pillow", "Cushion"), 
    ("Towel", "Blanket"), ("Soap", "Shampoo"), ("Toothbrush", "Comb"), ("Umbrella", "Raincoat"), 
    ("Candle", "Bulb"), ("Matchbox", "Lighter"), ("Camera", "Binoculars"),
    
    # 🌍 Nature, Places & Materials (24)
    ("Sun", "Moon"), ("Star", "Planet"), ("River", "Ocean"), ("Lake", "Pond"), 
    ("Mountain", "Hill"), ("Forest", "Jungle"), ("Rain", "Snow"), ("Cloud", "Fog"), 
    ("Village", "City"), ("Street", "Highway"), ("House", "Apartment"), ("School", "College"), 
    ("Hospital", "Clinic"), ("Shop", "Mall"), ("Park", "Garden"), ("Temple", "Mosque"), 
    ("Library", "Museum"), ("Beach", "Desert"), ("Island", "Continent"), ("Earth", "Mars"), 
    ("Gold", "Silver"), ("Diamond", "Ruby"), ("Iron", "Steel"), ("Coal", "Wood"),
    
    # 👕 Body Parts & Clothing (13)
    ("Eye", "Ear"), ("Hand", "Foot"), ("Hair", "Nails"), ("Shirt", "T-shirt"), 
    ("Jacket", "Sweater"), ("Shoes", "Slippers"), ("Hat", "Cap"), ("Socks", "Gloves"), 
    ("Ring", "Necklace"), ("Pants", "Shorts"), ("Tie", "Belt"), ("Scarf", "Muffler"), 
    ("Perfume", "Deodorant"),
    
    # 🚗 Transport (12)
    ("Car", "Jeep"), ("Bus", "Train"), ("Airplane", "Helicopter"), ("Bicycle", "Motorcycle"), 
    ("Boat", "Ship"), ("Truck", "Tractor"), ("Scooter", "Bike"), ("Rocket", "Jet"), 
    ("Submarine", "Ship"), ("Taxi", "Ambulance"), ("Metro", "Train"), ("Skateboard", "Roller Skates"),
    
    # ⚽ Sports & Professions (15)
    ("Cricket", "Baseball"), ("Football", "Basketball"), ("Tennis", "Badminton"), ("Chess", "Carrom"), 
    ("Ludo", "Monopoly"), ("Guitar", "Piano"), ("Flute", "Whistle"), ("Drum", "Bell"), 
    ("Doctor", "Nurse"), ("Teacher", "Principal"), ("Police", "Army"), ("Pilot", "Driver"), 
    ("Actor", "Singer"), ("Painter", "Writer"), ("Chef", "Waiter"),
    
    # 🌀 Extra Tricky Mixed Pairs (19)
    ("Pen", "Pencil"), ("Milk", "Water"), ("Apple", "Mango"), ("Chair", "Table"), 
    ("Shoes", "Socks"), ("Book", "Notebook"), ("Sun", "Star"), ("Rain", "Wind"), 
    ("Fire", "Water"), ("Ice", "Snow"), ("Paper", "Plastic"), ("Glass", "Plastic"), 
    ("Wood", "Metal"), ("Cotton", "Silk"), ("Leather", "Rubber"), ("Sand", "Soil"), 
    ("Brick", "Stone"), ("Broom", "Mop"), ("Dustbin", "Bucket")
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
        (5,  "⏳ **5 seconds...**"),
        (2,  "⏳ **3 seconds...**"),
        (1,  "⏳ **2 seconds...**"),
        (1,  "⏳ **1 second...**")
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
    
    imposter_failures = []
    for imp_id in game['imposter_ids']:
        if imp_id not in game['explanations']:
            p_name = clean_name(game['players'][imp_id]['name'])
            imposter_failures.append(f"⚠️ **CRITICAL: No explanation was received from a player** [{p_name}](tg://user?id={imp_id})")
    
    compiled_text = "📊 **EXPLANATION PHASE CONCLUDED!** 📊\n\n"
    if game['explanations']:
        compiled_text += "**Review the submitted statements carefully:**\n\n"
        for uid, exp_text in game['explanations'].items():
            safe_name = clean_name(game['players'][uid]['name'])
            user_tag = f"[{safe_name}](tg://user?id={uid})"
            compiled_text += f"• {user_tag} explained: \"_{exp_text}_\"\n"
    else:
        compiled_text += "**No players submitted their statements in time.**\n"
        
    if imposter_failures:
        compiled_text += "\n" + "\n".join(imposter_failures) + "\n"
        
    compiled_text += "\n🚨 **THE VOTING PHASE IS NOW OPEN!** 🚨\n\n👉 **How to cast your vote:**\n1️⃣ Reply to the suspect's message with `/vote`\n2️⃣ Type `/vote @username`\n3️⃣ Type `/vote [UserID]`"
    
    bot.send_message(chat_id, compiled_text, parse_mode="Markdown")

# ==========================================
# 🚀 CORE GAME COMMANDS
# ==========================================
@bot.message_handler(commands=['start', 'game'])
def handle_start(message):
    chat_id = message.chat.id

    if is_private(message):
        safe_name = clean_name(message.from_user.first_name)
        text = (
            "🕵️‍♂️ **SYSTEM ACCESS GRANTED** 🕵️‍♂️\n\n"
            f"Greetings, **{safe_name}**.\n\n"
            "You have entered the secure mainframe of **Gupt Shabd (The Blind Undercover)**. "
            "This bot analyzes deception, strategy, and manipulation.\n\n"
            "🧠 **Your Objective:** When added to a group, analyze the secret words, identify the liars, and amass points to dominate the global leaderboard.\n\n"
            "Use `/help` to view the comprehensive protocol manual. Good luck."
        )
        bot.send_message(chat_id, text, parse_mode="Markdown")
        return

    if chat_id not in games:
        init_game(chat_id)
        
    if games[chat_id]['state'] != 'inactive':
        bot.reply_to(message, "❌ **ACTION DENIED: A game session is already forming or running in this chat. Type `/end` to terminate it first.**", parse_mode="Markdown")
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
        "• `/daily` - Claim 50 free points daily (Executes **ONLY** in bot PM after 6:00 AM).\n\n"
        "**⚙️ UTILITIES:**\n"
        "• `/userid` - Reply to someone with this to extract their unique identifier.\n\n"
        "**🧠 REWARDS SYSTEM:**\n"
        "• Public Victory: **+10 points** to innocents.\n"
        "• Imposter Victory: **+25 points** to imposters."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['join'])
def join_game(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: You can only join a game inside a Group Chat arena.**", parse_mode="Markdown")
        return

    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'lobby':
        bot.reply_to(message, "❌ **ACTION DENIED: There is no active lobby. An administrator must type `/start` to initiate a new session.**", parse_mode="Markdown")
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username or ""

    if user_id in games[chat_id]['players']:
        bot.reply_to(message, f"⚠️ **WARNING:** {clean_name(user_name)}, you are already registered in the current lobby.", parse_mode="Markdown")
        return

    try:
        bot.send_message(user_id, "✅ **Lobby entry secured. Await further instructions in the group chat.**", parse_mode="Markdown")
        games[chat_id]['players'][user_id] = {'name': user_name, 'username': username}
        p_list = "\n".join([f"👤 [{clean_name(p['name'])}](tg://user?id={uid})" for uid, p in games[chat_id]['players'].items()])
        bot.send_message(chat_id, f"✅ **[{clean_name(user_name)}](tg://user?id={user_id}) has successfully joined! ({len(games[chat_id]['players'])}/4+)**\n\n**Registered Players:**\n{p_list}", parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException:
        bot.reply_to(message, f"❌ **ACCESS DENIED for {clean_name(user_name)}!**\n\nI am unable to send you a Private Message. You must click my profile, tap **START**, and then try `/join` again.", parse_mode="Markdown")

@bot.message_handler(commands=['startgame'])
def manual_start(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: This command is restricted to Group Chats.**", parse_mode="Markdown")
        return
        
    chat_id = message.chat.id
    if chat_id in games and games[chat_id]['state'] == 'lobby':
        if len(games[chat_id]['players']) >= 4:
            start_game_logic(chat_id)
        else:
            bot.reply_to(message, f"⚠️ **ACTION DENIED: A minimum of 4 players is required to force start the game. (Current: {len(games[chat_id]['players'])})**", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ **ACTION DENIED: There is no active lobby waiting to be started.**", parse_mode="Markdown")

def start_game_logic(chat_id):
    game = games[chat_id]
    game['state'] = 'explaining'
    
    num_players = len(game['players'])
    if num_players < 8: num_imposters = 1
    elif num_players < 12: num_imposters = 3
    elif num_players < 16: num_imposters = 5
    else: num_imposters = 5 + ((num_players - 12) // 4) * 2

    # 100% Random & Cache-Free Logic
    public_word, imposter_word = random.choice(WORD_PAIRS)
    game['public_word'], game['imposter_word'] = public_word, imposter_word
    
    player_ids = list(game['players'].keys())
    game['imposter_ids'] = random.sample(player_ids, num_imposters)
    game['explanations'], game['votes'] = {}, {}

    tags = [f"[{clean_name(p['name'])}](tg://user?id={uid})" for uid, p in game['players'].items()]
    
    bot.send_message(chat_id, f"🎮 **THE GAME HAS OFFICIALLY COMMENCED!** 🎮\n\n{', '.join(tags)}\n\n➡️ **Proceed to the bot's Private Messages (PM) and explain your secret word.**\n\n⏳ **You have exactly 1 minute and 30 seconds to submit your statement!**", parse_mode="Markdown")

    for uid in player_ids:
        try:
            if uid in game['imposter_ids']:
                assigned_word = imposter_word
            else:
                assigned_word = public_word
                
            pm_text = (
                f"🤫 **YOUR SECRET WORD:** **{assigned_word}**\n\n"
                f"➡️ **Proceed to provide your explanation here in the PM.**\n\n"
                f"⚠️ _Note: You do NOT know your identity! If your word is different from the majority, you are the Imposter. Defend your word carefully and play smart!_"
            )
            bot.send_message(uid, pm_text, parse_mode="Markdown")
        except:
            pass

    threading.Thread(target=explanation_timer, args=(chat_id,)).start()

@bot.message_handler(func=lambda m: is_private(m) and not m.text.startswith('/'))
def collect_pm_explanations(message):
    user_id = message.from_user.id
    for chat_id, game in games.items():
        if game['state'] == 'explaining' and user_id in game['players']:
            if user_id not in game['explanations']:
                game['explanations'][user_id] = message.text
                bot.reply_to(message, "✅ **Your explanation has been securely encrypted and recorded. Return to the group.**", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ **ACTION FAILED: You have already submitted a statement for this round.**", parse_mode="Markdown")
            return
    bot.reply_to(message, "❌ **ERROR: I only accept text statements when an active game is in the 'Explanation Phase'.**", parse_mode="Markdown")

@bot.message_handler(commands=['vote'])
def process_vote_command(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: Voting protocols can only be executed within the Group Chat arena.**", parse_mode="Markdown")
        return

    chat_id = message.chat.id
    if chat_id not in games or games[chat_id]['state'] != 'voting':
        bot.reply_to(message, "❌ **ACTION DENIED: The voting phase is currently closed or no active game exists.**", parse_mode="Markdown")
        return
        
    game, voter_id = games[chat_id], message.from_user.id
    
    if voter_id not in game['players']:
        bot.reply_to(message, "🚫 **AUTHORIZATION FAILED: You are not a registered participant in this session.**", parse_mode="Markdown")
        return
    if voter_id in game['votes']:
        bot.reply_to(message, "⚠️ **ACTION FAILED: You have already cast your binding vote.**", parse_mode="Markdown")
        return

    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()
        if len(args) > 1:
            arg = args[1]
            if arg.isdigit(): target_id = int(arg)
            elif arg.startswith('@'):
                target_username = arg.replace('@', '').strip().lower()
                for uid, p in game['players'].items():
                    if p['username'].lower() == target_username:
                        target_id = uid
                        break

    if not target_id or target_id not in game['players']:
        bot.reply_to(message, "❌ **INVALID TARGET:** Please cast your vote by replying to a user, tagging them, or entering their User ID.", parse_mode="Markdown")
        return

    game['votes'][voter_id] = target_id
    safe_target_name = clean_name(game['players'][target_id]['name'])
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
        user_tag = f"[{safe_name}](tg://user?id={uid})"
        results += f"• {user_tag}: {count} votes\n"
        
    results += f"\n🍏 **Public Word:** **{game['public_word']}**\n🥭 **Imposter Word:** **{game['imposter_word']}**\n\n"

    if len(highest_voted_players) > 1:
        results += "👔 **STALEMATE! The group failed to reach a consensus.**\n🏆 **THE IMPOSTERS ESCAPE AND SECURE THE VICTORY!**\n\n🏅 **Points Rewarded:**\n"
        for imp_id in game['imposter_ids']:
            safe_imp_name = clean_name(game['players'][imp_id]['name'])
            add_points(imp_id, safe_imp_name, 25)
            imp_tag = f"[{safe_imp_name}](tg://user?id={imp_id})"
            results += f"• {imp_tag} (Imposter): **+25 points**\n"
    elif highest_voted_players[0] in game['imposter_ids']:
        caught_id = highest_voted_players[0]
        safe_caught_name = clean_name(game['players'][caught_id]['name'])
        caught_tag = f"[{safe_caught_name}](tg://user?id={caught_id})"
        results += f"🎯 **EXECUTION SUCCESSFUL! {caught_tag} was indeed a liar!**\n🏆 **THE PUBLIC WINS!**\n\n🏅 **Points Rewarded:**\n"
        for uid in game['players'].keys():
            if uid not in game['imposter_ids']:
                safe_norm_name = clean_name(game['players'][uid]['name'])
                add_points(uid, safe_norm_name, 10)
                norm_tag = f"[{safe_norm_name}](tg://user?id={uid})"
                results += f"• {norm_tag}: **+10 points**\n"
    else:
        wrong_id = highest_voted_players[0]
        safe_wrong_name = clean_name(game['players'][wrong_id]['name'])
        wrong_tag = f"[{safe_wrong_name}](tg://user?id={wrong_id})"
        results += f"❌ **CATASTROPHIC FAILURE! You executed {wrong_tag}, an innocent player!**\n🏆 **THE IMPOSTERS WIN THE GAME!**\n\n🏅 **Points Rewarded:**\n"
        for imp_id in game['imposter_ids']:
            safe_imp_name = clean_name(game['players'][imp_id]['name'])
            add_points(imp_id, safe_imp_name, 25)
            imp_tag = f"[{safe_imp_name}](tg://user?id={imp_id})"
            results += f"• {imp_tag} (Imposter): **+25 points**\n"

    bot.send_message(chat_id, results, parse_mode="Markdown")
    game['state'] = 'inactive'

# --- SECURE END COMMAND ---
@bot.message_handler(commands=['end'])
def end_game(message):
    if not is_group(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: The `/end` command is restricted to Group Chats.**", parse_mode="Markdown")
        return
        
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in games or games[chat_id]['state'] == 'inactive':
        bot.reply_to(message, "⚠️ **ACTION FAILED: No active game session is currently running in this group.**", parse_mode="Markdown")
        return
        
    is_initiator = (user_id == games[chat_id].get('initiator_id'))
    
    is_admin = False
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            is_admin = True
    except:
        pass 
        
    if not (is_initiator or is_admin):
        bot.reply_to(message, "❌ **ACCESS DENIED: Unauthorized execution.**\n\nOnly **Group Administrators** or the **user who initiated the game** are permitted to use the `/end` command.", parse_mode="Markdown")
        return

    games[chat_id]['state'] = 'inactive'
    bot.reply_to(message, "🛑 **ADMINISTRATIVE OVERRIDE: The active game session has been forcefully terminated.**", parse_mode="Markdown")

# ==========================================
# 💰 ECONOMY & UTILITY COMMANDS
# ==========================================
@bot.message_handler(commands=['score'])
def check_score(message):
    pts = get_points(message.from_user.id)
    safe_name = clean_name(message.from_user.first_name)
    bot.reply_to(message, f"🥇 **[{safe_name}](tg://user?id={message.from_user.id}), your current verifiable balance is:** `{pts} points`", parse_mode="Markdown")

def build_leaderboard():
    rows = get_top_players()
    text = "🏆 **GLOBAL TOP 10 LEADERBOARD** 🏆\n\n"
    if not rows: text += "_The database is currently empty. Start playing to rank up!_"
    for idx, (uid, name, pts) in enumerate(rows):
        display_name = clean_name(name) if name else "Player"
        text += f"**{idx + 1}.** [{display_name}](tg://user?id={uid}) ➡️ **{pts} points**\n"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Refresh Standings", callback_data="refresh_leaderboard"))
    return text, markup

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

@bot.message_handler(commands=['daily'])
def claim_daily(message):
    if not is_private(message):
        bot.reply_to(message, "❌ **COMMAND DENIED: Security protocol requires `/daily` to be executed exclusively in Private Messages (PM).**", parse_mode="Markdown")
        return
        
    user_id = str(message.from_user.id)
    user_name = clean_name(message.from_user.first_name)
    
    user = users_collection.find_one({"_id": user_id})
    row_claim = user.get("daily_claim") if user else None
    
    now = datetime.now()
    current_cycle = now.replace(hour=6, minute=0, second=0, microsecond=0) if now.hour >= 6 else (now - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    
    can_claim = False
    if not row_claim:
        can_claim = True
    else:
        last_claim = datetime.fromisoformat(row_claim)
        if last_claim < current_cycle: can_claim = True
            
    if can_claim:
        users_collection.update_one(
            {"_id": user_id},
            {"$inc": {"points": 50}, "$set": {"name": user_name, "daily_claim": now.isoformat()}},
            upsert=True
        )
        bot.reply_to(message, "🎁 **DAILY BONUS AUTHORIZED!** 🎁\n\n💰 **+50 points** have been securely deposited into your account.\n⏳ _Return tomorrow after 6:00 AM IST for your next claim._", parse_mode="Markdown")
    else:
        next_claim = current_cycle + timedelta(days=1)
        time_left = next_claim - now
        h, rem = divmod(time_left.seconds, 3600)
        m, _ = divmod(rem, 60)
        bot.reply_to(message, f"❌ **ACCESS DENIED: You have already exhausted your daily claim quota for this cycle.**\n\n⏰ _Refresh available in:_ **{h}h {m}m** (Strictly after 6:00 AM)", parse_mode="Markdown")

@bot.message_handler(commands=['userid'])
def get_user_id(message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = clean_name(message.reply_to_message.from_user.first_name)
        bot.reply_to(message, f"👤 **Target:** [{target_name}](tg://user?id={target_id})\n🆔 **Unique ID:** `{target_id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ **INSTRUCTION:** Please reply to a specific user's message with `/userid` to extract their unique identifier.", parse_mode="Markdown")

# ==========================================
# 🌐 DUMMY WEB SERVER FOR RENDER
# ==========================================
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

print("🚀 Ultimate Gupt Shabd Bot is running...")
bot.infinity_polling()

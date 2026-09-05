import asyncio
import json
import os
import random
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ==================================================
# 1. কনফিগারেশন (আপনার তথ্য দেওয়া আছে)
# ==================================================
BOT_TOKEN = "8886694697:AAHx9SOP4X74UNUzb0Q_gRDIuhE6ebXahH4"
GROUP_CHAT_ID = -1003989081696
ADMIN_ID = 2089060393

CONFIG_FILE = "config.json"

# ==================================================
# 2. ডিফল্ট কনফিগ (৪টি সার্ভিস ও ৪টি দেশ)
# ==================================================
DEFAULT_CONFIG = {
    "is_active": True,
    "interval": 3,
    "services": [
        {"name": "Facebook", "active": True},
        {"name": "Instagram", "active": True},
        {"name": "WhatsApp", "active": True},
        {"name": "Telegram", "active": True},
    ],
    "countries": [
        {"code": "+880", "flag": "🇧🇩", "short": "BD", "length": 10, "active": True},
        {"code": "+91", "flag": "🇮🇳", "short": "IN", "length": 10, "active": True},
        {"code": "+95", "flag": "🇲🇲", "short": "MM", "length": 9, "active": True},
        {"code": "+1", "flag": "🇺🇸", "short": "US", "length": 10, "active": True},
    ]
}

# ==================================================
# 3. কনফিগ ফাংশন
# ==================================================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================================================
# 4. মেসেজ জেনারেটর (ঠিক ফরম্যাটে)
# ==================================================
def generate_random_phone(countries):
    active_countries = [c for c in countries if c.get("active", True)]
    if not active_countries:
        active_countries = countries
    country = random.choice(active_countries)
    number = ''.join(str(random.randint(0, 9)) for _ in range(country["length"]))
    if len(number) > 6:
        masked = number[:2] + "xxxx" + number[-4:]
    else:
        masked = number
    return {
        "full": f"{country['code']}{number}",
        "masked": masked,
        "flag": country["flag"],
        "short": country["short"],
        "code": country["code"],
    }

def generate_random_code():
    length = random.choice([4, 5, 6])
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def generate_fake_message(services, countries):
    active_services = [s["name"] for s in services if s.get("active", True)]
    if not active_services:
        active_services = [s["name"] for s in services]
    phone = generate_random_phone(countries)
    service = random.choice(active_services)
    en_tag = "#EN" if random.random() > 0.2 else ""
    dash = "━━━━━━━━━━━━━━━━━━"
    full_number = f"{phone['code']}{phone['masked']}"
    line = f"{phone['flag']} {phone['short']} {service} {full_number}"
    if en_tag:
        line += f" {en_tag}"
    return f"{dash}\n{line}\n{dash}"

# ==================================================
# 5. মেসেজ পাঠানোর ফাংশন (এখানে রঙ ঠিক করা হয়েছে)
# ==================================================
async def send_otp_message(bot, config):
    try:
        text = generate_fake_message(config["services"], config["countries"])
        code = generate_random_code()
        
        # ১ম বাটন: সবুজ (success), নিচের দুটি: নীল (primary)
        keyboard = [
            [InlineKeyboardButton(f"📋 {code}", callback_data="otp_code", style="success")],
            [InlineKeyboardButton("🤖 Number Bot", url="https://t.me/TrustOTP_Official_bot", style="primary")],
            [InlineKeyboardButton("💥 Main Channel", url="https://t.me/trustotpmethod", style="primary")]
        ]
        
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

async def auto_send(bot):
    while True:
        config = load_config()
        if config["is_active"]:
            await send_otp_message(bot, config)
        await asyncio.sleep(config["interval"])

def is_admin(user_id):
    return user_id == ADMIN_ID

# ==================================================
# 6. অ্যাডমিন মেনু
# ==================================================
async def admin_menu(update_or_query, context, edit=False):
    config = load_config()
    status = "🟢 চালু" if config["is_active"] else "🔴 বন্ধ"
    text = (
        f"🛠️ **অ্যাডমিন কন্ট্রোল প্যানেল**\n\n"
        f"📌 অবস্থা: {status}\n"
        f"⏱️ ইন্টারভাল: {config['interval']} সেকেন্ড\n"
        f"📱 সেবা: {len(config['services'])}টি\n"
        f"🌍 দেশ: {len(config['countries'])}টি\n\n"
        "নিচের বাটন থেকে পরিচালনা করুন:"
    )
    keyboard = [
        [InlineKeyboardButton(f"{'⏸️ বন্ধ' if config['is_active'] else '▶️ চালু'}", callback_data="toggle_active")],
        [InlineKeyboardButton(f"⏱️ ইন্টারভাল: {config['interval']}সেকেন্ড", callback_data="change_interval")],
        [InlineKeyboardButton(f"📱 সেবা ({len(config['services'])})", callback_data="manage_services")],
        [InlineKeyboardButton(f"🌍 দেশ ({len(config['countries'])})", callback_data="manage_countries")],
        [InlineKeyboardButton("📊 স্ট্যাটাস দেখুন", callback_data="show_status")],
        [InlineKeyboardButton("📨 ম্যানুয়াল মেসেজ পাঠান", callback_data="send_manual")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if edit:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==================================================
# 7. সার্ভিস ম্যানেজমেন্ট
# ==================================================
async def manage_services(update_or_query, edit=False):
    config = load_config()
    services = config["services"]
    text = "📱 **সেবা লিস্ট**\n\n"
    for i, s in enumerate(services, 1):
        status = "🟢" if s.get("active", True) else "🔴"
        text += f"{i}. {status} {s['name']}\n"
    text += f"\nমোট: {len(services)}টি\n\nনিচের বাটন দিয়ে পরিচালনা করুন:"
    
    keyboard = []
    row = []
    for i, s in enumerate(services):
        label = f"{'🟢' if s.get('active', True) else '🔴'} {s['name'][:8]}"
        row.append(InlineKeyboardButton(label, callback_data=f"tog_srv_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    row2 = []
    for i, s in enumerate(services):
        row2.append(InlineKeyboardButton(f"❌ {i+1}", callback_data=f"del_srv_{i}"))
        if len(row2) == 4:
            keyboard.append(row2)
            row2 = []
    if row2:
        keyboard.append(row2)
    
    keyboard.append([InlineKeyboardButton("➕ নতুন সেবা যোগ", callback_data="add_service_btn")])
    keyboard.append([InlineKeyboardButton("🔙 মেনুতে ফিরুন", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if edit:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==================================================
# 8. কান্ট্রি ম্যানেজমেন্ট
# ==================================================
async def manage_countries(update_or_query, edit=False):
    config = load_config()
    countries = config["countries"]
    text = "🌍 **কান্ট্রি লিস্ট**\n\n"
    for i, c in enumerate(countries, 1):
        status = "🟢" if c.get("active", True) else "🔴"
        text += f"{i}. {status} {c['flag']} {c['short']} ({c['code']}) লেংথ:{c['length']}\n"
    text += f"\nমোট: {len(countries)}টি\n\nনিচের বাটন দিয়ে পরিচালনা করুন:"
    
    keyboard = []
    row = []
    for i, c in enumerate(countries):
        label = f"{'🟢' if c.get('active', True) else '🔴'} {c['flag']}{c['short']}"
        row.append(InlineKeyboardButton(label, callback_data=f"tog_cty_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    row2 = []
    for i, c in enumerate(countries):
        row2.append(InlineKeyboardButton(f"❌ {c['short']}", callback_data=f"del_cty_{i}"))
        if len(row2) == 3:
            keyboard.append(row2)
            row2 = []
    if row2:
        keyboard.append(row2)
    
    keyboard.append([InlineKeyboardButton("➕ নতুন দেশ যোগ", callback_data="add_country_btn")])
    keyboard.append([InlineKeyboardButton("🔙 মেনুতে ফিরুন", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if edit:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==================================================
# 9. কলব্যাক হ্যান্ডলার
# ==================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ অনুমতি নেই!", show_alert=True)
        return
    
    await query.answer()
    data = query.data
    config = load_config()

    if data == "back_to_menu":
        await admin_menu(query, context, edit=True)
        return

    if data == "toggle_active":
        config["is_active"] = not config["is_active"]
        save_config(config)
        await admin_menu(query, context, edit=True)
        return

    if data == "change_interval":
        keyboard = [
            [InlineKeyboardButton("1 সেকেন্ড", callback_data="set_int_1"),
             InlineKeyboardButton("2 সেকেন্ড", callback_data="set_int_2")],
            [InlineKeyboardButton("3 সেকেন্ড", callback_data="set_int_3"),
             InlineKeyboardButton("5 সেকেন্ড", callback_data="set_int_5")],
            [InlineKeyboardButton("10 সেকেন্ড", callback_data="set_int_10"),
             InlineKeyboardButton("15 সেকেন্ড", callback_data="set_int_15")],
            [InlineKeyboardButton("30 সেকেন্ড", callback_data="set_int_30"),
             InlineKeyboardButton("60 সেকেন্ড", callback_data="set_int_60")],
            [InlineKeyboardButton("🔙 ফিরুন", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            f"⏱️ **ইন্টারভাল সেট করুন**\nবর্তমান: {config['interval']} সেকেন্ড",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    if data.startswith("set_int_"):
        sec = int(data.split("_")[2])
        config["interval"] = sec
        save_config(config)
        await admin_menu(query, context, edit=True)
        return

    if data == "manage_services":
        await manage_services(query, edit=True)
        return

    if data.startswith("tog_srv_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(config["services"]):
            config["services"][idx]["active"] = not config["services"][idx].get("active", True)
            save_config(config)
            await manage_services(query, edit=True)
        return

    if data.startswith("del_srv_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(config["services"]):
            removed = config["services"].pop(idx)
            save_config(config)
            await query.answer(f"✅ {removed['name']} মুছে ফেলা হয়েছে")
            await manage_services(query, edit=True)
        return

    if data == "add_service_btn":
        context.user_data["waiting_for"] = "add_service"
        await query.edit_message_text(
            "📝 এখন আপনার মেসেজ হিসেবে নতুন সেবার নাম লিখুন।\n"
            "উদাহরণ: `WhatsApp`\n\n"
            "❌ বাতিল করতে /cancel লিখুন।",
            parse_mode="Markdown"
        )
        return

    if data == "manage_countries":
        await manage_countries(query, edit=True)
        return

    if data.startswith("tog_cty_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(config["countries"]):
            config["countries"][idx]["active"] = not config["countries"][idx].get("active", True)
            save_config(config)
            await manage_countries(query, edit=True)
        return

    if data.startswith("del_cty_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(config["countries"]):
            removed = config["countries"].pop(idx)
            save_config(config)
            await query.answer(f"✅ {removed['flag']} {removed['short']} মুছে ফেলা হয়েছে")
            await manage_countries(query, edit=True)
        return

    if data == "add_country_btn":
        context.user_data["waiting_for"] = "add_country"
        await query.edit_message_text(
            "📝 এখন মেসেজ হিসেবে নতুন দেশের ডেটা লিখুন।\n"
            "ফরম্যাট: `ফ্ল্যাগ কোড শর্ট লেংথ`\n"
            "উদাহরণ: `🇲🇲 +95 MM 9`\n\n"
            "❌ বাতিল করতে /cancel লিখুন।",
            parse_mode="Markdown"
        )
        return

    if data == "show_status":
        status = "🟢 চালু" if config["is_active"] else "🔴 বন্ধ"
        active_services = sum(1 for s in config["services"] if s.get("active", True))
        active_countries = sum(1 for c in config["countries"] if c.get("active", True))
        text = (
            f"📊 **বর্তমান স্ট্যাটাস**\n\n"
            f"📌 অবস্থা: {status}\n"
            f"⏱️ ইন্টারভাল: {config['interval']} সেকেন্ড\n"
            f"📱 সেবা: {len(config['services'])}টি (সক্রিয়: {active_services})\n"
            f"🌍 দেশ: {len(config['countries'])}টি (সক্রিয়: {active_countries})\n"
            f"👤 অ্যাডমিন: {ADMIN_ID}\n"
            f"📋 গ্রুপ: {GROUP_CHAT_ID}\n"
            f"⏰ সময়: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরুন", callback_data="back_to_menu")]]),
            parse_mode="Markdown"
        )
        return

    if data == "send_manual":
        success = await send_otp_message(context.bot, config)
        msg = "✅ মেসেজ পাঠানো হয়েছে!" if success else "❌ ব্যর্থ!"
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ফিরুন", callback_data="back_to_menu")]])
        )
        return

    if data == "otp_code":
        await query.answer("✅ OTP Code", show_alert=False)

# ==================================================
# 10. মেসেজ হ্যান্ডলার (ইনপুট নেওয়ার জন্য)
# ==================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if "waiting_for" not in context.user_data:
        return

    action = context.user_data["waiting_for"]
    text = update.message.text.strip()

    if text.lower() == "/cancel":
        context.user_data.pop("waiting_for", None)
        await update.message.reply_text("❌ বাতিল করা হয়েছে।")
        return

    config = load_config()

    if action == "add_service":
        if any(s["name"] == text for s in config["services"]):
            await update.message.reply_text(f"⚠️ '{text}' ইতিমধ্যে আছে!")
            return
        config["services"].append({"name": text, "active": True})
        save_config(config)
        context.user_data.pop("waiting_for")
        await update.message.reply_text(f"✅ '{text}' যোগ করা হয়েছে!\nমোট সেবা: {len(config['services'])}টি")
        await manage_services(update, edit=False)

    elif action == "add_country":
        parts = text.split()
        if len(parts) != 4:
            await update.message.reply_text("❌ ভুল ফরম্যাট! উদাহরণ: `🇲🇲 +95 MM 9`")
            return
        flag, code, short, length_str = parts
        try:
            length = int(length_str)
        except ValueError:
            await update.message.reply_text("❌ লেংথ অবশ্যই সংখ্যা হতে হবে!")
            return
        for c in config["countries"]:
            if c["short"] == short:
                await update.message.reply_text(f"⚠️ '{short}' ইতিমধ্যে আছে!")
                return
        config["countries"].append({
            "flag": flag,
            "code": code,
            "short": short,
            "length": length,
            "active": True
        })
        save_config(config)
        context.user_data.pop("waiting_for")
        await update.message.reply_text(f"✅ {flag} {short} যোগ করা হয়েছে!\nমোট দেশ: {len(config['countries'])}টি")
        await manage_countries(update, edit=False)

# ==================================================
# 11. কমান্ড হ্যান্ডলার
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await admin_menu(update, context)
    else:
        await update.message.reply_text(
            "🤖 **Trust OTP Bot**\n\n"
            "এই গ্রুপে OTP মেসেজ পাঠানোর জন্য বট চলছে।\n"
            "অ্যাডমিন প্যানেল ব্যবহার করতে /admin লিখুন।",
            parse_mode="Markdown"
        )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_menu(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "waiting_for" in context.user_data:
        context.user_data.pop("waiting_for")
        await update.message.reply_text("❌ বাতিল করা হয়েছে।")
    else:
        await update.message.reply_text("কোনো কার্যক্রম চলছে না।")

# ==================================================
# 12. মেইন ফাংশন
# ==================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def start_auto(app):
        asyncio.create_task(auto_send(app.bot))
        logger.info("🚀 অটো-সেন্ডার চালু হয়েছে")

    app.post_init = start_auto

    print("=" * 50)
    print("🤖 Trust OTP Bot চলছে...")
    print(f"👤 অ্যাডমিন আইডি: {ADMIN_ID}")
    print(f"📱 গ্রুপ আইডি: {GROUP_CHAT_ID}")
    print(f"⏱️ ইন্টারভাল: {load_config()['interval']} সেকেন্ড")
    print("📌 বন্ধ করতে Ctrl+C চাপুন")
    print("=" * 50)

    app.run_polling()

if __name__ == "__main__":
    main()
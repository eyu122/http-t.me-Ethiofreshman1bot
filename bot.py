import sys
sys.path.insert(0, '/home/Max7676/.local/lib/python3.10/site-packages')

import os
import hmac
import hashlib
import time
import logging
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = "8512645298:AAGAQhbbCXNVsN8JHvoXkoahtVb2gBE9q-c"
OWNER_ID = 5089821980
BASE_URL = "https://max7676.pythonanywhere.com"
SECRET_KEY = "my-super-secret-key-1234"
FILES_DIR = "/home/Max7676/htmlbot/files"

flask_app = Flask(__name__)

def generate_token(filepath, expires_in=3600):
    expire_time = int(time.time()) + expires_in
    message = f"{filepath}:{expire_time}"
    sig = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{expire_time}:{sig}"

def verify_token(filepath, token):
    try:
        expire_time, sig = token.split(":", 1)
        if int(expire_time) < time.time():
            return False
        message = f"{filepath}:{expire_time}"
        expected = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
    except:
        return False

def get_view_url(category, filename):
    filepath = f"{category}/{filename}"
    token = generate_token(filepath)
    return f"{BASE_URL}/view/{category}/{filename}?token={token}"

def get_categories():
    os.makedirs(FILES_DIR, exist_ok=True)
    return [d for d in os.listdir(FILES_DIR)
            if os.path.isdir(os.path.join(FILES_DIR, d))]

def get_files_in_category(category):
    cat_path = os.path.join(FILES_DIR, category)
    if not os.path.exists(cat_path):
        return []
    return [f for f in os.listdir(cat_path) if f.endswith(".html")]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    if not categories:
        await update.message.reply_text(
            "No categories available yet. Check back soon!"
        )
        return
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat:{cat}")]
        for cat in categories
    ]
    await update.message.reply_text(
        "📂 Welcome! Please choose a category:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split(":", 1)[1]
    files = get_files_in_category(category)
    if not files:
        await query.edit_message_text("No files in this category yet.")
        return
    keyboard = [
        [InlineKeyboardButton(f[:-5], callback_data=f"file:{category}:{f}")]
        for f in files
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
    await query.edit_message_text(
        f"📁 *{category}* — choose a file:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, category, filename = query.data.split(":", 2)
    url = get_view_url(category, filename)
    keyboard = [[InlineKeyboardButton("🌐 Open File", url=url)]]
    await query.edit_message_text(
        f"📄 *{filename[:-5]}*\n\nTap the button below to open.\n"
        f"⏱ Link expires in 1 hour.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categories = get_categories()
    if not categories:
        await query.edit_message_text("No categories available yet.")
        return
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat:{cat}")]
        for cat in categories
    ]
    await query.edit_message_text(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /upload categoryname\nExample: /upload science"
        )
        return
    category = context.args[0]
    context.user_data["upload_category"] = category
    await update.message.reply_text(
        f"✅ Ready! Now send me the HTML file for category: *{category}*",
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    category = context.user_data.get("upload_category")
    if not category:
        await update.message.reply_text(
            "Please use /upload categoryname first."
        )
        return
    doc = update.message.document
    if not doc.file_name.endswith(".html"):
        await update.message.reply_text("❌ Only .html files are accepted.")
        return
    cat_path = os.path.join(FILES_DIR, category)
    os.makedirs(cat_path, exist_ok=True)
    file = await doc.get_file()
    save_path = os.path.join(cat_path, doc.file_name)
    await file.download_to_drive(save_path)
    context.user_data.pop("upload_category", None)
    await update.message.reply_text(
        f"✅ *{doc.file_name}* saved to *{category}* category!",
        parse_mode="Markdown"
    )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized.")
        return
    categories = get_categories()
    if not categories:
        await update.message.reply_text("No files uploaded yet.")
        return
    msg = "📋 *All Files:*\n\n"
    for cat in categories:
        files = get_files_in_category(cat)
        msg += f"📁 *{cat}*\n"
        msg += "\n".join(f"  • {f}" for f in files)
        msg += "\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized.")
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /delete categoryname filename.html"
        )
        return
    category, filename = context.args[0], context.args[1]
    file_path = os.path.join(FILES_DIR, category, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        await update.message.reply_text(
            f"🗑 Deleted *{filename}* from *{category}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ File not found.")

@flask_app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(handle_category, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(handle_file, pattern="^file:"))
    app.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    async with app:
        update = Update.de_json(request.get_json(), app.bot)
        await app.process_update(update)
    return Response("OK", status=200)

@flask_app.route("/view/<category>/<filename>")
def view_file(category, filename):
    token = request.args.get("token", "")
    filepath = f"{category}/{filename}"
    if not verify_token(filepath, token):
        return "Link expired or invalid", 403
    full_path = os.path.join(FILES_DIR, category, filename)
    if not os.path.exists(full_path):
        return "File not found", 404
    with open(full_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    safe_content = html_content.replace('"', '&quot;')
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Viewer</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #1a1a1a; }}
    iframe {{ width: 100vw; height: 100vh; border: none; display: block; }}
  </style>
  <script>
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('keydown', e => {{
      if ((e.ctrlKey || e.metaKey) && ['s','u','p'].includes(e.key.toLowerCase()))
        e.preventDefault();
    }});
  </script>
</head>
<body>
  <iframe srcdoc="{safe_content}" sandbox="allow-scripts allow-same-origin"></iframe>
</body>
</html>"""

@flask_app.route("/")
def index():
    return "Bot is running! ✅"

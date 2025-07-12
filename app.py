import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# Initialize Flask app
app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token from environment variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = Bot(token=TOKEN)

# Store bot data (for demonstration, use database in production)
bot_data = {
    'users': {},
    'stats': {'messages_processed': 0}
}

# ----- Bot Command Handlers -----
def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when /start is issued"""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\! I'm your Telegram bot\. '
        'Send /help to see what I can do\.'
    )
    
    # Track user
    bot_data['users'][user.id] = {
        'first_name': user.first_name,
        'last_contact': update.message.date
    }

def help_command(update: Update, context: CallbackContext) -> None:
    """Send help message when /help is issued"""
    help_text = """
Available commands:
/start - Start interacting with the bot
/help - Show this help message
/stats - Show bot statistics
/echo <text> - Echo back your text
"""
    update.message.reply_text(help_text)

def stats(update: Update, context: CallbackContext) -> None:
    """Show bot statistics"""
    stats_text = (
        f"Users: {len(bot_data['users']}\n"
        f"Messages processed: {bot_data['stats']['messages_processed']}"
    )
    update.message.reply_text(stats_text)

def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message"""
    text = ' '.join(context.args)
    if not text:
        update.message.reply_text("Please provide text to echo after /echo command")
        return
    
    update.message.reply_text(f"Echo: {text}")
    bot_data['stats']['messages_processed'] += 1

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle all non-command messages"""
    user_text = update.message.text
    update.message.reply_text(f"You said: {user_text}")
    bot_data['stats']['messages_processed'] += 1

# ----- Flask Routes -----
@app.route('/')
def index():
    return "Telegram bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via webhook"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

# ----- Initialization -----
def setup_dispatcher():
    """Set up command handlers"""
    dp = Dispatcher(bot, None, workers=0)
    
    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("echo", echo))
    
    # Message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    return dp

def set_webhook():
    """Set Telegram webhook"""
    webhook_url = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/webhook"
    bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

# Initialize dispatcher
dispatcher = setup_dispatcher()

# Set webhook when starting (only in production)
if os.environ.get('ENV') == 'production':
    set_webhook()

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

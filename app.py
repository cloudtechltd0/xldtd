import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def split_message(text: str, max_length: int = 4000):
    """Splits text into chunks, prioritizing newlines to avoid cutting words or Markdown."""
    chunks = []
    while len(text) > max_length:
        # Find the last newline within the allowed length limit
        split_idx = text.rfind('\n', 0, max_length)
        # If no newline found, just split at the max length limit
        if split_idx == -1:
            split_idx = max_length
        chunks.append(text[:split_idx])
        text = text[split_idx:]
    chunks.append(text)
    return chunks

# Async Telegram message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text

    # Show "typing..." status to the user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Using the official asynchronous generation method to prevent blocking the event loop
        response = await model.generate_content_async(user_text)
        reply = response.text
    except Exception as e:
        reply = f"Sorry, I encountered an error: {str(e)}"

    # Send response safely handling Telegram's 4096 character limit
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        chunks = split_message(reply)
        for chunk in chunks:
            if chunk.strip():  # Avoid sending empty whitespace messages
                await update.message.reply_text(chunk)

def main():
    # Verify environment variables are present before starting
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        print("Error: Missing TELEGRAM_BOT_TOKEN or GEMINI_API_KEY in environment.")
        return

    # Build the Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register the text message handler (ignoring bot commands like /start)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
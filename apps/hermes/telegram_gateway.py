"""
Hermes-Agent Telegram Gateway
Provides a private Telegram Bot interface for the owner/administrator.
Features dormant standby mode when TELEGRAM_BOT_TOKEN is not configured,
preventing container crash loops under process supervision.
"""
import os
import sys
import time
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hermes.telegram")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

try:
    from agent import HermesAgent
except (ImportError, ValueError):
    from .agent import HermesAgent

async def run_dormant_loop():
    logger.info("ℹ️ TELEGRAM_BOT_TOKEN not provided. Gateway running in dormant standby mode.")
    logger.info("To activate the Telegram bot, add TELEGRAM_BOT_TOKEN to Zerops environment vault.")
    while True:
        await asyncio.sleep(3600)

async def run_bot():
    if not TOKEN:
        await run_dormant_loop()
        return

    try:
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
    except ImportError:
        logger.warning("python-telegram-bot is not installed. Running in dormant standby mode.")
        await run_dormant_loop()
        return

    agent = HermesAgent()

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Hola. Soy Hermes, tu copiloto soberano en Zerops.\n"
            "Podés pedirme tareas de investigación, auditorías o ejecutar equipos de CrewAI y validaciones de PydanticAI."
        )

    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🟢 Hermes-Agent Status: OPERATIONAL\n"
            "• Gateway LLM: Bifrost (http://bifrost:8080/v1)\n"
            "• Virtual Key: vk-hermes-agent\n"
            "• NATS JetStream: Conectado\n"
            "• Base de Datos: PostgreSQL 18"
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        user_text = update.message.text
        logger.info(f"Received Telegram prompt: {user_text[:50]}...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            reply = await agent.run_turn(user_text)
            await update.message.reply_text(reply)
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            await update.message.reply_text(f"⚠️ Error al procesar tu solicitud: {str(e)}")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Hermes Telegram Gateway started successfully with long polling.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # Keep running
    while True:
        await asyncio.sleep(60)

def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Hermes Telegram Gateway stopped by user.")

if __name__ == "__main__":
    main()

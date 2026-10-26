"""
Hermes-Agent Telegram Gateway
Provides a private Telegram Bot interface for the owner/administrator.
Features dormant standby mode when TELEGRAM_BOT_TOKEN is not configured,
Zero-Trust whitelist security, continuous keep_typing feedback,
and resilient multi-tier message chunking.
"""
import os
import re
import sys
import time
import asyncio
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hermes.telegram")

ADMIN_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CLIENT_TOKEN = os.getenv("TELEGRAM_CLIENT_BOT_TOKEN", "").strip()

ADMIN_ALLOWED_USERS_RAW = os.getenv("TELEGRAM_ADMIN_ALLOWED_USERS") or os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
ADMIN_ALLOWED_USERS = {
    int(x.strip())
    for x in ADMIN_ALLOWED_USERS_RAW.split(",")
    if x.strip() and x.strip().lstrip("-").isdigit()
}

CLIENT_ALLOWED_USERS_RAW = os.getenv("TELEGRAM_CLIENT_ALLOWED_USERS", "").strip()
CLIENT_ALLOWED_USERS = {
    int(x.strip())
    for x in CLIENT_ALLOWED_USERS_RAW.split(",")
    if x.strip() and x.strip().lstrip("-").isdigit()
}

try:
    from agent import HermesAgent
except (ImportError, ValueError):
    from .agent import HermesAgent

async def run_dormant_loop():
    logger.info("ℹ️ No TELEGRAM_BOT_TOKEN provided. Gateway running in dormant standby mode.")
    logger.info("To activate the Telegram bot, add TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_BOT_TOKEN in Zerops.")
    while True:
        await asyncio.sleep(3600)

@asynccontextmanager
async def keep_typing(bot, chat_id: int, interval: float = 4.0):
    """
    Maintains continuous 'typing...' feedback in Telegram for long-running operations.
    Cancels cleanly upon exit.
    """
    stop_event = asyncio.Event()

    async def _loop():
        while not stop_event.is_set():
            try:
                await bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception:
                pass
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    task = asyncio.create_task(_loop())
    try:
        yield
    finally:
        stop_event.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

async def send_split_message(update, text: str, max_chunk_size: int = 3900, parse_mode: str = "Markdown"):
    """
    Splits long responses (>4096 chars) into balanced Markdown chunks
    preserving codeblock closures (```) and provides a resilient multi-tier
    fallback to plain text if Telegram Markdown parsing fails.
    """
    if not text:
        return

    chunks = []
    lines = text.splitlines(keepends=True)
    current_chunk = []
    current_len = 0
    in_code_block = False
    current_lang = ""

    code_fence_pattern = re.compile(r"^```(\w*)")

    for line in lines:
        fence_match = code_fence_pattern.match(line.strip())
        needed_margin = 10 if in_code_block else 0

        if current_len + len(line) + needed_margin > max_chunk_size:
            if current_chunk:
                if in_code_block:
                    current_chunk.append("\n```")
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_len = 0
                if in_code_block:
                    current_chunk.append(f"```{current_lang}\n")
                    current_len = len(current_chunk[0])

            while len(line) > max_chunk_size:
                chunks.append(line[:max_chunk_size])
                line = line[max_chunk_size:]

        current_chunk.append(line)
        current_len += len(line)

        if fence_match:
            if not in_code_block:
                in_code_block = True
                current_lang = fence_match.group(1)
            else:
                in_code_block = False
                current_lang = ""

    if current_chunk:
        if in_code_block:
            current_chunk.append("\n```")
        chunks.append("".join(current_chunk))

    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception as parse_err:
            logger.warning(f"Formatting error with {parse_mode} ({parse_err}). Falling back to plain text.")
            await update.message.reply_text(chunk, parse_mode=None)
        if len(chunks) > 1:
            await asyncio.sleep(0.3)

def build_bot_app(token: str, role: str, allowed_users: set, bifrost_key: str):
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        TypeHandler,
        ApplicationHandlerStop,
        filters,
        ContextTypes
    )

    agent = HermesAgent(role=role, bifrost_key=bifrost_key)
    app = ApplicationBuilder().token(token).build()

    async def security_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not allowed_users:
            return  # Open mode if no whitelist specified yet
        user = update.effective_user
        if not user or user.id not in allowed_users:
            uid = user.id if user else "desconocido"
            logger.warning(f"⛔ Acceso no autorizado ({role}): User ID {uid}")
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"⛔ Acceso no autorizado para el bot de {role}. Tu Telegram User ID ({uid}) no está registrado."
                )
            raise ApplicationHandlerStop

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        brand_name = os.environ.get("PROJECT_NAME", "tu negocio").replace("_", " ").title()
        if role == "client":
            msg = (
                f"👋 *Hola. Soy tu asistente de gestión para {brand_name}.*\n\n"
                "Puedo ayudarte a:\n"
                "• Consultar y cambiar precios de productos al instante\n"
                "• Ver y ajustar stock y catálogo\n"
                "• Consultar pedidos recientes y transacciones\n"
                "• Atender requerimientos de clientes\n\n"
                "Escribime en lenguaje natural lo que necesites consultar o modificar."
            )
        else:
            msg = (
                "👋 *Hola. Soy Hermes, tu copiloto soberano (AGY Twin) en Zerops 24/7.*\n\n"
                "Capacidades operativas:\n"
                "• `/status` - Salud del gateway y servicios\n"
                "• `/reset` - Limpiar ventana de contexto\n"
                "• Control de Zerops (start, stop, list, zcli)\n"
                "• GitOps de webdev/webprod (git status, log, diff, preview)\n"
                "• Gestión completa de catálogo e-commerce en vivo"
            )
        await send_split_message(update, msg)

    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🟢 Hermes Status ({role.upper()}): OPERATIONAL\n"
            f"• Virtual Key: {bifrost_key}\n"
            f"• Rol: {role}\n"
            f"• Base de Datos: PostgreSQL 18 (SSR Live Sync)\n"
            f"• Whitelist: {'Activa (' + str(len(allowed_users)) + ' usuarios)' if allowed_users else 'Abierta'}"
        )

    async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cid = update.effective_chat.id
        agent.history = []
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                import asyncpg
                conn = await asyncpg.connect(db_url, timeout=3.0)
                await conn.execute("DELETE FROM hermes_messages WHERE chat_id = $1", cid)
                await conn.close()
            except Exception:
                pass
        try:
            import aiosqlite
            db_path = "/mnt/localstorage/hermes/sessions.db"
            if os.path.exists(db_path):
                async with aiosqlite.connect(db_path, timeout=3.0) as db:
                    await db.execute("DELETE FROM hermes_messages WHERE chat_id = ?", (cid,))
                    await db.commit()
        except Exception:
            pass
        await update.message.reply_text("🧹 Historial y ventana de contexto reiniciados con éxito.")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return

        user_text = update.message.text or update.message.caption or ""
        photo_path = None

        if update.message.photo:
            try:
                photo = update.message.photo[-1]
                file_obj = await context.bot.get_file(photo.file_id)
                storage_dir = "/mnt/localstorage/products" if os.path.exists("/mnt/localstorage") else "/var/www/localstorage/products"
                os.makedirs(storage_dir, exist_ok=True)
                filename = f"telegram_{update.message.id}_{photo.file_unique_id}.jpg"
                dest_path = os.path.join(storage_dir, filename)
                await file_obj.download_to_drive(dest_path)
                photo_path = dest_path
                logger.info(f"[{role.upper()}] Foto guardada exitosamente en: {photo_path}")
            except Exception as pe:
                logger.error(f"[{role.upper()}] Error al descargar foto de Telegram: {pe}")

        if not user_text and not photo_path:
            return

        if photo_path:
            user_text = f"[Foto recibida y guardada localmente en {photo_path}]: {user_text}".strip()

        chat_id = update.effective_chat.id
        logger.info(f"[{role.upper()}] Prompt from chat {chat_id}: {user_text[:50]}...")
        async with keep_typing(context.bot, chat_id):
            try:
                reply = await agent.run_turn(user_text, chat_id=chat_id)
                await send_split_message(update, reply)
            except Exception as e:
                logger.error(f"[{role.upper()}] Error processing turn: {e}")
                await update.message.reply_text(f"⚠️ Error al procesar tu solicitud: {str(e)}")

    app.add_handler(TypeHandler(Update, security_gate), group=-1)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))
    return app

async def run_bot():
    if not ADMIN_TOKEN and not CLIENT_TOKEN:
        await run_dormant_loop()
        return

    try:
        import telegram
    except ImportError:
        logger.warning("python-telegram-bot is not installed. Running in dormant standby mode.")
        await run_dormant_loop()
        return

    apps = []
    if ADMIN_TOKEN:
        admin_app = build_bot_app(
            token=ADMIN_TOKEN,
            role="admin",
            allowed_users=ADMIN_ALLOWED_USERS,
            bifrost_key="vk-hermes-agent"
        )
        apps.append(admin_app)

    if CLIENT_TOKEN and CLIENT_TOKEN != ADMIN_TOKEN:
        client_app = build_bot_app(
            token=CLIENT_TOKEN,
            role="client",
            allowed_users=CLIENT_ALLOWED_USERS,
            bifrost_key="vk-hermes-client"
        )
        apps.append(client_app)

    logger.info(f"🚀 Starting Hermes Telegram Gateway ({len(apps)} active bot instance(s))...")
    for app in apps:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

    try:
        while True:
            await asyncio.sleep(60)
    finally:
        for app in apps:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception:
                pass

def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Hermes Telegram Gateway stopped by user.")

if __name__ == "__main__":
    main()

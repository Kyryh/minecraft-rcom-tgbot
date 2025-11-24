import logging

from aiomcrcon import Client, RCONConnectionError
from telegram import (
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
)


from os import getenv

__import__("dotenv").load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler("logs.log")],
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TOKEN = getenv("TOKEN")
IP = getenv("RCON_IP")
PORT = getenv("RCON_PORT")
PASSWORD = getenv("RCON_PASSWORD")
GROUP_ID = getenv("GROUP_ID")

client = Client(IP, PORT, PASSWORD)


async def is_admin(update: Update) -> bool:
    return update.effective_user.id in (
        admin.user.id for admin in await update.effective_chat.get_administrators()
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await client.connect()
        status = "✅ ONLINE"
        await client.close()
    except RCONConnectionError:
        status = "❌ OFFLINE"
    await update.message.reply_text("Server status: " + status)


async def rcon_command(command: str):
    async with client:
        response = await client.send_cmd(command)
        return response[0]


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await rcon_command("list"))


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("This is not for you.")
        return
    if not context.args:
        await update.message.reply_text("Syntax:\n\n/cmd <command>")
        return
    await update.message.reply_text(await rcon_command(" ".join(context.args)))


def main():
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["list", "players"], list_command))
    application.add_handler(
        CommandHandler("cmd", admin_command, filters.Chat(GROUP_ID))
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

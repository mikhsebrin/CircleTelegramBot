from pyrogram import idle
from pyrogram.types import BotCommand

import handlers
import database.database as db
from bot.bot import bot, app


async def main():
    db.set_state("worked_fight", 0)
    
    await bot.start()
    await app.start()
    
    await bot.set_bot_commands([
        BotCommand("queue", "queue"),
        BotCommand("swap_position", "swap position"),
        BotCommand("top", "top"),
        BotCommand("settings", "settings")
    ])
    
    await idle()


if __name__ == "__main__": 
    bot.run(main())

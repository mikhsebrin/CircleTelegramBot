import re
import os
import asyncio
from itertools import zip_longest

from pyrogram import filters

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID, ADMINS_ID
from filters.filters import worked_fight, is_admin
from keyboards.keyboards import keyboard_admin_settings

users_ = {}


@bot.on_message(
    filters.regex(
        re.compile(
            r"^/qupd(\s(!\s?)?(-?\d+)?)?$", re.IGNORECASE
        )
    ) &
    is_admin() &
    filters.chat(CHAT_CIRCLE_ID) &
    filters.reply &
    ~worked_fight()
)
async def test(client, message):
    matches = message.matches[0]
    arg = 0

    if message.reply_to_message.from_user.is_bot:
        await message.reply("Боту нельзя.")
        return

    reply_user_queue_value = (await db.get_user(
        message.reply_to_message.from_user.id, 
        "queue_index"
    ))[0]
    
    if matches.group(2) and matches.group(3):
        arg = matches.group(3)
    elif matches.group(3):
        arg = reply_user_queue_value + int(matches.group(3)) 
    else:
        arg = reply_user_queue_value + 1
    
    await db.set_user(message.reply_to_message.from_user.id, "queue_index", arg)
    await message.reply("Успешно.")


# Костыль, чтобы получить базу
@bot.on_message(
    filters.command("get_database") &
    is_admin() &
    ~worked_fight()
)
async def test(client, message):
    circle_bot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    database_path = os.path.join(circle_bot_dir, 'database', 'database.db')
    
    await message.reply_document(database_path)


async def get_settings_text(user_id: int) -> str:
    result = await db.get_user(
        user_id, 'permission_trusting', 'permission_private', 'permission_admin'
    )
    status_permission_trusting = "✅" if result[0] else "❌"
    status_permission_private ="✅" if result[1] else "❌"
    status_permission_admin = "✅" if result[2] else "❌"

    text =  (
        "<b>⚙️ Права:</b>"
        f"\n\n{status_permission_trusting} Доверие пользователю"
        "\n<i>(Исключить проверку валидности форвардов.)</i>"
        f"\n\n{status_permission_private} Приватная игра"
        "\n<i>(Разрешить приватную игру.)</i>"
        f"\n\n{status_permission_admin} Администрирование"
        "\n<i>(Разрешить использование админ. функций.)</i>"
    )
    return text


@bot.on_callback_query(filters.regex(r"^admin_setter_(.*)") & ~worked_fight())
@db.update_time
async def test(client, call):
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")
        return

    setting_type = call.matches[0].group(1)
    
    if setting_type == "permission_admin" and call.from_user.id not in ADMINS_ID:
        await call.answer("Не разрешено!")
        return

    if call.message.id not in users_:
        await call.answer("Ошибка.")
        return
    
    user_id = users_[call.message.id]

    result = await db.get_user(user_id, setting_type)
    status = 0 if result[0] else 1

    await db.set_user(user_id, setting_type, status)
    
    text = await get_settings_text(user_id)
    await call.message.edit_text(text, reply_markup=keyboard_admin_settings)
    await call.answer("Успешно.")


@bot.on_message(
    ((filters.command(["permission", "p"]) & filters.reply) | filters.regex(re.compile(r"\/(permission|p)([_\s](\d+))", re.I))) &
    ~worked_fight() &
    (is_admin() | filters.user(ADMINS_ID))
)
@db.update_time
async def test(client, message):
    if message.reply_to_message:
        if message.reply_to_message.from_user.is_bot:
            await message.reply("Боту нельзя.")
            return
        
        user_id = message.reply_to_message.from_user.id 
    else:
        user_id = int(message.matches[0].group(2))

    text = await get_settings_text(user_id)
    result = await message.reply(text, reply_markup=keyboard_admin_settings, quote=True)

    users_[result.id] = user_id


@bot.on_message(
    filters.command(["permission", "p"]) &
    (is_admin() | filters.user(ADMINS_ID)) &
    filters.private
)
@db.update_time
async def test(client, message):
    users = db.cursor.execute(
        "SELECT user_id, permission_trusting, permission_private, permission_admin FROM user_table WHERE permission_trusting != 0 OR permission_private != 0 OR permission_admin != 0"
    ).fetchall()
    
    text = "<b>Список пользователей:\n\n</b>"

    if users:
        batches = [
            list(
                filter(None, batch)
            )for batch in zip_longest(*[iter(users)] * 15)
        ]

        for users in batches:
            for user in users:
                status1 = ("✅" if user[1] else "🚫")
                status2 = ("✅" if user[2] else "🚫")
                status3 = ("✅" if user[3] else "🚫")

                text += (
                    f"ID: <code>{user[0]}</code>\n"
                    f"Доверие: {status1}\n"
                    f"Приват: {status2}\n"
                    f"Администратор: {status3}"

                    "\n\n"
                )

            await message.reply(text, quote=False)
            await asyncio.sleep(1)

            text = ""

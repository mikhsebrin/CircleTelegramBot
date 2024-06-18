import datetime
import asyncio

from pyrogram import filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID
from keyboards.keyboards import keyboard_come
from filters.filters import worked_fight

pings_exclude_ids = []


@bot.on_callback_query(filters.regex("^come$") & ~worked_fight())
@db.update_time
async def test(client, call):
    if call.from_user.id not in pings_exclude_ids:
        pings_exclude_ids.append(call.from_user.id)
    else:
        await call.answer("Успешно.")
        return
    
    await call.message.reply(
        f"{call.from_user.first_name}, успешно!"
        " Больше я не стану уведомлять тебя сегодня.",
        quote=False
    )
    await call.answer("Успешно.")


async def ping1() -> None:
    text = ""
    count = 0
    days = 14
    days_seconds_limit = datetime.datetime.now().timestamp() - 86400 * days
    
    users_ids = db.cursor.execute(
        "SELECT user_id FROM user_table "
        "WHERE notifications1 = 1 AND ? < last_activity_time",
        (days_seconds_limit,)
    ).fetchall()
    users_ids = [user_id[0] for user_id in users_ids]

    async for member in bot.get_chat_members(CHAT_CIRCLE_ID):
        if member.user.id in pings_exclude_ids:
            continue

        if member.user.id in users_ids:
            text += member.user.mention() + "\n"
            count += 1
        if count == 5:
            text += "\n⭕️ Скоро Круг крови!"
            await bot.send_message(CHAT_CIRCLE_ID, text)
            text = ""
            count = 0
            await asyncio.sleep(1)
    if count:
        text += "\n⭕️ Скоро Круг крови!"
        await bot.send_message(CHAT_CIRCLE_ID, text)
        await asyncio.sleep(1)
    
    await bot.send_message(
        CHAT_CIRCLE_ID, 
        "Кнопка.", 
        reply_markup=keyboard_come
    )


async def ping2() -> None:
    text = ""
    count = 0
    days_seconds_limit = datetime.datetime.now().timestamp() - 86400 * 14
    
    users_ids = db.cursor.execute(
        "SELECT user_id FROM user_table "
        "WHERE notifications2 = 1 AND ? < last_activity_time",
        (days_seconds_limit,)
    ).fetchall()
    users_ids = [user_id[0] for user_id in users_ids]

    async for member in bot.get_chat_members(CHAT_CIRCLE_ID):
        if member.user.id in users_ids:
            text += member.user.mention() + "\n"
            count += 1
        if count == 5:
            text += "\n⭕️ Совсем скоро Круг крови!"
            await bot.send_message(CHAT_CIRCLE_ID, text)
            text = ""
            count = 0
            await asyncio.sleep(1)
    if count:
        text += "\n⭕️ Совсем скоро Круг крови!"
        await bot.send_message(CHAT_CIRCLE_ID, text)
        await asyncio.sleep(1.1)


async def job_1():
    global pings_exclude_ids
    pings_exclude_ids = []
    
    result = await bot.send_message(
        CHAT_CIRCLE_ID, 
        "<b>❗️Старт ⭕️ Круга Крови через 1 час!</b>"
    )
    
    await result.pin(disable_notification=False)
    await ping1()


async def job_2():
    result = await bot.send_message(
        CHAT_CIRCLE_ID, 
        "<b>❗️Старт ⭕️ Круга Крови через 30 минут!</b>"
    )

    await result.pin(disable_notification=False)
    await ping1()


async def job_3():
    result = await bot.send_message(
        CHAT_CIRCLE_ID, 
        "<b>❗️Старт ⭕️ Круга Крови через 3 минуты!</b>"
    )

    await result.pin(disable_notification=False)
    await ping2()


scheduler = AsyncIOScheduler()
moscow_tz = datetime.timezone(datetime.timedelta(hours=3))

scheduler.add_job(job_1, "cron", hour=16, minute=30, timezone=moscow_tz)
scheduler.add_job(job_2, "cron", hour=17, minute=00, timezone=moscow_tz)
scheduler.add_job(job_3, "cron", hour=17, minute=27, timezone=moscow_tz)

scheduler.start()

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID
from keyboards.keyboards import keyboard_settings
from filters.filters import worked_fight

async def get_settings_text(user_id: int) -> str:
    result = await db.get_user(
        user_id, 'notifications1', 'notifications2', 'queue_visibility', 'top_visibility', 'target_notifications'
    )
    status_notifications1 = "✅" if result[0] else "❌"
    status_notifications2 ="✅" if result[1] else "❌"
    status_queue_visibility = "✅" if result[2] else "❌"
    status_top_visibility = "✅" if result[3] else "❌"
    status_target_notifications = "✅" if result[4] else "❌"

    text =  (
        "<b>⚙️ Настройки:</b>"
        f"\n\n{status_notifications1} Уведомления"
        "\n<i>(Уведомлять о скором начале круга.)</i>"
        f"\n\n{status_notifications2} Доп. уведомление"
        "\n<i>(Напомнить о круге незадолго до его старта.)</i>"
        f"\n\n{status_queue_visibility} Очередь"
        "\n<i>(Учитывать при выборе претендента на победу.)</i>"
        f"\n\n{status_top_visibility} Топ"
        "\n<i>(Отображать в топах.)</i>"
        f"\n\n{status_target_notifications} Таргет"
        "\n<i>(Учитывать при таргете противников.)</i>"
    )
    return text


@bot.on_callback_query(filters.regex(r"^cancel$") & ~worked_fight())
@db.update_time
async def test(client, call):
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")

    try:
        await call.message.edit_text("Закрыто.")
    except Exception as e: 
        pass 
    
    await call.answer()


@bot.on_callback_query(filters.regex(r"^switch_(.*)") & ~worked_fight())
@db.update_time
async def test(client, call):
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")
        return 
    
    user_id = call.from_user.id
    setting_type = call.matches[0].group(1)
    result = await db.get_user(user_id, setting_type)

    status = 0 if result[0] else 1


    await db.set_user(user_id, setting_type, status)
    
    text = await get_settings_text(user_id)
    await call.message.edit_text(text, reply_markup=keyboard_settings)
    await call.answer("Успешно.")


@bot.on_message(
    filters.command("settings") &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    text = await get_settings_text(message.from_user.id)
    await message.reply(text, reply_markup=keyboard_settings, quote=True)


@bot.on_message(
    filters.command("reset_my_top") &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Уверен!",
                callback_data="confirm_the_reset"
            )
        ],
        [
            InlineKeyboardButton(
                "↙️ Закрыть",
                callback_data="cancel"
            )
        ],
    ])
    
    await message.reply("Ты собираешься обнулить свою статистику. Уверен?", reply_markup=keyboard)


@bot.on_callback_query(filters.regex(r"^confirm_the_reset$") & ~worked_fight())
@db.update_time
async def test(client, call):    
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")
        return

    db.cursor.execute('''
        UPDATE user_top_table
        SET
            visits = 0,
            wins = 0,
            hits_dealt = 0,
            friendly_fire_hits = 0,
            blocked_hits = 0,
            misses = 0,
            damage_dealt = 0,
            pings = 0,
            shields_used = 0,
            successful_shield_usage = 0,
            hits_blocked_by_shield = 0,
            players_killed = 0,
            visits_strick = 0
        WHERE user_id = ?;
    ''', (call.from_user.id,))
    db.connect.commit()

    await call.answer("Успешно.")
    await call.message.edit_text("Статистика успешно обнулена.")

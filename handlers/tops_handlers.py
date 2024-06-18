import re
import asyncio
import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID, __bot_username__
from filters.filters import worked_fight
from keyboards.keyboards import keyboard_cancel, keyboard_top_type

# {msg_id: (tops_list, current_page, max_page, top_name, users{id: name}, time(unix))}
_tops = {}

_trottling_duration = 1.5
_last_call_time = datetime.datetime.now().timestamp()

tops_list = """
🏆 <b>Список топов</b>

Посещений круга крови (/top_1)
Победителей (/top_2)
Стрик посещений (/top_3)
Нанесённых ударов (/top_4)
Нанесённых ударов по своим (/top_5)
Заблокированных тебе ударов (/top_6)
Промахов (/top_7)
Нанесённого урона (/top_8)
Пинков (/top_9)
Использованных щитов (/top_10)
Удачно использованных щитов (/top_11)
Ударов тобой заблокировано (/top_12)
Игроков убито (/top_13)
"""

top_type_info = {
    1:  ("visits", "Посещений круга крови"),
    2:  ("wins", "Победителей"),
    3:  ("visits_strick", "Стрик посещений"),
    4:  ("hits_dealt", "Нанесённых ударов"),
    5:  ("friendly_fire_hits", "Нанесённых ударов по своим"),
    6:  ("blocked_hits", "Заблокированных тебе ударов"),
    7:  ("misses", "Промахов"),
    8:  ("damage_dealt", "Нанесённого урона"),
    9:  ("pings", "Пинков"),
    10: ("shields_used", "Использованных щитов"),
    11: ("successful_shield_usage", "Удачно использованных щитов"),
    12: ("hits_blocked_by_shield", "Ударов тобой заблокировано"),
    13: ("players_killed", "Игроков убито")
}


async def job_1():
    tops = _tops.copy()
    
    for message_id in tops:
        if datetime.datetime.now().timestamp() - tops[message_id][5] >= 60 * 60:
            del _tops[message_id]


async def trottling_check(call):
    global _last_call_time

    if datetime.datetime.now().timestamp() - _last_call_time < _trottling_duration:
        await call.answer(
            "Не так часто!\nОсталось подождать: " 
            f"{round(_trottling_duration - (datetime.datetime.now().timestamp() - _last_call_time), 2)} секунд")
        return False
    else:
        _last_call_time = datetime.datetime.now().timestamp()
        return True


def get_top_keyboard(all_page_num, current_page=0):
    tops_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️", 
                callback_data="left_top"
            ),
            InlineKeyboardButton(
                f"{current_page + 1}/{all_page_num + 1}", 
                callback_data="center_top"
            ),
            InlineKeyboardButton(
                "➡️", 
                callback_data="right_top"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Вернуться", 
                callback_data="top_switch_back"
            ),
        ]
    ])
    return tops_keyboard


@bot.on_callback_query(
    filters.regex(r'^top_switch_0$') & 
    ~worked_fight())
@db.update_time
async def test(client, call):
    await call.answer("Это тут для красоты :)")


@bot.on_callback_query(
    filters.regex(r'^top_switch_(\d+|back)') & 
    ~worked_fight())
@db.update_time
async def test(client, call):
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")
        return

    if not await trottling_check(call):
        return
    
    match = call.matches[0].group(1)

    if match == "back":
        await call.message.edit_text(tops_list, reply_markup=keyboard_top_type)
        await call.answer()
        return

    users = dict()
    async for member in bot.get_chat_members(chat_id=call.message.chat.id):
        users[member.user.id] = member.user.first_name

    top_type = top_type_info[int(match)]
    days_seconds_limit = datetime.datetime.now().timestamp() - 86400 * 14

    tops = db.cursor.execute(
        f"SELECT user_top_table.user_id, user_top_table.{top_type[0]} "
        f"FROM user_top_table "
        f"JOIN user_table ON user_top_table.user_id = user_table.user_id "
        f"WHERE (user_top_table.{top_type[0]} > 0 AND user_table.top_visibility = 1 AND {days_seconds_limit} < user_table.last_activity_time) "
        f"   OR user_top_table.user_id = {call.from_user.id} "
        f"ORDER BY user_top_table.{top_type[0]} DESC"
    ).fetchall()
    
    tops = [item for item in tops if item[0] in list(users.keys())]
    
    tops = list(enumerate(tops, 1))

    check = False
    text = f'🏆 {top_type[1]}\n'
        
    for count, (user_id, value) in tops:
        name = users[user_id]
        text += (
            f'\n{count}. '
            + (f"🧢{name} " if call.from_user.id == user_id else f"{name} ")
            + f'— {value}'
            
        )
        if call.from_user.id == user_id:
            check = True
        if count >= 10:
            break
    
    if not check:
        for count, (user_id, value) in tops[9:]:
            if call.from_user.id == user_id:
                name = users[user_id]
                text += (
                    '\n- - -\n'
                    f'{count}. '
                    + (f"🧢{name} " if call.from_user.id == user_id else f"{name} ")
                    + f'— {value}'
                )
                break
    page_all_num = sum(1 for _ in range(0, len(tops), 10)) - 1
    
    await call.message.edit_text(text, reply_markup=get_top_keyboard(page_all_num))
    _tops[call.message.id] = [tops, 0, page_all_num, top_type[1], users,  datetime.datetime.now().timestamp()]
    await call.answer()


@bot.on_callback_query(
    filters.regex(r'^(left|center|right)_top$') & 
    ~worked_fight())
@db.update_time
async def test(client, call):
    try:
        if call.from_user.id != call.message.reply_to_message.from_user.id:
            await call.answer("Это не твои кнопки.")
            return
    except:
        await call.answer("Неизвестная ошибка.")
        return
    
    if call.message.id not in _tops:
        await call.answer("Ошибка.")
        return

    info = _tops[call.message.id]
    direction = call.matches[0].group(1)
    required_page = info[1]
                  
    if direction == "left":
        if required_page - 1 < 0:
            required_page = sum(1 for _ in range(0, len(info[0]), 10)) - 1
        else:
            required_page -= 1                                    
    elif direction == "right":
        if required_page + 1 > info[2]:
            required_page = 0
        else:
            required_page += 1
    elif direction == "center":
        required_page = 0

    if info[1] == required_page:
        await call.answer("Ты уже тут :)")
        return

    if not await trottling_check(call):
        return

    check = False
    top_name = f'🏆 {info[3]}\n'
    text = ''
    count_ = 0

    last_value = 0

    for count, (user_id, value) in info[0][required_page * 10:]:
        name = info[4][user_id]
        text += (
            f'\n{count}. '
            + (f"🧢{name} " if call.from_user.id == user_id else f"{name} ")
            + f'— {value}'
            
        )
        count_ += 1
        
        last_value = count
        
        if call.from_user.id == user_id:
            check = True
        if count_ >= 10:
            break
    
    if not check:
        for count, (user_id, value) in info[0]:
            if call.from_user.id == user_id:
                name = info[4][user_id]
                if count > last_value:
                    text += (
                        '\n- - -'
                        f'\n{count}. '
                        + (f"🧢{name} " if call.from_user.id == user_id else f"{name} ")
                        + f'— {value}'
                    )
                else:
                    text = (
                        f'\n{count}. '
                        + (f"🧢{name} " if call.from_user.id == user_id else f"{name} ")
                        + f'— {value}'
                        '\n- - -'
                    ) + text
                break

    await call.message.edit_text(top_name + text, reply_markup=get_top_keyboard(info[2], required_page))
    
    _tops[call.message.id][1] = required_page 
    await call.answer()


@bot.on_message(
    filters.regex(re.compile(rf'^\/top(_(?P<value>[1-9]|1[0-3]))?(@{__bot_username__})?$', re.I)) &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    match = message.matches[0].group('value')
    
    if not match:
        await message.reply(tops_list, reply_markup=keyboard_top_type)
        return
    
    users = dict()
    async for member in bot.get_chat_members(chat_id=message.chat.id):
        users[member.user.id] = member.user.first_name

    top_type = top_type_info[int(match)]
    days_seconds_limit = datetime.datetime.now().timestamp() - 86400 * 14

    tops = db.cursor.execute(
        f"SELECT user_top_table.user_id, user_top_table.{top_type[0]} "
        f"FROM user_top_table "
        f"JOIN user_table ON user_top_table.user_id = user_table.user_id "
        f"WHERE (user_top_table.{top_type[0]} > 0 AND user_table.top_visibility = 1 AND {days_seconds_limit} < user_table.last_activity_time) "
        f"   OR user_top_table.user_id = {message.from_user.id} "
        f"ORDER BY user_top_table.{top_type[0]} DESC"
    ).fetchall()
    
    tops = [item for item in tops if item[0] in list(users.keys())]
    
    tops = list(enumerate(tops, 1))

    check = False
    text = f'🏆 {top_type[1]}\n'
    
    for count, (user_id, value) in tops:
        name = users[user_id]
        text += (
            f'\n{count}. '
            + (f"🧢{name} " if message.from_user.id == user_id else f"{name} ")
            + f'— {value}'
            
        )
        if message.from_user.id == user_id:
            check = True
        if count >= 10:
            break
    
    if not check:
        for count, (user_id, value) in tops[9:]:
            if message.from_user.id == user_id:
                name = users[user_id]
                text += (
                    '\n- - -\n'
                    f'{count}. '
                    + (f"🧢{name} " if message.from_user.id == user_id else f"{name} ")
                    + f'— {value}'
                )
                break
    page_all_num = sum(1 for _ in range(0, len(tops), 10)) - 1

    result = await message.reply(text, reply_markup=get_top_keyboard(page_all_num))
    _tops[result.id] = [tops, 0, page_all_num, top_type[1], users, datetime.datetime.now().timestamp()]


@bot.on_message(
    filters.command('stats') &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):    
    (
        _,
        visits, 
        wins, 
        hits_dealt, 
        friendly_fire_hits, 
        blocked_hits, 
        misses, 
        damage_dealt, 
        pings, 
        shields_used, 
        successful_shield_usag, 
        hits_blocked_by_shield, 
        players_killed,
        visits_strick
    ) = db.cursor.execute(f"SELECT * FROM user_top_table WHERE user_id = {message.from_user.id}").fetchone()

    await message.reply(f'''
📊 Ваша статистика:

Посещений круга крови: {visits} раз(а)
— выигрышных: {wins}
— стрик: {visits_strick}

Нанесено ударов всего: {hits_dealt}
— по своим: {friendly_fire_hits}
— заблокировано: {blocked_hits}

Промахов всего: {misses}
Всего урона нанесено: {damage_dealt}
Убил игроков: {players_killed}
Пнул игроков: {pings} раз(а)

Использовано щитов всего: {shields_used}
— успешных: {successful_shield_usag} ({round((successful_shield_usag / shields_used) * 100, 2) if shields_used else 0}%)

Ударов тобой заблокировано: {hits_blocked_by_shield}
    ''', 
    reply_markup=keyboard_cancel
    )

scheduler = AsyncIOScheduler()
scheduler.add_job(job_1, "interval", hours=1)
scheduler.start()

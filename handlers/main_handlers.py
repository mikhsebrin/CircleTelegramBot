import re
import math
import datetime
import asyncio 
import random
import urllib.parse
from collections import defaultdict

from pyrogram import filters
from pyrogram.errors import MessageEmpty, UserIsBlocked 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType

import database.database as db
from filters.filters import fighting_bot_forward, worked_fight, is_admin
from configs.configs import CHAT_CIRCLE_ID, CHANNEL_EVENTS_ID
from bot.bot import bot, app
from utils.counting_tops import counting_tops

queue_flag = True
result_sending = None
text = ""
winner_id = 0

players = dict()

fight_logs_list: list  = list()
# set(member, user_id)
users_logs_list: list = list()

users_in_group: list = list()


async def bot_reset():
    global queue_flag, result_sending, text, winner_id, players, fight_logs_list, users_logs_list, users_in_group
    db.set_state("worked_fight", 0)

    queue_flag = True
    result_sending = None
    text = ""
    winner_id = 0
    players = dict()
    fight_logs_list = list()
    users_logs_list = list()
    users_in_group = list()


@bot.on_message(filters.command("bot_reset") & is_admin())
async def test(client, message):
    await bot_reset()
    await message.reply("Успешно.")


@bot.on_callback_query(filters.regex('^done$'))
async def _(client, call):
    await call.message.delete()
    await call.answer()


async def get_target_keyboard(member: str, count):
    enemy_attack_text = urllib.parse.quote(f"🔪 ➡️ 🕳 {member}", safe='')

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"({count}) 🔪 Переслать", 
                    url=f"https://t.me/share/url?url={enemy_attack_text}"
                ),
                InlineKeyboardButton(
                    text="✖️ Убрать", 
                    callback_data="done"
                ),
            ]
        ]
    )


async def target(text: str, current_round: int):
    if current_round in (0, 1):
        await asyncio.sleep(20)
        
    logs = re.findall(r"([а-яёa-z]+) - (\d+)", text, re.I)
    logs = {member: int(heal) for member, heal in logs}

    if get_alive_enemies_sum():
        enemies = {member: logs[member] for member, is_info in players.items() if is_info["is_enemy"] and is_info["is_alive"]}
        enemies_sorted = sorted(enemies.items(), key=lambda item: item[1], reverse=False)
        enemies_group = {member: math.ceil(heal / 199) for member, heal in enemies_sorted}

        users = [(member, is_info) for member, is_info in players.items() if not is_info["is_enemy"] and is_info["is_alive"] and is_info["is_target"]]
        
        if not users:
            return
        
        users_group = {enemies: [] for enemies in enemies_group.keys()}
        users_private = {enemies: [] for enemies in enemies_group.keys()}

        group_text = ""

        for member, count in enemies_group.items():
            if not users:
                break
            
            for count in range(count):
                if users:
                    user = users[0]
                    users_group[member].append(user)
                    if user[1]["group_type"] == ChatType.PRIVATE:
                        users_private[member].append(user)
                    del users[0]
                else:
                    break
        
        while users:
            if not users:
                break
            
            for member in enemies_group.keys():
                if users:
                    user = users[0]
                    users_group[member].append(user)
                    if user[1]["group_type"] == ChatType.PRIVATE:
                        users_private[member].append(user)
                    del users[0]
                else:
                    break

        for member, users in users_group.items():
            if not users:
                continue

            group_text += f"\n({enemies_group[member]}) <code>🔪 ➡️ 🕳 {member}</code>\n"
            
            for user, is_info in users:
                if is_info["group_type"] == ChatType.PRIVATE:
                    group_text += f'{user} ({is_info["name"]})\n'
                else:
                    group_text += f'<a href="tg://user?id={is_info["id"]}"><b>{user}</b></a> ({is_info["name"]})\n'

        if group_text:
            await bot.send_message(result_sending.chat.id, f"<b>Раунд:</b> {current_round}\n" + group_text + "\n@HyperionFightbot")

        for member, users in users_private.items():
            if not users:
                continue

            private_text = f"<b>Раунд:</b> {current_round}\n\n<code>🔪 ➡️ 🕳 {member}</code>\n\n@HyperionFightbot"
            
            for user, is_info in users:
                await bot.send_message(is_info["id"], private_text, reply_markup=await get_target_keyboard(member, enemies_group[member]))
                await asyncio.sleep(0.2)
    else:
        target_names = [name for name, is_info in players.items() if is_info["id"] != winner_id]

        for member, user_id in [(member, is_info["id"]) for member, is_info in players.items() if not is_info["is_enemy"] and is_info["is_alive"] and is_info["group_type"] == ChatType.PRIVATE]:
            try:
                await asyncio.sleep(0.2)
            
                if user_id != winner_id:
                    

                    if target_names:
                        target_name = random.choice(target_names)
                        
                        text = f"<b>Раунд:</b> {current_round}\n\n<code>🔪 ➡️ 🕳 {target_name}</code>\n\n@HyperionFightbot</b>"
                        await bot.send_message(user_id, text, reply_markup=await get_target_keyboard(target_name, math.ceil(logs[target_name] / 199)))
                    else:
                        text = f"<b>Раунд:</b> {current_round}\n\n<code>🔪 ➡️ 🕳 {member}</code>\n\n@HyperionFightbot</b>"
                        await bot.send_message(user_id, text, reply_markup=await get_target_keyboard(member, math.ceil(logs[member] / 199)))

                else:
                    if target_names:
                        target_name = random.choice(target_names)
                        text = f"<b>Раунд:</b> {current_round}\n\n<code>🔪 ➡️ 🕳 {target_name}</code>\n\n@HyperionFightbot</b>"
                        await bot.send_message(user_id, text, reply_markup=await get_target_keyboard(target_name, math.ceil(logs[target_name] / 199)))
                    else:
                        text = "Выигрывай)"
                        await bot.send_message(user_id, text)
            except Exception as e:
                print(e)


async def update_strick() -> None:
    users_ids = [user_id[0] for user_id in db.cursor.execute(
        "SELECT user_id FROM user_top_table WHERE visits_strick > 0"
    ).fetchall()]
    current_users_id = set([user_id[1] for user_id in users_logs_list])
    
    for user_id in users_ids:
        if user_id not in current_users_id:
            db.cursor.execute( 
                "UPDATE user_top_table SET visits_strick = 0 WHERE user_id = ?",
                (user_id,)
            )
    
    db.connect.commit()


# Фильтрует тех, кто пришли на круг и живы(отключено)
async def present_on_the_circle(_, __, query):
    currnt_circle_users = []
    for member in players:
        if (
            # players[member]["is_alive"] and 
            not players[member]["is_enemy"]
        ):
            currnt_circle_users.append(players[member]["id"])

    if query.from_user.id in currnt_circle_users:
        return True
    else:
        return False


def get_alive_enemies_sum():
    return sum(1 for member in players if players[member]["is_alive"] and players[member]["is_enemy"])


async def send_queue(editing_text: bool=False):
    global winner_id
    
    chat_users = []
    async for member in bot.get_chat_members(result_sending.chat.id):
        chat_users.append(member.user.id)
    
    currnt_circle_users = []
    for member, is_info in players.items():
        if (
            is_info["is_alive"] and 
            not is_info["is_enemy"] and
            is_info["friendly_fire_winner"] < 1
        ):
            currnt_circle_users.append(is_info["id"])

    queue = db.cursor.execute(
        "SELECT user_id, queue_index FROM user_table "
        "WHERE queue_visibility = 1 ORDER BY queue_index DESC"
    ).fetchall()

    queue = {
        user_id: queue_index for user_id, queue_index in queue
        if user_id in chat_users and user_id in currnt_circle_users
    }    

    winner_id = list(queue.keys())[0] if queue else 0

    output = []
    for member in queue:
        user = await bot.get_users(member)
        output.append(user.first_name)

    try:
        await bot.send_message(result_sending.chat.id, "<b>  •  </b>".join(output))
    except MessageEmpty:
        await bot.send_message(result_sending.chat.id, "<b>Победитель не может быть определён.</b>")
    except Exception as e:
        await bot.send_message(result_sending.chat.id, "<b>Неизвестная ошибка.</b>")
        print(e)

    if editing_text: 
        try:
            await bot.edit_message_text(
                chat_id=result_sending.chat.id,
                message_id=result_sending.id,
                text=await reassembly(text),
            )
        except:
            pass

    # else:
    #     result_sending = await bot.send_message(
    #         result_sending.chat.id, 
    #         await reassembly(text)
    #     )


async def send_winner(text: str) -> None:
    winner = re.search(r"Победил\s(.+)!", text, re.I).group(1)
    if re.search("приз зрительских симпатий:", text):
        additional_winners = "\n".join(
            re.search(r"симпатий: (.+)", text, re.I).group(1).split(" и ")
        )

        result = await bot.send_message(
            result_sending.chat.id,
            f"🎉Круг завершён. {winner} победил!</b>\n\n<i>"
            f"🤙Приз зрительских симпатий:</i>\n{additional_winners}",
        )
    else:
        result = await bot.send_message(
            result_sending.chat.id, f"<b>🎉Круг завершён. {winner} победил!</b>"
        )

    await result.pin(disable_notification=True)

    for member in players:
        if players[member]["is_alive"] and not players[member]["is_enemy"]:
            await db.set_user(players[member]["id"], "queue_index", 0)
            await db.increment_user_field(players[member]["id"], 'wins', 1)


async def update_open_user() -> None:
    for member in players:
        if players[member]["current_round_open"]:
            players[member]["current_round_open"] = False


async def update_dead_users(text: str) -> None:
    logs = re.findall(r"🕳 ([а-яёa-z]+)\s-\s☠️", text, re.I)

    for member in logs:
        if member in players:
            players[member]["is_alive"] = False
        
        if players[member]["id"] == winner_id:
            await send_queue()


async def update_shield(text: str) -> None:
    logs = re.findall(r"🕳 ([а-яёa-z]+) (🛡 себя|🛡 🕳 [а-яёa-z]+)", text, re.I)

    for member in logs:
        if member[0] in players:
            players[member[0]]["shield"] -= 1


async def friendly_fire(text: str) -> None:
    logs = re.findall(r"([а-яёa-z]+) [🔪🦶] 🛡?🕳 ([а-яёa-z]+)", text, re.I)
    text = ""
    
    other_private_user = []
    
    for members in logs:
        if (
            get_alive_enemies_sum() and
            not players[members[0]]["is_enemy"] and
            not players[members[1]]["is_enemy"] and
            not players[members[1]]["current_round_open"] and
            members[0] != members[1]
        ):
            
            players[members[0]]["friendly_fire"] += 1
            
            if members[0] in [user[0] for user in users_logs_list]:
                await db.increment_user_field(players[members[0]]["id"], "friendly_fire_hits", 1)
            
            if  players[members[0]]["friendly_fire"] >= 2:

                if not players[members[0]]["in_group"]:
                    other_private_user.append((players[members[0]]["id"], "👹 Ты теперь противник"))
                    text += f'<b>{members[0]}</b> ({players[members[0]]["name"]}) 👹 Теперь противник\n'
                else:
                    text += f'<a href="tg://user?id={players[members[0]]["id"]}"><b>{members[0]}</b></a> ({players[members[0]]["name"]}) 👹 Теперь противник\n'

                players[members[0]]["is_enemy"] = True
                
            else:
                if not players[members[0]]["in_group"]:
                    other_private_user.append((players[members[0]]["id"], "❗️ НЕ БЕЙ СВОИХ"))
                    text += f'<b>{members[0]}</b> ({players[members[0]]["name"]}) ❗️ НЕ БЕЙ СВОИХ\n'
                else:
                    text += f'<a href="tg://user?id={players[members[0]]["id"]}"><b>{members[0]}</b></a> ({players[members[0]]["name"]}) ❗️ НЕ БЕЙ СВОИХ\n'
        elif (
            not get_alive_enemies_sum() and
            not players[members[0]]["is_enemy"] and
            not players[members[1]]["is_enemy"] and
            players[members[0]]["id"] != players[members[1]]["id"] and
            players[members[1]]["id"] == winner_id
        ):
            players[members[0]]["friendly_fire_winner"] += 1
            
            if not players[members[0]]["in_group"]:
                text += f'<b>{members[0]}</b> ({players[members[0]]["name"]}) ❗️ НЕ БЕЙ ПОБЕДИТЕЛЯ\n'
                other_private_user.append((players[members[0]]["id"], "❗️ НЕ БЕЙ ПОБЕДИТЕЛЯ"))
            else:
                text += f'<a href="tg://user?id={players[members[0]]["id"]}"><b>{members[0]}</b></a> ({players[members[0]]["name"]}) ❗️ НЕ БЕЙ ПОБЕДИТЕЛЯ\n'

            if members[0] in [user[0] for user in users_logs_list]:
                await db.increment_user_field(players[members[0]]["id"], "friendly_fire_hits", 1)

    if text:
        await bot.send_message(
            result_sending.chat.id,
            text[:4096]
        )
    
    if other_private_user:
        for user_id, text in other_private_user:
            try:
                await bot.send_message(user_id, text)
                await asyncio.sleep(0.2)
            except Exception as e:
                print(e)


async def reassembly(text: str) -> str:
    logs = re.findall(r"([а-яёa-z]+) - (\d+)", text, re.I)
    logs = {member: int(heal) for member, heal in logs}

    current_round = re.search(r"Раунд (\d+)", text).group(1)

    enemies = {member: logs[member] for member, is_info in players.items() if is_info["is_enemy"] and is_info["is_alive"]}
    enemies = sorted(enemies.items(), key=lambda item: item[1], reverse=False)
    enemies = {member: heal for member, heal in enemies}

    if enemies:
        allies_list = {
            member: logs[member] for member, is_info in players.items()
            if not is_info["is_enemy"] and 
            is_info["is_alive"] and
            is_info["friendly_fire_winner"] < 1
        }
    else:
        allies_list = {
            member: logs[member] for member, is_info in players.items()
            if not is_info["is_enemy"] and 
            is_info["is_alive"] and
            is_info["friendly_fire_winner"] < 1 and 
            is_info["in_group"]
        }

    winner_text = ""
    output = f"<b>Раунд:</b> {current_round}"
    
    if not enemies:
        violator_list =  {
            member: is_info for member, is_info in players.items()
            if (is_info["friendly_fire_winner"] >= 1 and
            not is_info["is_enemy"] and
            is_info["is_alive"]) or
            (not is_info["in_group"] and not is_info["is_enemy"] and is_info["is_alive"])
        }

        violator_list = {member: logs[member] for member, _ in violator_list.items()}
        output += f"\n\n<i>Нарушители:</i>" if len(violator_list) else ""
        for member, heal in violator_list.items():
            output += (
                f"\n👹 ({math.ceil(heal / 199)}) "
                f"<a href=\"tg://user?id={players[member]['id']}\">{players[member]['name']}</a> "
                f"<code>🔪 ➡️ 🕳 {member}</code> "
            )

    winner_added = False

    if not enemies: 
        output += "\n\n<i>Список участников:</i>" if len([name for name in allies_list if players[name]["id"] != winner_id]) else ""
        
        for member, heal in allies_list.items():
            if players[member]["id"] != winner_id:
                output += (
                    f"\n({math.ceil(heal / 199)}) "
                    f"<a href=\"tg://user?id={players[member]['id']}\">{players[member]['name']}</a> "
                    f"<code>🔪 ➡️ 🕳 {member}</code> "
                )
            else:
                winner_text += "\n\n<i><b>Победитель:</b></i>" if not winner_added else ""
                winner_added = True

                winner_text += (
                    f"\n({math.ceil(heal / 199)}) "
                    f"<a href=\"tg://user?id={players[member]['id']}\">{players[member]['name']}</a> "
                    f"/ 🛡: {players[member]['shield']} "
                    f"<code>🛡 Прикрыть ➡️ 🕳 {member}</code>"
                )
        output += winner_text
        output += "\n\n<code>💉 Детоксикация на себя</code>"
    else:
        output += f"\n\n<i>Количество участников:</i> <b>{len(allies_list)}</b>"

    output += f"\n\n<i>Список противников (<b>{len(enemies)}</b>):</i>" if len(enemies) else ""

    for member, heal in enemies.items():
        output += (
            f"\n({math.ceil(heal / 199)}) " 
            f"🛡: {players[member]['shield']} " +
            ("👹 " if players[member]['friendly_fire'] >= 2 else " ") +
            f"<code>🔪 ➡️ 🕳 {member}</code>"
        )

    output += "\n\n@HyperionFightbot"
    
    return output[:4096]


@bot.on_message(
    filters.regex(re.compile(r"^Твои статы:\n🕳\s(.+)\s-\s(-?\d+)", re.M)) &
    (filters.chat(CHAT_CIRCLE_ID) | filters.private) &
    worked_fight()
)
@db.update_time
async def test(client, message):
    global queue_flag

    trusting_status = (await db.get_user(message.from_user.id, "permission_trusting"))[0]
    private_status =  (await db.get_user(message.from_user.id, "permission_private"))[0]
    
    if message.chat.type == ChatType.PRIVATE:
        if not private_status:
            await message.reply("Обратитесь к администратору, чтобы получить приватный доступ.")
            await message.delete()
            return

    if not trusting_status:
        if message.forward_from:
            if not (datetime.datetime.now() - message.forward_date <= datetime.timedelta(hours=1)):
                await message.reply(f"{message.from_user.mention()}, форвард устарел.")
                await message.delete()
                return
        else:
            await message.reply(f"{message.from_user.mention()}, сообщение не является форвардом.")
            await message.delete()
            return

    member, heal = (
        message.matches[0].group(1),
        int(message.matches[0].group(2))
    )

    if (
        players[member]["is_enemy"] and
        players[member]["friendly_fire"] < 2
    ):
        if message.from_user.id not in [user_id[1] for user_id in users_logs_list]:
            value = (await db.get_user(message.from_user.id, "queue_index"))[0]
            await db.set_user(message.from_user.id, "queue_index", value + 1)
            await db.increment_user_field(message.from_user.id, "visits_strick", 1)
            await db.increment_user_field(message.from_user.id, "visits", 1)
        
            users_logs_list.append((member, message.from_user.id))

        result = (await db.get_user(message.from_user.id, "target_notifications"))[0]

        if message.chat.type == ChatType.PRIVATE:
            if not result:
                await db.set_user(message.from_user.id, "target_notifications", 1)
                result = 1

        if message.from_user.id not in users_in_group:
            if not result:
                await db.set_user(message.from_user.id, "target_notifications", 1)

            players[member]["in_group"] = False
            players[member]["name"] = "🎭"
        else:
            players[member]["in_group"] = True
            players[member]["name"] = message.from_user.first_name.split()[0][:14]
            
        players[member]["group_type"] = message.chat.type

        players[member]["is_enemy"] = False
        players[member]["id"] = message.from_user.id
        players[member]["current_round_open"] = True
        players[member]["is_target"] = bool((await db.get_user(message.from_user.id, "target_notifications"))[0])

        if int(heal) <= 0:
            players[member]['is_alive'] = False

        try:
            await bot.edit_message_text(
                chat_id=result_sending.chat.id,
                message_id=result_sending.id,
                text=await reassembly(text),
            )
        except Exception as e: 
            pass 

        if not get_alive_enemies_sum() and queue_flag:
                queue_flag = False
                await send_queue(editing_text=True)

    elif (not players[member]["is_enemy"]):
        await message.reply(f"{message.from_user.mention()}, ты уже в союзниках.")
    
    await message.delete()


@bot.on_message(
    filters.regex(re.compile(r"^Бой в 🩸  круге крови начался!", re.M)) &
    fighting_bot_forward() &
    worked_fight() &
    filters.chat(CHAT_CIRCLE_ID)
)
@db.update_time
async def test(client, message):
    await message.reply(f"{message.from_user.mention()}, форвард не содержит имени.")
    await message.delete()


@bot.on_message(
    filters.chat(CHAT_CIRCLE_ID) &
    worked_fight() &
    (~filters.text | ~filters.create(present_on_the_circle)) &
    ~is_admin()
)
@db.update_time
async def test(client, message):
    await message.delete()


@app.on_message(filters.chat(CHANNEL_EVENTS_ID))
async def test(client, message):
    global queue_flag, result_sending, text
    
    text = message.text

    if re.search("Бой в 🩸  круге крови начался!", text):
        db.set_state("worked_fight", 1)

        for member in re.findall(r"🕳 ([а-яёa-z]+) ", text, re.I):
            players[member] = {
                "id": None,
                "name": None,
                "is_alive": True,
                "shield": 2,
                "current_round_open": True,
                "friendly_fire": 0,
                "friendly_fire_winner": 0, 
                "is_enemy": True,
                "is_target": None,
                "in_group": None,
                "group_type": None
            }

        result_sending = await bot.send_message(
            CHAT_CIRCLE_ID,
            (
                "<b>⭕️ Круг Крови начался!</b>"
                f"\n\n<i>Список участников (<b>{len(players)}</b>):</i>\n🕳"
                + "\n🕳".join(players)
                + "\n\n<code>🛡 Прикрыть себя</code> / <code>💉 Детоксикация на себя</code>"
                "\n\n@HyperionFightbot"
            )
        )
        await result_sending.pin(disable_notification=True)

        async for member in bot.get_chat_members(CHAT_CIRCLE_ID):
            users_in_group.append(member.user.id)
            
        await target(text, current_round=0)

    if re.search("Раунд", text):
        current_round = int(re.search(r"Раунд (\d+)", text).group(1))

        fight_logs_list.append(text)

        await update_shield(text)
        await friendly_fire(text)
        await update_dead_users(text)
        await update_open_user()

        if not get_alive_enemies_sum() and queue_flag:
            queue_flag = False
            await send_queue()

        result_sending = await bot.send_message(
            result_sending.chat.id, 
            await reassembly(text)
        )

        await target(text, current_round=current_round)

    if re.search("Победил", text):
        await send_winner(message.text)
        await counting_tops(members=users_logs_list, logs_list=fight_logs_list)
        await update_strick()
        await bot_reset()

    if re.search("круге крови отменен", text):
        await bot.send_message(
            CHAT_CIRCLE_ID,
            "<b>⭕️ Круг крови не состоялся! Недостаточно участников.</b>",
        )

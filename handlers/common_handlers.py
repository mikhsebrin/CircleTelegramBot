import datetime

from pyrogram import filters

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID
from filters.filters import worked_fight


@bot.on_message(
    filters.command(["swap_position", "swp"]) &
    filters.chat(CHAT_CIRCLE_ID) &
    filters.reply &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    if message.reply_to_message.from_user.is_bot:
        await message.reply("Боту нельзя.")
        return
    
    user_queue_value = await db.get_user(
        message.from_user.id,
        "queue_index", "id"
    )
    reply_user_queue_value = await db.get_user(
        message.reply_to_message.from_user.id, 
        "queue_index", 'id'
    )

    if (
        (user_queue_value[0] < reply_user_queue_value[0]) or
        (
            user_queue_value[0] == reply_user_queue_value[0] and
            user_queue_value[1] > reply_user_queue_value[1]
        )
    ):
        await message.reply("Ваша позиция ниже.")
        return

    first_record_values = db.cursor.execute(
        f"SELECT * FROM user_table WHERE user_id = ?",
        (message.from_user.id,)
    ).fetchone()
    second_record_values = db.cursor.execute(
        f"SELECT * FROM user_table WHERE user_id = ?",
        (message.reply_to_message.from_user.id,)
    ).fetchone()
    
    update_values = [
        (*second_record_values[1:], first_record_values[0]),
        (*first_record_values[1:], second_record_values[0])
    ]
    
    db.cursor.executemany(
        f"UPDATE user_table SET "
        f"user_id = ?, queue_index = ?, last_activity_time = ?, "
        f"notifications1 = ?, notifications2 = ?, queue_visibility = ?, "
        f"top_visibility = ?, target_notifications = ?, permission_trusting = ?, permission_private = ?, permission_admin = ?"
        f"WHERE id = ?",
        update_values
    )
    db.connect.commit()

    await db.set_user(message.from_user.id, "queue_index", reply_user_queue_value[0])
    await db.set_user(
        message.reply_to_message.from_user.id, 
        "queue_index",
        user_queue_value[0]
    )
    await message.reply("Обмен произошёл успешно.")


@bot.on_message(
    filters.command(["queue", "q"]) &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    chat_users = []
    async for member in bot.get_chat_members(message.chat.id):
        chat_users.append(member.user.id)

    days_seconds_limit = datetime.datetime.now().timestamp() - 86400 * 7
    queue = db.cursor.execute(
        "SELECT user_id, queue_index FROM user_table "
        "WHERE (queue_visibility = 1 AND ? < last_activity_time AND queue_index >= 0) OR user_id = ? "
        "ORDER BY queue_index DESC",
        (days_seconds_limit, message.from_user.id)
    ).fetchall()   
    queue = {
        user_id: queue_index for user_id, queue_index in queue 
        if user_id in chat_users
    }
    output = []
    for member in queue:
        user = await bot.get_users(member)
        output.append(
            ("🧢" if message.from_user.id == user.id else "") + 
            user.mention + f" ({queue[member]})"
        )

    result = await message.reply("...")
    await result.edit_text("<b>  •  </b>".join(output))

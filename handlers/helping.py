from pyrogram import filters

import database.database as db
from bot.bot import bot
from configs.configs import CHAT_CIRCLE_ID
from filters.filters import worked_fight

from configs.configs import __version__

text = '''
<b>Ассалам алейкум, {user}!</b>

<b><u>Круг крови</u></b>

Когда? Ежедневно в 17:30 МСК

Зачем? Это общегородское событие. Возможная награда - 3 древние монеты и бафф -20% время передвижения и восстановления энергии на сутки.

Что делать? 
Придти в Безопасные земли -5 -7 до 17:30 МСК.
Записаться на битву
🩸  Участвовать
Не сходить с точки до конца битвы.
Бой происходит в чате Бои на гиперионе

Стратегия. 
Есть 2 возможных действия: ударить или прикрыть. Выбирай второе, если уверен, что на тебя или твоего союзника сейчас нападут, либо ударить, чтобы уменьшить здоровье противника. Магия в круге крови не действует.
Взаимодействие с игроками
Все участники битвы имеют уникальные случайные имена. Ты узнаешь своё имя начиная с 1 раунда. Перешли сообщение, начинающиеся с "Раунд" в городской чат Круг крови, чтобы союзники скорее узнали кто свой, а кто наш противник.

С каждым новым раундом в чате Круг крови будет отображен список противников, вида

Список противников:
(4) 🛡: <code>2 🔪 ➡️ 🕳 Бронзовый</code>
(4) 🛡: <code>2 🔪 ➡️ 🕳 Дерзкий</code>
 
(4) - минимальное количество ударов для убийства.
2🛡 - количество оставшихся щитов на бой. Максимум 2 щита на весь бой
🔪 ➡️ 🕳 Бронзовый  - команда для атаки (кликабельна-скопируй команду на убийство конкретного противника, которую можно вставить в чат  Бои на Гиперионе) 

Как только все противники будут повержены, бот раскроет имена союзников и укажет имя победителя. 

(3) Мария <code>🔪 ➡️ 🕳 Золотой</code>

Победитель:
(3) Татьяна / 🛡: 2 <code>🛡 Прикрыть ➡️ 🕳 Чёткий</code>

С этого раунда бей участников с верхнего списка и по возможности защищай победителя
'''


@bot.on_message(
    filters.private &
    filters.command("start") &
    ~worked_fight()
)
async def test(client, message):
    private_status =  (await db.get_user(message.from_user.id, "permission_private"))[0]
    if not private_status:
        await message.reply("Обратитесь к администратору, чтобы получить приватный доступ.")
    else:
        await message.reply("Салам!")


@bot.on_message(
    filters.new_chat_members &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
async def test(client, message):
    await message.reply(text.format(user=message.new_chat_members[0].mention()))
    
    if not message.new_chat_members[0].is_bot:
        await db.new_user(message.new_chat_members[0].id)


@bot.on_message(
    filters.command("help") &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    await message.reply(text.format(user=message.from_user.mention()))


@bot.on_message(
    filters.command(["version", "v"]) &
    filters.chat(CHAT_CIRCLE_ID) &
    ~worked_fight()
)
@db.update_time
async def test(client, message):
    await message.reply(f"<b>v{__version__}</b>")

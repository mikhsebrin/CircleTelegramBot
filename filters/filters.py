from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ChatMembersFilter

import database.database as db


def is_admin():
    async def flt(_, client, query):
        result = await db.get_user(query.from_user.id, "permission_admin")
        return bool(result[0])
    
    return filters.create(flt)


def fighting_bot_forward():
    FIGHTING_BOT_ID = 1102315510
    
    async def flt(_, client, query):
        if query.forward_from:
            if query.forward_from.id == FIGHTING_BOT_ID:
                return True
            else:
                return False
        else:
            return False
    
    return filters.create(flt)


def worked_fight():
    async def flt(_, __, ___):
        result = await db.get_state("worked_fight")
        return bool(result)
    
    return filters.create(flt)


def trusting_permission():
    async def flt(_, __, query):
        result = await db.get_user(query.from_user.id, "permission_trusting")
        return bool(result[0])
    
    return filters.create(flt)


def private_permission():
    async def flt(_, __, query):
        result = await db.get_user(query.from_user.id, "permission_private")
        return bool(result[0])
    
    return filters.create(flt)

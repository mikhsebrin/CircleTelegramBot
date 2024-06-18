from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard_settings = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "Уведомления",
            callback_data="switch_notifications1"
        )
    ],
    [
        InlineKeyboardButton(
            "Доп. уведомление",
            callback_data="switch_notifications2"
        )
    ],
    [
        InlineKeyboardButton(
            "Очередь",
            callback_data="switch_queue_visibility"
        )
    ],
    [
        InlineKeyboardButton(
            "Топ",
            callback_data="switch_top_visibility"

        )
    ],
    [
        InlineKeyboardButton(
            "Таргет",
            callback_data="switch_target_notifications"
        )
    ],
    [
        InlineKeyboardButton(
            "↙️ Закрыть",
            callback_data="cancel"
        )
    ],
])
keyboard_come = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "Отметиться", 
            callback_data="come"
        )
    ],
])
keyboard_cancel = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "↙️ Закрыть", 
            callback_data="cancel"
        )
    ],
])
keyboard_top_type = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "1",
            callback_data="top_switch_1"
        ),
        InlineKeyboardButton(
            "2",
            callback_data="top_switch_2"
        ),
        InlineKeyboardButton(
            "3",
            callback_data="top_switch_3"
        ),
        InlineKeyboardButton(
            "4",
            callback_data="top_switch_4"
        ),
        InlineKeyboardButton(
            "5",
            callback_data="top_switch_5"
        )
    ],
    [
        InlineKeyboardButton(
            "6",
            callback_data="top_switch_6"
        ),
        InlineKeyboardButton(
            "7",
            callback_data="top_switch_7"
        ),
        InlineKeyboardButton(
            "➖",
            callback_data="top_switch_0"
        ),
        InlineKeyboardButton(
            "8",
            callback_data="top_switch_8"
        ),
        InlineKeyboardButton(
            "9",
            callback_data="top_switch_9"
        ),

    ],
    [
        InlineKeyboardButton(
            "10",
            callback_data="top_switch_10"
        ),
        InlineKeyboardButton(
            "11",
            callback_data="top_switch_11"
        ),
        InlineKeyboardButton(
            "➖",
            callback_data="top_switch_0"
        ),
        InlineKeyboardButton(
            "12",
            callback_data="top_switch_12"
        ),
        InlineKeyboardButton(
            "13",
            callback_data="top_switch_13"
        )
    ]
])
keyboard_admin_settings = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "Доверие",
            callback_data="admin_setter_permission_trusting"
        )
    ],
    [
        InlineKeyboardButton(
            "Приват",
            callback_data="admin_setter_permission_private"
        )
    ],
    [
        InlineKeyboardButton(
            "Администрирование",
            callback_data="admin_setter_permission_admin"
        )
    ],
    [
        InlineKeyboardButton(
            "↙️ Закрыть",
            callback_data="cancel"
        )
    ],
])

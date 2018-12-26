from telebot import types

from .emoji import emoji
from .strings import Strings

menu_button = types.KeyboardButton(emoji['arrow_left'] + ' Меню')
back_button = types.KeyboardButton(emoji['arrow_left'] + ' ' + Strings.BACK)
forward_button = types.KeyboardButton(
    emoji['arrow_right'] + ' ' + Strings.FORWARD)
contact_button = types.KeyboardButton(
    emoji['iphone'] + Strings.SEND_PHONE, request_contact=True)
accept_button = types.KeyboardButton(
    emoji['white_check_mark'] + ' Подтвердить')
reject_button = types.KeyboardButton(emoji['x'] + ' Отменить')
branches_button = types.KeyboardButton(
    emoji['building'] + ' ' + Strings.BRANCHES)
news_button = types.KeyboardButton(emoji['news'] + ' ' + Strings.NEWS)
card_button = types.KeyboardButton(emoji['credit_card'] + ' ' + Strings.CARD)
feedback_button = types.KeyboardButton(Strings.FEEDBACK)


def build_main_menu_markup(categories=None, items=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(card_button)
    markup.add(*[news_button, branches_button])
    markup.add(feedback_button)

    return markup


def build_hide_markup():
    return types.ReplyKeyboardRemove()


def build_contact_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(contact_button)
    markup.add(back_button)

    return markup


def build_announcement_markup(back, forward):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if back:
        markup.add(back_button)
    if forward:
        markup.add(forward_button)
    markup.add(menu_button)

    return markup


hide_markup = build_hide_markup()
contact_markup = build_contact_markup()

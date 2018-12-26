import functools
import logging
import sys
import re
from datetime import datetime, date
from os import path
from threading import Thread, Lock
from timeit import default_timer
from jsonrpcclient.http_client import HTTPClient
from jsonrpcclient.request import Request
from setproctitle import setproctitle
import pickle as data

import eventlet
import telebot
import yaml
from telebot import types
from flask import Flask, render_template, request, Response, abort
from sqlalchemy import cast, Date, or_, distinct
from sqlalchemy.sql.expression import func

from app.database import init_database, init_manager, db
from app.emoji import clean_up
from app.markup import *
from app.models import User, Branch, Manager, Anonymous, Announcement, SyncTime, Feedback
from app.strings import Strings
from app.barcode import get_barcode
from app.syncer import Syncer

app = Flask(__name__)
root = path.dirname(path.abspath(__file__))

with app.open_resource('app.yaml', 'r') as stream:
    config = yaml.load(stream)

with open(root+'/database/where.pickle', 'rb') as f:
    where = data.load(f)

db_path = path.join(path.dirname(__file__), config['database']['name'])
syncer = Syncer(
    app,
    path=config['sync']['file'],
    cache_path=config['sync']['cache_file'],
)

channel_id = config['feedback']['channel_id']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = config['server']['echo']

app.secret_key = config['server']['secret']
bot = telebot.TeleBot(config['bot']['token'], threaded=True)
telebot.logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
logger.setLevel(logging.INFO)

chats = set()
chats_lock = Lock()



def authenticate():
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def timer():
    return default_timer() * 1000


def check_auth(username, password):
    return username == config['server']['username'] and password == config['server']['password']


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def non_command(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        text = getattr(args[0], 'text', None)
        if text and telebot.util.is_command(text):
            return
        return f(*args, **kwargs)

    return decorated


@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if is_manager(message.chat.id):
        bot.send_message(
            message.chat.id, 'Отправьте изображение', parse_mode='HTML')
        bot.register_next_step_handler(message, broadcast_image_handler)


def show_stats(message):
    with app.app_context():
        chat_id = message.chat.id

        if is_manager(chat_id):
            usernum = User.query.filter(User.user_id.isnot(None)).count()
            anonnum = Anonymous.query.count()

            send_main_menu(
                chat_id,
                'Количество зарегистрированых пользователей: <b>{}</b>\n' \
                'Общее число пользователей: <b>{}</b>'.format(usernum, anonnum))


@bot.message_handler(commands=['stats'])
def users_number(message):
    show_stats(message)


@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    chat_id = message.chat.id
    where[message.from_user.id] = 'AnyWhere'
    with open(root+'/database/where.pickle', 'wb') as f:
        data.dump(where, f)
    mes = message.text.split('d')
    if mes[0] == '/start fee' and len(mes) == 2:
        feed_id = message.text.split('d')
        where[message.from_user.id] = 'anwer:{}'.format(feed_id[1])
        with open(root+'/database/where.pickle', 'wb') as f:
           data.dump(where, f)
        markup = types.ReplyKeyboardMarkup()
        markup.row('Отменить')
        bot.send_message(message.chat.id, 'Напишите и отправьте сообщение, которое будет отправлено клиенту.', reply_markup = markup)
    else:
        is_new_chat = False
        with chats_lock:
            if chat_id not in chats:
                chats.add(chat_id)
                is_new_chat = True
        if is_new_chat:
            with app.app_context():
                if Anonymous.query.filter_by(chat_id=chat_id).first() is None:
                    db.session.add(Anonymous(chat_id))
                    db.session.commit()

        send_main_menu(chat_id,
                       Strings.WELCOME.format(message.from_user.first_name,
                                              config['company']['name']))


@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.chat.id
    if where[message.from_user.id][:5] == 'anwer':
        if message.text == 'Отменить':
            where[message.from_user.id] = 'AnyWhere'
            with open(root+'/database/where.pickle', 'wb') as f:
                data.dump(where, f)
            handle_message(message)
        else:
            feed_id = where[message.chat.id].split(':')
            where[message.from_user.id] = 'AnyWhere'
            with open(root+'/database/where.pickle', 'wb') as f:
                data.dump(where, f)
            bot.send_message(feed_id[1], message.text)
            bot.send_message(message.chat.id, 'Готово! Сообщение отправлено клиенту!')
            handle_message(message)
    else:
        is_new_chat = False
        with chats_lock:
            if chat_id not in chats:
                chats.add(chat_id)
                is_new_chat = True

        # print('first_name: {}'.format(message.from_user.first_name))
        # print('chat_id: {}'.format(message.chat.id))
        # print('user_id: {}'.format(message.from_user.id))

        if is_new_chat:
            with app.app_context():
                if Anonymous.query.filter_by(chat_id=chat_id).first() is None:
                    db.session.add(Anonymous(chat_id))
                    db.session.commit()

            send_main_menu(chat_id,
                           Strings.WELCOME.format(message.from_user.first_name,
                                                  config['company']['name']))
            return
        send_main_menu(chat_id, Strings.MAIN)

@bot.message_handler(content_types=['photo'])
def assign_image(message):
    uid = str(message.from_user.id)
    mx = 0
    mxid = 0
    for _, msg in enumerate(message.photo):
        if mx < msg.file_size:
            mx = msg.file_size
            mxid = msg.file_id
    name = '' if not message.caption else message.caption
    bot.send_photo(uid, mxid, mxid + '\n' + name, disable_notification=True)


def debug(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(e)

    return decorated


def is_manager(chat_id):
    with app.app_context():
        return Manager.query.filter_by(user_id=chat_id).count() > 0


@debug
def broadcast_image_handler(message):
    if message.content_type == 'photo':
        image = message.photo[-2].file_id
        bot.send_message(message.chat.id, 'Отправить текст', parse_mode='HTML')
        bot.register_next_step_handler(
            message, lambda msg: broadcast_text_handler(msg, image))
    else:
        bot.clear_step_handler(message)
        bot.register_next_step_handler(message, broadcast_image_handler)


@debug
def broadcast_text_handler(message, image):
    if message.content_type == 'text':
        bot.send_chat_action(message.chat.id, 'typing')
        with app.app_context():
            chat_ids = [u.chat_id for u in Anonymous.query.all()]
            if chat_ids:
                print(len(chat_ids))
                Thread(
                    target=send_broadcast,
                    args=[chat_ids, image, message.text]).start()
        send_main_menu(message.chat.id, 'Рассылка завершена!')
    else:
        bot.clear_step_handler(message)
        bot.register_next_step_handler(
            message, lambda msg: broadcast_text_handler(msg, image))


def send_main_menu(chat_id, text, barcode=None, barcode_text=None):
    mes = text.split('d')
    if mes[0] == '/start fee' and len(mes) == 2:
        feed_id = text.split('d')
        where[chat_id] = 'anwer:{}'.format(feed_id[1])
        with open(root+'/database/where.pickle', 'wb') as f:
           data.dump(where, f)
        markup = types.ReplyKeyboardMarkup()
        markup.row('Отменить')
        bot.send_message(chat_id, 'Напишите и отправьте сообщение, которое будет отправлено клиенту.', reply_markup = markup)
    else:
        main_menu_markup = build_main_menu_markup()

        if is_manager(chat_id):
            main_menu_markup.add(Strings.BROADCAST, Strings.STATS)

        if barcode:
            bot.send_photo(
                chat_id,
                barcode,
                caption=barcode_text,
                disable_notification=True,
                reply_markup=main_menu_markup)

        msg = bot.send_message(
            chat_id,
            text,
            reply_markup=main_menu_markup,
            disable_notification=True,
            parse_mode='HTML')

        bot.clear_step_handler(msg)
        bot.register_next_step_handler(msg, handle_main_menu)


def handle_main_menu(message):
    mes = message.text.split('d')
    if mes[0] == '/start fee' and len(mes) == 2:
        feed_id = message.text.split('d')
        where[message.from_user.id] = 'anwer:{}'.format(feed_id[1])
        with open(root+'/database/where.pickle', 'wb') as f:
           data.dump(where, f)
        markup = types.ReplyKeyboardMarkup()
        markup.row('Отменить')
        bot.send_message(message.chat.id, 'Напишите и отправьте сообщение, которое будет отправлено клиенту.', reply_markup = markup)
    else:
        with app.app_context():
            chat_id = message.chat.id
            command = clean_up(message.text)

            if is_manager(chat_id):
                if command in [Strings.STATS, '/stats']:
                    show_stats(message)
                    return
                elif command in [Strings.BROADCAST, '/broadcast']:
                    broadcast_command(message)
                    return

            if command == Strings.BRANCHES:
                send_branches(message)
                send_main_menu(chat_id, Strings.MAIN)
            elif command == Strings.NEWS:
                send_announcement(message, 0)
            elif command == Strings.CARD:
                send_card(message)
            elif command == Strings.FEEDBACK:
                send_feedback(message)
            else:
                send_main_menu(chat_id, Strings.MAIN)


def send_feedback(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(back_button)
    bot.send_message(message.chat.id,
        Strings.FEEDBACK_MESSAGE,
        reply_markup=markup,
        parse_mode='HTML',
        disable_notification=True)

    bot.clear_step_handler(message)
    bot.register_next_step_handler(message, handle_feedback)


def handle_feedback(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    text = message.text

    if clean_up(text) == Strings.BACK:
        send_main_menu(chat_id, Strings.MAIN)
        return

    with app.app_context():
        feedback = Feedback(user_id, first_name, text,
            last_name=last_name, nickname=username)

        db.session.add(feedback)
        db.session.commit()
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('Ответить', 't.me/MiniMe_uzbot?start=feed{}'.format(str(user_id))))
        bot.send_message(channel_id, str(feedback),
            parse_mode='HTML', reply_markup = markup,disable_notification=True)

    send_main_menu(chat_id, Strings.FEEDBACK_SUCCESS)


def send_announcement(message, offset, prev_offset=0):
    chat_id = message.chat.id

    with app.app_context():
        count = Announcement.query.count()
        back = count - offset < count
        forward = count - offset > 1

        if count > 0:
            msg = message
            announcement = Announcement.query.order_by(
                Announcement.id_.desc()).offset(offset).limit(1).first()
            if announcement is not None:
                if announcement.photo:
                    bot.send_photo(
                        chat_id, announcement.photo, disable_notification=True)
                msg = bot.send_message(
                    chat_id,
                    announcement.text,
                    disable_notification=True,
                    reply_markup=build_announcement_markup(back, forward))
            else:
                send_announcement(message, prev_offset)

            bot.register_next_step_handler(
                msg, lambda m: handle_announcement(m, offset, back, forward))
        else:
            send_main_menu(chat_id, Strings.NO_NEWS)


def handle_announcement(message, offset, back, forward):
    chat_id = message.chat.id
    cmd = clean_up(message.text)

    if cmd == Strings.FORWARD and forward:
        send_announcement(message, offset + 1, offset)
    elif cmd == Strings.BACK and back:
        send_announcement(message, offset - 1, offset)
    elif cmd == Strings.MENU:
        send_main_menu(chat_id, Strings.MAIN)
    else:
        send_announcement(message, offset)


def send_card(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = User.query.filter_by(user_id=user_id).first()
    if user is None:
        request_phone_number(message)
        return
    else:
        with app.app_context():
            text = str(SyncTime.query.first())
            text += str(user)
            barcode_text = 'Номер карты: {}\n'.format(user.barcode)

            send_main_menu(chat_id, text, get_barcode(user.barcode),
                           barcode_text)


def send_branches(message):
    msg = message
    chat_id = message.chat.id
    start = timer()
    branches = Branch.query.all()
    logger.debug('branches.all %d ms', timer() - start)

    main_menu_markup = build_main_menu_markup()

    bot.send_message(
        chat_id,
        'Наши адреса',
        disable_notification=True,
        reply_markup=main_menu_markup)

    for branch in branches:
        text = str(branch)
        if branch.image:
            msg = bot.send_photo(
                chat_id,
                branch.image,
                text,
                disable_notification=True,
                reply_markup=main_menu_markup)
        else:
            msg = bot.send_message(
                chat_id,
                text,
                disable_notification=True,
                parse_mode='HTML',
                reply_markup=main_menu_markup)
        if branch.location:
            msg = bot.send_location(
                chat_id,
                branch.location.latitude,
                branch.location.longitude,
                disable_notification=True,
                reply_markup=main_menu_markup)
    bot.register_next_step_handler(msg, handle_main_menu)


def request_phone_number(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id,
        emoji['iphone'] + Strings.PHONE,
        reply_markup=contact_markup,
        parse_mode='HTML')

    bot.clear_step_handler(msg)
    bot.register_next_step_handler(msg, handle_phone_number)


def handle_phone_number(message):
    with app.app_context():
        chat_id = message.chat.id
        if message.content_type == 'contact':
            phone_number = message.contact.phone_number
            if phone_number[0] == '+':
                phone_number = phone_number.replace('+', '')

            user = User.query.filter_by(phone_number=phone_number).first()
            if user is None:
                send_main_menu(chat_id, Strings.REJECT_AUTH)
                return

            user.user_id = message.from_user.id

            db.session.commit()

        elif message.content_type == 'text':
            text = clean_up(message.text)
            if text == Strings.SEND_PHONE:
                msg = bot.send_message(
                    chat_id,
                    Strings.VERSION,
                    parse_mode='HTML',
                    reply_markup=contact_markup)
                bot.register_next_step_handler(msg, handle_phone_number)
                return

            if text == Strings.BACK:
                send_main_menu(chat_id, Strings.MAIN)
                return
        else:
            request_phone_number(message)
            return

        send_card(message)


def send_broadcast(chat_ids, image, text):
    count = 0

    with app.app_context():
        db.session.add(Announcement(text, image))
        db.session.commit()

    if not chat_ids:
        return
    for chat_id in chat_ids:
        try:
            if image:
                bot.send_photo(chat_id, image, disable_notification=True)
            if text:
                bot.send_message(chat_id, text, disable_notification=True)
            count += 1
        except Exception:
            pass
    logger.info('send_broadcast %d/%d', count, len(chat_ids))


@app.route('/', methods=['POST'])
def web_hook():
    if request.headers.get('content-type') == 'application/json':
        data = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(data)
        if update.message:
            bot.process_new_messages([update.message])
        if update.inline_query:
            bot.process_new_inline_query([update.inline_query])
        return ''
    abort(403)


@app.route('/sync', methods=['POST', 'GET'])
def api_sync():
    try:
        syncer.sync()
    except:
        pass
    return '', 200


def bot_polling():
    bot.remove_webhook()
    bot.polling(False)


def main(argv):
    if len(argv) > 0:
        init_manager(app)
        return
    else:
        init_database(app)

    syncer.sync()
    syncer.schedule()

    setproctitle(config['company']['name'])
    if config['bot']['polling']:
        logger.info('starting polling...')
        thread = Thread(target=bot_polling)
        thread.start()
    else:
        logging.info('setting webhook...')
        bot.remove_webhook()
        bot.set_webhook(config['bot']['webhook'])
    me = bot.get_me()
    logger.info('Me: %s @%s', me.first_name, me.username)
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug'])


if __name__ == '__main__':
    main(sys.argv[1:])

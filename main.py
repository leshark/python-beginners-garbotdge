#/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shelve
import time

from requests.exceptions import ConnectionError, ReadTimeout

import config
from commands import monitor, new_users, report
from utils import bot, logger, validate_command, watching_newcommers


# Handler for banning invited user bots
@bot.message_handler(content_types=['new_chat_members'])
def ban_invited_bots(message):
    if not validate_command(message, check_chat=True):
        return

    new_users.ban_bots(message)


# Handler for initializing a chat's admin
@bot.message_handler(commands=['start'])
def start_msg(message):
    if not validate_command(message, check_isprivate=True, check_isadmin=True):
        return

    bot.reply_to(message, "Сюда будут пересылаться репорты из чата.")
    logger.info("Admin {} called /start".format(message.from_user.id))


@bot.message_handler(content_types=['text'])
def report_to_admins(message):
    if message.text.lower().startswith('!report'):
        if not validate_command(message, check_isreply=True):
            bot.reply_to(message, "Кого репортим?")
        else:
            report.my_report(message)

    if watching_newcommers(message.from_user.id):
        monitor.scan_contents(message)


@bot.message_handler(content_types=['sticker', 'photo', 'audio',\
                        'document', 'video', 'voice', 'video_note'])
def scan_for_spam(message):
    if watching_newcommers(message.from_user.id):
        monitor.scan_contents(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = int(call.message.text.split(' ')[3])
    message_id = int(call.message.text.split(' ')[7])

    with shelve.open(config.data_name, 'c', writeback=True) as data:
        data['reported_ids'] = [] if not data.get('reported_ids') else data['reported_ids']
        data['pending_ids'] = [] if not data.get('pending_ids') else data['pending_ids']

        if message_id not in data['pending_ids']:
            bot.reply_to(call.message, "Это сообщение уже отмодерировано.")
            return

        if call.data == 'ban':
            bot.kick_chat_member(chat_id=config.chat_id, user_id=user_id)
        elif call.data == 'release':
            bot.unban_chat_member(chat_id=config.chat_id, user_id=user_id)

        data['pending_ids'].remove(message_id)


while __name__ == '__main__':
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except ConnectionError:
        logger.exception("ConnectionError")
        time.sleep(15)
    except ReadTimeout:
        logger.exception("ReadTimeout")
        time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Good-bye")
        os._exit(0)
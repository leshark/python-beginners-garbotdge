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
    if not validate_command(message, check_isinchat=True):
        return

    new_users.ban_bots(message)


# Handler for initializing a chat's admin
@bot.message_handler(commands=['start'])
def start_msg(message):
    if not validate_command(message, check_isprivate=True, check_isadmin=True):
        return

    bot.reply_to(message, "Сюда будут пересылаться репорты из чата.")
    logger.info("Admin {} called /start".format(message.from_user.id))


# Handler for reporting spam to a chat's admins
@bot.message_handler(func=lambda m: m.chat.type != 'private' and m.text and\
                         m.text.lower().startswith('!report'))
def report_to_admins(message):
    if not validate_command(message, check_isreply=True):
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return

    report.my_report(message)


# Handler for monitoring messages of users who have <= 10 posts
@bot.message_handler(content_types=['text', 'sticker', 'photo', 'audio',\
                        'document', 'video', 'voice', 'video_note'])
def scan_for_spam(message):
    if watching_newcommers(message.from_user.id):
        monitor.scan_contents(message)


# Callback handler for the admins' judgment
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
            bot.restrict_chat_member(chat_id=config.chat_id, user_id=user_id,\
                can_send_messages=True, can_send_media_messages=True,\
                can_send_other_messages=True, can_add_web_page_previews=True)

        data['pending_ids'].remove(message_id)


# Entry point
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

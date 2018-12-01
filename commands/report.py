#/usr/bin/env python3
# -*- coding: utf-8 -*-
import shelve
import time

from telebot.apihelper import ApiException

import config
from utils import bot, logger, get_user


def my_report(message):
    """Handles users' reports
    """

    with shelve.open(config.data_name, 'c', writeback=True) as data:
        data['reported_pending'] = [] if not data.get('reported_pending') else data['reported_pending']
        data['report_ro_span'] = [time.time(), time.time()+60*config.ro_span_mins, 1]\
                                if not data.get('report_ro_span') else data['report_ro_span']

        # If time limit in which user's could get RO'd expires, starts a new span
        if time.time() > data['report_ro_span'][1]:
            data['report_ro_span'] = [time.time(), time.time()+60*config.ro_span_mins, 1]

        if message.reply_to_message.message_id in data['reported_pending']:
            data['reporters'] = {} if not data.get('reporters') else data['reporters']
            ro_giver(message, data['reporters'], data['report_ro_span'][2])
        else:
            report_to_admins(message)
            data['reported_pending'].append(message.reply_to_message.message_id)

        data['report_ro_span'][2] += 1


def ro_giver(message, db, count):
    """Gives RO to users who flood with the !report command,
    or bans those who have more than 3 warnings
    """

    if count <= config.report_limit:
        return

    user = message.from_user
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    db[user.id] = 0 if not db.get(user.id) else db[user.id]
    user_ro_status = config.ro_list[db[user.id]]
    if user_ro_status.isdigit():
        bot.restrict_chat_member(chat_id=config.chat_id, user_id=user.id,\
                until_date=time.time() + 60*int(user_ro_status))
        db[user.id] += 1
        logger.info("User {0} got {1} minutes of RO for flooding with !report".\
            format(get_user(user), user_ro_status))
    else:
        bot.kick_chat_member(chat_id=config.chat_id, user_id=user.id)
        del db[user.id]
        logger.info("User {} has been banned for flooding with !report".\
            format(get_user(user)))


def report_to_admins(message):
    """Sends a link to a user's reported message to the admins
    """

    from_chat = bot.get_chat(message.chat.id)
    from_chat_name = from_chat.username
    reported_id = message.reply_to_message.message_id
    reported_link = "https://t.me/{0}/{1}".format(from_chat_name, reported_id)

    for admin_id in config.admin_ids:
        try:
            bot.send_message(admin_id, reported_link)
        except ApiException as e:
            if str(e.result) == config.unreachable_msg:
                continue

    logger.info("Message {} has been reported to the admins".\
                format(message.reply_to_message.message_id))

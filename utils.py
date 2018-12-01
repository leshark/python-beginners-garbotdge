#/usr/bin/env python3
# -*- coding: utf-8 -*-
import functools
import logging
import shelve

import telebot
from telebot.apihelper import ApiException

import config

# Initializes the bot
bot = telebot.TeleBot(config.bot_token, threaded=False)
bot_id = bot.get_me().id

# Initializes the logger
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)


def get_user(user):
    """Returns a string with user's info in
    'ID First_name Last_name (@user_name)' format
    """

    user_info = '{0} {1}'.format(user.id, user.first_name)
    if user.last_name:
        user_info += ' {}'.format(user.last_name)
    if user.username:
        user_info += ' (@{})'.format(user.username)
    return user_info


def validate_command(message, check_isprivate=False, check_isinchat=False, check_isreply=False,\
                        check_isadmin=False):
    """Checks whether a command was called properly
    """

    if check_isprivate and message.chat.type != 'private':
        logger.info("User {0} called {1} not in a private chat. Aborting".\
                        format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    if check_isinchat and message.chat.id != config.chat_id:
        logger.info("We are not in our chat. Aborting")
        return False

    if check_isreply and getattr(message, 'reply_to_message') is None:
        logger.info("User {0} called {1} the wrong way".\
                        format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    if check_isadmin and message.from_user.id not in config.admin_ids:
        logger.info("User {0} tried to call {1}. Aborting".\
                        format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    return True


def watching_newcommers(user_id):
    """Checks if a user with user_id that has posted a message requires scanning
    i.e. whether the user has posted less than 10 messages
    """

    with shelve.open(config.data_name, 'c', writeback=True) as data:
        data['members'] = {} if not data.get('members') else data['members']
        if not data['members'].get(user_id):
            data['members'][user_id] = 0
        elif data['members'][user_id] > 10:
            return False

        data['members'][user_id] += 1
        return True


def get_chat_id(chat):
    """Returns a chat's id
    """

    return bot.get_chat(chat).id


def get_admins(chat):
    """Returns a list of chat admins' ids
    """

    return [admin.user.id for admin in bot.get_chat_administrators(chat) if not admin.user.is_bot]


def enough_rights(func):
    """Checks whether the bot has enough rights to execute the called func
    """

    @functools.wraps(func)
    def wrapper(message):
        if bot_id not in [admin.user.id for admin in bot.get_chat_administrators(config.chat_name)]:
            logger.info("Bot is not an admin. Aborting")
            return
        for admin_id in get_admins(config.chat_name):
            try:
                bot.send_chat_action(chat_id=admin_id, action='typing')
                return func(message)
            except ApiException as e:
                if str(e.result) == config.unreachable_exc:
                    continue
        logger.info("Bot can not contact any of the admins. Foreveralone")
        return

    return wrapper

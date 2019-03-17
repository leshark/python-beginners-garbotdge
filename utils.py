import logging
import os

import random
import requests
import telebot

import config
from models import Session, User

# Initializes the bot
bot = telebot.TeleBot(config.bot_token, threaded=False)
bot_id = bot.get_me().id

# Initializes the logger
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)


def validate_document(message):
    if message.document:
        file_name = message.document.file_name or ''
        file_size = message.document.file_size
        return os.path.splitext(file_name)[-1] in config.EXTENSIONS and file_size <= config.MAX_FILE_SIZE


def validate_paste(message):
    action = message.text
    source = message.reply_to_message
    if source and action:
        content = source.text or source.caption
        return content and action.lower() == '!paste'


def make_paste(content, holder, file_name='main.py'):
    headers = {'Authorization': f'token {config.GIT_TOKEN}'}
    payload = {
        'description': f'From: {holder}',
        'public': True,
        'files': {
            file_name: {
                'content': content
            }
        }
    }
    response = requests.post(config.PASTE_URL, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()['html_url']


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


def validate_command(message, check_isprivate=False, check_isinchat=False, check_isreply=False,
                     check_isadmin=False):
    """Checks whether a command was called properly
    """

    if check_isprivate and message.chat.type != 'private':
        logger.info("User {0} called {1} not in a private chat. Aborting".
                    format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    if check_isinchat and message.chat.id != get_chat_id(config.chat_name):
        logger.info("We are not in our chat. Aborting")
        return False

    if check_isreply and getattr(message, 'reply_to_message') is None:
        logger.info("User {0} called {1} the wrong way".
                    format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    if check_isadmin and message.from_user.id not in config.admin_ids:
        logger.info("User {0} tried to call {1}. Aborting".
                    format(get_user(message.from_user), message.text.split(' ')[0]))
        return False

    return True


def watching_newcommers(user_id):
    """Checks if a user with user_id that has posted a message requires scanning
    i.e. whether the user has posted less than 10 messages
    """

    session = Session()

    user_obj = session.query(User).get(user_id)
    if not user_obj:
        user_obj = User(user_id)
        session.add(user_obj)
    elif user_obj.msg_count > 10:
        session.close()
        return False

    user_obj.msg_count += 1
    session.commit()
    session.close()
    return True


def perfect_justice():
    """give user Read only with 1/6 chance
    """
    return random.choice((False, False, False, False, False, True))


def get_chat_id(chat):
    """Returns a chat's id
    """

    return bot.get_chat(chat).id


def get_admins(chat):
    """Returns a list of chat admins' ids
    """

    return [admin.user.id for admin in bot.get_chat_administrators(chat) if not admin.user.is_bot]

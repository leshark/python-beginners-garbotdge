from telebot import types
from telebot.apihelper import ApiException

import config
from config import r
from models import Session, User
from utils import bot, logger, get_user


def scan_contents(message):
    """Scans message's contents.
    calls punisher() upon detection of threat
    """

    if message.forward_from_chat:
        if message.forward_from_chat.type == 'channel' and \
        message.forward_from_chat.id not in config.whitelist_channels:
            punisher(message)
            return

    if message.entities:
        if forbidden_entities(message):
            punisher(message)


def forbidden_entities(message):
    """Checks for message's entities that could lead to a channel
    """

    # Encodes the message so any potential emojis can't mess up entities' offsets
    msg_enc = message.text.encode('utf-16le')

    for entity in message.entities:
        entity_text = msg_enc[2 * entity.offset:2 * (entity.offset + entity.length)].decode('utf-16le')
        if entity.type == 'url':
            if '/joinchat/' in entity_text:
                logger.info("Message {} has a channel link in an URL entity". \
                            format(message.message_id))
                return True
        elif entity.type == 'text_link':
            if '/joinchat/' in entity.url:
                logger.info("Message {} has a channel link in a text-link entity". \
                            format(message.message_id))
                return True
        elif entity.type == 'mention':
            if bot.get_chat(entity_text).type == 'channel':
                logger.info("Message {} has a channel link in a mention entity". \
                            format(message.message_id))
                return True

    return False


def punisher(message):
    """Gives RO to user who posted the message,
    deletes the message from chat,
    forwards the deleted message to the admins,
    triggers judgment buttons
    """

    session = Session()
    user_obj = session.query(User).get(message.from_user.id)
    if not user_obj:
        user_obj = User(message.from_user.id)
        session.add(user_obj)
    else:
        user_obj.msg_count -= 1
    session.commit()
    session.close()

    if r.get("spammer_{}".format(message.from_user.id)):
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        logger.info("Message {} has been deleted without alerting the admins due to flooding".format(message.message_id))
        return

    if message.from_user.id not in config.admin_ids:
        bot.restrict_chat_member(chat_id=config.chat_id, user_id=message.from_user.id)
        logger.info("User {} has been restricted for leading to a channel" \
                    .format(get_user(message.from_user)))

    r.set(message.message_id, 1)
    r.set("spammer_{}".format(message.from_user.id), 1, ex=config.spammer_timeout)

    judgement_text = "Reported user's ID: {} \n" \
                     "Reported message's ID: {} \n" \
                     "Что будем делать?".format(message.from_user.id, message.message_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_ban = types.InlineKeyboardButton(text="Отправить в бан", callback_data='ban')
    btn_release = types.InlineKeyboardButton(text="Снять РО", callback_data='release')
    keyboard.add(btn_ban, btn_release)

    for admin_id in config.admin_ids:
        try:
            reported = bot.forward_message(chat_id=admin_id, from_chat_id=config.chat_id, \
                                           message_id=message.message_id)
            bot.reply_to(reported, judgement_text, reply_markup=keyboard)
        except ApiException as e:
            if str(e.result) == config.unreachable_exc:
                continue

    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    logger.info("Message {} has been successfully auto-reported".format(message.message_id))

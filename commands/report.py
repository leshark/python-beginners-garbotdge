import time
from threading import Timer

from telebot.apihelper import ApiException

import config
from config import r
from models import Session, User
from utils import bot, logger, get_user


def my_report(message):
    """Handles users' reports
    """
    if not r.get(message.reply_to_message.message_id):
        report_to_admins(message)
        r.set(message.reply_to_message.message_id, 1, ex=60 * config.ro_span_mins)
        response = bot.send_message(chat_id=message.chat.id, text='Мы примем все необходимые меры, спасибо.')
        Timer(30, bot.delete_message, kwargs={
            'chat_id': response.chat.id, 'message_id': response.message_id
        }).start()
    elif r.incr(message.reply_to_message.message_id) >= config.report_threshold:
        ro_giver(message, r)


def ro_giver(message, r):
    """Gives RO to users who flood with the !report command,
    or bans those who have more than 3 warnings
    """

    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if int(r.get(message.reply_to_message.message_id)) == config.report_threshold:
        return

    session = Session()

    user_obj = session.query(User).get(message.from_user.id)
    if not user_obj:
        user_obj = User(message.from_user.id)
        session.add(user_obj)
        session.commit()

    if message.from_user.id in config.admin_ids:
        logger.info("Admin {} is flooding with !report. Doing nothing". \
                    format(get_user(message.from_user)))
        session.close()
        return

    user_obj.ro_level += 1
    session.commit()

    if user_obj.ro_level < 4:
        user_ro_minutes = config.ro_levels[user_obj.ro_level]
        bot.restrict_chat_member(chat_id=config.chat_id, user_id=message.from_user.id, \
                                 until_date=time.time() + 60 * user_ro_minutes)
        logger.info("User {0} got {1} minutes of RO for flooding with !report". \
                    format(get_user(message.from_user), user_ro_minutes))
    else:
        bot.kick_chat_member(chat_id=config.chat_id, user_id=message.from_user.id)
        session.delete(user_obj)
        logger.info("User {} has been banned for flooding with !report". \
                    format(get_user(message.from_user)))

    session.close()


def report_to_admins(message):
    """Sends a link to a user's reported message with a reporter's reason to the admins
    """

    from_chat = config.chat_name[1:]
    reported_id = message.reply_to_message.message_id
    reason = message.text.split(maxsplit=1)
    reported_msg = "https://t.me/{0}/{1}\n{2}".format(from_chat, reported_id,
                                                       reason[1][:30] if len(reason) > 1 else '')

    for admin_id in config.admin_ids:
        try:
            bot.send_message(admin_id, reported_msg)
        except ApiException as e:
            if str(e.result) == config.unreachable_exc:
                continue
    logger.info("Message {} has been successfully reported".format(message.reply_to_message.message_id))

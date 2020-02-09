import threading
import time

import redis
import requests
import telebot

import config


bot = telebot.TeleBot(config.BOT_TOKEN)
storage = redis.Redis(host='localhost', password=config.REDIS_PASS, port=6379, db=0)


@bot.message_handler(func=lambda msg: msg.chat.id in config.CHAT_IDS, content_types=['new_chat_members'])
def spam_checker(msg):
    user_id = msg.new_chat_member.id
    cas = requests.get('https://api.cas.chat/check', params={'user_id': user_id})
    result = cas.json()
    if result['ok'] or config.DEBUG_MODE:
        try:
            bot.kick_chat_member(msg.chat.id, user_id)
        except Exception as exception:
            print(exception)


def message_forwarder():
    while True:
        for chat_id in config.CHAT_IDS:
            previous = storage.get(f'msg:{chat_id}')
            if previous:
                bot.delete_message(chat_id, previous)
            message = bot.forward_message(
                chat_id=chat_id,
                from_chat_id=config.FORWARD_FROM,
                message_id=config.MESSAGE_ID
            )
            storage.set(f'msg:{chat_id}', message.message_id)
            time.sleep(.100)
        time.sleep(config.INTERVAL)


if __name__ == '__main__':
    threading.Thread(target=message_forwarder).start()
    bot.polling(none_stop=True)

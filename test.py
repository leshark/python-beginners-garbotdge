from telebot import TeleBot
import requests
import os



PASTE_URL = 'https://api.github.com/gists'
token = '650806688:AAGMVuB-I1zoIgmAFJKF7WsONiSiinHQWgc'
G = 'd1d9db3f435c1298a1114fe9f6c52e3204a52080'
bot = TeleBot(token)


def make_paste(content, holder):
    headers = {'Authorization': f'token {G}'}
    payload = {
        'description': f'From: {holder}',
        'public': True,
        'files': {
            'main.py': {
                'content': content.decode()
            }
        }
    }
    response = requests.post(PASTE_URL, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()['html_url']


@bot.message_handler(content_types=['document'])
def foo(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    print(os.path.splitext(file_info.file_path))
    print(downloaded_file)
    print(file_info)


bot.polling()
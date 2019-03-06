import argparse
import os

import redis

import tokens

filtered = ['picua']
bot_token = tokens.bot  # set your token in .bashrc (see tokens.py)
chat_name = '@ru_python_beginners'
MAX_FILE_SIZE = 1_000_000  # bytes
EXTENSIONS = ['.py', '.txt', '.json']
GIT_TOKEN = os.environ.get('GIT_TOKEN')
PASTE_URL = 'https://api.github.com/gists'
url = os.environ.get('DATABASE_URL')
r = redis.from_url(os.environ.get('REDIS_URL'))
whitelist_channels = [
    -1001120424883  # @best_of_ru_python
]
report_threshold = 2
spammer_timeout = 10
ro_span_mins = 60
ro_levels = {1: 5, 2: 30, 3: 120, 4: 'ban'}

unreachable_exc = r'<Response [403]>'

# Data for PostgreSQL
db_user_default = 'postgres'
db_password_default = ''

db_user = os.getenv('POSTGRESQL_USER', db_user_default)
db_password = os.getenv('POSTGRESQL_PASSWORD', db_password_default)
db_host = 'localhost'
db_port = 5432
db_name = 'testdb'

# Adds an option of running the bot in debug mode right from a console:
# `$ python3 main.py --debug`  OR  `$ python3 main.py -d`
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help='runs bot in debug mode', action='store_true')
args = parser.parse_args()
if args.debug:
    bot_token = tokens.bot_test  # set your token in .bashrc (see tokens.py)
    chat_name = '@pybegtest'
    r = redis.StrictRedis(host='localhost')
    url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    print("Running bot in debug mode")

# Automatically gets required ids depending on chat_name
from utils import get_admins, get_chat_id

chat_id = get_chat_id(chat_name)
admin_ids = get_admins(chat_name)

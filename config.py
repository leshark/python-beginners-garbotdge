#/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os

import tokens


bot_token = tokens.bot    # set your token in .bashrc (see tokens.py)
chat_name = '@ru_python_beginners'

path_dir = os.path.dirname(os.path.abspath(__file__))
data_name = path_dir + '/data/data'

ro_span_mins = 1
ro_list = ['5', '30', '120', 'ban']
report_limit = 3

unreachable_exc = r'<Response [403]>'

# Adds an option of running the bot in debug mode right from a console:
# `$ python3 main.py --debug`  OR  `$ python3 main.py -d`
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help='runs bot in debug mode', action='store_true')
args = parser.parse_args()
if args.debug:
    bot_token = tokens.bot_test  # set your token in .bashrc (see tokens.py)
    chat_name = '@pybegtest'
    print("Running bot in debug mode")


# Automatically gets required ids depending on chat_name
from utils import get_admins, get_chat_id

chat_id = get_chat_id(chat_name)
admin_ids = get_admins(chat_name)

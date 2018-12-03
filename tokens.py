import os


"""To set your API tokens via environmental variables
add the following lines to your .bashrc and restart bash by running $SHELL:
export PYBEG_BOT_TOKEN="XXXXX:XXXXXXXXXXX"
export PYBEG_BOT_TEST_TOKEN="XXXXX:XXXXXXXXXXX"
"""

default_bot = ''
bot = os.getenv('PYBEG_BOT_TOKEN', default_bot)
bot_test = os.getenv('PYBEG_BOT_TEST_TOKEN', default_bot)

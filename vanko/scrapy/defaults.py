import os

DEFAULT_BOT_NAME = 'scrapybot'
DEFAULT_PROJECT_DIR = os.path.join(os.path.expanduser('~'), '.vanko')
DEFAULT_SCRAPY_DIR = os.path.join(DEFAULT_PROJECT_DIR, 'scrapy')
DEFAULT_LOG_DIR = os.path.join(DEFAULT_PROJECT_DIR, 'logs')
ACTION_PARAMETER = 'ACTION'
ACTION_ARGUMENT = '--action='
PARAM_ARGUMENT = '--param='
DEFAULT_ACTION = 'crawl'
INITIAL_CWD = os.getcwd()

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


def is_on_bean_machine():
    return os.uname()[1] == 'beanmachine'


DIRECTORY = '/home/pi/episodes' if is_on_bean_machine() else os.environ.get('LOCALDIRECTORY')

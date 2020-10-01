from configparser import ConfigParser
import uuid

config = ConfigParser()

config.add_section('main')
config.set('main', 'CLIENT_ID', '')
config.set('main', 'API_KEY', '')
config.set('main', 'API_SECRET', '')
config.set('main', 'NONCE', str(uuid.uuid4()))

with open('configs/config.ini','w+') as f:
    config.write(f)

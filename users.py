import os
from dotenv import load_dotenv


load_dotenv(dotenv_path='../.envs/.env', verbose=True)

USERNAMES: list = os.getenv('USERNAMES').split(', ')

users: dict = {}
for username in USERNAMES:
    if username == '':  # or username == 'keksik_com_ua': continue
        continue
    load_dotenv(dotenv_path=f'../.envs/{username}.env', verbose=True, override=True)
    users.update({username: {
        'password': os.getenv('PASSWORD'),
        'seed': os.getenv('GOOGLE_AUTHENTICATOR_SEED'),
        'recovery_email': os.getenv('RECOVERY_EMAIL'),
        'recovery_email_password': os.getenv('RECOVERY_EMAIL_PASSWORD')}})

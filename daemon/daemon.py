#!/bin/python3

import os
import json
from time import sleep
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

load_dotenv(dotenv_path='../.envs/.env', verbose=True)

USERNAMES = os.getenv('USERNAMES').split(', ')

users = {}
for user in USERNAMES:
    if user == '': continue
    load_dotenv(dotenv_path=f'../.envs/{user}.env', verbose=True)
    users.update({user: os.getenv('PASSWORD')})

username = 'krasnikov.sergey.78'
password = users.get(username)

logger = logging.getLogger()


def login_user(username: str, password: str):
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    cl = Client()
    # adds a random delay between 1 and 3 seconds after each request
    cl.delay_range = [2, 5]

    try:
        session = cl.load_settings(path=f"../.sessions/{username}.json")
    except FileNotFoundError:
        session = None

    login_via_session = False
    login_via_pw = False

    if session:
        try:
            cl.set_settings(session)
            cl.login(username, password)

            # check if session is valid
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                logger.info("Session is invalid, need to login via username and password")

                old_session = cl.get_settings()

                # use the same device uuids across logins
                cl.set_settings({})
                cl.set_uuids(old_session["uuids"])

                cl.login(username, password)
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information: %s" % e)

    if not login_via_session:
        try:
            logger.info("Attempting to login via username and password. username: %s" % username)
            if cl.login(username, password):
                login_via_pw = True
                cl.dump_settings(f"../.sessions/{username}.json")
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:
        raise Exception("Couldn't login user with either password or session")

    return cl


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # pass
    # print_hi('PyCharm')

    cl = login_user(username=username, password=password)

    user_id = cl.user_id_from_username(username)

    print(user_id)
    print(type(user_id))
    threads_direct_messages = cl.direct_threads(amount=1)
    print(type(threads_direct_messages))
    print(threads_direct_messages)


    thread_last = threads_direct_messages[0]
    thread_last_messages = thread_last.messages
    for i, mess in enumerate(thread_last_messages):
        print(i, mess.text)

    messages = cl.direct_messages(int(thread_last.id))
    for i, msg in enumerate(messages):
        print(i, msg.text)

    followers = cl.user_followers(user_id=str(cl.user_id), amount=0)
    for i, follower in enumerate(followers):
        # print(i, type(follower))
        sleep(0.5)
        print(i, follower, cl.username_from_user_id(user_id=follower))

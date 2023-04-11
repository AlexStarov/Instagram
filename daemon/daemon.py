#!/bin/python3

import os
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

load_dotenv(dotenv_path='../envs/.env', verbose=True)

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

logger = logging.getLogger()


def login_user(username: str):
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    cl = Client()
    # adds a random delay between 1 and 3 seconds after each request
    cl.delay_range = [2, 5]

    try:
        session = cl.load_settings(f"../sessions/{username}.json")
    except FileNotFoundError:
        session = None

    login_via_session = False
    login_via_pw = False

    if session:
        try:
            cl.set_settings(session)
            cl.login(USERNAME, PASSWORD)

            # check if session is valid
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                logger.info("Session is invalid, need to login via username and password")

                old_session = cl.get_settings()

                # use the same device uuids across logins
                cl.set_settings({})
                cl.set_uuids(old_session["uuids"])

                cl.login(USERNAME, PASSWORD)
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information: %s" % e)

    if not login_via_session:
        try:
            logger.info("Attempting to login via username and password. username: %s" % USERNAME)
            if cl.login(USERNAME, PASSWORD):
                login_via_pw = True
                cl.dump_settings(f"../sessions/{username}.json")
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:
        raise Exception("Couldn't login user with either password or session")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # pass
    # print_hi('PyCharm')

    login_user(username=USERNAME)

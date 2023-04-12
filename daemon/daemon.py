#!/bin/python3

import os
import json
import asyncio
import random
from time import sleep

import instagrapi
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

load_dotenv(dotenv_path='../.envs/.env', verbose=True)

USERNAMES: list = os.getenv('USERNAMES').split(', ')

users: dict = {}
for user in USERNAMES:
    if user == '': continue
    load_dotenv(dotenv_path=f'../.envs/{user}.env', verbose=True)
    users.update({user: os.getenv('PASSWORD')})

username: str = 'krasnikov.sergey.78'
password: str = users.get(username)
user_id: int

logger = logging.getLogger()


async def login_user(username: str, password: str) -> instagrapi.Client:
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    print('login')
    print(datetime.now())
    print(username, password)

    cl = Client()
    # adds a random delay between 1 and 3 seconds after each request
    cl.delay_range = [2, 3]

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

    global user_id
    user_id = cl.user_id_from_username(username)
    print(f'{user_id=}')
    return cl

threads_direct_messages_dict: dict = {username: {} for username in users.keys() if username != ''}


async def threads_direct_messages(username: str, cl: instagrapi.Client):
    from pprint import pprint
    global threads_direct_messages_dict
    print('threads')
    print(datetime.now())
    print(username)

    threads_direct_messages_now = cl.direct_threads(amount=10)
    threads_direct_messages_old = threads_direct_messages_dict.get(username)
    if not threads_direct_messages_old:
        # TODO: это поведение в будующем нужно переделать, брать старое значение threads_direct_messages из базы
        """ Starting life from scratch """
        threads_direct_messages_dict[username] = threads_direct_messages_now
        return None

    if threads_direct_messages_old[0].id != threads_direct_messages_now[0].id or\
            threads_direct_messages_old[0].messages[0].id != threads_direct_messages_now[0].messages[0].id:
        """ Saving the current state """
        threads_direct_messages_dict.update({username: threads_direct_messages_now})

        threads_now_delete_list = []

        for n, thread_new in enumerate(threads_direct_messages_now):
            """ Checking the new and old list of threads """

            """ the case when we are looking for a new thread in the list of old threads """
            for i in range(len(threads_direct_messages_old)):
                thread_old = threads_direct_messages_old[i]
                # pprint(thread_new)
                # pprint(thread_old)
                if thread_old.id == thread_new.id and thread_old.messages[0].id == thread_new.messages[0].id:

                    # threads_old_delete_list.append(k)
                    threads_direct_messages_old.pop(i)
                    threads_now_delete_list.append(n)
                    break

        if len(threads_now_delete_list) > 0:

            threads_now_delete_list.reverse()
            for n in threads_now_delete_list:
                threads_direct_messages_now.pop(n)

            print(threads_direct_messages_now[0])
            print(threads_direct_messages_now[0].messages)
            print(threads_direct_messages_now[0].messages[0])
            print(threads_direct_messages_now[0].messages[0].item_type)
            print(threads_direct_messages_now[0].messages[0].text)

            print(f'{threads_direct_messages_now[0].users=}')
            print(f'{threads_direct_messages_now[0].inviter=}')

            print(f'{threads_direct_messages_now[0].users[0].pk=}')
            print(f'{threads_direct_messages_now[0].users[0].username=}')
            print(f'{(send_to := cl.user_id_from_username(username=threads_direct_messages_now[0].users[0].username))=}')
            print(threads_direct_messages_now[0].users)

            print(f'{threads_direct_messages_now[0].inviter.pk=}')
            print(f'{threads_direct_messages_now[0].inviter.username=}')
            print(f'{cl.user_id_from_username(username=threads_direct_messages_now[0].inviter.username)=}')
            print(threads_direct_messages_now[0].inviter)

            global user_id
            if threads_direct_messages_now[0].inviter.pk != user_id:
                if 'Я подписался'.lower() in threads_direct_messages_now[0].messages[0].text.lower():
                    print('ТЕСТОВАЯ СТРОКА')
                    cl.direct_send(text="Это отвечает БОТ: Я получил от тебя сообщение, что ты подписался, теперь мне нужно время, что-бы проверить это. Подожди немножко.", user_ids=[int(send_to), ])


    return None


async def process(username: str, password: str) -> None:
    print('process')
    print(datetime.now())
    print(username, password)
    cl = await login_user(username=username, password=password)
    await threads_direct_messages(username=username, cl=cl)


from datetime import datetime


async def main():
    n = 0
    while True:
        print(f'{(n := n + 1)=}')
        print('!!!', datetime.now())
        await asyncio.gather(*[process(username=username, password=password) for username, password in users.items()])
        print('@@@', datetime.now())

        sleep(random.uniform(5, 13))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # pass
    # print_hi('PyCharm')

    # cl = asyncio.run(login_user(username='krasnikov.sergey.78', password=users['krasnikov.sergey.78']))
    asyncio.run(main())

    # asyncio.sleep(random.uniform(25, 35))

    # user_id = cl.user_id_from_username(username)

    # print(user_id)
    # print(type(user_id))
        # threads_direct_messages = cl.direct_threads(amount=1)
        # print(type(threads_direct_messages))
        # print(threads_direct_messages)
        #
        #
        # thread_last = threads_direct_messages[0]
        # thread_last_messages = thread_last.messages
        # for i, mess in enumerate(thread_last_messages):
        #     print(i, mess.text)
        #
        # messages = cl.direct_messages(int(thread_last.id))
        # for i, msg in enumerate(messages):
        #     print(i, msg.text)
        #
        # followers = cl.user_followers(user_id=str(cl.user_id), amount=0)
        # for i, follower in enumerate(followers):
        #     # print(i, type(follower))
        #     sleep(0.5)
        #     print(i, follower, cl.username_from_user_id(user_id=follower))

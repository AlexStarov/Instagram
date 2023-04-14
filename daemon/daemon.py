#!/bin/python3

import os
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
for username in USERNAMES:
    if username == '' or username == 'keksik_com_ua': continue
    load_dotenv(dotenv_path=f'../.envs/{username}.env', verbose=True, override=True)
    users.update({username: {'password': os.getenv('PASSWORD')}})

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
    cl.delay_range = [2, 6]

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


async def threads_direct_messages(username: str, user_dict: dict):
    from pprint import pprint
    print('threads')
    print(datetime.now())
    print(username)

    cl = user_dict.get('cl')
    threads_direct_messages_now = cl.direct_threads(amount=10)
    threads_direct_messages_old = user_dict.get('threads_direct_messages')
    if not threads_direct_messages_old:
        # TODO: это поведение в будующем нужно переделать, брать старое значение threads_direct_messages из базы
        """ Starting life from scratch """
        user_dict['threads_direct_messages'] = threads_direct_messages_now
        return None

    if threads_direct_messages_old[0].id != threads_direct_messages_now[0].id or\
            threads_direct_messages_old[0].messages[0].id != threads_direct_messages_now[0].messages[0].id:
        """ Saving the current state """
        user_dict['threads_direct_messages'] = threads_direct_messages_now

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

            # print(f'{threads_direct_messages_now[0].users[0].pk=}')
            # print(f'{threads_direct_messages_now[0].users[0].username=}')
            # print(f'{(send_to := cl.user_id_from_username(username=threads_direct_messages_now[0].users[0].username))=}')
            # print(threads_direct_messages_now[0].users)
            #
            # print(f'{threads_direct_messages_now[0].inviter.pk=}')
            # print(f'{threads_direct_messages_now[0].inviter.username=}')
            # print(f'{cl.user_id_from_username(username=threads_direct_messages_now[0].inviter.username)=}')
            # print(threads_direct_messages_now[0].inviter)

            for thread in threads_direct_messages_now:

                # if thread.inviter.pk != user_id:
                for m, message in enumerate(thread.messages):
                    print(m, message)
                    print(m, message.text)
                    print(m, message.text.lower().startswith('Это отвечает БОТ:'.lower()))
                    if 'Я подписался'.lower() in message.text.lower() or\
                            'Я подписалась'.lower() in message.text.lower():

                        if m == 0 or \
                            (m > 0 and
                             message[m - 1].user_id != '7920069060' and
                             not message[m - 1].text.lower().startswith('Это отвечает БОТ:'.lower())):

                            checking_user_id = thread.users[0].pk
                            cl.direct_send(text="Это отвечает БОТ:\n"
                                                "Я получил от тебя сообщение, что ты подписался,"
                                                "теперь мне нужно время, что-бы проверить это.\n"
                                                "Подожди немножечко.", user_ids=[int(checking_user_id), ])

                            if await checking_user_id_among_followers(cl=cl, user_id=checking_user_id):
                                msg = "Это отвечает БОТ:\nДа ты просто ОГОНЬ.\n" \
                                      "Я нашёл тебя среди подписанных на меня.\n" \
                                      "Ты МАЛАДЕС.\n" \
                                      "Праздравляю тебя!!!"

                            else:
                                msg = "Это отвечает БОТ:\nЧёт ты гонишь фраерок.\n" \
                                      "Я не нашёл тебя среди подписанных на меня.\n" \
                                      "Ты меня в натуре разводишь....\n" \
                                      "А не пощёл бы ты...!!!"

                            cl.direct_send(text=msg, user_ids=[int(checking_user_id), ])

    return None


async def checking_user_id_among_followers(cl: instagrapi.Client, user_id: str) -> bool:

    followers: set = await get_followers(cl=cl)

    return user_id in followers


async def get_followers(cl: instagrapi.Client) -> set:

    return set(cl.user_followers(user_id=str(cl.user_id), amount=0))
    # for i, follower in enumerate(followers):
    #     print(i, follower, cl.username_from_user_id(user_id=follower))


from datetime import datetime


async def main():

    while True:
        for username in users.keys():
            print('!!!', datetime.now())

            user_dict: dict = users[username]

            if not user_dict.get('cl'):
                cl = await login_user(username=username, password=user_dict.get('password'))
                user_dict.update({'cl': cl, 'user_id': cl.user_id, 'username': cl.username})
                sleep(random.uniform(25, 35))

            await threads_direct_messages(username=username, user_dict=user_dict)

            print('@@@', datetime.now())

        sleep(random.uniform(7, 20))


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

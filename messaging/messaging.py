#!/bin/python3

from __future__ import absolute_import

import asyncio
import json
import random
from datetime import datetime
from time import sleep

import instagrapi
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, ClientError

from users import users
from auth.challenge import challenge_code_handler

import logging


logger = logging.getLogger()


async def login_user(username: str, password: str, seed: str = None) -> instagrapi.Client or None:
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
    cl.challenge_code_handler = challenge_code_handler

    try:
        session = cl.load_settings(path=f"../.sessions/{username}.json")
    except FileNotFoundError:
        session = None

    login_via_session = False
    login_via_pw = False
    login_via_TOTP = False

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

        sleep(random.uniform(5, 15))
        try:
            logger.info("Attempting to login via username and password. username: %s" % username)
            if cl.login(username, password):
                login_via_pw = True
                cl.dump_settings(f"../.sessions/{username}.json")
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:

        if seed:
            print('Trying to use 2FA trough Google Authenticator CODE !!!')

            sleep(random.uniform(5, 15))
            if cl.login(username, password, verification_code=cl.totp_generate_code(seed=seed)):
                login_via_TOTP = True
                cl.dump_settings(f"../.sessions/{username}.json")
            else:
                print("Couldn't login user with 2FA TOTP Google Authenticator CODE !!!")
        else:
            print("Couldn't login user with either password or session !!!")
            return

    if not login_via_pw and not login_via_session and not login_via_TOTP:
        # raise Exception("Couldn't login user with either password or session")
        print("Couldn't login user with either password or session or TOTP !!!")
        return

    return cl


async def threads_direct_messages(username: str, user_dict: dict):
    from pprint import pprint

    cl = user_dict.get('cl')
    user_id = user_dict.get('user_id')
    print('Start threads:', username, user_id, datetime.now().time())

    threads_direct_messages_now = cl.direct_threads(amount=10)
    # print(threads_direct_messages_now[0])
    # print(cl.user_info(user_id))
    # print('thread')
    # # pprint(thread_new)
    # print(threads_direct_messages_now[0])
    # print(threads_direct_messages_now[0].messages[0])
    # print(f'{await checking_if_the_user_is_followed(cl, user_id, threads_direct_messages_now[0].users[0].username)=}')
    # print(f'{await checking_if_the_user_is_followed(cl, user_id, threads_direct_messages_now[0].inviter.username)=}')

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
                if thread_old.id == thread_new.id and thread_old.messages[0].id == thread_new.messages[0].id:

                    # threads_old_delete_list.append(k)
                    threads_direct_messages_old.pop(i)
                    threads_now_delete_list.append(n)
                    break

        if len(threads_now_delete_list) > 0:

            threads_now_delete_list.reverse()
            for n in threads_now_delete_list:
                threads_direct_messages_now.pop(n)

            for thread in threads_direct_messages_now:

                # if thread.inviter.pk != user_id:
                messages: list = thread.messages
                for m, message in enumerate(messages):

                    if message.text and \
                        ('Я подписался'.lower() in message.text.lower() or
                            'Я подписалась'.lower() in message.text.lower()):

                        print(m, message.user_id, user_id)
                        print(message)
                        if (m == 0 and messages[0].user_id != user_id) or \
                            (m > 0 and
                             messages[m - 1].user_id != user_id and
                             not messages[m - 1].text.lower().startswith('Это отвечает БОТ:'.lower())):

                            checking_user_id = thread.users[0].pk
                            checking_username = thread.users[0].username
                            cl.direct_send(text="Это отвечает БОТ:\n"
                                                "Я получил от тебя сообщение, что ты подписался, "
                                                "теперь мне нужно время, что-бы проверить это.\n"
                                                "Подожди немножечко.", user_ids=[int(checking_user_id), ])

                            # if await checking_user_id_among_followers(cl=cl, user_id=checking_user_id):
                            if await checking_if_the_user_is_followed(cl=cl,
                                                                      user_id=user_id,
                                                                      checking_username=checking_username):
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


async def checking_if_the_user_is_followed(cl: instagrapi.Client, user_id: str, checking_username: str) -> bool:

    # print('followers', f'{cl.user_id=}', f'{cl.username=}', f'{checking_username=}')
    followers: list = cl.search_followers(user_id=user_id, query=checking_username)

    return True if followers[0].username == checking_username else False


async def checking_user_id_among_followers(cl: instagrapi.Client, user_id: str) -> bool:

    followers: set = await get_followers(cl=cl)

    return user_id in followers


async def get_followers(cl: instagrapi.Client) -> set:

    followers: dict = dict()
    while True:
        try:
            followers.update(cl.user_followers(user_id=str(cl.user_id), amount=0))
            return set(followers)
        except ChallengeRequired:
            pass


async def main():

    while True:
        for username in users.keys():
            print('!!!', datetime.now())

            user_dict: dict = users[username]

            if username == 'krasnikov.serhii':

                if not user_dict.get('cl'):
                    cl = await login_user(username=username, password=user_dict.get('password'), seed=user_dict.get('seed'))
                    user_dict.update({'cl': cl, 'user_id': cl.user_id, 'username': cl.username})
                    sleep(random.uniform(1, 5))

        for username in users.keys():
            user_dict: dict = users[username]

            if username == 'krasnikov.serhii':
                # pause = user_dict.get('pause', 0)
                # if pause:
                #     user_dict.update({'pause': pause - 1})
                #     sleep(random.uniform(1, 9))
                #     continue

                cl = user_dict.get('cl')
                print(cl)
                try:
                    threads = cl.direct_threads(amount=1)

                    for thread in threads:
                        print(thread)
                    # await threads_direct_messages(username=username, user_dict=user_dict)

                except ClientError as e:
                    print(f'instagrapi.exceptions.ClientError: {e}')
                    message = e.__getattribute__('message')
                    print(f'{type(message)=}')
                    print(f'{message=}')
                    try:
                        print(f'{json.loads(message)=}')
                    except json.decoder.JSONDecodeError:
                        pass

                    # if message == 'Please wait a few minutes before you try again.':
                    #     print('pause')
                    #     print(dir(e))
                    #     user_dict.update({'pause': 15})
                    # elif message in ('login_required', 'user_has_logged_out'):
                    #     cl = await login_user(username=username, password=user_dict.get('password'))
                    #     user_dict.update({'cl': cl, 'user_id': cl.user_id, 'username': cl.username})

                # except AssertionError as e:
                #
                #     message = e.__getattribute__('message')
                #     if message == 'Please wait a few minutes before you try again.':
                #         user_dict.update({'pause': 10})
                #
                #     require_login = e.__getattribute__('require_login')
                #     if require_login:
                #         cl = await login_user(username=username, password=user_dict.get('password'))
                #         user_dict.update({'cl': cl, 'user_id': cl.user_id, 'username': cl.username})

                print('@@@', datetime.now())

        break
        # try:
        #     print('Now you can INTERRUPT the process!!!')
        #     sleep(random.uniform(21, 51))
        # except KeyboardInterrupt:
        #     for username in users.keys():
        #
        #         user_dict: dict = users[username]
        #         cl = user_dict.get('cl')
        #         if cl:
        #             cl.logout()
        #
        #     raise

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # pass
    # cl = asyncio.run(login_user(username='krasnikov.sergey.78', password=users['krasnikov.sergey.78']))
    asyncio.run(main())

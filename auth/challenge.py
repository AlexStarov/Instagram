from instagrapi.mixins.challenge import ChallengeChoice

from .email import get_code_from_email


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.SMS:
        return False  # get_code_from_sms(username)
    elif choice == ChallengeChoice.EMAIL:
        return get_code_from_email(username)
    return False


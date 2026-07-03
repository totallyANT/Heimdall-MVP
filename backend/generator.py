import random
import string


def generate_password():

    chars = string.ascii_uppercase + string.digits

    return ''.join(
        random.choice(chars)
        for _ in range(6)
    )
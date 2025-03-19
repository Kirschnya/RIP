import random
from datetime import datetime, timedelta
from django.utils import timezone


def random_date():
    now = datetime.now(tz=timezone.utc)
    return now + timedelta(random.uniform(-1, 0) * 100)


def random_timedelta(factor=100):
    return timedelta(random.uniform(0, 1) * factor)


def random_bool():
    return bool(random.getrandbits(1))


def random_text():
    words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "cras", "eu", "blandit",
           "lacus",  "vivamus", "tincidunt", "ante", "nec", "nunc", "tincidunt", "lacinia", "curabitur", "maximus",
           "vulputate", "nisi", "vitae", "bibendum"]

    text = ""

    for _ in range(random.randint(1, 10)):
        text += random.choice(words) + " "

    text = text.strip().replace(text[0], text[0].upper(), 1)

    return text

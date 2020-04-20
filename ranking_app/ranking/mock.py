from datetime import datetime
import json
from pytz import timezone
import random

from faker import Faker


def support_datetime_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(repr(obj) + " is not JSON serializable")


id_list = [num for num in range(200, 0, -1)]
fake = Faker('ja_JP')


class TwitterResponseMock(object):
    def __init__(self, text):
        self.text = json.dumps(text, default=support_datetime_default)


def response_user_mock(name, url=fake.url(), contain_image_url=True):
    text = {'name': name, 'description': fake.text(),
            'url': url, 'followers_count': random.randrange(500)}
    if contain_image_url:
        text['profile_image_url_https'] = fake.image_url()
    return TwitterResponseMock(text)


def response_timeline_mock(text=fake.text()):
    ja_tz = timezone('Asia/Tokyo')
    start_time = datetime(2000, 1, 1, tzinfo=ja_tz)
    response_list = []
    for num in range(50):
        response_list.append({
            'id': id_list.pop(0), 'text': text,
            'created_at': fake.date_time_ad(tzinfo=ja_tz,
                                            start_datetime=start_time),
            'retweet_count': random.randrange(500),
            'favorite_count': random.randrange(500)})
    text_list = response_list
    return TwitterResponseMock(text_list)


def response_empty_mock():
    return TwitterResponseMock([])

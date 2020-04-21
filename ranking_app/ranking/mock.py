from datetime import datetime
import json
from pytz import timezone
import random

from faker import Faker


def support_datetime_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(repr(obj) + " is not JSON serializable")


fake = Faker('ja_JP')


class TwitterResponseMock(object):
    def __init__(self, text):
        self.text = json.dumps(text, default=support_datetime_default)


def response_user_mock(name, url=fake.url(), contain_icon_url=True,
                       contain_banner=True):
    text = {'name': name, 'description': fake.text(),
            'url': url, 'followers_count': random.randrange(500)}
    if contain_icon_url:
        text['profile_image_url_https'] = fake.image_url()
    if contain_banner:
        text['profile_banner_url'] = fake.image_url()
    return TwitterResponseMock(text)


def response_data_mock(url, query):
    if url == "https://api.twitter.com/1.1/users/show.json":
        response_data = {'name': fake.name(), 'url': fake.url(),
                         'description': fake.text(),
                         'followers_count': random.randrange(500)}
    elif url == "https://api.twitter.com/1.1/statuses/user_timeline.json":
        ja_tz = timezone('Asia/Tokyo')
        start_time = datetime(2000, 1, 1, tzinfo=ja_tz)
        response_data = []
        if 'max_id' in query:
            max_id = query['max_id']
            max_id += 2
        else:
            max_id = 0
        for tweet_id in range(max_id, max_id + 50):
            time = fake.date_time_ad(tzinfo=ja_tz, start_datetime=start_time)
            convert_time = time.strftime('%a %b %d %H:%M:%S %z %Y')
            response_data.append({
                'id': tweet_id, 'text': fake.text(),
                'id_str': str(tweet_id),
                'created_at': convert_time,
                'retweet_count': random.randrange(500),
                'favorite_count': random.randrange(500)})
        if response_data[-1]['id'] > 100:
            response_data = []
    return response_data


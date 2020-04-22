from datetime import datetime
from pytz import timezone
import random

from faker import Faker


def support_datetime_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(repr(obj) + " is not JSON serializable")


fake = Faker('ja_JP')


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
        if 'since_id' in query:
            max_id = query['since_id']
            max_id += 49
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


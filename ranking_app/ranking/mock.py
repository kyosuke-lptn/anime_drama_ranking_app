from datetime import datetime
from pytz import timezone
import random

from faker import Faker


def create_tweets(limit_id):
    response_data = []
    ja_tz = timezone('Asia/Tokyo')
    start_time = datetime(2000, 1, 1, tzinfo=ja_tz)
    for tweet_id in range(limit_id, limit_id-50, -1):
        time = fake.date_time_ad(tzinfo=ja_tz, start_datetime=start_time)
        convert_time = time.strftime('%a %b %d %H:%M:%S %z %Y')
        response_data.append({
            'id': tweet_id, 'text': fake.text(),
            'id_str': str(tweet_id),
            'created_at': convert_time,
            'retweet_count': random.randrange(500),
            'favorite_count': random.randrange(500)})
    if response_data[-1]['id'] < 0:
        response_data = []
    return response_data


fake = Faker('ja_JP')


def response_data_mock(url, query):
    """
    timelineのデータを取得する場合、新規取得ならtweetを100こ返す。更新ならtweetを50個返す。
    """
    if url == "https://api.twitter.com/1.1/users/show.json":
        response_data = {'name': fake.name(), 'url': fake.url(),
                         'description': fake.text(),
                         'followers_count': random.randrange(500)}
        return response_data
    elif url == "https://api.twitter.com/1.1/statuses/user_timeline.json":
        if 'max_id' in query:
            max_id = query['max_id']
        else:
            max_id = 100
        response_data = create_tweets(max_id)
        return response_data

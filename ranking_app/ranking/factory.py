from datetime import datetime
import random

import factory
from pytz import timezone

from . import models

JA_TZ = timezone('Asia/Tokyo')
START_TIME = datetime(2000, 1, 1, tzinfo=JA_TZ)


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    name = factory.Iterator(['アニメ', 'ドラマ'])


class ContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Content

    name = factory.Faker('word', locale='ja')
    description = factory.Faker('sentence', nb_words=20, locale='ja')
    release_date = factory.Faker('date_time_ad',
                                 tzinfo=JA_TZ,
                                 start_datetime=START_TIME)
    maker = factory.Faker('company', locale='ja')
    screen_name = factory.Sequence(lambda n: 'user%d' % n)
    category = factory.SubFactory(CategoryFactory)


class TwitterUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TwitterUser

    name = factory.Faker('user_name', locale='ja')
    content = factory.SubFactory(ContentFactory)
    description = factory.Faker('sentence', nb_words=20, locale='ja')
    official_url = factory.Faker('url', locale='ja')
    icon_url = factory.Faker('image_url', locale='ja')
    banner_url = factory.Faker('image_url', locale='ja')
    all_tweet_count = random.randrange(1000, 5000)
    all_retweet_count = random.randrange(1000, 5000)
    all_favorite_count = random.randrange(1000, 3000)
    followers_count = random.randrange(6000, 100000)


class TweetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Tweet

    tweet_id = str(factory.Sequence(lambda n: n))
    text = factory.Faker('sentence', nb_words=12, locale='ja')
    retweet_count = random.randrange(1000)
    favorite_count = random.randrange(1000)
    tweet_date = factory.Faker('date_time_ad', tzinfo=JA_TZ,
                               start_datetime=START_TIME)
    twitter_user = factory.SubFactory(TwitterUserFactory)

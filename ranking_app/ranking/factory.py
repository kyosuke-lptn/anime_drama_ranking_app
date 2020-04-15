import datetime
import random

from django.utils import timezone
import factory

from . import models


class ContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Content

    content_name = factory.Faker('word')
    description = factory.Faker('sentence', nb_words=12)
    release_date = timezone.localtime() - datetime.timedelta(days=365, hours=10)
    maker = factory.Faker('company', locale='ja')


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    category_name = factory.Iterator(['アニメ', '漫画', '映画', 'ドラマ'])

    @factory.post_generation
    def contents(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for content in extracted:
                self.contents.add(content)


class TwitterDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TwitterData

    tw_screen_name = factory.Faker('name')
    tw_description = factory.Faker('sentence', nb_words=12)
    content = factory.SubFactory(ContentFactory)


class TwitterRegularlyDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TwitterRegularlyData

    retweet_count = random.randrange(1000, 5000)
    favorite_count = random.randrange(1000, 5000)
    statuses_count = random.randrange(1000, 3000)
    listed_count = random.randrange(1000)
    followers_count = random.randrange(6000, 100000)
    tw_data = factory.SubFactory(TwitterDataFactory)


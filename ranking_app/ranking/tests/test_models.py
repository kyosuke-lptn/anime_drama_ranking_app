from unittest import mock

from django.db.utils import IntegrityError
from django.db.utils import DataError
from django.test import TestCase

from ranking import factory
from ranking.mock import response_data_mock
from ranking.models import TwitterApi
from ranking.models import TwitterUser
from ranking.models import Content

# Create your tests here.


class ContentModelTests(TestCase):

    def test_name_unique(self):
        factory.ContentFactory(name='movie A')
        with self.assertRaises(IntegrityError):
            factory.ContentFactory(name='movie A')

    def test_screen_name_unique(self):
        factory.ContentFactory(screen_name='sample')
        with self.assertRaises(IntegrityError):
            factory.ContentFactory(screen_name='sample')

    def test_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            factory.ContentFactory(name=name)

    def test_screen_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            factory.ContentFactory(screen_name=name)

    def test_maker_max_length(self):
        maker = 'a' * 51
        with self.assertRaises(DataError):
            factory.ContentFactory(maker=maker)


class CategoryModelTests(TestCase):

    def test_name_unique(self):
        factory.CategoryFactory(name='Movie')
        with self.assertRaises(IntegrityError):
            factory.CategoryFactory(name='Movie')

    def test_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            factory.CategoryFactory(name=name)


class TwitterUserModelTests(TestCase):

    def setUp(self):
        self.data = factory.TwitterUserFactory(all_retweet_count=100,
                                               all_favorite_count=50,
                                               all_tweet_count=10)

    def test_retweets_avg(self):
        self.assertEqual(self.data.retweets_avg(), 10)

    def test_favorite_avg(self):
        self.assertEqual(self.data.favorite_avg(), 5)


class TwitterApiModelTests(TestCase):

    def setUp(self):
        self.timeline_patcher = mock.patch('ranking.models.TwitterApi.get_base')
        self.mock_get_base = self.timeline_patcher.start()
        self.screen_name = 'sample_screen_name'
        self.content = factory.ContentFactory(screen_name=self.screen_name)
        self.mock_get_base.side_effect = response_data_mock

    def tearDown(self):
        self.timeline_patcher.stop()

    def test_get_user(self):
        TwitterApi().get_user('test_screen_name')

        self.mock_get_base.assert_called_once()

    def test_get_most_timeline_call_three_times(self):
        TwitterApi().get_most_timeline('test name')

        self.assertEqual(self.mock_get_base.call_count, 3)

    def test_get_and_store_twitter_data(self):
        TwitterApi().get_and_store_twitter_data(self.screen_name)

        twitter_user = Content.objects.get(
            screen_name=self.screen_name).twitteruser
        tweet_count = twitter_user.tweet_set.all().count()
        self.assertEqual(tweet_count, 100)
        self.assertEqual(self.mock_get_base.call_count, 4)

    def test_get_and_store_twitter_data_without_image_url(self):
        TwitterApi().get_and_store_twitter_data(self.screen_name)

        twitter_user = Content.objects.get(
            screen_name=self.screen_name).twitteruser
        self.assertIsNone(twitter_user.icon_url, None)
        self.assertIsNone(twitter_user.banner_url, None)

    def test_update_twitter_data(self):
        twitter_user = factory.TwitterUserFactory(content=self.content)
        factory.TweetFactory(twitter_user=twitter_user, tweet_id='1')

        TwitterApi().update_data(self.screen_name)

        updated_twitter_user = TwitterUser.objects.get(pk=twitter_user.pk)
        updated_tweet_count = updated_twitter_user.tweet_set.all().count()
        self.assertNotEqual(twitter_user.name, updated_twitter_user.name)
        self.assertGreater(updated_tweet_count, 1)

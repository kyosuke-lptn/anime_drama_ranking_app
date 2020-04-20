import json
from unittest import mock

from django.db.utils import IntegrityError, DataError
from django.test import TestCase

from ranking import factory
from ranking.mock import response_user_mock
from ranking.mock import response_timeline_mock
from ranking.mock import response_empty_mock
from ranking.models import TwitterApi, TwitterUser,Tweet

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
        self.patcher = mock.patch('requests_oauthlib.OAuth1Session.get')
        self.mock_oauth1session_get = self.patcher.start()
        self.screen_name = 'sample_screen_name'
        factory.ContentFactory(screen_name=self.screen_name)

    def tearDown(self):
        self.patcher.stop()

    def test_get_user(self):
        name = 'test name'
        url = "http: // sample.com"
        self.mock_oauth1session_get.return_value = response_user_mock(
            name=name, url=url)

        user = TwitterApi().get_user('test_screen_name')

        self.assertEqual(user['name'], name)
        self.assertEqual(user['url'], url)
        self.mock_oauth1session_get.assert_called_once()

    def test_get_most_timeline_call_twice(self):
        text = 'test description'
        self.mock_oauth1session_get.side_effect = [
            response_timeline_mock(text=text),
            response_empty_mock()]

        timeline = TwitterApi().get_most_timeline('test name')

        self.assertEqual(timeline[0]['text'], text)
        self.assertEqual(self.mock_oauth1session_get.call_count, 2)

    def test_get_and_store_twitter_data(self):
        name = 'sample user'
        self.mock_oauth1session_get.side_effect = [
            response_user_mock(name=name),
            response_timeline_mock(),
            response_timeline_mock(),
            response_empty_mock()]

        TwitterApi().get_and_store_twitter_data(self.screen_name)

        twitter_user_check = TwitterUser.objects.filter(name=name).exists()
        tweet_count = Tweet.objects.all().count()
        self.assertEqual(twitter_user_check, True)
        self.assertEqual(tweet_count, 100)
        self.assertEqual(self.mock_oauth1session_get.call_count, 4)

    def test_get_and_store_twitter_data_without_image_url(self):
        name = 'sample user'
        self.mock_oauth1session_get.side_effect = [
            response_user_mock(name=name, contain_image_url=False),
            response_timeline_mock(),
            response_empty_mock()]

        TwitterApi().get_and_store_twitter_data(self.screen_name)

        twitter_user_check = TwitterUser.objects.filter(name=name).exists()
        self.assertEqual(twitter_user_check, True)

from datetime import datetime
from pytz import timezone
from unittest import mock

from django.db.utils import IntegrityError
from django.db.utils import DataError
from django.test import TestCase

from ranking import factory
from ranking.mock import response_data_mock
from ranking.models import Content
from ranking.models import ScrapingContent
from ranking.models import TwitterApi
from ranking.models import TwitterUser

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

    def test_has_tweets(self):
        content = factory.ContentFactory()
        twitter_user = factory.TwitterUserFactory(content=content)
        factory.TweetFactory(twitter_user=twitter_user, tweet_id='1')

        self.assertTrue(content.has_tweets())

    def test_has_tweets_no_twitter_and_only_twitter_user(self):
        content = factory.ContentFactory()

        self.assertFalse(content.has_tweets())

        factory.TwitterUserFactory(content=content)

        self.assertTrue(content.has_tweets())

    def test_appraise(self):
        content = factory.ContentFactory()
        twitter_user = factory.TwitterUserFactory(content=content)
        for num in range(50):
            tweet = factory.TweetFactory(tweet_id=str(num),
                                         twitter_user=twitter_user)
            factory.TweetCountFactory(tweet=tweet, retweet_count=10,
                                      favorite_count=20)
        twitter_user.loads_tweet()

        self.assertEqual(content.appraise(), 0.40)

    def test_appraise_when_no_twitter_data(self):
        content = factory.ContentFactory()

        self.assertEqual(content.appraise(), 0)

    def test_sort_twitter_rating_by(self):
        anime_category = factory.CategoryFactory(name='アニメ')
        dorama_category = factory.CategoryFactory(name='ドラマ')
        content = self.create_content_twitter_tweet_tweetcount(
            anime_category, retweet=100)
        low_content = self.create_content_twitter_tweet_tweetcount(
            anime_category, retweet=10)
        dorama_content = self.create_content_twitter_tweet_tweetcount(
            dorama_category)

        sort_contents = Content.sort_twitter_rating_by(anime_category)
        self.assertEqual([content, low_content], sort_contents)
        self.assertNotIn(dorama_content, sort_contents)
        self.assertEqual(low_content, sort_contents[-1])

    @staticmethod
    def create_content_twitter_tweet_tweetcount(category, retweet=10):
        content = factory.ContentFactory(category=category)
        twitter_user = factory.TwitterUserFactory(content=content)
        for num in range(50):
            tweet = factory.TweetFactory(twitter_user=twitter_user)
            factory.TweetCountFactory(tweet=tweet, retweet_count=retweet,
                                      favorite_count=20)
        twitter_user.loads_tweet()
        return content


class CategoryModelTests(TestCase):

    def test_name_unique(self):
        factory.CategoryFactory(name='Movie')
        with self.assertRaises(IntegrityError):
            factory.CategoryFactory(name='Movie')

    def test_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            factory.CategoryFactory(name=name)


class StaffModelTests(TestCase):

    def test_unique_fields(self):
        staff = factory.StaffFactory(name='tanaka', role='主人公', is_cast=True)
        with self.assertRaises(IntegrityError):
            factory.StaffFactory(name='tanaka', role='主人公', is_cast=True,
                                 content=staff.content)


class TwitterUserModelTests(TestCase):

    def setUp(self):
        self.twitter_user = factory.TwitterUserFactory()

    def test_retweets_avg(self):
        """
        twitter_userにツイートの情報を反映するためにはloads_tweetメソッドが必要。
        """
        for num in range(10):
            tweet = factory.TweetFactory(tweet_id=str(num),
                                         twitter_user=self.twitter_user)
            factory.TweetCountFactory(tweet=tweet, retweet_count=10,
                                      favorite_count=5)
        self.assertEqual(self.twitter_user.retweets_avg(), 0)
        self.twitter_user.loads_tweet()
        self.assertEqual(self.twitter_user.retweets_avg(), 10)

    def test_favorite_avg(self):
        """
        twitter_userにツイートの情報を反映するためにはloads_tweetメソッドが必要。
        """
        for num in range(10):
            tweet = factory.TweetFactory(tweet_id=str(num),
                                         twitter_user=self.twitter_user)
            factory.TweetCountFactory(tweet=tweet, retweet_count=10,
                                      favorite_count=5)
        self.assertEqual(self.twitter_user.favorite_avg(), 0)
        self.twitter_user.loads_tweet()
        self.assertEqual(self.twitter_user.favorite_avg(), 5)

    def test_favorite_avg_with_0(self):
        self.assertEqual(self.twitter_user.favorite_avg(), 0)

    def test_retweets_avg_with_0(self):
        self.assertEqual(self.twitter_user.retweets_avg(), 0)


class TwitterApiModelTests(TestCase):

    def setUp(self):
        self.screen_name = 'sample_screen_name'
        self.content = factory.ContentFactory(screen_name=self.screen_name)

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_get_user(self, mock_get_base):
        mock_get_base.side_effect = response_data_mock

        TwitterApi().get_user('test_screen_name')

        mock_get_base.assert_called_once()

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_get_most_timeline_call_three_times(self, mock_get_base):
        mock_get_base.side_effect = response_data_mock

        TwitterApi().get_most_timeline('test name')

        self.assertEqual(mock_get_base.call_count, 3)

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_get_and_store_twitter_data(self, mock_get_base):
        mock_get_base.side_effect = response_data_mock

        TwitterApi().get_and_store_twitter_data(self.content)

        twitter_user = Content.objects.get(
            screen_name=self.screen_name).twitteruser
        tweet_count = twitter_user.tweet_set.all().count()
        self.assertEqual(tweet_count, 100)
        self.assertEqual(twitter_user.all_tweet_count, tweet_count)
        self.assertEqual(mock_get_base.call_count, 4)
        self.assertGreater(twitter_user.all_retweet_count, 0)
        self.assertGreater(twitter_user.all_favorite_count, 0)

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_get_and_store_twitter_data_without_screen_name(self,
                                                            mock_get_base):
        mock_get_base.side_effect = response_data_mock

        content = factory.ContentFactory(screen_name=None)
        TwitterApi().get_and_store_twitter_data(content)

        mock_get_base.assert_not_called()

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_get_and_store_twitter_data_without_image_url(self, mock_get_base):
        mock_get_base.side_effect = response_data_mock

        TwitterApi().get_and_store_twitter_data(self.content)

        twitter_user = Content.objects.get(
            screen_name=self.screen_name).twitteruser
        self.assertIsNone(twitter_user.icon_url, None)
        self.assertIsNone(twitter_user.banner_url, None)

    @mock.patch('ranking.models.TwitterApi.get_base')
    def test_update_data(self, mock_get_base):
        """
        # start_dateよりも古いツイートを取得できないかのテストはまだかけていない
        tweet_idが１〜５０のものを持っている状態で、更新データとして、tweet_idが１〜１００の
        ツイートを取得したときのテスト
        """
        mock_get_base.side_effect = response_data_mock

        ja_tz = timezone('Asia/Tokyo')
        start_time = datetime(2020, 4, 1, tzinfo=ja_tz)
        twitter_user = factory.TwitterUserFactory(content=self.content)
        for tweet_id in range(0, 50):
            tweet = factory.TweetFactory(twitter_user=twitter_user,
                                         tweet_id=str(tweet_id),
                                         tweet_date=start_time)
            factory.TweetCountFactory(tweet=tweet, retweet_count=10,
                                      favorite_count=10)
        twitter_user.loads_tweet()
        before_tweet_count = twitter_user.tweet_set.all().count()

        TwitterApi().update_data(self.content)

        updated_twitter_user = TwitterUser.objects.get(pk=twitter_user.pk)
        after_tweet_count = updated_twitter_user.tweet_set.all().count()
        updated_tweet = updated_twitter_user.tweet_set.get(tweet_id=1)
        self.assertNotEqual(twitter_user.name, updated_twitter_user.name)
        self.assertEqual(updated_twitter_user.all_tweet_count,
                         after_tweet_count)
        self.assertGreater(after_tweet_count, before_tweet_count)
        self.assertGreater(updated_twitter_user.all_retweet_count, 500)
        self.assertGreater(updated_twitter_user.all_favorite_count, 500)
        self.assertEqual(updated_tweet.tweetcount_set.all().count(), 2)


class WebScrapingModelTests(TestCase):
    @staticmethod
    def get_anime_data(category):
        """
        get_anime_dataメソッドをテストするためのメソッド。テスト用に少し変更しています。
        """
        scraping = ScrapingContent()
        scraping.contents_data = scraping.extra_data_from('test')
        scraping.store_contents_data(category)

    @mock.patch('ranking.models.ScrapingContent.extra_data_from')
    def test_store_contents_data(self, mock_contents_data):
        test_data = [
            {'name': 'サンプルドラマ',
             'description': '詳細について',
             'cast': ['主人公：田中太郎', 'ヒロイン：はげ'],
             'official_url': 'http://sample.com/aniani/',
             'maker': 'A制作会社',
             'staff': ['【原作】ランキングコミック、鈴木次郎', '【監督】別所誠人'],
             'img_url': 'https://sample.com/image/2222',
             'screen_name': 'test_name'}]
        mock_contents_data.return_value = test_data

        category = factory.CategoryFactory(name='アニメ')
        self.get_anime_data(category)

        content = Content.objects.get(name=test_data[0]['name'])
        self.assertEqual(content.description, test_data[0]['description'])
        self.assertEqual(content.maker, test_data[0]['maker'])
        self.assertEqual(content.screen_name, test_data[0]['screen_name'])
        self.assertEqual(content.category, category)
        self.assertEqual(content.staff_set.all().count(), 5)

    @mock.patch('ranking.models.ScrapingContent.extra_data_from')
    def test_store_contents_data_with_little_data(self, mock_contents_data):
        little_data = [{'name': 'サンプルドラマ'}]
        mock_contents_data.return_value = little_data

        category = factory.CategoryFactory(name='アニメ')
        self.get_anime_data(category)

        content = Content.objects.get(name=little_data[0]['name'])
        self.assertEqual(content.description, None)
        self.assertEqual(content.maker, None)
        self.assertEqual(content.screen_name, None)
        self.assertEqual(content.category, category)
        self.assertEqual(content.staff_set.all().count(), 0)

    @mock.patch('ranking.models.ScrapingContent.extra_data_from')
    def test_store_contents_data_without_data(self, mock_contents_data):
        mock_contents_data.return_value = []

        category = factory.CategoryFactory(name='アニメ')
        self.get_anime_data(category)

        self.assertEqual(Content.objects.all().count(), 0)

import json
from datetime import datetime

from django.db import models
from django.db import transaction
import environ
from requests_oauthlib import OAuth1Session

# Create your models here.


class Category(models.Model):
    name = models.CharField('カテゴリー名', max_length=50, unique=True,
                            db_index=True)

    def __str__(self):
        return self.name


class Content(models.Model):
    name = models.CharField('作品名', max_length=50, unique=True, db_index=True)
    description = models.TextField('詳細説明')
    release_date = models.DateField('リリース日', db_index=True, null=True,
                                    blank=True)
    maker = models.CharField('作り手', max_length=50, db_index=True)
    update_date = models.DateTimeField('更新日', auto_now=True, db_index=True,
                                       null=True, blank=True)
    screen_name = models.CharField('twitter ID', max_length=50, unique=True,
                                   db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 verbose_name='ジャンル', db_index=True)

    def __str__(self):
        return self.name

    def has_tweets(self):
        if hasattr(self, 'twitteruser') and hasattr(self.twitteruser, 'tweet_set'):
            return True
        return False


class TwitterUser(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    content = models.OneToOneField(Content, on_delete=models.CASCADE,
                                   verbose_name='作品')
    description = models.TextField('twitterからの詳細情報', null=True, blank=True)
    official_url = models.CharField('公式URL', max_length=500, null=True,
                                    blank=True)
    icon_url = models.CharField('アイコン画像のURL', max_length=500, null=True,
                                blank=True)
    banner_url = models.CharField('バナー画像のURL', max_length=500, null=True,
                                  blank=True)
    followers_count = models.PositiveIntegerField('フォワー数', null=True,
                                                  blank=True)
    all_tweet_count = models.PositiveIntegerField('取得したツイート数', null=True,
                                                  blank=True)
    all_retweet_count = models.PositiveIntegerField('リツイート総数', null=True,
                                                    blank=True)
    all_favorite_count = models.PositiveIntegerField('イイね総数', null=True,
                                                     blank=True)
    create_date = models.DateTimeField('作成日', auto_now_add=True)
    update_date = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.name

    def retweets_avg(self):
        result = self.all_retweet_count / self.all_tweet_count
        return round(result, 2)

    def favorite_avg(self):
        result = self.all_favorite_count / self.all_tweet_count
        return round(result, 2)


class Tweet(models.Model):
    tweet_id = models.CharField('ツイートID', unique=True, max_length=100)
    text = models.TextField('内容')
    retweet_count = models.PositiveIntegerField('リツート数')
    favorite_count = models.PositiveIntegerField('いいね数')
    twitter_user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE,
                                     verbose_name='Twitterデータ')
    tweet_date = models.DateTimeField('ツイート日')
    create_date = models.DateTimeField('ツイート取得日', auto_now_add=True)
    update_date = models.DateTimeField('ツイート取得更新日', auto_now=True)


TIMELINE_COUNT = '200'
TIMELINE_TRIM_USER = 'true'
TIMELINE_INCLUDE_RTS = 'false'


class TwitterApi(object):
    def __init__(self):
        env = environ.Env()
        environ.Env.read_env('.env')
        self.__consumer_key = env('CONSUMER_KEY')
        self.__consumer_secret = env('CONSUMER_SECRET')
        self.__access_token = env('ACCESS_TOKEN')
        self.__secret_token = env('SECRET_TOKEN')
        self.__api = self.auth_twitter()

    def auth_twitter(self):
        api = OAuth1Session(self.__consumer_key,
                            self.__consumer_secret,
                            self.__access_token,
                            self.__secret_token)
        return api

    def get_base(self, url, query_dict):
        response = self.__api.get(url, params=query_dict)
        result = json.loads(response.text)
        return result

    def get_simple_timeline(self, screen_name, max_id=None, since_id=None):
        timeline_url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        query = {
            "screen_name": screen_name,
            "count": TIMELINE_COUNT,
            "trim_user": TIMELINE_TRIM_USER,
            "include_rts": TIMELINE_INCLUDE_RTS}
        if max_id:
            query["max_id"] = max_id
        if since_id:
            query["since_id"] = since_id
        return self.get_base(timeline_url, query)

    def get_most_timeline(self, screen_name):
        timeline = self.get_simple_timeline(screen_name)
        next_id = timeline[-1]["id"] - 1
        while True:
            result = self.get_simple_timeline(screen_name, max_id=next_id)
            timeline.extend(result)
            if result:
                next_id = result[-1]["id"] - 1
            else:
                break
        return timeline

    def get_user(self, screen_name):
        user_url = "https://api.twitter.com/1.1/users/show.json"
        query = {"screen_name": screen_name}
        return self.get_base(user_url, query)

    @staticmethod
    def store_user(screen_name, user_data, content=None):
        """
        get_userメソッドで取得したデータを元にTwitterUserモデル作成・アップデートする
        :param screen_name: str
        :param user_data: obj　
        :param content: obj　コンテンツがあればTwitterUserのupdate、なければcreateになる
        :return TwitterUser: obj
        """
        if not content:
            content = Content.objects.get(screen_name=screen_name)
        twitter_user_args = {}
        fields_list = ['name', 'url', 'description', 'profile_image_url_https',
                       'profile_banner_url', 'followers_count']
        for attr_key, attr_value in user_data.items():
            if attr_key in fields_list:
                if attr_key == 'profile_image_url_https':
                    twitter_user_args['icon_url'] = attr_value
                elif attr_key == 'url':
                    twitter_user_args['official_url'] = attr_value
                elif attr_key == 'profile_banner_url':
                    twitter_user_args['banner_url'] = attr_value
                else:
                    twitter_user_args[attr_key] = attr_value
        return TwitterUser.objects.update_or_create(
            defaults=twitter_user_args, content=content)[0]

    @staticmethod
    def store_timeline_data(timeline_data, twitter_user):
        """
        get_timelineメソッドで取得したデータをTwitterUserとTweetに保存する
        :param timeline_data: obj
        :param twitter_user: obj
        """
        retweet_count, favorite_count = 0, 0
        for tweet in timeline_data:
            retweet_count += tweet['retweet_count']
            favorite_count += tweet['favorite_count']
            tweet_time = tweet['created_at']
            converted_time = datetime.strptime(
                tweet_time, '%a %b %d %H:%M:%S %z %Y')
            Tweet.objects.create(
                twitter_user=twitter_user, tweet_id=tweet['id_str'],
                tweet_date=converted_time, text=tweet['text'],
                retweet_count=tweet['retweet_count'],
                favorite_count=tweet['favorite_count'])
        twitter_user.all_tweet_count = len(timeline_data)
        twitter_user.all_retweet_count = retweet_count
        twitter_user.all_favorite_count = favorite_count
        twitter_user.save()

    @transaction.atomic
    def get_and_store_twitter_data(self, content):
        """
        TwitterAPIからデータを取得して,TwitterUserとTweetのモデルを作る
        :param content: obj
        """
        screen_name = content.screen_name
        user_data = self.get_user(screen_name)
        timeline_data = self.get_most_timeline(screen_name)
        twitter_user = self.store_user(screen_name, user_data)
        self.store_timeline_data(timeline_data, twitter_user)

    @transaction.atomic
    def update_data(self, content):
        """
        TwitterAPIからのデータを取得して、TwitterUserとTweetのモデルをアップデートする
        :param content: obj
        """
        # 最新の取得済みツイートを持ってくる（id）
        screen_name = content.screen_name
        twitter_user = content.twitteruser
        latest_tweet = twitter_user.tweet_set.order_by('-tweet_date')[0]
        latest_id = int(latest_tweet.tweet_id)

        # ツイートを取得する
        user_data = self.get_user(screen_name)
        timeline = self.get_simple_timeline(screen_name, since_id=latest_id)
        next_id = timeline[0]['id']
        while True:
            result = self.get_simple_timeline(screen_name, since_id=next_id)
            timeline.extend(result)
            if result:
                next_id = result[0]['id']
            else:
                break
        # ツイートを保存する
        updated_twitter_user = self.store_user(screen_name, user_data, content)
        self.store_timeline_data(timeline, updated_twitter_user)

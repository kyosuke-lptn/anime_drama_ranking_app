import json

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

    # def data(self):
    #     return {
    #         data.display_create_date(): [
    #             data.retweets_avg(), data.favorite_avg(), data.listed_count,
    #             data.followers_count, data.statuses_count
    #         ]
    #         for data in self.twitterdata_set.all()
    #         for data in data.twitterregularlydata_set.all()
    #     }


class TwitterUser(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    content = models.ForeignKey(Content, on_delete=models.CASCADE,
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
        return self.update_date.strftime("%Y/%m/%d %H:%M:%S")

    def retweets_avg(self):
        result = self.all_retweet_count / self.all_tweet_count
        return round(result, 2)

    def favorite_avg(self):
        result = self.all_favorite_count / self.all_tweet_count
        return round(result, 2)


class Tweet(models.Model):
    tweet_id = models.PositiveIntegerField('ツイートID', unique=True)
    text = models.TextField('内容')
    retweet_count = models.PositiveIntegerField('リツート数')
    favorite_count = models.PositiveIntegerField('いいね数')
    twitter_user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE,
                                     verbose_name='Twitterデータ')
    tweet_date = models.DateTimeField('ツイート日')
    create_date = models.DateTimeField('ツイート取得日', auto_now_add=True)
    update_date = models.DateTimeField('ツイート取得更新日', auto_now=True)

    # def last_id(self):
    #


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

    def get_simple_timeline(self, screen_name, max_id=None):
        timeline_url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        query = {
            "screen_name": screen_name,
            "count": TIMELINE_COUNT,
            "trim_user": TIMELINE_TRIM_USER,
            "include_rts": TIMELINE_INCLUDE_RTS}
        if max_id:
            query["max_id"] = max_id
        return self.get_base(timeline_url, query)

    def get_most_timeline(self, screen_name):
        timeline = self.get_simple_timeline(screen_name)
        next_id = timeline[-1]["id"] - 1
        while True:
            result = self.get_simple_timeline(screen_name, next_id)
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
    def store_user_data(screen_name, user_data):
        """
        get_userメソッドで取得したデータをTwitterUserに保存する
        :param screen_name: str
        :param user_data: obj　
        :return TwitterUser: obj
        """
        content = Content.objects.get(screen_name=screen_name)
        twitter_user_args = {'name': user_data['name'], 'content': content}
        fields_list = ['url', 'description', 'profile_image_url_https',
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
        return TwitterUser.objects.create(**twitter_user_args)

        # twitter_user = TwitterUser.objects.create(
        #     content=content, name=user_data['name'],
        #     official_url=user_data['url'], description=user_data['description'],
        #     icon_url=user_data['profile_image_url_https'],
        #     banner_url=user_data['profile_banner_url'],
        #     followers_count=user_data['followers_count'])
        # return twitter_user

    @staticmethod
    def create_tweets(timeline_data, twitter_user):
        """
        引数のtimelineデータのTweetモデルを作成する
        :param timeline_data: list
        :param twitter_user: obj
        :return リツイート総数、イイね総数、作成したtweetモデルのリスト: tuple
        """
        retweet_count, favorite_count, tweets_list = 0, 0, []
        for tweet in timeline_data:
            retweet_count += tweet['retweet_count']
            favorite_count += tweet['favorite_count']
            tweet_obj = Tweet.objects.create(
                twitter_user=twitter_user, tweet_id=tweet['id'],
                tweet_date=tweet['created_at'], text=tweet['text'],
                retweet_count=tweet['retweet_count'],
                favorite_count=tweet['favorite_count'])
            tweets_list.append(tweet_obj)
        return retweet_count, favorite_count, tweets_list

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
            Tweet.objects.create(
                twitter_user=twitter_user, tweet_id=tweet['id'],
                tweet_date=tweet['created_at'], text=tweet['text'],
                retweet_count=tweet['retweet_count'],
                favorite_count=tweet['favorite_count'])
        twitter_user.all_tweet_count = len(timeline_data)
        twitter_user.all_retweet_count = retweet_count
        twitter_user.all_favorite_count = favorite_count
        twitter_user.save()

    @transaction.atomic
    def get_and_store_twitter_data(self, screen_name):
        """
        TwitterAPIからデータを取得して,TwitterUserとTwitter
        :param screen_name: str
        """
        user_data = self.get_user(screen_name)
        timeline_data = self.get_most_timeline(screen_name)
        twitter_user = self.store_user_data(screen_name, user_data)
        self.store_timeline_data(timeline_data, twitter_user)

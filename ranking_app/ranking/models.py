import json

from django.db import models
from django.db import transaction
import environ
from requests_oauthlib import OAuth1Session

# Create your models here.


class Content(models.Model):
    content_name = models.CharField('作品名', max_length=50, unique=True,
                                    db_index=True)
    description = models.CharField('詳細説明', max_length=500)
    release_date = models.DateTimeField('リリース日', db_index=True)
    maker = models.CharField('作り手', max_length=50, db_index=True)
    update_date = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.content_name


class Category(models.Model):
    category_name = models.CharField('カテゴリー名', max_length=20, unique=True)
    contents = models.ManyToManyField(Content, verbose_name='作品名')

    def __str__(self):
        return self.category_name


class TwitterData(models.Model):
    tw_screen_name = models.CharField('スクリーンネーム', max_length=255,
                                      unique=True)
    tw_description = models.CharField('twitterからの詳細情報', max_length=500)
    content_url = models.CharField('公式URL', max_length=500, null=True,
                                   blank=True)
    profile_image_url_https = models.CharField('アイコン画像のURL',
                                               max_length=500, null=True,
                                               blank=True)
    profile_banner_url = models.CharField('バナー画像のURL', max_length=500,
                                          null=True, blank=True)
    content = models.ForeignKey(Content, on_delete=models.CASCADE,
                                verbose_name='作品名')
    create_date = models.DateTimeField('作成日', auto_now_add=True)
    update_date = models.DateTimeField('更新日', auto_now=True)


class TwitterRegularlyData(models.Model):
    retweet_count = models.PositiveIntegerField('リツイート総数', null=True,
                                                blank=True)
    favorite_count = models.PositiveIntegerField('いいね総数', null=True,
                                                 blank=True)
    statuses_count = models.PositiveIntegerField('ツイート取得総数',
                                                 null=True, blank=True)
    listed_count = models.PositiveIntegerField('リスト総数', null=True,
                                               blank=True)
    followers_count = models.PositiveIntegerField('フォワー数', null=True,
                                                  blank=True)
    tw_data = models.ForeignKey(TwitterData, on_delete=models.CASCADE,
                                verbose_name='Twitterデータ')
    create_date = models.DateTimeField('データ取得日', auto_now_add=True)

    def retweets_avg(self):
        result = self.retweet_count / self.statuses_count
        return round(result, 2)

    def favorite_avg(self):
        result = self.favorite_count / self.statuses_count
        return round(result, 2)


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

    def auth_twitter(self):
        twitter = OAuth1Session(self.__consumer_key,
                                self.__consumer_secret,
                                self.__access_token,
                                self.__secret_token)
        return twitter

    def get_base(self, url, query_dict):
        api = self.auth_twitter()
        response = api.get(url, params=query_dict)
        result = json.loads(response.text)
        return result

    def get_simple_timeline(self, user_name, max_id=None):
        timeline_url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        query = {
            "screen_name": user_name,
            "count": TIMELINE_COUNT,
            "trim_user": TIMELINE_TRIM_USER,
            "include_rts": TIMELINE_INCLUDE_RTS
        }
        if max_id:
            query["max_id"] = max_id
        return self.get_base(timeline_url, query)

    def get_most_timeline(self, user_name):
        timeline = self.get_simple_timeline(user_name)
        next_id = timeline[-1]["id"] - 1
        while True:
            result = self.get_simple_timeline(user_name, next_id)
            timeline.extend(result)
            if result:
                next_id = result[-1]["id"] - 1
            else:
                break
        return timeline

    def get_user(self, user_name):
        user_url = "https://api.twitter.com/1.1/users/show.json"
        query = {
            "screen_name": user_name
        }
        return self.get_base(user_url, query)

    @transaction.atomic
    def insert_twitter_data_to_ranking_class(self, content):
        TwitterData.objects.create()




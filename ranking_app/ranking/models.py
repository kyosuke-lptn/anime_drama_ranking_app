from collections import Counter
from datetime import datetime
import json
import re
import time

from bs4 import BeautifulSoup
from django.db import models
from django.db import transaction
import environ
from requests_oauthlib import OAuth1Session
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import urllib3

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
                                   db_index=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 verbose_name='ジャンル', db_index=True)

    def __str__(self):
        return self.name

    def has_tweets(self):
        if hasattr(self, 'twitteruser') and hasattr(self.twitteruser,
                                                    'tweet_set'):
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
    create_date = models.DateTimeField('作成日', auto_now_add=True)
    update_date = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.name

    def all_tweet_count(self):
        return self.tweet_set.all().count()

    def all_retweet_count(self):
        count = 0
        for tweet in self.tweet_set.all():
            count += tweet.retweet_count
        return count

    def all_favorite_count(self):
        count = 0
        for tweet in self.tweet_set.all():
            count += tweet.favorite_count
        return count

    def retweets_avg(self):
        if self.all_retweet_count() == 0 or self.all_retweet_count() == 0:
            return 0
        result = self.all_retweet_count() / self.all_tweet_count()
        return round(result, 2)

    def favorite_avg(self):
        if self.all_favorite_count() == 0 or self.all_retweet_count() == 0:
            return 0
        result = self.all_favorite_count() / self.all_tweet_count()
        return round(result, 2)

    def latest_tweet(self):
        return self.tweet_set.order_by('-tweet_date')[0]


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
        :param user_data: list　
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
        :param timeline_data: list
        :param twitter_user: obj
        """
        if timeline_data:
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
        next_id = int(latest_tweet.tweet_id)

        # ツイートを取得する
        user_data = self.get_user(screen_name)
        timeline = []
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


ANIME_TOP_URL = 'https://anime.eiga.com'


class ScrapingContent(object):
    def __init__(self):
        self.contents_data = []

    def create_url(self, url='', anime_default=False):
        if anime_default:
            url = ANIME_TOP_URL + url
        return url

    def get_html_from(self, url):
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        return response

    # def get_html_with_chrome_from(self, url):
    #     options = Options()
    #     options.binary_location = '/usr/bin/google-chrome'
    #     options.add_argument('--headless')
    #     options.add_argument("--disable-dev-shm-using")
    #     # options.set_headless(True)
    #     driver = webdriver.Chrome('chromedriver', options=options)
    #     # driver = webdriver.Chrome(chrome_options=options)
    #     driver.get(url)
    #     return driver.page_source.encode('utf-8')

    def extra_data_from(self, response):
        soup = BeautifulSoup(response.data, 'lxml')
        for p_tag in soup.find_all('p', {'class': 'seasonAnimeTtl'}):
            for content in p_tag:
                content_dict = {'name': content.text}
                url = self.create_url(content['href'], anime_default=True)
                html_data = self.get_html_from(url)
                soup = BeautifulSoup(html_data.data, 'lxml')
                description_data = soup.select_one('#detailSynopsis > dd')
                cast_data = soup.select_one(
                    '#detailCast > dd > ul:nth-child(1)')
                official_url = soup.select_one('#detailLink > dd > ul > li > a')
                maker = soup.select_one(
                    '#main > div:nth-child(1) > div.articleInner > div > div > div.animeDetailBox.clearfix > div.animeDetailL > dl:nth-child(4) > dd > ul > li')
                staff = soup.select_one('#detailStaff > dd')
                img_data = soup.select_one(
                    '#main > div:nth-child(1) > div.articleInner > div > div > div.animeDetailBox.clearfix > div.animeDetailImg > img')
                print(content.text)
                screen_name = self.get_screen_name_from(official_url.text)
                print(screen_name)
                if description_data:
                    content_dict['description'] = description_data.text
                if cast_data:
                    cast = [person.text for person in cast_data.find_all('li')]
                    content_dict['cast'] = cast
                content_dict['official_url'] = official_url.text
                if maker:
                    content_dict['maker'] = maker.text
                if staff:
                    staff_list = [item.text for item in staff.find_all('li')]
                    content_dict['staff'] = staff_list
                if img_data:
                    content_dict['img'] = img_data['src']
                if screen_name:
                    content_dict['screen_name'] = screen_name

                self.contents_data.append(content_dict)
                time.sleep(1)
        return self.contents_data

    # TODO (sumitani) 除外する文言を追加する
    def get_screen_name_from(self, url):
        response = self.get_html_from(url)
        soup = BeautifulSoup(response.data, 'lxml')
        pattern = r'href="https://twitter.com/(\w+)(\?\w+=\w+)?"'
        repatter = re.compile(pattern)
        extract_a_tag_list = repatter.findall(str(soup))
        print(extract_a_tag_list)
        if extract_a_tag_list:
            screen_name = Counter(extract_a_tag_list).most_common()[0][0][0]
        else:
            screen_name = None
        time.sleep(1)
        return screen_name

from collections import Counter
from datetime import datetime
import json
import re
import time
from pytz import timezone

from bs4 import BeautifulSoup
from django.db import models
from django.db import transaction
import environ
from requests_oauthlib import OAuth1Session
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import urllib3

# Create your models here.

HIGH_RANK_CONTENT = 5


class Category(models.Model):
    name = models.CharField('カテゴリー名', max_length=50, unique=True,
                            db_index=True)

    def has_high_rank_content_sort_by_twitter_data(self):
        return Content.sort_twitter_rating_by(self)[:HIGH_RANK_CONTENT]

    def __str__(self):
        return self.name


class Content(models.Model):
    name = models.CharField('作品名', max_length=50, unique=True, db_index=True)
    description = models.TextField('詳細説明', null=True, blank=True)
    release_date = models.DateField('リリース日', db_index=True, null=True,
                                    blank=True)
    maker = models.CharField('作り手', max_length=50, db_index=True, null=True,
                             blank=True)
    update_date = models.DateTimeField('更新日', auto_now=True, db_index=True,
                                       null=True, blank=True)
    screen_name = models.CharField('twitter ID', max_length=50, unique=True,
                                   db_index=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 verbose_name='ジャンル', db_index=True)
    img_url = models.CharField('画像のURL', max_length=500, null=True,
                               blank=True)

    def __str__(self):
        return self.name

    def has_tweets(self):
        if hasattr(self, 'twitteruser') and hasattr(self.twitteruser,
                                                    'tweet_set'):
            return True
        return False

    def appraise(self):
        """
        （いいねx1 ＋ リツイートx2）/100の計算式でランキングのための数値を算出しています。
        これは、いいねよりリツイートの方が数が比較的少なく、リツイートの方が価値が高いと考えたためです。
        :return:
        """
        if self.has_tweets():
            retweet_avg = self.twitteruser.retweets_avg()
            favorite_avg = self.twitteruser.favorite_avg()
            result = (favorite_avg + retweet_avg * 2) / 100
            return round(result, 2)
        else:
            return 0

    @classmethod
    def sort_twitter_rating_by(cls, category=None):
        """
        カテゴリーに含まれるツイッター評価値順にソートしたコンテンツを返す
        :return: tuple in list
        """
        if category:
            contents = {
                content: content.appraise()
                for content in cls.objects.filter(category=category)}
        else:
            contents = {
                content: content.appraise()
                for content in cls.objects.all()}
        score_sorted = sorted(contents.items(), key=lambda x: x[1],
                              reverse=True)
        return [content_tuple[0] for content_tuple in score_sorted]

    def main_performers(self):
        return self.staff_set.filter(is_cast=True)[:4]

    def performers(self):
        return self.staff_set.filter(is_cast=True)

    def only_staff(self):
        return self.staff_set.filter(is_cast=False)


class Staff(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    role = models.CharField(max_length=50, db_index=True)
    is_cast = models.BooleanField(db_index=True, default=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE,
                                verbose_name='作品', db_index=True)

    class Meta:
        unique_together = ('name', 'role', 'content')

    def __str__(self):
        return self.name


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
    followers_count = models.PositiveIntegerField('フォワー数', default=0)
    all_tweet_count = models.PositiveIntegerField('ツイート総数', default=0)
    all_retweet_count = models.PositiveIntegerField('リツイート総数', default=0)
    all_favorite_count = models.PositiveIntegerField('いいね総数', default=0)
    create_date = models.DateTimeField('作成日', auto_now_add=True)
    update_date = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.name

    def retweets_avg(self):
        if self.all_retweet_count == 0 or self.all_retweet_count == 0:
            return 0
        result = self.all_retweet_count / self.all_tweet_count
        return round(result, 2)

    def favorite_avg(self):
        if self.all_favorite_count == 0 or self.all_retweet_count == 0:
            return 0
        result = self.all_favorite_count / self.all_tweet_count
        return round(result, 2)

    def loads_tweet(self):
        self.all_favorite_count = 0
        self.all_retweet_count = 0
        tweets = self.tweet_set.all()
        self.all_tweet_count = tweets.count()
        for tweet in tweets:
            self.all_retweet_count += tweet.retweet_count()
            self.all_favorite_count += tweet.favorite_count()
        self.save()

    def latest_tweet(self):
        return self.tweet_set.order_by('-tweet_date')[0]


class Tweet(models.Model):
    tweet_id = models.CharField('ツイートID', unique=True, max_length=100)
    text = models.TextField('内容')
    twitter_user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE,
                                     verbose_name='Twitterデータ')
    tweet_date = models.DateTimeField('ツイート日')

    def latest_tweet_count(self):
        return self.tweetcount_set.order_by('-create_date')[0]

    def retweet_count(self):
        return self.latest_tweet_count().retweet_count

    def favorite_count(self):
        return self.latest_tweet_count().favorite_count


class TweetCount(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE,
                              verbose_name='ツイート')
    retweet_count = models.PositiveIntegerField('リツート数')
    favorite_count = models.PositiveIntegerField('いいね数')
    create_date = models.DateTimeField('ツイート取得日', auto_now_add=True)


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
        time.sleep(1)
        return result

    def get_simple_timeline(self, screen_name, max_id=None, since_id=None):
        timeline_url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        query = {
            "screen_name": screen_name,
            "count": TIMELINE_COUNT,
            "trim_user": TIMELINE_TRIM_USER,
            "include_rts": TIMELINE_INCLUDE_RTS}
        if max_id or max_id == 0:
            query["max_id"] = max_id
        if since_id:
            query["since_id"] = since_id
        return self.get_base(timeline_url, query)

    def get_most_timeline(self, screen_name, since_id=None):
        timeline = self.get_simple_timeline(screen_name, since_id=since_id)
        next_id = timeline[-1]["id"] - 1
        while True:
            result = self.get_simple_timeline(screen_name, max_id=next_id,
                                              since_id=since_id)
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
            for tweet in timeline_data:
                tweet_time = tweet['created_at']
                converted_time = datetime.strptime(
                    tweet_time, '%a %b %d %H:%M:%S %z %Y')
                tweet_args = {'twitter_user': twitter_user,
                              'tweet_date': converted_time,
                              'text': tweet['text']}
                new_tweet = Tweet.objects.update_or_create(
                    defaults=tweet_args, tweet_id=tweet['id_str'])[0]
                TweetCount.objects.create(
                    tweet=new_tweet, retweet_count=tweet['retweet_count'],
                    favorite_count=tweet['favorite_count'])
            twitter_user.loads_tweet()

    @transaction.atomic
    def get_and_store_twitter_data(self, content):
        """
        TwitterAPIからデータを取得して,TwitterUserとTweetのモデルを新規作成する
        :param content: obj
        """
        screen_name = content.screen_name
        if screen_name:
            user_data = self.get_user(screen_name)
            timeline_data = self.get_most_timeline(screen_name)
            twitter_user = self.store_user(screen_name, user_data)
            self.store_timeline_data(timeline_data, twitter_user)

    def get_updated_timeline(self, screen_name, twitter_user, start_datetime):
        target_tweet = twitter_user.tweet_set.filter(
            tweet_date__gte=start_datetime).order_by('tweet_date')[0]
        since_id = int(target_tweet.tweet_id) - 1
        timeline_data = self.get_most_timeline(screen_name, since_id=since_id)
        return timeline_data

    @classmethod
    def start_datetime(cls):
        ja_tz = timezone('Asia/Tokyo')
        current_month = datetime.now().month
        current_year = datetime.now().year
        if current_month in [1, 2, 3]:
            return datetime(current_year, 1, 1, tzinfo=ja_tz)
        elif current_month in [4, 5, 6]:
            return datetime(current_year, 4, 1, tzinfo=ja_tz)
        elif current_month in [7, 8, 9]:
            return datetime(current_year, 7, 1, tzinfo=ja_tz)
        elif current_month in [10, 11, 12]:
            return datetime(current_year, 10, 1, tzinfo=ja_tz)

    @transaction.atomic
    def update_data(self, content):
        """
        TwitterAPIからのデータを取得して、TwitterUserとTweetのモデルをアップデートする
        :param content: obj
        """
        screen_name = content.screen_name
        twitter_user = content.twitteruser
        start_datetime = self.start_datetime()
        timeline = self.get_updated_timeline(screen_name, twitter_user,
                                             start_datetime)
        user_data = self.get_user(screen_name)
        updated_twitter_user = self.store_user(screen_name, user_data, content)
        self.store_timeline_data(timeline, updated_twitter_user)


ANIME_TOP_URL = 'https://anime.eiga.com'
EXCLUSION_LIST = ['share', 'bs7ch_pr', 'tvtokyo_pr', 'intent', 'search']


class ScrapingContent(object):
    def __init__(self):
        self.contents_data = []
        self.contents = []

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
        anime_boxes = soup.find_all('div', {'class': 'animeSeasonBox'})
        if anime_boxes:
            for box in anime_boxes:
                p_tag = box.find('p', 'seasonAnimeTtl')
                content_dict = {'name': p_tag.text}
                detail_url = p_tag.find('a')['href']
                maker_tag = box.select('dt:contains("制作会社") ~ dd')
                if maker_tag:
                    content_dict['maker'] = maker_tag[0].text
                url = self.create_url(detail_url, anime_default=True)
                html_data = self.get_html_from(url)
                soup = BeautifulSoup(html_data.data, 'lxml')
                description_data = soup.select_one('#detailSynopsis > dd')
                cast_data = soup.select_one(
                    '#detailCast > dd > ul:nth-child(1)')
                official_url = soup.select_one('#detailLink > dd > ul > li > a')
                staff = soup.select_one('#detailStaff > dd')
                img_data = soup.select_one(
                    '#main > div:nth-child(1) > div.articleInner > div > div'
                    '> div.animeDetailBox.clearfix > div.animeDetailImg > img')
                screen_name = self.get_screen_name_from(official_url.text)
                if description_data:
                    content_dict['description'] = description_data.text
                if cast_data:
                    cast = [person.text for person in cast_data.find_all('li')]
                    content_dict['cast'] = cast
                content_dict['official_url'] = official_url.text
                if staff:
                    staff_list = [item.text for item in staff.find_all('li')]
                    content_dict['staff'] = staff_list
                if img_data:
                    content_dict['img_url'] = img_data['src']
                if screen_name:
                    content_dict['screen_name'] = screen_name

                self.contents_data.append(content_dict)
                time.sleep(1)
        return self.contents_data

    def get_screen_name_from(self, url):
        response = self.get_html_from(url)
        soup = BeautifulSoup(response.data, 'lxml')
        pattern = r'https://twitter.com/(\w+)(\?\w+=\w+)?'
        repatter = re.compile(pattern)
        a_tag_list = soup.find_all('a', {'href': repatter})
        screen_name = None
        if a_tag_list:
            extract_a_tag_list = [
                repatter.match(attr['href']).groups()[0].lower() for attr in
                a_tag_list]
            correct_a_tag = []
            for word in extract_a_tag_list:
                if word not in EXCLUSION_LIST:
                    correct_a_tag.append(word)
            if correct_a_tag:
                screen_name = Counter(correct_a_tag).most_common()[0][0]
        return screen_name

    # TODO (3) 取得できなかった情報について、release_dateについて
    @transaction.atomic
    def store_contents_data(self, category):
        """
        引数のデータをcontentモデル・staffモデルとして保存する。
        :param category: obj
        """
        if self.contents_data:
            for content_data in self.contents_data:
                fields_list = ['name', 'description', 'maker', 'screen_name',
                               'img_url']
                content_args = {'category': category}
                for attr_key, attr_value in content_data.items():
                    if attr_key in fields_list:
                        content_args[attr_key] = attr_value
                new_content = Content.objects.create(**content_args)
                self.contents.append(new_content)

                if 'staff' in content_data:
                    role_and_name = [re.split('[【】、]', person)
                                     for person in content_data['staff']]
                    for item in role_and_name:
                        staff_args = {'name': item[2], 'role': item[1],
                                      'content': new_content}
                        Staff.objects.create(**staff_args)
                        limit = len(item) - 3
                        for num in range(limit):
                            staff_args = {'role': item[1],
                                          'name': item[num + 3],
                                          'content': new_content}
                            Staff.objects.create(**staff_args)
                if 'cast' in content_data:
                    role_and_name = [
                        person.split('：') for person in content_data['cast']]
                    for person in role_and_name:
                        staff_args = {'role': person[0], 'name': person[1],
                                      'content': new_content, 'is_cast': True}
                        Staff.objects.create(**staff_args)

    def get_anime_data(self):
        """
        アニメに関する情報を取得しモデルを新規作成する
        :return: list 取得したデータ
        """
        url = self.create_url('/program', anime_default=True)
        response = self.get_html_from(url)
        self.extra_data_from(response)
        anime_category = Category.objects.get(name='アニメ')
        self.store_contents_data(anime_category)
        return self

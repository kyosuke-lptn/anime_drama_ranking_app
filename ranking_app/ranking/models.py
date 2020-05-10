from collections import Counter
from datetime import datetime
import json
import re
import time
from pytz import timezone
import io

from bs4 import BeautifulSoup
from django.db import models
from django.db import transaction
import environ
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from requests_oauthlib import OAuth1Session
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
        :return list: [{'rank': int(順位), 'content': cls(content), 'points': int(ポイント)}, ..]
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
        ranking, sort_result = 1, []
        for content_tuple in score_sorted:
            content_data = {'rank': ranking, 'content': content_tuple[0],
                            'points': content_tuple[1]}
            sort_result.append(content_data)
            ranking += 1
        return sort_result

    def rank(self):
        sort_contents = Content.sort_twitter_rating_by(self.category)
        rank_list = [info['content'] for info in sort_contents]
        return rank_list.index(self) + 1

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

    def popular_tweet(self):
        start_datetime = TwitterApi.start_datetime()
        tweets = {tweet.latest_tweet_count().appraise(): tweet for tweet in
                  self.tweet_set.filter(tweet_date__gte=start_datetime).prefetch_related('tweetcount_set')}
        return sorted(tweets.items(), reverse=True)[0]

    # def display_popular_tweet(self):


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

    def appraise(self):
        """
        （いいねx1 ＋ リツイートx2）/100の計算式でランキングのための数値を算出しています。
        これは、いいねよりリツイートの方が数が比較的少なく、リツイートの方が価値が高いと考えたためです。
        :return:
        """
        if self.retweet_count or self.favorite_count:
            result = (self.favorite_count + self.retweet_count * 2) / 100
            return round(result, 2)
        else:
            return 0


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


ANIME_TOP_DOMAIN = 'https://anime.eiga.com'
DRAMA_PART1_DOMAIN = 'https://thetv.jp'
DRAMA_PART1_PATH = "/program/selection/316/"
DRAMA_PART2_DOMAIN = "https://drama-circle.com/"
EXCLUSION_LIST = ['share', 'bs7ch_pr', 'tvtokyo_pr', 'intent', 'search']
EXCLUSION_ANIME_IMG = ["https://eiga.k-img.com/anime/images/shared/noimg/320.png?1484793255"]


class ScrapingContent(object):
    def __init__(self):
        self.contents_data = []
        self.contents = []

    @staticmethod
    def create_url(url='', anime_default=False, drama_default1=False):
        if anime_default:
            url = ANIME_TOP_DOMAIN + url
        elif drama_default1:
            url = DRAMA_PART1_DOMAIN + url
        return url

    @staticmethod
    def get_html_from(url):
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        return response

    def extra_drama_part1_data_from(self, response):
        """
        名前、あらすじ、画像URL、スタッフ情報、キャスト情報を取得するメソッド
        :return list:
            [dict, dict, ...., dict]
        """
        soup = BeautifulSoup(response.data, 'lxml')
        url_list = self.extra_drama_part1_url(soup)
        next_page_path = soup.select_one('ul.pageNav > li.nextPage > a')['href']
        next_page_url = self.create_url(next_page_path, drama_default1=True)
        time.sleep(1)
        next_response = self.get_html_from(next_page_url)
        next_soup = BeautifulSoup(next_response.data, 'lxml')
        url_list_of_next_page = self.extra_drama_part1_url(next_soup)
        url_list.extend(url_list_of_next_page)
        contents_list = []
        for detail_url in url_list:
            time.sleep(1)
            detail_response = self.get_html_from(detail_url)
            detail_data = self.extra_drama_part1_detail_data_from(
                detail_response)
            contents_list.append(detail_data)
        return contents_list

    @staticmethod
    def extra_drama_part1_detail_data_from(response):
        """
        :return dict:
          {name: (text), description: (text), img_url: (text),
          cast: list[role, name], staff: list[role, name]}
        """
        detail_soup = BeautifulSoup(response.data, 'lxml')
        name = detail_soup.select_one(
            '#top > div.cp_cont__h > div > div.pp_prg_hdr__grid_1_1 > h1 >'
            ' span.pp_prg_name__ttl').text.replace('\u3000', '')
        description = detail_soup.select_one(
            '#top > div.cp_cont__b > div.pp_prg_data > '
            'div.pp_prg_data__grid_1_1 > p.pp_prg_plot').text
        img_url_data = detail_soup.select_one(
            '#top > div.cp_cont__b > div.pp_prg_data >'
            ' div.pp_prg_data__grid_1_2 > img')
        cast_data = detail_soup.find_all('div', class_="cp_cast__txt")
        cast_list = []
        pattern = r'役'
        repatter = re.compile(pattern)
        for cast_tag in cast_data:
            cast_name_data = cast_tag.find('span', class_="cp_cast__name")
            cast_role_data = cast_tag.find('p', class_="cp_cast__char")
            if cast_name_data and cast_role_data:
                cast_role = cast_role_data.text
                if repatter.search(cast_role):
                    cast_role = cast_role[:-1]
                cast_list.append('{}:{}'.format(cast_role, cast_name_data.text))
        staff_data = detail_soup.find_all('li', class_="cp_stf_ls__i")
        staff_list = []
        for staff_tag in staff_data:
            staff_name_data = staff_tag.find('span', class_="cp_stf__n")
            staff_role_data = staff_tag.find('span', class_="cp_stf__r")
            if staff_name_data and staff_role_data:
                staff_list.append('{}:{}'.format(
                    staff_role_data.text, staff_name_data.text))
        contents_dict = {'name': name, 'description': description}
        if img_url_data:
            contents_dict['img_url'] = img_url_data['src']
        if cast_list:
            contents_dict['cast'] = cast_list
        if staff_list:
            contents_dict['staff'] = staff_list
        return contents_dict

    def extra_drama_part1_url(self, soup):
        url_list = []
        contents_boxes = soup.select(
            'div.contentBody.programContent.cn_prg_selections > '
            'ul.listContent.programList > li.listItem.largeItem')
        for box in contents_boxes:
            a_tag = box.find('a')
            if a_tag:
                url_path = a_tag['href']
                url = self.create_url(url_path, drama_default1=True)
                url_list.append(url)
        return url_list

    def extra_drama_part2_data_from(self, response):
        """
        作品名、公式URL、screen_name、放送開始日を取得するメソッド
        :return list: ここで取得したcontent情報のリスト
            [dict, dict, ..., dict]
        """
        soup = BeautifulSoup(response.data, 'lxml')
        drama_boxes = soup.select(
            '#new-season > #season-drama > .day-dramas > ul')
        contents_list = []
        if drama_boxes:
            for item in drama_boxes:
                a_tag = item.find('a')
                if a_tag:
                    detail_page_url = a_tag['href']
                    time.sleep(1)
                    details_page_response = self.get_html_from(detail_page_url)
                    content_dict = self.extra_drama_detail_part2_data_from(
                        details_page_response)
                    contents_list.append(content_dict)
        return contents_list

    @staticmethod
    def extra_drama_detail_part2_data_from(response):
        """
        :return: dict
            {name: (text), official_url: (text), screen_name: (text),
            release_date: (time_date), maker: (text)}
        """
        soup = BeautifulSoup(response.data, 'lxml')
        all_info = soup.find_all('ul', class_='square')
        basic_info = all_info[0].find_all('li')
        content_dict = {}
        pattern = r'https://twitter.com/(\w+)(\?\w+=\w+)?'
        repatter = re.compile(pattern)
        for li in basic_info:
            if 'タイトル：' in li.text:
                content_dict['name'] = re.split('：', li.text)[1]
            if 'ドラマ公式URL' in li.text:
                content_dict['official_url'] = li.find('a')['href']
            if 'ドラマ公式Twitter' in li.text:
                screen_name_data = repatter.match(li.find('a')['href'])
                content_dict['screen_name'] = screen_name_data.groups()[0]
            if '放映日時' in li.text:
                date_and_time = re.split(' ', li.text)[1]
                if '放送開始日' in li.text:
                    year_and_month = re.split('：', li.text)[1]
                    release_time_date = year_and_month + " " + date_and_time
                    native_date = datetime.strptime(release_time_date,
                                                    '%Y年%m月%d日 %H:%M')
                    content_dict['release_date'] = timezone(
                        'Asia/Tokyo').localize(native_date)
        maker_info = all_info[-1]
        maker_text = maker_info.find_all('li')[-1].text
        content_dict['maker'] = re.split('：', maker_text)[1]
        return content_dict

    def combine(self, contents_list1, contents_list2):
        combined_list = []
        for part2 in contents_list2:
            for part1 in contents_list1:
                if part1['name'].startswith(part2['name']):
                    part1.update(part2)
                    combined_list.append(part1)
        return combined_list

    def extra_anime_data_from(self, response):
        """
        :return self.contents_data (list):
            [dict, dict, ... dict]

            ＊dictの内容
            {name: (text), maker: (text), description: (text),
            cast: list[(text)], official_url: (text), staff: list[(text)],
            img_url: (text), screen_name: (text)}
        """
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
                    if img_data['src'] in EXCLUSION_ANIME_IMG:
                        content_dict['img_url'] = None
                    else:
                        content_dict['img_url'] = img_data['src']
                if screen_name:
                    content_dict['screen_name'] = screen_name

                self.contents_data.append(content_dict)
                time.sleep(1)
        return self.contents_data

    def get_screen_name_from(self, url):
        """
        引数のURLのサイトからtwitterのIDを抜き取り返す
        :param url:
        :return　str: screen_name
        """
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
    def store_contents_data(self, category, anime=False, drama=False):
        """
        引数のデータをcontentモデル・staffモデルとして保存する。
        :param category: obj
        :param anime: Boolean
        :param drama: Boolean
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
                if anime:
                    self.store_anime_staff(content_data, new_content)
                if drama:
                    self.store_drama_staff(content_data, new_content)

    @staticmethod
    def store_anime_staff(content_dict, content):
        """
        :param content_dict: 取得したコンテンツのdict
        :param content: スタッフ情報を保存するコンテンツ
        """
        if 'staff' in content_dict:
            role_and_name = [re.split('[【】、]', person)
                             for person in content_dict['staff']]
            for item in role_and_name:
                staff_args = {'name': item[2], 'role': item[1],
                              'content': content}
                Staff.objects.create(**staff_args)
                limit = len(item) - 3
                for num in range(limit):
                    staff_args = {'role': item[1],
                                  'name': item[num + 3],
                                  'content': content}
                    Staff.objects.create(**staff_args)
        if 'cast' in content_dict:
            role_and_name = [
                person.split('：') for person in content_dict['cast']]
            for person in role_and_name:
                staff_args = {'role': person[0], 'name': person[1],
                              'content': content, 'is_cast': True}
                Staff.objects.create(**staff_args)

    @staticmethod
    def store_drama_staff(content_dict, content):
        if 'staff' in content_dict:
            role_and_name = [re.split(':', person)
                             for person in content_dict['staff']]
            for person in role_and_name:
                staff_args = {'name': person[1], 'role': person[0],
                              'content': content}
                Staff.objects.create(**staff_args)
        if 'cast' in content_dict:
            role_and_name = [
                person.split(':') for person in content_dict['cast']]
            for person in role_and_name:
                staff_args = {'name': person[1], 'role': person[0],
                              'content': content, 'is_cast': True}
                Staff.objects.create(**staff_args)

    @transaction.atomic
    def get_anime_data(self):
        """
        アニメに関する情報を取得しモデルを新規作成する
        :return: list 取得したデータ
        """
        url = self.create_url('/program', anime_default=True)
        response = self.get_html_from(url)
        self.extra_anime_data_from(response)
        anime_category = Category.objects.get(name='アニメ')
        self.store_contents_data(anime_category, anime=True)
        return self

    @transaction.atomic
    def get_drama_data(self):
        """
        ドラマに関する情報を取得しモデルを作成する
        :return:
        """
        url = self.create_url(DRAMA_PART1_PATH, drama_default1=True)
        response_part1 = self.get_html_from(url)
        part1_contents_list = self.extra_drama_part1_data_from(response_part1)
        response_part2 = self.get_html_from(DRAMA_PART2_DOMAIN)
        part2_contents_list = self.extra_drama_part2_data_from(response_part2)
        self.contents_data = self.combine(
            part1_contents_list, part2_contents_list)
        drama_category = Category.objects.get(name='ドラマ')
        self.store_contents_data(drama_category, drama=True)
        return self


class Graph(object):

    def __init__(self):
        self.ax = None
        self.svg = None

    def set_rank_graph(self, content):
        start = TwitterApi.start_datetime()
        tweet_list = content.twitteruser.tweet_set.filter(
            tweet_date__gte=start).order_by('-tweet_date')
        x, y = [], []
        for tweet in tweet_list:
            x.append(tweet.latest_tweet_count().appraise())
            y.append(tweet.tweet_date)
        ja_tz = timezone('Asia/Tokyo')
        self.ax = plt.subplot()
        self.ax.plot(y, x)
        date_format = mdates.DateFormatter("%m/%d")
        date_interval = mdates.DayLocator(interval=5, tz=ja_tz)
        self.ax.xaxis.set_major_locator(date_interval)
        self.ax.xaxis.set_major_formatter(date_format)
        self.ax.set_xlim(start, datetime.now(ja_tz))

    def plt_to_svg(self):
        buf = io.BytesIO()
        plt.savefig(buf, format='svg', bbox_inches='tight')
        self.svg = buf.getvalue()
        buf.close()
        return self.svg

    def plt_clean(self):
        plt.cla()

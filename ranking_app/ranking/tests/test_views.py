from django.test import TestCase
from django.urls import reverse

from ..factory import CategoryFactory
from ..factory import ContentFactory
from ..factory import TwitterUserFactory
from ..factory import TweetFactory
from ..factory import TweetCountFactory
from ..factory import StaffFactory
from ..models import Content


def create_content_with_data(category, name=None, retweet=None):
    if name:
        content = ContentFactory(name=name, category=category)
    else:
        content = ContentFactory(category=category)
    twitter_user = TwitterUserFactory(content=content)
    tweet = TweetFactory(twitter_user=twitter_user)
    if retweet:
        TweetCountFactory(tweet=tweet, retweet_count=retweet)
    else:
        TweetCountFactory(tweet=tweet)
    return content


class RankingIndexViewTests(TestCase):

    def test_display_only_high_rank_content(self):
        anime = CategoryFactory(name='アニメ')
        CategoryFactory(name='ドラマ')
        contents = []
        for num in range(5):
            contents.append(
                create_content_with_data(anime, 'most popular{}'.format(num),
                                         100 - num))
        for num in range(50):
            create_content_with_data(anime, 'Not popular{}'.format(num), num)

        response = self.client.get(reverse('ranking:index'))
        self.assertEqual(response.status_code, 200)
        for content in contents:
            self.assertContains(response, content.name)
            self.assertContains(response, content.appraise())
        self.assertNotContains(response, "Not popular")


class CategoryViewTests(TestCase):

    def test_anime_category(self):
        anime = CategoryFactory(name='アニメ')
        for _ in range(30):
            create_content_with_data(anime)

        sort_info = Content.sort_twitter_rating_by(anime)
        contents = [info['content'] for info in sort_info]
        for page in range(2):
            response = self.client.get(
                "".join([reverse('ranking:category', args=[anime.id]),
                         '?p={}'.format(page)]))
            self.assertEqual(response.status_code, 200)
            stop = 15 * page
            start = stop - 15
            for ranking_content in contents[start:stop]:
                self.assertContains(response, ranking_content.name)
                self.assertContains(response, ranking_content.img_url)
                for cast in ranking_content.performers():
                    self.assertContains(response, cast.name)
                    self.assertContains(response, cast.role)
            self.assertNotContains(response, contents[stop])
            self.assertContains(response, '美しい世界は')

    def test_paging(self):
        anime = CategoryFactory(name='アニメ')
        for _ in range(30):
            create_content_with_data(anime)

        response = self.client.get(reverse('ranking:category', args=[anime.id]))

        self.assertContains(response, 'p=1')
        self.assertContains(response, 'p=2')


class ContentDetailViewTests(TestCase):

    def test_works_fine(self):
        anime = CategoryFactory(name='アニメ')
        content = create_content_with_data(anime)
        cast = StaffFactory(is_cast=True, content=content)
        staff = StaffFactory(is_cast=False, content=content)

        response = self.client.get(
            reverse('ranking:content_detail', args=[content.id]))

        self.assertContains(response, content.name)
        self.assertContains(response, content.img_url)
        self.assertContains(response, content.screen_name)
        self.assertContains(response, content.description)
        self.assertContains(response, content.maker)
        # TODO release_dateの表示を設定する
        # self.assertContains(response, content.release_date)
        self.assertContains(response, content.twitteruser.followers_count)
        self.assertContains(response, content.twitteruser.all_tweet_count)
        self.assertContains(response, content.twitteruser.favorite_avg())
        self.assertContains(response, content.twitteruser.retweets_avg())
        self.assertContains(response, content.twitteruser.official_url)
        self.assertContains(response, cast.name)
        self.assertContains(response, cast.role)
        self.assertContains(response, staff.name)
        self.assertContains(response, staff.role)


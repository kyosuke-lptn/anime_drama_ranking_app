from django.test import TestCase
from django.urls import reverse

from ..factory import CategoryFactory
from ..factory import ContentFactory
from ..factory import TwitterUserFactory
from ..factory import TweetFactory
from ..factory import TweetCountFactory
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
    def test_displayed_correctly(self):
        anime = CategoryFactory(name='アニメ')
        CategoryFactory(name='ドラマ')
        content = create_content_with_data(anime, 'most popular', 100)

        response = self.client.get(reverse('ranking:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, content.name)
        self.assertQuerysetEqual(response.context['anime'],
                                 ['<Content: most popular>'])


class CategoryViewTests(TestCase):

    def test_paging(self):
        anime = CategoryFactory(name='アニメ')
        for _ in range(30):
            create_content_with_data(anime)

        contents = Content.sort_twitter_rating_by(anime)
        for page in range(2):
            response = self.client.get(
                "".join([reverse('ranking:category', args=[anime.id]),
                         '?p={}'.format(page)]))
            self.assertEqual(response.status_code, 200)
            stop = 15 * page
            start = stop - 15
            for ranking_content in contents[start:stop]:
                self.assertContains(response, ranking_content.name)
                self.assertNotContains(response, contents[stop])


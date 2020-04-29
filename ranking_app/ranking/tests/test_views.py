from django.test import TestCase
from django.urls import reverse

from ..factory import CategoryFactory
from ..factory import ContentFactory
from ..factory import TwitterUserFactory
from ..factory import TweetFactory
from ..factory import TweetCountFactory


def create_content_with_data(name, category, retweet, favorite):
    content = ContentFactory(name=name, category=category)
    twitter_user = TwitterUserFactory(content=content)
    tweet = TweetFactory(twitter_user=twitter_user)
    TweetCountFactory(tweet=tweet, retweet_count=retweet,
                      favorite_count=favorite)
    return content


class RankingIndexViewTests(TestCase):
    def test_displayed_correctly(self):
        anime = CategoryFactory(name='アニメ')
        CategoryFactory(name='ドラマ')
        content = create_content_with_data('most popular', anime, 100, 100)

        response = self.client.get(reverse('ranking:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, content.name)
        self.assertQuerysetEqual(response.context['anime'],
                                 ['<Content: most popular>'])
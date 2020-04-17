from django.db.utils import IntegrityError, DataError
from django.test import TestCase

from ranking import factory

# Create your tests here.


class ContentModelTests(TestCase):

    def test_content_name_unique(self):
        factory.ContentFactory(content_name='movie A')
        with self.assertRaises(IntegrityError):
            factory.ContentFactory(content_name='movie A')

    def test_content_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            factory.ContentFactory(content_name=name)

    def test_description_max_length(self):
        description = 'a' * 501
        with self.assertRaises(DataError):
            factory.ContentFactory(description=description)

    def test_maker_max_length(self):
        maker = 'a' * 51
        with self.assertRaises(DataError):
            factory.ContentFactory(maker=maker)


class CategoryModelTests(TestCase):

    def test_category_name_unique(self):
        factory.CategoryFactory(category_name='Movie')
        with self.assertRaises(IntegrityError):
            factory.CategoryFactory(category_name='Movie')

    def test_category_name_max_length(self):
        name = 'a' * 21
        with self.assertRaises(DataError):
            factory.CategoryFactory(category_name=name)


class TwitterDataModelTests(TestCase):

    def setUp(self):
        self.data = factory.TwitterRegularlyDataFactory(retweet_count=100,
                                                        favorite_count=50,
                                                        statuses_count=10)

    def test_retweets_avg(self):
        self.assertEqual(self.data.retweets_avg(), 10)

    def test_favorite_avg(self):
        self.assertEqual(self.data.favorite_avg(), 5)


import datetime
from django.db.utils import IntegrityError, DataError
from django.test import TestCase
from django.utils import timezone

from ranking.models import Content, Category, TwitterData

# Create your tests here.


def create_content(name='sample movie',
                   description='This movie is interesting',
                   maker='sample company'):
    release_date = timezone.now() - datetime.timedelta(days=365)
    return Content.objects.create(content_name=name,
                                  description=description,
                                  release_date=release_date,
                                  maker=maker)


def create_category(category_name='Movie',
                    content=None):
    new_category = Category.objects.create(category_name=category_name)
    if content:
        new_category.content.add(content)
        new_category.save()
    return new_category


class ContentModelTests(TestCase):

    def test_content_name_unique(self):
        create_content(name='movie A')
        with self.assertRaises(IntegrityError):
            create_content(name='movie A')

    def test_content_name_max_length(self):
        name = 'a' * 51
        with self.assertRaises(DataError):
            create_content(name=name)

    def test_description_max_length(self):
        description = 'a' * 501
        with self.assertRaises(DataError):
            create_content(description=description)

    def test_maker_max_length(self):
        maker = 'a' * 51
        with self.assertRaises(DataError):
            create_content(maker=maker)


class CategoryModelTests(TestCase):

    def test_category_name_unique(self):
        create_category(category_name='Movie')
        with self.assertRaises(IntegrityError):
            create_category(category_name='Movie')

    def test_category_name_max_length(self):
        name = 'a' * 21
        with self.assertRaises(DataError):
            create_category(category_name=name)

    def test_many_to_many(self):
        A = create_content(name='content A')
        B = create_content(name='content B')
        anime = create_category(category_name='Anime')
        movie = create_category(category_name='Movie')
        A.category_set.add(anime)
        A.category_set.add(movie)
        A.save()
        B.category_set.add(anime)
        B.save()
        self.assertEqual(A.category_set.count(), 2)
        self.assertEqual(anime.content.count(), 2)


class TwitterDataModelTests(TestCase):

    def test_attr(self):
        content = create_content()
        time = timezone.now()
        tw_data = TwitterData.objects.create(
            tweets_count=50,
            aggregation_period=time,
            content=content
        )
        self.assertEqual(tw_data.tweets_count, 50)
        self.assertEqual(tw_data.aggregation_period, time)
        self.assertEqual(tw_data.content, content)

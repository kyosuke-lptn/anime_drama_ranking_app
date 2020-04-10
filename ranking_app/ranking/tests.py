import datetime

from django.test import TestCase
from django.utils import timezone

from .models import Content

from .models import Content, Category, TwitterData

# Create your tests here.


def create_content(name='sample movie'):
    content_name = name
    description = 'This movie is interesting'
    release_date = timezone.now() - datetime.timedelta(days=365)
    maker = 'sample company'
    return Content.objects.create(content_name=content_name,
                                  description=description,
                                  release_date=release_date,
                                  maker=maker)


class ContentModelTests(TestCase):

    def test_content_name_unique(self):
        # TODO (sumitani) テストをかく
        # create_content(name='movie A')
        # create_content(name='movie A')
        # self.assertEqual(
        #     Content.objects.all().count(),
        #     1
        # )

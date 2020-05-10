from django.core.management.base import BaseCommand

from ...models import Category
from ...models import TwitterApi


class Command(BaseCommand):

    help = 'Aggregate tweets data'

    def add_arguments(self, parser):
        parser.add_argument('--anime', action='store_true', default=False,
                            help='アニメ情報を取得します。')
        parser.add_argument('--drama', action='store_true', default=False,
                            help='ドラマ情報を取得します。')

    def handle(self, *args, **options):
        contents = None
        api = TwitterApi()
        if options['anime']:
            contents = Category.objects.get(name='アニメ').content_set.all()
        elif options['drama']:
            contents = Category.objects.get(name='ドラマ').content_set.all()
        if contents:
            for content in contents:
                if content.has_tweets():
                    api.update_data(content)
                    print('{} : データ取得完了しました！！'.format(content.name))
        else:
            print('オプションを付けてないか、contentが存在しない')

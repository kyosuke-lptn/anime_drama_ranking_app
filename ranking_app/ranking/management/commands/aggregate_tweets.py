from django.core.management.base import BaseCommand

from ...models import Content
from ...models import TwitterApi


class Command(BaseCommand):

    help = 'Aggregate tweets data'

    def add_arguments(self, parser):
        parser.add_argument('-sn', nargs=1, type=str, required=True,
                            help='（必須）検索するtwitterアカウントのscreen name')

    def handle(self, *args, **options):
        screen_name = options['sn'].pop()
        api = TwitterApi()
        content = Content.objects.get(screen_name=screen_name)
        if content.has_tweets():
            api.update_data(content)
        else:
            api.get_and_store_twitter_data(content)
        print('データ取得完了しました！！')

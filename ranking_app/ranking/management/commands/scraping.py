from django.core.management.base import BaseCommand

from ...models import ScrapingContent
from ...models import TwitterApi


class Command(BaseCommand):

    help = 'Get information by category using scraping.' \
           'You must choose either option(--anime or --dorama).'

    def add_arguments(self, parser):
        parser.add_argument('--anime', action='store_true', default=False,
                            help='アニメ情報を取得します。')
        parser.add_argument('--dorama', action='store_true', default=False,
                            help='ドラマ情報を取得します。')

    def handle(self, *args, **options):
        if options['anime']:
            content_getter = ScrapingContent().get_anime_data()
            if content_getter.contents:
                print('アニメサイトのスクレイピングが完了しました。')
                api = TwitterApi()
                for content in content_getter.contents:
                    api.get_and_store_twitter_data(content)
            else:
                print('スクレイピングが失敗しました。コードを見直してください。')
        elif options['dorama']:
            print('あとで実装します。。')

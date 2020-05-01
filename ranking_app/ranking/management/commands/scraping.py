from django.core.management.base import BaseCommand

from ...models import ScrapingContent
from ...models import TwitterApi


class Command(BaseCommand):

    help = 'Get information by category using scraping.' \
           'You must choose either option(--anime or --dorama).'

    def add_arguments(self, parser):
        parser.add_argument('--anime', action='store_true', default=False,
                            help='アニメ情報を取得します。')
        parser.add_argument('--drama', action='store_true', default=False,
                            help='ドラマ情報を取得します。')

    def handle(self, *args, **options):
        # TODO 取得データをファイルに一時保存んするか考える。スクレイピング結果の確認方法について。
        if options['anime']:
            content_getter = ScrapingContent().get_anime_data()
            print('アニメサイトのスクレイピングが完了しました。')
            api = TwitterApi()
            try:
                for content in content_getter.contents:
                    api.get_and_store_twitter_data(content)
                print('Twitterの情報取得完了しました。')
                print('合計{}個のモデルを作成しました。'.format(len(content_getter.contents)))
            except AttributeError as e:
                print('スクレイピングが失敗しました。保存したモデルはロールバックされます。コードを見直してください。:'
                      '{}'.format(e))
        if options['drama']:
            content_getter = ScrapingContent().get_drama_data()
            print('ドラマサイトのスクレイピングが完了しました。')
            api = TwitterApi()
            try:
                for content in content_getter.contents:
                    api.get_and_store_twitter_data(content)
                print('Twitterの情報取得完了しました。')
                print('合計{}個のモデルを作成しました。'.format(len(content_getter.contents)))
            except AttributeError as e:
                print('スクレイピングが失敗しました。保存したモデルはロールバックされます。コードを見直してください。: '
                      '{}'.format(e))

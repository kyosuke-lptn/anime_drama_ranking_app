from django.core.management.base import BaseCommand

from ...models import TwitterApi, Content


class Command(BaseCommand):

    help = 'Aggregate tweets data'

    def add_arguments(self, parser):
        parser.add_argument('-cn', nargs=1, type=str, required=True,
                            help='（必須）登録済みのコンテンツの名前')
        parser.add_argument('-sn', nargs=1, type=str, required=True,
                            help='（必須）検索するtwitterアカウントのscreen name')

    def handle(self, *args, **options):
        content_name = options['cn'].pop()
        screen_name = options['sn'].pop()
        content = Content.objects.get(content_name=content_name)
        twitter_api = TwitterApi()
        tw_timeline = twitter_api.get_most_timeline(screen_name)
        tw_user = twitter_api.get_user(screen_name)
        twitter_api.insert_twitter_data_to_ranking_class(content, tw_user,
                                                         tw_timeline)
        print('データ取得完了しました！！')



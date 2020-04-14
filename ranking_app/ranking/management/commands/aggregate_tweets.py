from django.core.management.base import BaseCommand

from ...models import TwitterData, TwitterApi


class Command(BaseCommand):

    help = 'Aggregate tweets data'

    def handle(self, *args, **options):
        screen_name =
        twitter_api = TwitterApi()
        tw_timeline = twitter_api.get_most_timeline(screen_name)
        tw_user = twitter_api.get_user(screen_name)
        # TODO (sumitani) いかにTwitterRefularyDataとTwitterDateに入力するコマンドをかく




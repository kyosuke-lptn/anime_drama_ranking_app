from django.db.utils import IntegrityError

from .models import Category


class InitCreateCategoryMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

        def create_category(name):
            try:
                Category.objects.create(name=name)
            except IntegrityError:
                print('すでに{}のカテゴリーが追加されています。'.format(name))
        create_category('アニメ')
        create_category('ドラマ')

    def __call__(self, request):
        response = self.get_response(request)
        return response

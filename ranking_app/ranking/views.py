from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from .models import Category
from .models import Content
from .utils import paging

# Create your views here.


class IndexView(TemplateView):
    template_name = 'ranking/index.html.haml'


DISPLAY_NUMBER = 15


class CategoryIndexView(View):
    def get(self, request, category_id, *args, **kwargs):
        category = Category.objects.get(id=category_id)
        all_contents = Content.sort_twitter_rating_by(category)
        contents_info = paging(request, all_contents, DISPLAY_NUMBER)
        context = {
            'category': category,
            'contents_info': contents_info,
        }
        return render(request, 'ranking/category.html.haml', context)


class ContentDetailView(View):
    def get(self, request, content_id, *args, **kwargs):
        content = Content.objects.get(pk=content_id)
        context = {
            'content': content,
        }
        return render(request, 'ranking/content_detail.html.haml', context)


index = IndexView.as_view()
category_index = CategoryIndexView.as_view()
content_detail = ContentDetailView.as_view()

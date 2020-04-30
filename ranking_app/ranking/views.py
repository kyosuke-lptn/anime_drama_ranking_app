from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views import View
from django.views.generic import TemplateView

from .models import Category
from .models import Content
from .utils import paging

# Create your views here.


class IndexView(TemplateView):
    template_name = 'ranking/index.html.haml'


DISPLAY_NUMBER = 15


class CategoryView(View):
    def get(self, request, category_id, *args, **kwargs):
        category = Category.objects.get(id=category_id)
        all_contents = Content.sort_twitter_rating_by(category)
        contents = paging(request, all_contents, DISPLAY_NUMBER)
        context = {
            'category': category,
            'contents': contents,
        }
        return render(request, 'ranking/category.html.haml', context)


index_view = IndexView.as_view()
category_view = CategoryView.as_view()

def animation(request):
    template = loader.get_template('ranking/category.html.haml')
    return HttpResponse(template.render())

def drama(request):
    template = loader.get_template('ranking/dramas.html.haml')
    return HttpResponse(template.render())

def show(request):
    template = loader.get_template('ranking/detail.html.haml')
    return HttpResponse(template.render())
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views import View
from django.views.generic import TemplateView

from .models import Category
from .models import Content

# Create your views here.


class IndexView(TemplateView):
    template_name = 'ranking/index.html.haml'

    def get_context_data(self, **kwargs):
        # TODO もっと簡単にかく
        context = super().get_context_data(**kwargs)
        anime = Category.objects.get(name='アニメ')
        dorama = Category.objects.get(name='ドラマ')
        context['anime'] = Content.sort_twitter_rating_by(anime)[:5]
        context['dorama'] = Content.sort_twitter_rating_by(dorama)[:5]
        return context


DISPLAY_NUMBER = 15


class CategoryView(View):
    def get(self, request, category_id, *args, **kwargs):
        anime = Category.objects.get(id=category_id)
        all_contents = Content.sort_twitter_rating_by(anime)
        paginator = Paginator(all_contents, DISPLAY_NUMBER)
        p = request.GET.get('p')
        contents = paginator.get_page(p)
        context = {
            'contents': contents
        }
        return render(request, 'ranking/category.html.haml', context)


index = IndexView.as_view()
category = CategoryView.as_view()

def animation(request):
    template = loader.get_template('ranking/category.html.haml')
    return HttpResponse(template.render())

def drama(request):
    template = loader.get_template('ranking/dramas.html.haml')
    return HttpResponse(template.render())

def show(request):
    template = loader.get_template('ranking/detail.html.haml')
    return HttpResponse(template.render())
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from .models import Category
from .models import Content

# Create your views here.


class IndexView(TemplateView):
    template_name = 'ranking/index.html.haml'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anime = Category.objects.get(name='アニメ')
        dorama = Category.objects.get(name='ドラマ')
        context['anime'] = Content.sort_twitter_rating_by(anime)[:5]
        context['dorama'] = Content.sort_twitter_rating_by(dorama)[:5]
        return context


index = IndexView.as_view()

def animation(request):
    template = loader.get_template('ranking/animations.html.haml')
    return HttpResponse(template.render())

def drama(request):
    template = loader.get_template('ranking/dramas.html.haml')
    return HttpResponse(template.render())

def show(request):
    template = loader.get_template('ranking/detail.html.haml')
    return HttpResponse(template.render())
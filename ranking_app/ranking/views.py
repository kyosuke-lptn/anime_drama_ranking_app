from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from .models import Content

# Create your views here.


def index(request):
    template = loader.get_template('ranking/index.html.haml')
    return HttpResponse(template.render())

def show(request):
    template = loader.get_template('ranking/detail.html.haml')
    return HttpResponse(template.render())

def show1(request):
    template = loader.get_template('ranking/category.html.haml')
    return HttpResponse(template.render())
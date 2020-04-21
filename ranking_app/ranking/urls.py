from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index, name='index'),
    path('category/', views.show, name = 'show'),
    path('detail/', views.show, name = 'show')
]
